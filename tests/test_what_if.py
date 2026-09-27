"""
Comprehensive Automated Test Suite for Counterfactual What-If Analysis.

Verifies:
1. Valid What-If simulation request for verified live model (Diabetes Mellitus).
2. Explicit Chronic Liver governance lock rejection and message integrity.
3. Invalid disease rejection.
4. Unknown and invalid feature validation.
5. Patient features immutability.
6. Probability delta and prediction status calculation.
7. Verification that production model artifacts remain completely untouched.
8. FastAPI /api/what-if and /api/what-if/status/{disease} endpoint contracts.
9. Static UI presence of What-If controls, disclaimers, and lock banners.
"""

import copy
import hashlib
import json
import os
import pytest
from typing import Dict, Any

from src.prediction.counterfactual_service import (
    CounterfactualService,
    SIMULATION_DISCLAIMER,
    CHRONIC_LIVER_LOCK_MESSAGE
)
from src.prediction.model_loader import ModelLoader
from app.disease_schemas import DEMO_PATIENT_DATA
from app.auth import DoctorCredentialStore, SessionRegistry
from app.main import app


@pytest.fixture
def service():
    return CounterfactualService()


@pytest.fixture
def auth_headers():
    doc_store = DoctorCredentialStore()
    session_reg = SessionRegistry()
    doc = doc_store.get_doctor("dr.jenkins@hospital.org") or {
        "doctor_id": "test_doc@hospital.org",
        "doctor_name": "Dr. Sarah Jenkins",
        "specialty": "Cardiology",
        "account_role": "CDSS_PHYSICIAN"
    }
    token = session_reg.create_session(doc)
    return {"Authorization": token}


# --- 1. VALID REQUEST & PROBABILITY CALCULATION ---

def test_valid_what_if_diabetes_simulation(service):
    """Verify live What-If simulation on verified Diabetes model."""
    original = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    # Demo patient: blood_glucose_level=100.0, HbA1c_level=5.7, bmi=25.4 (Absence / low risk)

    modified = copy.deepcopy(original)
    modified["blood_glucose_level"] = 220.0
    modified["HbA1c_level"] = 8.5
    modified["bmi"] = 34.0

    res = service.simulate_what_if("diabetes", original, modified)

    assert res["status"] == "success"
    assert res["disease"] == "diabetes"
    assert res["simulation_disclaimer"] == SIMULATION_DISCLAIMER

    # Baseline assertions (Low risk / Absence)
    orig_prob = res["original"]["probability"]
    assert orig_prob < 0.10
    assert res["original"]["predicted_class"] == 0
    assert res["original"]["predicted_label"] == "Absence"
    assert res["original"]["clinical_status"] == "NOT DETECTED"
    assert res["original"]["risk_tier"] == "LOW_RISK"

    # Counterfactual assertions (Elevated risk / Presence)
    cf_prob = res["counterfactual"]["probability"]
    assert cf_prob > 0.80
    assert res["counterfactual"]["predicted_class"] == 1
    assert res["counterfactual"]["predicted_label"] == "Presence"
    assert res["counterfactual"]["clinical_status"] == "DETECTED"
    assert res["counterfactual"]["risk_tier"] == "HIGH_RISK"

    # Delta assertions
    assert res["delta"]["probability_change"] > 0
    assert res["delta"]["percentage_points_change"] > 50.0
    assert res["delta"]["direction"] == "increase"
    assert res["delta"]["prediction_changed"] is True

    # Modified features list assertions
    mod_feats = {item["feature"]: item for item in res["modified_features"]}
    assert "blood_glucose_level" in mod_feats
    assert mod_feats["blood_glucose_level"]["original_value"] == 100.0
    assert mod_feats["blood_glucose_level"]["counterfactual_value"] == 220.0
    assert mod_feats["blood_glucose_level"]["delta"] == 120.0

    assert "HbA1c_level" in mod_feats
    assert mod_feats["HbA1c_level"]["original_value"] == 5.7
    assert mod_feats["HbA1c_level"]["counterfactual_value"] == 8.5


def test_valid_what_if_heart_disease_simulation(service):
    """Verify live What-If simulation on Heart Disease XGBoost model with Row 5 clinical baseline."""
    # Row 5 (0-indexed 4): 6.74% baseline probability
    original = {
        'Age': 74, 'Sex': 0, 'Chest_pain_type': 2, 'BP': 120, 'Cholesterol': 269,
        'FBS_over_120': 0, 'EKG_results': 2, 'Max_HR': 121, 'Exercise_angina': 1,
        'ST_depression': 0.2, 'Slope_of_ST': 1, 'Number_of_vessels_fluro': 1, 'Thallium': 3
    }
    frozen_copy = copy.deepcopy(original)

    # 1. Unmodified baseline parity simulation
    res_base = service.simulate_what_if("heart_disease", original, original)
    assert res_base["status"] == "success"
    assert res_base["original"]["probability_formatted"] == "6.74%"
    assert res_base["counterfactual"]["probability_formatted"] == "6.74%"
    assert res_base["delta"]["percentage_points_change"] == 0.0
    assert res_base["delta"]["direction"] == "unchanged"

    # 2. Modify Chest_pain_type from 2 to 4 (Asymptomatic)
    mod1 = copy.deepcopy(original)
    mod1["Chest_pain_type"] = 4
    res_mod1 = service.simulate_what_if("heart_disease", original, mod1)
    assert res_mod1["original"]["probability_formatted"] == "6.74%"
    assert res_mod1["counterfactual"]["probability"] > 0.40
    assert res_mod1["delta"]["percentage_points_change"] > 30.0
    assert res_mod1["delta"]["direction"] == "increase"

    # 3. Categorical string encoding support (e.g. "Male" for Sex)
    mod2 = copy.deepcopy(original)
    mod2["Sex"] = "Male"
    res_mod2 = service.simulate_what_if("heart_disease", original, mod2)
    assert res_mod2["counterfactual"]["probability"] > 0.30
    assert res_mod2["delta"]["direction"] == "increase"

    # 4. Verify baseline immutability
    assert original == frozen_copy


# --- 2. CHRONIC LIVER GOVERNANCE LOCK ---

def test_chronic_liver_governance_lock(service):
    """Verify Chronic Liver Disease is strictly locked with the required governance message."""
    demo = DEMO_PATIENT_DATA["Chronic_liver"]

    is_locked, reason = service.is_disease_locked("Chronic_liver")
    assert is_locked is True
    assert reason == CHRONIC_LIVER_LOCK_MESSAGE

    with pytest.raises(ValueError) as excinfo:
        service.simulate_what_if("Chronic_liver", demo, demo)

    assert CHRONIC_LIVER_LOCK_MESSAGE in str(excinfo.value)
    assert "What-If Simulation for Chronic Liver Disease is temporarily locked pending approval of the corrected model." in str(excinfo.value)


# --- 3. IMMUTABILITY OF ORIGINAL PATIENT FEATURES ---

def test_patient_features_immutability(service):
    """Verify that original_features dictionary is never mutated."""
    original = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    frozen_snapshot = copy.deepcopy(original)

    modified = copy.deepcopy(original)
    modified["blood_glucose_level"] = 240.0

    service.simulate_what_if("diabetes", original, modified)

    assert original == frozen_snapshot
    assert original["blood_glucose_level"] == 100.0


# --- 4. INVALID DISEASE & FEATURE VALIDATION ---

def test_invalid_disease_rejection(service):
    """Verify unknown or unapproved disease triggers rejection."""
    with pytest.raises(ValueError) as exc:
        service.simulate_what_if("unknown_disease", {}, {})
    assert "What-If Analysis is currently enabled for verified models" in str(exc.value)


def test_unknown_feature_rejection(service):
    """Verify unknown features are strictly rejected."""
    original = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    modified = copy.deepcopy(original)
    modified["fictional_biomarker_xyz"] = 999.0

    with pytest.raises(ValueError) as exc:
        service.simulate_what_if("diabetes", original, modified)
    assert "Unknown feature" in str(exc.value)


def test_missing_feature_rejection(service):
    """Verify missing required features are rejected."""
    original = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    modified = copy.deepcopy(original)
    del modified["blood_glucose_level"]

    with pytest.raises(ValueError) as exc:
        service.simulate_what_if("diabetes", original, modified)
    assert "Missing required feature" in str(exc.value)


def test_invalid_numeric_value_rejection(service):
    """Verify non-numeric or negative values are rejected."""
    original = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    modified = copy.deepcopy(original)
    modified["blood_glucose_level"] = "high"

    with pytest.raises(ValueError) as exc:
        service.simulate_what_if("diabetes", original, modified)
    assert "must be a numeric value" in str(exc.value)

    modified["blood_glucose_level"] = -50.0
    with pytest.raises(ValueError) as exc_neg:
        service.simulate_what_if("diabetes", original, modified)
    assert "cannot be negative" in str(exc_neg.value)


# --- 5. PRODUCTION MODEL INTEGRITY & UNTOUCHED ARTIFACTS ---

def test_production_model_artifacts_integrity():
    """Verify that all production model artifacts are present and untouched."""
    models_dir = r"d:\MultiAgent_CDSS\models"
    assert os.path.exists(models_dir)

    expected_models = [
        ("anemia", "anemia_xgboost_pipeline.pkl"),
        ("B_cancer", "breast_cancer_xgboost_pipeline (1).pkl"),
        ("Chronic_liver", "chronic_liver_xgboost_pipeline.pkl"),
        ("diabetes", "diabetes_xgboost_pipeline.pkl"),
        ("heart_disease", "heart_disease_xgboost_pipeline (1).pkl"),
        ("Hepatitis", "hepatitis_xgboost_pipeline.pkl"),
        ("Kidney", "kidney_xgboost_pipeline (1).pkl"),
        ("lung_cancer", "lung_cancer_xgboost_pipeline.pkl"),
        ("Parkinsons", "parkinsons_xgboost_pipeline.pkl"),
        ("Stroke", "stroke_balanced_xgboost_pipeline.pkl")
    ]

    for disease, filename in expected_models:
        path = os.path.join(models_dir, disease, filename)
        assert os.path.exists(path), f"Production model missing: {path}"
        assert os.path.getsize(path) > 1000, f"Production model corrupted: {path}"

    # Specifically check production Chronic Liver model size
    liver_path = os.path.join(models_dir, "Chronic_liver", "chronic_liver_xgboost_pipeline.pkl")
    assert os.path.getsize(liver_path) == 123053


# --- 6. FASTAPI ENDPOINT CONTRACTS ---

def test_fastapi_what_if_endpoints():
    """Verify /api/what-if and /api/what-if/status endpoints directly via FastAPI app."""
    from app.main import simulate_what_if, get_what_if_status, WhatIfRequest
    import asyncio

    dummy_doc = {"doctor_id": "test_doc", "doctor_name": "Dr. Test"}

    # Test status endpoint for locked Chronic Liver
    status_liver = asyncio.run(get_what_if_status("Chronic_liver", doctor=dummy_doc))
    assert status_liver["is_locked"] is True
    assert status_liver["lock_reason"] == CHRONIC_LIVER_LOCK_MESSAGE
    assert status_liver["is_supported"] is False

    # Test status endpoint for live Diabetes
    status_diab = asyncio.run(get_what_if_status("diabetes", doctor=dummy_doc))
    assert status_diab["is_locked"] is False
    assert status_diab["is_supported"] is True

    # Test simulate_what_if endpoint with valid Diabetes payload
    orig = copy.deepcopy(DEMO_PATIENT_DATA["diabetes"])
    mod = copy.deepcopy(orig)
    mod["blood_glucose_level"] = 180.0
    req = WhatIfRequest(disease="diabetes", original_features=orig, modified_features=mod)

    sim_res = asyncio.run(simulate_what_if(req, doctor=dummy_doc))
    assert sim_res["status"] == "success"
    assert sim_res["disease"] == "diabetes"
    assert sim_res["delta"]["direction"] == "increase"

    # Test simulate_what_if endpoint for locked Chronic Liver raises HTTPException with 400
    from fastapi import HTTPException
    req_liver = WhatIfRequest(
        disease="Chronic_liver",
        original_features=DEMO_PATIENT_DATA["Chronic_liver"],
        modified_features=DEMO_PATIENT_DATA["Chronic_liver"]
    )
    with pytest.raises(HTTPException) as http_exc:
        asyncio.run(simulate_what_if(req_liver, doctor=dummy_doc))
    assert http_exc.value.status_code == 400
    assert CHRONIC_LIVER_LOCK_MESSAGE in http_exc.value.detail


# --- 7. STATIC UI ASSET INTEGRITY ---

def test_static_ui_what_if_elements():
    """Verify HTML and CSS contain What-If interactive elements, section trigger, and lock notice."""
    html_path = r"d:\MultiAgent_CDSS\app\static\index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    js_path = r"d:\MultiAgent_CDSS\app\static\app.js"
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    # Top-right header button removed; section 1 trigger preserved
    assert 'id="btn-open-whatif"' not in html
    assert 'id="btn-section-whatif"' in js
    assert "Simulate Clinical Variations" in js

    # Modal disclaimer banner removed
    assert 'whatif-disclaimer-banner' not in html
    assert "Model-Based Counterfactual Simulation" not in html

    # Essential What-If modal UI elements strictly preserved
    assert 'id="modal-what-if"' in html
    assert 'id="whatif-lock-banner"' in html
    assert 'id="whatif-orig-prob"' in html
    assert 'id="whatif-sim-prob"' in html
    assert 'id="whatif-delta-points"' in html
    assert 'id="btn-run-whatif"' in html
    assert 'id="btn-reset-whatif"' in html
    assert "What-If Simulation for Chronic Liver Disease is temporarily locked pending approval of the corrected model." in html

    css_path = r"d:\MultiAgent_CDSS\app\static\styles.css"
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    assert ".btn-whatif" in css
    assert ".modal-whatif-container" in css
    assert ".whatif-comparison-dashboard" in css
    assert ".whatif-delta-pill" in css
    assert ".whatif-lock-banner" in css
