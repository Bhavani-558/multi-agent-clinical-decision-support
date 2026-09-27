"""
Dynamic Clinical Interpretation Generator for Module 7 — Reporting Layer.
Generates concise, physician-facing clinical interpretations synthesized strictly from
actual model outputs: prediction, SHAP attributions, PrimeKG biomedical evidence,
trust analysis, consensus level, decision fusion, and counterfactual simulation.
"""

from typing import Dict, Any, List, Optional


def generate_dynamic_clinical_interpretation(
    disease_name: str,
    is_detected: bool,
    probability_formatted: str,
    risk_tier: str,
    shap_features: Optional[List[Dict[str, Any]]] = None,
    mapped_node: Optional[str] = None,
    total_triples: int = 0,
    supporting_evidence: int = 0,
    conflicting_evidence: int = 0,
    neutral_evidence: int = 0,
    consensus_level: str = "MODERATE_CONSENSUS",
    trust_score: Optional[float] = None,
    fused_confidence: Optional[float] = None,
    has_conflicting_signals: bool = False,
    counterfactual_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates a 2-4 paragraph dynamic, grounded, physician-facing clinical interpretation.

    Answers:
      A. What did the system predict?
      B. What are the main factors influencing the prediction?
      C. What biomedical evidence supports the prediction?
      D. Is there conflicting evidence?
      E. What does the trust/consensus analysis indicate?
      F. What is the overall interpretation for the physician?
    """
    disease_phrase = str(disease_name or "the target condition").lower().strip()
    features = shap_features or []

    # -------------------------------------------------------------
    # 1. System Prediction & Main Influencing Factors (Questions A & B)
    # -------------------------------------------------------------
    pred_lead = (
        f"The assessment indicates an elevated predicted likelihood of {disease_phrase} based on "
        f"the evaluated clinical parameters, with an estimated model probability of {probability_formatted} ({risk_tier or 'High Risk'})."
        if is_detected
        else (
            f"The assessment indicates a low predicted likelihood of {disease_phrase} based on "
            f"the evaluated clinical parameters, with an estimated model probability of {probability_formatted} ({risk_tier or 'Low Risk'})."
        )
    )

    inc_list = [
        f.get("feature", f.get("feature_name", "Feature"))
        for f in features
        if "increase" in str(f.get("impact", f.get("impact_direction", ""))).lower()
    ]
    dec_list = [
        f.get("feature", f.get("feature_name", "Feature"))
        for f in features
        if "decrease" in str(f.get("impact", f.get("impact_direction", ""))).lower()
    ]
    all_names = [f.get("feature", f.get("feature_name", "Feature")) for f in features]

    if inc_list and dec_list:
        factor_lead = (
            f"The primary clinical factors influencing this prediction include {', '.join(all_names)}, "
            f"with {', '.join(inc_list)} contributing toward higher risk and {', '.join(dec_list)} contributing toward lower risk."
        )
    elif inc_list:
        factor_lead = f"The primary clinical factors influencing this prediction include {', '.join(inc_list)}, all contributing toward higher risk."
    elif dec_list:
        factor_lead = f"The primary clinical factors contributing to this prediction include {', '.join(dec_list)}, all contributing toward lower risk."
    else:
        factor_lead = "Feature attribution analysis evaluated input parameters without individual dominant directional drivers."

    paragraph1 = f"{pred_lead} {factor_lead}"

    # -------------------------------------------------------------
    # 2. Biomedical Evidence & Consistency/Contradiction Analysis (Questions C & D)
    # -------------------------------------------------------------
    node_str = mapped_node or disease_name
    is_insufficient = (
        (total_triples == 0)
        or ("INSUFFICIENT" in consensus_level.upper())
        or (supporting_evidence == 0 and conflicting_evidence == 0)
    )
    is_strongly_supporting = supporting_evidence > 0 and conflicting_evidence == 0 and not has_conflicting_signals
    is_mixed = supporting_evidence > 0 and conflicting_evidence > 0

    if has_conflicting_signals or is_mixed:
        paragraph2 = (
            f"Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '{node_str}' identified "
            f"{total_triples} evidence relationships, comprising {supporting_evidence} supporting, "
            f"{conflicting_evidence} conflicting, and {neutral_evidence} neutral items. The presence of both supporting "
            f"and conflicting signals indicates that the available biomedical evidence is not fully consistent with the "
            f"model prediction. Because divergent evidence items were identified across the knowledge graph, the system "
            f"incorporates this disagreement directly into the evidence-aware evaluation to inform clinical review."
        )
    elif is_insufficient:
        paragraph2 = (
            f"Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '{node_str}' indicates that "
            f"available biomedical evidence is limited ({total_triples} evidence items retrieved). The system explicitly "
            f"notes that current biomedical literature in the knowledge graph provides insufficient data to independently "
            f"confirm or refute the prediction, underscoring the need for careful clinical assessment."
        )
    elif is_strongly_supporting:
        paragraph2 = (
            f"Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '{node_str}' identified "
            f"{total_triples} evidence relationships ({supporting_evidence} supporting, 0 conflicting, and "
            f"{neutral_evidence} neutral items). The available biomedical evidence aligns with the model prediction, "
            f"reinforcing the pathophysiological consistency of the evaluated clinical parameters."
        )
    else:
        paragraph2 = (
            f"Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '{node_str}' identified "
            f"{total_triples} evidence relationships ({supporting_evidence} supporting, {conflicting_evidence} conflicting, "
            f"and {neutral_evidence} neutral items), providing contextual literature grounding for the clinical evaluation."
        )

    # -------------------------------------------------------------
    # 3. Trust/Consensus Analysis, Decision Fusion & Overall Interpretation (Questions E & F)
    # -------------------------------------------------------------
    consensus_display = (consensus_level or "MODERATE_CONSENSUS").replace("_", " ")
    trust_score_formatted = f"{trust_score:.4f}" if trust_score is not None else "N/A"
    fused_conf_formatted = f"{fused_confidence:.4f}" if fused_confidence is not None else "N/A"

    cf_text = ""
    if counterfactual_data and counterfactual_data.get("modified_features"):
        mod_features = counterfactual_data["modified_features"]
        mod_names = [m.get("label", m.get("feature", "feature")) for m in mod_features]
        orig_p = counterfactual_data.get("original", {}).get("probability_formatted", "")
        sim_p = counterfactual_data.get("counterfactual", {}).get("probability_formatted", "")
        if orig_p and sim_p:
            cf_text = (
                f" In counterfactual simulation, adjusting {', '.join(mod_names)} altered the estimated "
                f"probability from {orig_p} to {sim_p}, demonstrating sensitivity to actionable clinical target adjustments."
            )

    paragraph3 = (
        f"Multi-source consensus evaluation established a {consensus_display} classification with an overall "
        f"system trust score of {trust_score_formatted} and a fused confidence score of {fused_conf_formatted}.{cf_text} "
        f"Overall, the system considers the available evidence and model output together to provide an "
        f"evidence-aware decision-support interpretation. This result is intended strictly to assist the physician and "
        f"should be interpreted alongside comprehensive clinical judgment."
    )

    paragraphs = [paragraph1, paragraph2, paragraph3]
    return {
        "paragraph1": paragraph1,
        "paragraph2": paragraph2,
        "paragraph3": paragraph3,
        "paragraphs": paragraphs,
        "full_text": "\n\n".join(paragraphs),
    }
