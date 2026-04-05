import os
import requests
from utils.mock_data import (
    get_conditions, get_observations, get_medications,
    get_all_patients, verify_user, explain_term
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIClient:
    def __init__(self):
        self.token = None
        self._mock = False

    def set_token(self, token: str):
        self.token = token

    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _get(self, path):
        try:
            r = requests.get(f"{BACKEND_URL}{path}", headers=self._headers(), timeout=5)
            if r.status_code == 200:
                return r.json()
        except (requests.ConnectionError, requests.Timeout):
            self._mock = True
        return None

    def _post(self, path, data):
        try:
            r = requests.post(f"{BACKEND_URL}{path}", json=data, headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return r.json()
        except (requests.ConnectionError, requests.Timeout):
            self._mock = True
        return None

    def login(self, username, password):
        result = self._post("/api/auth/login", {"username": username, "password": password})
        if result:
            return result

        # mock fallback
        mock = verify_user(username, password)
        if mock["success"]:
            return {
                "access_token": "mock_jwt_token",
                "token_type": "bearer",
                "role": mock["role"],
                "patient_id": mock["patient_id"],
                "name": mock["name"],
                "username": mock["username"],
            }
        return None

    def get_patient_conditions(self, patient_id):
        result = self._get(f"/api/patients/{patient_id}/conditions")
        return result if result is not None else get_conditions(patient_id)

    def get_patient_observations(self, patient_id):
        result = self._get(f"/api/patients/{patient_id}/observations")
        return result if result is not None else get_observations(patient_id)

    def get_patient_medications(self, patient_id):
        result = self._get(f"/api/patients/{patient_id}/medications")
        return result if result is not None else get_medications(patient_id)

    def get_all_patients(self):
        result = self._get("/api/patients")
        return result if result is not None else get_all_patients()

    def explain_medical_term(self, term, context=None):
        result = self._post("/api/explain", {"term": term, "context": context or ""})
        return result if result is not None else explain_term(term, context)

    def health_check(self):
        result = self._get("/api/health")
        return result or {"backend": False, "database": False, "rag_ready": False}
