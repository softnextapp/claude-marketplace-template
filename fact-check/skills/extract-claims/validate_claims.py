#!/usr/bin/env python3
"""Validate claims.yaml for completeness and consistency before deep verification.

Usage:
    python validate_claims.py path/to/claims.yaml

Exit codes:
    0 — valid (may have warnings)
    1 — invalid (has errors)
"""

import yaml
import sys
import json
from pathlib import Path

REQUIRED_CLAIM_FIELDS = [
    "id", "text", "location", "category", "criticality",
    "impact", "research_module", "search_queries_suggested"
]

VALID_CATEGORIES = {
    "technical_performance", "technical_feasibility", "market_sizing",
    "competitive_landscape", "cost_estimate", "citation_verification",
    "standard_compliance", "temporal_claim", "user_behavior",
    "regulatory", "architectural_claim"
}

VALID_CRITICALITIES = {"high", "medium", "low"}
VALID_SEARCH_DEPTHS = {"quick", "thorough"}


def validate_claims(yaml_path: Path) -> dict:
    """Validate a claims.yaml file and return a structured result."""
    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    errors = []
    warnings = []

    if not isinstance(data, dict):
        return {
            "file": yaml_path.name,
            "valid": False,
            "errors": ["File does not contain a YAML mapping"],
            "warnings": [],
            "stats": {}
        }

    # --- Top-level structure ---
    for field in ("prd_source", "extraction_date", "execution", "claims"):
        if field not in data:
            errors.append(f"Missing top-level field: {field}")

    if "claims" not in data:
        return {
            "file": yaml_path.name,
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "stats": {}
        }

    # --- Execution config ---
    exec_cfg = data.get("execution", {})
    depth = exec_cfg.get("search_depth")
    if depth not in VALID_SEARCH_DEPTHS:
        errors.append(
            f"Invalid search_depth: '{depth}'. Must be one of {sorted(VALID_SEARCH_DEPTHS)}"
        )

    batch = exec_cfg.get("batch_size")
    if not isinstance(batch, int) or batch < 1:
        errors.append(f"batch_size must be a positive integer, got: {batch}")

    # --- Claims ---
    claims = data.get("claims", [])
    if not isinstance(claims, list):
        errors.append("'claims' must be a list")
        claims = []

    if len(claims) == 0:
        errors.append("No claims found in claims.yaml")

    max_claims = exec_cfg.get("max_claims", 25)
    if len(claims) > max_claims:
        errors.append(f"Too many claims: {len(claims)} exceeds max_claims={max_claims}")

    seen_ids = set()
    for i, claim in enumerate(claims):
        prefix = f"Claim[{i}]"

        if not isinstance(claim, dict):
            errors.append(f"{prefix} is not a mapping")
            continue

        # Required fields
        for field in REQUIRED_CLAIM_FIELDS:
            if field not in claim:
                errors.append(f"{prefix} missing required field: {field}")

        # ID uniqueness and format
        cid = claim.get("id", "")
        if cid in seen_ids:
            errors.append(f"{prefix} duplicate id: {cid}")
        seen_ids.add(cid)

        if cid and not (cid.startswith("CLM-") and len(cid) == 7):
            warnings.append(f"{prefix} id '{cid}' doesn't follow CLM-NNN format")

        # Category
        cat = claim.get("category", "")
        if cat and cat not in VALID_CATEGORIES:
            errors.append(
                f"{prefix} invalid category: '{cat}'. "
                f"Must be one of {sorted(VALID_CATEGORIES)}"
            )

        # Criticality
        crit = claim.get("criticality", "")
        if crit and crit not in VALID_CRITICALITIES:
            errors.append(f"{prefix} invalid criticality: '{crit}'")

        # Text length
        text = claim.get("text", "")
        if isinstance(text, str) and len(text) < 10:
            warnings.append(f"{prefix} claim text is very short ({len(text)} chars)")

        # Search queries
        queries = claim.get("search_queries_suggested", [])
        if not isinstance(queries, list) or len(queries) < 1:
            warnings.append(f"{prefix} should have at least 1 search query suggested")

    # --- Stats ---
    stats = {
        "total_claims": len(claims),
        "by_criticality": {
            c: sum(1 for cl in claims if cl.get("criticality") == c)
            for c in VALID_CRITICALITIES
        },
        "by_category": {
            c: sum(1 for cl in claims if cl.get("category") == c)
            for c in VALID_CATEGORIES
            if any(cl.get("category") == c for cl in claims)
        }
    }

    return {
        "file": yaml_path.name,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_claims.py <path-to-claims.yaml>", file=sys.stderr)
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f"File not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    result = validate_claims(yaml_path)

    # Pretty-print the result
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["errors"]:
        print(f"\nVALIDATION FAILED — {len(result['errors'])} error(s)", file=sys.stderr)
    else:
        print(f"\nVALIDATION PASSED", file=sys.stderr)
        if result["warnings"]:
            print(f"  ({len(result['warnings'])} warning(s))", file=sys.stderr)

    # Print stats summary
    stats = result.get("stats", {})
    if stats:
        print(f"\n  Total claims: {stats.get('total_claims', 0)}", file=sys.stderr)
        by_crit = stats.get("by_criticality", {})
        print(f"  High: {by_crit.get('high', 0)} | "
              f"Medium: {by_crit.get('medium', 0)} | "
              f"Low: {by_crit.get('low', 0)}", file=sys.stderr)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
