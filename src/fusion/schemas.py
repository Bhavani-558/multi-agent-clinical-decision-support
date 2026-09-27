"""
Pydantic Schemas for Module 6 — Decision / Fusion Layer.
Defines structured representations for Decision-Support Classifications, Fused Confidence Breakdown,
Uncertainty Flags, and the 5-field ClinicalDecisionOutput.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DecisionSupportClassification(str, Enum):
    """
    Mutually exclusive decision-support categories.
    Clarifies system provides clinical decision support without autonomous prescribing.
    """
    HIGH_RISK_DECISION_SUPPORT = "HIGH_RISK_DECISION_SUPPORT"
    LOW_RISK_DECISION_SUPPORT = "LOW_RISK_DECISION_SUPPORT"
    CONTRADICTION_FLAG = "CONTRADICTION_FLAG"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DEGRADED_CONFIDENCE = "DEGRADED_CONFIDENCE"


class FusedConfidenceBreakdown(BaseModel):
    """Breakdown of fused confidence score components and system safety cap status."""
    overall_fused_score: float = Field(..., description="Final fused confidence score bounded between 0.0 and 1.0")
    pre_cap_fused_score: Optional[float] = Field(None, description="Fused score before any contradiction safety ceiling")
    trust_component: float = Field(..., description="Contribution of Module 5 trust score (0.40 * trust_score)")
    consensus_component: float = Field(..., description="Contribution of Module 5 consensus score (0.35 * consensus_score)")
    model_confidence_component: float = Field(..., description="Contribution of model decisiveness factor (0.25 * confidence_factor)")
    is_capped_by_contradiction: bool = Field(default=False, description="True if score was capped at 0.50 due to contradictory evidence")
    cap_documentation: Optional[str] = Field(None, description="Documentation explaining system safety cap (non-clinical software rule)")


class UncertaintyFlag(BaseModel):
    """Represents a specific uncertainty or missing evidence caveat."""
    flag_code: str = Field(..., description="Identifier code for uncertainty type")
    description: str = Field(..., description="Human-readable description of uncertainty")
    severity: str = Field(default="MEDIUM", description="Severity level: HIGH, MEDIUM, LOW")


class ClinicalDecisionOutput(BaseModel):
    """
    Final structured output for Module 6 — Decision / Fusion Layer.
    Maintains 5 distinct top-level fields for clear clinical separation.
    """
    disease: str = Field(..., description="Target disease model identifier")
    model_id: str = Field(..., description="Model ID")
    decision_classification: DecisionSupportClassification = Field(..., description="Decision-support category")
    fused_confidence: FusedConfidenceBreakdown = Field(..., description="Fused confidence score and breakdown")
    
    # 5 Separate Top-Level Fields
    prediction_summary: Dict[str, Any] = Field(..., description="Field 1: ML Model Prediction Summary")
    shap_summary: Optional[Dict[str, Any]] = Field(None, description="Field 2: SHAP Explanation Summary")
    evidence_summary: Dict[str, Any] = Field(..., description="Field 3: Biomedical Graph Evidence Summary")
    trust_and_consensus_summary: Dict[str, Any] = Field(..., description="Field 4: Module 5 Trust & Consensus Summary")
    decision_interpretation: str = Field(..., description="Field 5: Decision-Support Rationale & Guidance")
    
    uncertainty_flags: List[UncertaintyFlag] = Field(default_factory=list, description="List of uncertainty/caveat flags")
