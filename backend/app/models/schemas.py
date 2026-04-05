from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    patient_id: Optional[str] = None
    name: str
    username: str


class PatientSummary(BaseModel):
    id: str
    name: str


class Condition(BaseModel):
    display: str
    clinical_status: str
    recorded_date: str


class Medication(BaseModel):
    medication_name: str
    instructions: str
    purpose: str = ""
    prescribed_date: str


class Observation(BaseModel):
    id: str
    display: str
    value: Optional[float] = None
    unit: str = ""
    flag: str = ""
    effective_date: str


class ExplainRequest(BaseModel):
    term: str
    context: Optional[str] = ""


class ExplainResponse(BaseModel):
    plain_language: str
    sources: list[str]
    readability_score: float


class HealthResponse(BaseModel):
    backend: bool
    database: bool
    rag_ready: bool
