import json
import re
import os

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Load banned phrases
banned_phrases_path = "banned_phrases.txt"
banned_phrases = [p.strip().lower() for p in open(banned_phrases_path).read().splitlines() if p.strip()]
print(f"Banned phrases: {banned_phrases}")

# Load business suffixes
business_suffixes_path = "business_suffixes.txt"
business_suffixes = [p.strip().lower() for p in open(business_suffixes_path).read().splitlines() if p.strip()]
print(f"Business suffixes: {business_suffixes}")

# Load unique company names and clean them
company_names = []
with open("unique_company_names.csv", "r") as f:
    # Skip header
    next(f)
    for line in f:
        # Remove quotes and clean up the name
        name = line.strip().strip('"')
        if name:  # Only add non-empty names
            company_names.append(name)

def clean_company_name(name):
    if not isinstance(name, str):
        return [""]
    
    cleaned_versions = []
    
    # Base cleaning: remove punctuation and normalize spaces
    base_cleaned = re.sub(r'[^\w\s]', '', name).strip()
    base_cleaned = re.sub(r'\s+', ' ', base_cleaned)
    
    # Check for acronym: only add last word if it is uppercase and is not a business suffix
    original_words = name.split()
    if original_words:
        last_word = original_words[-1]
        if last_word.isupper() and last_word.lower() not in business_suffixes:
            cleaned_versions.append(last_word)
    
    # Remove short words (1-3 characters) from the end
    words_base = base_cleaned.split()
    while words_base and len(words_base[-1]) <= 3:
        words_base.pop()
    base_cleaned = ' '.join(words_base).strip()

    # Remove business suffixes from the cleaned name (ignore case)
    suffix_pattern = r'\b(?:' + '|'.join(re.escape(suffix) for suffix in business_suffixes) + r')\b'
    base_cleaned = re.sub(suffix_pattern, '', base_cleaned, flags=re.IGNORECASE).strip()
    
    cleaned_versions.append(base_cleaned)
    
    # Additional cleaning if parentheses are present
    if '(' in name and ')' in name:
        without_parentheses = re.sub(r'\(.*$', '', name).strip()
        without_parentheses = re.sub(r'[^\w\s]', '', without_parentheses).strip()
        without_parentheses = re.sub(r'\s+', ' ', without_parentheses)
        without_parentheses = re.sub(suffix_pattern, '', without_parentheses, flags=re.IGNORECASE).strip()
        words_without = without_parentheses.split()
        while words_without and len(words_without[-1]) <= 3:
            words_without.pop()
        without_parentheses = ' '.join(words_without).strip()
        
        cleaned_versions.append(without_parentheses)
    
    # Remove duplicates and empty strings
    cleaned_versions = list(set(v.lower() for v in cleaned_versions if v))
    
    return cleaned_versions

# Clean all company names for comparison
cleaned_company_names = {}
for name in company_names:
    cleaned_versions = clean_company_name(name)
    for cleaned in cleaned_versions:
        if cleaned:  # Only add non-empty cleaned versions
            cleaned_company_names[cleaned] = name

with open("cleaned_company_names.json", "w") as f:
    json.dump(cleaned_company_names, f, indent=2)

# Load JSON data
try:
    file_path = "all_clinical_trials.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

lead_sponsors = set()
original_lead_sponsors_count = 0
after_banned_count = 0
identified_trials_count = 0

# Track which companies we've found and their trials
known_companies = {}
unknown_trials = []

for trial in data:
    try:
        original_lead_sponsors_count += 1
        
        # Safely get lead sponsor and collaborators
        lead_sponsor = trial.get("Lead Sponsor", "")
        collaborators_str = trial.get("Collaborators", "")
        collaborators = [c.strip() for c in collaborators_str.split(",") if c.strip()]

        # Skip if lead sponsor is banned
        if any(bp in lead_sponsor.lower() for bp in banned_phrases):
            continue

        after_banned_count += 1
        trial_identified = False
        matched_companies = set()

        # Check if lead sponsor matches any company name
        cleaned_lead_versions = clean_company_name(lead_sponsor)
        for cleaned_lead in cleaned_lead_versions:
            if cleaned_lead in cleaned_company_names:
                matched_companies.add(cleaned_company_names[cleaned_lead])
                trial_identified = True
                break

        # Check collaborators
        for collab in collaborators:
            cleaned_collab_versions = clean_company_name(collab)
            for cleaned_collab in cleaned_collab_versions:
                if cleaned_collab in cleaned_company_names:
                    matched_companies.add(cleaned_company_names[cleaned_collab])
                    trial_identified = True
                    break
            if trial_identified:
                break

        if trial_identified:
            identified_trials_count += 1
            # Add trial to each matched company
            for company in matched_companies:
                if company not in known_companies:
                    known_companies[company] = {
                        "trial_count": 0,
                        "trials": []
                    }
                known_companies[company]["trial_count"] += 1
                known_companies[company]["trials"].append(trial)
        else:
            unknown_trials.append(trial)

        if not collaborators:
            lead_sponsors.add((lead_sponsor, ""))
        else:
            # Only add if at least one collaborator is not banned
            if any(not any(bp in c.lower() for bp in banned_phrases) for c in collaborators):
                lead_sponsors.add((lead_sponsor, ", ".join(collaborators)))
    except Exception as e:
        print(f"Error processing trial: {e}")
        continue

# Write known companies to JSON file
try:
    with open("output/known_companies.json", "w") as f:
        json.dump(known_companies, f, indent=2)
except Exception as e:
    print(f"Error writing known_companies.json: {e}")

# Write unknown companies to file
unknown_companies = [name for name in company_names if name not in known_companies]
try:
    with open("output/unknown_companies.txt", "w") as f:
        for company in sorted(unknown_companies):
            cleaned_versions = clean_company_name(company)
            f.write(f"{company} | {', '.join(cleaned_versions)}\n")
except Exception as e:
    print(f"Error writing unknown_companies.txt: {e}")

# Write all company names and their cleaned versions
try:
    with open("output/company_name_cleaning.txt", "w") as f:
        for company in sorted(company_names):
            cleaned_versions = clean_company_name(company)
            f.write(f"{company} | {', '.join(cleaned_versions)}\n")
except Exception as e:
    print(f"Error writing company_name_cleaning.txt: {e}")

# Write unknown trials to file
try:
    with open("output/unknown_trials.json", "w") as f:
        json.dump(unknown_trials, f, indent=2)
except Exception as e:
    print(f"Error writing unknown_trials.json: {e}")

# Write lead sponsors to file
try:
    with open("output/lead_sponsors.txt", "w") as f:
        for i, (sponsor, collabs) in enumerate(sorted(lead_sponsors), 1):
            f.write(f"{i}. {sponsor} | {collabs}\n")
except Exception as e:
    print(f"Error writing lead_sponsors.txt: {e}")

# Print statistics
print(f"Original number of lead sponsors: {original_lead_sponsors_count}")
print(f"After filtering by banned words: {after_banned_count}")
print(f"Number of unique company names: {len(company_names)}")
print(f"Number of identified trials: {identified_trials_count}")
print(f"Number of unknown trials: {len(unknown_trials)}")
print(f"Number of known companies: {len(known_companies)}")
print(f"Number of unknown companies: {len(unknown_companies)}")