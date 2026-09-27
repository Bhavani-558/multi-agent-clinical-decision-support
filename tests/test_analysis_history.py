import json
from pathlib import Path

import pytest

from app.analysis_history_db import AnalysisHistoryDB


@pytest.fixture
def history_db(tmp_path):
    db_path = tmp_path / "history.sqlite3"
    db = AnalysisHistoryDB(str(db_path))
    yield db
    db.close()


def test_history_db_creates_and_queries_records(history_db):
    record_id = history_db.save_analysis(
        doctor_id="doc@example.com",
        patient_id="P001",
        patient_name="Rahul Kumar",
        disease="heart_disease",
        prediction="Presence",
        model_probability=0.87,
        clinical_input_data={"Age": 58, "Sex": 1},
        shap_data={"top_attributions": [{"feature_name": "Age"}]},
        evidence_data={"supporting": 3},
        reasoning_data={"summary": "Reasoning summary"},
        trust_confidence_data={"trust_score": 0.8},
        report_data={"sections": [{"section_id": "disease_prediction"}]},
        final_interpretation="Interpretation",
    )

    assert record_id is not None
    assert history_db.get_history(doctor_id="doc@example.com")[0]["patient_id"] == "P001"
    assert history_db.get_patient_history(patient_id="P001", doctor_id="doc@example.com")[0]["disease"] == "heart_disease"
    assert history_db.get_history(doctor_id="doc@example.com", search="Rahul")[0]["patient_name"] == "Rahul Kumar"
    assert history_db.get_history(doctor_id="doc@example.com", disease_filter="heart_disease")[0]["prediction"] == "Presence"


def test_history_db_keeps_same_patient_multiple_analyses_separate(history_db):
    history_db.save_analysis(
        doctor_id="doc@example.com",
        patient_id="P001",
        patient_name="Rahul Kumar",
        disease="heart_disease",
        prediction="Presence",
        model_probability=0.81,
        clinical_input_data={"Age": 50},
        report_data={"sections": [{"section_id": "disease_prediction"}]},
    )
    history_db.save_analysis(
        doctor_id="doc@example.com",
        patient_id="P001",
        patient_name="Rahul Kumar",
        disease="heart_disease",
        prediction="Absence",
        model_probability=0.42,
        clinical_input_data={"Age": 52},
        report_data={"sections": [{"section_id": "disease_prediction"}]},
    )

    rows = history_db.get_patient_history(patient_id="P001", doctor_id="doc@example.com")
    assert len(rows) == 2
    assert {row["prediction"] for row in rows} == {"Presence", "Absence"}


def test_history_db_uses_doctor_scope_and_patient_search(history_db):
    history_db.save_analysis(
        doctor_id="doc1@example.com",
        patient_id="P002",
        patient_name="Test User",
        disease="diabetes",
        prediction="Presence",
        model_probability=0.61,
        report_data={"sections": []},
    )
    history_db.save_analysis(
        doctor_id="doc2@example.com",
        patient_id="P003",
        patient_name="Another User",
        disease="stroke",
        prediction="Absence",
        model_probability=0.23,
        report_data={"sections": []},
    )

    assert len(history_db.get_history(doctor_id="doc1@example.com")) == 1
    assert history_db.get_history(doctor_id="doc1@example.com", patient_id_filter="P002")[0]["patient_name"] == "Test User"
    assert history_db.get_history(doctor_id="doc1@example.com", search="Test")[0]["patient_name"] == "Test User"
