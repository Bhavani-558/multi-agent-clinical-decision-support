"""
Model Loader for CDSS Prediction Module.
Handles safe loading, compatibility patching, and metadata extraction for all 10 disease XGBoost models.
"""

import os
import joblib
import pickle
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sklearn
import sklearn.compose._column_transformer as ct

# Apply compatibility patch for scikit-learn version differences when loading serialized models
if not hasattr(ct, '_RemainderColsList'):
    class _RemainderColsList(list):
        pass
    ct._RemainderColsList = _RemainderColsList


class ModelMetadata:
    """Encapsulates all extracted metadata and objects for a single disease model artifact."""
    def __init__(
        self,
        disease: str,
        folder_name: str,
        file_name: str,
        file_path: str,
        container_type: str,
        preprocessor: Any,
        estimator: Any,
        feature_names: List[str],
        target_classes: List[Any],
        label_encoder: Optional[Any] = None,
        class_names: Optional[List[str]] = None,
        scale_pos_weight: Optional[float] = None,
        has_internal_onehot: bool = False,
        internal_categorical_cols: Optional[List[str]] = None,
        unresolved_categorical_cols: Optional[List[str]] = None
    ):
        self.disease = disease
        self.folder_name = folder_name
        self.file_name = file_name
        self.file_path = file_path
        self.container_type = container_type
        self.preprocessor = preprocessor
        self.estimator = estimator
        self.feature_names = feature_names
        self.target_classes = target_classes
        self.label_encoder = label_encoder
        self.class_names = class_names
        self.scale_pos_weight = scale_pos_weight
        self.has_internal_onehot = has_internal_onehot
        self.internal_categorical_cols = internal_categorical_cols or []
        self.unresolved_categorical_cols = unresolved_categorical_cols or []


class ModelLoader:
    """
    Loader and registry for disease prediction model artifacts.
    """
    DISEASE_MODEL_MAP = {
        "anemia": ("anemia", "anemia_xgboost_pipeline.pkl"),
        "B_cancer": ("B_cancer", "breast_cancer_xgboost_pipeline (1).pkl"),
        "Chronic_liver": ("Chronic_liver", "chronic_liver_xgboost_pipeline.pkl"),
        "diabetes": ("diabetes", "diabetes_xgboost_pipeline.pkl"),
        "heart_disease": ("heart_disease", "heart_disease_xgboost_pipeline (1).pkl"),
        "Hepatitis": ("Hepatitis", "hepatitis_xgboost_pipeline.pkl"),
        "Kidney": ("Kidney", "kidney_xgboost_pipeline (1).pkl"),
        "lung_cancer": ("lung_cancer", "lung_cancer_xgboost_pipeline.pkl"),
        "Parkinsons": ("Parkinsons", "parkinsons_xgboost_pipeline.pkl"),
        "Stroke": ("Stroke", "stroke_balanced_xgboost_pipeline.pkl")
    }

    # Features that are semantically categorical but require pre-encoded numeric values
    # (because no string-to-numeric mapping dictionary is stored in the artifact)
    UNRESOLVED_CATEGORICAL_MAP = {
        "Chronic_liver": ["Gender"],
        "diabetes": ["gender", "smoking_history"],
        "heart_disease": ["Sex", "Chest_pain_type", "FBS_over_120", "EKG_results", "Exercise_angina", "Slope_of_ST", "Thallium"],
        "Kidney": ["Rbc", "Htn"],
        "Stroke": ["gender", "ever_married", "work_type", "Residence_type", "smoking_status"]
    }

    def __init__(self, models_root_dir: str = r"d:\MultiAgent_CDSS\models"):
        self.models_root_dir = models_root_dir
        self._loaded_models: Dict[str, ModelMetadata] = {}

    def get_model(self, disease: str) -> ModelMetadata:
        """Get or load a model for a specific disease by name."""
        if disease not in self.DISEASE_MODEL_MAP:
            raise ValueError(f"Unknown disease '{disease}'. Available: {list(self.DISEASE_MODEL_MAP.keys())}")
            
        if disease not in self._loaded_models:
            self._loaded_models[disease] = self._load_model_artifact(disease)
            
        return self._loaded_models[disease]

    def load_all_models(self) -> Dict[str, ModelMetadata]:
        """Load and cache all 10 disease models."""
        for disease in self.DISEASE_MODEL_MAP.keys():
            self.get_model(disease)
        return self._loaded_models

    def _load_model_artifact(self, disease: str) -> ModelMetadata:
        folder_name, file_name = self.DISEASE_MODEL_MAP[disease]
        file_path = os.path.join(self.models_root_dir, folder_name, file_name)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Model file not found at: {file_path}")
            
        # Load artifact safely using joblib with pickle fallback
        try:
            obj = joblib.load(file_path)
        except Exception:
            with open(file_path, 'rb') as f:
                obj = pickle.load(f)

        container_type = type(obj).__name__
        preprocessor = None
        estimator = None
        label_encoder = None
        class_names = None
        feature_names = []
        target_classes = []
        scale_pos_weight = None
        has_internal_onehot = False
        internal_categorical_cols = []

        if isinstance(obj, dict):
            preprocessor = obj.get("preprocessor")
            estimator = obj.get("model")
            label_encoder = obj.get("label_encoder")
            if obj.get("class_names") is not None:
                class_names = list(obj["class_names"])
            if obj.get("feature_names") is not None:
                feature_names = list(obj["feature_names"])
            if "scale_pos_weight" in obj:
                scale_pos_weight = float(obj["scale_pos_weight"])
        elif hasattr(obj, "steps"):
            preprocessor = obj.named_steps.get("preprocessor")
            estimator = obj.named_steps.get("model", obj.steps[-1][1])

        # Extract feature names if not present in dict
        if not feature_names and preprocessor is not None:
            if hasattr(preprocessor, "feature_names_in_"):
                feature_names = list(preprocessor.feature_names_in_)

        # Extract target classes & estimator params
        if estimator is not None:
            if hasattr(estimator, "classes_"):
                target_classes = list(estimator.classes_)
            if hasattr(estimator, "get_params") and scale_pos_weight is None:
                params = estimator.get_params()
                if "scale_pos_weight" in params:
                    scale_pos_weight = params["scale_pos_weight"]

        # Check ColumnTransformer for internal OneHotEncoder
        if preprocessor is not None:
            t_list = getattr(preprocessor, "transformers_", getattr(preprocessor, "transformers", []))
            for t in t_list:
                t_name, t_trans, t_cols = t[0], t[1], t[2]
                cols_list = list(t_cols) if hasattr(t_cols, '__iter__') and not isinstance(t_cols, str) else [t_cols]
                if "onehot" in str(t_trans).lower() or "encoder" in str(t_trans).lower():
                    has_internal_onehot = True
                    internal_categorical_cols.extend(cols_list)

        unresolved_categorical_cols = self.UNRESOLVED_CATEGORICAL_MAP.get(disease, [])

        # Apply scikit-learn version compatibility fixes on preprocessor components
        if preprocessor is not None:
            self._fix_sklearn_compat(preprocessor)

        return ModelMetadata(
            disease=disease,
            folder_name=folder_name,
            file_name=file_name,
            file_path=file_path,
            container_type=container_type,
            preprocessor=preprocessor,
            estimator=estimator,
            feature_names=feature_names,
            target_classes=target_classes,
            label_encoder=label_encoder,
            class_names=class_names,
            scale_pos_weight=scale_pos_weight,
            has_internal_onehot=has_internal_onehot,
            internal_categorical_cols=internal_categorical_cols,
            unresolved_categorical_cols=unresolved_categorical_cols
        )

    def _fix_sklearn_compat(self, preprocessor: Any):
        """Recursively fix missing attributes on unpickled sklearn components for version compatibility."""
        if hasattr(preprocessor, "steps"):
            for _, step_obj in preprocessor.steps:
                self._fix_sklearn_compat(step_obj)
        elif hasattr(preprocessor, "transformers_") or hasattr(preprocessor, "transformers"):
            t_list = getattr(preprocessor, "transformers_", getattr(preprocessor, "transformers", []))
            for t in t_list:
                t_trans = t[1]
                self._fix_sklearn_compat(t_trans)
        else:
            # Check if SimpleImputer
            if type(preprocessor).__name__ == "SimpleImputer":
                if not hasattr(preprocessor, "_fill_dtype"):
                    preprocessor._fill_dtype = getattr(preprocessor, "_fit_dtype", None)

