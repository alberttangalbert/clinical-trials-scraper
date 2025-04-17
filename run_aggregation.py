import json
import re
import os
from collections import defaultdict

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Load banned phrases
banned_phrases_path = "resources/banned_phrases.txt"
banned_phrases = [p.strip().lower() for p in open(banned_phrases_path).read().splitlines() if p.strip()]
print(f"Banned phrases: {banned_phrases}")

# Load business suffixes (only true suffixes like Inc, Ltd, AG, GmbH)
business_suffixes_path = "resources/business_suffixes.txt"
business_suffixes = [p.strip().lower() for p in open(business_suffixes_path).read().splitlines() if p.strip()]
print(f"Business suffixes: {business_suffixes}")

# Load unique company names and clean them
company_names = []
with open("resources/unique_company_names.csv", "r") as f:
    next(f)  # Skip header
    for line in f:
        name = line.strip().strip('"')
        if name:
            company_names.append(name)

# Cleaning function
def clean_company_name(name):
    if not isinstance(name, str):
        return []
    # Base cleaning: remove punctuation and normalize spaces
    cleaned = re.sub(r'[\(\)\.,;:\-]', ' ', name)
    cleaned = re.sub(r'[^\w\s]', '', cleaned).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned).lower()
    # Remove known suffixes
    suffix_pattern = r'\b(?:' + '|'.join(re.escape(s) for s in business_suffixes) + r')\b'
    cleaned = re.sub(suffix_pattern, '', cleaned).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return [cleaned] if cleaned else []

# Build multi-map to detect collisions
temp_map = defaultdict(list)
for orig in company_names:
    for cleaned in clean_company_name(orig):
        temp_map[cleaned].append(orig)

# Report collisions
for key, vals in temp_map.items():
    if len(vals) > 1:
        print(f"Collision for key '{key}': {vals}")

# Keep only unique mappings
cleaned_company_names = {k: v for k, v in temp_map.items() if len(v) == 1}

# Save cleaned mappings for reference
with open("output/cleaned_company_names.json", "w") as f:
    json.dump({k: v[0] for k, v in cleaned_company_names.items()}, f, indent=2)

# Load JSON data
try:
    with open("output/all_clinical_trials.json", 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

known_companies = {}
unknown_trials = []
lead_sponsors = set()

for trial in data:
    lead = trial.get("Lead Sponsor", "").strip()
    collabs = [c.strip() for c in trial.get("Collaborators", "").split(",") if c.strip()]
    # Skip banned
    if any(bp in lead.lower() for bp in banned_phrases):
        continue
    matched = set()
    # Match lead
    for cl in clean_company_name(lead):
        if cl in cleaned_company_names:
            matched.add(cleaned_company_names[cl][0])
            break
        elif cl in temp_map and len(temp_map[cl]) > 1:
            print(f"Ambiguous lead match '{lead}' → candidates {temp_map[cl]}")
    # Match collaborators
    for coll in collabs:
        for cl in clean_company_name(coll):
            if cl in cleaned_company_names:
                matched.add(cleaned_company_names[cl][0])
                break
            elif cl in temp_map and len(temp_map[cl]) > 1:
                print(f"Ambiguous collaborator match '{coll}' → {temp_map[cl]}")
        if matched:
            break
    if matched:
        for comp in matched:
            known_companies.setdefault(comp, {"trial_count": 0, "trials": []})
            known_companies[comp]["trial_count"] += 1
            known_companies[comp]["trials"].append(trial)
    else:
        unknown_trials.append(trial)
    # Record lead sponsors list
    if not collabs or any(bp not in c.lower() for c in collabs for bp in banned_phrases):
        lead_sponsors.add((lead, ", ".join(collabs)))

# Write outputs
with open("output/known_companies.json", "w") as f:
    json.dump(known_companies, f, indent=2)

with open("output/unknown_trials.json", "w") as f:
    json.dump(unknown_trials, f, indent=2)

with open("output/lead_sponsors.txt", "w") as f:
    for i, (s, c) in enumerate(sorted(lead_sponsors), 1):
        f.write(f"{i}. {s} | {c}\n")

print(f"Identified trials: {sum(v['trial_count'] for v in known_companies.values())}")
print(f"Unknown trials: {len(unknown_trials)}")
print("Number of known companies:", len(known_companies))
print("Number of unknown company names:", len(company_names) - len(known_companies))