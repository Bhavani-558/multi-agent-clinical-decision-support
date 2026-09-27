"""
Unit Tests for Module 7 — Reporting Layer.
Verifies dynamic extraction of ClinicalDecisionOutput elements, 0-recalculation score preservation,
multi-format export (Markdown, Text, JSON), missing SHAP fallback, contradiction safety banners,
all 5 decision classification types, and non-prescriptive clinical compliance.
"""

import pytest
import json
from src.knowledge.schemas import (
    KnowledgeGraphEvidence,
    PhenotypeEvidence,
    DrugEvidence,
    GeneBiomarkerEvidence
)
from src.reasoning.schemas import (
    EvidenceCategoryItem,
    ContradictionAnalysis,
    ConsensusResult,
    TrustScoreResult,
    ReasoningOutput
)
from src.fusion.schemas import (
    DecisionSupportClassification,
    FusedConfidenceBreakdown,
    ClinicalDecisionOutput,
    UncertaintyFlag
)
from src.fusion.fusion_engine import FusionEngine
from src.reporting.schemas import ClinicalDecisionReport, ClinicalReportSection
from src.reporting.report_generator import ClinicalReportGenerator
from agents.reporting_agent import ReportingAgent


@pytest.fixture
def mock_high_risk_decision_output():
    """Mock ClinicalDecisionOutput for consistent High Risk case."""
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.88,
        "risk_tier": "HIGH_RISK",
        "status": "SUCCESS"
    }
    shap_summary = {
        "disease": "heart_disease",
        "base_value": 0.35,
        "shap_status": "INCLUDED",
        "top_attributions": [
            {"feature_name": "thalach", "attribution_value": 0.22, "feature_value": 150, "impact_direction": "increases_risk"},
            {"feature_name": "oldpeak", "attribution_value": 0.18, "feature_value": 2.5, "impact_direction": "increases_risk"}
        ]
    }
    evidence_summary = {
        "mapped_graph_node": "heart disease",
        "total_triples_found": 15,
        "supporting_count": 3,
        "conflicting_count": 0,
        "neutral_count": 2,
        "phenotype_count": 5,
        "drug_count": 4,
        "gene_count": 6
    }
    trust_and_consensus_summary = {
        "overall_trust_score": 0.8500,
        "confidence_factor": 0.7600,
        "shap_alignment_factor": 1.0000,
        "graph_evidence_factor": 0.8000,
        "evidence_consistency_factor": 1.0000,
        "shap_status": "INCLUDED",
        "weights_used": {"confidence_factor": 0.3, "shap_alignment_factor": 0.25, "graph_evidence_factor": 0.25, "evidence_consistency_factor": 0.2},
        "consensus_level": "STRONG_CONSENSUS",
        "consensus_score": 0.9000,
        "disease_risk_tier": "HIGH_RISK"
    }
    fused = FusedConfidenceBreakdown(
        overall_fused_score=0.8125,
        trust_component=0.3400,
        consensus_component=0.3150,
        model_confidence_component=0.1575,
        is_capped_by_contradiction=False,
        cap_documentation="Standard fused confidence score calculation applied without contradiction capping."
    )
    return ClinicalDecisionOutput(
        disease="heart_disease",
        model_id="heart_disease",
        decision_classification=DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT,
        fused_confidence=fused,
        prediction_summary=prediction_summary,
        shap_summary=shap_summary,
        evidence_summary=evidence_summary,
        trust_and_consensus_summary=trust_and_consensus_summary,
        decision_interpretation="High predicted risk supported by consistent knowledge evidence and/or SHAP attributions.",
        uncertainty_flags=[]
    )


@pytest.fixture
def mock_contradiction_decision_output():
    """Mock ClinicalDecisionOutput for Contradiction Flag case with Safety Cap."""
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.85,
        "risk_tier": "HIGH_RISK"
    }
    shap_summary = {"disease": "heart_disease", "shap_status": "INCLUDED", "top_attributions": []}
    evidence_summary = {
        "mapped_graph_node": "heart disease",
        "total_triples_found": 10,
        "supporting_count": 1,
        "conflicting_count": 2,
        "neutral_count": 1
    }
    trust_and_consensus_summary = {
        "overall_trust_score": 0.4000,
        "confidence_factor": 0.7000,
        "shap_alignment_factor": 0.0,
        "graph_evidence_factor": 0.5000,
        "evidence_consistency_factor": 0.0,
        "shap_status": "INCLUDED",
        "weights_used": {},
        "consensus_level": "CONTRADICTORY_CONSENSUS",
        "consensus_score": 0.0,
        "disease_risk_tier": "HIGH_RISK"
    }
    fused = FusedConfidenceBreakdown(
        overall_fused_score=0.5000,
        trust_component=0.1600,
        consensus_component=0.0000,
        model_confidence_component=0.1750,
        is_capped_by_contradiction=True,
        cap_documentation="Fused confidence score capped at 0.50 due to contradictory evidence."
    )
    flags = [
        UncertaintyFlag(flag_code="FLAG_CONTRADICTORY_EVIDENCE", description="Conflicting evidence detected", severity="HIGH")
    ]
    return ClinicalDecisionOutput(
        disease="heart_disease",
        model_id="heart_disease",
        decision_classification=DecisionSupportClassification.CONTRADICTION_FLAG,
        fused_confidence=fused,
        prediction_summary=prediction_summary,
        shap_summary=shap_summary,
        evidence_summary=evidence_summary,
        trust_and_consensus_summary=trust_and_consensus_summary,
        decision_interpretation="Conflicting evidence detected. Expert clinician audit required.",
        uncertainty_flags=flags
    )


@pytest.fixture
def mock_degraded_decision_output():
    """Mock ClinicalDecisionOutput for Degraded Confidence (Missing SHAP) case."""
    prediction_summary = {
        "model_id": "diabetes",
        "predicted_class": 1,
        "predicted_label": "High Risk",
        "probability": 0.75,
        "risk_tier": "HIGH_RISK"
    }
    shap_summary = {"disease": "diabetes", "shap_status": "OMITTED_RENORMALIZED", "top_attributions": []}
    evidence_summary = {"supporting_count": 2, "conflicting_count": 0, "neutral_count": 1}
    trust_and_consensus_summary = {
        "overall_trust_score": 0.6500,
        "confidence_factor": 0.5000,
        "shap_alignment_factor": None,
        "graph_evidence_factor": 0.6000,
        "evidence_consistency_factor": 1.0000,
        "shap_status": "OMITTED_RENORMALIZED",
        "consensus_level": "MODERATE_CONSENSUS",
        "consensus_score": 0.7000,
        "disease_risk_tier": "HIGH_RISK"
    }
    fused = FusedConfidenceBreakdown(
        overall_fused_score=0.6300,
        trust_component=0.2600,
        consensus_component=0.2450,
        model_confidence_component=0.1250,
        is_capped_by_contradiction=False,
        cap_documentation="Standard calculation."
    )
    flags = [
        UncertaintyFlag(flag_code="FLAG_MISSING_SHAP", description="SHAP feature attributions unavailable", severity="MEDIUM")
    ]
    return ClinicalDecisionOutput(
        disease="diabetes",
        model_id="diabetes",
        decision_classification=DecisionSupportClassification.DEGRADED_CONFIDENCE,
        fused_confidence=fused,
        prediction_summary=prediction_summary,
        shap_summary=shap_summary,
        evidence_summary=evidence_summary,
        trust_and_consensus_summary=trust_and_consensus_summary,
        decision_interpretation="Confidence is reduced because SHAP information is unavailable.",
        uncertainty_flags=flags
    )


# --- UNIT TESTS ---

def test_full_report_generation_structure(mock_high_risk_decision_output):
    """Test 1: Verify complete report generation containing all 7 dynamic sections and multi-format exports."""
    generator = ClinicalReportGenerator()
    report = generator.generate_report(mock_high_risk_decision_output)

    assert isinstance(report, ClinicalDecisionReport)
    assert report.disease == "heart_disease"
    assert report.decision_classification == "HIGH_RISK_DECISION_SUPPORT"
    assert len(report.sections) == 7

    section_ids = [sec.section_id for sec in report.sections]
    expected_ids = [
        "disease_prediction",
        "key_factors",
        "biomedical_evidence",
        "evidence_comparison",
        "trust_and_confidence",
        "final_interpretation",
        "export_and_disclaimer"
    ]
    assert section_ids == expected_ids

    # Check multi-format outputs
    assert len(report.markdown_report) > 0
    assert len(report.text_report) > 0
    assert isinstance(report.json_payload, dict)
    assert report.json_payload["disease"] == "heart_disease"


def test_exact_score_preservation(mock_high_risk_decision_output):
    """Test 2: Verify all upstream scores are preserved exactly without recalculation."""
    generator = ClinicalReportGenerator()
    report = generator.generate_report(mock_high_risk_decision_output)

    assert report.fused_confidence_score == 0.8125
    assert report.overall_trust_score == 0.8500
    assert report.consensus_level == "STRONG_CONSENSUS"

    # Check prediction section metric
    sec1 = report.sections[0]
    assert sec1.metrics["model_probability"] == "88.00%"
    assert sec1.metrics["model_decisiveness_factor"] == round(2.0 * abs(0.88 - 0.5), 4)

    # Check fused confidence section metric (Section 5)
    sec5 = report.sections[4]
    assert sec5.metrics["overall_fused_score"] == 0.8125
    assert sec5.metrics["trust_component"] == 0.3400
    assert sec5.metrics["consensus_component"] == 0.3150


def test_missing_shap_handling(mock_degraded_decision_output):
    """Test 3: Verify missing SHAP (OMITTED_RENORMALIZED) is handled gracefully without errors."""
    generator = ClinicalReportGenerator()
    report = generator.generate_report(mock_degraded_decision_output)

    sec2 = report.sections[1]  # SHAP section
    assert sec2.metrics["shap_status"] == "OMITTED_RENORMALIZED"
    assert "omitted or unavailable" in sec2.summary_text.lower()
    assert report.decision_classification == "DEGRADED_CONFIDENCE"


def test_contradiction_safety_banner(mock_contradiction_decision_output):
    """Test 4: Verify contradiction flag triggers safety cap documentation and Markdown callout."""
    generator = ClinicalReportGenerator()
    report = generator.generate_report(mock_contradiction_decision_output)

    assert report.is_capped_by_contradiction is True
    assert report.fused_confidence_score == 0.5000
    assert "CONTRADICTION SAFETY CAP ACTIVATED" in report.markdown_report
    assert "ACTIVATED (CAPPED AT 0.50)" in report.text_report


def test_all_five_classifications():
    """Test 5: Verify report generator executes successfully for all 5 Module 6 decision classifications."""
    generator = ClinicalReportGenerator()
    classifications = [
        DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT,
        DecisionSupportClassification.LOW_RISK_DECISION_SUPPORT,
        DecisionSupportClassification.CONTRADICTION_FLAG,
        DecisionSupportClassification.INSUFFICIENT_EVIDENCE,
        DecisionSupportClassification.DEGRADED_CONFIDENCE
    ]

    for cat in classifications:
        fused = FusedConfidenceBreakdown(
            overall_fused_score=0.50 if cat == DecisionSupportClassification.CONTRADICTION_FLAG else 0.75,
            trust_component=0.30,
            consensus_component=0.25,
            model_confidence_component=0.20,
            is_capped_by_contradiction=(cat == DecisionSupportClassification.CONTRADICTION_FLAG),
            cap_documentation="Cap test"
        )
        c_output = ClinicalDecisionOutput(
            disease="test_disease",
            model_id="test_model",
            decision_classification=cat,
            fused_confidence=fused,
            prediction_summary={"probability": 0.70, "predicted_label": "Risk", "risk_tier": "HIGH_RISK"},
            shap_summary={"shap_status": "INCLUDED", "top_attributions": []},
            evidence_summary={"supporting_count": 1, "conflicting_count": 0, "neutral_count": 0},
            trust_and_consensus_summary={"overall_trust_score": 0.75, "consensus_level": "MODERATE_CONSENSUS"},
            decision_interpretation=f"Test interpretation for {cat.value}",
            uncertainty_flags=[]
        )

        report = generator.generate_report(c_output)
        assert report.decision_classification == cat.value
        assert len(report.sections) == 7
        assert cat.value in report.markdown_report


def test_non_prescriptive_compliance(mock_high_risk_decision_output):
    """Test 6: Verify generated report text strictly adheres to non-prescriptive, decision-support guidelines."""
    generator = ClinicalReportGenerator()
    report = generator.generate_report(mock_high_risk_decision_output)

    text_content = (report.markdown_report + "\n" + report.text_report).lower()

    # Forbidden prescription / autonomous clinical treatment terms
    forbidden_terms = ["mg/day", "take orally", "prescribe", "administer 50", "recommended dosage"]

    for term in forbidden_terms:
        assert term not in text_content, f"Forbidden prescriptive term '{term}' found in clinical report text!"

    # Required decision support disclaimer terms in Section 7 audit metadata
    sec7_text = report.sections[6].summary_text.lower()
    assert "machine-assisted clinical decision support" in sec7_text
    assert "not constitute a clinical diagnosis" in sec7_text

    # Verify disclaimer note is completely removed from downloaded markdown and text reports
    assert "not constitute a clinical diagnosis" not in text_content


def test_reporting_agent_integration(mock_high_risk_decision_output):
    """Test 7: Verify ReportingAgent wrapper executes report generation seamlessly."""
    agent = ReportingAgent()
    report = agent.generate_report(mock_high_risk_decision_output)

    assert isinstance(report, ClinicalDecisionReport)
    assert report.disease == "heart_disease"
    assert report.decision_classification == "HIGH_RISK_DECISION_SUPPORT"
