"""
Schemas for SHAP Explainability Module.
Defines standardized Pydantic models for feature attributions and disease explanations.
"""

from typing import List, Any, Optional
from pydantic import BaseModel, Field


class FeatureAttribution(BaseModel):
    """Represents SHAP feature attribution for a single feature."""
    feature_name: str = Field(..., description="Name of the input feature")
    raw_value: Any = Field(..., description="Raw input value provided for patient")
    shap_value: float = Field(..., description="SHAP attribution value for positive disease outcome")
    impact_direction: str = Field(..., description="Impact direction: 'increases_risk', 'decreases_risk', or 'neutral'")
    rank: int = Field(..., description="1-based importance rank based on absolute SHAP value")


class SHAPExplanation(BaseModel):
    """Complete SHAP explanation payload for a single disease evaluation."""
    disease: str = Field(..., description="Name of target disease model")
    prediction_probability: float = Field(..., description="Predicted probability for positive class")
    base_value: float = Field(..., description="SHAP base value / expected model output")
    top_attributions: List[FeatureAttribution] = Field(..., description="Top N most impactful features")
    all_attributions: List[FeatureAttribution] = Field(..., description="Complete list of all feature attributions sorted by impact rank")
