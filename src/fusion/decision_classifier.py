"""
Decision-Support Classifier for Module 6.
Evaluates ReasoningOutput to assign deterministic DecisionSupportClassification tiers
and generate uncertainty flags.
"""

from typing import List, Dict, Any, Tuple
from src.reasoning.schemas import ReasoningOutput
from src.fusion.schemas import DecisionSupportClassification, UncertaintyFlag


class DecisionClassifier:
    """
    Classifies clinical evaluation payloads into 5 mutually exclusive Decision-Support Tiers.
    Explicitly provides decision support for clinicians without autonomous prescribing/diagnosing.
    """

    def classify(self, reasoning: ReasoningOutput) -> Tuple[DecisionSupportClassification, List[UncertaintyFlag]]:
        """
        Determines the decision-support classification and collects uncertainty flags.
        """
        prob = reasoning.prediction_summary.get("probability", 0.5)
        conf_analysis = reasoning.contradiction_analysis
        consensus = reasoning.consensus_result
        trust = reasoning.trust_score

        flags: List[UncertaintyFlag] = []

        # 1. Collect Uncertainty Flags
        if trust.shap_status == "OMITTED_RENORMALIZED":
            flags.append(UncertaintyFlag(
                flag_code="FLAG_MISSING_SHAP",
                description="SHAP attributions omitted; weights dynamically renormalized",
                severity="MEDIUM"
            ))

        if trust.graph_evidence_factor == 0.0 or conf_analysis.supporting_count == 0:
            flags.append(UncertaintyFlag(
                flag_code="FLAG_ZERO_GRAPH_TRIPLES",
                description="No supporting PrimeKG graph evidence triples found",
                severity="HIGH" if conf_analysis.neutral_count == 0 else "MEDIUM"
            ))

        if conf_analysis.has_contradictions:
            flags.append(UncertaintyFlag(
                flag_code="FLAG_CONTRADICTORY_EVIDENCE",
                description=f"{conf_analysis.conflicting_count} conflicting evidence item(s) detected",
                severity="HIGH"
            ))

        if trust.confidence_factor < 0.30:  # |prob - 0.5| < 0.15
            flags.append(UncertaintyFlag(
                flag_code="FLAG_LOW_MODEL_DECISIVENESS",
                description=f"Model prediction probability ({prob:.3f}) is near the decision boundary (0.50)",
                severity="MEDIUM"
            ))

        # 2. Determine Classification Category (in priority order)

        # Tier 1: Contradiction Flag
        if conf_analysis.has_contradictions and (
            consensus.consensus_level == "CONTRADICTORY_CONSENSUS" or
            trust.evidence_consistency_factor < 0.60 or
            conf_analysis.conflicting_count > conf_analysis.supporting_count
        ):
            return DecisionSupportClassification.CONTRADICTION_FLAG, flags

        # Tier 2: Insufficient Evidence
        if (
            consensus.consensus_level == "INSUFFICIENT_EVIDENCE" or
            (trust.graph_evidence_factor == 0.0 and conf_analysis.supporting_count == 0) or
            trust.overall_trust_score < 0.45
        ):
            return DecisionSupportClassification.INSUFFICIENT_EVIDENCE, flags

        # Tier 3: Degraded Confidence
        if (
            trust.shap_status == "OMITTED_RENORMALIZED" or
            trust.confidence_factor < 0.30
        ) and not conf_analysis.has_contradictions:
            return DecisionSupportClassification.DEGRADED_CONFIDENCE, flags

        # Tier 4: High Risk Decision Support
        if prob >= 0.50 and trust.overall_trust_score >= 0.60:
            return DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT, flags

        # Tier 5: Low Risk Decision Support
        if prob < 0.50 and trust.overall_trust_score >= 0.60:
            return DecisionSupportClassification.LOW_RISK_DECISION_SUPPORT, flags

        # Fallback / Boundary handling
        if prob >= 0.50:
            return DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT, flags
        else:
            return DecisionSupportClassification.LOW_RISK_DECISION_SUPPORT, flags
