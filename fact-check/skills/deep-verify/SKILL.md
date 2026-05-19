---
name: deep-verify
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch, Agent
description: >
  Read extracted claims from claims.yaml, launch parallel verification agents
  for each claim using web search and academic sources, and produce individual
  JSON verdict files. This is the second step in the fact-checking pipeline:
  run /extract-claims first to generate claims.yaml, then this skill to
  research each claim, then /verify-report for the final report. Use whenever
  the user says "verify claims", "deep verify", "research the claims", "fact-check",
  "lance la vérification", "launch verification", or wants to start the research
  phase after extracting claims from any document.
---

# Deep Verify

This skill reads claims from `claims.yaml` (produced by `/extract-claims`), launches parallel verification agents, and produces structured JSON verdicts for each claim. Each agent searches the web, cross-references sources, and renders a verdict with confidence score.

## Step 1: Locate and validate claims.yaml

Find `*/claims.yaml` in the current working directory using `Glob`. Read the execution config and the list of claims.

Run the validation script before launching any agents:

```bash
python /path/to/extract-claims/validate_claims.py path/to/claims.yaml
```

If validation fails, display the errors and ask the user to fix them or re-run `/extract-claims`. Do not proceed with invalid input.

Read the execution config from the file:
- `batch_size` — how many agents to run in parallel
- `search_depth` — `quick` or `thorough` (default `quick` for medium claims)
- `model_override` — `haiku` (default) or `sonnet`. Haiku is sufficient for pattern-matching fact-check work and costs ~5x less than Sonnet
- `run_in_background` — `true` (default) for parallel execution and 5-minute prompt cache hits
- `output_dir` — where to write verdict JSON files
- `language` — language for the report (search queries should still be in English)
- `claims_per_agent` — `1` default; can be `2` or `3` for thematic clusters (claims sharing same sources/topic) to amortize agent overhead

Note: accepter le champ `source:` (nouveau) et `prd_source:` (rétrocompatibilité v0) dans claims.yaml.

## Step 1.5: Pre-verify optimization (token efficiency)

Before launching agents, optimize `claims.yaml` to minimize cost. Display proposed changes and apply them by editing the file directly:

1. **Drop `low` claims** — they rarely produce actionable corrections. Either delete them from the YAML or note them as "self-verified" without spawning an agent.
2. **Set `search_depth: "quick"` per-claim for `medium`** — 2 sources are enough for medium-criticality claims; 3 sources should be reserved for `high`.
3. **Detect thematic clusters** — if 2-3 claims share the same topic/sources (e.g. all about same vendor incident, same regulation, same benchmark family), merge them into a single agent call with `claims_per_agent: 2` or `3`. Document cluster mapping in a comment block at the top of `claims.yaml`.

After optimization, display: "Optimized N claims -> M agents to spawn (X high thorough, Y medium quick, Z dropped low, W clusters)."

## Step 2: Resume check

Check if any verdict JSON files already exist in `output_dir`. For each `CLM-XXX.json` that exists and is valid JSON with a `verdict` field, skip that claim. This enables resuming after interruption without re-doing completed work.

Display: "Found N existing verdicts. Skipping: CLM-001, CLM-005, ... Remaining: M claims to verify."

## Step 3: Execute verification agents in batches

Process remaining claims in batches of `batch_size`. For each claim, spawn a subagent using the `Agent` tool.

### Pre-calculating parameters

Before spawning, compute these values for each claim:

- `min_sources`: 3 if `search_depth` is `thorough`, 2 if `quick`
- `output_path`: absolute path to `{output_dir}/{claim_id}.json`
- `agent_config_path`: absolute path to `agent-config-compact.md` (default — embarque OPT-B response brevity et OPT-E compact evidence). Fallback `agents/claim-verifier-agent.md` si version legacy.

### Agent prompt template

**Hard Constraint**: The prompt below must be strictly reproduced for each agent, only replacing the variables in `{xxx}`. Do not modify the structure or wording — consistency across agents is critical for comparable results.

```
## Mission
Vérifier factuellement l'affirmation suivante.

## Configuration
Read the agent instructions at: {agent_config_path}
Schema JSON output, méthode, self-check, response brevity (OPT-B), compact evidence mode (OPT-E) : voir le fichier de config.

## Affirmation
ID: {claim_id}
Texte: "{claim_text}"
Criticité: {claim_criticality} (search_depth: {search_depth}, min_sources: {min_sources})
Impact si fausse: {claim_impact}

## Requêtes suggérées
{search_queries_suggested}

## Output
Écrire JSON à : {output_path}
**RÈGLE STRICTE OPT-K** : UN fichier par claim, nommé EXACTEMENT `CLM-XXX.json` (pas de suffix _verdict, pas de fichier agrégé tels que `verdicts.json`, `verdict.md`, `verification-results.json`). Si tu traites N claims, tu écris N fichiers `CLM-XXX.json` distincts.
Schéma + self-check + interdits explicites : voir agent-config-compact.md section « File path strict ».
```

> **Note**: prompt template raccourci (-50 % vs version pré-OPT-D). Le détail (méthode, schéma JSON, self-check, OPT-B, OPT-E) est dans `agents/claim-verifier-agent.md` ou `agent-config-compact.md`. Le main prompt ne reprend QUE les variables dynamiques.

### One-shot example

For the first batch, include this example at the end of the first agent's prompt to anchor quality expectations:

```
## Example verdict (for reference)

A claim "LightRAG offers 82% better performance than GraphRAG on legal datasets" might produce:

{{
  "claim_id": "CLM-001",
  "claim_text": "LightRAG offers 82% better performance than GraphRAG on legal datasets",
  "verdict": "partially_confirmed",
  "confidence": 0.5,
  "summary": "The 82.54% win rate exists in the LightRAG paper (ArXiv 2410.05779) but is self-reported, uses LLM-as-judge (GPT-4), and no independent reproduction has been published.",
  "evidence": [...],
  "nuances": "The figure exists in the paper but the methodology is debatable. The 82% is a relative win rate, not an absolute 82% precision gain.",
  "recommendation": "Reformulate: 'LightRAG claims a 82% win rate vs GraphRAG on legal datasets (self-evaluation, not independently reproduced). GraphRAG-Bench (2026) nuances these results.'"
}}
```

### Spawning pattern

For each batch:
1. Spawn all agents in the batch simultaneously using multiple `Agent` tool calls in a single message. **Always pass `model: model_override` (default `"haiku"`) and `run_in_background: true`** to keep cost low and enable 5-minute prompt cache reuse across the batch:

   ```javascript
   Agent({
     description: "Verify CLM-XXX",
     subagent_type: "general-purpose",
     model: "haiku",              // from execution.model_override
     run_in_background: true,     // from execution.run_in_background
     prompt: "<rendered prompt template>"
   })
   ```

2. Wait for all agents in the batch to complete
3. Validate each output using `validate_verdict.py`:
   ```bash
   python /path/to/deep-verify/validate_verdict.py path/to/CLM-XXX.json
   ```
4. If a verdict fails validation, log the error but continue (don't block the pipeline)
5. Display progress after each batch

## Step 4: Progress monitoring

After each batch completes, display:

```
Batch N/M complete.
- Verified: CLM-001 (confirmed, 0.85), CLM-002 (contradicted, 0.72), CLM-003 (unverified, 0.3)
- Failed validation: [list if any]
- Remaining: X claims
```

If `batch_size` < total remaining claims, proceed to the next batch automatically (no confirmation needed — the user already approved the scope in the extraction step).

## Step 4.5: Verdict normalization (OPT-J)

Avant le summary final, **toujours** lancer la normalisation des verdicts pour standardiser les variantes non-canoniques produites par les agents Haiku (P2 retour : `VERIFIED`, `PASS`, `FOUND_IN_SOURCES`, etc.) :

```bash
python /path/to/deep-verify/validate_verdict.py --normalize {output_dir}
```

Cette étape :
- mappe `verified`, `pass`, `found_in_sources`, `verified_high` -> `confirmed`
- mappe `verified_partial`, `partially_verified`, `partial` -> `partially_confirmed`
- mappe `not_found`, `no_evidence` -> `unverified`
- mappe `fail`, `false` -> `contradicted`
- mappe `stale`, `expired` -> `outdated`
- gère les préfixes verbeux comme `"PASS — both sub-claims confirmed"` (extraction du premier token)

Permet à `/verify-report` (et OPT-F lecture partielle) de filtrer les verdicts par enum strict via simple grep, sans cas particuliers.

## Step 5: Execution summary

When all batches are done:

```
Verification complete.
- Claims verified: X/Y
- Failed/timeout: Z
- Results in: {output_dir}/

Verdict distribution:
- Confirmed: N
- Partially confirmed: N
- Unverified: N
- Contradicted: N
- Outdated: N

Run /verify-report to generate the confrontation report.
```

## Error handling

- **Agent timeout**: If an agent doesn't respond within 5 minutes, mark the claim as `unverified` with confidence 0.0 and a note explaining the timeout
- **Invalid JSON output**: Run `validate_verdict.py`. If it fails, log the errors, try to fix obvious JSON issues (trailing commas, missing brackets), re-validate. If still broken, skip and note in summary
- **No search results**: The agent should set verdict to `unverified` with an explanation of what was searched and why nothing conclusive was found
- **Rate limiting**: If WebSearch returns rate limit errors, pause 30 seconds between batches

## Output structure

```
{source_name_slug}/
  |-- claims.yaml           # (unchanged, from /extract-claims)
  `-- results/
      |-- CLM-001.json
      |-- CLM-002.json
      `-- ...
```
