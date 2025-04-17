import json
import re
import os
from collections import defaultdict

# -----------------------------------------------------------------------------
# Setup: make sure output directory exists
# -----------------------------------------------------------------------------
os.makedirs("output", exist_ok=True)

# -----------------------------------------------------------------------------
# Load banned phrases (we’ll skip any lead/collaborator containing these)
# -----------------------------------------------------------------------------
banned_phrases_path = "resources/banned_phrases.txt"
banned_phrases = [
    p.strip().lower()
    for p in open(banned_phrases_path).read().splitlines()
    if p.strip()
]
print(f"Banned phrases: {banned_phrases}")

# -----------------------------------------------------------------------------
# Load business suffixes (true legal suffixes to strip off, like Inc, Ltd, AG)
# -----------------------------------------------------------------------------
business_suffixes_path = "resources/business_suffixes.txt"
business_suffixes = [
    p.strip().lower()
    for p in open(business_suffixes_path).read().splitlines()
    if p.strip()
]
print(f"Business suffixes: {business_suffixes}")

# -----------------------------------------------------------------------------
# Read in the raw company names from your CSV
# -----------------------------------------------------------------------------
company_names = []
with open("resources/unique_company_names.csv", "r") as f:
    next(f)  # skip header
    for line in f:
        name = line.strip().strip('"')
        if name:
            company_names.append(name)

# -----------------------------------------------------------------------------
# Cleaning function: returns a single normalized string key for each company
# -----------------------------------------------------------------------------
def clean_company_name(name):
    """
    Turn a raw company name into a cleaned, lowercase key:
      1) Drop any '(' … ')' and everything after
      2) Strip punctuation
      3) Lowercase + trim
      4) Remove known suffixes (Inc, LLC, AG, GmbH, etc.)
      5) Collapse extra spaces
    """
    if not isinstance(name, str):
        return ""

    # 1) Remove parentheses and everything after
    #    e.g. "Acme Corp (USA) GmbH" → "Acme Corp "
    name = re.sub(r'\([^)]*\).*$', '', name)

    # 2) Remove common punctuation characters
    cleaned = re.sub(r'[\.,;:\-]', '', name)

    # 3) Strip anything that’s not a letter/number/underscore/space
    cleaned = re.sub(r'[^\w\s]', '', cleaned)

    # 4) Lowercase and trim whitespace
    cleaned = cleaned.strip().lower()

    # 5) Remove any of the known suffix words
    #    (case-insensitive thanks to re.IGNORECASE flag)
    suffix_pattern = r'\b(?:' + '|'.join(re.escape(s) for s in business_suffixes) + r')\b'
    cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.IGNORECASE).strip()

    # 6) Collapse any run of spaces down to a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned

# -----------------------------------------------------------------------------
# Build a temporary map from cleaned key → list of raw names
# This lets us detect collisions (multiple raw names mapping to same key)
# -----------------------------------------------------------------------------
temp_map = defaultdict(list)
for raw in company_names:
    key = clean_company_name(raw)
    if key:  # skip empty keys
        temp_map[key].append(raw)

# -----------------------------------------------------------------------------
# Build final mapping of unique cleaned key → single raw name
# (only keep keys that map to exactly one raw name)
# -----------------------------------------------------------------------------
unique_cleaned_map = {
    key: originals[0]
    for key, originals in temp_map.items()
    if len(originals) == 1
}

# Save that cleaned → raw mapping for reference
with open("output/cleaned_company_names.json", "w") as f:
    json.dump(unique_cleaned_map, f, indent=2)

# -----------------------------------------------------------------------------
# Load your clinical trials data
# -----------------------------------------------------------------------------
try:
    with open("output/all_clinical_trials.json", 'r') as f:
        trials_data = json.load(f)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

# Prepare containers for matched companies and unknown trials
known_companies = {}   # cleaned_key → { trial_count, trials: [...] }
unknown_trials = []    # trials we couldn’t match to any company
lead_sponsors = set()  # to record unique (lead, collaborators) pairs

# -----------------------------------------------------------------------------
# Iterate through each trial, try to match lead sponsor or collaborators
# -----------------------------------------------------------------------------
for trial in trials_data:
    lead_raw = trial.get("Lead Sponsor", "").strip()
    collab_list = [
        c.strip() for c in trial.get("Collaborators", "").split(",") if c.strip()
    ]

    # Skip trial entirely if lead contains a banned phrase
    if any(bp in lead_raw.lower() for bp in banned_phrases):
        continue

    matched = set()

    # --- Attempt to match the lead sponsor ---
    lead_key = clean_company_name(lead_raw)
    if lead_key in unique_cleaned_map:
        matched.add(unique_cleaned_map[lead_key])

    # --- If no lead match, try collaborators ---
    if not matched:
        for collab_raw in collab_list:
            collab_key = clean_company_name(collab_raw)
            if collab_key in unique_cleaned_map:
                matched.add(unique_cleaned_map[collab_key])
                break

    # --- Record matched trials or unknowns ---
    if matched:
        for company in matched:
            entry = known_companies.setdefault(company, {"trial_count": 0, "trials": []})
            entry["trial_count"] += 1
            entry["trials"].append(trial)
    else:
        unknown_trials.append(trial)

    # --- Track the raw lead/collab pairing for reporting ---
    if not collab_list or not any(bp in c.lower() for c in collab_list for bp in banned_phrases):
        lead_sponsors.add((lead_raw, ", ".join(collab_list)))

# -----------------------------------------------------------------------------
# Write out the results
# -----------------------------------------------------------------------------
with open("output/known_companies.json", "w") as f:
    json.dump(known_companies, f, indent=2)

with open("output/unknown_trials.json", "w") as f:
    json.dump(unknown_trials, f, indent=2)

with open("output/lead_sponsors.txt", "w") as f:
    for i, (lead, collab_str) in enumerate(sorted(lead_sponsors), 1):
        f.write(f"{i}. {lead} | {collab_str}\n")

# Final summary
total_matched = sum(v["trial_count"] for v in known_companies.values())
print(f"Identified trials: {total_matched}")
print(f"Unknown trials: {len(unknown_trials)}")
print(f"Number of known companies: {len(known_companies)}")
print(f"Number of unknown company names: {len(company_names) - len(known_companies)}")