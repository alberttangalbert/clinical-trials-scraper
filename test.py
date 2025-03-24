import json

file_path = "recent_clinical_trials.json"

data = json.load(open(file_path))
print(f"Loaded {len(data)} trials")