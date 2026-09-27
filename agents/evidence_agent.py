"""
Evidence Agent Module for CDSS.
Re-exports EvidenceAgent from src.evidence.evidence_agent.
"""

from src.evidence.evidence_agent import EvidenceAgent
from src.knowledge.graph_service import Neo4jGraphService

__all__ = ["EvidenceAgent", "Neo4jGraphService"]
