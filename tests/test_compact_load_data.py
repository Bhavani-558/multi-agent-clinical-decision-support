"""
Test for Compact LOAD DATA Feature and Heart Disease Row 3 Example.
"""

import os
import re
from app.dataset_service import DatasetService
from src.prediction.predictor import DiseasePredictor


def test_html_modal_is_compact_with_no_preview_elements():
    """Verify that index.html contains ONLY the compact modal without tables, search, or filters."""
    html_path = os.path.join(r"d:\MultiAgent_CDSS", "app", "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Modal container must exist and have compact class
    assert 'id="modal-load-dataset"' in content
    assert "modal-compact" in content
    assert 'id="form-load-dataset-row"' in content
    assert 'id="dataset-row-input"' in content
    assert 'id="btn-confirm-load-dataset"' in content
    assert 'id="btn-cancel-dataset-modal"' in content

    # Crucial negative checks: NO table, NO search, NO ground-truth filter in the modal
    assert 'id="dataset-preview-table"' not in content
    assert 'id="dataset-filter-search"' not in content
    assert 'id="dataset-filter-target"' not in content
    assert 'id="dataset-preview-tbody"' not in content
    assert 'id="btn-dataset-prev"' not in content
    assert 'id="btn-dataset-next"' not in content


def test_app_js_validation_logic():
    """Verify that app.js implements the strict validation rules and compact workflow."""
    js_path = os.path.join(r"d:\MultiAgent_CDSS", "app", "static", "app.js")
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify validation checks exist in JS
    assert "Please enter a dataset row number." in content
    assert "Please enter a valid numeric row number." in content
    assert "Row number must be at least 1." in content
    assert "Row number cannot exceed" in content
    assert "loaded successfully." in content

    # Verify no preview table functions exist in JS
    assert "fetchAndRenderDatasetPreview" not in content
    assert "renderDatasetPreviewTable" not in content
    assert "datasetPreviewTbody" not in content


def test_heart_disease_row_3_execution():
    """
    User example verification:
    If Heart Disease is selected and user enters row 3:
    -> load row 3 from Heart_Disease_Prediction.csv
    -> populate existing Heart Disease fields (row index 2)
    -> target Heart_Disease is excluded
    -> existing Heart Disease XGBoost pipeline runs normally.
    """
    svc = DatasetService()
    predictor = DiseasePredictor()

    # Row 3 (1-indexed) corresponds to 0-indexed row 2
    row_data = svc.get_dataset_row("heart_disease", row_index=2)
    assert row_data["display_label"] == "Dataset Row: 3"
    assert row_data["file_name"] == "Heart_Disease_Prediction.csv"

    features = row_data["features"]

    # Verify target column is excluded
    assert "Heart_Disease" not in features
    assert "heart_disease" not in features

    # Verify expected Heart Disease features are present
    expected_feats = [
        "Age", "Sex", "Chest_pain_type", "BP", "Cholesterol", "FBS_over_120",
        "EKG_results", "Max_HR", "Exercise_angina", "ST_depression",
        "Slope_of_ST", "Number_of_vessels_fluro", "Thallium"
    ]
    for feat in expected_feats:
        assert feat in features, f"Missing feature {feat}"
        assert features[feat] is not None

    # Run prediction through XGBoost pipeline
    prediction = predictor.predict_disease("heart_disease", features)

    assert prediction.status == "SUCCESS"
    assert prediction.disease == "heart_disease"
    assert prediction.predicted_class is not None
    assert 0.0 <= prediction.probability <= 1.0


def test_heart_disease_row_2_execution():
    """
    Requirement 8 verification:
    Select Heart Disease -> LOAD DATA -> enter 2 -> LOAD DATA
    -> row 2 values must populate the existing Heart Disease fields
    -> target Heart_Disease is excluded
    -> existing Heart Disease XGBoost model runs successfully.
    """
    svc = DatasetService()
    predictor = DiseasePredictor()

    # 1-based Row 2 corresponds to index 1
    row_data = svc.get_dataset_row_1based("heart_disease", row_number=2)
    assert row_data["display_label"] == "Dataset Row: 2"
    assert row_data["file_name"] == "Heart_Disease_Prediction.csv"

    features = row_data["features"]
    assert "Heart_Disease" not in features
    assert "heart_disease" not in features

    # Raw row 2: Age: 67, Sex: 0, BP: 115, Cholesterol: 564
    assert features["Age"] == 67
    assert features["Sex"] == 0
    assert features["BP"] == 115
    assert features["Cholesterol"] == 564

    # Run prediction through XGBoost pipeline
    prediction = predictor.predict_disease("heart_disease", features)
    assert prediction.status == "SUCCESS"
    assert prediction.disease == "heart_disease"
    assert prediction.predicted_class is not None
    assert 0.0 <= prediction.probability <= 1.0


def test_dataset_service_validation_errors():
    """
    Requirements 5 & 6 verification:
    - Row number exceeding max rows returns 'Row number cannot exceed [N] for this dataset.'
    - Row number < 1 returns 'Row number must be at least 1.'
    - Dataset not found returns 'Dataset not found for [Disease Name].'
    """
    import pytest
    svc = DatasetService()

    # 1. Row number cannot exceed total rows (Chronic Liver has 583 rows)
    with pytest.raises(IndexError, match=r"Row number cannot exceed 583 for this dataset\."):
        svc.get_dataset_row_1based("Chronic_liver", 600)

    # 2. Row number must be at least 1
    with pytest.raises(IndexError, match=r"Row number must be at least 1\."):
        svc.get_dataset_row_1based("heart_disease", 0)

    # 3. Dataset not found
    with pytest.raises(FileNotFoundError, match=r"Dataset not found for Unknown Disease\."):
        svc.get_dataset_row_1based("Unknown Disease", 1)


def test_fastapi_load_row_endpoint():
    """
    Requirement 7 verification:
    Check FastAPI route GET /api/dataset/{disease}/load-row/{row_number}.
    """
    import asyncio
    from fastapi import HTTPException
    import pytest
    from app.main import load_dataset_row_1based

    doctor = {"doctor_id": "doctor@hospital.org", "doctor_name": "Test Doctor"}

    # Valid row 2 for Heart Disease
    resp = asyncio.run(load_dataset_row_1based("heart_disease", row_number=2, doctor=doctor))
    assert resp["status"] == "success"
    assert resp["data"]["display_label"] == "Dataset Row: 2"
    assert resp["data"]["features"]["Age"] == 67
    assert "Heart_Disease" not in resp["data"]["features"]

    # Invalid row: exceeds Chronic Liver 583 rows
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(load_dataset_row_1based("Chronic_liver", row_number=600, doctor=doctor))
    assert exc_info.value.status_code == 400
    assert "Row number cannot exceed 583 for this dataset." in exc_info.value.detail

    # Invalid disease: meaningful error
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(load_dataset_row_1based("Nonexistent_Disease", row_number=1, doctor=doctor))
    assert exc_info.value.status_code == 404
    assert "Dataset not found for" in exc_info.value.detail


def test_fastapi_testclient_http_requests():
    """
    Live HTTP integration test using Starlette / FastAPI TestClient.
    Verifies HTTP status codes, headers, and payload structures.
    """
    from fastapi.testclient import TestClient
    from app.main import app, session_reg

    import httpx
    # Starlette 0.27.0 passes app to httpx.Client, which httpx 0.28.0+ deprecated/removed
    _orig_init = httpx.Client.__init__
    httpx.Client.__init__ = lambda self, *args, **kwargs: _orig_init(
        self, *args, **{k: v for k, v in kwargs.items() if k != "app"}
    )

    client = TestClient(app)
    token = session_reg.create_session({
        "doctor_id": "dr.jenkins@hospital.org",
        "doctor_name": "Dr. Sarah Jenkins, MD",
        "specialty": "Cardiology",
        "account_role": "CDSS_PHYSICIAN"
    })
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Heart Disease row 2 via HTTP GET
    res = client.get("/api/dataset/heart_disease/load-row/2", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["data"]["display_label"] == "Dataset Row: 2"
    assert body["data"]["features"]["Age"] == 67
    assert "Heart_Disease" not in body["data"]["features"]

    # 2. Chronic Liver row 600 via HTTP GET -> 400 Bad Request
    res2 = client.get("/api/dataset/Chronic_liver/load-row/600", headers=headers)
    assert res2.status_code == 400
    assert "Row number cannot exceed 583 for this dataset." in res2.json()["detail"]

    # 3. Heart Disease row 0 via HTTP GET -> 400 Bad Request
    res3 = client.get("/api/dataset/heart_disease/load-row/0", headers=headers)
    assert res3.status_code == 400
    assert "Row number must be at least 1." in res3.json()["detail"]

    # 4. Unknown disease via HTTP GET -> 404 with custom message (NOT generic 'Not Found')
    res4 = client.get("/api/dataset/Nonexistent_Disease/load-row/1", headers=headers)
    assert res4.status_code == 404
    assert "Dataset not found for Nonexistent Disease." in res4.json()["detail"]
    assert res4.json()["detail"] != "Not Found"


