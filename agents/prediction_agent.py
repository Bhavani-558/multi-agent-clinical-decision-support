"""
Prediction Agent Module for CDSS.
Responsible for orchestrating disease prediction models and multi-disease evaluation.
"""

from typing import Dict, Any, List, Optional
from src.prediction.predictor import DiseasePredictor
from src.prediction.model_loader import ModelLoader
from src.prediction.schemas import DiseasePrediction, BatchPredictionResult


class PredictionAgent:
    """
    Agent responsible for coordinating predictions across all 10 trained disease models.
    """

    def __init__(self, models_root_dir: Optional[str] = None):
        if models_root_dir is None:
            models_root_dir = str(Path(__file__).resolve().parents[1] / "models")
        self.loader = ModelLoader(models_root_dir=models_root_dir)
        self.predictor = DiseasePredictor(loader=self.loader)

    def get_supported_diseases(self) -> List[str]:
        """Return list of supported disease models."""
        return list(self.loader.DISEASE_MODEL_MAP.keys())

    def get_disease_schema(self, disease: str) -> Dict[str, Any]:
        """Retrieve expected input features and metadata for a disease model."""
        meta = self.loader.get_model(disease)
        return {
            "disease": disease,
            "feature_names": meta.feature_names,
            "n_features": len(meta.feature_names),
            "unresolved_categorical_cols": meta.unresolved_categorical_cols,
            "has_internal_onehot": meta.has_internal_onehot,
            "internal_categorical_cols": meta.internal_categorical_cols,
            "target_classes": meta.target_classes,
            "class_names": meta.class_names or (list(meta.label_encoder.classes_) if meta.label_encoder else [])
        }

    def predict_single_disease(self, disease: str, features: Dict[str, Any]) -> DiseasePrediction:
        """Run prediction for a single specified disease."""
        return self.predictor.predict_disease(disease, features)

    def evaluate_patient(
        self,
        patient_profile: Dict[str, Any],
        diseases: Optional[List[str]] = None,
        patient_id: Optional[str] = None
    ) -> BatchPredictionResult:
        """
        Evaluate a patient profile against specified disease models (or all 10 by default).
        """
        target_diseases = diseases or self.get_supported_diseases()
        predictions: Dict[str, DiseasePrediction] = {}
        successful_count = 0
        unresolved_count = 0
        error_count = 0

        for disease in target_diseases:
            pred = self.predictor.predict_disease(disease, patient_profile)
            predictions[disease] = pred
            if pred.status == "SUCCESS":
                successful_count += 1
            elif pred.status == "UNRESOLVED_MAPPING_REQUIRED":
                unresolved_count += 1
            else:
                error_count += 1

        summary = {
            "total_evaluated": len(target_diseases),
            "successful_predictions": successful_count,
            "unresolved_mappings_required": unresolved_count,
            "errors": error_count
        }

        return BatchPredictionResult(
            patient_id=patient_id,
            predictions=predictions,
            summary=summary
        )
