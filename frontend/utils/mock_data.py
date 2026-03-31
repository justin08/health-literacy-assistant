"""
Mock data - Reads from cleaned_patient_data.json
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
    if not name:
        continue
    
    pid = name.lower().replace(" ", "_")
    username = name.split()[0].lower()
    
    # Handle duplicate usernames
    if username in MOCK_USERS:
        username = f"{username}_{pid[:8]}"
    
    MOCK_USERS[username] = {"password": "password123", "role": "patient", "patient_id": pid, "name": name}
    
    # Convert measurements to observations
    obs = [{"id": f"{pid}_{i}", "display": m["test"], "value": m["result"], 
            "unit": m.get("unit", ""), "flag": "", "effective_date": m.get("date", "")} 
           for i, m in enumerate(p.get("measurements", []))]
    
    MOCK_PATIENTS[pid] = {"id": pid, "name": name, "gender": "Unknown", 
                          "conditions": [], "observations": obs, "medications": []}

# Mock explanations
EXPLANATIONS = {
    "hypertension": ("Your blood pressure is higher than normal.", ["American Heart Association"], 7.2),
    "diabetes": ("Your body has trouble using sugar for energy.", ["American Diabetes Association"], 7.5),
    "a1c": ("The A1c test measures your average blood sugar over 3 months.", ["ADA"], 6.0),
    "lisinopril": ("Lisinopril helps lower blood pressure.", ["MedlinePlus"], 6.2),
    "metformin": ("Metformin helps your body use insulin better.", ["ADA"], 6.8),
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
    for key, (text, sources, score) in EXPLANATIONS.items():
        if key in term.lower():
            return {"plain_language": text, "sources": sources, "readability_score": score}
    return {"plain_language": f"'{term}' is a medical term.", "sources": ["Demo"], "readability_score": 8.0}
