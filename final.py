from dotenv import load_dotenv

load_dotenv()

import json
import pandas as pd
import datetime
from typing import Dict, Any, List
from app.core.modality_classifier import get_modality_areas_from_description
from app.core.indication_classifier import get_indication_areas_from_description
from app.core.outcome_classifier import get_outcome_areas_from_description
from app.core.primary_purpose_classifier import get_primary_purpose_areas_from_description

# ---- Helper functions for one-hot encoding and processing ----
def encode_outcomes(text: str, company_name: str, azure_service, outcome_areas: List[str]) -> Dict[str, int]:
    """
    One-hot encode outcomes categories from text using the outcome classifier.
    Categories: Clinical Outcomes, Surrogate Outcomes, Composite Outcomes, Patient-Reported Outcomes,
                Pharmacokinetic/Pharmacodynamic Outcomes, Safety/Tolerability Outcomes.
    """
    print(f"\n[DEBUG] Encoding outcomes for company: {company_name}")
    print(f"[DEBUG] Input text length: {len(text)} characters")
    
    categories = ["Clinical Outcomes", "Surrogate Outcomes", "Composite Outcomes",
                 "Patient-Reported Outcomes", "Pharmacokinetic/Pharmacodynamic Outcomes",
                 "Safety/Tolerability Outcomes"]
    
    # Get the outcome areas using the classifier
    print("[DEBUG] Calling outcome classifier...")
    outcome_areas_found = get_outcome_areas_from_description(
        text, company_name, azure_service, outcome_areas
    )
    print(f"[DEBUG] Found outcome areas: {outcome_areas_found}")
    
    # Create one-hot encoding based on found outcome areas with case-insensitive comparison
    result = {cat: 1 if cat.lower() in [area.lower() for area in outcome_areas_found] else 0 for cat in categories}
    print(f"[DEBUG] One-hot encoding result: {result}")
    return result

def encode_primary_purpose(purpose: str, company_name: str, azure_service, primary_purpose_areas: List[str]) -> Dict[str, int]:
    """
    One-hot encode primary purpose using the primary purpose classifier.
    Categories: Treatment, Prevention, Diagnostic, Supportive Care, Screening,
               Health Services Research, Basic Science, Other
    """
    print(f"\n[DEBUG] Encoding primary purpose for company: {company_name}")
    print(f"[DEBUG] Input purpose length: {len(purpose)} characters")
    
    categories = ["Treatment", "Prevention", "Diagnostic", "Supportive Care", 
                 "Screening", "Health Services Research", "Basic Science", "Other"]
    
    # Get the primary purpose areas using the classifier
    print("[DEBUG] Calling primary purpose classifier...")
    purpose_areas_found = get_primary_purpose_areas_from_description(
        purpose, company_name, azure_service, primary_purpose_areas
    )
    print(f"[DEBUG] Found primary purpose areas: {purpose_areas_found}")
    
    # Create one-hot encoding based on found purpose areas with case-insensitive comparison
    result = {cat: 1 if cat.lower() in [area.lower() for area in purpose_areas_found] else 0 for cat in categories}
    print(f"[DEBUG] One-hot encoding result: {result}")
    return result

def one_hot_phases(phases: str) -> Dict[str, int]:
    """
    One-hot encode phase information. If multiple phases are listed (e.g., "PHASE1, PHASE2"),
    both get a 1.
    """
    print(f"\n[DEBUG] Encoding phases: {phases}")
    phases = phases.upper().replace(" ", "")
    mapping = {"Phase 1": 0, "Phase 2": 0, "Phase 3": 0}
    if "PHASE1" in phases:
        mapping["Phase 1"] = 1
    if "PHASE2" in phases:
        mapping["Phase 2"] = 1
    if "PHASE3" in phases:
        mapping["Phase 3"] = 1
    print(f"[DEBUG] Phase encoding result: {mapping}")
    return mapping

def one_hot_study_type(study_type: str) -> Dict[str, int]:
    """
    One-hot encode study type into 'Interventional' or 'Observational'.
    """
    print(f"\n[DEBUG] Encoding study type: {study_type}")
    mapping = {"Interventional": 0, "Observational": 0}
    stype = study_type.lower()
    if "intervention" in stype:
        mapping["Interventional"] = 1
    elif "observat" in stype:
        mapping["Observational"] = 1
    else:
        mapping["Interventional"] = 1
    print(f"[DEBUG] Study type encoding result: {mapping}")
    return mapping

def arms_count(arms: str) -> int:
    """
    Split the arms string by comma and count the number of arms.
    """
    print(f"\n[DEBUG] Counting arms: {arms}")
    if arms:
        count = len([arm.strip() for arm in arms.split(",") if arm.strip()])
        print(f"[DEBUG] Found {count} arms")
        return count
    print("[DEBUG] No arms found")
    return 0

def one_hot_bool(value: bool) -> int:
    result = 1 if value else 0
    print(f"[DEBUG] Boolean encoding: {value} -> {result}")
    return result

# ---- Main processing function for a company ----
def process_company(company_name: str, trials: List[Dict[str, Any]],
                    azure_service, modality_list: List[str], indication_list: List[str],
                    outcome_areas: List[str], primary_purpose_areas: List[str]) -> pd.DataFrame:
    print(f"\n[DEBUG] Processing company: {company_name}")
    print(f"[DEBUG] Number of trials to process: {len(trials)}")
    
    rows = []
    for i, trial in enumerate(trials, 1):
        print(f"\n[DEBUG] Processing trial {i}/{len(trials)}")
        
        # Join Detailed Description and Brief Summary for modality and indication classification
        description = ""
        if trial.get("Detailed Description"):
            description += trial["Detailed Description"]
        if trial.get("Brief Summary"):
            description += " " + trial["Brief Summary"]
        print(f"[DEBUG] Combined description length: {len(description)} characters")
            
        print("[DEBUG] Classifying modality...")
        modalities = get_modality_areas_from_description(description, azure_service, modality_list)
        print(f"[DEBUG] Found modalities: {modalities}")
        
        print("[DEBUG] Classifying indications...")
        indications = get_indication_areas_from_description(description, azure_service, indication_list)
        print(f"[DEBUG] Found indications: {indications}")
        
        # Process outcomes one-hot using the new classifier
        print("[DEBUG] Processing primary outcomes...")
        primary_outcomes_encoding = encode_outcomes(
            trial.get("Primary Outcomes", ""), 
            company_name, 
            azure_service, 
            outcome_areas
        )
        
        print("[DEBUG] Processing secondary outcomes...")
        secondary_outcomes_encoding = encode_outcomes(
            trial.get("Secondary Outcomes", ""), 
            company_name, 
            azure_service, 
            outcome_areas
        )
        
        # One-hot encode study type and phases
        print("[DEBUG] Encoding study type...")
        study_type_encoding = one_hot_study_type(trial.get("Study Type", ""))
        
        print("[DEBUG] Encoding phases...")
        phase_encoding = one_hot_phases(trial.get("Phases", ""))
        
        # Encode primary purpose using the new classifier
        print("[DEBUG] Processing primary purpose...")
        primary_purpose_encoding = encode_primary_purpose(
            trial.get("Primary Purpose", ""), 
            company_name, 
            azure_service, 
            primary_purpose_areas
        )
        
        # Count arms
        print("[DEBUG] Counting arms...")
        arms_num = arms_count(trial.get("Arms", ""))
        
        # Build row data
        print("[DEBUG] Building row data...")
        row = {
            "modality": modalities,
            "indications": indications,
            "phase": phase_encoding,
            "sponsor_name": company_name,
            "failed?": trial.get("Failed?", False),
            "enrollment": trial.get("Enrollment", None),
            "overall_status": trial.get("Overall Status", ""),
            "disease/condition": trial.get("Conditions", ""),
            "accepts_healthy_volunteers": trial.get("Accepts Healthy Volunteers", False),
            "primary_outcomes": trial.get("Primary Outcomes", ""),
            "min_age": trial.get("Min Age", ""),
            "max_age": trial.get("Max Age", ""),
            "start_date": trial.get("Start Date", ""),
            "Primary Completion Date": trial.get("Primary Completion Date", ""),
            "Last Update Date": trial.get("Last Update Date", ""),
            "study_type_interventional": study_type_encoding["Interventional"],
            "study_type_observational": study_type_encoding["Observational"],
            "arms_count": arms_num,
            "number_of_sites": trial.get("Number of Sites", None),
            "FDA_Regulated_Drug": one_hot_bool(trial.get("FDA Regulated Drug", False)),
            "FDA_Regulated_Device": one_hot_bool(trial.get("FDA Regulated Device", False)),
            **{f"primary_outcome_{k.replace(' ', '_').lower()}": v for k, v in primary_outcomes_encoding.items()},
            **{f"secondary_outcome_{k.replace(' ', '_').lower()}": v for k, v in secondary_outcomes_encoding.items()},
            **{f"primary_purpose_{k.replace(' ', '_').lower()}": v for k, v in primary_purpose_encoding.items()},
        }
        rows.append(row)
        print(f"[DEBUG] Completed processing trial {i}")
    
    print(f"\n[DEBUG] Creating DataFrame for {company_name}")
    df = pd.DataFrame(rows)
    print(f"[DEBUG] DataFrame shape: {df.shape}")
    return df

# ---- Main script execution ----
if __name__ == "__main__":
    print("\n[DEBUG] Starting main script execution")
    
    # Load the JSON file
    print("[DEBUG] Loading companies data from JSON...")
    with open("output/known_companies.json", "r") as f:
        companies_data = json.load(f)
    print(f"[DEBUG] Loaded data for {len(companies_data)} companies")
        
    # Initialize Azure OpenAI service
    print("[DEBUG] Initializing Azure OpenAI service...")
    from app.services.azure.azure_openai_service import AzureOpenaiService
    azure_service = AzureOpenaiService()
    
    # Define lists
    print("[DEBUG] Setting up classification lists...")
    modality_list = ["Protein/Monoclonal Antibodies", "Small molecules", "Cell therapy", "Gene therapy"]
    indication_list = ["Oncology", "Autoimmune", "Infectious Diseases", "Cardiovascular", "COVID-19"]
    outcome_areas = ["Clinical Outcomes", "Surrogate Outcomes", "Composite Outcomes",
                    "Patient-Reported Outcomes", "Pharmacokinetic/Pharmacodynamic Outcomes",
                    "Safety/Tolerability Outcomes"]
    primary_purpose_areas = ["Treatment", "Prevention", "Diagnostic", "Supportive Care",
                           "Screening", "Health Services Research", "Basic Science", "Other"]
    
    # Process each company
    print("\n[DEBUG] Starting company processing loop")
    for company_name, company_info in companies_data.items():
        print(f"\n[DEBUG] Processing company: {company_name}")
        trials = company_info.get("trials", [])
        print(f"[DEBUG] Found {len(trials)} trials for {company_name}")
        
        df = process_company(company_name, trials, azure_service, modality_list, indication_list,
                           outcome_areas, primary_purpose_areas)
        
        # Save dataframe to CSV
        csv_filename = f"output/{company_name.replace(' ', '_')}_trials.csv"
        print(f"[DEBUG] Saving DataFrame to {csv_filename}")
        df.to_csv(csv_filename, index=False)
        print(f"[DEBUG] Saved {company_name} trials to {csv_filename}")
    
    print("\n[DEBUG] Script execution completed")
