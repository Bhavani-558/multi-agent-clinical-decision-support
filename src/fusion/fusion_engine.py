"""
Fusion Engine for Module 6 — Decision / Fusion Layer.
Aggregates outputs from Modules 1–5, computes fused confidence, maintains 5 separate top-level fields,
and synthesizes decision-support interpretations.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence, EvidenceAgentResponse
from src.reasoning.schemas import ReasoningOutput
from src.fusion.schemas import (
    DecisionSupportClassification,
    FusedConfidenceBreakdown,
    ClinicalDecisionOutput,
    UncertaintyFlag
)
from src.fusion.decision_classifier import DecisionClassifier
from src.reasoning.contradiction_detector import ContradictionDetector


class FusionEngine:
    """
    Core synthesis engine for decision and evidence fusion.
    Consumes Module 5 Trust Score & Consensus without modification.
    """

    def __init__(self, classifier: Optional[DecisionClassifier] = None):
        self.classifier = classifier or DecisionClassifier()

    def calculate_fused_confidence(
        self,
        reasoning: ReasoningOutput,
        classification: DecisionSupportClassification
    ) -> FusedConfidenceBreakdown:
        """
        Calculates fused confidence score consuming Module 5 Trust Score directly.
        Applies system-design safety cap (0.50) if contradictory evidence exists.
        """
        trust = reasoning.trust_score
        consensus = reasoning.consensus_result

        s_trust = trust.overall_trust_score
        s_consensus = consensus.consensus_score
        s_conf = trust.confidence_factor

        t_comp = round(0.40 * s_trust, 4)
        c_comp = round(0.35 * s_consensus, 4)
        m_comp = round(0.25 * s_conf, 4)

        raw_fused = round(t_comp + c_comp + m_comp, 4)

        is_capped = (
            classification == DecisionSupportClassification.CONTRADICTION_FLAG or
            consensus.consensus_level == "CONTRADICTORY_CONSENSUS" or
            reasoning.contradiction_analysis.has_contradictions and reasoning.contradiction_analysis.conflicting_count > 0
        )

        if is_capped:
            final_fused = min(raw_fused, 0.50)
            cap_doc = (
                "Fused confidence score capped at 0.50 (deterministic system-design software safety rule "
                "to prevent high confidence during conflicting evidence; NOT a clinically validated threshold)."
            )
        else:
            final_fused = max(0.0, min(1.0, raw_fused))
            cap_doc = "Standard fused confidence score calculation applied without contradiction capping."

        return FusedConfidenceBreakdown(
            overall_fused_score=final_fused,
            pre_cap_fused_score=raw_fused,
            trust_component=t_comp,
            consensus_component=c_comp,
            model_confidence_component=m_comp,
            is_capped_by_contradiction=is_capped,
            cap_documentation=cap_doc
        )

    def generate_decision_interpretation(
        self,
        model_id: str,
        classification: DecisionSupportClassification,
        fused_confidence: FusedConfidenceBreakdown,
        reasoning: ReasoningOutput
    ) -> str:
        """
        Synthesizes structured decision-support interpretation text.
        Maintains clear distinction between prediction, evidence, trust/consensus, and decision support.
        Does NOT invent medical facts, drug prescriptions, or treatment guidelines.
        """
        prob = reasoning.prediction_summary.get("probability", 0.0)
        c_level = reasoning.consensus_result.consensus_level
        t_score = reasoning.trust_score.overall_trust_score

        lines = [
            f"=== CDSS DECISION-SUPPORT SYNTHESIS REPORT: {model_id.upper()} ===",
            f"Classification: [{classification.value}]",
            f"Fused Confidence Score: {fused_confidence.overall_fused_score:.4f}",
            "",
            "1. MODEL PREDICTION SUMMARY:",
            f"   - Predicted Risk Probability: {prob * 100:.1f}%",
            f"   - Predicted Label: {reasoning.prediction_summary.get('predicted_label', 'N/A')}",
            f"   - Model Decisiveness Factor: {reasoning.trust_score.confidence_factor:.4f}",
            "",
            "2. SHAP EXPLANATION SUMMARY:",
            f"   - SHAP Status: {reasoning.trust_score.shap_status}",
            f"   - SHAP Alignment Factor: {reasoning.trust_score.shap_alignment_factor if reasoning.trust_score.shap_alignment_factor is not None else 'N/A (Omitted/Renormalized)'}",
            "",
            "3. BIOMEDICAL GRAPH EVIDENCE SUMMARY:",
            f"   - Mapped Graph Node: '{reasoning.prediction_summary.get('model_id', model_id)}'",
            f"   - Supporting Evidence Items: {reasoning.contradiction_analysis.supporting_count}",
            f"   - Conflicting Evidence Items: {reasoning.contradiction_analysis.conflicting_count}",
            f"   - Neutral / Contextual Items: {reasoning.contradiction_analysis.neutral_count}",
            "",
            "4. TRUST & CONSENSUS EVALUATION SUMMARY:",
            f"   - Module 5 Trust Score: {t_score:.4f} (Preserved unchanged)",
            f"   - Consensus Level: {c_level} (Score: {reasoning.consensus_result.consensus_score:.4f})",
            f"   - Evidence Consistency Factor: {reasoning.trust_score.evidence_consistency_factor:.4f}",
            "",
            "5. CLINICAL DECISION-SUPPORT INTERPRETATION & AUDIT GUIDANCE:"
        ]

        if classification == DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT:
            lines.append("   - Interpretation: High predicted risk supported by consistent knowledge evidence and/or SHAP attributions.")
            lines.append("   - System Guidance: Highlighted for practitioner review. Evaluate patient clinical history alongside predictions.")
        elif classification == DecisionSupportClassification.LOW_RISK_DECISION_SUPPORT:
            lines.append("   - Interpretation: Low predicted risk based on the available model and supporting evidence.")
            lines.append("   - System Guidance: Clinician review is recommended.")
        elif classification == DecisionSupportClassification.CONTRADICTION_FLAG:
            lines.append("   - Interpretation: Conflicting evidence detected between model prediction, graph triples, or SHAP attributions.")
            lines.append("   - System Guidance: Expert clinician audit required to review conflicting evidence items before action.")
        elif classification == DecisionSupportClassification.INSUFFICIENT_EVIDENCE:
            lines.append("   - Interpretation: Model prediction lacks sufficient PrimeKG graph evidence backing or resolved nodes.")
            lines.append("   - System Guidance: Proceed with caution. Prediction cannot be independently corroborated by graph knowledge.")
        elif classification == DecisionSupportClassification.DEGRADED_CONFIDENCE:
            lines.append("   - Interpretation: Confidence is reduced because SHAP information is unavailable or model decisiveness is low.")
            lines.append("   - System Guidance: Review the available evidence before interpretation.")

        lines.append(f"\nSystem Safety Documentation: {fused_confidence.cap_documentation}")

        return "\n".join(lines)

    def evaluate_fusion(
        self,
        reasoning: ReasoningOutput,
        shap_explanation: Optional[Dict[str, Any]] = None,
        graph_evidence: Optional[KnowledgeGraphEvidence] = None
    ) -> ClinicalDecisionOutput:
        """
        Executes full Module 6 decision fusion pipeline.
        Maintains 5 distinct top-level fields in output payload.
        """
        # Step 1: Determine Decision-Support Classification & Uncertainty Flags
        classification, flags = self.classifier.classify(reasoning)

        # Step 2: Compute Fused Confidence (consuming Module 5 Trust Score directly)
        fused_confidence = self.calculate_fused_confidence(reasoning, classification)

        # Step 3: Synthesize Decision Rationale
        interpretation = self.generate_decision_interpretation(
            model_id=reasoning.model_id,
            classification=classification,
            fused_confidence=fused_confidence,
            reasoning=reasoning
        )

        # Build Field 2: SHAP Summary
        if shap_explanation:
            shap_summary = {
                "disease": shap_explanation.get("disease", reasoning.disease),
                "base_value": shap_explanation.get("base_value", 0.0),
                "top_attributions": shap_explanation.get("top_attributions", []),
                "shap_status": reasoning.trust_score.shap_status
            }
        else:
            shap_summary = {
                "disease": reasoning.disease,
                "shap_status": reasoning.trust_score.shap_status,
                "top_attributions": [
                    item.model_dump() for item in reasoning.supporting_evidence + reasoning.conflicting_evidence
                    if item.category == "shap_attribution"
                ]
            }

        # Build Field 3: Evidence Summary
        if graph_evidence:
            graph_counts = ContradictionDetector().get_graph_evidence_counts(graph_evidence)
            evidence_summary = {
                "mapped_graph_node": graph_evidence.mapped_graph_node,
                "total_triples_found": graph_counts["total"],
                "supporting_count": graph_counts["supporting"],
                "conflicting_count": graph_counts["conflicting"],
                "neutral_count": graph_counts["neutral"],
                "combined_supporting_count": reasoning.contradiction_analysis.supporting_count,
                "combined_conflicting_count": reasoning.contradiction_analysis.conflicting_count,
                "combined_neutral_count": reasoning.contradiction_analysis.neutral_count,
                "phenotype_count": len(graph_evidence.phenotypes),
                "drug_count": len(graph_evidence.drugs),
                "gene_count": len(graph_evidence.genes_biomarkers)
            }
        else:
            evidence_summary = {
                "supporting_count": reasoning.contradiction_analysis.supporting_count,
                "conflicting_count": reasoning.contradiction_analysis.conflicting_count,
                "neutral_count": reasoning.contradiction_analysis.neutral_count,
                "contradiction_summary": reasoning.contradiction_analysis.contradiction_summary
            }

        # Build Field 4: Trust & Consensus Summary (Preserving Module 5 Trust Score)
        trust_and_consensus_summary = {
            "overall_trust_score": reasoning.trust_score.overall_trust_score,  # Preserved unchanged
            "confidence_factor": reasoning.trust_score.confidence_factor,
            "shap_alignment_factor": reasoning.trust_score.shap_alignment_factor,
            "graph_evidence_factor": reasoning.trust_score.graph_evidence_factor,
            "evidence_consistency_factor": reasoning.trust_score.evidence_consistency_factor,
            "shap_status": reasoning.trust_score.shap_status,
            "weights_used": reasoning.trust_score.weights_used,
            "consensus_level": reasoning.consensus_result.consensus_level,
            "consensus_score": reasoning.consensus_result.consensus_score,
            "disease_risk_tier": reasoning.consensus_result.disease_risk_tier
        }

        return ClinicalDecisionOutput(
            disease=reasoning.disease,
            model_id=reasoning.model_id,
            decision_classification=classification,
            fused_confidence=fused_confidence,
            prediction_summary=reasoning.prediction_summary,  # Field 1
            shap_summary=shap_summary,                        # Field 2
            evidence_summary=evidence_summary,                # Field 3
            trust_and_consensus_summary=trust_and_consensus_summary,  # Field 4
            decision_interpretation=interpretation,            # Field 5
            uncertainty_flags=flags
        )
