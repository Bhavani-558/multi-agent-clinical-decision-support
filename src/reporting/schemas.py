"""
Pydantic Schemas for Module 7 — Reporting Layer.
Defines structured representations for report sections, clinical decision support reports,
and multi-format outputs (Markdown, Text, JSON).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class ClinicalReportSection(BaseModel):
    """Represents a discrete section within the clinical decision-support report."""
    section_id: str = Field(..., description="Unique section identifier code")
    title: str = Field(..., description="Human-readable section title")
    summary_text: str = Field(..., description="Textual summary or narrative for this section")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Key quantitative metrics for the section")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Structured items (e.g. SHAP attributions, triples)")


class ClinicalDecisionReport(BaseModel):
    """
    Structured Clinical Decision Support Report.
    Consumes Module 6 ClinicalDecisionOutput directly without score recalculation.
    Provides structured sections alongside formatted Markdown, Text, and JSON representations.
    """
    report_id: str = Field(default_factory=lambda: f"REP-{uuid.uuid4().hex[:8].upper()}", description="Unique report identifier")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Report generation timestamp")

    disease: str = Field(..., description="Target disease model identifier")
    model_id: str = Field(..., description="Model ID")
    decision_classification: str = Field(..., description="Module 6 Decision-Support Classification")
    fused_confidence_score: float = Field(..., description="Preserved fused confidence score")
    is_capped_by_contradiction: bool = Field(default=False, description="Flag indicating system safety cap applied")
    overall_trust_score: float = Field(..., description="Preserved Module 5 Trust Score")
    consensus_level: str = Field(..., description="Preserved Module 5 Consensus Level")
    llm_explanation: Optional[str] = Field(default=None, description="Groq LLM Clinical Explanation")
    
    # Structured Report Content
    sections: List[ClinicalReportSection] = Field(default_factory=list, description="List of 10 dynamic report sections")
    uncertainty_flags: List[Dict[str, Any]] = Field(default_factory=list, description="List of active system uncertainty warnings")
    
    # Formatted Representations
    markdown_report: str = Field(..., description="Formatted Markdown string representation")
    text_report: str = Field(..., description="Formatted Plain Text string representation")
    json_payload: Dict[str, Any] = Field(default_factory=dict, description="Full JSON-serializable audit payload")
