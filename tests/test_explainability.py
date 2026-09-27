"""
Unit tests for CDSS Explainability & SHAP Module.
Tests mapping registry and SHAP explanation generation across all 10 disease models.
"""

import pytest
import numpy as np
from src.prediction.model_loader import ModelLoader
from src.prediction.mapping_registry import map_patient_features, get_mapped_value
from src.explainability.shap_service import SHAPExplainerService
from src.explainability.schemas import SHAPExplanation, FeatureAttribution


@pytest.fixture(scope="module")
def model_loader():
    loader = ModelLoader()
    loader.load_all_models()
    return loader


@pytest.fixture(scope="module")
def shap_service(model_loader):
    return SHAPExplainerService(loader=model_loader)


def test_mapping_registry_verified_mappings():
    """Verify categorical string-to-numeric mappings for diabetes, Stroke, Chronic_liver."""
    assert get_mapped_value("diabetes", "gender", "Female") == 0
    assert get_mapped_value("diabetes", "gender", "Male") == 1
    assert get_mapped_value("diabetes", "smoking_history", "never") == 4

    assert get_mapped_value("Stroke", "gender", "Male") == 1
    assert get_mapped_value("Stroke", "ever_married", "Yes") == 1
    assert get_mapped_value("Stroke", "work_type", "Private") == 2
    assert get_mapped_value("Stroke", "smoking_status", "smokes") == 3

    assert get_mapped_value("Chronic_liver", "Gender", "female") == 0
    assert get_mapped_value("Chronic_liver", "Gender", "Male") == 1


def test_mapping_registry_numeric_passthrough():
    """Verify that native numeric inputs (including Heart Disease and Kidney values) pass through unchanged."""
    assert get_mapped_value("heart_disease", "Sex", 1) == 1
    assert get_mapped_value("heart_disease", "Chest_pain_type", 4) == 4

    assert get_mapped_value("Kidney", "Rbc", 1.0) == 1.0
    assert get_mapped_value("Kidney", "Htn", 0.37) == 0.37


def test_mapping_registry_unmapped_string_error():
    """Verify that unmapped string inputs raise ValueError."""
    with pytest.raises(ValueError, match="Unmapped categorical value"):
        get_mapped_value("diabetes", "gender", "UnknownGenderString")


# Sample test patient feature dicts for all 10 disease models
SAMPLE_PATIENT_INPUTS = {
    "anemia": {"Gender": 0, "Hemoglobin": 11.5, "MCH": 24.0, "MCHC": 28.0, "MCV": 75.0},
    "B_cancer": {
        "mean_radius": 14.0, "mean_texture": 19.0, "mean_perimeter": 90.0, "mean_area": 600.0,
        "mean_smoothness": 0.09, "mean_compactness": 0.1, "mean_concavity": 0.08,
        "mean_concave_points": 0.04, "mean_symmetry": 0.18, "mean_fractal_dimension": 0.06
    },
    "Chronic_liver": {
        "Age": 45, "Gender": "Female", "Total_Bilirubin": 1.2, "Direct_Bilirubin": 0.4,
        "Alkaline_Phosphotase": 200, "Alamine_Aminotransferase": 35, "Aspartate_Aminotransferase": 40,
        "Total_Protiens": 6.5, "Albumin": 3.2, "Albumin_and_Globulin_Ratio": 0.9
    },
    "diabetes": {
        "gender": "Female", "age": 55.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 28.5, "HbA1c_level": 6.2, "blood_glucose_level": 140
    },
    "heart_disease": {
        "Age": 60, "Sex": 1, "Chest_pain_type": 4, "BP": 130, "Cholesterol": 240,
        "FBS_over_120": 0, "EKG_results": 2, "Max_HR": 140, "Exercise_angina": 1,
        "ST_depression": 1.5, "Slope_of_ST": 2, "Number_of_vessels_fluro": 1, "Thallium": 7
    },
    "Hepatitis": {
        "Age": 40, "Sex": "female", "ALB": 38.0, "ALP": 75.0, "ALT": 25.0, "AST": 30.0, "BIL": 12.0
    },
    "Kidney": {
        "Bp": 80.0, "Sg": 1.02, "Al": 1.0, "Su": 0.0, "Rbc": 1.0, "Bu": 36.0,
        "Sc": 1.2, "Sod": 138.0, "Pot": 4.5, "Hemo": 14.0, "Wbcc": 7800.0, "Rbcc": 5.2, "Htn": 0.37
    },
    "lung_cancer": {
        "GENDER": "M", "AGE": 65, "SMOKING": 2, "YELLOW_FINGERS": 1, "ANXIETY": 1,
        "PEER_PRESSURE": 1, "CHRONIC_DISEASE": 2, "FATIGUE": 2, "ALLERGY": 1,
        "WHEEZING": 2, "ALCOHOL_CONSUMING": 2, "COUGHING": 2, "SHORTNESS_OF_BREATH": 2,
        "SWALLOWING_DIFFICULTY": 1, "CHEST_PAIN": 2
    },
    "Parkinsons": {
        "MDVP:Fo(Hz)": 120.0, "MDVP:Fhi(Hz)": 150.0, "MDVP:Flo(Hz)": 90.0,
        "MDVP:Jitter(%)": 0.006, "MDVP:Jitter(Abs)": 0.00005, "MDVP:RAP": 0.003,
        "MDVP:PPQ": 0.003, "Jitter:DDP": 0.009, "MDVP:Shimmer": 0.03,
        "MDVP:Shimmer(dB)": 0.3, "Shimmer:APQ3": 0.015, "Shimmer:APQ5": 0.018,
        "MDVP:APQ": 0.02, "Shimmer:DDA": 0.045, "NHR": 0.015, "HNR": 22.0,
        "RPDE": 0.45, "DFA": 0.65, "spread1": -5.0, "spread2": 0.2, "D2": 2.1, "PPE": 0.18
    },
    "Stroke": {
        "gender": "Male", "age": 67.0, "hypertension": 1, "heart_disease": 0,
        "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban",
        "avg_glucose_level": 105.5, "bmi": 29.0, "smoking_status": "formerly smoked"
    }
}


@pytest.mark.parametrize("disease", [
    "anemia", "B_cancer", "Chronic_liver", "diabetes", "heart_disease",
    "Hepatitis", "Kidney", "lung_cancer", "Parkinsons", "Stroke"
])
def test_shap_explanation_generation(shap_service, disease):
    """Test SHAP explanation generation across all 10 disease models."""
    sample_input = SAMPLE_PATIENT_INPUTS[disease]
    explanation = shap_service.explain_prediction(disease, sample_input, top_n=5)

    assert isinstance(explanation, SHAPExplanation)
    assert explanation.disease == disease
    assert 0.0 <= explanation.prediction_probability <= 1.0
    assert isinstance(explanation.base_value, float)
    assert len(explanation.top_attributions) == 5
    assert len(explanation.all_attributions) >= 5

    # Check top attribution structure
    top1 = explanation.top_attributions[0]
    assert isinstance(top1, FeatureAttribution)
    assert top1.rank == 1
    assert top1.impact_direction in ["increases_risk", "decreases_risk", "neutral"]
    assert isinstance(top1.shap_value, float)
