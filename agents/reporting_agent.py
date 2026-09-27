"""
Reporting Agent Module for CDSS.
Provides ReportingAgent class wrapping ClinicalReportGenerator for generating structured,
human-readable clinical decision-support reports.
"""

from typing import Dict, Any, Optional
from src.fusion.schemas import ClinicalDecisionOutput
from src.reasoning.schemas import ReasoningOutput
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reporting.schemas import ClinicalDecisionReport
from src.reporting.report_generator import ClinicalReportGenerator


class ReportingAgent:
    """
    Reporting Agent responsible for consuming Module 6 ClinicalDecisionOutput payloads
    and generating structured, multi-format clinical decision-support reports.
    """

    def __init__(self, generator: Optional[ClinicalReportGenerator] = None):
        self.generator = generator or ClinicalReportGenerator()

    def generate_report(
        self,
        decision_output: ClinicalDecisionOutput,
        reasoning_output: Optional[ReasoningOutput] = None,
        graph_evidence: Optional[KnowledgeGraphEvidence] = None,
        patient_metadata: Optional[Dict[str, Any]] = None,
        llm_explanation: Optional[str] = None
    ) -> ClinicalDecisionReport:
        """Generates structured ClinicalDecisionReport from ClinicalDecisionOutput."""
        return self.generator.generate_report(
            decision_output=decision_output,
            reasoning_output=reasoning_output,
            graph_evidence=graph_evidence,
            patient_metadata=patient_metadata,
            llm_explanation=llm_explanation
        )


__all__ = ["ReportingAgent", "ClinicalReportGenerator"]
