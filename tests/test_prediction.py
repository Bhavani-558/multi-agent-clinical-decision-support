"""
Automated unit and integration tests for the CDSS Prediction Module across all 10 models.
"""

import pytest
import numpy as np
from src.prediction.model_loader import ModelLoader
from src.prediction.predictor import DiseasePredictor
from agents.prediction_agent import PredictionAgent


@pytest.fixture
def model_loader():
    return ModelLoader()


@pytest.fixture
def predictor(model_loader):
    return DiseasePredictor(loader=model_loader)


@pytest.fixture
def prediction_agent():
    return PredictionAgent()


def test_model_loader_all_10_models(model_loader):
    """Test loading all 10 disease model artifacts."""
    loaded_models = model_loader.load_all_models()
    assert len(loaded_models) == 10
    
    expected_diseases = [
        "anemia", "B_cancer", "Chronic_liver", "diabetes", "heart_disease",
        "Hepatitis", "Kidney", "lung_cancer", "Parkinsons", "Stroke"
    ]
    for disease in expected_diseases:
        assert disease in loaded_models
        meta = loaded_models[disease]
        assert meta.preprocessor is not None
        assert meta.estimator is not None
        assert len(meta.feature_names) > 0


def test_prediction_anemia_multiclass(predictor):
    """Test multiclass prediction for Anemia model (14 numeric features, 9 target classes)."""
    sample_input = {
        "WBC": 6.5, "LYMp": 30.0, "NEUTp": 60.0, "LYMn": 2.0, "NEUTn": 4.0,
        "RBC": 4.5, "HGB": 13.5, "HCT": 40.0, "MCV": 88.0, "MCH": 29.0,
        "MCHC": 33.0, "PLT": 250.0, "PDW": 12.0, "PCT": 0.25
    }
    res = predictor.predict_disease("anemia", sample_input)
    assert res.status == "SUCCESS"
    assert res.disease == "anemia"
    assert res.is_multiclass is True
    assert 0 <= res.probability <= 1.0
    assert len(res.class_probabilities) == 9
    assert "Healthy" in res.class_probabilities


def test_prediction_b_cancer(predictor):
    """Test Breast Cancer model (30 numeric features)."""
    sample_input = {col: 1.0 for col in [
        "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
        "compactness_mean", "concavity_mean", "concave_points_mean", "symmetry_mean", "fractal_dimension_mean",
        "radius_se", "texture_se", "perimeter_se", "area_se", "smoothness_se",
        "compactness_se", "concavity_se", "concave_points_se", "symmetry_se", "fractal_dimension_se",
        "radius_worst", "texture_worst", "perimeter_worst", "area_worst", "smoothness_worst",
        "compactness_worst", "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
    ]}
    res = predictor.predict_disease("B_cancer", sample_input)
    assert res.status == "SUCCESS"
    assert res.predicted_label in ["B", "M"]


def test_prediction_chronic_liver(predictor):
    """Test Chronic Liver model with numeric pre-encoded Gender."""
    sample_input = {
        "Age": 45, "Gender": 1, "Total_Bilirubin": 0.8, "Direct_Bilirubin": 0.2,
        "Alkaline_Phosphotase": 200, "Alamine_Aminotransferase": 25,
        "Aspartate_Aminotransferase": 30, "Total_Protiens": 7.0,
        "Albumin": 4.0, "Albumin_and_Globulin_Ratio": 1.2
    }
    res = predictor.predict_disease("Chronic_liver", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_diabetes_numeric(predictor):
    """Test Diabetes model with numeric pre-encoded inputs."""
    sample_input = {
        "gender": 1.0, "age": 50.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": 0.0, "bmi": 25.4, "HbA1c_level": 5.7, "blood_glucose_level": 100.0
    }
    res = predictor.predict_disease("diabetes", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_heart_disease_numeric(predictor):
    """Test Heart Disease model with numeric pre-encoded inputs."""
    sample_input = {
        "Age": 55, "Sex": 1, "Chest_pain_type": 2, "BP": 130, "Cholesterol": 240,
        "FBS_over_120": 0, "EKG_results": 0, "Max_HR": 150, "Exercise_angina": 0,
        "ST_depression": 1.0, "Slope_of_ST": 1, "Number_of_vessels_fluro": 0, "Thallium": 3
    }
    res = predictor.predict_disease("heart_disease", sample_input)
    assert res.status == "SUCCESS"
    assert res.predicted_label in ["Absence", "Presence"]


def test_prediction_internal_onehot_hepatitis(predictor):
    """Test Hepatitis model with string categoricals handled by internal OneHotEncoder."""
    sample_input = {
        "age": 40.0, "bilirubin": 1.0, "alk_phosphate": 85.0, "sgot": 30.0, "albumin": 4.0, "protime": 80.0,
        "sex": "male", "steroid": "no", "antivirals": "no", "fatigue": "no", "malaise": "no",
        "anorexia": "no", "liver_big": "no", "liver_firm": "no", "spleen_palpable": "no",
        "spiders": "no", "ascites": "no", "varices": "no", "histology": "no"
    }
    res = predictor.predict_disease("Hepatitis", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_kidney_numeric(predictor):
    """Test Kidney model with numeric inputs."""
    sample_input = {
        "Bp": 80, "Sg": 1.020, "Al": 1, "Su": 0, "Rbc": 1, "Bu": 36, "Sc": 1.2,
        "Sod": 137, "Pot": 4.4, "Hemo": 15.4, "Wbcc": 7800, "Rbcc": 5.2, "Htn": 0
    }
    res = predictor.predict_disease("Kidney", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_internal_onehot_lung_cancer(predictor):
    """Test Lung Cancer model with string GENDER handled by internal OneHotEncoder."""
    sample_input = {
        "GENDER": "M", "AGE": 60, "SMOKING": 2, "YELLOW_FINGERS": 1, "ANXIETY": 1,
        "PEER_PRESSURE": 2, "CHRONIC_DISEASE": 1, "FATIGUE": 2, "ALLERGY": 1,
        "WHEEZING": 2, "ALCOHOL_CONSUMING": 2, "COUGHING": 2, "SHORTNESS_OF_BREATH": 2,
        "SWALLOWING_DIFFICULTY": 1, "CHEST_PAIN": 2
    }
    res = predictor.predict_disease("lung_cancer", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_parkinsons(predictor):
    """Test Parkinson's model (22 numeric features)."""
    sample_input = {
        "MDVP:Fo(Hz)": 119.992, "MDVP:Fhi(Hz)": 157.302, "MDVP:Flo(Hz)": 74.997,
        "MDVP:Jitter(%)": 0.00784, "MDVP:Jitter(Abs)": 0.00007, "MDVP:RAP": 0.00370,
        "MDVP:PPQ": 0.00554, "Jitter:DDP": 0.01109, "MDVP:Shimmer": 0.04374,
        "MDVP:Shimmer(dB)": 0.426, "Shimmer:APQ3": 0.02182, "Shimmer:APQ5": 0.03130,
        "MDVP:APQ": 0.02971, "Shimmer:DDA": 0.06545, "NHR": 0.02211, "HNR": 21.033,
        "RPDE": 0.414783, "DFA": 0.815285, "spread1": -4.813031, "spread2": 0.266482,
        "D2": 2.301442, "PPE": 0.284654
    }
    res = predictor.predict_disease("Parkinsons", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_stroke_numeric(predictor):
    """Test Stroke model with numeric pre-encoded inputs."""
    sample_input = {
        "gender": 1, "age": 67.0, "hypertension": 0, "heart_disease": 1,
        "ever_married": 1, "work_type": 2, "Residence_type": 1,
        "avg_glucose_level": 228.69, "bmi": 36.6, "smoking_status": 1
    }
    res = predictor.predict_disease("Stroke", sample_input)
    assert res.status == "SUCCESS"


def test_prediction_diabetes_string_categoricals(predictor):
    """Test Diabetes model with string categorical inputs mapped via registry."""
    sample_input_string = {
        "gender": "Female", "age": 50.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 25.4, "HbA1c_level": 5.7, "blood_glucose_level": 100.0
    }
    res = predictor.predict_disease("diabetes", sample_input_string)
    assert res.status == "SUCCESS"
    assert res.disease == "diabetes"
    assert res.predicted_class in [0, 1]
    assert res.predicted_label in ["Absence", "Presence"]
    assert 0.0 <= res.probability <= 1.0



def test_unresolved_categorical_mapping_detection(predictor):
    """Test that string categoricals for unmapped models/features raise UNRESOLVED_MAPPING_REQUIRED."""
    sample_input_unmapped = {
        "Age": 55, "Sex": "male", "Chest_pain_type": "type_A", "BP": 130, "Cholesterol": 240,
        "FBS_over_120": 0, "EKG_results": 0, "Max_HR": 150, "Exercise_angina": 0,
        "ST_depression": 1.0, "Slope_of_ST": 1, "Number_of_vessels_fluro": 0, "Thallium": 3
    }
    res = predictor.predict_disease("heart_disease", sample_input_unmapped)
    assert res.status == "UNRESOLVED_MAPPING_REQUIRED"
    assert len(res.unresolved_mappings) >= 1


def test_prediction_agent_batch_evaluation(prediction_agent):
    """Test PredictionAgent evaluating a patient profile across multiple disease models."""
    patient_profile = {
        "gender": 1.0, "age": 55.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": 0.0, "bmi": 26.5, "HbA1c_level": 6.0, "blood_glucose_level": 110.0,
        "WBC": 7.0, "LYMp": 28.0, "NEUTp": 62.0, "LYMn": 2.1, "NEUTn": 4.5,
        "RBC": 4.8, "HGB": 14.0, "HCT": 42.0, "MCV": 88.0, "MCH": 29.5,
        "MCHC": 33.5, "PLT": 260.0, "PDW": 11.5, "PCT": 0.26
    }
    batch_res = prediction_agent.evaluate_patient(patient_profile, diseases=["anemia", "diabetes"])
    assert batch_res.summary["total_evaluated"] == 2
    assert batch_res.predictions["anemia"].status == "SUCCESS"
    assert batch_res.predictions["diabetes"].status == "SUCCESS"
