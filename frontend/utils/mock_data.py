"""
Mock data - Reads from cleaned_patient_data.json (FHIR format)
"""

import json
import os

# Load JSON data
def _load_json():
    path = os.path.join(os.path.dirname(__file__), 'cleaned_patient_data.json')
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

data = _load_json()

# Build users and patients
MOCK_USERS = {"admin": {"password": "admin123", "role": "admin", "patient_id": None, "name": "Admin User"}}
MOCK_PATIENTS = {}

for p in data:
    name = p.get("name", "")
    patient_id = p.get("patient_id", "")
    if not name or not patient_id:
        continue
    
    # Create username from full name (lowercase, replace spaces with underscores)
    username = name.lower().replace(" ", "_")
    
    # If username already exists, add a suffix
    original_username = username
    counter = 1
    while username in MOCK_USERS:
        username = f"{original_username}_{counter}"
        counter += 1
    
    MOCK_USERS[username] = {"password": "password123", "role": "patient", "patient_id": patient_id, "name": name}
    
    # Convert conditions
    conditions = []
    for c in p.get("Condition", []):
        conditions.append({
            "display": c.get("diagnosis", "Unknown"),
            "clinical_status": "active",
            "recorded_date": c.get("date", "")
        })
    
    # Convert medications
    medications = []
    for m in p.get("MedicationRequest", []):
        medications.append({
            "medication_name": m.get("medication", "Unknown"),
            "instructions": m.get("dosage_instruction", "As directed"),
            "purpose": "",
            "prescribed_date": m.get("date", "")
        })
    
    # Convert observations
    observations = []
    for o in p.get("Observation", []):
        obs = {
            "id": f"{patient_id}_{len(observations)}",
            "display": o.get("test", "Unknown"),
            "value": o.get("result"),
            "unit": o.get("unit", ""),
            "flag": "",
            "effective_date": o.get("date", "")
        }
        # Add flag for abnormal values
        if obs["display"].lower() == "hemoglobin a1c" and obs["value"] and obs["value"] > 6.0:
            obs["flag"] = "H"
        observations.append(obs)
    
    MOCK_PATIENTS[patient_id] = {
        "id": patient_id,
        "name": name,
        "gender": "Unknown",
        "birth_date": None,
        "conditions": conditions,
        "observations": observations,
        "medications": medications
    }

print(f"Loaded {len(MOCK_PATIENTS)} patients with conditions, medications, and observations")
print(f"Created {len(MOCK_USERS)} user accounts")

# Mock explanations
EXPLANATIONS = {
    "hypertension": ("Your blood pressure is higher than normal. This means your heart is working harder than it should to pump blood.", ["American Heart Association"], 7.2),
    "diabetes": ("Your body has trouble using sugar for energy. This causes sugar to build up in your blood.", ["American Diabetes Association"], 7.5),
    "hyperlipidemia": ("This means high cholesterol in your blood. Too much cholesterol can build up in your arteries over time.", ["American Heart Association"], 6.8),
    "a1c": ("The A1c test measures your average blood sugar over 3 months. Lower numbers mean better control.", ["American Diabetes Association"], 6.0),
    "glucose": ("Glucose is the main type of sugar in your blood. It comes from the food you eat.", ["MedlinePlus"], 6.8),
    "cholesterol": ("Cholesterol is a waxy substance in your blood. High levels can increase heart disease risk.", ["American Heart Association"], 6.6),
    "lisinopril": ("Lisinopril helps lower blood pressure by relaxing your blood vessels.", ["MedlinePlus"], 6.2),
    "metformin": ("Metformin helps your body use insulin better and lowers sugar production.", ["American Diabetes Association"], 6.8),
    "simvistatin": ("Simvastatin is a statin that helps lower cholesterol.", ["American Heart Association"], 6.5),
}

# Helper functions
def get_patient(pid): return MOCK_PATIENTS.get(pid)
def get_conditions(pid): return MOCK_PATIENTS.get(pid, {}).get("conditions", [])
def get_observations(pid): return MOCK_PATIENTS.get(pid, {}).get("observations", [])
def get_medications(pid): return MOCK_PATIENTS.get(pid, {}).get("medications", [])
def get_all_patients(): return [{"id": pid, "name": p["name"]} for pid, p in MOCK_PATIENTS.items()]

def verify_user(username, password):
    u = MOCK_USERS.get(username)
    if u and u["password"] == password:
        return {"success": True, "role": u["role"], "patient_id": u["patient_id"], "name": u["name"], "username": username}
    return {"success": False}

def explain_term(term, context=""):
    term_lower = term.lower()
    for key, (text, sources, score) in EXPLANATIONS.items():
        if key in term_lower:
            return {"plain_language": text, "sources": sources, "readability_score": score}
    return {"plain_language": f"'{term}' is a medical term.", "sources": ["Demo"], "readability_score": 8.0}
