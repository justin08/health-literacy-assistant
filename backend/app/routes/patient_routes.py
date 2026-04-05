from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import PatientSummary, Condition, Medication, Observation
from app.services.patient_service import (
    get_all_patients,
    get_conditions,
    get_medications,
    get_observations,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=List[PatientSummary])
def list_patients(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return get_all_patients()


@router.get("/{patient_id}/conditions", response_model=List[Condition])
def patient_conditions(patient_id: str, user: dict = Depends(get_current_user)):
    _check_access(user, patient_id)
    return get_conditions(patient_id)


@router.get("/{patient_id}/medications", response_model=List[Medication])
def patient_medications(patient_id: str, user: dict = Depends(get_current_user)):
    _check_access(user, patient_id)
    return get_medications(patient_id)


@router.get("/{patient_id}/observations", response_model=List[Observation])
def patient_observations(patient_id: str, user: dict = Depends(get_current_user)):
    _check_access(user, patient_id)
    return get_observations(patient_id)


def _check_access(user: dict, patient_id: str):
    if user.get("role") == "admin":
        return
    if user.get("patient_id") != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your record")
