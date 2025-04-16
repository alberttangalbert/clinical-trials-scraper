n_id = "NCT03510546"
import json
all_clinical_trials = []
with open("all_clinical_trials.json", "r") as f:
    all_clinical_trials = json.load(f)

for trial in all_clinical_trials:
    if trial["NCT ID"] == n_id:
        print(trial)
        break