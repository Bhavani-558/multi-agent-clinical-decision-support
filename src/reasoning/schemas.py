"""
Pydantic Schemas for Module 5 — Reasoning / Trust Layer.
Defines structured representations for evidence categorization, contradiction analysis,
consensus evaluation, trust score breakdown, and structured reasoning outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvidenceCategoryItem(BaseModel):
    """Represents a single evaluated item of evidence (graph triple or SHAP attribution)."""
    category: str = Field(..., description="Entity category: phenotype, gene_biomarker, drug, exposure, comorbidity, shap_attribution")
    entity_name: str = Field(..., description="Name of the clinical entity or feature")
    relation_or_impact: str = Field(..., description="Relation type (e.g. indication, contraindication) or SHAP impact direction")
    detail: str = Field(..., description="Human-readable description of the evidence item")
    is_supporting: bool = Field(default=False, description="True if evidence supports disease risk/finding")
    is_conflicting: bool = Field(default=False, description="True if evidence conflicts with disease risk/finding")
    is_neutral: bool = Field(default=False, description="True if evidence is contextual/neutral")


class ContradictionAnalysis(BaseModel):
    """Detailed breakdown of supporting, conflicting, and neutral evidence."""
    supporting_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    conflicting_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    neutral_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    supporting_count: int = 0
    conflicting_count: int = 0
    neutral_count: int = 0
    has_contradictions: bool = Field(default=False, description="True ONLY when explicit conflicting items exist")
    contradiction_summary: str = Field(..., description="Summary of evidence breakdown and conflicting findings")


class ConsensusResult(BaseModel):
    """Result of deterministic evidence consensus evaluation."""
    consensus_level: str = Field(..., description="STRONG_CONSENSUS, MODERATE_CONSENSUS, WEAK_CONSENSUS, CONTRADICTORY_CONSENSUS, or INSUFFICIENT_EVIDENCE")
    consensus_score: float = Field(..., description="Deterministic consensus score between 0.0 and 1.0")
    disease_risk_tier: str = Field(..., description="HIGH_RISK or LOW_RISK based on prediction probability threshold 0.5")
    explanation: str = Field(..., description="Detailed rationale explaining the consensus determination")


class TrustScoreResult(BaseModel):
    """Reproducible Trust Score breakdown and weight configurations."""
    overall_trust_score: float = Field(..., description="Final bounded trust score between 0.0 and 1.0")
    confidence_factor: float = Field(..., description="Model decisiveness factor 2 * |prob - 0.5|")
    shap_alignment_factor: Optional[float] = Field(None, description="Ratio of aligned SHAP feature attributions")
    graph_evidence_factor: float = Field(..., description="Volume and resolution factor of PrimeKG graph triples")
    evidence_consistency_factor: float = Field(..., description="Consistency factor: 1.0 - (conflicting / total_evaluable)")
    shap_status: str = Field(default="INCLUDED", description="INCLUDED or OMITTED_RENORMALIZED")
    weights_used: Dict[str, float] = Field(default_factory=dict, description="Active normalized weights applied")
    logic_documentation: str = Field(..., description="Step-by-step documentation of trust score calculation")


class ReasoningOutput(BaseModel):
    """Structured output payload for Module 5 — Reasoning / Trust Layer."""
    disease: str = Field(..., description="Target disease model identifier")
    model_id: str = Field(..., description="Model ID")
    prediction_summary: Dict[str, Any] = Field(..., description="Summary of ML model prediction")
    contradiction_analysis: ContradictionAnalysis = Field(..., description="Contradiction and evidence breakdown")
    supporting_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    conflicting_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    neutral_evidence: List[EvidenceCategoryItem] = Field(default_factory=list)
    consensus_result: ConsensusResult = Field(..., description="Consensus evaluation result")
    trust_score: TrustScoreResult = Field(..., description="Trust score evaluation result")
    reasoning_summary: str = Field(..., description="Comprehensive clinical reasoning synthesis text")
