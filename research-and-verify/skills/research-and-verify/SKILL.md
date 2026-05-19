---
name: research-and-verify
description: >
  Run the full deep-research + fact-check pipeline end-to-end, non-stop.
  Wraps /deep-research → /extract-claims → /deep-verify →
  /verify-report with a single up-front interview, then chains the four
  phases without any inter-phase pause. Only error/conflict conditions
  (pre-existing outdir, missing verdicts, sub-skill crash) can interrupt —
  never the normal happy path. Use when the user wants a verified
  referential on a topic, says "lance le pipeline complet", "recherche +
  vérif", "deep research vérifié", "référentiel fact-checké", or invokes
  /research-and-verify.
---

# research-and-verify

You are orchestrating a four-phase verified-research pipeline. You will NOT
re-implement any phase — each phase is delegated to its dedicated sub-skill
via the `Skill` tool. Your job is to (1) collect inputs once via an
interview, (2) chain the four sub-skills in order **without pausing between
them on the happy path**, (3) filter the final report by a confidence
threshold the user chose up front, and (4) optionally emit a
`prompt-retour.md` for `/clear` continuation if the session burnt many
tokens.

**Non-interruptive guarantee.** Once the COLLECT phase ends and the
pre-flight overwrite/resume question is answered, the pipeline runs to the
end without any further prompt to the user, **except** when an error or
conflict requires a decision the wrapper cannot make safely on its own
(missing verdict files, sub-skill returning empty output, etc. — see
"Error handling"). There is **no editorial gate** between extraction and
verification. If the user wants to curate `claims.yaml` by hand, they can
abort, edit the file, and re-run on the same `$outdir` with `resume` —
extraction will be skipped and verification will pick up the edited file.

## Pipeline at a glance

```
[COLLECT]   Interview (6 questions) + pre-flight (overwrite/resume/abort)
                ↓
[PHASE 1]   Skill('deep-research')          → $outdir/referentiel.md
                ↓  (auto)
[PHASE 2]   Skill('extract-claims')      → $outdir/claims.yaml
                ↓  (auto — no gate)
[PHASE 3]   Skill('deep-verify')         → $outdir/verdicts/CLM-XXX.json
                ↓  (auto)
[PHASE 4]   Skill('verify-report')       → $outdir/report.md (filtré)
                ↓
[OUTRO]     Conditionnellement : $outdir/prompt-retour.md + reco /clear
```

## COLLECT — Interview (6 questions)

Ask these six questions **sequentially**, one per `AskUserQuestion` call (or
free text where indicated). Do not ask all at once — depth often depends on
context, and threshold depends on subject sensitivity.

Variables you must end the COLLECT phase with:
- `$subject` — string, free text
- `$context` — string, free text (may be empty)
- `$depth` — `"quick"` or `"deep"`
- `$max_claims` — integer, 1..25 (hard cap enforced by `validate_claims.py`)
- `$threshold` — `"all"` | `"confirmed-only"` | `"high-confidence-only"`
- `$outdir` — absolute path, defaults to `$CWD/<slug>/` where
  `<slug> = kebab-case($subject)`

`$CWD = the working directory at skill invocation (from the environment "Primary working directory" line).`

### Q1 — Subject (free text)

> "Sujet de la recherche ? (texte libre, sera utilisé comme slug du dossier
> de sortie)"

Set `$subject`. Compute `$slug = kebab-case($subject)` (lowercase, spaces →
`-`, strip diacritics, collapse repeats, trim).
Example: "Sécurité Webhooks & Idempotency" → "securite-webhooks-idempotency".

### Q2 — Context (free text, optional)

> "Contexte / stack / projet concerné ? (optionnel, tape `skip` pour passer)"

Set `$context` to "" if user replied `skip`.

### Q3 — Depth (bounded)

Use `AskUserQuestion` with these options:
- `quick` — "Survol rapide (10-15 best practices, ~5-7 web searches)"
- `deep` — "Référentiel complet (50+ règles, 8-10 web searches + cross-ref)" — **default**

Set `$depth`.

### Q4 — Max claims (bounded)

Use `AskUserQuestion`:
- `10` — "Mini pipeline (best practices stables, 1 cluster d'agents)"
- `20` — "Pipeline standard (recommandé)" — **default**
- `25` — "Pipeline maximal (hard cap validate_claims.py)"

Set `$max_claims`.

### Q5 — Confidence threshold (bounded)

Use `AskUserQuestion`:
- `all` — "Tout inclure (confirmed + partial + unverified + contradicted)" — **default**
- `confirmed-only` — "Confirmed + partially_confirmed seulement"
- `high-confidence-only` — "Confirmed ET confidence ≥ 0.8 seulement"

Set `$threshold`.

### Q6 — Output directory (free text with default)

> "Dossier de sortie ? (défaut: `$CWD/$slug/`)"

If user replies empty / `default` / `ok`, set `$outdir = $CWD/$slug/`.
Otherwise use what they provided. Resolve to absolute path.

### Post-COLLECT — pre-flight

Before Phase 1:
1. Create `$outdir` if missing: `mkdir -p $outdir`.
2. If `$outdir` already contains files (`referentiel.md`, `claims.yaml`,
   `verdicts/`, `report.md`), ask the user **once**:
   - `overwrite` — delete these paths before proceeding:
     - `$outdir/referentiel.md`
     - `$outdir/claims.yaml`
     - `$outdir/verdicts/`   (entire directory, recursive)
     - `$outdir/report.md`
     - `$outdir/prompt-retour.md`
     Any other files in `$outdir` are left untouched.
   - `resume` — skip phases whose output already exists
   - `abort` — stop the pipeline
   Default: `abort` if no response.
3. Echo the resolved variables to the user as a confirmation block before
   launching Phase 1.

This is the **last** user-facing question on the happy path. From here on,
the four phases chain automatically; user input is only solicited again if
an error/conflict condition is hit (see "Error handling").

## PHASE 1 — deep-research

Invoke the `deep-research` sub-skill with a prompt that hands over the
COLLECT variables. Do **not** re-implement deep-research — the sub-skill
already handles 3-source synthesis, web search caps, and depth tuning.

Pre-check (if `resume` was chosen at pre-flight):
  If `$outdir/referentiel.md` already exists and is non-empty, skip
  the invocation, announce "↪ Phase 1 skipped (resume): $outdir/referentiel.md already
  present", and proceed to the next phase.

Invocation pattern:

```
Skill('deep-research') with prompt:
  Subject: $subject
  Context: $context (or "no specific context" if empty)
  Depth: $depth
  Output file: $outdir/referentiel.md
  Reminder: respect OPT-H (web-search caps) (cap 5-7 searches for quick, 8-10 for deep).
```

When the sub-skill returns:
1. Verify `$outdir/referentiel.md` exists and is non-empty.
2. If missing or empty, surface the error to the user and abort.
3. Otherwise, announce: "✅ Phase 1 done. Referential at $outdir/referentiel.md (N lines)."
4. Proceed automatically to Phase 2 — no gate here.

## PHASE 2 — extract-claims

Invoke the `extract-claims` sub-skill on the referential. Hard cap at
`$max_claims` (≤ 25). Cluster detection — OPT-C (cluster detection) — and
reuse markers — OPT-N (reuse markers) — are already integrated in the
sub-skill; just remind it explicitly in the prompt.

Pre-check (if `resume` was chosen at pre-flight):
  If `$outdir/claims.yaml` already exists and is non-empty, skip
  the invocation, announce "↪ Phase 2 skipped (resume): $outdir/claims.yaml already
  present", and proceed to the next phase.

Invocation pattern:

```
Skill('extract-claims') with prompt:
  Source: $outdir/referentiel.md
  Max claims: $max_claims (hard cap 25)
  Output: $outdir/claims.yaml
  Reminders:
    - OPT-C: detect clusters and add `cluster:` field per claim
    - OPT-N: mark claims previously verified with `verified_in:` if any
      memory or prior pipeline output suggests reuse
    - Prioritise `high` and `medium`, minimise `low`. The sub-skill applies its own priors per $max_claims.
```

When the sub-skill returns:
1. Verify `$outdir/claims.yaml` exists.
2. Parse it (read tool) and compute summary counts: high / medium / low /
   total / distinct clusters.
3. If `total == 0`, abort with: "claims.yaml is empty — inspect
   $outdir/referentiel.md and re-run." (Error condition — see "Error
   handling".)
4. Otherwise, announce a one-line summary to the user (counts + cluster
   list + path) and **proceed automatically to Phase 3 without pausing**.
   The user is not asked to confirm or edit. If they want to curate
   `claims.yaml` by hand, they can interrupt, edit the file, and re-run
   the skill with `resume` — Phase 3 will then verify the edited file.

## PHASE 3 — deep-verify

Invoke the `deep-verify` sub-skill on the claims file produced in
Phase 2 (or restored from a previous run via `resume`). All token
optimisations A–S are already integrated in the sub-skill; the wrapper
only **reminds** of the critical ones in the invocation prompt for
robustness.

Pre-check (if `resume` was chosen at pre-flight):
  If `$outdir/verdicts/` directory exists and contains at least one
  `CLM-*.json` file, skip the invocation, announce "↪ Phase 3 skipped
  (resume): $outdir/verdicts/ already present", and proceed to the next phase.

Invocation pattern:

```
Skill('deep-verify') with prompt:
  Claims file: $outdir/claims.yaml
  Verdicts dir: $outdir/verdicts/
  Mode: run_in_background=true, model=haiku, compact agent config.
  Reminders:
    - OPT-K (strict file paths): strict file path enforcement — UN fichier CLM-XXX.json par claim
    - OPT-J (verdict normalisation): normalize verdicts after run (validate_verdict.py --normalize)
    - OPT-G (verdict schema whitelist): respect verdict JSON schema whitelist
```

When the sub-skill returns (all background agents complete):
1. List `$outdir/verdicts/CLM-*.json`.
2. Cross-reference against `claims.yaml` (excluding any claim with
   `verify_skip: true`).
3. If any non-skipped claim has no matching verdict file, surface the
   missing IDs and ask: `retry-missing` | `abort` | `proceed-anyway`.
   (Error condition — see "Error handling".)
4. Otherwise, announce: "✅ Phase 3 done. N verdicts at $outdir/verdicts/."
5. Proceed automatically to Phase 4.

## PHASE 4 — verify-report (with threshold filter)

Invoke `verify-report` with the threshold filter from COLLECT injected
into the prompt. The sub-skill itself is **not patched** — filtering is
expressed as an instruction in the invocation prompt.

Pre-check (if `resume` was chosen at pre-flight):
  If `$outdir/report.md` already exists and is non-empty, skip the
  invocation, announce "↪ Phase 4 skipped (resume): $outdir/report.md already
  present", and proceed to the next phase.

Invocation pattern:

```
Skill('verify-report') with prompt:
  Verdicts dir: $outdir/verdicts/
  Output: $outdir/report.md
  Mode: concise — OPT-F (lazy verdict reads): lit JSON intégral seulement pour non-confirmed

  Threshold filter ($threshold):
    case "all":
      Include every verdict in the body. No filtering.
    case "confirmed-only":
      Body includes only verdicts with status ∈
        {confirmed, partially_confirmed}.
      Append a "## Filtered out" section listing the others with the
      claim ID, status, and ONE-LINE reason.
    case "high-confidence-only":
      Body includes only verdicts with status == "confirmed"
      AND confidence ≥ 0.8.
      Append a "## Filtered out" section listing the others with the
      claim ID, status, confidence, and ONE-LINE reason.

  At top of report, add a one-line banner:
    "> Threshold: $threshold — N kept, M filtered out."
```

When the sub-skill returns:
1. Verify `$outdir/report.md` exists.
2. Announce: "✅ Phase 4 done. Report at $outdir/report.md."
3. Proceed to OUTRO.

## OUTRO — token economy + optional prompt-retour

A Claude instance cannot reliably introspect its own context size, so the
wrapper uses a deterministic **heuristic** based on pipeline parameters
instead of a measured token count.

Decision rule:

  heavy_session = ($depth == "deep") OR ($max_claims >= 20)

  if heavy_session:
    write $outdir/prompt-retour.md with this body:

      ---
      Subject: $subject
      Context: $context
      Outdir: $outdir
      Pipeline status: complete
      Threshold applied: $threshold
      Livrables:
        - referentiel.md
        - claims.yaml
        - verdicts/CLM-*.json
        - report.md
      ---

      Reprise du sujet "$subject".

      Pipeline research-and-verify terminé dans $outdir/. Le rapport final
      est filtré au seuil "$threshold" (voir bannière en tête du fichier).

      Next steps possibles :
        - Lire $outdir/report.md
        - Demander une synthèse exécutive du report
        - Demander un patch des claims contradicted/unverified
        - Relancer une vérification ciblée sur un cluster
        - Convertir le report en livrable client (slides, exec memo, etc.)

    display to user:
      "Pipeline terminé. Pipeline lourd (depth=$depth, max_claims=$max_claims).
       Recommandation : /clear puis charger $outdir/prompt-retour.md pour
       la suite (économie de tokens substantielle)."

  else:
    display to user:
      "Pipeline terminé. Livrables dans $outdir/.
       Pipeline léger — pas besoin de /clear immédiat."

This is the terminal state of the skill. Do not continue beyond OUTRO.

## Error handling

The wrapper does **not** retry automatically. On the happy path, the four
phases chain without ever asking the user a question. The user is
solicited again **only** when one of the conditions below is hit. Each
such interruption is genuinely necessary — the wrapper cannot decide
safely on its own. Resumption is always possible — re-invoking
research-and-verify on the same `$outdir` with `resume` will skip phases
whose output already exists.

| Failure | Behaviour |
|---------|-----------|
| `$outdir` pre-existing with conflicting files | Asked at end of COLLECT (pre-flight): `overwrite` / `resume` / `abort` (default abort). |
| `deep-research` returns no file or empty file | Abort. Show sub-skill's error verbatim. Suggest re-running with a more specific subject. |
| `extract-claims` returns 0 claims | Abort. Point at `$outdir/referentiel.md` for the user to inspect. |
| `deep-verify` produces partial verdict set | Ask user: `retry-missing` / `abort` / `proceed-anyway`. |
| `verify-report` returns no file | Abort. Verdicts are preserved — user can re-run report manually. |

Never:
- Modify any file outside `$outdir` (except as needed by the sub-skills'
  own conventions).
- Retry a failed sub-skill more than once automatically.
- Insert any prompt between phases on the happy path. The only legitimate
  user-facing pauses are (a) the COLLECT interview, (b) the pre-flight
  overwrite/resume question, and (c) the error conditions in the table
  above.

## Reference

- Sub-skills consumed (read-only), expected siblings in the same `skills/`
  directory (project-local `.claude/skills/` or user-global):
  - `deep-research/SKILL.md`
  - `extract-claims/SKILL.md`
  - `deep-verify/SKILL.md`
  - `verify-report/SKILL.md`
- Origin: bundle research-and-verify-skills, see `README.md` at bundle root
  for install instructions on Linux/macOS/Windows.
