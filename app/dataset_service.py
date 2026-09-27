"""
Dataset Service for Module 8 UI - LOAD DATA Feature.
Manages local dataset loading, cleaning, row previewing, and feature extraction
from data/raw according to the verified DISEASE_DATASET_CONFIG.
No model files, preprocessing pipelines, or predictions are modified here.
"""

import os
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class DatasetService:
    """
    Service for loading and preparing dataset rows from data/raw
    for the 10 CDSS disease models.
    """

    DISEASE_DATASET_CONFIG = {
        "anemia": {
            "disease_name": "Anemia",
            "file_name": "diagnosed_cbc_data_v4.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "Diagnosis",
            "id_cols": [],
            "feature_cols": [
                "WBC", "LYMp", "NEUTp", "LYMn", "NEUTn", "RBC",
                "HGB", "HCT", "MCV", "MCH", "MCHC", "PLT", "PDW", "PCT"
            ]
        },
        "B_cancer": {
            "disease_name": "Breast Cancer",
            "file_name": "BreastCancer_Data.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "diagnosis",
            "id_cols": ["id", "Unnamed: 32"],
            "feature_cols": [
                "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
                "compactness_mean", "concavity_mean", "concave_points_mean", "symmetry_mean", "fractal_dimension_mean",
                "radius_se", "texture_se", "perimeter_se", "area_se", "smoothness_se",
                "compactness_se", "concavity_se", "concave_points_se", "symmetry_se", "fractal_dimension_se",
                "radius_worst", "texture_worst", "perimeter_worst", "area_worst", "smoothness_worst",
                "compactness_worst", "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
            ]
        },
        "Chronic_liver": {
            "disease_name": "Chronic Liver",
            "file_name": "indian_liver_patient.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "Dataset",
            "id_cols": [],
            "feature_cols": [
                "Age", "Gender", "Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase",
                "Alamine_Aminotransferase", "Aspartate_Aminotransferase", "Total_Protiens",
                "Albumin", "Albumin_and_Globulin_Ratio"
            ]
        },
        "diabetes": {
            "disease_name": "Diabetes",
            "file_name": "diabetes_prediction_dataset.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "diabetes",
            "id_cols": [],
            "feature_cols": [
                "gender", "age", "hypertension", "heart_disease",
                "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level"
            ]
        },
        "heart_disease": {
            "disease_name": "Heart Disease",
            "file_name": "Heart_Disease_Prediction.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "Heart_Disease",
            "id_cols": [],
            "feature_cols": [
                "Age", "Sex", "Chest_pain_type", "BP", "Cholesterol", "FBS_over_120",
                "EKG_results", "Max_HR", "Exercise_angina", "ST_depression",
                "Slope_of_ST", "Number_of_vessels_fluro", "Thallium"
            ]
        },
        "Hepatitis": {
            "disease_name": "Hepatitis",
            "file_name": "hepatitis.data",
            "format": "uci_data",
            "has_header": False,
            "na_values": ["?"],
            "raw_column_order": [
                "Class", "age", "sex", "steroid", "antivirals", "fatigue", "malaise",
                "anorexia", "liver_big", "liver_firm", "spleen_palpable", "spiders",
                "ascites", "varices", "bilirubin", "alk_phosphate", "sgot", "albumin",
                "protime", "histology"
            ],
            "target_col": "Class",
            "id_cols": [],
            "feature_cols": [
                "age", "sex", "steroid", "antivirals", "fatigue", "malaise", "anorexia",
                "liver_big", "liver_firm", "spleen_palpable", "spiders", "ascites",
                "varices", "bilirubin", "alk_phosphate", "sgot", "albumin", "protime", "histology"
            ]
        },
        "Kidney": {
            "disease_name": "Kidney",
            "file_name": "Chronic_Kidney.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "Class",
            "id_cols": [],
            "feature_cols": [
                "Bp", "Sg", "Al", "Su", "Rbc", "Bu", "Sc", "Sod", "Pot", "Hemo", "Wbcc", "Rbcc", "Htn"
            ]
        },
        "lung_cancer": {
            "disease_name": "Lung Cancer",
            "file_name": "survey lung cancer.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "LUNG_CANCER",
            "id_cols": [],
            "feature_cols": [
                "GENDER", "AGE", "SMOKING", "YELLOW_FINGERS", "ANXIETY", "PEER_PRESSURE",
                "CHRONIC_DISEASE", "FATIGUE", "ALLERGY", "WHEEZING", "ALCOHOL_CONSUMING",
                "COUGHING", "SHORTNESS_OF_BREATH", "SWALLOWING_DIFFICULTY", "CHEST_PAIN"
            ]
        },
        "Parkinsons": {
            "disease_name": "Parkinson's",
            "file_name": "parkinsons.data",
            "format": "csv",
            "has_header": True,
            "target_col": "status",
            "id_cols": ["name"],
            "feature_cols": [
                "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)", "MDVP:Jitter(%)",
                "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
                "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5",
                "MDVP:APQ", "Shimmer:DDA", "NHR", "HNR", "RPDE", "DFA",
                "spread1", "spread2", "D2", "PPE"
            ]
        },
        "Stroke": {
            "disease_name": "Stroke",
            "file_name": "healthcare-dataset-stroke-data.csv",
            "format": "csv",
            "has_header": True,
            "target_col": "stroke",
            "id_cols": ["id"],
            "feature_cols": [
                "gender", "age", "hypertension", "heart_disease", "ever_married",
                "work_type", "Residence_type", "avg_glucose_level", "bmi", "smoking_status"
            ]
        }
    }

    @classmethod
    def normalize_disease_key(cls, disease: str) -> Optional[str]:
        """Normalizes any disease string/slug to the verified config key."""
        if not disease:
            return None
        if disease in cls.DISEASE_DATASET_CONFIG:
            return disease
        norm = str(disease).strip().lower().replace("-", "_").replace(" ", "_")
        for key in cls.DISEASE_DATASET_CONFIG:
            k_norm = key.lower().replace("-", "_").replace(" ", "_")
            if norm == k_norm:
                return key
            dname_norm = cls.DISEASE_DATASET_CONFIG[key]["disease_name"].lower().replace("-", "_").replace(" ", "_")
            if norm == dname_norm:
                return key
        return None

    @classmethod
    def get_display_name(cls, disease: str) -> str:
        """Returns clean human-readable name for error messages."""
        norm = cls.normalize_disease_key(disease)
        if norm and norm in cls.DISEASE_DATASET_CONFIG:
            return cls.DISEASE_DATASET_CONFIG[norm]["disease_name"]
        clean = str(disease or "").replace("_", " ").replace("-", " ").strip()
        return clean.title() if clean else "Unknown Disease"

    def __init__(self, raw_dir: Optional[str] = None):
        if raw_dir is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            self.raw_dir = os.path.join(project_root, "data", "raw")
        else:
            self.raw_dir = raw_dir
        self._dataset_cache: Dict[str, pd.DataFrame] = {}

    def _load_raw_df(self, disease: str) -> pd.DataFrame:
        """Loads and returns the cleaned DataFrame for the given disease."""
        norm_key = self.normalize_disease_key(disease)
        if not norm_key:
            display_name = self.get_display_name(disease)
            raise FileNotFoundError(f"Dataset not found for {display_name}.")

        if norm_key in self._dataset_cache:
            return self._dataset_cache[norm_key]

        cfg = self.DISEASE_DATASET_CONFIG[norm_key]
        file_path = os.path.join(self.raw_dir, cfg["file_name"])

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset not found for {cfg['disease_name']}.")

        if cfg["format"] == "uci_data":
            df = pd.read_csv(
                file_path,
                header=None,
                names=cfg["raw_column_order"],
                na_values=cfg.get("na_values", ["?"])
            )
        else:
            df = pd.read_csv(file_path)

        # Standard column name normalization: strip whitespace and replace internal spaces with underscores
        df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]

        # Handle disease-specific target name variants
        if norm_key == "heart_disease" and "Heart_Disease" not in df.columns:
            for alt in ["Heart_Disease", "Heart_disease", "heart_disease"]:
                if alt in df.columns:
                    df.rename(columns={alt: "Heart_Disease"}, inplace=True)
                    break

        # Safe imputation of missing values
        # Numeric columns -> median; categorical/object -> mode or fallback
        for col in df.columns:
            if df[col].isna().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
                else:
                    mode_series = df[col].mode()
                    mode_val = mode_series.iloc[0] if len(mode_series) > 0 else "Unknown"
                    df[col] = df[col].fillna(mode_val)

        # Ensure Breast Cancer drops Unnamed columns
        if norm_key == "B_cancer":
            unnamed_cols = [c for c in df.columns if c.lower().startswith("unnamed")]
            if unnamed_cols:
                df.drop(columns=unnamed_cols, inplace=True, errors="ignore")

        self._dataset_cache[norm_key] = df
        return df

    def get_dataset_info(self, disease: str) -> Dict[str, Any]:
        """Returns metadata about the dataset (total records, target classes, filename)."""
        norm_key = self.normalize_disease_key(disease)
        if not norm_key:
            display_name = self.get_display_name(disease)
            raise FileNotFoundError(f"Dataset not found for {display_name}.")

        cfg = self.DISEASE_DATASET_CONFIG[norm_key]
        df = self._load_raw_df(norm_key)
        target_col = cfg["target_col"]
        target_vals = []
        if target_col in df.columns:
            target_vals = [str(v) for v in df[target_col].dropna().unique().tolist()[:10]]

        return {
            "disease": disease,
            "disease_name": cfg["disease_name"],
            "file_name": cfg["file_name"],
            "total_rows": len(df),
            "feature_count": len(cfg["feature_cols"]),
            "target_col": target_col,
            "target_classes": target_vals
        }

    def get_dataset_preview(
        self,
        disease: str,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        target_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns a paginated preview list of dataset rows for doctor selection in the UI modal.
        """
        cfg = self.DISEASE_DATASET_CONFIG.get(disease)
        if not cfg:
            raise ValueError(f"Unknown disease: {disease}")

        df = self._load_raw_df(disease)
        target_col = cfg["target_col"]
        feature_cols = cfg["feature_cols"]

        # Optional filtering by ground truth
        filtered_indices = df.index
        if target_filter and target_col in df.columns:
            filtered_indices = df[df[target_col].astype(str).str.lower() == target_filter.lower()].index

        # Search across preview rows if query provided
        if search:
            query = search.lower().strip()
            matched_indices = []
            for idx in filtered_indices:
                row_str = " ".join([str(df.at[idx, c]) for c in feature_cols[:6] if c in df.columns])
                if target_col in df.columns:
                    row_str += " " + str(df.at[idx, target_col])
                if query in row_str.lower():
                    matched_indices.append(idx)
            filtered_indices = pd.Index(matched_indices)

        total_matching = len(filtered_indices)
        sliced_indices = filtered_indices[offset:offset + limit]

        rows = []
        for idx in sliced_indices:
            row_series = df.loc[idx]
            ground_truth_raw = row_series.get(target_col, "N/A")

            # Human-readable ground truth representation
            ground_truth_label = self._format_ground_truth(disease, ground_truth_raw)

            # Compact feature preview (first 4 features) for table display
            preview_snippet = {}
            for col in feature_cols[:4]:
                if col in row_series:
                    v = row_series[col]
                    preview_snippet[col] = round(v, 2) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

            rows.append({
                "row_index": int(idx),
                "display_label": f"Dataset Row: {int(idx) + 1}",
                "ground_truth_raw": str(ground_truth_raw),
                "ground_truth_label": ground_truth_label,
                "preview_features": preview_snippet
            })

        return {
            "disease": disease,
            "disease_name": cfg["disease_name"],
            "file_name": cfg["file_name"],
            "total_rows": len(df),
            "total_matching": total_matching,
            "limit": limit,
            "offset": offset,
            "rows": rows
        }

    def get_dataset_row(self, disease: str, row_index: int) -> Dict[str, Any]:
        """
        Retrieves an exact row from the local dataset, cleans it, strips target & identifier columns,
        and returns the mapped features strictly matching the existing patient form inputs.
        row_index is 0-indexed.
        """
        norm_key = self.normalize_disease_key(disease)
        if not norm_key:
            display_name = self.get_display_name(disease)
            raise FileNotFoundError(f"Dataset not found for {display_name}.")

        cfg = self.DISEASE_DATASET_CONFIG[norm_key]
        df = self._load_raw_df(norm_key)
        total_rows = len(df)
        if row_index < 0:
            raise IndexError("Row number must be at least 1.")
        if row_index >= total_rows:
            raise IndexError(f"Row number cannot exceed {total_rows} for this dataset.")

        row_series = df.iloc[row_index]
        target_col = cfg["target_col"]
        ground_truth_raw = row_series.get(target_col, "N/A")
        ground_truth_label = self._format_ground_truth(norm_key, ground_truth_raw)

        # Extract only the verified model feature columns
        cleaned_features: Dict[str, Any] = {}
        for col in cfg["feature_cols"]:
            if col not in row_series:
                continue

            val = row_series[col]

            # Convert numpy types to native Python types
            if pd.isna(val):
                val = 0.0
            elif isinstance(val, (np.integer, int)) and not isinstance(val, bool):
                val = int(val)
            elif isinstance(val, (np.floating, float)):
                val = float(val)
            elif isinstance(val, (np.bool_, bool)):
                val = bool(val)

            # Disease-specific value formatting for form dropdowns
            cleaned_features[col] = self._format_feature_value_for_form(norm_key, col, val)

        return {
            "disease": norm_key,
            "disease_name": cfg["disease_name"],
            "row_index": int(row_index),
            "display_label": f"Dataset Row: {int(row_index) + 1}",
            "file_name": cfg["file_name"],
            "ground_truth_raw": str(ground_truth_raw),
            "ground_truth_label": ground_truth_label,
            "features": cleaned_features
        }

    def get_dataset_row_1based(self, disease: str, row_number: int) -> Dict[str, Any]:
        """
        Retrieves an exact row from the local dataset using 1-based indexing (Row 1, Row 2, etc.)
        Validates row number bounds and returns cleaned features.
        """
        norm_key = self.normalize_disease_key(disease)
        if not norm_key:
            display_name = self.get_display_name(disease)
            raise FileNotFoundError(f"Dataset not found for {display_name}.")

        cfg = self.DISEASE_DATASET_CONFIG[norm_key]
        df = self._load_raw_df(norm_key)
        total_rows = len(df)
        if row_number < 1:
            raise IndexError("Row number must be at least 1.")
        if row_number > total_rows:
            raise IndexError(f"Row number cannot exceed {total_rows} for this dataset.")

        return self.get_dataset_row(norm_key, row_number - 1)

    def _format_feature_value_for_form(self, disease: str, feature: str, value: Any) -> Any:
        """
        Maps raw dataset values to matching UI form field options (e.g. Hepatitis 1/2 to 'male'/'female' and 'no'/'yes').
        Natively numerical features pass through as clean floats/ints.
        """
        if disease == "Hepatitis":
            # Hepatitis dataset uses 1=male, 2=female for sex; 1=no, 2=yes for symptoms
            if feature == "sex":
                try:
                    num = int(float(value))
                    return "male" if num == 1 else "female"
                except Exception:
                    return str(value).lower()
            elif feature in [
                "steroid", "antivirals", "fatigue", "malaise", "anorexia",
                "liver_big", "liver_firm", "spleen_palpable", "spiders",
                "ascites", "varices", "histology"
            ]:
                try:
                    num = int(float(value))
                    return "no" if num == 1 else "yes"
                except Exception:
                    return str(value).lower()

        elif disease == "Chronic_liver" and feature == "Gender":
            # Dataset has "Male" / "Female"
            return str(value).strip().lower()

        elif disease == "lung_cancer" and feature == "GENDER":
            # Dataset has "M" / "F"
            return str(value).strip().upper()

        elif disease in ["diabetes", "Stroke"]:
            # String categoricals like "Female", "never", "Private" pass as string matching dropdown options
            if isinstance(value, str):
                return value.strip()

        # For numeric values, round clean floats if whole
        if isinstance(value, float) and value.is_integer():
            return int(value)

        return value

    def _format_ground_truth(self, disease: str, raw_target: Any) -> str:
        """Returns human-readable ground-truth outcome for display in the row selection modal only."""
        if pd.isna(raw_target):
            return "Unknown"

        val_str = str(raw_target).strip()

        if disease == "diabetes":
            return "Presence (Diabetes)" if val_str in ["1", "1.0", "yes", "true"] else "Absence (Non-Diabetic)"
        elif disease == "Stroke":
            return "Presence (Stroke)" if val_str in ["1", "1.0", "yes", "true"] else "Absence (No Stroke)"
        elif disease == "B_cancer":
            return "Malignant (M)" if val_str.upper() in ["M", "1", "1.0"] else "Benign (B)"
        elif disease == "heart_disease":
            return "Presence" if "pres" in val_str.lower() or val_str in ["1", "1.0"] else "Absence"
        elif disease == "Chronic_liver":
            return "Liver Patient (1)" if val_str in ["1", "1.0"] else "Non-Liver Patient (2)"
        elif disease == "Kidney":
            return "ckd" if "ckd" in val_str.lower() or val_str in ["1", "1.0"] else "notckd"
        elif disease == "lung_cancer":
            return "YES (Lung Cancer)" if val_str.upper() in ["YES", "1", "1.0"] else "NO (No Cancer)"
        elif disease == "Parkinsons":
            return "Presence (Parkinson's)" if val_str in ["1", "1.0"] else "Healthy (0)"
        elif disease == "Hepatitis":
            return "Live" if val_str in ["2", "2.0", "live"] else "Die"
        elif disease == "anemia":
            return val_str

        return val_str
