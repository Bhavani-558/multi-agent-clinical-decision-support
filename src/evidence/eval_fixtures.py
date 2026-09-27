"""
Evaluation Test Cases and Fixtures for LLM Clinical Explanation Faithfulness.
Contains representative CDSS cases covering supporting, conflicting, low-risk, and degraded SHAP scenarios.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from src.knowledge.schemas import (
    KnowledgeGraphEvidence,
    GeneBiomarkerEvidence,
    DrugEvidence,
    ComorbidityEvidence,
    PhenotypeEvidence
)


@dataclass
class LLMEvalCase:
    case_id: str
    disease: str
    description: str
    model_id: str
    prediction: Dict[str, Any]
    shap_explanation: Dict[str, Any]
    graph_evidence: KnowledgeGraphEvidence
    safety_context: Dict[str, Any]
    expected_facts: Dict[str, Any]


def get_eval_test_cases() -> List[LLMEvalCase]:
    """
    Returns a suite of 4 representative CDSS evaluation cases.
    """
    # Case 1: High-risk Heart Disease with strong supporting biomedical evidence
    case1_graph = KnowledgeGraphEvidence(
        model_id="heart_disease",
        queried_disease_name="heart_disease",
        mapped_graph_node="heart disease",
        phenotypes=[
            PhenotypeEvidence(phenotype_name="Chest Pain", relation_type="disease_phenotype")
        ],
        genes_biomarkers=[
            GeneBiomarkerEvidence(gene_symbol="IL6", relation_type="disease_protein"),
            GeneBiomarkerEvidence(gene_symbol="TNF", relation_type="disease_protein"),
            GeneBiomarkerEvidence(gene_symbol="CRP", relation_type="disease_protein")
        ],
        drugs=[
            DrugEvidence(drug_name="Capsaicin", indication_type="contraindication"),
            DrugEvidence(drug_name="Caffeine", indication_type="contraindication")
        ],
        comorbidities=[
            ComorbidityEvidence(disease_name="rheumatic heart disease", relation_type="disease_disease"),
            ComorbidityEvidence(disease_name="cardiovascular disease", relation_type="disease_disease")
        ],
        total_triples_found=40
    )

    case1 = LLMEvalCase(
        case_id="case_1_heart_disease_high_risk",
        disease="heart_disease",
        description="High-risk heart disease prediction with positive SHAP chest pain and supporting PrimeKG triples.",
        model_id="heart_disease",
        prediction={"predicted_label": "Presence", "probability": 0.85},
        shap_explanation={
            "top_features": [
                {"feature_name": "cp", "shap_value": 0.35, "raw_value": 3},
                {"feature_name": "thalach", "shap_value": -0.15, "raw_value": 150}
            ]
        },
        graph_evidence=case1_graph,
        safety_context={
            "contradiction_flag_raised": False,
            "is_capped_by_contradiction": False,
            "fused_confidence": 0.85
        },
        expected_facts={
            "predicted_label": "Presence",
            "probability_pct": 85.0,
            "shap_features": ["cp", "thalach"],
            "positive_shap_features": ["cp"],
            "negative_shap_features": ["thalach"],
            "retrieved_entities": ["IL6", "TNF", "CRP", "Capsaicin", "Caffeine", "rheumatic heart disease", "cardiovascular disease"],
            "contradiction_expected": False
        }
    )

    # Case 2: Diabetes with mixed/contradictory evidence (Safety Cap Applied)
    case2_graph = KnowledgeGraphEvidence(
        model_id="diabetes",
        queried_disease_name="diabetes",
        mapped_graph_node="diabetes mellitus",
        phenotypes=[
            PhenotypeEvidence(phenotype_name="Polyuria", relation_type="disease_phenotype"),
            PhenotypeEvidence(phenotype_name="Polydipsia", relation_type="disease_phenotype")
        ],
        genes_biomarkers=[
            GeneBiomarkerEvidence(gene_symbol="INS", relation_type="disease_protein")
        ],
        drugs=[
            DrugEvidence(drug_name="Metformin", indication_type="indication"),
            DrugEvidence(drug_name="Glipizide", indication_type="contraindication")
        ],
        comorbidities=[
            ComorbidityEvidence(disease_name="essential hypertension", relation_type="disease_disease")
        ],
        total_triples_found=25
    )

    case2 = LLMEvalCase(
        case_id="case_2_diabetes_contradiction_mixed",
        disease="diabetes",
        description="Mixed diabetes prediction with high glucose but normal BMI, conflicting drug indications, and safety cap applied.",
        model_id="diabetes",
        prediction={"predicted_label": "Presence", "probability": 0.62},
        shap_explanation={
            "top_features": [
                {"feature_name": "Glucose", "shap_value": 0.45, "raw_value": 160},
                {"feature_name": "BMI", "shap_value": -0.25, "raw_value": 21.8}
            ]
        },
        graph_evidence=case2_graph,
        safety_context={
            "contradiction_flag_raised": True,
            "is_capped_by_contradiction": True,
            "fused_confidence": 0.50
        },
        expected_facts={
            "predicted_label": "Presence",
            "probability_pct": 62.0,
            "shap_features": ["Glucose", "BMI"],
            "positive_shap_features": ["Glucose"],
            "negative_shap_features": ["BMI"],
            "retrieved_entities": ["Polyuria", "Polydipsia", "INS", "Metformin", "Glipizide", "essential hypertension"],
            "contradiction_expected": True
        }
    )

    # Case 3: Low-risk Kidney Disease
    case3_graph = KnowledgeGraphEvidence(
        model_id="kidney_disease",
        queried_disease_name="kidney_disease",
        mapped_graph_node="chronic kidney disease",
        phenotypes=[],
        genes_biomarkers=[
            GeneBiomarkerEvidence(gene_symbol="ACE", relation_type="disease_protein"),
            GeneBiomarkerEvidence(gene_symbol="AGTR1", relation_type="disease_protein")
        ],
        drugs=[
            DrugEvidence(drug_name="Lisinopril", indication_type="indication")
        ],
        comorbidities=[],
        total_triples_found=18
    )

    case3 = LLMEvalCase(
        case_id="case_3_kidney_disease_low_risk",
        disease="kidney_disease",
        description="Low-risk chronic kidney disease prediction with negative SHAP attributions.",
        model_id="kidney_disease",
        prediction={"predicted_label": "Absence", "probability": 0.12},
        shap_explanation={
            "top_features": [
                {"feature_name": "hemo", "shap_value": -0.38, "raw_value": 15.2},
                {"feature_name": "sc", "shap_value": -0.22, "raw_value": 0.9}
            ]
        },
        graph_evidence=case3_graph,
        safety_context={
            "contradiction_flag_raised": False,
            "is_capped_by_contradiction": False,
            "fused_confidence": 0.88
        },
        expected_facts={
            "predicted_label": "Absence",
            "probability_pct": 12.0,
            "shap_features": ["hemo", "sc"],
            "positive_shap_features": [],
            "negative_shap_features": ["hemo", "sc"],
            "retrieved_entities": ["ACE", "AGTR1", "Lisinopril"],
            "contradiction_expected": False
        }
    )

    # Case 4: Hypertension with Degraded (Empty) SHAP Attributions
    case4_graph = KnowledgeGraphEvidence(
        model_id="hypertension",
        queried_disease_name="hypertension",
        mapped_graph_node="hypertensive disease",
        phenotypes=[
            PhenotypeEvidence(phenotype_name="High Blood Pressure", relation_type="disease_phenotype")
        ],
        genes_biomarkers=[
            GeneBiomarkerEvidence(gene_symbol="NOS3", relation_type="disease_protein")
        ],
        drugs=[
            DrugEvidence(drug_name="Amlodipine", indication_type="indication")
        ],
        comorbidities=[],
        total_triples_found=15
    )

    case4 = LLMEvalCase(
        case_id="case_4_hypertension_degraded_shap",
        disease="hypertension",
        description="Hypertension prediction with missing/degraded SHAP explanation.",
        model_id="hypertension",
        prediction={"predicted_label": "Presence", "probability": 0.78},
        shap_explanation={"top_features": []},
        graph_evidence=case4_graph,
        safety_context={
            "contradiction_flag_raised": False,
            "is_capped_by_contradiction": False,
            "fused_confidence": 0.65
        },
        expected_facts={
            "predicted_label": "Presence",
            "probability_pct": 78.0,
            "shap_features": [],
            "positive_shap_features": [],
            "negative_shap_features": [],
            "retrieved_entities": ["High Blood Pressure", "NOS3", "Amlodipine"],
            "contradiction_expected": False
        }
    )

    return [case1, case2, case3, case4]
