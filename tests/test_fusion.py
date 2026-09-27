"""
Unit Tests for Module 6 — Decision / Fusion Layer.
Verifies decision-support classifications, fused confidence calculation, contradiction cap,
missing SHAP degraded confidence handling, score bounds, determinism, and Module 5 trust score preservation.
"""

import pytest
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
from src.fusion.decision_classifier import DecisionClassifier
from src.fusion.fusion_engine import FusionEngine
from agents.fusion_agent import FusionAgent


@pytest.fixture
def mock_reasoning_high_risk_consistent():
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.88,
        "status": "SUCCESS"
    }
    contradiction_analysis = ContradictionAnalysis(
        supporting_evidence=[
            EvidenceCategoryItem(category="phenotype", entity_name="Chest pain", relation_or_impact="disease_phenotype_positive", detail="Chest pain", is_supporting=True)
        ],
        conflicting_evidence=[],
        neutral_evidence=[],
        supporting_count=1,
        conflicting_count=0,
        neutral_count=0,
        has_contradictions=False,
        contradiction_summary="Consistent evidence"
    )
    consensus_result = ConsensusResult(
        consensus_level="STRONG_CONSENSUS",
        consensus_score=0.90,
        disease_risk_tier="HIGH_RISK",
        explanation="Strong consensus"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.85,
        confidence_factor=0.76,
        shap_alignment_factor=1.0,
        graph_evidence_factor=0.80,
        evidence_consistency_factor=1.0,
        shap_status="INCLUDED",
        weights_used={"confidence_factor": 0.3, "shap_alignment_factor": 0.25, "graph_evidence_factor": 0.25, "evidence_consistency_factor": 0.2},
        logic_documentation="Doc"
    )
    return ReasoningOutput(
        disease="heart_disease",
        model_id="heart_disease",
        prediction_summary=prediction_summary,
        contradiction_analysis=contradiction_analysis,
        supporting_evidence=contradiction_analysis.supporting_evidence,
        conflicting_evidence=[],
        neutral_evidence=[],
        consensus_result=consensus_result,
        trust_score=trust_score,
        reasoning_summary="Summary text"
    )


@pytest.fixture
def mock_reasoning_low_risk_consistent():
    prediction_summary = {
        "model_id": "diabetes",
        "predicted_class": 0,
        "predicted_label": "Low Risk",
        "probability": 0.12,
        "status": "SUCCESS"
    }
    contradiction_analysis = ContradictionAnalysis(
        supporting_evidence=[
            EvidenceCategoryItem(category="shap_attribution", entity_name="bmi", relation_or_impact="decreases_risk", detail="Low BMI", is_supporting=True)
        ],
        conflicting_evidence=[],
        neutral_evidence=[],
        supporting_count=1,
        conflicting_count=0,
        neutral_count=0,
        has_contradictions=False,
        contradiction_summary="Consistent evidence"
    )
    consensus_result = ConsensusResult(
        consensus_level="STRONG_CONSENSUS",
        consensus_score=0.90,
        disease_risk_tier="LOW_RISK",
        explanation="Strong consensus"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.82,
        confidence_factor=0.76,
        shap_alignment_factor=1.0,
        graph_evidence_factor=0.70,
        evidence_consistency_factor=1.0,
        shap_status="INCLUDED",
        weights_used={"confidence_factor": 0.3, "shap_alignment_factor": 0.25, "graph_evidence_factor": 0.25, "evidence_consistency_factor": 0.2},
        logic_documentation="Doc"
    )
    return ReasoningOutput(
        disease="diabetes",
        model_id="diabetes",
        prediction_summary=prediction_summary,
        contradiction_analysis=contradiction_analysis,
        supporting_evidence=contradiction_analysis.supporting_evidence,
        conflicting_evidence=[],
        neutral_evidence=[],
        consensus_result=consensus_result,
        trust_score=trust_score,
        reasoning_summary="Summary text"
    )


@pytest.fixture
def mock_reasoning_contradiction():
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.85,
        "status": "SUCCESS"
    }
    contradiction_analysis = ContradictionAnalysis(
        supporting_evidence=[],
        conflicting_evidence=[
            EvidenceCategoryItem(category="drug", entity_name="Contraindicated Drug", relation_or_impact="contraindication", detail="Contraindicated", is_conflicting=True),
            EvidenceCategoryItem(category="phenotype", entity_name="Negative Phenotype", relation_or_impact="disease_phenotype_negative", detail="Negative", is_conflicting=True)
        ],
        neutral_evidence=[],
        supporting_count=0,
        conflicting_count=2,
        neutral_count=0,
        has_contradictions=True,
        contradiction_summary="Contradictions detected"
    )
    consensus_result = ConsensusResult(
        consensus_level="CONTRADICTORY_CONSENSUS",
        consensus_score=0.0,
        disease_risk_tier="HIGH_RISK",
        explanation="Contradictory consensus"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.40,
        confidence_factor=0.70,
        shap_alignment_factor=0.0,
        graph_evidence_factor=0.50,
        evidence_consistency_factor=0.0,
        shap_status="INCLUDED",
        weights_used={"confidence_factor": 0.3, "shap_alignment_factor": 0.25, "graph_evidence_factor": 0.25, "evidence_consistency_factor": 0.2},
        logic_documentation="Doc"
    )
    return ReasoningOutput(
        disease="heart_disease",
        model_id="heart_disease",
        prediction_summary=prediction_summary,
        contradiction_analysis=contradiction_analysis,
        supporting_evidence=[],
        conflicting_evidence=contradiction_analysis.conflicting_evidence,
        neutral_evidence=[],
        consensus_result=consensus_result,
        trust_score=trust_score,
        reasoning_summary="Summary text"
    )


@pytest.fixture
def mock_reasoning_insufficient_evidence():
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.85,
        "status": "SUCCESS"
    }
    contradiction_analysis = ContradictionAnalysis(
        supporting_evidence=[],
        conflicting_evidence=[],
        neutral_evidence=[],
        supporting_count=0,
        conflicting_count=0,
        neutral_count=0,
        has_contradictions=False,
        contradiction_summary="Insufficient evidence"
    )
    consensus_result = ConsensusResult(
        consensus_level="INSUFFICIENT_EVIDENCE",
        consensus_score=0.0,
        disease_risk_tier="HIGH_RISK",
        explanation="Insufficient evidence"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.30,
        confidence_factor=0.70,
        shap_alignment_factor=None,
        graph_evidence_factor=0.0,
        evidence_consistency_factor=1.0,
        shap_status="OMITTED_RENORMALIZED",
        weights_used={"confidence_factor": 0.4, "graph_evidence_factor": 0.3333, "evidence_consistency_factor": 0.2667},
        logic_documentation="Doc"
    )
    return ReasoningOutput(
        disease="heart_disease",
        model_id="heart_disease",
        prediction_summary=prediction_summary,
        contradiction_analysis=contradiction_analysis,
        supporting_evidence=[],
        conflicting_evidence=[],
        neutral_evidence=[],
        consensus_result=consensus_result,
        trust_score=trust_score,
        reasoning_summary="Summary text"
    )


@pytest.fixture
def mock_reasoning_degraded_confidence():
    prediction_summary = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "predicted_label": "Presence",
        "probability": 0.85,
        "status": "SUCCESS"
    }
    contradiction_analysis = ContradictionAnalysis(
        supporting_evidence=[
            EvidenceCategoryItem(category="phenotype", entity_name="Chest pain", relation_or_impact="disease_phenotype_positive", detail="Chest pain", is_supporting=True)
        ],
        conflicting_evidence=[],
        neutral_evidence=[],
        supporting_count=1,
        conflicting_count=0,
        neutral_count=0,
        has_contradictions=False,
        contradiction_summary="Consistent evidence"
    )
    consensus_result = ConsensusResult(
        consensus_level="MODERATE_CONSENSUS",
        consensus_score=0.70,
        disease_risk_tier="HIGH_RISK",
        explanation="Moderate consensus"
    )
    trust_score = TrustScoreResult(
        overall_trust_score=0.68,
        confidence_factor=0.70,
        shap_alignment_factor=None,
        graph_evidence_factor=0.60,
        evidence_consistency_factor=1.0,
        shap_status="OMITTED_RENORMALIZED",
        weights_used={"confidence_factor": 0.4, "graph_evidence_factor": 0.3333, "evidence_consistency_factor": 0.2667},
        logic_documentation="Doc"
    )
    return ReasoningOutput(
        disease="heart_disease",
        model_id="heart_disease",
        prediction_summary=prediction_summary,
        contradiction_analysis=contradiction_analysis,
        supporting_evidence=contradiction_analysis.supporting_evidence,
        conflicting_evidence=[],
        neutral_evidence=[],
        consensus_result=consensus_result,
        trust_score=trust_score,
        reasoning_summary="Summary text"
    )


def test_high_risk_case(mock_reasoning_high_risk_consistent):
    """Test 1: Verify high-risk probability + consistent high trust -> HIGH_RISK_DECISION_SUPPORT."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_high_risk_consistent)

    assert isinstance(output, ClinicalDecisionOutput)
    assert output.decision_classification == DecisionSupportClassification.HIGH_RISK_DECISION_SUPPORT
    assert output.fused_confidence.overall_fused_score > 0.60
    assert output.fused_confidence.is_capped_by_contradiction is False


def test_low_risk_case(mock_reasoning_low_risk_consistent):
    """Test 2: Verify low-risk probability + consistent high trust -> LOW_RISK_DECISION_SUPPORT."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_low_risk_consistent)

    assert isinstance(output, ClinicalDecisionOutput)
    assert output.decision_classification == DecisionSupportClassification.LOW_RISK_DECISION_SUPPORT
    assert output.fused_confidence.overall_fused_score > 0.60
    assert output.fused_confidence.is_capped_by_contradiction is False


def test_contradiction_case(mock_reasoning_contradiction):
    """Test 3: Verify conflicting evidence -> CONTRADICTION_FLAG and 0.50 safety cap applied."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_contradiction)

    assert output.decision_classification == DecisionSupportClassification.CONTRADICTION_FLAG
    assert output.fused_confidence.is_capped_by_contradiction is True
    assert output.fused_confidence.overall_fused_score <= 0.50
    assert "safety rule" in output.fused_confidence.cap_documentation.lower()


def test_insufficient_evidence_case(mock_reasoning_insufficient_evidence):
    """Test 4: Verify zero triples / INSUFFICIENT_EVIDENCE -> INSUFFICIENT_EVIDENCE classification."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_insufficient_evidence)

    assert output.decision_classification == DecisionSupportClassification.INSUFFICIENT_EVIDENCE
    assert any(flag.flag_code == "FLAG_ZERO_GRAPH_TRIPLES" for flag in output.uncertainty_flags)


def test_degraded_confidence_case(mock_reasoning_degraded_confidence):
    """Test 5: Verify missing SHAP (OMITTED_RENORMALIZED) -> DEGRADED_CONFIDENCE classification."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_degraded_confidence)

    assert output.decision_classification == DecisionSupportClassification.DEGRADED_CONFIDENCE
    assert any(flag.flag_code == "FLAG_MISSING_SHAP" for flag in output.uncertainty_flags)


def test_fused_score_bounds_and_determinism(mock_reasoning_high_risk_consistent):
    """Test 6: Verify fused confidence score is bounded in [0, 1] and deterministic across runs."""
    agent = FusionAgent()
    out1 = agent.evaluate(mock_reasoning_high_risk_consistent)
    out2 = agent.evaluate(mock_reasoning_high_risk_consistent)

    assert 0.0 <= out1.fused_confidence.overall_fused_score <= 1.0
    assert out1.fused_confidence.overall_fused_score == out2.fused_confidence.overall_fused_score
    assert out1.decision_classification == out2.decision_classification


def test_preservation_of_module5_trust_score(mock_reasoning_high_risk_consistent):
    """Test 7: Verify Module 5 Trust Score is preserved without recalculation or replacement."""
    agent = FusionAgent()
    output = agent.evaluate(mock_reasoning_high_risk_consistent)

    input_trust = mock_reasoning_high_risk_consistent.trust_score.overall_trust_score
    preserved_trust = output.trust_and_consensus_summary["overall_trust_score"]

    assert preserved_trust == input_trust
    assert output.trust_and_consensus_summary["shap_status"] == mock_reasoning_high_risk_consistent.trust_score.shap_status
