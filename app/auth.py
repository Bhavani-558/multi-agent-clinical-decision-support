"""
LEGACY REFERENCE: Authentication Engine & Credential Store for Module 8 UI.
NOTE: Active physician authentication, registration, session JWT tokens, and password security
have been migrated to Supabase Auth (see app/supabase_client.py).
This file and data/doctors_db.json are retained untouched as legacy fallback/reference components.

DISCLAIMER: Authentication controls access to registered CDSS doctor accounts within this software system.
It does not constitute real-world medical licensure verification.
"""

import os
import json
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "doctors_db.json")

# Password Hashing Utilities (PBKDF2-HMAC-SHA256)
ITERATIONS = 100_000
SALT_SIZE = 16


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Hashes password with PBKDF2-HMAC-SHA256 and salt. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = secrets.token_bytes(SALT_SIZE)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )
    return hash_bytes.hex(), salt.hex()


def verify_password(password: str, stored_hash_hex: str, salt_hex: str) -> bool:
    """Verifies candidate password against stored hash using constant-time digest comparison."""
    try:
        salt = bytes.fromhex(salt_hex)
        candidate_hash_hex, _ = hash_password(password, salt)
        return hmac.compare_digest(candidate_hash_hex, stored_hash_hex)
    except Exception:
        return False


class DoctorCredentialStore:
    """Persistent credential store for registered CDSS doctor accounts."""

    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path

    def _load_db(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return {}
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_db(self, data: Dict[str, Dict[str, Any]]):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_doctor(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        db = self._load_db()
        return db.get(doctor_id.lower().strip())

    def authenticate(self, doctor_id: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates doctor credentials with failproof fallback for registered CDSS physicians.
        Returns safe doctor profile dictionary on success.
        """
        clean_id = doctor_id.lower().strip()
        record = self.get_doctor(clean_id)
        if record:
            if not verify_password(password, record.get("password_hash", ""), record.get("salt", "")):
                return None
            return {
                "doctor_id": record["doctor_id"],
                "doctor_name": record["doctor_name"],
                "specialty": record.get("specialty", "Clinical Specialist"),
                "gender": record.get("gender", "female"),
                "account_role": record.get("account_role", "CDSS_PHYSICIAN")
            }

        return None

    def register_doctor(self, doctor_id: str, doctor_name: str, specialty: str, password: str, gender: Optional[str] = "female") -> Dict[str, Any]:
        """Registers or updates a doctor account with hashed password."""
        clean_id = doctor_id.lower().strip()
        db = self._load_db()

        hash_hex, salt_hex = hash_password(password)
        record = {
            "doctor_id": clean_id,
            "doctor_name": doctor_name,
            "specialty": specialty,
            "gender": gender or "female",
            "account_role": "CDSS_PHYSICIAN",
            "password_hash": hash_hex,
            "salt": salt_hex,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        db[clean_id] = record
        self._save_db(db)
        return {
            "doctor_id": clean_id,
            "doctor_name": doctor_name,
            "specialty": specialty,
            "gender": gender or "female"
        }


class SessionRegistry:
    """In-memory session token registry with 2-hour TTL expiration & token revocation."""

    def __init__(self, ttl_hours: float = 2.0):
        self.ttl = timedelta(hours=ttl_hours)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, doctor_profile: Dict[str, Any]) -> str:
        """Generates a secure 64-character token and registers active session."""
        token = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + self.ttl
        self._sessions[token] = {
            "doctor": doctor_profile,
            "expires_at": expires_at
        }
        return token

    def validate_session(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validates token. Returns doctor profile if active and unexpired, else None."""
        if not token:
            return None
            
        clean_token = token.replace("Bearer ", "").strip()
        session = self._sessions.get(clean_token)

        if not session:
            return None

        if datetime.now(timezone.utc) > session["expires_at"]:
            # Expired token -> revoke and reject
            self.revoke_session(clean_token)
            return None

        return session["doctor"]

    def revoke_session(self, token: Optional[str]) -> bool:
        """Revokes token server-side upon logout."""
        if not token:
            return False
        clean_token = token.replace("Bearer ", "").strip()
        if clean_token in self._sessions:
            del self._sessions[clean_token]
            return True
        return False
