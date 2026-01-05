#!/usr/bin/env python3
import os
import sys
import json
import yaml
import shutil
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.yaml"
STATEMENTS_DIR = ROOT / "statements"
ANALYSIS_DIR = ROOT / "analysis"

def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout.strip()

def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def extract_basic_fields(text: str):
    """Very lightweight heuristics. You can improve these later."""
    lower = text.lower()

    # emails (simple heuristic)
    import re
    emails = sorted(set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.I)))

    # urls
    urls = sorted(set(re.findall(r"https?://[^\s)>\]]+", text)))

    # keywords (presence checks)
    has_safe_harbor = any(k in lower for k in ["safe harbor", "safeharbor"])
    has_disclosure = any(k in lower for k in ["coordinated disclosure", "responsible disclosure", "vulnerability disclosure", "cvd"])
    mentions_sla = any(k in lower for k in ["within", "business day", "days", "hours", "timeline", "sla", "respond", "response time"])
    mentions_scope = "in scope" in lower or "out of scope" in lower or "scope" in lower

    return {
        "emails": emails,
        "urls": urls,
        "signals": {
            "safe_harbor_mentioned": has_safe_harbor,
            "disclosure_process_mentioned": has_disclosure,
            "sla_or_timeline_mentioned": mentions_sla,
            "scope_mentioned": mentions_scope,
        }
    }

def normalize_sections(text: str):
    """
    Minimal normalization:
    - keep raw
    - try to split into sections by Markdown headings
    """
    lines = text.splitlines()
    sections = []
    current = {"title": "ROOT", "content": []}

    for line in lines:
        if line.startswith("#"):
            # flush previous
            if current["content"]:
                sections.append({
                    "title": current["title"],
                    "content": "\n".join(current["content"]).strip()
                })
            # new heading
            title = line.lstrip("#").strip()
            current = {"title": title if title else "UNTITLED", "content": []}
        else:
            current["content"].append(line)

    if current["content"]:
        sections.append({
            "title": current["title"],
            "content": "\n".join(current["content"]).strip()
        })

    # crude mapping to canonical buckets
    canonical = {
        "contact": [],
        "reporting": [],
        "scope": [],
        "disclosure_policy": [],
        "sla": [],
        "other": []
    }

    for s in sections:
        t = s["title"].lower()
        c = s["content"]
        if any(k in t for k in ["contact", "email", "pgp", "key"]):
            canonical["contact"].append(s)
        elif any(k in t for k in ["report", "reporting", "vulnerab", "security issue", "how to"]):
            canonical["reporting"].append(s)
        elif "scope" in t or "in scope" in t or "out of scope" in t:
            canonical["scope"].append(s)
        elif any(k in t for k in ["disclosure", "policy", "coordinated", "responsible"]):
            canonical["disclosure_policy"].append(s)
        elif any(k in t for k in ["timeline", "sla", "response", "timeframe"]):
            canonical["sla"].append(s)
        else:
            canonical["other"].append(s)

    return canonical

def ingest_one(source, tmp_base: Path):
    name = source["name"]
    repo = source["repo"]
    ref = (source.get("ref") or "").strip()
    paths = source.get("statement_paths") or []

    repo_dir = tmp_base / name
    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    # shallow clone
    run(["git", "clone", "--depth", "1", repo, str(repo_dir)])
    if ref:
        # If ref is a tag/branch/commit, fetch it shallowly
        run(["git", "fetch", "--depth", "1", "origin", ref], cwd=repo_dir)
        run(["git", "checkout", ref], cwd=repo_dir)

    commit = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
    fetched_at = datetime.now(timezone.utc).isoformat()

    found_any = False
    for relpath in paths:
        p = repo_dir / relpath
        if not p.exists():
            continue

        found_any = True
        raw = p.read_text(encoding="utf-8", errors="replace")
        raw_hash = sha256_text(raw)

        # store raw statement (verbatim) under commit
        out_raw_dir = STATEMENTS_DIR / name / commit
        safe_mkdir(out_raw_dir)
        out_raw_file = out_raw_dir / Path(relpath).name
        out_raw_file.write_text(raw, encoding="utf-8")

        # build normalized analysis record
        basics = extract_basic_fields(raw)
        canonical_sections = normalize_sections(raw)

        analysis = {
            "project": name,
            "repo": repo,
            "ref": ref if ref else None,
            "source_path": relpath,
            "commit": commit,
            "fetched_at_utc": fetched_at,
            "raw_sha256": raw_hash,
            "extracted": basics,
            "sections": canonical_sections,
        }

        out_analysis_dir = ANALYSIS_DIR / name
        safe_mkdir(out_analysis_dir)
        out_analysis_file = out_analysis_dir / f"{commit}.yaml"
        out_analysis_file.write_text(yaml.safe_dump(analysis, sort_keys=False, allow_unicode=True), encoding="utf-8")

        print(f"[OK] {name}: {relpath} @ {commit}")

    if not found_any:
        print(f"[WARN] {name}: no statement files found among {paths}", file=sys.stderr)

def main():
    if not SOURCES_FILE.exists():
        print(f"Missing {SOURCES_FILE}", file=sys.stderr)
        sys.exit(1)

    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8"))
    sources = data.get("sources", [])

    safe_mkdir(STATEMENTS_DIR)
    safe_mkdir(ANALYSIS_DIR)

    tmp_base = ROOT / ".tmp_upstream"
    safe_mkdir(tmp_base)

    for s in sources:
        ingest_one(s, tmp_base)

    # cleanup temp clones (optional)
    shutil.rmtree(tmp_base, ignore_errors=True)

if __name__ == "__main__":
    main()
