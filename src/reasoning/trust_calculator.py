"""
Trust Score Calculator Engine for Module 5.
Calculates a reproducible, bounded Trust Score (0.0 to 1.0) based on clearly defined factors.
Implements dynamic weight renormalization when SHAP data is missing.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reasoning.schemas import ContradictionAnalysis, TrustScoreResult
from src.reasoning.contradiction_detector import ContradictionDetector


class TrustCalculator:
    """
    Calculates reproducible trust scores and factor breakdowns.
    """

    BASE_WEIGHT_CONFIDENCE = 0.30
    BASE_WEIGHT_SHAP = 0.25
    BASE_WEIGHT_GRAPH = 0.25
    BASE_WEIGHT_CONSISTENCY = 0.20

    def calculate_trust_score(
        self,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        contradiction_analysis: ContradictionAnalysis,
        shap_explanation: Optional[Dict[str, Any]] = None
    ) -> TrustScoreResult:
        """
        Calculates trust score with active weight renormalization if SHAP data is missing.
        """
        prob = prediction.get("probability", prediction.get("positive_probability", 0.5))

        # 1. Model Confidence Factor: 2 * |prob - 0.5|
        confidence_factor = round(2.0 * abs(prob - 0.5), 4)

        # 2. Graph Evidence Factor: min(1.0, total_triples / 10.0) if node resolved
        triples_found = ContradictionDetector().get_graph_evidence_counts(graph_evidence)["total"]
        if graph_evidence.mapped_graph_node:
            graph_factor = round(min(1.0, triples_found / 10.0), 4)
        else:
            graph_factor = 0.0

        # 3. Evidence Consistency Factor: 1.0 - (conflicting / max(1, supporting + conflicting))
        tot_eval = contradiction_analysis.supporting_count + contradiction_analysis.conflicting_count
        if tot_eval > 0:
            consistency_factor = round(1.0 - (contradiction_analysis.conflicting_count / tot_eval), 4)
        else:
            consistency_factor = 1.0

        # 4. SHAP Alignment Factor (if present)
        has_shap = shap_explanation is not None and bool(
            shap_explanation.get("top_attributions") or shap_explanation.get("top_features")
        )

        shap_factor: Optional[float] = None
        weights_used: Dict[str, float] = {}

        if has_shap:
            shap_status = "INCLUDED"
            shap_items = [
                item for item in contradiction_analysis.supporting_evidence + contradiction_analysis.conflicting_evidence
                if item.category == "shap_attribution"
            ]
            tot_shap = len(shap_items)
            if tot_shap > 0:
                aligned_shap = sum(1 for item in shap_items if item.is_supporting)
                shap_factor = round(aligned_shap / tot_shap, 4)
            else:
                shap_factor = 1.0

            weights_used = {
                "confidence_factor": self.BASE_WEIGHT_CONFIDENCE,
                "shap_alignment_factor": self.BASE_WEIGHT_SHAP,
                "graph_evidence_factor": self.BASE_WEIGHT_GRAPH,
                "evidence_consistency_factor": self.BASE_WEIGHT_CONSISTENCY
            }

            raw_score = (
                self.BASE_WEIGHT_CONFIDENCE * confidence_factor +
                self.BASE_WEIGHT_SHAP * shap_factor +
                self.BASE_WEIGHT_GRAPH * graph_factor +
                self.BASE_WEIGHT_CONSISTENCY * consistency_factor
            )
        else:
            shap_status = "OMITTED_RENORMALIZED"
            # Renormalize weights: sum of base weights without SHAP is 0.30 + 0.25 + 0.20 = 0.75
            w_sum = self.BASE_WEIGHT_CONFIDENCE + self.BASE_WEIGHT_GRAPH + self.BASE_WEIGHT_CONSISTENCY
            w_conf = round(self.BASE_WEIGHT_CONFIDENCE / w_sum, 4)
            w_graph = round(self.BASE_WEIGHT_GRAPH / w_sum, 4)
            w_cons = round(self.BASE_WEIGHT_CONSISTENCY / w_sum, 4)

            weights_used = {
                "confidence_factor": w_conf,
                "graph_evidence_factor": w_graph,
                "evidence_consistency_factor": w_cons
            }

            raw_score = (
                w_conf * confidence_factor +
                w_graph * graph_factor +
                w_cons * consistency_factor
            )

        final_trust_score = round(max(0.0, min(1.0, raw_score)), 4)

        doc_lines = [
            "Trust Score Calculation Breakdown:",
            f"  - Model Confidence Factor: {confidence_factor:.4f} (Weight: {weights_used.get('confidence_factor', 0.0):.4f})",
            f"  - Graph Evidence Factor: {graph_factor:.4f} (Weight: {weights_used.get('graph_evidence_factor', 0.0):.4f})",
            f"  - Evidence Consistency Factor: {consistency_factor:.4f} (Weight: {weights_used.get('evidence_consistency_factor', 0.0):.4f})"
        ]
        if has_shap:
            doc_lines.append(f"  - SHAP Alignment Factor: {shap_factor:.4f} (Weight: {weights_used.get('shap_alignment_factor', 0.0):.4f})")
        else:
            doc_lines.append("  - SHAP Factor: Excluded (Weights renormalized dynamically)")

        doc_lines.append(f"  -> Overall Trust Score: {final_trust_score:.4f} [{shap_status}]")

        return TrustScoreResult(
            overall_trust_score=final_trust_score,
            confidence_factor=confidence_factor,
            shap_alignment_factor=shap_factor,
            graph_evidence_factor=graph_factor,
            evidence_consistency_factor=consistency_factor,
            shap_status=shap_status,
            weights_used=weights_used,
            logic_documentation="\n".join(doc_lines)
        )
