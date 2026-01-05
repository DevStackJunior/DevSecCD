import json, os
from datetime import datetime

results = {
    "scan_date": datetime.now().isoformat(),
    "repository": os.environ.get("GITHUB_REPOSITORY", "unknown"),
    "bandit": {},
    "safety": {},
    "semgrep": {}
}

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

results["bandit"] = load_json("bandit_report.json")
results["safety"] = load_json("safety_report.json")
results["semgrep"] = load_json("semgrep_report.json")

with open("security_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("✅ Rapport agrégé créé: security_report.json")
