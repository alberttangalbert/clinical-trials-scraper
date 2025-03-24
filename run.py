#!/usr/bin/env python3
import requests
import json
import sys

API_URL = "https://clinicaltrials.gov/api/v2/studies"
OUTPUT_FILE = "recent_clinical_trials.json"
PAGE_SIZE = 100  # number of trials to fetch

FAILED_STATUSES = {"TERMINATED", "SUSPENDED", "WITHDRAWN"}


def fetch_recent_trials(page_size: int = PAGE_SIZE) -> list:
    params = {
        "format": "json",
        "pageSize": page_size,
        "sort": "LastUpdatePostDate:desc"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    data = response.json().get("studies", [])
    enriched = []

    for study in data:
        ps = study.get("protocolSection", {})
        id_mod = ps.get("identificationModule", {})
        status_mod = ps.get("statusModule", {})
        sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
        design_mod = ps.get("designModule", {})
        outcomes_mod = ps.get("outcomesModule", {})
        elig_mod = ps.get("eligibilityModule", {})
        loc_mod = ps.get("contactsLocationsModule", {})

        enriched.append({
            "NCT ID": id_mod.get("nctId"),
            "Official Title": id_mod.get("officialTitle"),
            "Lead Sponsor": sponsor_mod.get("leadSponsor", {}).get("name"),
            "Collaborators": ", ".join(c.get("name") for c in sponsor_mod.get("collaborators", [])),
            "Overall Status": status_mod.get("overallStatus"),
            "Failed?": status_mod.get("overallStatus") in FAILED_STATUSES,
            "Brief Summary": ps.get("descriptionModule", {}).get("briefSummary"),
            "Detailed Description": ps.get("descriptionModule", {}).get("detailedDescription"),
            "Conditions": ", ".join(ps.get("conditionsModule", {}).get("conditions", [])),
            "Interventions": ", ".join(i.get("name") for i in ps.get("armsInterventionsModule", {}).get("interventions", [])),
            "Enrollment": design_mod.get("enrollmentInfo", {}).get("count"),
            "Primary Outcomes": "; ".join(o.get("measure") for o in outcomes_mod.get("primaryOutcomes", [])),
            "Secondary Outcomes": "; ".join(o.get("measure") for o in outcomes_mod.get("secondaryOutcomes", [])),
            "Min Age": elig_mod.get("minimumAge"),
            "Max Age": elig_mod.get("maximumAge"),
            "Sex Eligibility": elig_mod.get("sex"),
            "Accepts Healthy Volunteers": elig_mod.get("healthyVolunteers"),
            "Start Date": status_mod.get("startDateStruct", {}).get("date"),
            "Primary Completion Date": status_mod.get("primaryCompletionDateStruct", {}).get("date"),
            "Last Update Date": status_mod.get("lastUpdatePostDateStruct", {}).get("date"),
            "Study Type": design_mod.get("studyType"),
            "Phases": ", ".join(design_mod.get("phases", [])),
            "Locations": ", ".join(f"{loc.get('city', '')}, {loc.get('country', '')}" for loc in loc_mod.get("locations", []))
        })
    return enriched


def main():
    try:
        trials = fetch_recent_trials()
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(trials, f, indent=2)
        print(f"Retrieved metadata for {len(trials)} trials → saved to '{OUTPUT_FILE}'")
    except requests.HTTPError as http_err:
        print(f"HTTP error: {http_err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()