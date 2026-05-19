#!/usr/bin/env python3
"""
Validate the Claude Cowork marketplace repo before a PR is merged.

Checks:
  1. .claude-plugin/marketplace.json exists, parses, has required fields.
  2. Every plugin listed in marketplace.json has a corresponding folder
     with .claude-plugin/plugin.json.
  3. Every plugin.json parses, has required fields (name, version, description),
     and name is kebab-case + matches the folder name.
  4. Every plugin name is lowercase-hyphenated.
  5. Every plugin folder at the repo root is listed in marketplace.json
     (no orphan plugin folders).
  6. Every SKILL.md under skills/ has YAML frontmatter with name + description.

Exit code 0 on success, 1 on any failure. Failures are printed to stdout.

Run locally:    python scripts/validate_marketplace.py
Run in CI:      same command, called from .github/workflows/validate-pr.yml

No third-party dependencies — only stdlib + a tiny YAML frontmatter parser.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([-+].+)?$")

# Extensions considérées comme texte pour la vérification CRLF
TEXT_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".tpl", ".py", ".js", ".sh", ".txt"}

# Folders at the repo root that are NOT plugins
NON_PLUGIN_ROOT_DIRS = {
    ".claude-plugin",
    ".github",
    ".git",
    "scripts",
    "docs",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"  OK:   {msg}")


def parse_frontmatter(text: str) -> dict | None:
    """Tiny YAML frontmatter parser. Only handles `key: value` lines between --- markers."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if len(lines) < 2:
        return None
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    fm: dict[str, str] = {}
    for line in lines[1:end_idx]:
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def validate_marketplace_json() -> dict | None:
    print("\n[1] Validating .claude-plugin/marketplace.json")
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if not path.exists():
        fail(f"{path.relative_to(REPO_ROOT)} does not exist")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"marketplace.json: invalid JSON — {e}")
        return None
    for field in ("name", "owner", "plugins"):
        if field not in data:
            fail(f"marketplace.json: missing required field '{field}'")
    if "plugins" in data and not isinstance(data["plugins"], list):
        fail("marketplace.json: 'plugins' must be a list")
    if not errors:
        ok(f"marketplace.json parsed, lists {len(data.get('plugins', []))} plugin(s)")
    return data


def validate_plugin_entry(entry: dict, idx: int) -> str | None:
    """Validate one entry in marketplace.json plugins[]. Returns the resolved folder name."""
    for field in ("name", "source", "description"):
        if field not in entry:
            fail(f"plugins[{idx}]: missing required field '{field}'")
            return None
    name = entry["name"]
    if not KEBAB_RE.match(name):
        fail(f"plugins[{idx}]: name '{name}' is not lowercase-hyphenated")
    source = entry["source"]
    if not isinstance(source, str) or not source.startswith("./"):
        fail(
            f"plugins[{idx}] '{name}': source must be a relative path starting with './' "
            f"(got '{source}'). External sources require public target repos."
        )
        return name
    folder = REPO_ROOT / source[2:]
    if not folder.is_dir():
        fail(f"plugins[{idx}] '{name}': source folder '{source}' does not exist")
    return name


def validate_plugin_folder(plugin_name: str) -> None:
    print(f"\n[2] Validating plugin folder: {plugin_name}/")
    folder = REPO_ROOT / plugin_name
    pjson_path = folder / ".claude-plugin" / "plugin.json"
    if not pjson_path.exists():
        fail(f"{plugin_name}/.claude-plugin/plugin.json does not exist")
        return
    try:
        pjson = json.loads(pjson_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{plugin_name}/.claude-plugin/plugin.json: invalid JSON — {e}")
        return
    for field in ("name", "version", "description"):
        if field not in pjson:
            fail(f"{plugin_name}/plugin.json: missing required field '{field}'")
    if "name" in pjson:
        if pjson["name"] != plugin_name:
            fail(
                f"{plugin_name}/plugin.json: name '{pjson['name']}' does not match folder '{plugin_name}'"
            )
        if not KEBAB_RE.match(pjson["name"]):
            fail(f"{plugin_name}/plugin.json: name '{pjson['name']}' is not lowercase-hyphenated")
    if "version" in pjson and not SEMVER_RE.match(str(pjson["version"])):
        fail(f"{plugin_name}/plugin.json: version '{pjson['version']}' is not SemVer-shaped")
    ok(f"{plugin_name}/.claude-plugin/plugin.json parsed")

    # Validate skills/ if it exists
    skills_dir = folder / "skills"
    if skills_dir.is_dir():
        skill_count = 0
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                fail(f"{plugin_name}/skills/{skill_dir.name}/SKILL.md does not exist")
                continue
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            if fm is None:
                fail(f"{plugin_name}/skills/{skill_dir.name}/SKILL.md: missing YAML frontmatter")
                continue
            for field in ("name", "description"):
                if field not in fm or not fm[field]:
                    fail(
                        f"{plugin_name}/skills/{skill_dir.name}/SKILL.md: frontmatter missing '{field}'"
                    )
            skill_count += 1
        ok(f"{plugin_name}/skills/ — {skill_count} skill(s) validated")


def check_crlf(plugin_names: set[str]) -> None:
    """Vérifie qu'aucun fichier texte des plugins ne contient des fins de ligne CRLF.

    Les CRLF cassent silencieusement le parser YAML du frontmatter SKILL.md
    et rendent les plugins invisibles dans Cowork (incident ag-documents 2026-05-18).
    """
    print("\n[4] Checking for CRLF line endings in plugin files")
    crlf_files: list[str] = []
    for plugin_name in sorted(plugin_names):
        plugin_dir = REPO_ROOT / plugin_name
        for f in sorted(plugin_dir.rglob("*")):
            if not f.is_file():
                continue
            if f.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if b"\r" in f.read_bytes():
                    crlf_files.append(str(f.relative_to(REPO_ROOT)))
            except OSError:
                pass
    if crlf_files:
        for path in crlf_files:
            fail(f"CRLF detected: {path}")
        fail(
            f"{len(crlf_files)} file(s) have CRLF line endings — "
            "convert to LF (dos2unix or PowerShell -replace '\\r\\n','\\n')"
        )
    else:
        ok("no CRLF line endings detected")


def check_orphan_folders(listed: set[str]) -> None:
    print("\n[3] Checking for orphan plugin folders")
    for child in sorted(REPO_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name in NON_PLUGIN_ROOT_DIRS:
            continue
        if child.name.startswith("."):
            continue
        if child.name not in listed:
            fail(
                f"folder '{child.name}/' exists at repo root but is not listed in marketplace.json"
            )
        else:
            ok(f"folder '{child.name}/' is listed")


def main() -> int:
    print(f"Validating Claude Cowork marketplace at: {REPO_ROOT}")
    data = validate_marketplace_json()
    if data is None:
        return 1

    listed_names: set[str] = set()
    for idx, entry in enumerate(data.get("plugins", [])):
        if not isinstance(entry, dict):
            fail(f"plugins[{idx}]: must be an object")
            continue
        name = validate_plugin_entry(entry, idx)
        if name:
            listed_names.add(name)
            validate_plugin_folder(name)

    check_crlf(listed_names)
    check_orphan_folders(listed_names)

    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print("PASSED: marketplace is sync-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
