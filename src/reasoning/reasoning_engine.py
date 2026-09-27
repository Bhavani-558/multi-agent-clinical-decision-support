"""
Reasoning Engine for Module 5.
Orchestrates evidence categorization, contradiction detection, consensus analysis,
trust score calculation, and structured reasoning synthesis.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence, EvidenceAgentResponse
from src.reasoning.schemas import ReasoningOutput
from src.reasoning.contradiction_detector import ContradictionDetector
from src.reasoning.consensus_analyzer import ConsensusAnalyzer
from src.reasoning.trust_calculator import TrustCalculator


class ReasoningEngine:
    """
    Core engine for multi-source clinical reasoning, contradiction analysis, consensus, and trust scoring.
    """

    def __init__(
        self,
        detector: Optional[ContradictionDetector] = None,
        analyzer: Optional[ConsensusAnalyzer] = None,
        calculator: Optional[TrustCalculator] = None
    ):
        self.detector = detector or ContradictionDetector()
        self.analyzer = analyzer or ConsensusAnalyzer()
        self.calculator = calculator or TrustCalculator()

    def generate_reasoning_summary(
        self,
        model_id: str,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        contradiction: Any,
        consensus: Any,
        trust: Any
    ) -> str:
        """
        Synthesizes a structured clinical reasoning summary text.
        """
        prob = prediction.get("probability", prediction.get("positive_probability", 0.0))
        mapped_node = graph_evidence.mapped_graph_node or "Unresolved"

        lines = [
            f"=== CDSS Reasoning & Trust Evaluation Report: {model_id.upper()} ===",
            f"Mapped Graph Entity: '{mapped_node}'",
            f"Model Predicted Risk: {prob * 100:.1f}% [{consensus.disease_risk_tier}]",
            "",
            "1. EVIDENCE BREAKDOWN & CONTRADICTION ANALYSIS:",
            f"   - Supporting Evidence Items: {contradiction.supporting_count}",
            f"   - Conflicting Evidence Items: {contradiction.conflicting_count}",
            f"   - Neutral / Contextual Items: {contradiction.neutral_count}",
            f"   - Summary: {contradiction.contradiction_summary}",
            "",
            "2. CONSENSUS EVALUATION:",
            f"   - Consensus Level: {consensus.consensus_level}",
            f"   - Consensus Score: {consensus.consensus_score:.4f}",
            f"   - Rationale: {consensus.explanation}",
            "",
            "3. TRUST SCORE BREAKDOWN:",
            f"   - Overall Trust Score: {trust.overall_trust_score:.4f} ({trust.shap_status})",
            f"   - Model Confidence Factor: {trust.confidence_factor:.4f}",
            f"   - Graph Evidence Factor: {trust.graph_evidence_factor:.4f}",
            f"   - Evidence Consistency Factor: {trust.evidence_consistency_factor:.4f}"
        ]

        if trust.shap_alignment_factor is not None:
            lines.append(f"   - SHAP Alignment Factor: {trust.shap_alignment_factor:.4f}")

        lines.append(f"\n{trust.logic_documentation}")

        return "\n".join(lines)

    def evaluate_reasoning(
        self,
        model_id: str,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        shap_explanation: Optional[Dict[str, Any]] = None
    ) -> ReasoningOutput:
        """
        Executes full reasoning pipeline for prediction, graph evidence, and optional SHAP attributions.
        """
        # Step 1: Categorize evidence & detect contradictions
        contradiction_analysis = self.detector.analyze_evidence(
            prediction=prediction,
            graph_evidence=graph_evidence,
            shap_explanation=shap_explanation
        )

        # Step 2: Evaluate consensus
        consensus_result = self.analyzer.evaluate_consensus(
            prediction=prediction,
            graph_evidence=graph_evidence,
            contradiction_analysis=contradiction_analysis,
            shap_explanation=shap_explanation
        )

        # Step 3: Calculate reproducible trust score
        trust_result = self.calculator.calculate_trust_score(
            prediction=prediction,
            graph_evidence=graph_evidence,
            contradiction_analysis=contradiction_analysis,
            shap_explanation=shap_explanation
        )

        # Step 4: Synthesize text summary
        summary = self.generate_reasoning_summary(
            model_id=model_id,
            prediction=prediction,
            graph_evidence=graph_evidence,
            contradiction=contradiction_analysis,
            consensus=consensus_result,
            trust=trust_result
        )

        prediction_summary = {
            "model_id": model_id,
            "predicted_class": prediction.get("predicted_class", -1),
            "predicted_label": prediction.get("predicted_label"),
            "probability": prediction.get("probability", prediction.get("positive_probability", 0.0)),
            "class_probabilities": prediction.get("class_probabilities", {}),
            "probability_class_label": (
                list(prediction.get("class_probabilities", {}).keys())[1]
                if len(prediction.get("class_probabilities", {})) >= 2 else None
            ),
            "status": prediction.get("status", "SUCCESS")
        }

        return ReasoningOutput(
            disease=model_id,
            model_id=model_id,
            prediction_summary=prediction_summary,
            contradiction_analysis=contradiction_analysis,
            supporting_evidence=contradiction_analysis.supporting_evidence,
            conflicting_evidence=contradiction_analysis.conflicting_evidence,
            neutral_evidence=contradiction_analysis.neutral_evidence,
            consensus_result=consensus_result,
            trust_score=trust_result,
            reasoning_summary=summary
        )

    def evaluate_evidence_response(self, evidence_response: EvidenceAgentResponse) -> ReasoningOutput:
        """
        Evaluates reasoning directly from an EvidenceAgentResponse payload.
        """
        return self.evaluate_reasoning(
            model_id=evidence_response.model_id,
            prediction=evidence_response.prediction,
            graph_evidence=evidence_response.graph_evidence,
            shap_explanation=evidence_response.shap_explanation
        )
