import json
import os
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent 

input_folder = base_dir / "data" / "fhir"
output_file = base_dir / "data" / "cleaned_patient_data.json"
files_to_process = 10

def extract_full_patient_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
    

    patient_record = {
        "patient_id": "Unknown",
        "name": "Unknown",
        "Condition": [],
        "MedicationRequest": [],
        "Observation": []
    }

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        res_type = resource.get('resourceType')
        
        
        if res_type == 'Patient':
            patient_record["patient_id"] = resource.get('id')
            names = resource.get('name', [{}])[0]
            patient_record["name"] = f"{' '.join(names.get('given', []))} {names.get('family', '')}".strip()

        
        elif res_type == 'Condition':
            patient_record["Condition"].append({
                "diagnosis": resource.get('code', {}).get('text', 'Unknown'),
                "date": resource.get('recordedDate', '')[:10]
            })

        
        elif res_type == 'MedicationRequest':
            dosage = resource.get('dosageInstruction', [{}])[0].get('text', 'As directed')
            patient_record["MedicationRequest"].append({
                "medication": resource.get('medicationCodeableConcept', {}).get('text', 'Unknown'),
                "dosage_instruction": dosage,
                "date": resource.get('authoredOn', '')[:10]
            })

        
        elif res_type == 'Observation':
            value_qty = resource.get('valueQuantity', {})
            if value_qty.get('value') is not None:
                patient_record["Observation"].append({
                    "test": resource.get('code', {}).get('text', 'Unknown'),
                    "result": round(float(value_qty.get('value')), 2),
                    "unit": value_qty.get('unit', ''),
                    "date": resource.get('effectiveDateTime', '')[:10]
                })

    return patient_record


all_patients = []
if not os.path.exists(input_folder):
    print(f"Error: Folder {input_folder} not found.")
else:
    
    json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]
    for filename in json_files[:files_to_process]:
        path = os.path.join(input_folder, filename)
        print(f"Processing: {filename}")
        all_patients.append(extract_full_patient_data(path))

    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_patients, f, indent=4)

    print(f"\nDone! Processed {len(all_patients)} records. Check {output_file}")