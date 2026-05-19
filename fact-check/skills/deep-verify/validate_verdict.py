#!/usr/bin/env python3
"""Validate verdict JSON files for completeness and consistency.

Usage:
    python validate_verdict.py path/to/CLM-001.json
    python validate_verdict.py path/to/results/   # validates all JSON in directory

Exit codes:
    0 — all valid (may have warnings)
    1 — at least one invalid file
"""

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "claim_id", "claim_text", "verdict", "confidence",
    "summary", "evidence", "recommendation"
]

VALID_VERDICTS = {
    "confirmed", "partially_confirmed", "unverified",
    "contradicted", "outdated"
}

# OPT-J — verdict synonym normalization map (P2 retour : agents Haiku produisent
# des variantes non-canoniques). Lowercase keys → canonical value.
VERDICT_SYNONYMS = {
    "verified": "confirmed",
    "verified_high": "confirmed",
    "found_in_sources": "confirmed",
    "pass": "confirmed",
    "ok": "confirmed",
    "verified_partial": "partially_confirmed",
    "partially_verified": "partially_confirmed",
    "partial": "partially_confirmed",
    "not_found": "unverified",
    "no_evidence": "unverified",
    "fail": "contradicted",
    "false": "contradicted",
    "stale": "outdated",
    "expired": "outdated",
}


def normalize_verdict(raw: str) -> str:
    """Normalize a verdict string to canonical enum (OPT-J).

    Tries: full match, then first-token match (before space/dash/em-dash/colon)
    to handle agent verbose prefixes like "PASS — both sub-claims...".
    """
    if not isinstance(raw, str):
        return raw
    lower = raw.strip().lower()
    if lower in VALID_VERDICTS:
        return lower
    if lower in VERDICT_SYNONYMS:
        return VERDICT_SYNONYMS[lower]
    # First-token fallback (split on common separators)
    for sep in ("—", " - ", " — ", ":", " "):
        if sep in lower:
            head = lower.split(sep, 1)[0].strip()
            if head in VALID_VERDICTS:
                return head
            if head in VERDICT_SYNONYMS:
                return VERDICT_SYNONYMS[head]
    return raw  # leave untouched if unknown


def normalize_file(json_path: Path) -> bool:
    """Read, normalize verdict, write back. Return True if changed."""
    try:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(data, dict):
        return False
    raw = data.get("verdict", "")
    canonical = normalize_verdict(raw)
    if canonical != raw:
        data["verdict"] = canonical
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    return False

VALID_SOURCE_TYPES = {
    "academic_paper", "industry_report", "official_docs",
    "vendor_blog", "news", "forum"
}

VALID_CREDIBILITIES = {"high", "medium", "low"}


def validate_verdict(json_path: Path) -> dict:
    """Validate a single verdict JSON file."""
    try:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "file": json_path.name,
            "valid": False,
            "errors": [f"Invalid JSON: {e}"],
            "warnings": []
        }

    errors = []
    warnings = []

    if not isinstance(data, dict):
        return {
            "file": json_path.name,
            "valid": False,
            "errors": ["File does not contain a JSON object"],
            "warnings": []
        }

    # --- Required fields ---
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # --- Verdict value ---
    verdict = data.get("verdict", "")
    if verdict not in VALID_VERDICTS:
        errors.append(
            f"Invalid verdict: '{verdict}'. "
            f"Must be one of {sorted(VALID_VERDICTS)}"
        )

    # --- Confidence range ---
    conf = data.get("confidence", -1)
    if not isinstance(conf, (int, float)):
        errors.append(f"Confidence must be a number, got: {type(conf).__name__}")
    elif not (0.0 <= conf <= 1.0):
        errors.append(f"Confidence {conf} out of range [0.0, 1.0]")

    # --- Summary length ---
    summary = data.get("summary", "")
    if isinstance(summary, str) and len(summary) < 20:
        warnings.append(f"Summary is very short ({len(summary)} chars)")

    # --- Evidence ---
    evidence = data.get("evidence", [])
    if not isinstance(evidence, list):
        errors.append("'evidence' must be a list")
        evidence = []

    if len(evidence) == 0:
        errors.append("No evidence provided")

    for i, ev in enumerate(evidence):
        prefix = f"Evidence[{i}]"

        if not isinstance(ev, dict):
            errors.append(f"{prefix} is not an object")
            continue

        # Required evidence fields
        if "source_url" not in ev:
            errors.append(f"{prefix} missing source_url")
        if "supports_claim" not in ev:
            errors.append(f"{prefix} missing supports_claim")

        # Optional but expected fields
        if "relevant_finding" not in ev:
            warnings.append(f"{prefix} missing relevant_finding")

        # Validate source_type if present
        src_type = ev.get("source_type", "")
        if src_type and src_type not in VALID_SOURCE_TYPES:
            warnings.append(
                f"{prefix} non-standard source_type: '{src_type}'"
            )

        # Validate credibility if present
        cred = ev.get("source_credibility", "")
        if cred and cred not in VALID_CREDIBILITIES:
            warnings.append(
                f"{prefix} non-standard source_credibility: '{cred}'"
            )

    # --- Consistency checks ---
    if isinstance(conf, (int, float)):
        if verdict == "confirmed" and conf < 0.6:
            errors.append(
                f"Inconsistency: verdict=confirmed but confidence={conf} "
                f"(expected >= 0.6)"
            )
        if verdict == "contradicted" and conf < 0.3:
            errors.append(
                f"Inconsistency: verdict=contradicted but confidence={conf} "
                f"(expected >= 0.3 — low confidence contradiction is suspect)"
            )
        if verdict == "unverified" and conf > 0.7:
            warnings.append(
                f"Unusual: verdict=unverified but confidence={conf} "
                f"(high confidence usually implies a definitive verdict)"
            )

    # --- Check for supporting vs contradicting evidence alignment ---
    if evidence and verdict in ("confirmed", "contradicted"):
        supporting = sum(1 for ev in evidence if ev.get("supports_claim", False))
        contradicting = len(evidence) - supporting

        if verdict == "confirmed" and contradicting > supporting:
            warnings.append(
                f"Verdict is 'confirmed' but more evidence contradicts "
                f"({contradicting}) than supports ({supporting})"
            )
        if verdict == "contradicted" and supporting > contradicting:
            warnings.append(
                f"Verdict is 'contradicted' but more evidence supports "
                f"({supporting}) than contradicts ({contradicting})"
            )

    return {
        "file": json_path.name,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python validate_verdict.py [--normalize] <path-to-CLM-XXX.json or directory>",
            file=sys.stderr
        )
        sys.exit(1)

    args = sys.argv[1:]
    do_normalize = False
    if args and args[0] == "--normalize":
        do_normalize = True
        args = args[1:]

    if not args:
        print("Missing path argument", file=sys.stderr)
        sys.exit(1)
    target = Path(args[0])

    if target.is_dir():
        json_files = sorted(target.glob("CLM-*.json"))
        if not json_files:
            print(f"No CLM-*.json files found in {target}", file=sys.stderr)
            sys.exit(1)
    elif target.is_file():
        json_files = [target]
    else:
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    # OPT-J — normalize first if requested
    if do_normalize:
        n_changed = 0
        for json_path in json_files:
            if normalize_file(json_path):
                n_changed += 1
        print(f"Normalized {n_changed}/{len(json_files)} verdict files (OPT-J).", file=sys.stderr)

    all_valid = True
    for json_path in json_files:
        result = validate_verdict(json_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if not result["valid"]:
            all_valid = False
            print(
                f"\n  FAILED — {len(result['errors'])} error(s)",
                file=sys.stderr
            )
        else:
            print(f"\n  PASSED", file=sys.stderr)
            if result["warnings"]:
                print(
                    f"  ({len(result['warnings'])} warning(s))",
                    file=sys.stderr
                )

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
