"""Fetch drug/medication content from MedlinePlus Connect API.
"""

import json
import logging
import re
import time
from pathlib import Path
 
import requests
from bs4 import BeautifulSoup
 
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PATIENT_DATA = DATA_DIR / "cleaned_patient_data.json"
DRUGS_OUTPUT_DIR = DATA_DIR / "knowledge_docs" / "raw" / "drugs"
 
CONNECT_API = "https://connect.medlineplus.gov/service"
RXNORM_CS = "2.16.840.1.113883.6.88"
 
# Broad coverage: top prescribed drugs in the US + common Synthea medications
COMMON_DRUGS = [
    # Cardiovascular
    "Lisinopril", "Amlodipine", "Losartan", "Metoprolol", "Atenolol",
    "Carvedilol", "Valsartan", "Enalapril", "Ramipril", "Diltiazem",
    "Nifedipine", "Hydrochlorothiazide", "Furosemide", "Spironolactone",
    "Chlorthalidone", "Warfarin", "Clopidogrel", "Apixaban", "Rivaroxaban",
    "Heparin", "Digoxin", "Amiodarone", "Hydralazine", "Clonidine",
    "Prazosin", "Isosorbide",
 
    # Cholesterol / Lipids
    "Atorvastatin", "Simvastatin", "Rosuvastatin", "Pravastatin",
    "Lovastatin", "Ezetimibe", "Fenofibrate", "Gemfibrozil",
 
    # Diabetes
    "Metformin", "Glipizide", "Glyburide", "Glimepiride",
    "Insulin", "Insulin Glargine", "Insulin Lispro", "Insulin Aspart",
    "Sitagliptin", "Empagliflozin", "Dapagliflozin", "Canagliflozin",
    "Liraglutide", "Semaglutide", "Dulaglutide", "Pioglitazone",
 
    # Pain / Anti-inflammatory
    "Ibuprofen", "Naproxen", "Acetaminophen", "Aspirin",
    "Meloxicam", "Diclofenac", "Celecoxib", "Indomethacin",
    "Tramadol", "Hydrocodone", "Oxycodone", "Morphine",
    "Codeine", "Gabapentin", "Pregabalin", "Lidocaine",
 
    # Mental Health
    "Sertraline", "Fluoxetine", "Escitalopram", "Citalopram",
    "Paroxetine", "Venlafaxine", "Duloxetine", "Bupropion",
    "Trazodone", "Mirtazapine", "Amitriptyline", "Nortriptyline",
    "Alprazolam", "Lorazepam", "Diazepam", "Clonazepam",
    "Buspirone", "Hydroxyzine", "Lithium", "Quetiapine",
    "Risperidone", "Aripiprazole", "Olanzapine", "Haloperidol",
 
    # Respiratory
    "Albuterol", "Fluticasone", "Budesonide", "Montelukast",
    "Tiotropium", "Ipratropium", "Prednisone", "Prednisolone",
    "Dexamethasone", "Methylprednisolone", "Theophylline",
    "Cetirizine", "Loratadine", "Fexofenadine", "Diphenhydramine",
 
    # Gastrointestinal
    "Omeprazole", "Pantoprazole", "Esomeprazole", "Lansoprazole",
    "Famotidine", "Ranitidine", "Ondansetron", "Metoclopramide",
    "Loperamide", "Docusate", "Polyethylene Glycol", "Lactulose",
    "Sucralfate", "Mesalamine",
 
    # Antibiotics
    "Amoxicillin", "Azithromycin", "Ciprofloxacin", "Levofloxacin",
    "Doxycycline", "Metronidazole", "Cephalexin", "Sulfamethoxazole",
    "Trimethoprim", "Clindamycin", "Nitrofurantoin", "Penicillin",
    "Amoxicillin Clavulanate", "Ceftriaxone", "Vancomycin",
 
    # Thyroid / Endocrine
    "Levothyroxine", "Methimazole", "Propylthiouracil",
 
    # Bone / Joint
    "Alendronate", "Methotrexate", "Allopurinol", "Colchicine",
    "Cyclobenzaprine", "Tizanidine",
 
    # Seizure / Neuro
    "Carbamazepine", "Levetiracetam", "Phenytoin", "Valproic Acid",
    "Lamotrigine", "Topiramate", "Oxcarbazepine",
    "Donepezil", "Memantine", "Carbidopa Levodopa",
 
    # Reproductive / Hormonal
    "Medroxyprogesterone", "Norethindrone", "Estradiol",
    "Conjugated Estrogens", "Tamoxifen",
 
    # Skin
    "Mupirocin", "Ketoconazole", "Permethrin",
 
    # Other common
    "Epinephrine", "Nitroglycerin", "Naloxone", "Sumatriptan",
    "Zolpidem", "Modafinil", "Sildenafil", "Tamsulosin",
    "Finasteride", "Latanoprost", "Timolol",
]
 
 
def extract_drug_names_from_patients() -> set[str]:
    """Pull unique drug base names from the patient data file."""
    try:
        with open(PATIENT_DATA) as f:
            patients = json.load(f)
    except FileNotFoundError:
        logger.warning("Patient data not found at %s", PATIENT_DATA)
        return set()
 
    clean_names = set()
    for p in patients:
        for m in p.get("MedicationRequest", []):
            raw = m.get("medication", "")
            if not raw:
                continue
            base = re.split(r'\s+\d', raw)[0].strip()
            base = re.sub(r'\[.*?\]', '', base).strip()
            if len(base) >= 3 and not base.startswith("NDA"):
                clean_names.add(base)
 
    return clean_names
 
 
def fetch_drug_info(drug_name: str) -> dict | None:
    """Query MedlinePlus Connect API for a drug name."""
    params = {
        "mainSearchCriteria.v.cs": RXNORM_CS,
        "mainSearchCriteria.v.dn": drug_name,
        "knowledgeResponseType": "application/json",
    }
 
    try:
        resp = requests.get(CONNECT_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("API call failed for '%s': %s", drug_name, e)
        return None
 
    entries = data.get("feed", {}).get("entry", [])
    if not entries:
        logger.info("  No results for '%s'", drug_name)
        return None
 
    entry = entries[0]
    title = entry.get("title", {}).get("_value", drug_name)
    summary_html = entry.get("summary", {}).get("_value", "")
 
    summary_clean = ""
    if summary_html:
        soup = BeautifulSoup(summary_html, "html.parser")
        summary_clean = soup.get_text(separator=" ", strip=True)
 
    url = ""
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            url = link.get("href", "")
            break
 
    if not summary_clean:
        logger.info("  Empty summary for '%s'", drug_name)
        return None
 
    return {
        "drug_name": drug_name,
        "title": title,
        "summary": summary_clean,
        "url": url,
        "source": "MedlinePlus Drug Information",
    }
 
 
def save_drug_results(results: list[dict]) -> int:
    """Save each drug result as a separate JSON file."""
    DRUGS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 
    saved = 0
    for result in results:
        slug = re.sub(r'[^a-z0-9]+', '_', result["drug_name"].lower()).strip('_')
        path = DRUGS_OUTPUT_DIR / f"{slug}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        saved += 1
 
    return saved
 
 
def main():
    patient_drugs = extract_drug_names_from_patients()
    all_drugs = patient_drugs | set(COMMON_DRUGS)
 
    logger.info("Drug names from patient data: %d", len(patient_drugs))
    logger.info("Common drugs list: %d", len(COMMON_DRUGS))
    logger.info("Total unique drugs to fetch: %d", len(all_drugs))
    logger.info("")
 
    results = []
    seen_titles = set()
    failed = []
 
    for i, drug in enumerate(sorted(all_drugs), 1):
        logger.info("[%d/%d] Fetching: %s", i, len(all_drugs), drug)
        info = fetch_drug_info(drug)
 
        if info and info["title"] not in seen_titles:
            seen_titles.add(info["title"])
            results.append(info)
            logger.info("  -> %s (%d chars)", info["title"], len(info["summary"]))
        elif not info:
            failed.append(drug)
 
        time.sleep(0.8)
 
    saved = save_drug_results(results)
 
    print(f"\n{'='*60}")
    print(f"Results: {saved} drugs saved to {DRUGS_OUTPUT_DIR}")
    print(f"Failed/no results: {len(failed)}")
    if failed:
        print(f"Missing: {', '.join(failed[:20])}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
    print(f"{'='*60}")
 
 
if __name__ == "__main__":
    main()