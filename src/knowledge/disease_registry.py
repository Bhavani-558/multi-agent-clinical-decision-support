"""
Disease Registry for CDSS Knowledge Layer.
Provides canonical disease mapping from ML model identifiers to PrimeKG Neo4j disease node names.
"""

from typing import Dict, List, Optional

# Verified mappings between ML model identifiers and PrimeKG disease node names (n.name)
DISEASE_GRAPH_MAPPINGS: Dict[str, List[str]] = {
    "anemia": [
        "anemia (disease)",
        "aplastic anemia",
        "hemolytic anemia",
        "anemia"
    ],
    "B_cancer": [
        "breast cancer",
        "sporadic breast cancer"
    ],
    "Chronic_liver": [
        "liver disease",
        "fatty liver disease"
    ],
    "diabetes": [
        "prediabetes syndrome",
        "gestational diabetes",
        "monogenic diabetes",
        "diabetes insipidus"
    ],
    "heart_disease": [
        "heart disease",
        "hypertensive heart disease",
        "congenital heart disease"
    ],
    "Hepatitis": [
        "hepatitis",
        "viral hepatitis",
        "alcoholic hepatitis"
    ],
    "Kidney": [
        "chronic kidney disease",
        "kidney disease"
    ],
    "lung_cancer": [
        "lung cancer",
        "lung cancer susceptibility"
    ],
    "Parkinsons": [
        "Parkinson disease",
        "parkinsonian disorder"
    ],
    "Stroke": [
        "stroke disorder",
        "large artery stroke"
    ]
}


def get_graph_disease_candidates(model_id: str) -> List[str]:
    """
    Returns candidate PrimeKG disease node names for a given model ID.
    
    Args:
        model_id: ML model identifier (e.g. 'heart_disease', 'diabetes')
        
    Returns:
        List of candidate node names ordered by resolution priority.
    """
    return DISEASE_GRAPH_MAPPINGS.get(model_id, [model_id.lower().replace("_", " ")])


def get_canonical_disease_name(model_id: str) -> str:
    """
    Returns the primary canonical disease node name for a given model ID.
    
    Args:
        model_id: ML model identifier
        
    Returns:
        Primary disease name string.
    """
    candidates = get_graph_disease_candidates(model_id)
    return candidates[0] if candidates else model_id
