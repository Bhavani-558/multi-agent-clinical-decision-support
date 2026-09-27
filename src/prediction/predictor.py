"""
Core Predictor Engine for CDSS.
Performs feature alignment, schema validation, preprocessing execution, and inference.
"""

from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from src.prediction.model_loader import ModelLoader, ModelMetadata
from src.prediction.mapping_registry import map_patient_features, resolve_human_label
from src.prediction.schemas import DiseasePrediction, UnresolvedMappingInfo



class DiseasePredictor:
    """
    Inference Engine for executing predictions across all 10 CDSS XGBoost models.
    """

    def __init__(self, loader: Optional[ModelLoader] = None):
        self.loader = loader or ModelLoader()

    def predict_disease(self, disease: str, input_data: Dict[str, Any]) -> DiseasePrediction:
        """
        Execute prediction for a single disease using provided feature dictionary.
        """
        try:
            meta = self.loader.get_model(disease)
        except Exception as e:
            return DiseasePrediction(
                disease=disease,
                model_filename="UNKNOWN",
                predicted_class=-1,
                probability=0.0,
                status="ERROR",
                error_message=f"Failed to load model for {disease}: {str(e)}"
            )

        # Step 0: Apply verified string-to-numeric categorical encodings from registry
        try:
            mapped_data = map_patient_features(disease, input_data)
        except Exception as map_err:
            return DiseasePrediction(
                disease=disease,
                model_filename=meta.file_name,
                predicted_class=-1,
                probability=0.0,
                status="ERROR",
                error_message=f"Feature encoding error: {str(map_err)}"
            )

        # Step 1: Check for missing features
        missing_features = [col for col in meta.feature_names if col not in mapped_data]
        if missing_features:
            return DiseasePrediction(
                disease=disease,
                model_filename=meta.file_name,
                predicted_class=-1,
                probability=0.0,
                status="ERROR",
                error_message=f"Missing required input features: {missing_features}"
            )

        # Step 2: Check for unresolved categorical string inputs
        unresolved_list: List[UnresolvedMappingInfo] = []
        for col in meta.unresolved_categorical_cols:
            val = mapped_data.get(col)
            if isinstance(val, str):
                unresolved_list.append(
                    UnresolvedMappingInfo(
                        disease=disease,
                        feature_name=col,
                        received_value=val,
                        message=(
                            f"Feature '{col}' received string value '{val}'. Model artifact requires "
                            f"numeric pre-encoded input. Feature string-to-numeric mapping dictionary is not stored in the .pkl artifact."
                        )
                    )
                )

        if unresolved_list:
            return DiseasePrediction(
                disease=disease,
                model_filename=meta.file_name,
                predicted_class=-1,
                probability=0.0,
                status="UNRESOLVED_MAPPING_REQUIRED",
                unresolved_mappings=unresolved_list,
                error_message=f"Unresolved categorical string mappings required for: {[u.feature_name for u in unresolved_list]}"
            )

        # Step 3: Construct DataFrame with exact feature names and order
        df_input = pd.DataFrame([{col: mapped_data[col] for col in meta.feature_names}])

        # Step 4: Preprocess input
        try:
            X_preprocessed = meta.preprocessor.transform(df_input)
        except Exception as prep_err:
            return DiseasePrediction(
                disease=disease,
                model_filename=meta.file_name,
                predicted_class=-1,
                probability=0.0,
                status="ERROR",
                error_message=f"Preprocessing error: {str(prep_err)}"
            )

        # Step 5: Execute Model Predict / Predict Proba
        try:
            if hasattr(meta.estimator, "predict_proba"):
                probs = meta.estimator.predict_proba(X_preprocessed)[0]
            else:
                preds = meta.estimator.predict(X_preprocessed)[0]
                probs = np.array([1.0 - float(preds), float(preds)])
        except Exception as pred_err:
            return DiseasePrediction(
                disease=disease,
                model_filename=meta.file_name,
                predicted_class=-1,
                probability=0.0,
                status="ERROR",
                error_message=f"Inference error: {str(pred_err)}"
            )

        # Step 6: Process Prediction Outputs & Class Probabilities
        is_multiclass = (len(probs) > 2) or (disease == "anemia")
        class_probs_map: Dict[str, float] = {}

        if is_multiclass:
            predicted_idx = int(np.argmax(probs))
            top_prob = float(probs[predicted_idx])
            
            # Target class label resolution
            if meta.class_names and len(meta.class_names) == len(probs):
                class_labels = meta.class_names
            elif meta.label_encoder and hasattr(meta.label_encoder, "classes_") and len(meta.label_encoder.classes_) == len(probs):
                class_labels = [str(c) for c in meta.label_encoder.classes_]
            else:
                class_labels = [str(i) for i in range(len(probs))]

            for idx, label in enumerate(class_labels):
                human_lbl = resolve_human_label(disease, label)
                class_probs_map[human_lbl] = round(float(probs[idx]), 4)

            predicted_class = predicted_idx
            raw_label = class_labels[predicted_idx] if predicted_idx < len(class_labels) else str(predicted_idx)
            predicted_label = resolve_human_label(disease, raw_label)

        else:
            # Binary classification
            pos_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
            predicted_idx = 1 if pos_prob >= 0.5 else 0
            top_prob = pos_prob

            if meta.class_names and len(meta.class_names) >= 2:
                label_neg, label_pos = str(meta.class_names[0]), str(meta.class_names[1])
            elif meta.label_encoder and hasattr(meta.label_encoder, "classes_") and len(meta.label_encoder.classes_) >= 2:
                label_neg, label_pos = str(meta.label_encoder.classes_[0]), str(meta.label_encoder.classes_[1])
            else:
                label_neg, label_pos = "0", "1"

            label_neg = resolve_human_label(disease, label_neg)
            label_pos = resolve_human_label(disease, label_pos)

            class_probs_map[label_neg] = round(1.0 - pos_prob, 4)
            class_probs_map[label_pos] = round(pos_prob, 4)

            predicted_class = predicted_idx
            predicted_label = label_pos if predicted_idx == 1 else label_neg

        return DiseasePrediction(
            disease=disease,
            model_filename=meta.file_name,
            is_multiclass=is_multiclass,
            predicted_class=predicted_class,
            predicted_label=predicted_label,
            probability=round(top_prob, 4),
            class_probabilities=class_probs_map,
            status="SUCCESS"
        )

