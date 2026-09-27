"""
Dynamic Disease Schema & Demo Patient Data Service for Module 8 UI.
Queries ModelLoader and mapping_registry to build clean schema definitions and sample patient payloads.
"""

from typing import Dict, Any, List
from src.prediction.model_loader import ModelLoader
from src.prediction.mapping_registry import CATEGORICAL_MAPPINGS

# Human-readable titles & descriptions for 10 diseases
DISEASE_METADATA: Dict[str, Dict[str, str]] = {
    "anemia": {
        "title": "Anemia Classification",
        "description": "Multiclass evaluation of hematological parameters for anemia type diagnosis.",
        "icon": "🩸",
        "category": "Hematology"
    },
    "B_cancer": {
        "title": "Breast Cancer Risk",
        "description": "Assessment of fine needle aspirate nuclear features for malignancy detection.",
        "icon": "🎗️",
        "category": "Oncology"
    },
    "Chronic_liver": {
        "title": "Chronic Liver Disease",
        "description": "Evaluation of hepatic biomarkers, bilirubin, and enzyme levels.",
        "icon": "🧪",
        "category": "Hepatology"
    },
    "diabetes": {
        "title": "Diabetes Mellitus",
        "description": "Glycemic status assessment using blood glucose, HbA1c, and BMI.",
        "icon": "📊",
        "category": "Endocrinology"
    },
    "heart_disease": {
        "title": "Heart Disease Risk",
        "description": "Cardiovascular risk evaluation based on ECG, Thallium, and hemodynamic markers.",
        "icon": "🫀",
        "category": "Cardiology"
    },
    "Hepatitis": {
        "title": "Hepatitis Evaluation",
        "description": "Assessment of viral hepatitis markers, liver function, and clinical symptoms.",
        "icon": "🔬",
        "category": "Hepatology"
    },
    "Kidney": {
        "title": "Chronic Kidney Disease",
        "description": "Renal function screening using electrolytes, specific gravity, and blood urea.",
        "icon": "🩺",
        "category": "Nephrology"
    },
    "lung_cancer": {
        "title": "Lung Cancer Assessment",
        "description": "Evaluation of pulmonary symptoms, environmental factors, and lifestyle risk.",
        "icon": "🫁",
        "category": "Pulmonology"
    },
    "Parkinsons": {
        "title": "Parkinson's Disease",
        "description": "Biomedical voice measurement analysis for neurodegenerative risk.",
        "icon": "🧠",
        "category": "Neurology"
    },
    "Stroke": {
        "title": "Stroke Risk Assessment",
        "description": "Multivariate cerebrovascular stroke risk evaluation.",
        "icon": "⚡",
        "category": "Neurology"
    }
}

# Valid demo patient inputs for 1-click test patient loading
DEMO_PATIENT_DATA: Dict[str, Dict[str, Any]] = {
    "anemia": {
        "WBC": 6.5, "LYMp": 30.0, "NEUTp": 60.0, "LYMn": 2.0, "NEUTn": 4.0,
        "RBC": 4.5, "HGB": 13.5, "HCT": 40.0, "MCV": 88.0, "MCH": 29.0,
        "MCHC": 33.0, "PLT": 250.0, "PDW": 12.0, "PCT": 0.25
    },
    "B_cancer": {
        "radius_mean": 14.0, "texture_mean": 19.0, "perimeter_mean": 90.0, "area_mean": 600.0, "smoothness_mean": 0.10,
        "compactness_mean": 0.12, "concavity_mean": 0.08, "concave_points_mean": 0.05, "symmetry_mean": 0.18, "fractal_dimension_mean": 0.06,
        "radius_se": 0.40, "texture_se": 1.20, "perimeter_se": 2.80, "area_se": 40.0, "smoothness_se": 0.007,
        "compactness_se": 0.02, "concavity_se": 0.03, "concave_points_se": 0.015, "symmetry_se": 0.02, "fractal_dimension_se": 0.003,
        "radius_worst": 16.0, "texture_worst": 25.0, "perimeter_worst": 105.0, "area_worst": 800.0, "smoothness_worst": 0.14,
        "compactness_worst": 0.25, "concavity_worst": 0.27, "concave_points_worst": 0.12, "symmetry_worst": 0.29, "fractal_dimension_worst": 0.08
    },
    "Chronic_liver": {
        "Age": 45, "Gender": "male", "Total_Bilirubin": 0.8, "Direct_Bilirubin": 0.2,
        "Alkaline_Phosphotase": 200, "Alamine_Aminotransferase": 25,
        "Aspartate_Aminotransferase": 30, "Total_Protiens": 7.0,
        "Albumin": 4.0, "Albumin_and_Globulin_Ratio": 1.2
    },
    "diabetes": {
        "gender": "Female", "age": 50.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 25.4, "HbA1c_level": 5.7, "blood_glucose_level": 100.0
    },
    "heart_disease": {
        "Age": 58, "Sex": 1, "Chest_pain_type": 4, "BP": 140, "Cholesterol": 289,
        "FBS_over_120": 0, "EKG_results": 0, "Max_HR": 172, "Exercise_angina": 0,
        "ST_depression": 0.0, "Slope_of_ST": 1, "Number_of_vessels_fluro": 0, "Thallium": 3
    },
    "Hepatitis": {
        "age": 40.0, "bilirubin": 1.0, "alk_phosphate": 85.0, "sgot": 30.0, "albumin": 4.0, "protime": 80.0,
        "sex": "male", "steroid": "no", "antivirals": "no", "fatigue": "no", "malaise": "no",
        "anorexia": "no", "liver_big": "no", "liver_firm": "no", "spleen_palpable": "no",
        "spiders": "no", "ascites": "no", "varices": "no", "histology": "no"
    },
    "Kidney": {
        "Bp": 80, "Sg": 1.020, "Al": 1, "Su": 0, "Rbc": 1, "Bu": 36, "Sc": 1.2,
        "Sod": 137, "Pot": 4.4, "Hemo": 15.4, "Wbcc": 7800, "Rbcc": 5.2, "Htn": 0
    },
    "lung_cancer": {
        "GENDER": "M", "AGE": 62, "SMOKING": 2, "YELLOW_FINGERS": 2, "ANXIETY": 1,
        "PEER_PRESSURE": 1, "CHRONIC_DISEASE": 2, "FATIGUE": 2, "ALLERGY": 1,
        "WHEEZING": 2, "ALCOHOL_CONSUMING": 2, "COUGHING": 2, "SHORTNESS_OF_BREATH": 2,
        "SWALLOWING_DIFFICULTY": 2, "CHEST_PAIN": 2
    },
    "Parkinsons": {
        "MDVP:Fo(Hz)": 119.992, "MDVP:Fhi(Hz)": 157.302, "MDVP:Flo(Hz)": 74.997,
        "MDVP:Jitter(%)": 0.00784, "MDVP:Jitter(Abs)": 0.00007, "MDVP:RAP": 0.00370,
        "MDVP:PPQ": 0.00554, "Jitter:DDP": 0.01109, "MDVP:Shimmer": 0.04374,
        "MDVP:Shimmer(dB)": 0.426, "Shimmer:APQ3": 0.02182, "Shimmer:APQ5": 0.03130,
        "MDVP:APQ": 0.02971, "Shimmer:DDA": 0.06545, "NHR": 0.02211, "HNR": 21.033,
        "RPDE": 0.414783, "DFA": 0.815285, "spread1": -4.813031, "spread2": 0.266482,
        "D2": 2.301442, "PPE": 0.284654
    },
    "Stroke": {
        "gender": "Male", "age": 67.0, "hypertension": 1, "heart_disease": 0,
        "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban",
        "avg_glucose_level": 228.69, "bmi": 36.6, "smoking_status": "formerly smoked"
    }
}


class DynamicSchemaService:
    """Provides project-derived feature schemas and demo patient payloads."""

    def __init__(self):
        self.loader = ModelLoader()

    def get_all_diseases_schema(self) -> List[Dict[str, Any]]:
        """Returns metadata and feature schemas for all 10 diseases dynamically from ModelLoader."""
        diseases = []
        model_map = self.loader.DISEASE_MODEL_MAP

        for disease_id in model_map.keys():
            meta = self.loader.get_model(disease_id)
            meta_info = DISEASE_METADATA.get(disease_id, {
                "title": disease_id.replace("_", " ").title(),
                "description": f"Clinical decision support model for {disease_id}.",
                "icon": "🏥",
                "category": "General"
            })

            features_schema = []
            registered_mappings = CATEGORICAL_MAPPINGS.get(disease_id, {})

            for feat in meta.feature_names:
                field_type = "numeric"
                options = []

                if feat in registered_mappings:
                    field_type = "categorical"
                    # Deduplicate keys (e.g. Male vs male)
                    unique_opts = {}
                    for opt_str, opt_val in registered_mappings[feat].items():
                        clean_label = opt_str.capitalize() if isinstance(opt_str, str) else str(opt_str)
                        unique_opts[clean_label] = opt_str
                    options = [{"label": k, "value": v} for k, v in unique_opts.items()]
                elif feat.lower() in ["sex", "gender"]:
                    field_type = "categorical"
                    demo_val = DEMO_PATIENT_DATA.get(disease_id, {}).get(feat)
                    if isinstance(demo_val, int):
                        options = [
                            {"label": "Male", "value": 1},
                            {"label": "Female", "value": 0}
                        ]
                    elif str(demo_val).upper() in ["M", "F"]:
                        options = [
                            {"label": "Male (M)", "value": "M"},
                            {"label": "Female (F)", "value": "F"}
                        ]
                    else:
                        options = [
                            {"label": "Male", "value": "male"},
                            {"label": "Female", "value": "female"}
                        ]
                elif feat in meta.internal_categorical_cols:
                    field_type = "categorical"
                    options = [
                        {"label": "No", "value": "no"},
                        {"label": "Yes", "value": "yes"}
                    ]

                # Human-friendly field label
                pretty_label = feat.replace("_", " ").title()

                features_schema.append({
                    "name": feat,
                    "label": pretty_label,
                    "type": field_type,
                    "options": options,
                    "placeholder": f"Enter {pretty_label}"
                })

            diseases.append({
                "id": disease_id,
                "title": meta_info["title"],
                "description": meta_info["description"],
                "icon": meta_info["icon"],
                "category": meta_info["category"],
                "total_features": len(meta.feature_names),
                "features": features_schema,
                "demo_patient": DEMO_PATIENT_DATA.get(disease_id, {})
            })

        return diseases
