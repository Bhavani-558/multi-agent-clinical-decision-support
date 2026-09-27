"""
Fusion Agent Module for CDSS.
Provides FusionAgent class wrapping FusionEngine for decision/evidence fusion,
confidence assessment, and decision-support classification.
"""

from typing import Dict, Any, Optional
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reasoning.schemas import ReasoningOutput
from src.fusion.schemas import ClinicalDecisionOutput
from src.fusion.fusion_engine import FusionEngine


class FusionAgent:
    """
    Fusion Agent responsible for consuming Module 5 Reasoning outputs,
    computing fused confidence scores, assigning Decision-Support Classifications,
    and producing structured ClinicalDecisionOutput payloads.
    """

    def __init__(self, engine: Optional[FusionEngine] = None):
        self.engine = engine or FusionEngine()

    def evaluate(
        self,
        reasoning: ReasoningOutput,
        shap_explanation: Optional[Dict[str, Any]] = None,
        graph_evidence: Optional[KnowledgeGraphEvidence] = None
    ) -> ClinicalDecisionOutput:
        """Evaluates decision fusion and produces ClinicalDecisionOutput."""
        return self.engine.evaluate_fusion(
            reasoning=reasoning,
            shap_explanation=shap_explanation,
            graph_evidence=graph_evidence
        )


__all__ = ["FusionAgent", "FusionEngine"]
