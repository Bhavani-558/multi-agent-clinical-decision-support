"""
SHAP Explainer Service for CDSS.
Provides feature attributions using shap.TreeExplainer across all 10 trained disease XGBoost models.
"""

import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List, Optional, Tuple
from src.prediction.model_loader import ModelLoader, ModelMetadata
from src.prediction.mapping_registry import map_patient_features
from src.explainability.schemas import FeatureAttribution, SHAPExplanation


class SHAPExplainerService:
    """
    Service responsible for generating SHAP feature explanations for disease prediction models.
    """

    def __init__(self, loader: Optional[ModelLoader] = None):
        self.loader = loader or ModelLoader()
        self._explainers: Dict[str, shap.TreeExplainer] = {}

    def get_explainer(self, disease: str) -> shap.TreeExplainer:
        """Get or initialize cached shap.TreeExplainer for a disease model."""
        if disease not in self._explainers:
            meta = self.loader.get_model(disease)
            # TreeExplainer is initialized directly on the trained XGBoost estimator
            self._explainers[disease] = shap.TreeExplainer(meta.estimator)
        return self._explainers[disease]

    def explain_prediction(
        self,
        disease: str,
        patient_features: Dict[str, Any],
        top_n: int = 5
    ) -> SHAPExplanation:
        """
        Generate SHAP explanation payload for a single patient and disease model.
        """
        meta = self.loader.get_model(disease)
        explainer = self.get_explainer(disease)

        # 1. Apply verified categorical mappings (for diabetes, Stroke, Chronic_liver)
        mapped_features = map_patient_features(disease, patient_features)

        # 2. Build aligned DataFrame matching original expected feature names
        df_input = pd.DataFrame([mapped_features])
        for col in meta.feature_names:
            if col not in df_input.columns:
                df_input[col] = np.nan
        df_input = df_input[meta.feature_names]

        # 3. Transform features via model's saved preprocessor
        X_proc = meta.preprocessor.transform(df_input)

        # 4. Predict probability for positive class
        proba_arr = meta.estimator.predict_proba(X_proc)
        if proba_arr.shape[1] > 1:
            pred_prob = float(proba_arr[0, 1])
        else:
            pred_prob = float(proba_arr[0, 0])

        # 5. Calculate SHAP values
        raw_shap = explainer.shap_values(X_proc)
        
        # Handle SHAP output shapes across library versions
        if isinstance(raw_shap, list):
            # List of arrays per class -> take class 1 (positive class)
            shap_vec = raw_shap[1][0] if len(raw_shap) > 1 else raw_shap[0][0]
        elif isinstance(raw_shap, np.ndarray):
            if raw_shap.ndim == 3:  # (n_samples, n_features, n_classes)
                shap_vec = raw_shap[0, :, 1] if raw_shap.shape[2] > 1 else raw_shap[0, :, 0]
            elif raw_shap.ndim == 2:  # (n_samples, n_features)
                shap_vec = raw_shap[0, :]
            elif raw_shap.ndim == 1:
                shap_vec = raw_shap
            else:
                shap_vec = raw_shap.flatten()
        else:
            shap_vec = np.array(raw_shap).flatten()

        # 6. Extract base value (expected output)
        base_val = explainer.expected_value
        if isinstance(base_val, (list, np.ndarray)):
            if len(base_val) > 1:
                base_val = float(base_val[1])
            else:
                base_val = float(base_val[0])
        else:
            base_val = float(base_val)

        # 7. Resolve feature names & raw values
        if meta.has_internal_onehot and hasattr(meta.preprocessor, "get_feature_names_out"):
            out_names = list(meta.preprocessor.get_feature_names_out())
            resolved_names = [name.replace("numeric__", "").replace("categorical__", "").replace("cat__", "") for name in out_names]
            # Map raw values: if OneHot output column, check original raw value
            raw_vals_list = []
            for name in out_names:
                parts = name.split("__")
                col_name = parts[-1] if len(parts) > 1 else name
                if "_" in col_name and not col_name in patient_features:
                    orig_col = col_name.split("_")[0]
                    raw_vals_list.append(patient_features.get(orig_col, np.nan))
                else:
                    raw_vals_list.append(patient_features.get(col_name, np.nan))
        else:
            resolved_names = meta.feature_names
            raw_vals_list = [patient_features.get(col, np.nan) for col in meta.feature_names]

        # 8. Build list of FeatureAttribution objects
        attributions: List[FeatureAttribution] = []
        for feat_name, raw_v, s_val in zip(resolved_names, raw_vals_list, shap_vec):
            s_float = float(s_val)
            if s_float > 1e-6:
                direction = "increases_risk"
            elif s_float < -1e-6:
                direction = "decreases_risk"
            else:
                direction = "neutral"

            attributions.append(
                FeatureAttribution(
                    feature_name=feat_name,
                    raw_value=raw_v if pd.notna(raw_v) else "Missing",
                    shap_value=round(s_float, 6),
                    impact_direction=direction,
                    rank=0  # Placeholder, assigned below
                )
            )

        # 9. Sort by absolute SHAP impact magnitude and assign ranks
        attributions.sort(key=lambda a: abs(a.shap_value), reverse=True)
        for rank_idx, attr in enumerate(attributions, start=1):
            attr.rank = rank_idx

        top_attributions = attributions[:top_n]

        return SHAPExplanation(
            disease=disease,
            prediction_probability=round(pred_prob, 6),
            base_value=round(base_val, 6),
            top_attributions=top_attributions,
            all_attributions=attributions
        )
