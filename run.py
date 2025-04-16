#!/usr/bin/env python3
import requests
import json
import sys

API_URL = "https://clinicaltrials.gov/api/v2/studies"
OUTPUT_FILE = "all_clinical_trials.json"
PAGE_SIZE = 1000  # maximum trials per request
FAILED_STATUSES = {"TERMINATED", "SUSPENDED", "WITHDRAWN"}

def safe_join(iterable, sep=", "):
    # Convert items to strings and skip None values.
    return sep.join(str(item) for item in iterable if item is not None)

def fetch_all_trials(page_size: int = PAGE_SIZE) -> list:
    all_trials = []
    page_token = None  # initial request has no pageToken

    while True:
        params = {
            "format": "json",
            "pageSize": page_size,
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        studies = data.get("studies", [])
        if not studies:
            break

        for study in studies:
            ps = study.get("protocolSection", {})
            id_mod = ps.get("identificationModule", {})
            status_mod = ps.get("statusModule", {})
            sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
            design_mod = ps.get("designModule", {})
            outcomes_mod = ps.get("outcomesModule", {})
            elig_mod = ps.get("eligibilityModule", {})
            loc_mod = ps.get("contactsLocationsModule", {})
            oversight_mod = ps.get("oversightModule", {})
            adverse_mod = ps.get("adverseEventsModule", {})
            doc_mod = ps.get("documentSection", {})
            ipd_mod = ps.get("ipdSharingStatementModule", {})
            baseline_mod = ps.get("baselineCharacteristicsModule", {})

            trial = {
                "NCT ID": id_mod.get("nctId"),
                "Official Title": id_mod.get("officialTitle"),
                "Lead Sponsor": sponsor_mod.get("leadSponsor", {}).get("name"),
                "Collaborators": safe_join(c.get("name") for c in sponsor_mod.get("collaborators", [])),
                "Overall Status": status_mod.get("overallStatus"),
                "Failed?": status_mod.get("overallStatus") in FAILED_STATUSES,
                "Brief Summary": ps.get("descriptionModule", {}).get("briefSummary"),
                "Detailed Description": ps.get("descriptionModule", {}).get("detailedDescription"),
                "Conditions": safe_join(ps.get("conditionsModule", {}).get("conditions", [])),
                "Interventions": safe_join(i.get("name") for i in ps.get("armsInterventionsModule", {}).get("interventions", [])),
                "Enrollment": design_mod.get("enrollmentInfo", {}).get("count"),
                "Primary Outcomes": safe_join(o.get("measure") for o in outcomes_mod.get("primaryOutcomes", [])),
                "Secondary Outcomes": safe_join(o.get("measure") for o in outcomes_mod.get("secondaryOutcomes", [])),
                "Min Age": elig_mod.get("minimumAge"),
                "Max Age": elig_mod.get("maximumAge"),
                "Sex Eligibility": elig_mod.get("sex"),
                "Accepts Healthy Volunteers": elig_mod.get("healthyVolunteers"),
                "Start Date": status_mod.get("startDateStruct", {}).get("date"),
                "Primary Completion Date": status_mod.get("primaryCompletionDateStruct", {}).get("date"),
                "Last Update Date": status_mod.get("lastUpdatePostDateStruct", {}).get("date"),
                "Study Type": design_mod.get("studyType"),
                "Phases": safe_join(phase for phase in design_mod.get("phases", [])),
                "Locations": safe_join(
                    f"{loc.get('city') or ''}, {loc.get('country') or ''}"
                    for loc in loc_mod.get("locations", [])
                    if loc.get("city") or loc.get("country")
                ),
                # Additional hyperparameters
                "Randomization": design_mod.get("designInfo", {}).get("allocation"),
                "Masking": design_mod.get("designInfo", {}).get("maskingInfo", {}).get("masking"),
                "Intervention Model": design_mod.get("designInfo", {}).get("interventionModel"),
                "Primary Purpose": design_mod.get("designInfo", {}).get("primaryPurpose"),
                "Arms": safe_join(ag.get("label") for ag in ps.get("armsInterventionsModule", {}).get("armGroups", [])),
                "Adverse Events Summary": {
                    "Serious Events": adverse_mod.get("seriousEvents"),
                    "Other Events": adverse_mod.get("otherEvents"),
                },
                "Number of Sites": len(loc_mod.get("locations", [])),
                "FDA Regulated Drug": oversight_mod.get("isFdaRegulatedDrug"),
                "FDA Regulated Device": oversight_mod.get("isFdaRegulatedDevice"),
                "DSMB Present": oversight_mod.get("oversightHasDmc"),
                "Expanded Access": status_mod.get("expandedAccessInfo", {}).get("hasExpandedAccess"),
                "IPD Sharing": ipd_mod.get("ipdSharing"),
                "Protocol Documents": safe_join(
                    doc.get("filename") for doc in doc_mod.get("largeDocumentModule", {}).get("largeDocs", [])
                ),
                "Study First Submit Date": status_mod.get("studyFirstSubmitDate"),
                "Study First Post Date": status_mod.get("studyFirstPostDateStruct", {}).get("date"),
                "Results First Submit Date": status_mod.get("resultsFirstSubmitDate"),
                "Results First Post Date": status_mod.get("resultsFirstPostDateStruct", {}).get("date"),
                "Baseline Characteristics": baseline_mod  # raw capture of baseline demographics info
            }
            all_trials.append(trial)

        print(f"Fetched {len(studies)} trials. Next page token: {page_token}")
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_trials

def main():
    try:
        trials = fetch_all_trials()
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