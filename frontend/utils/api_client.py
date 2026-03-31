"""
API Client for Health Literacy Assistant (Mock Mode)
Returns mock data only - no external API calls
"""

from typing import Dict, Optional, List
from utils.mock_data import (
    get_conditions, get_observations, get_medications,
    get_all_patients, verify_user, explain_term
)

class APIClient:
    """Client that returns mock data (standalone mode)"""

    def __init__(self):
        self.token = None

    def set_token(self, token: str):
        self.token = token

    # ========== Public Methods ==========

    def login(self, username: str, password: str) -> Optional[Dict]:
        result = verify_user(username, password)
        if result["success"]:
            return {
                "access_token": "mock_jwt_token",
                "token_type": "bearer",
                "role": result["role"],
                "patient_id": result["patient_id"],
                "name": result["name"],
                "username": result["username"]
            }
        return None

    def get_patient_conditions(self, patient_id: str) -> Optional[List]:
        return get_conditions(patient_id)

    def get_patient_observations(self, patient_id: str) -> Optional[List]:
        return get_observations(patient_id)

    def get_patient_medications(self, patient_id: str) -> Optional[List]:
        return get_medications(patient_id)

    def get_all_patients(self) -> Optional[List]:
        return get_all_patients()

    def explain_medical_term(self, term: str, context: str = None) -> Optional[Dict]:
        return explain_term(term, context)

    def health_check(self) -> Dict[str, bool]:
        return {"backend": True, "database": True}
