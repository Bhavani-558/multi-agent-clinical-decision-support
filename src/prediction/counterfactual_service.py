"""
Generic Counterfactual What-If Simulation Service for Clinical Decision Support.
Enables clinicians to simulate how altering specific patient biomarkers / clinical features
impacts disease prediction probabilities and clinical detection status.

STRICT SAFETY & INTEGRITY CONSTRAINTS:
1. Reuses existing, frozen preprocessor and XGBoost model artifacts directly.
2. Does NOT modify or retrain any model.
3. Does NOT alter or save over the patient's actual medical record.
4. Input validation: Rejects unknown features, missing features, and out-of-bounds values.
5. Immutability: Treats original patient features as immutable.
6. Governed Lock: Chronic Liver Disease is explicitly locked until corrected model approval:
   "What-If Simulation for Chronic Liver Disease is temporarily locked pending approval of the corrected model."
7. Verified Live Models enforce universal polarity:
   - class 1 -> Disease Presence -> DETECTED -> HIGH_RISK
   - class 0 -> Disease Absence -> NOT DETECTED -> LOW_RISK
8. Machine Learning Simulation Disclaimer is always attached to outputs.
"""

from typing import Dict, Any, List, Optional, Tuple
import copy
import math
import numpy as np
import pandas as pd

from src.prediction.model_loader import ModelLoader, ModelMetadata
from src.prediction.mapping_registry import map_patient_features, CATEGORICAL_MAPPINGS, DISEASE_TARGET_LABEL_MAPPINGS

SIMULATION_DISCLAIMER = (
    "Model-based simulation only. It does not represent a guaranteed medical outcome or treatment recommendation."
)

CHRONIC_LIVER_LOCK_MESSAGE = (
    "What-If Simulation for Chronic Liver Disease is temporarily locked pending approval of the corrected model."
)

# Explicit governance registry
LOCKED_DISEASES: Dict[str, str] = {
    "Chronic_liver": CHRONIC_LIVER_LOCK_MESSAGE
}

# Verified live disease models where Class 1 = Presence (DETECTED) and Class 0 = Absence (NOT DETECTED)
VERIFIED_LIVE_DISEASES: List[str] = [
    "diabetes",
    "heart_disease",
    "Stroke"
]

HEART_DISEASE_CATEGORICAL_ENCODING: Dict[str, Dict[Any, int]] = {
    "Sex": {
        "Female": 0, "Male": 1,
        "female": 0, "male": 1,
        "F": 0, "M": 1, "f": 0, "m": 1,
        "0": 0, "1": 1, 0: 0, 1: 1
    },
    "Chest_pain_type": {
        "Typical Angina": 1, "Atypical Angina": 2, "Non-anginal Pain": 3, "Asymptomatic": 4,
        "Typical angina": 1, "Atypical angina": 2, "Non-anginal pain": 3,
        "typical angina": 1, "atypical angina": 2, "non-anginal pain": 3, "asymptomatic": 4,
        "1": 1, "2": 2, "3": 3, "4": 4, 1: 1, 2: 2, 3: 3, 4: 4
    },
    "FBS_over_120": {
        "No (<= 120 mg/dl)": 0, "Yes (> 120 mg/dl)": 1,
        "No": 0, "Yes": 1, "no": 0, "yes": 1,
        "False": 0, "True": 1, "false": 0, "true": 1,
        "<= 120": 0, "> 120": 1, "<=120": 0, ">120": 1,
        "0": 0, "1": 1, 0: 0, 1: 1
    },
    "EKG_results": {
        "Normal": 0, "ST-T Wave Abnormality": 1, "Left Ventricular Hypertrophy": 2,
        "normal": 0, "st-t wave abnormality": 1, "left ventricular hypertrophy": 2,
        "ST-T wave abnormality": 1, "Left ventricular hypertrophy": 2,
        "0": 0, "1": 1, "2": 2, 0: 0, 1: 1, 2: 2
    },
    "Exercise_angina": {
        "No": 0, "Yes": 1, "no": 0, "yes": 1,
        "False": 0, "True": 1, "false": 0, "true": 1,
        "0": 0, "1": 1, 0: 0, 1: 1
    },
    "Slope_of_ST": {
        "Upsloping": 1, "Flat": 2, "Downsloping": 3,
        "upsloping": 1, "flat": 2, "downsloping": 3,
        "1": 1, "2": 2, "3": 3, 1: 1, 2: 2, 3: 3
    },
    "Thallium": {
        "Normal": 3, "Fixed Defect": 6, "Reversible Defect": 7,
        "normal": 3, "fixed defect": 6, "reversible defect": 7,
        "Fixed defect": 6, "Reversible defect": 7,
        "3": 3, "6": 6, "7": 7, 3: 3, 6: 6, 7: 7
    }
}


class CounterfactualService:
    """
    Generic simulation engine executing counterfactual what-if evaluations
    using trained disease pipelines without modifying model states or patient records.
    """

    def __init__(self, loader: Optional[ModelLoader] = None):
        self.loader = loader or ModelLoader()

    def get_supported_diseases(self) -> List[str]:
        """Returns verified disease models currently enabled for live what-if simulation."""
        return list(VERIFIED_LIVE_DISEASES)

    def is_disease_locked(self, disease: str) -> Tuple[bool, Optional[str]]:
        """Checks if a disease model is locked by governance rules."""
        if disease in LOCKED_DISEASES:
            return True, LOCKED_DISEASES[disease]
        return False, None

    def validate_features(self, disease: str, features: Dict[str, Any], meta: ModelMetadata) -> None:
        """
        Validates feature presence, names, and value domains against disease schema.
        Raises ValueError for unknown features, missing features, or invalid values.
        """
        expected_cols = set(meta.feature_names)
        provided_cols = set(features.keys())

        # Check for unknown feature keys
        unknown = provided_cols - expected_cols
        if unknown:
            raise ValueError(
                f"Unknown feature(s) for {disease}: {sorted(list(unknown))}. Allowed features: {meta.feature_names}"
            )

        # Check for missing required features
        missing = expected_cols - provided_cols
        if missing:
            raise ValueError(f"Missing required feature(s) for {disease}: {sorted(list(missing))}")

        # Domain and type validation
        registered_cat = CATEGORICAL_MAPPINGS.get(disease, {})

        for feat in meta.feature_names:
            val = features[feat]
            if val is None:
                raise ValueError(f"Feature '{feat}' cannot be null.")

            # Validate Heart Disease specific categorical encodings
            if disease == "heart_disease" and feat in HEART_DISEASE_CATEGORICAL_ENCODING:
                enc = HEART_DISEASE_CATEGORICAL_ENCODING[feat]
                is_valid = (val in enc) or (str(val) in enc) or (val in enc.values())
                if not is_valid:
                    try:
                        if int(float(str(val))) in enc.values():
                            is_valid = True
                    except (ValueError, TypeError):
                        pass
                if not is_valid:
                    raise ValueError(
                        f"Invalid value for categorical feature '{feat}': '{val}'. "
                        f"Allowed values: {sorted(list(str(k) for k in enc.keys() if isinstance(k, str)))}"
                    )
            # Validate categorical features if registered in generic registry
            elif feat in registered_cat:
                valid_options = set(registered_cat[feat].keys())
                # Also accept integer mapped codes (0, 1, 2)
                valid_codes = set(registered_cat[feat].values())
                is_valid = (val in valid_options) or (val in valid_codes) or (str(val) in valid_options)
                if not is_valid:
                    try:
                        if int(float(str(val))) in valid_codes:
                            is_valid = True
                    except (ValueError, TypeError):
                        pass
                if not is_valid:
                    raise ValueError(
                        f"Invalid value for categorical feature '{feat}': '{val}'. "
                        f"Allowed values: {sorted(list(str(k) for k in valid_options))}"
                    )
            elif feat in meta.internal_categorical_cols:
                if str(val).lower() not in ["yes", "no", "1", "0", 1, 0]:
                    raise ValueError(f"Invalid value for feature '{feat}': '{val}'. Allowed: 'yes', 'no'.")
            elif feat.lower() in ["sex", "gender"]:
                if str(val).lower() not in ["male", "female", "m", "f", "1", "0", 1, 0]:
                    raise ValueError(f"Invalid value for '{feat}': '{val}'. Allowed: 'male', 'female', 1, 0.")
            else:
                # Numeric feature validation
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Feature '{feat}' must be a numeric value, received: '{val}'")

                if math.isnan(num_val) or math.isinf(num_val):
                    raise ValueError(f"Feature '{feat}' contains invalid numeric value (NaN or Inf).")

                if num_val < 0:
                    raise ValueError(f"Feature '{feat}' cannot be negative (received {num_val}).")

                if feat.lower() in ["age"] and (num_val < 1 or num_val > 125):
                    raise ValueError(f"Age must be between 1 and 125 (received {num_val}).")

    def _execute_pipeline_inference(
        self, disease: str, features: Dict[str, Any], meta: ModelMetadata
    ) -> Dict[str, Any]:
        """
        Runs the exact frozen preprocessing pipeline and XGBoost estimator inference.
        Enforces verified class polarity:
        - class 1 -> Disease Presence -> DETECTED -> HIGH_RISK
        - class 0 -> Disease Absence -> NOT DETECTED -> LOW_RISK
        """
        # Map verified categorical strings (e.g. 'female' -> 0)
        mapped_data = map_patient_features(disease, features)

        # Apply Heart Disease categorical encoding if applicable
        if disease == "heart_disease":
            for feat, enc in HEART_DISEASE_CATEGORICAL_ENCODING.items():
                if feat in mapped_data:
                    raw_v = mapped_data[feat]
                    if raw_v in enc:
                        mapped_data[feat] = enc[raw_v]
                    elif str(raw_v) in enc:
                        mapped_data[feat] = enc[str(raw_v)]
                    else:
                        try:
                            num_v = int(float(str(raw_v)))
                            if num_v in enc.values():
                                mapped_data[feat] = num_v
                        except (ValueError, TypeError):
                            pass

        # Build single-row DataFrame aligned strictly to model's expected feature names
        df_input = pd.DataFrame([{col: mapped_data[col] for col in meta.feature_names}])

        # Ensure all columns intended for numeric processing are numeric types
        for col in meta.feature_names:
            try:
                df_input[col] = pd.to_numeric(df_input[col])
            except Exception:
                pass

        # Apply existing trained preprocessor
        X_preprocessed = meta.preprocessor.transform(df_input)

        # Execute estimator predict_proba
        if hasattr(meta.estimator, "predict_proba"):
            probs = meta.estimator.predict_proba(X_preprocessed)[0]
        else:
            raw_pred = meta.estimator.predict(X_preprocessed)[0]
            probs = np.array([1.0 - float(raw_pred), float(raw_pred)])

        # Universal verified polarity for binary disease models
        # probs[1] = P(Disease Presence | X), probs[0] = P(Disease Absence | X)
        pos_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
        neg_prob = 1.0 - pos_prob

        target_labels = DISEASE_TARGET_LABEL_MAPPINGS.get(disease, {"0": "Absence", "1": "Presence"})
        label_pos = target_labels.get("1", "Presence")
        label_neg = target_labels.get("0", "Absence")

        if pos_prob >= 0.50:
            predicted_class = 1
            predicted_label = label_pos
            clinical_status = "DETECTED"
            risk_tier = "HIGH_RISK"
        else:
            predicted_class = 0
            predicted_label = label_neg
            clinical_status = "NOT DETECTED"
            risk_tier = "LOW_RISK"

        return {
            "probability": round(pos_prob, 4),
            "probability_formatted": f"{pos_prob * 100:.2f}%",
            "predicted_class": predicted_class,
            "predicted_label": predicted_label,
            "clinical_status": clinical_status,
            "risk_tier": risk_tier,
            "class_probabilities": {
                label_neg: round(neg_prob, 4),
                label_pos: round(pos_prob, 4)
            }
        }

    def simulate_what_if(
        self,
        disease: str,
        original_features: Dict[str, Any],
        modified_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates counterfactual changes between original patient features and modified features.
        Keeps original features immutable, validates all inputs, enforces governance locks,
        and computes the probability delta.
        """
        # Step 1: Check governance lock
        is_locked, lock_reason = self.is_disease_locked(disease)
        if is_locked:
            raise ValueError(lock_reason)

        # Step 2: Validate disease model is supported
        supported = self.get_supported_diseases()
        if disease not in supported:
            raise ValueError(
                f"What-If Analysis is currently enabled for verified models: {supported}. "
                f"Disease '{disease}' is not available for simulation."
            )

        meta = self.loader.get_model(disease)

        # Step 3: Enforce immutability via deep copy
        orig_copy = copy.deepcopy(original_features)
        mod_copy = copy.deepcopy(modified_features)

        # Step 4: Validate inputs against disease schema
        self.validate_features(disease, orig_copy, meta)
        self.validate_features(disease, mod_copy, meta)

        # Step 5: Run model inference (exact existing pipeline, zero retraining)
        orig_res = self._execute_pipeline_inference(disease, orig_copy, meta)
        cf_res = self._execute_pipeline_inference(disease, mod_copy, meta)

        # Step 6: Identify modified features & compute individual deltas
        diffs = []
        for feat in meta.feature_names:
            val_orig = orig_copy[feat]
            val_mod = mod_copy[feat]

            is_diff = False
            delta_val = None

            try:
                num_orig = float(val_orig)
                num_mod = float(val_mod)
                if not math.isclose(num_orig, num_mod, rel_tol=1e-5, abs_tol=1e-5):
                    is_diff = True
                    delta_val = round(num_mod - num_orig, 4)
            except (ValueError, TypeError):
                if str(val_orig).strip().lower() != str(val_mod).strip().lower():
                    is_diff = True

            if is_diff:
                diffs.append({
                    "feature": feat,
                    "label": feat.replace("_", " ").title(),
                    "original_value": val_orig,
                    "counterfactual_value": val_mod,
                    "delta": delta_val
                })

        # Step 7: Calculate probability delta
        p_orig = orig_res["probability"]
        p_cf = cf_res["probability"]
        prob_change = round(p_cf - p_orig, 4)
        pct_points = round((p_cf - p_orig) * 100, 2)

        if pct_points > 0:
            direction = "increase"
        elif pct_points < 0:
            direction = "decrease"
        else:
            direction = "unchanged"

        prediction_changed = (orig_res["predicted_class"] != cf_res["predicted_class"])

        return {
            "status": "success",
            "disease": disease,
            "simulation_disclaimer": SIMULATION_DISCLAIMER,
            "original": orig_res,
            "counterfactual": cf_res,
            "delta": {
                "probability_change": prob_change,
                "percentage_points_change": pct_points,
                "direction": direction,
                "prediction_changed": prediction_changed
            },
            "modified_features": diffs,
            "total_modified_features": len(diffs)
        }
