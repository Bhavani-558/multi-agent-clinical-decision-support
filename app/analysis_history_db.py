import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class AnalysisHistoryDB:
    """Small SQLite-backed persistence layer for doctor-scoped patient analysis history."""

    def __init__(self, db_path: Optional[str] = None):
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "analysis_history.sqlite3",
        )
        self.db_path = db_path or default_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self):
        if self.conn:
            self.conn.close()

    def _ensure_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                disease TEXT NOT NULL,
                prediction TEXT,
                model_probability REAL,
                analysis_timestamp TEXT NOT NULL,
                clinical_input_data TEXT,
                shap_data TEXT,
                evidence_data TEXT,
                reasoning_data TEXT,
                trust_confidence_data TEXT,
                report_data TEXT,
                final_interpretation TEXT
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_doctor_patient ON analysis_history (doctor_id, patient_id, analysis_timestamp DESC)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_doctor_name ON analysis_history (doctor_id, patient_name)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_doctor_disease ON analysis_history (doctor_id, disease)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_timestamp ON analysis_history (analysis_timestamp DESC)"
        )
        self.conn.commit()

    @staticmethod
    def _json_dumps(value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value, default=str)

    @staticmethod
    def _json_loads(value: Optional[str]) -> Any:
        if value is None or value == "":
            return None
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def save_analysis(
        self,
        doctor_id: str,
        patient_id: str,
        patient_name: str,
        disease: str,
        prediction: Optional[str] = None,
        model_probability: Optional[float] = None,
        clinical_input_data: Optional[Dict[str, Any]] = None,
        shap_data: Optional[Dict[str, Any]] = None,
        evidence_data: Optional[Dict[str, Any]] = None,
        reasoning_data: Optional[Dict[str, Any]] = None,
        trust_confidence_data: Optional[Dict[str, Any]] = None,
        report_data: Optional[Dict[str, Any]] = None,
        final_interpretation: Optional[str] = None,
    ) -> int:
        clean_doctor_id = (doctor_id or "").strip()
        clean_patient_id = (patient_id or "").strip()
        clean_patient_name = (patient_name or "").strip()
        clean_disease = (disease or "").strip()

        if not clean_doctor_id or not clean_patient_id or not clean_patient_name or not clean_disease:
            raise ValueError("Patient and doctor identifiers are required to save an analysis history record.")

        timestamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

        cursor = self.conn.execute(
            """
            INSERT INTO analysis_history (
                doctor_id,
                patient_id,
                patient_name,
                disease,
                prediction,
                model_probability,
                analysis_timestamp,
                clinical_input_data,
                shap_data,
                evidence_data,
                reasoning_data,
                trust_confidence_data,
                report_data,
                final_interpretation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_doctor_id,
                clean_patient_id,
                clean_patient_name,
                clean_disease,
                prediction,
                float(model_probability) if model_probability is not None else None,
                timestamp,
                self._json_dumps(clinical_input_data),
                self._json_dumps(shap_data),
                self._json_dumps(evidence_data),
                self._json_dumps(reasoning_data),
                self._json_dumps(trust_confidence_data),
                self._json_dumps(report_data),
                final_interpretation,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def _serialize_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "doctor_id": row["doctor_id"],
            "patient_id": row["patient_id"],
            "patient_name": row["patient_name"],
            "disease": row["disease"],
            "prediction": row["prediction"],
            "model_probability": row["model_probability"],
            "analysis_timestamp": row["analysis_timestamp"],
            "clinical_input_data": self._json_loads(row["clinical_input_data"]),
            "shap_data": self._json_loads(row["shap_data"]),
            "evidence_data": self._json_loads(row["evidence_data"]),
            "reasoning_data": self._json_loads(row["reasoning_data"]),
            "trust_confidence_data": self._json_loads(row["trust_confidence_data"]),
            "report_data": self._json_loads(row["report_data"]),
            "final_interpretation": row["final_interpretation"],
        }

    def get_history(
        self,
        doctor_id: str,
        search: Optional[str] = None,
        patient_id_filter: Optional[str] = None,
        disease_filter: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM analysis_history WHERE doctor_id = ?"
        params: List[Any] = [doctor_id]

        if patient_id_filter:
            query += " AND patient_id = ?"
            params.append(patient_id_filter)
        if disease_filter:
            query += " AND disease = ?"
            params.append(disease_filter)
        if search:
            clean_search = search.strip()
            if clean_search:
                query += " AND (LOWER(patient_id) LIKE LOWER(?) OR LOWER(patient_name) LIKE LOWER(?) OR LOWER(disease) LIKE LOWER(?))"
                like = f"%{clean_search}%"
                params.extend([like, like, like])

        query += " ORDER BY analysis_timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [self._serialize_row(row) for row in rows]

    def get_patient_history(self, patient_id: str, doctor_id: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM analysis_history WHERE doctor_id = ? AND patient_id = ? ORDER BY analysis_timestamp DESC",
            (doctor_id, patient_id),
        ).fetchall()
        return [self._serialize_row(row) for row in rows]

    def get_record(self, analysis_id: int, doctor_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM analysis_history WHERE id = ? AND doctor_id = ?",
            (analysis_id, doctor_id),
        ).fetchone()
        if row is None:
            return None
        return self._serialize_row(row)
