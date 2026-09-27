"""
Neo4j Knowledge Graph Service for CDSS.
Provides read-only query interfaces to retrieve PrimeKG evidence triples.
"""

import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from src.knowledge.disease_registry import get_graph_disease_candidates
from src.knowledge.schemas import (
    KnowledgeGraphEvidence,
    PhenotypeEvidence,
    GeneBiomarkerEvidence,
    DrugEvidence,
    ExposureEvidence,
    ComorbidityEvidence,
    GraphTriple
)

# Load environment variables
load_dotenv()


class Neo4jGraphService:
    """
    Read-only service wrapper for querying the PrimeKG Neo4j Graph Database.
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """Establishes driver connection if not already connected."""
        if not self._driver:
            if not self.password:
                raise ValueError("NEO4J_PASSWORD environment variable is not configured.")
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                liveness_check_timeout=0,
                max_connection_lifetime=180
            )
        return self._driver

    def close(self):
        """Closes driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a read-only Cypher query with parameter binding and single retry for transient connection drops."""
        try:
            driver = self.connect()
            with driver.session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except (ServiceUnavailable, SessionExpired):
            # Transient disconnect or defunct connection: recycle driver and retry once
            self.close()
            driver = self.connect()
            with driver.session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]

    def verify_connection(self) -> bool:
        """Verifies database connectivity."""
        try:
            res = self.run_query("RETURN 1 as ping")
            return len(res) > 0 and res[0].get("ping") == 1
        except Exception:
            return False

    def resolve_disease_node(self, model_id: str) -> Optional[str]:
        """
        Resolves a model_id to an existing PrimeKG disease node name.
        """
        candidates = get_graph_disease_candidates(model_id)
        for candidate in candidates:
            res = self.run_query(
                "MATCH (d:Entity {type: 'disease'}) WHERE toLower(d.name) = toLower($name) RETURN d.name as name LIMIT 1",
                {"name": candidate}
            )
            if res:
                return res[0]["name"]

        # Partial match fallback
        for candidate in candidates:
            res = self.run_query(
                "MATCH (d:Entity {type: 'disease'}) WHERE toLower(d.name) CONTAINS toLower($name) RETURN d.name as name ORDER BY size(d.name) ASC LIMIT 1",
                {"name": candidate}
            )
            if res:
                return res[0]["name"]

        return None

    def get_disease_phenotypes(self, disease_name: str, limit: int = 15) -> List[PhenotypeEvidence]:
        """Retrieves associated symptoms and clinical presentations."""
        cypher = """
        MATCH (d:Entity {type: 'disease'})-[r:RELATED_TO]-(p:Entity {type: 'effect/phenotype'})
        WHERE toLower(d.name) = toLower($disease_name)
        RETURN p.name as phenotype, properties(r).type as relation_type
        LIMIT $limit
        """
        records = self.run_query(cypher, {"disease_name": disease_name, "limit": limit})
        return [
            PhenotypeEvidence(
                phenotype_name=r["phenotype"],
                relation_type=r.get("relation_type", "disease_phenotype_positive")
            )
            for r in records
        ]

    def get_disease_genes(self, disease_name: str, limit: int = 15) -> List[GeneBiomarkerEvidence]:
        """Retrieves associated genes and biomarker proteins."""
        cypher = """
        MATCH (d:Entity {type: 'disease'})-[r:RELATED_TO]-(g:Entity {type: 'gene/protein'})
        WHERE toLower(d.name) = toLower($disease_name)
        RETURN g.name as gene, properties(r).type as relation_type
        LIMIT $limit
        """
        records = self.run_query(cypher, {"disease_name": disease_name, "limit": limit})
        return [
            GeneBiomarkerEvidence(
                gene_symbol=r["gene"],
                relation_type=r.get("relation_type", "disease_protein")
            )
            for r in records
        ]

    def get_disease_drugs(self, disease_name: str, limit: int = 15) -> List[DrugEvidence]:
        """Retrieves associated therapeutic drugs (indications, contraindications, off-label)."""
        cypher = """
        MATCH (d:Entity {type: 'disease'})-[r:RELATED_TO]-(dr:Entity {type: 'drug'})
        WHERE toLower(d.name) = toLower($disease_name)
        RETURN dr.name as drug, properties(r).type as relation_type
        LIMIT $limit
        """
        records = self.run_query(cypher, {"disease_name": disease_name, "limit": limit})
        return [
            DrugEvidence(
                drug_name=r["drug"],
                indication_type=r.get("relation_type", "indication")
            )
            for r in records
        ]

    def get_disease_exposures(self, disease_name: str, limit: int = 10) -> List[ExposureEvidence]:
        """Retrieves associated environmental and lifestyle exposures."""
        cypher = """
        MATCH (d:Entity {type: 'disease'})-[r:RELATED_TO]-(e:Entity {type: 'exposure'})
        WHERE toLower(d.name) = toLower($disease_name)
        RETURN e.name as exposure, properties(r).type as relation_type
        LIMIT $limit
        """
        records = self.run_query(cypher, {"disease_name": disease_name, "limit": limit})
        return [
            ExposureEvidence(
                exposure_name=r["exposure"],
                relation_type=r.get("relation_type", "exposure_disease")
            )
            for r in records
        ]

    def get_comorbidities(self, disease_name: str, limit: int = 10) -> List[ComorbidityEvidence]:
        """Retrieves associated comorbidity diseases."""
        cypher = """
        MATCH (d:Entity {type: 'disease'})-[r:RELATED_TO]-(c:Entity {type: 'disease'})
        WHERE toLower(d.name) = toLower($disease_name) AND toLower(c.name) <> toLower($disease_name)
        RETURN c.name as comorbidity, properties(r).type as relation_type
        LIMIT $limit
        """
        records = self.run_query(cypher, {"disease_name": disease_name, "limit": limit})
        return [
            ComorbidityEvidence(
                disease_name=r["comorbidity"],
                relation_type=r.get("relation_type", "disease_disease")
            )
            for r in records
        ]

    def get_full_evidence_for_model(self, model_id: str, limit_per_category: int = 10) -> KnowledgeGraphEvidence:
        """
        Retrieves complete structured PrimeKG evidence for a CDSS model identifier.
        """
        mapped_name = self.resolve_disease_node(model_id) or model_id
        
        phenotypes = self.get_disease_phenotypes(mapped_name, limit=limit_per_category)
        genes = self.get_disease_genes(mapped_name, limit=limit_per_category)
        drugs = self.get_disease_drugs(mapped_name, limit=limit_per_category)
        exposures = self.get_disease_exposures(mapped_name, limit=limit_per_category)
        comorbidities = self.get_comorbidities(mapped_name, limit=limit_per_category)

        total_triples = len(phenotypes) + len(genes) + len(drugs) + len(exposures) + len(comorbidities)

        return KnowledgeGraphEvidence(
            model_id=model_id,
            queried_disease_name=model_id,
            mapped_graph_node=mapped_name,
            phenotypes=phenotypes,
            genes_biomarkers=genes,
            drugs=drugs,
            exposures=exposures,
            comorbidities=comorbidities,
            total_triples_found=total_triples
        )
