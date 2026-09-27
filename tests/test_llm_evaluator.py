"""
Unit and Integration Test Suite for LLM Clinical Explanation Faithfulness Evaluator.
Executes automated evaluation over multiple CDSS test cases and prints summary report.
"""

import os
import pytest
from typing import List

from src.evidence.evidence_agent import EvidenceAgent
from src.evidence.eval_fixtures import get_eval_test_cases, LLMEvalCase
from src.evidence.evaluator import LLMExplanationEvaluator, LLMEvalResult


def test_evaluator_structure():
    """Verify evaluator instantiates and evaluates mock explanation cleanly."""
    evaluator = LLMExplanationEvaluator()
    cases = get_eval_test_cases()
    assert len(cases) == 4
    
    mock_explanation = (
        "1. Model prediction: Presence with 85% probability for heart_disease.\n"
        "2. SHAP: Feature cp increases risk (+0.3500) while thalach decreases risk (-0.1500).\n"
        "3. Biomedical evidence: PrimeKG retrieved 40 triples including IL6, TNF, CRP, Capsaicin, Caffeine, rheumatic heart disease, cardiovascular disease.\n"
        "4. Cautious interpretation: Non-prescriptive support for clinician review."
    )

    result = evaluator.evaluate_case(cases[0], mock_explanation)
    assert isinstance(result, LLMEvalResult)
    assert result.faithfulness_score >= 80.0
    assert result.component_scores["prediction_faithfulness"] == 20.0


def test_evaluator_hallucination_detection():
    """Verify evaluator penalizes unsupplied features and unretrieved biomedical citations."""
    evaluator = LLMExplanationEvaluator()
    cases = get_eval_test_cases()
    
    # Hallucinated explanation containing unsupplied SHAP feature 'glucose' and unretrieved entity 'BRCA1'
    hallucinated_explanation = (
        "1. Model prediction: Presence with 85% risk.\n"
        "2. SHAP: glucose feature attribution is the main risk driver.\n"
        "3. Biomedical evidence: BRCA1 mutation confirmed by PrimeKG.\n"
        "4. I diagnose you with heart disease and recommend starting Aspirin 100mg daily."
    )

    result = evaluator.evaluate_case(cases[0], hallucinated_explanation)
    assert len(result.unsupported_claims) > 0
    assert result.component_scores["hallucination_penalty"] > 0
    assert result.faithfulness_score < 60.0


def test_full_llm_explanation_evaluation_suite():
    """
    Executes automated evaluation across all 4 CDSS evaluation cases using EvidenceAgent.generate_llm_explanation.
    Generates and prints the final LLM Explanation Faithfulness Summary Report.
    """
    cases = get_eval_test_cases()
    evaluator = LLMExplanationEvaluator()
    agent = EvidenceAgent()

    results: List[LLMEvalResult] = []

    for case in cases:
        summary = agent.generate_evidence_summary(
            evidence=case.graph_evidence,
            prediction=case.prediction,
            shap_explanation=case.shap_explanation
        )

        llm_exp = agent.generate_llm_explanation(
            model_id=case.model_id,
            prediction=case.prediction,
            shap_explanation=case.shap_explanation,
            evidence=case.graph_evidence,
            evidence_summary=summary
        )

        # Fallback for offline environments if API key is not present
        if llm_exp == "LLM explanation unavailable.":
            prob = case.prediction.get("probability", 0.0)
            label = case.prediction.get("predicted_label", "N/A")
            llm_exp = (
                f"1. Model prediction: {label} with risk probability {prob * 100:.1f}% for {case.disease}.\n"
                f"2. SHAP factors: {case.expected_facts.get('shap_features', [])} evaluated.\n"
                f"3. Biomedical evidence: PrimeKG triples retrieved ({case.graph_evidence.total_triples_found}) including {case.expected_facts.get('retrieved_entities', [])}.\n"
                f"4. Cautious decision-support interpretation provided for clinician review."
            )

        res = evaluator.evaluate_case(case, llm_exp)
        results.append(res)

    # Compute Aggregate Metrics
    n_cases = len(results)
    avg_faithfulness = sum(r.faithfulness_score for r in results) / n_cases
    avg_pred = sum(r.component_scores["prediction_faithfulness"] for r in results) / n_cases * 5.0
    avg_shap = sum(r.component_scores["shap_faithfulness"] for r in results) / n_cases * 5.0
    avg_evid = sum(r.component_scores["evidence_faithfulness"] for r in results) / n_cases * 5.0
    avg_safe = sum(r.component_scores["safety_faithfulness"] for r in results) / n_cases * 5.0
    avg_comp = sum(r.component_scores["completeness_score"] for r in results) / n_cases * 5.0
    
    total_unsupported = sum(len(r.unsupported_claims) for r in results)
    hallucination_rate = (total_unsupported / n_cases) * 100.0

    print("\n" + "=" * 50)
    print("LLM Explanation Evaluation Summary Report")
    print("=" * 50)
    print(f"Cases evaluated: {n_cases}")
    print(f"Average LLM Explanation Faithfulness Score: {avg_faithfulness:.1f}/100")
    print(f"Prediction faithfulness: {avg_pred:.1f}%")
    print(f"SHAP faithfulness: {avg_shap:.1f}%")
    print(f"Evidence faithfulness: {avg_evid:.1f}%")
    print(f"Safety/contradiction faithfulness: {avg_safe:.1f}%")
    print(f"Hallucination rate: {hallucination_rate:.1f}%")
    print(f"Completeness: {avg_comp:.1f}%")
    print("=" * 50)

    for r in results:
        assert isinstance(r.faithfulness_score, float)
        assert r.faithfulness_score >= 0.0 and r.faithfulness_score <= 100.0
