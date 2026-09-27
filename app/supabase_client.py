"""
Supabase Authentication Integration Engine for Module 8 CDSS.
Provides secure physician registration, email/password authentication, JWT session verification,
and logout session revocation using Supabase Auth.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_supabase_client = None


def get_supabase_client():
    """Initializes and returns the singleton Supabase Client instance."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        # Fallback or initialization check
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return _supabase_client
    except Exception as e:
        print(f"[SUPABASE INIT ERROR]: {e}")
        return None


def register_doctor_supabase(email: str, password: str, username: str, specialty: str, gender: Optional[str] = None) -> Dict[str, Any]:
    """
    Registers a new physician using Supabase Auth.
    Stores username, specialty, and gender inside user_metadata.
    """
    client = get_supabase_client()
    if not client:
        raise ValueError("Supabase configuration missing (SUPABASE_URL / SUPABASE_ANON_KEY not set).")

    clean_email = email.lower().strip()
    clean_username = username.strip()
    clean_specialty = specialty.strip() or "Clinical Specialist"
    clean_gender = (gender or "male").strip().lower()

    res = client.auth.sign_up({
        "email": clean_email,
        "password": password,
        "options": {
            "data": {
                "username": clean_username,
                "doctor_name": clean_username,
                "specialty": clean_specialty,
                "gender": clean_gender,
                "account_role": "CDSS_PHYSICIAN"
            }
        }
    })

    if not res.user:
        raise ValueError("Supabase registration failed. Please try again.")

    user_meta = res.user.user_metadata or {}
    return {
        "doctor_id": res.user.email,
        "doctor_name": user_meta.get("username", clean_username),
        "specialty": user_meta.get("specialty", clean_specialty),
        "gender": user_meta.get("gender", clean_gender),
        "user_id": res.user.id,
        "confirmation_sent": res.session is None
    }


def login_doctor_supabase(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticates physician email and password against Supabase Auth.
    Returns access_token and doctor profile.
    """
    client = get_supabase_client()
    if not client:
        raise ValueError("Supabase configuration missing (SUPABASE_URL / SUPABASE_ANON_KEY not set).")

    clean_email = email.lower().strip()

    try:
        res = client.auth.sign_in_with_password({
            "email": clean_email,
            "password": password
        })
    except Exception as err:
        raise ValueError("Invalid Doctor Email or Password.") from err

    if not res.user or not res.session:
        raise ValueError("Invalid Doctor Email or Password.")

    user_meta = res.user.user_metadata or {}
    return {
        "session_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "doctor": {
            "doctor_id": res.user.email,
            "doctor_name": user_meta.get("username", user_meta.get("doctor_name", "Physician")),
            "specialty": user_meta.get("specialty", "Clinical Specialist"),
            "gender": user_meta.get("gender"),
            "account_role": user_meta.get("account_role", "CDSS_PHYSICIAN")
        }
    }


def verify_token_supabase(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Validates incoming Bearer session token against Supabase Auth.
    Returns safe doctor profile dictionary on success, or None on invalid/expired token.
    """
    if not token:
        return None

    clean_token = token.replace("Bearer ", "").strip()
    client = get_supabase_client()
    if not client:
        return None

    try:
        user_res = client.auth.get_user(clean_token)
        if not user_res or not user_res.user:
            return None

        user = user_res.user
        user_meta = user.user_metadata or {}
        return {
            "doctor_id": user.email,
            "doctor_name": user_meta.get("username", user_meta.get("doctor_name", "Physician")),
            "specialty": user_meta.get("specialty", "Clinical Specialist"),
            "gender": user_meta.get("gender"),
            "account_role": user_meta.get("account_role", "CDSS_PHYSICIAN")
        }
    except Exception:
        return None


def logout_doctor_supabase(token: Optional[str]) -> bool:
    """Revokes active session token via Supabase Auth sign-out."""
    if not token:
        return False
    clean_token = token.replace("Bearer ", "").strip()
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.auth.sign_out(clean_token)
        return True
    except Exception:
        return True
