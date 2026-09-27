"""
Categorical Mapping Registry for CDSS Prediction and Explainability Modules.
Contains strictly verified string-to-numeric mappings for models requiring input encoding.
No mappings are invented for natively numeric models (e.g. Heart Disease, Kidney).
"""

from typing import Dict, Any, Optional

# Verified Categorical Input Mappings
CATEGORICAL_MAPPINGS: Dict[str, Dict[str, Dict[str, int]]] = {
    "diabetes": {
        "gender": {
            "Female": 0,
            "Male": 1,
            "Other": 2,
            "female": 0,
            "male": 1,
            "other": 2
        },
        "smoking_history": {
            "No Info": 0,
            "no info": 0,
            "current": 1,
            "ever": 2,
            "former": 3,
            "never": 4,
            "not current": 5
        }
    },
    "Stroke": {
        "gender": {
            "Female": 0,
            "Male": 1,
            "Other": 2,
            "female": 0,
            "male": 1,
            "other": 2
        },
        "ever_married": {
            "No": 0,
            "Yes": 1,
            "no": 0,
            "yes": 1
        },
        "work_type": {
            "Govt_job": 0,
            "Never_worked": 1,
            "Private": 2,
            "Self-employed": 3,
            "children": 4
        },
        "Residence_type": {
            "Rural": 0,
            "Urban": 1,
            "rural": 0,
            "urban": 1
        },
        "smoking_status": {
            "Unknown": 0,
            "formerly smoked": 1,
            "never smoked": 2,
            "smokes": 3
        }
    },
    "Chronic_liver": {
        "Gender": {
            "female": 0,
            "male": 1,
            "Female": 0,
            "Male": 1
        }
    }
}

# Verified Disease Target Class Human-Readable Label Mappings for Report/UI Display
DISEASE_TARGET_LABEL_MAPPINGS: Dict[str, Dict[str, str]] = {
    "diabetes": {"0": "Absence", "1": "Presence"},
    "Stroke": {"0": "Absence", "1": "Presence"},
    "heart_disease": {"0": "Absence", "1": "Presence"},
    "lung_cancer": {"0": "Absence", "1": "Presence"},
    "Parkinsons": {"0": "Absence", "1": "Presence"},
    "Kidney": {"0": "ckd", "1": "notckd", "ckd": "ckd", "notckd": "notckd"},
    "Chronic_liver": {"1": "Liver Patient", "2": "Non-Liver Patient", "0": "Liver Patient"},
    "Hepatitis": {"0": "Die", "1": "Live"},
    "B_cancer": {"0": "B", "1": "M", "B": "B", "M": "M"},
    "anemia": {
        "0": "Healthy",
        "1": "Iron deficiency anemia",
        "2": "Leukemia",
        "3": "Leukemia with thrombocytopenia",
        "4": "Macrocytic anemia",
        "5": "Normocytic hypochromic anemia",
        "6": "Normocytic normochromic anemia",
        "7": "Other microcytic anemia",
        "8": "Thrombocytopenia"
    }
}


def resolve_human_label(disease: str, raw_label: Any) -> str:
    """
    Map raw model class string/int (e.g. '0', '1', 0, 1) to verified human-readable display label.
    If no specific mapping exists or raw_label is already human-readable, returns str(raw_label).
    """
    str_val = str(raw_label).strip()
    disease_labels = DISEASE_TARGET_LABEL_MAPPINGS.get(disease, {})
    return disease_labels.get(str_val, str_val)


def get_mapped_value(disease: str, feature: str, raw_val: Any) -> Any:
    """
    Look up verified numeric code for a categorical feature string.
    If the value is already numeric or no mapping is defined for the disease/feature, returns raw_val.
    Raises ValueError if raw_val is an unmapped string for a mapped categorical feature.
    """
    if isinstance(raw_val, (int, float)) and not isinstance(raw_val, bool):
        return raw_val

    disease_mappings = CATEGORICAL_MAPPINGS.get(disease, {})
    feature_mapping = disease_mappings.get(feature)

    if feature_mapping is not None:
        str_val = str(raw_val).strip()
        if str_val in feature_mapping:
            return feature_mapping[str_val]
        else:
            raise ValueError(
                f"Unmapped categorical value '{raw_val}' for feature '{feature}' in disease '{disease}'. "
                f"Allowed values: {list(feature_mapping.keys())}"
            )

    return raw_val


def map_patient_features(disease: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode all categorical features in a patient dict for the given disease.
    Unmapped/natively-numeric features pass through unchanged.
    """
    mapped_dict = {}
    for feat, val in features.items():
        mapped_dict[feat] = get_mapped_value(disease, feat, val)
    return mapped_dict

