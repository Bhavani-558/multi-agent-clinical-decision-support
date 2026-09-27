"""
Tests for DatasetService and End-to-End LOAD DATA Workflow across all 10 diseases.
Verifies:
1. Dataset loading, feature extraction, and target exclusion.
2. Safe NaN imputation and Hepatitis '?' handling.
3. DiseasePredictor compatibility with loaded dataset rows for all 10 diseases.
4. FastAPI endpoints for dataset info, preview, and row extraction.
"""

import asyncio
import pytest
from app.main import get_dataset_info, get_dataset_preview, get_dataset_row
from app.dataset_service import DatasetService
from src.prediction.predictor import DiseasePredictor


ALL_DISEASES = [
    "anemia",
    "B_cancer",
    "Chronic_liver",
    "diabetes",
    "heart_disease",
    "Hepatitis",
    "Kidney",
    "lung_cancer",
    "Parkinsons",
    "Stroke"
]


@pytest.fixture(scope="module")
def dataset_service():
    return DatasetService()


@pytest.fixture(scope="module")
def predictor():
    return DiseasePredictor()


def test_all_10_datasets_exist_and_load(dataset_service):
    """Verifies that all 10 datasets can be loaded with nonzero rows and expected metadata."""
    for disease in ALL_DISEASES:
        info = dataset_service.get_dataset_info(disease)
        assert info["disease"] == disease
        assert info["total_rows"] > 0, f"{disease} dataset has 0 rows"
        assert info["feature_count"] > 0, f"{disease} dataset has 0 features"
        assert "target_col" in info
        assert "target_classes" in info


def test_dataset_preview_structure(dataset_service):
    """Verifies that preview returns paginated rows with ground truth labels and preview features."""
    for disease in ALL_DISEASES:
        preview = dataset_service.get_dataset_preview(disease, limit=5, offset=0)
        assert preview["disease"] == disease
        assert len(preview["rows"]) == 5
        assert preview["total_matching"] >= 5

        first_row = preview["rows"][0]
        assert "row_index" in first_row
        assert "display_label" in first_row
        assert "ground_truth_label" in first_row
        assert "preview_features" in first_row
        assert len(first_row["preview_features"]) > 0


def test_dataset_row_excludes_targets_and_ids(dataset_service):
    """
    Critical requirement: Loaded row features must NOT contain target or identifier columns
    (e.g., id, name, Diagnosis, stroke, Class, status, etc.).
    """
    for disease in ALL_DISEASES:
        cfg = dataset_service.DISEASE_DATASET_CONFIG[disease]
        target_col = cfg["target_col"]
        id_cols = cfg.get("id_cols", [])

        row_data = dataset_service.get_dataset_row(disease, row_index=0)
        features = row_data["features"]

        # Target column must NOT be in features
        assert target_col not in features, f"Target '{target_col}' leaked into features for {disease}"
        assert target_col.lower() not in [f.lower() for f in features], f"Target variation leaked into {disease}"

        # Id columns must NOT be in features
        for id_col in id_cols:
            assert id_col not in features, f"ID column '{id_col}' found in features for {disease}"

        # Display label must be clear
        assert row_data["display_label"] == "Dataset Row: 1"
        assert row_data["ground_truth_label"] != ""


def test_hepatitis_nan_and_categorical_handling(dataset_service):
    """Verifies that Hepatitis '?' values are cleaned and encoded to 'male'/'female' and 'no'/'yes'."""
    row_data = dataset_service.get_dataset_row("Hepatitis", row_index=0)
    features = row_data["features"]

    assert features["sex"] in ["male", "female"]
    assert features["steroid"] in ["no", "yes"]
    assert features["antivirals"] in ["no", "yes"]
    assert features["fatigue"] in ["no", "yes"]
    assert isinstance(features["age"], (int, float))
    assert isinstance(features["bilirubin"], (int, float))
    assert not any(v == "?" for v in features.values()), "Found raw '?' in features"


def test_stroke_nan_bmi_handling(dataset_service):
    """Verifies that Stroke missing BMI values are safely imputed to numeric values."""
    df = dataset_service._load_raw_df("Stroke")
    assert not df["bmi"].isna().any(), "Stroke BMI contains unhandled NaNs"
    row_data = dataset_service.get_dataset_row("Stroke", row_index=0)
    features = row_data["features"]
    assert isinstance(features["bmi"], (int, float))
    assert "id" not in features


@pytest.mark.parametrize("disease", ALL_DISEASES)
def test_all_10_diseases_loaded_row_predict_successfully(dataset_service, predictor, disease):
    """
    Requirement 11:
    Test all 10 diseases individually:
    Select disease -> select row -> LOAD DATA -> verify fields populated
    -> ANALYZE -> verify the corresponding model runs successfully.
    """
    row_data = dataset_service.get_dataset_row(disease, row_index=2)
    features = row_data["features"]

    # Verify features are populated and nonempty
    assert len(features) > 0, f"No features extracted for {disease}"

    # Run through the actual DiseasePredictor
    result = predictor.predict_disease(disease, features)

    assert result.status == "SUCCESS", f"Prediction failed for {disease}: {result.error_message}"
    assert result.disease == disease
    assert result.predicted_class is not None
    assert 0.0 <= result.probability <= 1.0
    assert len(result.class_probabilities) > 0


def test_api_dataset_endpoints():
    """Verifies FastAPI GET /api/dataset endpoints with authenticated doctor context."""
    doctor = {"doctor_id": "doctor@hospital.org", "doctor_name": "Test Doctor"}

    # Test info endpoint
    resp = asyncio.run(get_dataset_info("diabetes", doctor=doctor))
    assert resp["status"] == "success"
    assert resp["info"]["total_rows"] == 100000

    # Test preview endpoint
    resp = asyncio.run(get_dataset_preview("diabetes", limit=10, offset=0, doctor=doctor))
    assert resp["status"] == "success"
    assert len(resp["preview"]["rows"]) == 10

    # Test row endpoint
    resp = asyncio.run(get_dataset_row("diabetes", row_index=5, doctor=doctor))
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["row_index"] == 5
    assert data["display_label"] == "Dataset Row: 6"
    assert "diabetes" not in data["features"]
    assert "age" in data["features"]
