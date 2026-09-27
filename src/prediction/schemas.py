"""
Pydantic schemas for the CDSS Prediction Module.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class FeatureValue(BaseModel):
    """Container for individual feature value with optional raw vs encoded representations."""
    name: str
    value: Any


class UnresolvedMappingInfo(BaseModel):
    """Details regarding input categorical features that require numeric encoding not stored in artifact."""
    disease: str
    feature_name: str
    received_value: Any
    message: str = (
        "Artifact expects numeric pre-encoded input for this feature. "
        "Original string-to-numeric mapping dictionary is not stored in the .pkl file."
    )


class DiseasePrediction(BaseModel):
    """Result structure for a single disease model prediction."""
    disease: str
    model_filename: str
    is_multiclass: bool = False
    predicted_class: Union[int, str]
    predicted_label: Optional[str] = None
    probability: float = Field(..., description="Probability of positive class or max class")
    class_probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Probability distribution across all target classes"
    )
    status: str = Field(
        default="SUCCESS",
        description="SUCCESS, UNRESOLVED_MAPPING_REQUIRED, or ERROR"
    )
    unresolved_mappings: List[UnresolvedMappingInfo] = Field(default_factory=list)
    error_message: Optional[str] = None


class BatchPredictionResult(BaseModel):
    """Container for predictions across multiple diseases."""
    patient_id: Optional[str] = None
    predictions: Dict[str, DiseasePrediction] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)
