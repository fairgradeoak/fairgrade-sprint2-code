# for importing
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Prints the languages your Judge0 supports (id and name) and saves them to results/languages.csv.
# The ids are what the question's `language_id` field and the UI's language dropdown use.
# Needs Judge0 running. Run it from the project root: python scripts/list_languages.py
import csv

from fairgrade import judge0_client
sys.stdout.reconfigure(encoding="utf-8")

endpoint, headers = judge0_client.settings()
languages = judge0_client.request("listing the languages", "GET", f"{endpoint}/languages", headers, 10)

results_dir = root / "results"
results_dir.mkdir(parents=True, exist_ok=True)
output_file = results_dir / "languages.csv"
with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "name"])
    for language in sorted(languages, key=lambda item: item["id"]):
        writer.writerow([language["id"], language["name"]])
        print(f"{language['id']:>4}  {language['name']}")

print(f"\n{len(languages)} languages, saved to {output_file}")
