#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements-security.txt

bandit -r . -f json -o bandit_report.json || true
safety check --json > safety_report.json || true
semgrep --config=auto --json -o semgrep_report.json . || true

python scripts/aggregate_security_reports.py
