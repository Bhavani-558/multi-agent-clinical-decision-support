"""
Evidence Agent for CDSS.
Integrates ML Model Predictions, SHAP Feature Importance, and Neo4j PrimeKG Evidence.
"""

import os
import json
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from groq import Groq

from src.knowledge.graph_service import Neo4jGraphService
from src.knowledge.schemas import KnowledgeGraphEvidence, EvidenceAgentResponse

load_dotenv()


class EvidenceAgent:
    """
    Evidence Agent responsible for bridging feature-level SHAP attributions with PrimeKG graph triples.
    """

    def __init__(self, graph_service: Optional[Neo4jGraphService] = None):
        self.graph_service = graph_service or Neo4jGraphService()

        self.groq_client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.groq_model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    def generate_evidence_summary(self, evidence: KnowledgeGraphEvidence, prediction: Dict[str, Any], shap_explanation: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a human-readable clinical evidence summary combining ML predictions, SHAP, and PrimeKG triples.
        """
        model_id = evidence.model_id
        mapped_node = evidence.mapped_graph_node
        prob = prediction.get("probability", prediction.get("positive_probability", 0.0))

        summary_lines = [
            f"Clinical Evidence Report for {model_id.upper()} (Mapped Node: '{mapped_node}')",
            f"Model Prediction Risk Score: {prob * 100:.1f}%",
            f"Total Graph Triples Found: {evidence.total_triples_found}"
        ]

        if shap_explanation and "top_features" in shap_explanation:
            top_features = shap_explanation["top_features"]
            summary_lines.append("\nTop Contributing Risk Features (SHAP):")
            for f in top_features[:3]:
                feat_name = f.get("feature_name", f.get("feature", "unknown"))
                impact = f.get("shap_value", 0.0)
                summary_lines.append(f"  - {feat_name}: SHAP value {impact:+.4f}")

        if evidence.phenotypes:
            summary_lines.append(f"\nAssociated Clinical Symptoms/Phenotypes ({len(evidence.phenotypes)}):")
            for p in evidence.phenotypes[:5]:
                summary_lines.append(f"  - {p.phenotype_name} [{p.relation_type}]")

        if evidence.drugs:
            summary_lines.append(f"\nAssociated Medications & Contraindications ({len(evidence.drugs)}):")
            for d in evidence.drugs[:5]:
                summary_lines.append(f"  - {d.drug_name} [{d.indication_type}]")

        if evidence.genes_biomarkers:
            summary_lines.append(f"\nTarget Genes / Biomarkers ({len(evidence.genes_biomarkers)}):")
            for g in evidence.genes_biomarkers[:5]:
                summary_lines.append(f"  - {g.gene_symbol} [{g.relation_type}]")

        if evidence.comorbidities:
            summary_lines.append(f"\nAssociated Comorbidities ({len(evidence.comorbidities)}):")
            for c in evidence.comorbidities[:5]:
                summary_lines.append(f"  - {c.disease_name} [{c.relation_type}]")

        return "\n".join(summary_lines)

    def generate_llm_explanation(
        self,
        model_id: str,
        prediction: Dict[str, Any],
        shap_explanation: Optional[Dict[str, Any]],
        evidence: KnowledgeGraphEvidence,
        evidence_summary: str
    ) -> str:
        """
        Calls Groq LLM API to generate a clinical decision-support explanation based strictly on supplied data.
        """
        try:
            if not os.getenv("GROQ_API_KEY"):
                return "LLM explanation unavailable."

            prob = prediction.get("probability", prediction.get("positive_probability", 0.0))
            label = prediction.get("predicted_label", prediction.get("predicted_class", "N/A"))
            shap_data = json.dumps(
            shap_explanation or {},
            indent=2,
            default=str
)
            prompt = (
                f"You are a clinical decision support explanation agent. Explain the following structured CDSS findings strictly using the supplied data.\n"
                f"CRITICAL RULES:\n"
                f"- Use ONLY the supplied data below.\n"
                f"- Never invent patient information, biomedical evidence, or citations.\n"
                f"- Never change the ML prediction or override safety caps.\n"
                f"- Never make a definitive diagnosis or prescribe treatment.\n"
                f"- Provide a cautious interpretation.\n\n"
                f"FINDINGS:\n"
                f"1. Disease Model Target: {model_id}\n"
                f"2. Model Prediction: {label} (Risk Probability: {prob * 100:.1f}%)\n"
                f"3. SHAP Explanation Data:\n{shap_data}\n\n"
                f"4. Clinical Evidence Summary:\n{evidence_summary}\n\n"
                f"Please produce a clear clinical decision-support explanation covering:\n"
                f"1. What the model predicted.\n"
                f"2. Which SHAP features most influenced the prediction and whether they increase or decrease risk.\n"
                f"3. What relevant biomedical evidence was retrieved from PrimeKG/Neo4j (supporting vs conflicting evidence/contradictions).\n"
                f"4. A cautious interpretation of the overall result for clinician review."
            )

            completion = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": "You are a clinical decision support assistant. Explain clinical findings concisely and cautiously based ONLY on provided data without making diagnosis or treatment recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )

            if completion.choices and completion.choices[0].message.content:
                return completion.choices[0].message.content.strip()
            return "LLM explanation unavailable."
        except Exception as e:
            print(f"[EvidenceAgent] Groq LLM API call error: {e}")
            return "LLM explanation unavailable."

    def evaluate_evidence(self, model_id: str, prediction: Dict[str, Any], shap_explanation: Optional[Dict[str, Any]] = None) -> EvidenceAgentResponse:
        """
        Evaluates clinical evidence for a prediction by querying Neo4j PrimeKG.
        """
        graph_evidence = self.graph_service.get_full_evidence_for_model(model_id)
        print("\n=== NEO4J EVIDENCE RETRIEVED ===")
        print(graph_evidence.model_dump())
        summary = self.generate_evidence_summary(graph_evidence, prediction, shap_explanation)

        llm_exp = self.generate_llm_explanation(
            model_id=model_id,
            prediction=prediction,
            shap_explanation=shap_explanation,
            evidence=graph_evidence,
            evidence_summary=summary
        )

        return EvidenceAgentResponse(
            model_id=model_id,
            prediction=prediction,
            shap_explanation=shap_explanation,
            graph_evidence=graph_evidence,
            evidence_summary=summary,
            llm_explanation=llm_exp
        )
