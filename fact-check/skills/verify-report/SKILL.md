---
name: verify-report
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
description: >
  Read verification results from JSON verdict files, confront each claim with
  evidence, identify cross-cutting patterns, and generate a structured markdown
  report. This is the final step in the fact-checking pipeline: run
  /extract-claims to extract claims from any document, then /deep-verify to
  research them, then this skill to produce the confrontation report. Use when
  the user says "generate report", "verification report", "confrontation report",
  "génère le rapport", "montre les résultats", "show results", or wants to see
  the synthesis of the deep verification phase.
---

# Verify Report

This skill reads the verdict JSON files produced by `/deep-verify`, confronts each claim against its evidence, identifies cross-cutting patterns, and generates a structured report. The report is designed to be actionable: it tells the author exactly what to fix, keep, or investigate further.

## Step 1: Locate the results

Find `*/claims.yaml` in the current working directory. Read the execution config and the full list of claims.

Note: accepter le champ `source:` (nouveau) et `prd_source:` (rétrocompatibilité v0) dans claims.yaml. Le rapport doit mentionner la source originale en en-tête.

Scan the `output_dir` (from claims.yaml's `execution.output_dir`) for all `CLM-*.json` files. For each file, validate it using:

```bash
python /path/to/deep-verify/validate_verdict.py path/to/results/
```

Report any missing or invalid verdicts: "CLM-005 is missing, CLM-012 failed validation (reason). The report will cover N/M claims."

## Step 2: Confrontation analysis

For each claim, perform a meta-verification.

**OPT-F — Concise mode optimization (token efficiency) :** En mode `concise` (default), **ne lire entièrement que les JSONs avec verdict dans {partially_confirmed, contradicted, unverified, outdated}**. Pour les `confirmed`, lire seulement `verdict`, `confidence`, `claim_text` (lecture partielle via Read offset/limit ou via `python -c` qui n'extrait que les champs nécessaires). Économie typique : 60-80 % de la lecture JSON quand la majorité est confirmed.

1. **Read the verdict JSON** — load the verdict, confidence, evidence, and recommendation (full pour issues, partial pour confirmed-haute-conf — cf. OPT-F)
2. **Re-read the original claim** from claims.yaml — compare the claim text to what was investigated
3. **Assess verdict consistency** — Does the verdict match the evidence? A "confirmed" verdict with only 1 low-credibility source is suspicious. A "contradicted" verdict where only 1 out of 4 sources disagrees is not really contradicted.
4. **Flag suspicious patterns:**
   - Verdict "confirmed" but confidence < 0.5
   - Verdict "contradicted" but most evidence supports the claim
   - All evidence from the same source domain (single-source dependency)
   - Evidence dates more than 2 years old on a fast-moving topic
   - Recommendation says "keep as-is" but confidence is below 0.6

## Step 3: Identify cross-cutting patterns

Look across all verdicts for systemic issues:

- **Problematic section**: multiple claims from the same source section are contradicted or unverified — the section needs a rewrite, not just individual fixes
- **Outdated cluster**: 3+ claims flagged as `outdated` — the source needs a freshness pass
- **Unverifiable mass**: many `unverified` verdicts — the source makes assertions that can't be externally validated, which weakens its credibility
- **Single-source dependency**: one paper or report is cited as evidence for 3+ different claims — fragile foundation
- **Inter-claim inconsistency**: Claim A confirmed says X, Claim B confirmed says not-X — the source has an internal contradiction based on verified external facts
- **Category concentration**: most issues cluster in one category (e.g., all market_sizing claims are weak) — signals a specific knowledge gap

## Step 4: Ask report preferences

Use `AskUserQuestion` to ask:

1. "What language for the report?" (default: same as the source)
2. "Level of detail?" — options:
   - **Concise** (default): executive summary + problematic claims only + patterns. Sufficient for most pipelines and saves significant tokens when the source has many confirmed claims.
   - **Detailed**: full report with all claims including confirmed ones. Use only when the user needs an audit trail.
3. "Include confirmed claims in detail?" — options:
   - **Yes**: full evidence for every claim
   - **No** (default): confirmed claims as a compact list, detail only for issues

## Step 5: Generate the report

Write the report in markdown following this structure:

```markdown
# Deep Review — [Source Name]

> Generated on YYYY-MM-DD
> Source: [path or "inline-text"] (N claims verified out of M extracted)
> Depth: thorough / quick

## Executive Summary

X claims verified out of Y extracted.
- [checkmark] N confirmed
- [warning] N partially confirmed
- [cross] N contradicted
- [question] N unverifiable
- [calendar] N outdated

Most problematic sections: [list sections with highest issue density]
Overall recommendation: [Go / Go with reservations / Rework needed on sections X, Y]

## Dashboard by Category

| Category | Total | Confirmed | Partial | Contradicted | Unverified | Outdated |
|----------|-------|-----------|---------|-------------|-----------|---------|
| Technical Performance | 5 | 2 | 1 | 1 | 1 | 0 |
| Market Sizing | 3 | 1 | 1 | 0 | 0 | 1 |
| ... | | | | | | |

## Contradicted Claims (action required)

For each contradicted claim:

### CLM-XXX — "[short claim text]"
- **Location:** section X, paragraph Y (ou slide N)
- **Verdict:** Contradicted (confidence: 0.XX)
- **What the source says:** [exact claim text]
- **What the research shows:** [synthesis of contradicting evidence]
- **Sources:** [source1] (credibility), [source2] (credibility)
- **Recommendation:** [concrete action — reformulate, remove, replace]

## Partially Confirmed Claims (review recommended)

Same format as above, but with nuances about what's correct and what's not.

## Outdated Claims

Same format, emphasizing what changed and when.

## Unverifiable Claims

Brief list with explanation of why verification failed and suggestions
for where the author might find better data.

## Confirmed Claims

If detailed mode: same format.
If concise mode: compact table — ID, text, confidence, number of sources.

## Cross-cutting Patterns

Synthesize the patterns identified in Step 3. Each pattern should include:
- What the pattern is
- Which claims it affects (list CLM IDs)
- Why it matters
- Recommended action

## Sources Used

Deduplicated list of all sources across all verdicts, sorted by credibility:

### High credibility
- [source URL] — used for CLM-001, CLM-005, CLM-012

### Medium credibility
- [source URL] — used for CLM-003

### Low credibility
- [source URL] — used for CLM-008
```

## Step 6: Write and suggest next steps

Write the report to `report.md` in the source's working directory (same directory as claims.yaml and results/).

Then suggest:
- "Would you like me to apply the recommended reformulations directly in the source document?"
- "Would you like to run `/review-prd` for a complementary structural review?" (si la source est un PRD)
- "Would you like to re-verify any specific claims with different search queries?"

## Output structure

```
{source_name_slug}/
  |-- claims.yaml
  |-- results/
  |   |-- CLM-001.json
  |   `-- ...
  `-- report.md          <- generated by this skill
```

## Report quality guidelines

The report should be:
- **Actionable**: every finding leads to a concrete recommendation
- **Proportionate**: don't bury 2 critical contradictions under 30 confirmed claims. Lead with what matters
- **Honest about uncertainty**: if confidence is low, say so. Don't present weak evidence as strong conclusions
- **Source-transparent**: always show the sources, their credibility, and their dates. The reader should be able to verify your verification
- **Respectful of the author's work**: the goal is to improve the document, not to demonstrate how wrong it is. Frame findings constructively
