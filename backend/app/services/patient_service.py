import json
import os
from app.config import settings


def _load_patients():
    path = os.path.join(settings.data_dir, "cleaned_patient_data.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"patient data not found at {path}")
        return []


_raw_data = _load_patients()

USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "patient_id": None,
        "name": "Admin User",
    }
}

PATIENTS = {}

for p in _raw_data:
    name = p.get("name", "")
    pid = p.get("patient_id", "")
    if not name or not pid:
        continue

    username = name.lower().replace(" ", "_")
    original = username
    counter = 1
    while username in USERS:
        username = f"{original}_{counter}"
        counter += 1

    USERS[username] = {
        "password": "password123",
        "role": "patient",
        "patient_id": pid,
        "name": name,
    }

    conditions = []
    for c in p.get("Condition", []):
        conditions.append(
            {
                "display": c.get("diagnosis", "Unknown"),
                "clinical_status": "active",
                "recorded_date": c.get("date", ""),
            }
        )

    medications = []
    for m in p.get("MedicationRequest", []):
        medications.append(
            {
                "medication_name": m.get("medication", "Unknown"),
                "instructions": m.get("dosage_instruction", "As directed"),
                "purpose": "",
                "prescribed_date": m.get("date", ""),
            }
        )

    observations = []
    for o in p.get("Observation", []):
        obs = {
            "id": f"{pid}_{len(observations)}",
            "display": o.get("test", "Unknown"),
            "value": o.get("result"),
            "unit": o.get("unit", ""),
            "flag": "",
            "effective_date": o.get("date", ""),
        }
        if obs["display"].lower() == "hemoglobin a1c" and obs["value"] and obs["value"] > 6.0:
            obs["flag"] = "H"
        observations.append(obs)

    PATIENTS[pid] = {
        "id": pid,
        "name": name,
        "conditions": conditions,
        "observations": observations,
        "medications": medications,
    }


def verify_user(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if user and user["password"] == password:
        return {
            "role": user["role"],
            "patient_id": user["patient_id"],
            "name": user["name"],
            "username": username,
        }
    return None


def get_all_patients() -> list:
    return [{"id": pid, "name": p["name"]} for pid, p in PATIENTS.items()]


def get_conditions(patient_id: str) -> list:
    patient = PATIENTS.get(patient_id)
    return patient["conditions"] if patient else []


def get_medications(patient_id: str) -> list:
    patient = PATIENTS.get(patient_id)
    return patient["medications"] if patient else []


def get_observations(patient_id: str) -> list:
    patient = PATIENTS.get(patient_id)
    return patient["observations"] if patient else []
