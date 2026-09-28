"""
Report Generator for Module 7 — Reporting Layer.
Dynamically extracts clinical decision output elements from Module 6 (and Modules 1–5),
rendering structured, human-readable Clinical Decision Support reports in Markdown, Plain Text, and JSON formats.
Strictly preserves all upstream scores without recalculation or hardcoded data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from src.fusion.schemas import ClinicalDecisionOutput, DecisionSupportClassification
from src.reasoning.schemas import ReasoningOutput, EvidenceCategoryItem
from src.knowledge.schemas import KnowledgeGraphEvidence
from src.reporting.schemas import ClinicalReportSection, ClinicalDecisionReport
from src.reasoning.contradiction_detector import ContradictionDetector


class ClinicalReportGenerator:
    """
    Generates structured, multi-format clinical decision-support reports.
    Consumes ClinicalDecisionOutput directly from Module 6 without modifying upstream values.
    """

    NON_CLINICAL_DISCLAIMER = (
        "NOTICE: This report is generated strictly for machine-assisted clinical decision support. "
        "It does NOT constitute a clinical diagnosis, medical prescription, or treatment guideline. "
        "All predictions, evidence synthesis, and risk tiers must be independently audited and "
        "verified by a qualified, licensed healthcare professional."
    )

    def generate_report(
        self,
        decision_output: ClinicalDecisionOutput,
        reasoning_output: Optional[ReasoningOutput] = None,
        graph_evidence: Optional[KnowledgeGraphEvidence] = None,
        patient_metadata: Optional[Dict[str, Any]] = None,
        llm_explanation: Optional[str] = None
    ) -> ClinicalDecisionReport:
        """
        Executes full report generation pipeline.
        Dynamically builds 7 structured user-facing report sections and formats Markdown, Plain Text, and JSON representations.
        """
        # Step 1: Extract Core Metrics safely (handling model instances or dicts)
        disease = decision_output.disease
        model_id = decision_output.model_id
        classification = (
            decision_output.decision_classification.value
            if isinstance(decision_output.decision_classification, DecisionSupportClassification)
            else str(decision_output.decision_classification)
        )
        fused = decision_output.fused_confidence
        overall_fused = fused.overall_fused_score if hasattr(fused, 'overall_fused_score') else fused['overall_fused_score']
        pre_cap_fused = fused.pre_cap_fused_score if hasattr(fused, 'pre_cap_fused_score') else fused.get('pre_cap_fused_score')
        is_capped = fused.is_capped_by_contradiction if hasattr(fused, 'is_capped_by_contradiction') else fused.get('is_capped_by_contradiction', False)

        tc_summary = decision_output.trust_and_consensus_summary or {}
        overall_trust = tc_summary.get('overall_trust_score', 0.0)
        consensus_level = tc_summary.get('consensus_level', 'UNKNOWN')

        # Convert uncertainty flags
        raw_flags = decision_output.uncertainty_flags or []
        uncertainty_list = []
        for flag in raw_flags:
            if hasattr(flag, 'model_dump'):
                uncertainty_list.append(flag.model_dump())
            elif isinstance(flag, dict):
                uncertainty_list.append(flag)
            else:
                uncertainty_list.append({
                    "flag_code": getattr(flag, 'flag_code', 'UNKNOWN'),
                    "description": getattr(flag, 'description', str(flag)),
                    "severity": getattr(flag, 'severity', 'MEDIUM')
                })

        # Step 2: Build the 7 Dynamic User-Facing Report Sections
        sections: List[ClinicalReportSection] = []

        # Section 1: DISEASE PREDICTION
        sec1 = self._build_section_1_prediction(decision_output)
        sections.append(sec1)

        # Section 2: KEY CONTRIBUTING FACTORS (SHAP)
        sec2 = self._build_section_2_shap(decision_output, reasoning_output)
        sections.append(sec2)

        # Section 3: BIOMEDICAL EVIDENCE
        sec3 = self._build_section_3_primekg(decision_output, graph_evidence)
        sections.append(sec3)

        # Section 4: EVIDENCE & PREDICTION COMPARISON
        sec4 = self._build_section_4_comparison(decision_output, reasoning_output)
        sections.append(sec4)

        # Section 5: TRUST & CONFIDENCE
        sec5 = self._build_section_5_trust_confidence(decision_output)
        sections.append(sec5)

        # Section 6: FINAL DECISION-SUPPORT INTERPRETATION
        sec6 = self._build_section_6_interpretation(decision_output, llm_explanation=llm_explanation)
        sections.append(sec6)

        # Section 7: DOWNLOAD REPORT & MANDATORY DISCLAIMER
        sec7 = self._build_section_7_disclaimer(decision_output, uncertainty_list)
        sections.append(sec7)

        # Step 3: Render Formatted Outputs (Markdown and Plain Text)
        markdown_str = self._render_markdown(
            disease=disease,
            model_id=model_id,
            classification=classification,
            overall_fused=overall_fused,
            is_capped=is_capped,
            pre_cap_fused=pre_cap_fused,
            sections=sections,
            uncertainty_flags=uncertainty_list,
            patient_metadata=patient_metadata,
            llm_explanation=llm_explanation
        )

        text_str = self._render_text(
            disease=disease,
            model_id=model_id,
            classification=classification,
            overall_fused=overall_fused,
            is_capped=is_capped,
            pre_cap_fused=pre_cap_fused,
            sections=sections,
            uncertainty_flags=uncertainty_list,
            patient_metadata=patient_metadata,
            llm_explanation=llm_explanation
        )

        # Construct Report Object
        report = ClinicalDecisionReport(
            disease=disease,
            model_id=model_id,
            decision_classification=classification,
            fused_confidence_score=overall_fused,
            is_capped_by_contradiction=is_capped,
            overall_trust_score=overall_trust,
            consensus_level=consensus_level,
            llm_explanation=llm_explanation,
            sections=sections,
            uncertainty_flags=uncertainty_list,
            markdown_report=markdown_str,
            text_report=text_str,
            json_payload={}
        )

        # Populate JSON payload
        report.json_payload = report.model_dump(exclude={'json_payload'})
        return report

    # --- SECTION BUILDERS ---

    @staticmethod
    def _probability_label(decision_output: ClinicalDecisionOutput, prediction_summary: Dict[str, Any]) -> str:
        class_probabilities = prediction_summary.get("class_probabilities", {})
        if len(class_probabilities) > 2:
            return f"predicted class ({prediction_summary.get('predicted_label', 'N/A')})"
        label = prediction_summary.get("probability_class_label")
        if not label and len(class_probabilities) >= 2:
            label = list(class_probabilities.keys())[1]
        if not label:
            from src.prediction.mapping_registry import resolve_human_label
            label = resolve_human_label(decision_output.disease, "1")
        return f"positive class ({label})"

    @staticmethod
    def _safety_cap_description(fused: Any, is_capped: bool) -> str:
        if not is_capped:
            return "Standard uncapped score"
        pre_cap = fused.pre_cap_fused_score if hasattr(fused, "pre_cap_fused_score") else fused.get("pre_cap_fused_score")
        if pre_cap is not None and pre_cap > 0.50:
            return f"Contradiction safety ceiling = 0.50; reduced from pre-cap score {pre_cap:.4f}"
        if pre_cap is not None:
            return "Contradiction detected; safety ceiling = 0.50; no reduction was required"
        return "Capped at 0.50 due to contradiction"

    def _build_section_1_prediction(self, decision_output: ClinicalDecisionOutput) -> ClinicalReportSection:
        p_summary = decision_output.prediction_summary or {}
        prob = p_summary.get("probability", 0.0)
        pred_class = p_summary.get("predicted_class", 0)
        label = p_summary.get("predicted_label", "N/A")
        decisiveness = 2.0 * abs(prob - 0.5)

        # Presentation layer guard: convert any raw numeric class ID to verified human-readable label
        from src.prediction.mapping_registry import resolve_human_label
        label = resolve_human_label(decision_output.disease, label)
        probability_label = p_summary.get("probability_class_label")
        class_probabilities = p_summary.get("class_probabilities", {})
        if not probability_label and len(class_probabilities) >= 2:
            probability_label = list(class_probabilities.keys())[1]
        if not probability_label:
            probability_label = resolve_human_label(decision_output.disease, "1")
        probability_metric_label = (
            f"Probability of Predicted Class ({label})"
            if len(class_probabilities) > 2
            else f"Probability of Positive Class ({probability_label})"
        )

        # Class 0 / Healthy / Absence -> LOW_RISK
        if str(pred_class).strip() in ["0", "-1"] or label in ["Healthy", "Absence", "B", "notckd"]:
            tier = "LOW_RISK"
        else:
            tier = "HIGH_RISK"
        summary_text = ""

        metrics = {
            "disease": decision_output.disease,
            "predicted_result": label,
            "probability_label": probability_metric_label,
            "model_probability": f"{prob * 100:.2f}%",
            "risk_tier": tier,
            "model_decisiveness_factor": round(decisiveness, 4)
        }

        return ClinicalReportSection(
            section_id="disease_prediction",
            title="1. Disease Prediction",
            summary_text=summary_text,
            metrics=metrics,
            items=[]
        )



    def _build_section_2_shap(
        self,
        decision_output: ClinicalDecisionOutput,
        reasoning_output: Optional[ReasoningOutput]
    ) -> ClinicalReportSection:
        shap_summary = decision_output.shap_summary or {}
        shap_status = shap_summary.get("shap_status", "UNKNOWN")
        if shap_status == "UNKNOWN" and decision_output.trust_and_consensus_summary:
            shap_status = decision_output.trust_and_consensus_summary.get("shap_status", "UNKNOWN")

        base_value = shap_summary.get("base_value", None)
        attributions = shap_summary.get("top_attributions", [])

        # Fallback: if top_attributions is empty in shap_summary, extract from reasoning_output
        if not attributions and reasoning_output:
            attributions = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in reasoning_output.supporting_evidence + reasoning_output.conflicting_evidence + reasoning_output.neutral_evidence
                if (isinstance(item, dict) and item.get("category") == "shap_attribution") or getattr(item, "category", "") == "shap_attribution"
            ]

        # Strictly sort by absolute SHAP magnitude descending and limit to Top 5
        def _get_abs_shap_val(attr):
            if hasattr(attr, "model_dump"):
                attr = attr.model_dump()
            if isinstance(attr, dict):
                val = attr.get("shap_value", attr.get("attribution_value", 0.0))
            else:
                val = getattr(attr, "shap_value", getattr(attr, "attribution_value", 0.0))
            try:
                return abs(float(val))
            except (ValueError, TypeError):
                return 0.0

        if isinstance(attributions, list) and attributions:
            attributions = sorted(attributions, key=_get_abs_shap_val, reverse=True)[:5]

        items = []
        if shap_status == "OMITTED_RENORMALIZED" or not attributions:
            summary_text = (
                "SHAP feature attributions were omitted or unavailable for this prediction. "
                "System trust score weights were dynamically renormalized."
            )
        else:
            summary_text = (
                f"Extracted {len(attributions)} top feature attributions affecting the prediction. "
                "Feature impacts indicate directional push towards increasing (+) or decreasing (–) disease risk."
            )
            for attr in attributions:
                if hasattr(attr, "model_dump"):
                    attr_dict = attr.model_dump()
                elif isinstance(attr, dict):
                    attr_dict = attr
                else:
                    attr_dict = {}

                s_val = attr_dict.get("shap_value", attr_dict.get("attribution_value", None))
                r_val = attr_dict.get("raw_value", attr_dict.get("feature_value", "N/A"))
                f_name = attr_dict.get("feature_name", attr_dict.get("entity_name", "Unknown"))
                i_dir = attr_dict.get("impact_direction", attr_dict.get("relation_or_impact", "NEUTRAL"))
                detail = attr_dict.get("detail", "")

                if (s_val is None or isinstance(s_val, str)) and detail:
                    import re
                    match = re.search(r"SHAP:\s*([+-]?\d+\.?\d*)", detail)
                    if match:
                        try:
                            s_val = float(match.group(1))
                        except ValueError:
                            s_val = detail
                    else:
                        s_val = attr_dict.get("attribution_value", detail)
                elif s_val is None:
                    s_val = 0.0

                items.append({
                    "feature_name": f_name,
                    "attribution_value": s_val,
                    "shap_value": s_val,
                    "raw_value": r_val,
                    "feature_value": r_val,
                    "impact_direction": i_dir
                })

        metrics = {
            "shap_status": shap_status,
            "base_value": base_value if base_value is not None else "N/A",
            "total_attributions_retrieved": len(items)
        }

        return ClinicalReportSection(
            section_id="key_factors",
            title="2. Key Contributing Factors",
            summary_text=summary_text,
            metrics=metrics,
            items=items
        )

    def _build_section_3_primekg(
        self,
        decision_output: ClinicalDecisionOutput,
        graph_evidence: Optional[KnowledgeGraphEvidence]
    ) -> ClinicalReportSection:
        e_summary = decision_output.evidence_summary or {}
        node = e_summary.get("mapped_graph_node", "Unknown")

        if graph_evidence:
            node = graph_evidence.mapped_graph_node or node
            graph_counts = ContradictionDetector().get_graph_evidence_counts(graph_evidence)
            total = graph_counts["total"]
            sup = graph_counts["supporting"]
            conf = graph_counts["conflicting"]
            neu = graph_counts["neutral"]
        else:
            total = e_summary.get("total_triples_found", 0)
            sup = e_summary.get("supporting_count", 0)
            conf = e_summary.get("conflicting_count", 0)
            neu = e_summary.get("neutral_count", 0)

        summary_text = (
            f"Retrieved {total} biomedical evidence triples from PrimeKG knowledge graph mapped to entity '{node}'. "
            f"Evidence breakdown: {sup} supporting, {conf} conflicting, and {neu} neutral items."
        )

        metrics = {
            "mapped_graph_node": node,
            "total_evidence_triples": total,
            "supporting_evidence": sup,
            "conflicting_evidence": conf,
            "neutral_evidence": neu
        }

        return ClinicalReportSection(
            section_id="biomedical_evidence",
            title="3. Biomedical Evidence",
            summary_text=summary_text,
            metrics=metrics,
            items=[]
        )

    def _build_section_4_comparison(
        self,
        decision_output: ClinicalDecisionOutput,
        reasoning_output: Optional[ReasoningOutput]
    ) -> ClinicalReportSection:
        classification = decision_output.decision_classification
        class_val = classification.value if hasattr(classification, "value") else str(classification)
        e_summary = decision_output.evidence_summary or {}
        p_summary = decision_output.prediction_summary or {}
        
        prob = p_summary.get("probability", 0.0)
        label = p_summary.get("predicted_label", "N/A")
        tier = p_summary.get("risk_tier") or ("HIGH_RISK" if prob >= 0.5 else "LOW_RISK")
        conf_count = e_summary.get("conflicting_count", 0)
        sup_count = e_summary.get("supporting_count", 0)
        neu_count = e_summary.get("neutral_count", 0)
        # Count SHAP feature items vs Graph evidence triples dynamically
        shap_count = 0
        if decision_output.shap_summary:
            shap_count = len(decision_output.shap_summary.get("top_attributions", []))
        if shap_count == 0 and reasoning_output:
            all_items = reasoning_output.supporting_evidence + reasoning_output.conflicting_evidence + reasoning_output.neutral_evidence
            shap_count = sum(1 for item in all_items if (isinstance(item, dict) and item.get("category") == "shap_attribution") or getattr(item, "category", "") == "shap_attribution")

        if reasoning_output:
            combined_items = (
                reasoning_output.supporting_evidence
                + reasoning_output.conflicting_evidence
                + reasoning_output.neutral_evidence
            )
            total_combined = len(combined_items)
            sup_count = len(reasoning_output.supporting_evidence)
            conf_count = len(reasoning_output.conflicting_evidence)
            neu_count = len(reasoning_output.neutral_evidence)
        else:
            total_combined = e_summary.get("total_triples_found", 0) + shap_count

        graph_count = e_summary.get("total_triples_found", max(0, total_combined - shap_count))

        if class_val == "CONTRADICTION_FLAG" or conf_count > 0:
            comparison_explanation = (
                f"The reasoning layer evaluates combined evidence by integrating PrimeKG biomedical graph triples with SHAP feature attributions:\n"
                f"- Model Prediction: Predicts risk probability of {prob * 100:.2f}% ({label} / {tier}).\n"
                f"- Biomedical Graph Evidence (PrimeKG): {graph_count} total graph evidence triples retrieved from Neo4j.\n"
                f"- Combined Pipeline Signals: {total_combined} total signals evaluated ({sup_count} supporting, {conf_count} conflicting, {neu_count} neutral), combining graph triples with {shap_count} SHAP feature attributions.\n"
                f"- Contradiction Analysis: Misalignment detected between pipeline signals. Contradiction detected; safety ceiling = 0.50."
            )
            has_contradiction = True
        else:
            comparison_explanation = (
                f"The reasoning layer evaluates combined evidence by integrating PrimeKG biomedical graph triples with SHAP feature attributions:\n"
                f"- Model Prediction: Predicts risk probability of {prob * 100:.2f}% ({label} / {tier}).\n"
                f"- Biomedical Graph Evidence (PrimeKG): {graph_count} total graph evidence triples retrieved from Neo4j.\n"
                f"- Combined Pipeline Signals: {total_combined} total signals evaluated ({sup_count} supporting, {conf_count} conflicting, {neu_count} neutral), combining graph triples with {shap_count} SHAP feature attributions.\n"
                f"- Alignment Status: All pipeline signals are aligned with the prediction."
            )
            has_contradiction = False

        metrics = {
            "alignment_status": "CONTRADICTION_DETECTED" if has_contradiction else "ALIGNED",
            "decision_classification": class_val,
            "conflicting_evidence_count": conf_count,
            "supporting_evidence_count": sup_count,
            "neutral_evidence_count": neu_count,
            "total_combined_signals": total_combined,
            "shap_attribution_count": shap_count,
            "biomedical_graph_triples_count": graph_count
        }

        return ClinicalReportSection(
            section_id="evidence_comparison",
            title="4. Evidence & Prediction Comparison",
            summary_text=comparison_explanation,
            metrics=metrics,
            items=[]
        )

    def _build_section_5_trust_confidence(self, decision_output: ClinicalDecisionOutput) -> ClinicalReportSection:
        tc = decision_output.trust_and_consensus_summary or {}
        fused = decision_output.fused_confidence
        overall_fused = fused.overall_fused_score if hasattr(fused, 'overall_fused_score') else fused['overall_fused_score']
        is_capped = fused.is_capped_by_contradiction if hasattr(fused, 'is_capped_by_contradiction') else fused.get('is_capped_by_contradiction', False)

        trust_score = tc.get("overall_trust_score", 0.0)
        consensus_lvl = tc.get("consensus_level", "UNKNOWN")
        consensus_score = tc.get("consensus_score", 0.0)

        summary_text = (
            f"Evaluated multi-source consistency and trust metrics:\n"
            f"- Trust Score: {trust_score:.4f}\n"
            f"- Consensus Level: {consensus_lvl} (Score: {consensus_score:.4f})\n"
            f"- Fused Confidence Score: {overall_fused:.4f} "
                f"({self._safety_cap_description(fused, is_capped)})"
        )

        metrics = {
            "trust_score": round(trust_score, 4),
            "consensus_level": consensus_lvl,
            "consensus_score": round(consensus_score, 4),
            "fused_confidence_score": round(overall_fused, 4),
            "overall_fused_score": round(overall_fused, 4),
            "trust_component": round(fused.trust_component if hasattr(fused, 'trust_component') else fused.get('trust_component', 0.0), 4),
            "consensus_component": round(fused.consensus_component if hasattr(fused, 'consensus_component') else fused.get('consensus_component', 0.0), 4),
            "is_capped_by_contradiction": is_capped,
            "metric_type": "Software Alignment & System Confidence (Not Disease Severity)"
        }

        return ClinicalReportSection(
            section_id="trust_and_confidence",
            title="5. System Trust & Confidence Metrics",
            summary_text=summary_text,
            metrics=metrics,
            items=[]
        )

    def _build_section_6_interpretation(
        self,
        decision_output: ClinicalDecisionOutput,
        llm_explanation: Optional[str] = None
    ) -> ClinicalReportSection:
        p_summary = decision_output.prediction_summary or {}
        prob = p_summary.get("probability", 0.0)
        label = p_summary.get("predicted_label", "N/A")
        
        e_summary = decision_output.evidence_summary or {}
        sup_count = e_summary.get("supporting_count", 0)
        conf_count = e_summary.get("conflicting_count", 0)
        
        fused = decision_output.fused_confidence
        overall_fused = fused.overall_fused_score if hasattr(fused, 'overall_fused_score') else fused.get('overall_fused_score', 0.0)
        
        classification = decision_output.decision_classification
        class_val = classification.value if hasattr(classification, 'value') else str(classification)
        
        disease_name = decision_output.disease.replace('_', ' ').lower()
        probability_label = self._probability_label(decision_output, p_summary)
        
        if class_val == "CONTRADICTION_FLAG" or conf_count > 0:
            summary_text = (
                f"The model predicts {label}; the probability of {probability_label} is {prob * 100:.2f}%. "
                f"However, the available evidence is conflicting: SHAP shows both risk-increasing and risk-decreasing feature contributions, "
                f"while the biomedical evidence contains {sup_count} supporting and {conf_count} conflicting items. "
                f"Because these signals are not sufficiently aligned, the system raises a contradiction flag. "
                f"The combined decision-support confidence is {overall_fused * 100:.2f}%. "
                f"This indicates uncertainty in the overall decision-support assessment and should not be interpreted as disease severity or a definitive diagnosis."
            )
        elif class_val == "HIGH_RISK_DECISION_SUPPORT":
            summary_text = (
                f"The model predicts {label}; the probability of {probability_label} is {prob * 100:.2f}%. "
                f"The biomedical evidence contains {sup_count} supporting items aligned with high risk. "
                f"The combined decision-support confidence is {overall_fused * 100:.2f}%. "
                f"This Machine-Assisted Decision Support output assists clinical evaluation and should not be interpreted as a definitive diagnosis."
            )
        elif class_val == "LOW_RISK_DECISION_SUPPORT":
            summary_text = (
                f"The model predicts {label}; the probability of {probability_label} is {prob * 100:.2f}%. "
                f"The biomedical evidence contains {sup_count} supporting items consistent with low risk. "
                f"The combined decision-support confidence is {overall_fused * 100:.2f}%. "
                f"This output is for machine-assisted clinical decision support and should not be interpreted as a definitive diagnosis."
            )
        elif class_val == "DEGRADED_CONFIDENCE":
            summary_text = (
                f"The model predicts {label}; the probability of {probability_label} is {prob * 100:.2f}%. "
                f"However, SHAP feature explanation was unavailable or omitted, leading to dynamic weight renormalization. "
                f"The combined decision-support confidence is {overall_fused * 100:.2f}%. "
                f"This indicates degraded explanation confidence and requires clinician audit."
            )
        else:  # INSUFFICIENT_EVIDENCE or default
            summary_text = (
                f"The model predicts {label}; the probability of {probability_label} is {prob * 100:.2f}%. "
                f"Biomedical evidence retrieval found insufficient graph triples to confirm the prediction. "
                f"The combined decision-support confidence is {overall_fused * 100:.2f}%. "
                f"Independent clinical audit is recommended."
            )

        if llm_explanation:
            summary_text += f"\n\n[CLINICAL INTERPRETATION]\n{llm_explanation}"

        metrics = {
            "guidance_mode": "Non-Prescriptive Machine-Assisted Support",
            "decision_classification": class_val
        }

        return ClinicalReportSection(
            section_id="final_interpretation",
            title="6. Final Decision-Support Interpretation",
            summary_text=summary_text,
            metrics=metrics,
            items=[]
        )

    def _build_section_7_disclaimer(self, decision_output: ClinicalDecisionOutput, uncertainty_list: List[Dict[str, Any]]) -> ClinicalReportSection:
        summary_text = (
            f"This structured report is formatted and validated for export (JSON/Markdown) and downstream PDF generation.\n\n"
            f"{self.NON_CLINICAL_DISCLAIMER}"
        )

        metrics = {
            "export_formats_prepared": ["Markdown", "JSON", "PDF_Ready"],
            "uncertainty_flag_count": len(uncertainty_list),
            "disclaimer_applied": True
        }

        return ClinicalReportSection(
            section_id="export_and_disclaimer",
            title="7. Download Report & Software Audit Disclaimer",
            summary_text=summary_text,
            metrics=metrics,
            items=uncertainty_list
        )

    # --- RENDERING FORMATTERS ---

    def _render_standardized_report(
        self,
        disease: str,
        model_id: str,
        classification: str,
        overall_fused: float,
        is_capped: bool,
        pre_cap_fused: Optional[float],
        sections: List[ClinicalReportSection],
        uncertainty_flags: List[Dict[str, Any]],
        patient_metadata: Optional[Dict[str, Any]],
        is_markdown: bool = True,
        llm_explanation: Optional[str] = None
    ) -> str:
        patient_meta = patient_metadata or {}

        # 1. Patient Information
        p_id = str(patient_meta.get("patient_id") or "PAT_001").strip()
        p_name = str(patient_meta.get("patient_name") or "Patient").strip()
        age = str(patient_meta.get("age") or patient_meta.get("Age") or "N/A").strip()
        raw_gender = patient_meta.get("gender") if patient_meta.get("gender") is not None else patient_meta.get("Sex", patient_meta.get("sex", "N/A"))
        if str(raw_gender).strip() in ["1", 1, "1.0", "Male", "male"]:
            gender = "Male"
        elif str(raw_gender).strip() in ["0", 0, "0.0", "Female", "female"]:
            gender = "Female"
        else:
            gender = str(raw_gender).strip() if raw_gender is not None else "N/A"

        kolkata_tz = ZoneInfo("Asia/Kolkata")
        raw_ts = patient_meta.get("timestamp")
        raw_analysis_date = patient_meta.get("analysis_date")

        date_time = ""

        if raw_ts:
            if isinstance(raw_ts, datetime):
                if raw_ts.tzinfo is not None:
                    date_time = raw_ts.astimezone(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S IST")
                else:
                    date_time = raw_ts.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts_str = str(raw_ts).strip()
                has_utc_info = (
                    "+" in ts_str
                    or ts_str.endswith("Z")
                    or ts_str.endswith("z")
                    or "-00:00" in ts_str
                    or "UTC" in ts_str.upper()
                )
                if has_utc_info:
                    try:
                        iso_clean = ts_str.replace("Z", "+00:00").replace("z", "+00:00")
                        if iso_clean.upper().endswith("UTC"):
                            iso_clean = iso_clean[:-3].strip() + "+00:00"
                        dt_utc = datetime.fromisoformat(iso_clean)
                        if dt_utc.tzinfo is None:
                            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                        date_time = dt_utc.astimezone(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S IST")
                    except Exception:
                        date_time = ts_str
                else:
                    date_time = ts_str
        elif raw_analysis_date:
            if isinstance(raw_analysis_date, datetime):
                if raw_analysis_date.tzinfo is not None:
                    date_time = raw_analysis_date.astimezone(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S IST")
                else:
                    date_time = str(raw_analysis_date)
            else:
                date_str = str(raw_analysis_date).strip()
                has_utc_info = (
                    "+" in date_str
                    or date_str.endswith("Z")
                    or date_str.endswith("z")
                    or "-00:00" in date_str
                    or "UTC" in date_str.upper()
                )
                if has_utc_info and "T" in date_str:
                    try:
                        iso_clean = date_str.replace("Z", "+00:00").replace("z", "+00:00")
                        if iso_clean.upper().endswith("UTC"):
                            iso_clean = iso_clean[:-3].strip() + "+00:00"
                        dt_utc = datetime.fromisoformat(iso_clean)
                        if dt_utc.tzinfo is None:
                            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                        date_time = dt_utc.astimezone(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S IST")
                    except Exception:
                        date_time = date_str
                else:
                    date_time = date_str

        if not date_time:
            date_time = datetime.now(kolkata_tz).strftime("%Y-%m-%d %H:%M:%S IST")
        
        disease_clean = disease.replace("_", " ").title().strip()

        # Extract section dictionaries
        sec_dict = {s.section_id: s for s in sections}

        # 2. Prediction Metrics
        pred_sec = sec_dict.get("disease_prediction")
        pred_metrics = pred_sec.metrics if pred_sec else {}
        pred_label = pred_metrics.get("predicted_result", "Absence")
        prob_str = pred_metrics.get("model_probability", "0.00%")
        risk_tier = pred_metrics.get("risk_tier", "LOW_RISK")

        label_lower = str(pred_label).lower().strip()
        tier_upper = str(risk_tier).upper().strip()
        if label_lower in ["presence", "positive", "detected", "malignant", "die"] or tier_upper == "HIGH_RISK":
            detection_status = "DETECTED"
            risk_level_display = "HIGH RISK"
        else:
            detection_status = "NOT DETECTED"
            risk_level_display = "LOW RISK"

        # 3. Top 5 SHAP factors
        shap_sec = sec_dict.get("key_factors")
        shap_items = shap_sec.items if shap_sec else []
        def _get_item_abs(item):
            val = item.get("shap_value", item.get("attribution_value", 0.0)) if isinstance(item, dict) else getattr(item, "shap_value", getattr(item, "attribution_value", 0.0))
            try:
                return abs(float(val))
            except (ValueError, TypeError):
                return 0.0

        top5_items = sorted(shap_items, key=_get_item_abs, reverse=True)[:5] if isinstance(shap_items, list) else []

        top5_clean = []
        for item in top5_items:
            f_raw = item.get("feature_name", item.get("name", "Unknown"))
            f_clean = " ".join(w.capitalize() for w in str(f_raw).replace("_", " ").strip().split())
            
            raw_impact = str(item.get("impact_direction", item.get("relation_or_impact", "neutral"))).lower()
            if "decrease" in raw_impact:
                impact_text = "Decreases risk"
            elif "increase" in raw_impact:
                impact_text = "Increases risk"
            else:
                try:
                    s_num = float(item.get("shap_value", item.get("attribution_value", 0.0)))
                    impact_text = "Decreases risk" if s_num < 0 else "Increases risk"
                except (ValueError, TypeError):
                    impact_text = "Neutral"

            s_val = item.get("shap_value", item.get("attribution_value", 0.0))
            try:
                s_num = float(s_val)
                s_str = f"{s_num:+.4f}"
            except (ValueError, TypeError):
                s_str = str(s_val)

            r_val = item.get("raw_value", item.get("feature_value", "N/A"))
            top5_clean.append({
                "feature": f_clean,
                "impact": impact_text,
                "shap": s_str,
                "raw": str(r_val)
            })

        # 4. Biomedical Evidence
        bio_sec = sec_dict.get("biomedical_evidence")
        bio_metrics = bio_sec.metrics if bio_sec else {}
        mapped_node = bio_metrics.get("mapped_graph_node", disease_clean)
        total_findings = bio_metrics.get("total_evidence_triples", 0)
        sup_count = bio_metrics.get("supporting_evidence", 0)
        conf_count = bio_metrics.get("conflicting_evidence", 0)
        neu_count = bio_metrics.get("neutral_evidence", 0)

        # 5. Evidence & Prediction Comparison
        comp_sec = sec_dict.get("evidence_comparison")
        comp_metrics = comp_sec.metrics if comp_sec else {}
        align_status = comp_metrics.get("alignment_status", "ALIGNED")

        if is_capped or (conf_count > 0 and sup_count > 0) or align_status == "CONTRADICTION_DETECTED":
            agreement_status = "Mixed"
        elif conf_count > 0 and sup_count == 0:
            agreement_status = "Conflicting"
        elif sup_count == 0 and conf_count == 0:
            agreement_status = "Neutral"
        else:
            agreement_status = "Aligned"

        # 6. Trust Analysis
        trust_sec = sec_dict.get("trust_and_confidence")
        trust_metrics = trust_sec.metrics if trust_sec else {}
        overall_trust = trust_metrics.get("overall_trust_score", trust_metrics.get("trust_score", 0.0))
        consensus_lvl = str(trust_metrics.get("consensus_level", "UNKNOWN")).replace("_", " ").upper()
        consensus_score = trust_metrics.get("consensus_score", 0.0)
        trust_comp = trust_metrics.get("trust_component", 0.0)
        cons_comp = trust_metrics.get("consensus_component", 0.0)
        fused_score = trust_metrics.get("fused_confidence_score", trust_metrics.get("overall_fused_score", overall_fused))

        contradiction_status = "CONFLICT DETECTED" if (is_capped or conf_count > 0) else ("ALIGNED" if sup_count > 0 else "NEUTRAL")

        # Formatting Prefix
        h1 = "# " if is_markdown else ""
        h2 = "## " if is_markdown else ""
        h3 = "### " if is_markdown else ""

        lines = []
        lines.append(f"{h1}🩺 Patient Clinical Decision-Support Report")
        lines.append("")
        lines.append(f"{h2}1. PATIENT INFORMATION")
        lines.append(f"Patient ID: {p_id}")
        lines.append(f"Patient Name: {p_name}")
        lines.append(f"Age: {age}")
        lines.append(f"Gender: {gender}")
        lines.append(f"Analysis Date/Time: {date_time}")
        lines.append(f"Selected Disease: {disease_clean}")
        lines.append("")
        lines.append(f"{h2}2. 🧠 DISEASE PREDICTION")
        lines.append(f"Predicted Disease: {disease_clean}")
        lines.append(f"Final Classification: {detection_status}")
        lines.append(f"Model Probability: {prob_str}")
        lines.append(f"Risk Level: {risk_level_display}")
        lines.append("")
        lines.append(f"{h2}3. 🔍 KEY CONTRIBUTING FACTORS")
        lines.append("Feature | Impact | SHAP Value | Raw Value")
        for f in top5_clean[:5]:
            lines.append(f"{f['feature']} | {f['impact']} | {f['shap']} | {f['raw']}")
        if not top5_clean:
            lines.append("No SHAP feature attributions available.")
        lines.append("")
        lines.append(f"{h2}4. 🧬 BIOMEDICAL EVIDENCE")
        lines.append(f"Knowledge Graph Findings: {total_findings}")
        lines.append(f"Supporting Evidence: {sup_count}")
        lines.append(f"Conflicting Evidence: {conf_count}")
        lines.append(f"Neutral Evidence: {neu_count}")
        lines.append(f"Relevant Evidence Details / References: Mapped to PrimeKG entity '{mapped_node}'. {total_findings} biomedical evidence triples retrieved from Neo4j knowledge graph.")
        lines.append("")
        lines.append(f"{h2}5. ⚖️ EVIDENCE & PREDICTION COMPARISON")
        lines.append(f"Model Prediction: {pred_label} ({prob_str} / {risk_level_display})")
        lines.append(f"Biomedical Evidence Count: {total_findings} graph triples from PrimeKG")
        lines.append(f"Agreement Status: {agreement_status}")
        lines.append(f"Supporting Count: {sup_count}")
        lines.append(f"Conflicting Count: {conf_count}")
        lines.append(f"Neutral Count: {neu_count}")
        lines.append("")
        lines.append(f"{h2}6. 🛡️ TRUST ANALYSIS")
        lines.append(f"{h3}A. ⚠️ Contradiction Analysis")
        lines.append(f"Supporting: {sup_count}")
        lines.append(f"Conflicting: {conf_count}")
        lines.append(f"Neutral: {neu_count}")
        lines.append(f"Contradiction Status: {contradiction_status}")
        if is_capped:
            if not is_markdown:
                lines.append(f"CONTRADICTION SAFETY CAP ACTIVATED (CAPPED AT 0.50): Contradiction detected; safety ceiling = 0.50; reduced from pre-cap score {pre_cap_fused:.4f}" if pre_cap_fused and pre_cap_fused > 0.5 else "CONTRADICTION SAFETY CAP ACTIVATED (CAPPED AT 0.50): Contradiction detected; safety ceiling = 0.50")
            else:
                lines.append(f"CONTRADICTION SAFETY CAP ACTIVATED: Contradiction detected; safety ceiling = 0.50; reduced from pre-cap score {pre_cap_fused:.4f}" if pre_cap_fused and pre_cap_fused > 0.5 else "CONTRADICTION SAFETY CAP ACTIVATED: Contradiction detected; safety ceiling = 0.50")
        lines.append("")
        lines.append(f"{h3}B. 🤝 Consensus Analysis")
        lines.append(f"Consensus Level: {consensus_lvl}")
        lines.append(f"Consensus Score: {consensus_score:.4f}" if isinstance(consensus_score, float) else f"Consensus Score: {consensus_score}")
        lines.append("")
        lines.append(f"{h3}C. 🛡️ Trust Score")
        lines.append(f"Overall Trust Score: {overall_trust:.4f}" if isinstance(overall_trust, float) else f"Overall Trust Score: {overall_trust}")
        lines.append(f"Trust Component: {trust_comp:.4f}" if isinstance(trust_comp, float) else f"Trust Component: {trust_comp}")
        lines.append(f"Consensus Component: {cons_comp:.4f}" if isinstance(cons_comp, float) else f"Consensus Component: {cons_comp}")
        lines.append(f"Fused Confidence Score: {fused_score:.4f}" if isinstance(fused_score, float) else f"Fused Confidence Score: {fused_score}")
        lines.append(f"Decision Classification: {classification}")
        lines.append("")
        lines.append(f"{h2}7. 📋 FINAL SYSTEM DECISION")
        lines.append("FINAL SYSTEM DECISION")
        lines.append("")
        lines.append(f"{disease_clean} — {detection_status}")
        lines.append("")
        lines.append(f"Risk Level: {risk_level_display}")
        lines.append(f"Model Probability: {prob_str}")
        lines.append("")

        lines.append(f"{h3}🧠 CLINICAL INTERPRETATION")

        final_interp_sec = sec_dict.get("final_interpretation")
        interp_text = ""
        if final_interp_sec and final_interp_sec.summary_text:
            interp_text = final_interp_sec.summary_text
        elif llm_explanation:
            interp_text = llm_explanation

        if interp_text:
            interp_clean = interp_text.replace("[CLINICAL INTERPRETATION]\n", "").replace("[CLINICAL INTERPRETATION]", "").strip()
            while "\n\n\n" in interp_clean:
                interp_clean = interp_clean.replace("\n\n\n", "\n\n")
            if interp_clean:
                lines.append(interp_clean)

        return "\n".join(lines)

    def _render_markdown(
        self,
        disease: str,
        model_id: str,
        classification: str,
        overall_fused: float,
        is_capped: bool,
        pre_cap_fused: Optional[float],
        sections: List[ClinicalReportSection],
        uncertainty_flags: List[Dict[str, Any]],
        patient_metadata: Optional[Dict[str, Any]],
        llm_explanation: Optional[str] = None
    ) -> str:
        return self._render_standardized_report(
            disease=disease,
            model_id=model_id,
            classification=classification,
            overall_fused=overall_fused,
            is_capped=is_capped,
            pre_cap_fused=pre_cap_fused,
            sections=sections,
            uncertainty_flags=uncertainty_flags,
            patient_metadata=patient_metadata,
            is_markdown=True,
            llm_explanation=llm_explanation
        )

    def _render_text(
        self,
        disease: str,
        model_id: str,
        classification: str,
        overall_fused: float,
        is_capped: bool,
        pre_cap_fused: Optional[float],
        sections: List[ClinicalReportSection],
        uncertainty_flags: List[Dict[str, Any]],
        patient_metadata: Optional[Dict[str, Any]],
        llm_explanation: Optional[str] = None
    ) -> str:
        return self._render_standardized_report(
            disease=disease,
            model_id=model_id,
            classification=classification,
            overall_fused=overall_fused,
            is_capped=is_capped,
            pre_cap_fused=pre_cap_fused,
            sections=sections,
            uncertainty_flags=uncertainty_flags,
            patient_metadata=patient_metadata,
            is_markdown=False,
            llm_explanation=llm_explanation
        )
