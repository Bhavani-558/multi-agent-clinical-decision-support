"""
FastAPI Server for Module 8 UI - Clinical Decision Support Dashboard.
Acts purely as a thin orchestration API layer serving static frontend SPA assets and invoking live Modules 1-7.
Includes PBKDF2 doctor authentication, session token verification, and route protection.
No medical calculations or report logic are duplicated or modified in this file.
"""

import sys
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel

# Ensure project root is on sys.path
sys.path.insert(0, r"d:\MultiAgent_CDSS")

from app.disease_schemas import DynamicSchemaService
from app.dataset_service import DatasetService
from agents.prediction_agent import PredictionAgent
from src.explainability.shap_service import SHAPExplainerService
from agents.evidence_agent import EvidenceAgent
from agents.reasoning_agent import ReasoningAgent
from src.fusion.fusion_engine import FusionEngine
from src.reporting.report_generator import ClinicalReportGenerator
from src.prediction.counterfactual_service import CounterfactualService

app = FastAPI(
    title="MultiAgent CDSS - Module 8 UI",
    description="Doctor Decision Support Dashboard REST API with Real Authentication",
    version="1.0.0"
)

# Instantiate schema service & lazy-loaded module singletons
schema_service = DynamicSchemaService()
dataset_service = DatasetService()
pred_agent = PredictionAgent()
shap_service = SHAPExplainerService()
ev_agent = EvidenceAgent()
reasoning_agent = ReasoningAgent()
fusion_engine = FusionEngine()
report_generator = ClinicalReportGenerator()
counterfactual_service = CounterfactualService()


class LoginRequest(BaseModel):
    doctor_id: str
    password: str


class RegisterRequest(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    password: str
    gender: Optional[str] = None


class LogoutRequest(BaseModel):
    session_token: Optional[str] = None


class AnalysisRequest(BaseModel):
    disease: str
    patient_features: Dict[str, Any]
    patient_metadata: Optional[Dict[str, Any]] = None


class ExportRequest(BaseModel):
    markdown_report: str
    patient_id: str
    disease: str
    format: str = "markdown"


class WhatIfRequest(BaseModel):
    disease: str
    original_features: Dict[str, Any]
    modified_features: Dict[str, Any]


# Mount static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


from app.supabase_client import (
    register_doctor_supabase,
    login_doctor_supabase,
    verify_token_supabase,
    logout_doctor_supabase,
    get_supabase_client
)
from app.analysis_history_db import AnalysisHistoryDB

from app.auth import DoctorCredentialStore, SessionRegistry

doc_store = DoctorCredentialStore()
session_reg = SessionRegistry()
history_db = AnalysisHistoryDB()


def verify_session(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency protecting API routes. Accepts valid Supabase JWT or local Session Token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")

    if get_supabase_client():
        doctor_profile = verify_token_supabase(authorization)
        if doctor_profile:
            return doctor_profile

    local_profile = session_reg.validate_session(authorization)
    if local_profile:
        return local_profile

    raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0"}
        )
    return HTMLResponse("<h2>Module 8 UI - Static assets loading...</h2>")


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """
    Authenticates physician email and password against Supabase Auth, with local fallback only when Supabase is unavailable.
    """
    if not req.doctor_id or not req.password:
        raise HTTPException(status_code=400, detail="Doctor Email and password are required.")

    # Supabase is authoritative whenever it is configured.
    supabase_client = get_supabase_client()
    if supabase_client:
        try:
            auth_res = login_doctor_supabase(req.doctor_id, req.password)
            return {
                "status": "success",
                "session_token": auth_res["session_token"],
                "doctor": auth_res["doctor"]
            }
        except Exception as exc:
            cause = getattr(exc, "__cause__", None)
            cause_type = type(cause).__name__ if cause else type(exc).__name__
            print(f"[SUPABASE LOGIN ERROR] {cause_type}: authentication request failed")
            raise HTTPException(status_code=401, detail="Supabase authentication failed. Check the account, password, and Supabase connectivity.")

    # Local fallback is used only when Supabase is not configured or unavailable.
    local_doc = doc_store.authenticate(req.doctor_id, req.password)
    if local_doc:
        token = session_reg.create_session(local_doc)
        return {
            "status": "success",
            "session_token": token,
            "doctor": local_doc
        }

    raise HTTPException(status_code=401, detail="Invalid Doctor Email or password.")


@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """
    Registers new doctor account locally and in Supabase Auth.
    """
    clean_id = req.doctor_id.lower().strip()
    clean_name = req.doctor_name.strip()
    clean_specialty = req.specialty.strip()
    clean_gender = (req.gender or "female").strip().lower()

    if not clean_id or not clean_name or not req.password:
        raise HTTPException(status_code=400, detail="All required fields must be completed.")

    if "@" not in clean_id or "." not in clean_id:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    supabase_client = get_supabase_client()
    if supabase_client:
        try:
            supabase_res = register_doctor_supabase(
                email=clean_id,
                password=req.password,
                username=clean_name,
                specialty=clean_specialty,
                gender=clean_gender
            )
            return {
                "status": "success",
                "message": "Physician account created in Supabase. Confirm your email if required, then sign in.",
                "doctor": supabase_res,
            }
        except Exception as exc:
            print(f"[SUPABASE REGISTRATION ERROR] {type(exc).__name__}: registration request failed")
            raise HTTPException(status_code=400, detail="Supabase registration failed. Check the account details and Supabase connectivity.")

    local_res = doc_store.register_doctor(clean_id, clean_name, clean_specialty, req.password, clean_gender)

    return {
        "status": "success",
        "message": "Local physician account created successfully. Please sign in.",
        "doctor": local_res
    }


@app.post("/api/auth/logout")
async def logout(req: LogoutRequest, authorization: Optional[str] = Header(None)):
    """Revokes active Supabase Auth session token upon physician sign-out."""
    token_to_revoke = req.session_token or authorization
    if token_to_revoke:
        logout_doctor_supabase(token_to_revoke)
        session_reg.revoke_session(token_to_revoke)
    return {"status": "success", "message": "Session invalidated."}


@app.get("/api/diseases")
async def get_diseases(doctor: Dict[str, Any] = Depends(verify_session)):
    """Protected Endpoint: Returns dynamic feature schemas & demo payloads for all 10 diseases."""
    return {
        "status": "success",
        "doctor_id": doctor["doctor_id"],
        "diseases": schema_service.get_all_diseases_schema()
    }


@app.get("/api/dataset/{disease}/info")
async def get_dataset_info(disease: str, doctor: Dict[str, Any] = Depends(verify_session)):
    """Protected Endpoint: Returns metadata about the local raw dataset for the given disease."""
    try:
        info = dataset_service.get_dataset_info(disease)
        return {"status": "success", "info": info}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset info: {str(e)}")


@app.get("/api/dataset/{disease}/preview")
async def get_dataset_preview(
    disease: str,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    target_filter: Optional[str] = None,
    doctor: Dict[str, Any] = Depends(verify_session)
):
    """Protected Endpoint: Returns paginated preview rows of the dataset for physician selection."""
    try:
        preview = dataset_service.get_dataset_preview(
            disease=disease,
            limit=limit,
            offset=offset,
            search=search,
            target_filter=target_filter
        )
        return {"status": "success", "preview": preview}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview dataset: {str(e)}")


@app.get("/api/dataset/{disease}/row/{row_index}")
async def get_dataset_row(
    disease: str,
    row_index: int,
    doctor: Dict[str, Any] = Depends(verify_session)
):
    """
    Protected Endpoint: Retrieves and returns cleaned features from an exact dataset row (0-indexed).
    Removes identifier and target columns so only input features are returned.
    """
    try:
        data = dataset_service.get_dataset_row(disease, row_index)
        return {"status": "success", "data": data}
    except IndexError as ie:
        raise HTTPException(status_code=400, detail=str(ie))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset row: {str(e)}")


@app.get("/api/dataset/{disease}/load-row/{row_number}")
async def load_dataset_row_1based(
    disease: str,
    row_number: int,
    doctor: Dict[str, Any] = Depends(verify_session)
):
    """
    Protected Endpoint: 1-based dataset row loader (Row 1, Row 2, etc.)
    Retrieves and returns cleaned features from an exact dataset row.
    """
    try:
        data = dataset_service.get_dataset_row_1based(disease, row_number)
        return {"status": "success", "data": data}
    except IndexError as ie:
        raise HTTPException(status_code=400, detail=str(ie))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset row: {str(e)}")



def _extract_prediction_snapshot(report: Dict[str, Any]) -> Dict[str, Any]:
    sections = report.get("sections") or []
    pred_section = next(
        (section for section in sections if section.get("section_id") in {"disease_prediction", "prediction"}),
        None,
    )
    metrics = (pred_section or {}).get("metrics") or {}
    pred_label = metrics.get("predicted_result") or metrics.get("prediction") or "Unknown"
    prob_value = metrics.get("model_probability")
    if isinstance(prob_value, str):
        cleaned = prob_value.replace("%", "").strip()
        try:
            probability = float(cleaned)
            if "%" in str(prob_value):
                probability = probability / 100.0
        except (TypeError, ValueError):
            probability = None
    else:
        probability = float(prob_value) if prob_value is not None else None

    return {
        "prediction": pred_label,
        "model_probability": probability,
    }


@app.get("/api/history")
async def get_analysis_history(
    doctor: Dict[str, Any] = Depends(verify_session),
    search: Optional[str] = None,
    patient_id: Optional[str] = None,
    disease: Optional[str] = None,
):
    """Protected list endpoint for authenticated doctor's analysis history."""
    doctor_id = (doctor.get("doctor_id") or doctor.get("doctor") or "").strip()
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Doctor identity is unavailable.")
    return {
        "status": "success",
        "items": history_db.get_history(
            doctor_id=doctor_id,
            search=search,
            patient_id_filter=patient_id,
            disease_filter=disease,
        )
    }


@app.get("/api/history/{analysis_id}")
async def get_analysis_history_record(
    analysis_id: int,
    doctor: Dict[str, Any] = Depends(verify_session),
):
    """Protected endpoint for retrieving a previously saved report record."""
    doctor_id = (doctor.get("doctor_id") or doctor.get("doctor") or "").strip()
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Doctor identity is unavailable.")
    record = history_db.get_record(analysis_id=analysis_id, doctor_id=doctor_id)
    if record is None:
        raise HTTPException(status_code=404, detail="History record not found.")
    return {"status": "success", "item": record}


@app.get("/api/history/patient/{patient_id}")
async def get_patient_history(
    patient_id: str,
    doctor: Dict[str, Any] = Depends(verify_session),
):
    """Protected endpoint for the authenticated doctor's prior analyses for a specific patient."""
    doctor_id = (doctor.get("doctor_id") or doctor.get("doctor") or "").strip()
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Doctor identity is unavailable.")
    records = history_db.get_patient_history(patient_id=patient_id, doctor_id=doctor_id)
    return {"status": "success", "items": records}


@app.post("/api/analyze")
async def analyze_patient(req: AnalysisRequest, doctor: Dict[str, Any] = Depends(verify_session)):
    """
    Protected Endpoint: Executes live E2E pipeline (Modules 1-7) for the given disease and patient features.
    Returns exact Pydantic report payload without modifying or recalculating any scores.
    """
    try:
        disease = req.disease
        features = req.patient_features
        metadata = req.patient_metadata or {
            "patient_id": "PATIENT-REF-1092",
            "target_disease": disease,
            "evaluating_physician": doctor["doctor_name"]
        }
        if "age" not in metadata and "Age" in features:
            metadata["age"] = features["Age"]
        elif "age" not in metadata and "age" in features:
            metadata["age"] = features["age"]
        if "gender" not in metadata and "Sex" in features:
            metadata["gender"] = features["Sex"]
        elif "gender" not in metadata and "gender" in features:
            metadata["gender"] = features["gender"]

        # Module 1: Prediction
        pred_res = pred_agent.predict_single_disease(disease=disease, features=features)

        # Module 2: SHAP Explanation
        shap_res = shap_service.explain_prediction(disease=disease, patient_features=features)

        # Module 3 & 4: PrimeKG Evidence Retrieval & Evidence Agent
        evidence_resp = ev_agent.evaluate_evidence(
            model_id=disease,
            prediction=pred_res.model_dump(),
            shap_explanation=shap_res.model_dump()
        )
        graph_evidence = evidence_resp.graph_evidence

        # Module 5: Reasoning & Trust Layer
        reasoning_out = reasoning_agent.evaluate_evidence_payload(evidence_resp)

        # Module 6: Decision / Fusion Layer
        decision_out = fusion_engine.evaluate_fusion(
            reasoning=reasoning_out,
            shap_explanation=shap_res.model_dump(),
            graph_evidence=graph_evidence
        )

        # Module 7: Clinical Report Generation
        report_out = report_generator.generate_report(
            decision_output=decision_out,
            reasoning_output=reasoning_out,
            graph_evidence=graph_evidence,
            patient_metadata=metadata,
            llm_explanation=evidence_resp.llm_explanation
        )

        latest_report_payload = report_out.model_dump()
        prediction_snapshot = _extract_prediction_snapshot(latest_report_payload)
        doctor_id = doctor.get("doctor_id") or doctor.get("doctor", {}).get("doctor_id")
        patient_id = str(metadata.get("patient_id") or "").strip()
        patient_name = str(metadata.get("patient_name") or "").strip()

        if doctor_id and patient_id and patient_name:
            final_interpretation = ""
            for section in latest_report_payload.get("sections") or []:
                if section.get("section_id") in {"final_interpretation", "interpretation"}:
                    final_interpretation = section.get("summary_text") or ""
                    break
            if not final_interpretation:
                final_interpretation = latest_report_payload.get("llm_explanation") or ""

            history_db.save_analysis(
                doctor_id=doctor_id,
                patient_id=patient_id,
                patient_name=patient_name,
                disease=disease,
                prediction=prediction_snapshot.get("prediction"),
                model_probability=prediction_snapshot.get("model_probability"),
                clinical_input_data=req.patient_features,
                shap_data=(shap_res.model_dump() if hasattr(shap_res, "model_dump") else shap_res),
                evidence_data=(evidence_resp.model_dump() if hasattr(evidence_resp, "model_dump") else evidence_resp),
                reasoning_data=(reasoning_out.model_dump() if hasattr(reasoning_out, "model_dump") else reasoning_out),
                trust_confidence_data=(decision_out.model_dump() if hasattr(decision_out, "model_dump") else decision_out),
                report_data=latest_report_payload,
                final_interpretation=final_interpretation,
            )

        return {
            "status": "success",
            "disease": disease,
            "patient_features": features,
            "report": latest_report_payload
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline evaluation error: {str(e)}")


@app.post("/api/export-report")
async def export_report(req: ExportRequest, doctor: Dict[str, Any] = Depends(verify_session)):
    """Protected Endpoint: Exports clinical report as downloadable file."""
    filename = f"Clinical_Report_{req.disease}_{req.patient_id}.md"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return Response(content=req.markdown_report, media_type="text/markdown", headers=headers)


@app.post("/api/export-pdf")
async def export_pdf(req: ExportRequest, doctor: Dict[str, Any] = Depends(verify_session)):
    """Protected Endpoint: Exports standardized clinical decision support report as professional PDF."""
    from src.reporting.pdf_exporter import build_clinical_report_pdf
    pdf_buffer = build_clinical_report_pdf(req.markdown_report)
    filename = f"Clinical_Report_{req.disease}_{req.patient_id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers=headers)


@app.post("/api/what-if")
async def simulate_what_if(req: WhatIfRequest, doctor: Dict[str, Any] = Depends(verify_session)):
    """
    Protected Endpoint: Executes counterfactual what-if simulation by varying selected features
    and re-running the frozen model pipeline. Does NOT retrain or alter any model.
    """
    try:
        res = counterfactual_service.simulate_what_if(
            disease=req.disease,
            original_features=req.original_features,
            modified_features=req.modified_features
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counterfactual simulation error: {str(e)}")


@app.get("/api/what-if/status/{disease}")
async def get_what_if_status(disease: str, doctor: Dict[str, Any] = Depends(verify_session)):
    """Protected Endpoint: Returns whether What-If is enabled or locked for the requested disease."""
    is_locked, reason = counterfactual_service.is_disease_locked(disease)
    supported = disease in counterfactual_service.get_supported_diseases()
    return {
        "status": "success",
        "disease": disease,
        "is_locked": is_locked,
        "lock_reason": reason,
        "is_supported": supported
    }

