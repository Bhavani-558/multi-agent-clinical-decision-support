"""
Consensus Analyzer Engine for Module 5.
Evaluates model probability decisiveness, SHAP feature direction alignment,
and PrimeKG evidence triples to produce a deterministic consensus result.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reasoning.schemas import ContradictionAnalysis, ConsensusResult
from src.reasoning.contradiction_detector import ContradictionDetector


class ConsensusAnalyzer:
    """
    Evaluates evidence consensus across ML prediction, SHAP attributions, and PrimeKG triples.
    """

    def evaluate_consensus(
        self,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        contradiction_analysis: ContradictionAnalysis,
        shap_explanation: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """
        Calculates a deterministic consensus level, score, and explanation.
        """
        prob = prediction.get("probability", prediction.get("positive_probability", 0.5))
        pred_class = prediction.get("predicted_class", 0)

        # Class 0 indicates absence/healthy (LOW_RISK); Class >= 1 indicates disease presence (HIGH_RISK)
        if str(pred_class).strip() in ["0", "-1"]:
            risk_tier = "LOW_RISK"
        else:
            risk_tier = "HIGH_RISK" if prob >= 0.5 else "LOW_RISK"


        supp_cnt = contradiction_analysis.supporting_count
        conf_cnt = contradiction_analysis.conflicting_count
        tot_eval = supp_cnt + conf_cnt
        triples_found = ContradictionDetector().get_graph_evidence_counts(graph_evidence)["total"]

        # Case 1: Insufficient Evidence
        if tot_eval == 0 and triples_found == 0:
            return ConsensusResult(
                consensus_level="INSUFFICIENT_EVIDENCE",
                consensus_score=0.0,
                disease_risk_tier=risk_tier,
                explanation="Insufficient evidence: No PrimeKG graph triples or evaluable features found to establish consensus."
            )

        # Case 2: Contradictory Consensus
        if conf_cnt > supp_cnt or (conf_cnt > 0 and supp_cnt == 0):
            score = round(supp_cnt / max(1, tot_eval), 4)
            return ConsensusResult(
                consensus_level="CONTRADICTORY_CONSENSUS",
                consensus_score=score,
                disease_risk_tier=risk_tier,
                explanation=f"Contradictory consensus: Conflicting evidence detected ({conf_cnt} conflicting vs {supp_cnt} supporting items)."
            )

        # Case 3: Strong Consensus
        confidence_delta = abs(prob - 0.5)
        if confidence_delta >= 0.20 and conf_cnt == 0 and supp_cnt >= 1:
            ratio = supp_cnt / max(1, tot_eval)
            score = round(min(1.0, 0.70 + 0.30 * ratio), 4)
            return ConsensusResult(
                consensus_level="STRONG_CONSENSUS",
                consensus_score=score,
                disease_risk_tier=risk_tier,
                explanation=f"Strong consensus: High prediction confidence ({prob*100:.1f}%) strongly supported by evidence ({supp_cnt} supporting, 0 conflicting)."
            )

        # Case 4: Moderate Consensus
        if supp_cnt > conf_cnt:
            score = round(supp_cnt / max(1, tot_eval), 4)
            return ConsensusResult(
                consensus_level="MODERATE_CONSENSUS",
                consensus_score=score,
                disease_risk_tier=risk_tier,
                explanation=f"Moderate consensus: Prediction supported by {supp_cnt} evidence item(s) with {conf_cnt} conflicting item(s)."
            )

        # Case 5: Weak Consensus Fallback
        return ConsensusResult(
            consensus_level="WEAK_CONSENSUS",
            consensus_score=0.30,
            disease_risk_tier=risk_tier,
            explanation=f"Weak consensus: Limited supporting evidence ({supp_cnt} supporting) and low prediction confidence delta ({confidence_delta:.2f})."
        )
