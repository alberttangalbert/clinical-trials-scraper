from dotenv import load_dotenv
load_dotenv()

import json
import pandas as pd
import datetime
import re
from typing import Dict, Any, List

from app.services.bing_search import search_bing
from app.services.scrape_webpage import scrape_and_parse_webpage, get_cached_drug_info

# Define the elements we want to extract (using data-testid attributes)
TARGET_ELEMENTS = [
    "descriptions-item__value--drugType",
    "descriptions-item__value--synonyms",
    "descriptions-item__value--target",
    "descriptions-item__value--action",
    "descriptions-item__value--mechanism",
    "descriptions-item__value--therapeutic",
    "descriptions-item__value--activeDisease",
    "descriptions-item__value--inActiveDisease",
    "descriptions-item__value--originOrg",
    "descriptions-item__value--activeOrg"
]

# ---- Helper functions for one-hot encoding and processing ----

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

def count_collaborators(collaborators: str) -> int:
    """
    Count the number of collaborators by splitting the string on commas.
    Returns 0 if collaborators is None or empty.
    """
    if not collaborators:
        return 0
    collaborator_list = [c.strip() for c in collaborators.split(",") if c.strip()]
    return len(collaborator_list)

def scrape_drug_info(drug_name: str) -> Dict[str, str]:
    """
    Scrape drug information from PatSnap using Bing search, with caching.
    """
    print(f"\n[DEBUG] Scraping drug info for: {drug_name}")
    
    # Clean the drug name for caching
    clean_name = re.sub(r"[^\w\-]", "", drug_name.split()[0].split(",")[0])
    
    # Check cache first
    cached_info = get_cached_drug_info(clean_name)
    if cached_info:
        return cached_info
    
    # Search PatSnap via Bing
    domain = "synapse.patsnap.com"
    results = search_bing(drug_name, domain)
    print(f"[DEBUG] Bing search results: {results}")
    
    # Look for the first Synapse drug page
    for page in results.get('webPages', {}).get('value', []):
        url = page.get('url', '')
        if 'synapse.patsnap.com/drug' in url:
            print(f"[DEBUG] Found drug page URL: {url}")
            content = scrape_and_parse_webpage(url, TARGET_ELEMENTS, clean_name)
            print(f"[DEBUG] Extracted content: {content}")
            return content

    print("[DEBUG] No drug page found")
    return {}

def process_company(company_name: str, trials: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process all trials for a single company and return a DataFrame.
    """
    print(f"\n[DEBUG] Processing company: {company_name} ({len(trials)} trials)")
    rows = []
    
    for i, trial in enumerate(trials, start=1):
        drug_name = trial.get("Interventions", "")
        trial_id  = trial.get("NCT ID", "")
        print(f"[DEBUG] Trial {i}: {drug_name} ({trial_id})")
        
        # Scrape or fetch from cache
        if drug_name:
            cleaned = re.sub(r"[^\w\-]", "", drug_name.split()[0].split(",")[0])
            drug_info = scrape_drug_info(f"{cleaned} {trial_id}")
        else:
            drug_info = {}
        
        # Encodings and counts
        study_enc = one_hot_study_type(trial.get("Study Type", ""))
        phase_enc = one_hot_phases(trial.get("Phases", ""))
        arm_num   = arms_count(trial.get("Arms", ""))

        # Build output row
        row = {
            "nct_id": trial_id,
            "company_name": company_name,
            "drug_name": drug_name,
            **{key.split("--")[-1]: drug_info.get(key, "") for key in TARGET_ELEMENTS},
            "study_type_interventional": study_enc["Interventional"],
            "study_type_observational":  study_enc["Observational"],
            "phase": phase_enc,
            "arms_count": arm_num,
            "number_of_sites": trial.get("Number of Sites"),
            "enrollment": trial.get("Enrollment"),
            "overall_status": trial.get("Overall Status", ""),
            "failed?": trial.get("Failed?", False),
            "accepts_healthy_volunteers": one_hot_bool(trial.get("Accepts Healthy Volunteers", False)),
            "number_of_collaborators": count_collaborators(trial.get("Collaborators", "")),
            # ... include any additional trial fields you need ...
        }
        rows.append(row)
        print(f"[DEBUG] Finished trial {i}")

    df = pd.DataFrame(rows)
    print(f"[DEBUG] Built DataFrame: {df.shape} rows")
    return df

if __name__ == "__main__":
    print("\n[DEBUG] Starting main script")
    
    # Load companies JSON
    with open("output/known_companies.json") as f:
        companies_data = json.load(f)
    print(f"[DEBUG] Found {len(companies_data)} companies")

    # Prepare or load master CSV
    out_csv = "output/all_trials.csv"
    try:
        all_df = pd.read_csv(out_csv)
        print(f"[DEBUG] Loaded existing CSV ({all_df.shape[0]} rows)")
    except FileNotFoundError:
        all_df = pd.DataFrame()
        print("[DEBUG] No existing CSV, creating new one")

    # Process each company
    for company, info in companies_data.items():
        trials = info.get("trials", [])
        comp_df = process_company(company, trials)
        all_df = pd.concat([all_df, comp_df], ignore_index=True)
        all_df.to_csv(out_csv, index=False)
        print(f"[DEBUG] Saved {comp_df.shape[0]} trials for {company}")

    print(f"[DEBUG] Completed. Total trials: {all_df.shape[0]}")