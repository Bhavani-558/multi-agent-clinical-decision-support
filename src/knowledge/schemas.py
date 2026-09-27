"""
Pydantic Schemas for Knowledge & Evidence Layer.
Defines structured representations of Neo4j graph triples and clinical evidence reports.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphTriple(BaseModel):
    """Represents a single clinical graph relationship triple."""
    source_node: str = Field(..., description="Source entity name")
    source_type: str = Field(..., description="Source entity type (e.g. disease)")
    relationship_type: str = Field(..., description="PrimeKG interaction type (r.type)")
    target_node: str = Field(..., description="Target entity name")
    target_type: str = Field(..., description="Target entity type (e.g. effect/phenotype, drug, gene/protein)")


class PhenotypeEvidence(BaseModel):
    """Clinical phenotype / symptom associated with a disease."""
    phenotype_name: str
    relation_type: str  # e.g. disease_phenotype_positive, disease_phenotype_negative


class GeneBiomarkerEvidence(BaseModel):
    """Gene or protein associated with a disease."""
    gene_symbol: str
    relation_type: str  # e.g. disease_protein


class DrugEvidence(BaseModel):
    """Therapeutic drug associated with a disease."""
    drug_name: str
    indication_type: str  # e.g. indication, contraindication, off-label use


class ExposureEvidence(BaseModel):
    """Environmental or lifestyle exposure associated with a disease."""
    exposure_name: str
    relation_type: str  # e.g. exposure_disease


class ComorbidityEvidence(BaseModel):
    """Associated comorbidity disease."""
    disease_name: str
    relation_type: str  # e.g. disease_disease


class KnowledgeGraphEvidence(BaseModel):
    """Aggregated clinical evidence retrieved from PrimeKG for a disease."""
    model_id: str
    queried_disease_name: str
    mapped_graph_node: str
    phenotypes: List[PhenotypeEvidence] = Field(default_factory=list)
    genes_biomarkers: List[GeneBiomarkerEvidence] = Field(default_factory=list)
    drugs: List[DrugEvidence] = Field(default_factory=list)
    exposures: List[ExposureEvidence] = Field(default_factory=list)
    comorbidities: List[ComorbidityEvidence] = Field(default_factory=list)
    total_triples_found: int = 0


class EvidenceAgentResponse(BaseModel):
    """Combined response payload from Evidence Agent."""
    model_id: str
    prediction: Dict[str, Any]
    shap_explanation: Optional[Dict[str, Any]] = None
    graph_evidence: KnowledgeGraphEvidence
    evidence_summary: str
    llm_explanation: Optional[str] = None
