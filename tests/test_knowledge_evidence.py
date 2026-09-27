"""
Unit Tests for Module 4 — Knowledge & Evidence Layer.
Verifies Neo4j connectivity, disease node resolution, Cypher query execution,
and Evidence Agent integration across all 10 CDSS disease models.
"""

import pytest
from src.knowledge.disease_registry import get_graph_disease_candidates, get_canonical_disease_name
from src.knowledge.graph_service import Neo4jGraphService
from src.knowledge.schemas import KnowledgeGraphEvidence, EvidenceAgentResponse
from src.evidence.evidence_agent import EvidenceAgent

# List of all 10 CDSS disease model IDs
ALL_MODEL_IDS = [
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
def graph_service():
    """Provides a shared Neo4jGraphService instance for testing."""
    service = Neo4jGraphService()
    yield service
    service.close()


def test_neo4j_connectivity(graph_service):
    """Test 1: Verify read-only connection to live Neo4j database."""
    connected = graph_service.verify_connection()
    assert connected is True, "Failed to connect to Neo4j graph database using .env credentials"


def test_disease_registry_mappings():
    """Test 2: Verify candidate mappings exist for all 10 disease models."""
    for model_id in ALL_MODEL_IDS:
        candidates = get_graph_disease_candidates(model_id)
        assert isinstance(candidates, list)
        assert len(candidates) > 0
        canonical = get_canonical_disease_name(model_id)
        assert isinstance(canonical, str)
        assert len(canonical) > 0


@pytest.mark.parametrize("model_id", ALL_MODEL_IDS)
def test_disease_node_resolution(graph_service, model_id):
    """Test 3: Verify all 10 disease models resolve to a PrimeKG disease node."""
    resolved_name = graph_service.resolve_disease_node(model_id)
    assert resolved_name is not None, f"Model '{model_id}' failed to resolve to a Neo4j PrimeKG disease node"
    assert isinstance(resolved_name, str)


def test_get_disease_phenotypes(graph_service):
    """Test 4: Verify phenotype retrieval Cypher query."""
    phenotypes = graph_service.get_disease_phenotypes("anemia (disease)", limit=5)
    assert isinstance(phenotypes, list)
    assert len(phenotypes) > 0
    for p in phenotypes:
        assert hasattr(p, "phenotype_name")
        assert hasattr(p, "relation_type")


def test_get_disease_genes(graph_service):
    """Test 5: Verify gene/protein biomarker retrieval Cypher query."""
    genes = graph_service.get_disease_genes("breast cancer", limit=5)
    assert isinstance(genes, list)
    assert len(genes) > 0
    for g in genes:
        assert hasattr(g, "gene_symbol")
        assert hasattr(g, "relation_type")


def test_get_disease_drugs(graph_service):
    """Test 6: Verify drug indication/contraindication retrieval Cypher query."""
    drugs = graph_service.get_disease_drugs("chronic kidney disease", limit=5)
    assert isinstance(drugs, list)
    assert len(drugs) > 0
    for d in drugs:
        assert hasattr(d, "drug_name")
        assert hasattr(d, "indication_type")


def test_get_full_evidence_for_model(graph_service):
    """Test 7: Verify complete graph evidence retrieval for a model."""
    evidence = graph_service.get_full_evidence_for_model("heart_disease", limit_per_category=5)
    assert isinstance(evidence, KnowledgeGraphEvidence)
    assert evidence.model_id == "heart_disease"
    assert evidence.mapped_graph_node == "heart disease"
    assert evidence.total_triples_found > 0


def test_evidence_agent_evaluation(graph_service):
    """Test 8: Verify EvidenceAgent evaluates predictions and generates summaries."""
    agent = EvidenceAgent(graph_service=graph_service)

    mock_prediction = {
        "model_id": "heart_disease",
        "predicted_class": 1,
        "probability": 0.87
    }

    mock_shap = {
        "top_features": [
            {"feature_name": "cp", "shap_value": 0.35},
            {"feature_name": "thalach", "shap_value": 0.22}
        ]
    }

    response = agent.evaluate_evidence(
        model_id="heart_disease",
        prediction=mock_prediction,
        shap_explanation=mock_shap
    )

    assert isinstance(response, EvidenceAgentResponse)
    assert response.model_id == "heart_disease"
    assert "Clinical Evidence Report" in response.evidence_summary
    assert "87.0%" in response.evidence_summary
    assert response.graph_evidence.total_triples_found > 0
