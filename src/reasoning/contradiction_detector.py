"""
Contradiction & Evidence Categorization Engine for Module 5.
Categorizes retrieved PrimeKG graph evidence triples and SHAP feature attributions
into 3 distinct categories: Supporting, Conflicting, and Neutral/Contextual.
Strictly relies on retrieved relationship types and feature impact directions.
"""

from typing import Dict, Any, Optional, List
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reasoning.schemas import EvidenceCategoryItem, ContradictionAnalysis


class ContradictionDetector:
    """
    Evaluates evidence consistency across ML prediction, SHAP attributions, and PrimeKG triples.
    """

    SUPPORTING_PHENOTYPE_RELATIONS = {
        "disease_phenotype_positive", "associated_with", "has_symptom", "phenotype_disease"
    }
    CONFLICTING_PHENOTYPE_RELATIONS = {
        "disease_phenotype_negative", "negative_phenotype"
    }

    SUPPORTING_DRUG_RELATIONS = {"indication"}
    CONFLICTING_DRUG_RELATIONS = {"contraindication", "contraindicated_in", "contraindicated"}

    @staticmethod
    def _normalized_relation(value: str) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _unique_records(records: List[Any], fields: List[str]) -> List[Any]:
        unique = []
        seen = set()
        for record in records:
            key = tuple(str(getattr(record, field, "")).strip().lower() for field in fields)
            if key not in seen:
                seen.add(key)
                unique.append(record)
        return unique

    def get_graph_evidence_counts(self, graph_evidence: KnowledgeGraphEvidence) -> Dict[str, int]:
        """Return unique PrimeKG-only counts using the same relation semantics as analysis."""
        phenotypes = self._unique_records(graph_evidence.phenotypes, ["phenotype_name", "relation_type"])
        genes = self._unique_records(graph_evidence.genes_biomarkers, ["gene_symbol", "relation_type"])
        drugs = self._unique_records(graph_evidence.drugs, ["drug_name", "indication_type"])
        exposures = self._unique_records(graph_evidence.exposures, ["exposure_name", "relation_type"])
        comorbidities = self._unique_records(graph_evidence.comorbidities, ["disease_name", "relation_type"])

        supporting = sum(
            1 for item in phenotypes
            if self._normalized_relation(item.relation_type) in self.SUPPORTING_PHENOTYPE_RELATIONS
        )
        conflicting = sum(
            1 for item in phenotypes
            if self._normalized_relation(item.relation_type) in self.CONFLICTING_PHENOTYPE_RELATIONS
        )
        supporting += sum(
            1 for item in drugs
            if self._normalized_relation(item.indication_type) in self.SUPPORTING_DRUG_RELATIONS
        )
        conflicting += sum(
            1 for item in drugs
            if self._normalized_relation(item.indication_type) in self.CONFLICTING_DRUG_RELATIONS
        )
        supporting += len(genes)
        total = len(phenotypes) + len(genes) + len(drugs) + len(exposures) + len(comorbidities)
        neutral = total - supporting - conflicting

        return {
            "total": total,
            "supporting": supporting,
            "conflicting": conflicting,
            "neutral": neutral
        }

    def analyze_evidence(
        self,
        prediction: Dict[str, Any],
        graph_evidence: KnowledgeGraphEvidence,
        shap_explanation: Optional[Dict[str, Any]] = None
    ) -> ContradictionAnalysis:
        """
        Categorizes evidence into supporting, conflicting, and neutral items based on retrieved relation types.
        """
        prob = prediction.get("probability", prediction.get("positive_probability", 0.5))
        is_high_risk = prob >= 0.5

        supporting_items: List[EvidenceCategoryItem] = []
        conflicting_items: List[EvidenceCategoryItem] = []
        neutral_items: List[EvidenceCategoryItem] = []

        # 1. Phenotypes
        for p in self._unique_records(graph_evidence.phenotypes, ["phenotype_name", "relation_type"]):
            rel = self._normalized_relation(p.relation_type)
            name = p.phenotype_name
            if rel in self.CONFLICTING_PHENOTYPE_RELATIONS:
                conflicting_items.append(EvidenceCategoryItem(
                    category="phenotype",
                    entity_name=name,
                    relation_or_impact=p.relation_type,
                    detail=f"Phenotype '{name}' has negative/conflicting association [{p.relation_type}]",
                    is_conflicting=True
                ))
            elif rel in self.SUPPORTING_PHENOTYPE_RELATIONS:
                supporting_items.append(EvidenceCategoryItem(
                    category="phenotype",
                    entity_name=name,
                    relation_or_impact=p.relation_type,
                    detail=f"Phenotype '{name}' supports disease clinical presentation [{p.relation_type}]",
                    is_supporting=True
                ))
            else:
                neutral_items.append(EvidenceCategoryItem(
                    category="phenotype",
                    entity_name=name,
                    relation_or_impact=p.relation_type,
                    detail=f"Phenotype '{name}' has contextual association [{p.relation_type}]",
                    is_neutral=True
                ))

        # 2. Drugs
        for d in self._unique_records(graph_evidence.drugs, ["drug_name", "indication_type"]):
            rel = self._normalized_relation(d.indication_type)
            name = d.drug_name
            if rel in self.CONFLICTING_DRUG_RELATIONS:
                conflicting_items.append(EvidenceCategoryItem(
                    category="drug",
                    entity_name=name,
                    relation_or_impact=d.indication_type,
                    detail=f"Medication '{name}' is contraindicated for target disease [{d.indication_type}]",
                    is_conflicting=True
                ))
            elif rel in self.SUPPORTING_DRUG_RELATIONS:
                supporting_items.append(EvidenceCategoryItem(
                    category="drug",
                    entity_name=name,
                    relation_or_impact=d.indication_type,
                    detail=f"Medication '{name}' is indicated for target disease [{d.indication_type}]",
                    is_supporting=True
                ))
            else:
                neutral_items.append(EvidenceCategoryItem(
                    category="drug",
                    entity_name=name,
                    relation_or_impact=d.indication_type,
                    detail=f"Medication '{name}' has off-label or contextual relationship [{d.indication_type}]",
                    is_neutral=True
                ))

        # 3. Genes / Biomarkers
        for g in self._unique_records(graph_evidence.genes_biomarkers, ["gene_symbol", "relation_type"]):
            name = g.gene_symbol
            supporting_items.append(EvidenceCategoryItem(
                category="gene_biomarker",
                entity_name=name,
                relation_or_impact=g.relation_type,
                detail=f"Gene/Biomarker '{name}' associated with disease [{g.relation_type}]",
                is_supporting=True
            ))

        # 4. Exposures (Contextual / Neutral)
        for e in self._unique_records(graph_evidence.exposures, ["exposure_name", "relation_type"]):
            name = e.exposure_name
            neutral_items.append(EvidenceCategoryItem(
                category="exposure",
                entity_name=name,
                relation_or_impact=e.relation_type,
                detail=f"Environmental exposure '{name}' recorded as contextual risk factor [{e.relation_type}]",
                is_neutral=True
            ))

        # 5. Comorbidities (Contextual / Neutral)
        for c in self._unique_records(graph_evidence.comorbidities, ["disease_name", "relation_type"]):
            name = c.disease_name
            neutral_items.append(EvidenceCategoryItem(
                category="comorbidity",
                entity_name=name,
                relation_or_impact=c.relation_type,
                detail=f"Associated comorbidity '{name}' noted as clinical co-occurrence [{c.relation_type}]",
                is_neutral=True
            ))

        # 6. SHAP Feature Attributions
        if shap_explanation:
            top_features = shap_explanation.get("top_attributions", shap_explanation.get("top_features", []))
            for f in top_features:
                feat_name = f.get("feature_name", f.get("feature", "unknown"))
                impact = f.get("impact_direction", "")
                shap_val = f.get("shap_value", 0.0)

                if not impact:
                    if shap_val > 0.01:
                        impact = "increases_risk"
                    elif shap_val < -0.01:
                        impact = "decreases_risk"
                    else:
                        impact = "neutral"

                if is_high_risk:
                    if impact == "increases_risk":
                        supporting_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' increases risk (SHAP: {shap_val:+.4f}) aligning with HIGH_RISK prediction",
                            is_supporting=True
                        ))
                    elif impact == "decreases_risk":
                        conflicting_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' decreases risk (SHAP: {shap_val:+.4f}) conflicting with HIGH_RISK prediction",
                            is_conflicting=True
                        ))
                    else:
                        neutral_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' has neutral impact (SHAP: {shap_val:+.4f})",
                            is_neutral=True
                        ))
                else:
                    if impact == "decreases_risk":
                        supporting_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' decreases risk (SHAP: {shap_val:+.4f}) aligning with LOW_RISK prediction",
                            is_supporting=True
                        ))
                    elif impact == "increases_risk":
                        conflicting_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' increases risk (SHAP: {shap_val:+.4f}) conflicting with LOW_RISK prediction",
                            is_conflicting=True
                        ))
                    else:
                        neutral_items.append(EvidenceCategoryItem(
                            category="shap_attribution",
                            entity_name=feat_name,
                            relation_or_impact=impact,
                            detail=f"Feature '{feat_name}' has neutral impact (SHAP: {shap_val:+.4f})",
                            is_neutral=True
                        ))

        has_conflicts = len(conflicting_items) > 0

        if has_conflicts:
            summary = (
                f"Contradictions detected: {len(conflicting_items)} conflicting evidence item(s) found "
                f"alongside {len(supporting_items)} supporting item(s) and {len(neutral_items)} neutral item(s)."
            )
        elif len(supporting_items) == 0 and len(conflicting_items) == 0:
            summary = (
                "Insufficient evidence: No explicit supporting or conflicting evidence items found "
                f"({len(neutral_items)} neutral/contextual items)."
            )
        else:
            summary = (
                f"Consistent evidence: {len(supporting_items)} supporting evidence item(s) found "
                f"with 0 conflicting items ({len(neutral_items)} neutral/contextual items)."
            )

        return ContradictionAnalysis(
            supporting_evidence=supporting_items,
            conflicting_evidence=conflicting_items,
            neutral_evidence=neutral_items,
            supporting_count=len(supporting_items),
            conflicting_count=len(conflicting_items),
            neutral_count=len(neutral_items),
            has_contradictions=has_conflicts,
            contradiction_summary=summary
        )
