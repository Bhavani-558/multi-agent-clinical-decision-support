"""
Unit & Integration Tests for Dynamic Clinical Interpretation and Visible Safety Banner Removal.
Verifies:
1. The visible red contradiction safety banner is NOT rendered in the report UI.
2. The Clinical Interpretation is dynamic and adapts to input data.
3. Disease name comes from actual assessment data.
4. Risk factors and their directional impact come from actual SHAP explanation data.
5. Evidence status (supporting, conflicting, neutral counts) comes from actual PrimeKG evidence.
6. Conflicting evidence is naturally and correctly reflected in the explanation text.
7. Strongly supporting and insufficient evidence states are correctly distinguished.
8. Counterfactual simulation results are dynamically incorporated when present.
9. No hard-coded clinical explanation is returned.
10. Existing backend ML, fusion, trust, and safety-cap mechanisms remain intact.
"""

import os
import re
import pytest

from src.reporting.clinical_interpretation import generate_dynamic_clinical_interpretation
from src.fusion.fusion_engine import FusionEngine
from src.fusion.schemas import FusedConfidenceBreakdown
from src.reasoning.schemas import (
    EvidenceCategoryItem,
    ContradictionAnalysis,
    ConsensusResult,
    TrustScoreResult,
    ReasoningOutput,
)
from src.reporting.report_generator import ClinicalReportGenerator
from src.fusion.schemas import DecisionSupportClassification, ClinicalDecisionOutput


APP_JS_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "static", "app.js")
STYLES_CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "static", "styles.css")


@pytest.fixture(scope="module")
def app_js_content():
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def styles_css_content():
    with open(STYLES_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ==============================================================================
# Requirement 1 & 17.1: Visible Safety Banner Removed from Report UI
# ==============================================================================

def test_visible_safety_banner_not_rendered_in_report_ui(app_js_content):
    """Verify that the red 'CONTRADICTION SAFETY CAP ACTIVATED' warning banner is removed from visible report UI."""
    assert "CONTRADICTION SAFETY CAP ACTIVATED" not in app_js_content
    assert "The fused confidence score for this evaluation was capped at 0.50 due to contradictory biomedical evidence items." not in app_js_content


def test_underlying_safety_cap_chip_preserved(app_js_content):
    """Verify that the underlying safety constraint indicator chip (0.50 Capped) remains preserved in Section 5."""
    assert "0.50 Capped" in app_js_content
    assert "🛡️ Safety Cap:" in app_js_content


# ==============================================================================
# Requirement 2: FINAL SYSTEM DECISION Section & CLINICAL INTERPRETATION Heading
# ==============================================================================

def test_final_system_decision_section_structure_preserved(app_js_content):
    """Verify outer section title and inner clinical interpretation heading are preserved."""
    assert "FINAL SYSTEM DECISION" in app_js_content
    assert "🧠 CLINICAL INTERPRETATION" in app_js_content
    assert "final-system-decision-card" in app_js_content
    assert "llm-clinical-explanation-section" in app_js_content
    assert "llm-explanation-paragraph" in app_js_content


def test_styles_support_prominent_clinical_interpretation(styles_css_content):
    """Verify styles.css contains prominent styling rules for the standalone clinical interpretation card."""
    assert ".final-system-decision-card" in styles_css_content
    assert ".llm-explanation-title" in styles_css_content
    assert ".llm-explanation-paragraph" in styles_css_content
    assert ".llm-explanation-p" in styles_css_content


# ==============================================================================
# Requirement 17.2 & 17.7: Dynamic Generation (Not Hard-Coded)
# ==============================================================================

def test_dynamic_generation_yields_different_text_for_different_cases():
    """Verify that the explanation generator produces distinct, customized text for different clinical inputs."""
    case_hd = generate_dynamic_clinical_interpretation(
        disease_name="Heart Disease",
        is_detected=True,
        probability_formatted="85.97%",
        risk_tier="High Risk",
        shap_features=[
            {"feature": "Cholesterol", "impact": "Increases risk"},
            {"feature": "Number of Vessels Fluro", "impact": "Decreases risk"},
        ],
        total_triples=31,
        supporting_evidence=6,
        conflicting_evidence=10,
        neutral_evidence=15,
        consensus_level="CONTRADICTORY_CONSENSUS",
        trust_score=0.7015,
        fused_confidence=0.5000,
        has_conflicting_signals=True,
    )

    case_db = generate_dynamic_clinical_interpretation(
        disease_name="Diabetes",
        is_detected=False,
        probability_formatted="12.30%",
        risk_tier="Low Risk",
        shap_features=[
            {"feature": "Blood Glucose Level", "impact": "Decreases risk"},
            {"feature": "HbA1c Level", "impact": "Decreases risk"},
        ],
        total_triples=15,
        supporting_evidence=12,
        conflicting_evidence=0,
        neutral_evidence=3,
        consensus_level="STRONG_CONSENSUS",
        trust_score=0.8800,
        fused_confidence=0.8200,
        has_conflicting_signals=False,
    )

    # Must be distinct and not identical
    assert case_hd["full_text"] != case_db["full_text"]
    assert len(case_hd["paragraphs"]) == 3
    assert len(case_db["paragraphs"]) == 3

    # Check that old repetitive hard-coded sentence is NOT used
    assert "at or above the model’s 50% decision threshold" not in case_hd["full_text"]
    assert "below the model’s 50% decision threshold" not in case_db["full_text"]


# ==============================================================================
# Requirement 17.3: Disease Name from Actual Result
# ==============================================================================

def test_disease_name_comes_from_actual_result():
    """Verify disease name is dynamically incorporated into the explanation."""
    res_lung = generate_dynamic_clinical_interpretation(
        disease_name="Lung Cancer",
        is_detected=True,
        probability_formatted="91.20%",
        risk_tier="High Risk",
    )
    assert "lung cancer" in res_lung["paragraph1"].lower()

    res_anemia = generate_dynamic_clinical_interpretation(
        disease_name="Anemia",
        is_detected=False,
        probability_formatted="22.10%",
        risk_tier="Low Risk",
    )
    assert "anemia" in res_anemia["paragraph1"].lower()


# ==============================================================================
# Requirement 17.4: Risk Factors & Direction from Actual Explanation Data
# ==============================================================================

def test_risk_factors_and_directions_from_actual_data():
    """Verify that actual SHAP features and their directional impact are reflected without raw SHAP numbers."""
    shap_data = [
        {"feature": "Serum Cholesterol", "impact": "Increases risk"},
        {"feature": "Chest Pain Type", "impact": "Increases risk"},
        {"feature": "Resting ECG", "impact": "Decreases risk"},
    ]
    res = generate_dynamic_clinical_interpretation(
        disease_name="Heart Disease",
        is_detected=True,
        probability_formatted="78.40%",
        risk_tier="High Risk",
        shap_features=shap_data,
    )
    p1 = res["paragraph1"]
    assert "Serum Cholesterol" in p1
    assert "Chest Pain Type" in p1
    assert "Resting ECG" in p1
    assert "contributing toward higher risk" in p1
    assert "contributing toward lower risk" in p1


# ==============================================================================
# Requirement 17.5 & 17.6: Evidence Status & Conflicting Evidence
# ==============================================================================

def test_conflicting_evidence_reflected_naturally_without_red_banner():
    """Verify that when conflicting evidence is present, it is naturally discussed in Paragraph 2."""
    res = generate_dynamic_clinical_interpretation(
        disease_name="Heart Disease",
        is_detected=True,
        probability_formatted="85.97%",
        risk_tier="High Risk",
        mapped_node="coronary heart disease",
        total_triples=31,
        supporting_evidence=6,
        conflicting_evidence=10,
        neutral_evidence=15,
        has_conflicting_signals=True,
    )
    p2 = res["paragraph2"]
    assert "31 evidence relationships" in p2
    assert "6 supporting" in p2
    assert "10 conflicting" in p2
    assert "15 neutral" in p2
    assert "available biomedical evidence is not fully consistent with the model prediction" in p2
    assert "coronary heart disease" in p2


def test_strongly_supporting_evidence_reflects_alignment():
    """Verify that when evidence is strongly supporting, alignment with prediction is explained."""
    res = generate_dynamic_clinical_interpretation(
        disease_name="Diabetes",
        is_detected=False,
        probability_formatted="15.00%",
        risk_tier="Low Risk",
        mapped_node="type 2 diabetes",
        total_triples=20,
        supporting_evidence=18,
        conflicting_evidence=0,
        neutral_evidence=2,
        has_conflicting_signals=False,
    )
    p2 = res["paragraph2"]
    assert "strongly aligns with the model prediction" in p2
    assert "18 supporting" in p2
    assert "0 conflicting" in p2


def test_insufficient_evidence_explicitly_stated():
    """Verify that when evidence is limited or insufficient, it is explicitly communicated."""
    res = generate_dynamic_clinical_interpretation(
        disease_name="Hepatitis",
        is_detected=True,
        probability_formatted="65.00%",
        risk_tier="High Risk",
        mapped_node="chronic hepatitis",
        total_triples=0,
        supporting_evidence=0,
        conflicting_evidence=0,
        consensus_level="INSUFFICIENT_EVIDENCE",
    )
    p2 = res["paragraph2"]
    assert "available biomedical evidence is limited" in p2
    assert "insufficient data to independently confirm or refute" in p2


# ==============================================================================
# Counterfactual Simulation Dynamic Integration
# ==============================================================================

def test_counterfactual_simulation_integrated_when_available():
    """Verify that counterfactual what-if simulation data is dynamically incorporated into Paragraph 3."""
    cf_data = {
        "modified_features": [
            {"feature": "trestbps", "label": "Blood Pressure"},
            {"feature": "chol", "label": "Cholesterol"},
        ],
        "original": {"probability_formatted": "45.31%"},
        "counterfactual": {"probability_formatted": "28.50%"},
    }
    res = generate_dynamic_clinical_interpretation(
        disease_name="Heart Disease",
        is_detected=False,
        probability_formatted="45.31%",
        risk_tier="Low Risk",
        counterfactual_data=cf_data,
    )
    p3 = res["paragraph3"]
    assert "In counterfactual simulation" in p3
    assert "Blood Pressure, Cholesterol" in p3
    assert "45.31%" in p3
    assert "28.50%" in p3


# ==============================================================================
# Requirement 17.8: Backend Safety Cap Logic & Models Remain Intact
# ==============================================================================

def test_backend_safety_cap_logic_remains_active():
    """Verify that FusionEngine still caps confidence at 0.50 on contradiction."""
    engine = FusionEngine()
    contra_analysis = ContradictionAnalysis(
        supporting_evidence=[],
        conflicting_evidence=[
            EvidenceCategoryItem(
                category="phenotype",
                entity_name="test",
                relation_or_impact="conflicts",
                detail="test conflict",
                is_conflicting=True
            )
        ],
        neutral_evidence=[],
        supporting_count=0,
        conflicting_count=1,
        neutral_count=0,
        has_contradictions=True,
        contradiction_summary="Conflict found"
    )
    cons_result = ConsensusResult(
        consensus_level="CONTRADICTORY_CONSENSUS",
        consensus_score=0.40,
        disease_risk_tier="HIGH_RISK",
        explanation="Contradictory"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.75,
        confidence_factor=0.70,
        graph_evidence_factor=0.60,
        evidence_consistency_factor=0.40,
        shap_status="INCLUDED",
        logic_documentation="Test doc"
    )
    reasoning_out = ReasoningOutput(
        disease="heart_disease",
        model_id="heart_disease",
        prediction_summary={"probability": 0.85, "predicted_label": "Presence"},
        contradiction_analysis=contra_analysis,
        consensus_result=cons_result,
        trust_score=trust_score,
        reasoning_summary="Test summary"
    )

    fused = engine.calculate_fused_confidence(reasoning_out, DecisionSupportClassification.CONTRADICTION_FLAG)
    assert fused.is_capped_by_contradiction is True
    assert fused.overall_fused_score == 0.5000
    assert fused.cap_documentation.startswith("Fused confidence score capped at 0.50")


def test_report_generator_preserves_safety_cap():
    """Verify ClinicalReportGenerator preserves safety cap status and 0.50 score."""
    generator = ClinicalReportGenerator()
    fused = FusedConfidenceBreakdown(
        overall_fused_score=0.50,
        trust_component=0.25,
        consensus_component=0.15,
        model_confidence_component=0.10,
        is_capped_by_contradiction=True,
        cap_documentation="Contradiction safety ceiling = 0.50",
    )
    c_output = ClinicalDecisionOutput(
        disease="heart_disease",
        model_id="heart_disease",
        decision_classification=DecisionSupportClassification.CONTRADICTION_FLAG,
        fused_confidence=fused,
        overall_trust_score=0.65,
        consensus_level="CONTRADICTORY_CONSENSUS",
    )

    report = generator.generate_report(c_output)
    assert report.is_capped_by_contradiction is True
    assert report.fused_confidence_score == 0.50
