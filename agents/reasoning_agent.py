"""
Reasoning Agent Module for CDSS.
Provides ReasoningAgent class wrapping ReasoningEngine for multi-source reasoning,
contradiction analysis, evidence consensus, and reproducible trust score evaluation.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence, EvidenceAgentResponse
from src.reasoning.schemas import ReasoningOutput
from src.reasoning.reasoning_engine import ReasoningEngine


class ReasoningAgent:
    """
    Reasoning Agent responsible for contradiction detection, consensus determination,
    and reproducible trust scoring across clinical predictions, SHAP attributions, and PrimeKG evidence.
    """

    def __init__(self, engine: Optional[ReasoningEngine] = None):
        self.engine = engine or ReasoningEngine()

    def evaluate(
        self,
        model_id: str,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        shap_explanation: Optional[Dict[str, Any]] = None
    ) -> ReasoningOutput:
        """Evaluates clinical evidence, consensus, and trust score."""
        return self.engine.evaluate_reasoning(
            model_id=model_id,
            prediction=prediction,
            graph_evidence=graph_evidence,
            shap_explanation=shap_explanation
        )

    def evaluate_evidence_payload(self, evidence_response: EvidenceAgentResponse) -> ReasoningOutput:
        """Evaluates clinical evidence, consensus, and trust score from EvidenceAgentResponse."""
        return self.engine.evaluate_evidence_response(evidence_response)


__all__ = ["ReasoningAgent", "ReasoningEngine"]
