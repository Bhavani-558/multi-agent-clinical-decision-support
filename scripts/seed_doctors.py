"""
Seeding script for registered CDSS doctor accounts.
Hashes passwords using PBKDF2-HMAC-SHA256 and writes secure accounts to data/doctors_db.json.
No plaintext passwords are stored in the database.
"""

import sys
import os

sys.path.insert(0, r"d:\MultiAgent_CDSS")

from dotenv import load_dotenv
from app.auth import DoctorCredentialStore

load_dotenv()

def seed_doctors():
    store = DoctorCredentialStore()

    # Read credentials from environment or default dev variables
    doc1_email = os.getenv("SEED_DOCTOR_EMAIL_1", "dr.jenkins@hospital.org")
    doc1_pass = os.getenv("SEED_DOCTOR_PASSWORD_1", "ClinicalSupport2026!")

    doc2_email = os.getenv("SEED_DOCTOR_EMAIL_2", "dr.chen@clinical.org")
    doc2_pass = os.getenv("SEED_DOCTOR_PASSWORD_2", "MedicalAudit2026!")

    print("=== SEEDING CDSS REGISTERED DOCTOR ACCOUNTS ===")
    
    res1 = store.register_doctor(
        doctor_id=doc1_email,
        doctor_name="Dr. Sarah Jenkins, MD",
        specialty="Cardiology & Clinical Support",
        password=doc1_pass
    )
    print(f"Registered Doctor: {res1['doctor_name']} ({res1['doctor_id']})")

    res2 = store.register_doctor(
        doctor_id=doc2_email,
        doctor_name="Dr. Michael Chen, MD",
        specialty="Oncology & Hematology",
        password=doc2_pass
    )
    print(f"Registered Doctor: {res2['doctor_name']} ({res2['doctor_id']})")

    print("Doctor credential database successfully seeded at data/doctors_db.json!")

if __name__ == "__main__":
    seed_doctors()
