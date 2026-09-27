"""
Unit Tests for Module 5 — Reasoning / Trust Layer.
Verifies contradiction detection, 3-way evidence categorization, consensus analysis,
missing SHAP weight renormalization, trust score determinism & bounds [0, 1], and ReasoningAgent integration.
"""

import pytest
from src.knowledge.schemas import (
    KnowledgeGraphEvidence,
    PhenotypeEvidence,
    GeneBiomarkerEvidence,
    DrugEvidence,
    ExposureEvidence,
    ComorbidityEvidence,
    EvidenceAgentResponse
)
from src.reasoning.schemas import (
    EvidenceCategoryItem,
    ContradictionAnalysis,
    ConsensusResult,
    TrustScoreResult,
    ReasoningOutput
)
from src.reasoning.contradiction_detector import ContradictionDetector
from src.reasoning.consensus_analyzer import ConsensusAnalyzer
from src.reasoning.trust_calculator import TrustCalculator
from src.reasoning.reasoning_engine import ReasoningEngine
from agents.reasoning_agent import ReasoningAgent


@pytest.fixture
def mock_high_risk_prediction():
    return {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "High Risk",
        "probability": 0.88,
        "status": "SUCCESS"
    }


@pytest.fixture
def mock_low_risk_prediction():
    return {
        "model_id": "diabetes",
        "predicted_class": 0,
        "predicted_label": "Low Risk",
        "probability": 0.12,
        "status": "SUCCESS"
    }


@pytest.fixture
def mock_shap_high_risk_aligned():
    return {
        "disease": "heart_disease",
        "prediction_probability": 0.88,
        "top_attributions": [
            {"feature_name": "cp", "shap_value": 0.35, "impact_direction": "increases_risk", "rank": 1},
            {"feature_name": "thalach", "shap_value": 0.22, "impact_direction": "increases_risk", "rank": 2}
        ]
    }


@pytest.fixture
def mock_shap_high_risk_conflicting():
    return {
        "disease": "heart_disease",
        "prediction_probability": 0.88,
        "top_attributions": [
            {"feature_name": "chol", "shap_value": -0.40, "impact_direction": "decreases_risk", "rank": 1}
        ]
    }


@pytest.fixture
def mock_graph_evidence_normal():
    return KnowledgeGraphEvidence(
        model_id="heart_disease",
        queried_disease_name="heart_disease",
        mapped_graph_node="heart disease",
        phenotypes=[
            PhenotypeEvidence(phenotype_name="Chest pain", relation_type="disease_phenotype_positive"),
            PhenotypeEvidence(phenotype_name="Shortness of breath", relation_type="disease_phenotype_positive")
        ],
        genes_biomarkers=[
            GeneBiomarkerEvidence(gene_symbol="ACE", relation_type="disease_protein")
        ],
        drugs=[
            DrugEvidence(drug_name="Aspirin", indication_type="indication"),
            DrugEvidence(drug_name="Warfarin", indication_type="off-label use")
        ],
        exposures=[
            ExposureEvidence(exposure_name="Tobacco smoke", relation_type="exposure_disease")
        ],
        comorbidities=[
            ComorbidityEvidence(disease_name="Hypertension", relation_type="disease_disease")
        ],
        total_triples_found=7
    )


@pytest.fixture
def mock_graph_evidence_conflicting():
    return KnowledgeGraphEvidence(
        model_id="heart_disease",
        queried_disease_name="heart_disease",
        mapped_graph_node="heart disease",
        phenotypes=[
            PhenotypeEvidence(phenotype_name="Abnormal symptom", relation_type="disease_phenotype_negative")
        ],
        drugs=[
            DrugEvidence(drug_name="Unsafe Drug", indication_type="contraindication")
        ],
        total_triples_found=2
    )


@pytest.fixture
def mock_graph_evidence_empty():
    return KnowledgeGraphEvidence(
        model_id="heart_disease",
        queried_disease_name="heart_disease",
        mapped_graph_node="heart disease",
        total_triples_found=0
    )


def test_insufficient_evidence_vs_contradiction(mock_high_risk_prediction, mock_graph_evidence_empty):
    """
    Test 1: Verify zero supporting graph triples results in INSUFFICIENT_EVIDENCE
    and has_contradictions == False (lack of evidence is NOT a contradiction).
    """
    detector = ContradictionDetector()
    analyzer = ConsensusAnalyzer()

    analysis = detector.analyze_evidence(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_empty,
        shap_explanation=None
    )

    assert analysis.has_contradictions is False
    assert analysis.conflicting_count == 0
    assert analysis.supporting_count == 0

    consensus = analyzer.evaluate_consensus(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_empty,
        contradiction_analysis=analysis,
        shap_explanation=None
    )

    assert consensus.consensus_level == "INSUFFICIENT_EVIDENCE"
    assert consensus.consensus_score == 0.0


def test_three_way_evidence_categorization(
    mock_high_risk_prediction,
    mock_graph_evidence_normal,
    mock_shap_high_risk_aligned
):
    """
    Test 2: Verify supporting, conflicting, and neutral items are correctly categorized.
    """
    detector = ContradictionDetector()
    analysis = detector.analyze_evidence(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_normal,
        shap_explanation=mock_shap_high_risk_aligned
    )

    assert isinstance(analysis, ContradictionAnalysis)
    assert analysis.supporting_count > 0
    assert analysis.neutral_count > 0  # Exposure, comorbidity, off-label drug
    assert analysis.conflicting_count == 0
    assert analysis.has_contradictions is False

    # Check categories
    supp_categories = [item.category for item in analysis.supporting_evidence]
    assert "phenotype" in supp_categories
    assert "drug" in supp_categories
    assert "gene_biomarker" in supp_categories
    assert "shap_attribution" in supp_categories

    neut_categories = [item.category for item in analysis.neutral_evidence]
    assert "exposure" in neut_categories
    assert "comorbidity" in neut_categories


def test_conflicting_evidence_categorization(
    mock_high_risk_prediction,
    mock_graph_evidence_conflicting,
    mock_shap_high_risk_conflicting
):
    """
    Test 3: Verify negative phenotypes, contraindications, and opposing SHAP features are flagged as conflicting.
    """
    detector = ContradictionDetector()
    analysis = detector.analyze_evidence(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_conflicting,
        shap_explanation=mock_shap_high_risk_conflicting
    )

    assert analysis.has_contradictions is True
    assert analysis.conflicting_count >= 3  # negative phenotype, contraindication, opposing SHAP
    assert analysis.supporting_count == 0

    analyzer = ConsensusAnalyzer()
    consensus = analyzer.evaluate_consensus(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_conflicting,
        contradiction_analysis=analysis,
        shap_explanation=mock_shap_high_risk_conflicting
    )

    assert consensus.consensus_level == "CONTRADICTORY_CONSENSUS"


def test_missing_shap_handling_and_weight_renormalization(
    mock_high_risk_prediction,
    mock_graph_evidence_normal
):
    """
    Test 4: Verify missing SHAP excludes SHAP factor and renormalizes remaining weights to sum to 1.0.
    """
    calculator = TrustCalculator()

    detector = ContradictionDetector()
    analysis = detector.analyze_evidence(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_normal,
        shap_explanation=None
    )

    trust = calculator.calculate_trust_score(
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_normal,
        contradiction_analysis=analysis,
        shap_explanation=None
    )

    assert trust.shap_status == "OMITTED_RENORMALIZED"
    assert trust.shap_alignment_factor is None
    assert "shap_alignment_factor" not in trust.weights_used

    # Active weights must sum to 1.0 (with floating precision tolerance)
    weight_sum = sum(trust.weights_used.values())
    assert abs(weight_sum - 1.0) < 1e-3

    # Check bounds
    assert 0.0 <= trust.overall_trust_score <= 1.0


def test_trust_score_bounds_and_determinism(
    mock_high_risk_prediction,
    mock_graph_evidence_normal,
    mock_shap_high_risk_aligned
):
    """
    Test 5: Verify trust score is strictly in [0, 1] and deterministic across runs.
    """
    agent = ReasoningAgent()

    out1 = agent.evaluate(
        model_id="heart_disease",
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_normal,
        shap_explanation=mock_shap_high_risk_aligned
    )

    out2 = agent.evaluate(
        model_id="heart_disease",
        prediction=mock_high_risk_prediction,
        graph_evidence=mock_graph_evidence_normal,
        shap_explanation=mock_shap_high_risk_aligned
    )

    assert isinstance(out1, ReasoningOutput)
    assert 0.0 <= out1.trust_score.overall_trust_score <= 1.0
    assert 0.0 <= out1.consensus_result.consensus_score <= 1.0

    # Deterministic equality
    assert out1.trust_score.overall_trust_score == out2.trust_score.overall_trust_score
    assert out1.consensus_result.consensus_level == out2.consensus_result.consensus_level
    assert len(out1.supporting_evidence) == len(out2.supporting_evidence)


def test_reasoning_agent_evaluate_evidence_payload(
    mock_high_risk_prediction,
    mock_graph_evidence_normal,
    mock_shap_high_risk_aligned
):
    """
    Test 6: Verify ReasoningAgent evaluates EvidenceAgentResponse payload cleanly.
    """
    agent = ReasoningAgent()

    payload = EvidenceAgentResponse(
        model_id="heart_disease",
        prediction=mock_high_risk_prediction,
        shap_explanation=mock_shap_high_risk_aligned,
        graph_evidence=mock_graph_evidence_normal,
        evidence_summary="Mock summary"
    )

    output = agent.evaluate_evidence_payload(payload)

    assert isinstance(output, ReasoningOutput)
    assert output.disease == "heart_disease"
    assert output.consensus_result.consensus_level == "STRONG_CONSENSUS"
    assert "=== CDSS Reasoning & Trust Evaluation Report" in output.reasoning_summary
