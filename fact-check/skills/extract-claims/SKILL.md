---
name: extract-claims
allowed-tools: Read, Write, Glob, AskUserQuestion
description: >
  Extract verifiable factual claims from any document or text snippet (PRD, slides, article,
  rapport, brief, doc technique, ou texte brut passé en paramètre) and generate a structured
  claims.yaml for deep verification. Use when the user wants to fact-check a document, verify
  the claims in a deck or article, validate the factual basis of any written content, or check
  whether numbers, benchmarks, market data, and technical assertions hold up. Also triggers when
  the user mentions "fact-check ce document", "vérifie ces slides", "verify claims",
  "check the numbers", "are these benchmarks real", "validate assumptions", or wants to know if
  a document's assertions hold up against external evidence. This skill is the first step in a
  3-skill pipeline: extract claims here, then /deep-verify to research them,
  then /verify-report for the final confrontation report.
---

# Claim Extraction

This skill reads a source document (or accepts inline text) and extracts every factual assertion that can be verified against external sources. The output is a structured `claims.yaml` that feeds into `/deep-verify` for deep research.

This is fundamentally different from `/review-prd` which checks internal consistency and structure. This skill identifies claims about the *outside world* — benchmarks, market data, competitor existence, technical limitations — that need to be checked against reality.

## Step 0: Load the source

Three input modes are accepted:

**Mode A — Chemin de fichier** : lire le fichier indiqué. Formats acceptés : `.md`, `.txt`, `.pdf`, `.docx`, `.pptx`. Pour `.pptx`, extraire le texte de chaque slide (bullets + speaker notes) via le skill `pptx` du marketplace ou via `python-pptx`. Si l'input est un `.pptx` avec très peu de texte par slide, considérer les bullets et speaker notes comme le contenu textuel à analyser.

**Mode B — Texte brut** : si l'utilisateur passe directement du contenu en paramètre (string), l'utiliser tel quel sans Read tool. Conserver `source: "inline-text"` dans le YAML et ajouter un champ `source_excerpt:` avec les 200 premiers caractères pour traçabilité.

**Mode C — Auto-discovery** : si aucun input n'est fourni, utiliser `Glob` pour trouver les fichiers candidats dans le répertoire courant (`*.md`, `*.txt`, `*.pdf`, `*.docx`, `*.pptx`). Demander à l'utilisateur de confirmer lequel analyser.

Read the entire source. If it spans multiple files, read all of them. Also read any referenced context files since they may contain additional verifiable claims.

## Step 1: Extract claims

Analyze every section of the source and identify assertions that make factual statements about the world outside the project. For each candidate, ask: "Could someone with internet access check whether this is true?"

### What to extract

Statements that:
- **Cite numbers**: benchmarks, percentages, latencies, throughput, costs, sizes
- **Describe the market**: TAM/SAM/SOM, growth rates, market share, competitive landscape
- **Assert existence or absence**: "no open-source competitor exists", "this API supports X"
- **Reference external work**: papers, reports, standards, frameworks (whether cited or not)
- **Make technical claims**: performance characteristics, compatibility, limitations, feasibility
- **Include temporal assertions**: "since 2024", "industry standard since", "current trend"
- **Describe costs or pricing**: infrastructure costs, API pricing, licensing models
- **Claim user behavior**: adoption rates, usage patterns, survey results

### What NOT to extract

- Internal project decisions ("we chose React for the frontend")
- Effort estimates ("this will take 3 sprints") — unless they're based on external benchmarks
- Naming choices, code conventions, team structure
- Opinions explicitly framed as such ("we believe", "our hypothesis is")
- Aspirational goals that don't claim factual backing

Log excluded items as `internal_decision` in your extraction notes — this helps the user understand what was considered and rejected.

### Calibration guidelines

The goal is to extract enough claims to be thorough without drowning the user in noise:
- **Target range**: adaptatif selon la taille de l'input (~3-5 claims par page A4 équivalent, ou ~1-2 claims par slide dense). Plancher: 3 claims. Plafond: 25.
- **Noise ceiling**: if you're extracting more than 5 `low`-criticality claims per page, you're being too aggressive — raise your threshold
- **Hard cap**: 25 claims maximum. If extraction exceeds this, keep only `high` + `medium`, sorted by descending impact
- **Distribution target**: 5-8 `high`, 8-12 `medium`, 0-2 `low` max. Verification of `low` claims rarely produces actionable corrections; prefer dropping them.
- **Minimum threshold**: si l'input est très court (1-2 paragraphes, 1-2 slides) et yields fewer than 2 claims, alerter l'utilisateur : "Ce document a peu de claims factuels vérifiables — confirme que tu veux quand même lancer la vérification."

### Filtrage par criticité (token efficiency)

Verification cost grows linearly with claim count. Apply this policy at extraction time:

| Criticality | Default action | search_depth | Rationale |
|-------------|---------------|--------------|-----------|
| `high` | Verify with agent | `thorough` (3 sources min) | Structural decisions ride on these |
| `medium` | Verify with agent | `quick` (2 sources min) | Localized adjustments only |
| `low` | **Skip or drop** | n/a | Verification rarely produces corrections worth the tokens |

Set `search_depth` per claim if needed (override at claim level supersedes execution default). Drop `low` claims unless the user explicitly asks otherwise. Document this in the handoff message.

### Search queries

For each claim, generate 3-5 search queries that an agent could use to verify it. Think about:
- The most direct search for the specific fact
- Alternative phrasings that might surface different sources
- Searches for the cited source itself (paper title, report name)
- Searches for contradicting evidence ("X limitations", "X vs Y comparison")

These queries are not final — the verification agent will generate more — but they give it a strong starting point.

## Step 2: Classify each claim

For every extracted claim, determine:

### Category

| Category | What it covers | Default research module |
|----------|---------------|----------------------|
| `technical_performance` | Benchmarks, latency, throughput, perf numbers | `academic-and-technical` |
| `technical_feasibility` | Compatibility, limitations, whether X can do Y | `academic-and-technical` |
| `market_sizing` | TAM/SAM/SOM, market projections, growth rates | `market-and-industry` |
| `competitive_landscape` | Competitors, positioning, market share | `market-and-industry` |
| `cost_estimate` | Infrastructure costs, pricing, economic models | `market-and-industry` |
| `citation_verification` | References to specific papers, reports, standards | `academic-and-technical` |
| `standard_compliance` | Regulatory requirements, certifications, norms | `official-sources` |
| `temporal_claim` | "Since 2024", "trend since", historical assertions | _(depends on subject)_ |
| `user_behavior` | Adoption rates, usage patterns, survey data | `community-and-terrain` |
| `regulatory` | Legal requirements, compliance mandates | `official-sources` |
| `architectural_claim` | Architecture justifications based on external facts | `academic-and-technical` |

### Criticality

| Level | When to assign it | What it means if the claim is false |
|-------|------------------|-------------------------------------|
| `high` | The claim structures a go/no-go decision, architecture choice, or business model | The document's foundation is shaky |
| `medium` | The claim influences a design choice or prioritization | A localized adjustment is needed |
| `low` | The claim is contextual, illustrative, or secondary | Credibility dip but no structural damage |

## Step 2.5: Cluster detection (OPT-C — token efficiency)

Avant de présenter les claims à l'utilisateur, détecter automatiquement les clusters thématiques. Heuristique simple :

1. Pour chaque paire de claims, calculer overlap des `search_queries_suggested` (mots-clés communs >= 2) ou même domaine de source primaire attendu.
2. Si overlap >= 2 mots-clés OU même catégorie + même source attendue : claims dans le même cluster.
3. Assigner un identifiant de cluster (A, B, C, ...) à chaque claim via le champ `cluster:`.

Ajouter à chaque claim dans `claims.yaml` :
```yaml
- id: "CLM-001"
  ...
  cluster: "A"  # claims A001, A002, A003 vérifiés par 1 seul agent
```

Cette annotation permet à `/deep-verify` (Step 1.5) de regrouper les claims du même cluster en 1 seul Agent call avec `claims_per_agent: N`. **Gain typique : -50 % nombre d'agents** sur les pipelines avec sources convergentes (benchmarks, leaderboards, rapports d'analystes).

## Step 3: Review with the user

Present a summary via `AskUserQuestion`:

1. **Extraction summary**: total claims found, breakdown by category and criticality
2. **Ask these questions**:
   - "I found N verifiable claims. Want to add or remove any?" (free text input)
   - "Which claims should we verify?" — options: All / High only / High + Medium
   - "How deep should the research go?" — options:
     - **Quick** (3 queries/claim, 2 sources minimum — faster, cheaper)
     - **Thorough** (8-10 queries/claim, 3 sources minimum — more reliable)
   - "How many verification agents to run in parallel?" (default: 3)

Apply the user's choices: filter claims by scope, set the execution config.

## Step 4: Write claims.yaml

Create a directory named after the source (slugified) and write `claims.yaml`:

```yaml
# claims.yaml
source: "path/to/the-document.md"   # ou "inline-text" si Mode B
source_excerpt: "..."               # 200 premiers caractères si inline-text (sinon omis)
extraction_date: "YYYY-MM-DD"
execution:
  batch_size: 3              # agents in parallel
  search_depth: "quick"      # thorough | quick — default quick for medium claims
  model_override: "haiku"    # haiku | sonnet — default haiku for verification (-80% cost)
  run_in_background: true    # parallel execution + 5min prompt cache
  output_dir: "./results"
  language: "fr"             # match the source's language
  claims_per_agent: 1        # 1 default; allow 2-3 for thematic clusters
  max_claims: 25

claims:
  - id: "CLM-001"
    text: "The exact claim text from the source"
    location: "section X, paragraph Y"  # ou "slide N" pour .pptx
    category: "technical_performance"
    criticality: "high"
    impact: "Why it matters if this is false"
    research_module: "academic-and-technical"
    cluster: "A"
    search_queries_suggested:
      - "first search query"
      - "second search query"
      - "third search query"
```

**Note — Breaking change v0.1** : le champ `prd_source:` a été renommé `source:` pour refléter le caractère générique du skill. Les pipelines qui lisaient `prd_source:` doivent être mis à jour.

**ID format**: `CLM-001`, `CLM-002`, etc. — sequential, zero-padded to 3 digits.

**Language**: Set `execution.language` to match the source's language. Claims text should be in the source's original language; search queries should be in English (most research sources are in English) unless the claim is specifically about non-English content.

## Step 5: Validate

Run `validate_claims.py` on the generated file:

```bash
python /path/to/extract-claims/validate_claims.py path/to/claims.yaml
```

If validation fails, fix the issues and re-validate. The validation script checks:
- All required fields present on every claim
- Valid categories and criticality levels
- Unique claim IDs
- At least 1 search query per claim
- Total claims within the hard cap
- Consistent execution config

## Step 6: Hand off

Tell the user:

> Claims extracted and validated: N claims (X high, Y medium, Z low).
> Results saved to `{slug}/claims.yaml`.
>
> Next step: run `/deep-verify` to launch verification agents.

---

## Exemple (extrait de PRD — vaut aussi pour un slide, un paragraphe d'article, etc.)

**Source excerpt:**
> "Our system will use LightRAG for retrieval, which offers 82% better performance than GraphRAG on legal datasets (source: LightRAG paper, HKU 2024). Estimated cost is $0.02/query. The legal-tech RAG market is worth $1.8B and growing at 34% annually."

**Extracted claims:**

| ID | Claim | Category | Criticality |
|-----|-------|----------|------------|
| CLM-001 | LightRAG offers 82% better performance than GraphRAG on legal datasets | `technical_performance` | `high` |
| CLM-002 | Cost of $0.02 per query for LightRAG-based retrieval | `cost_estimate` | `medium` |
| CLM-003 | Legal-tech RAG market is worth $1.8B | `market_sizing` | `medium` |
| CLM-004 | Legal-tech RAG market growing at 34% annually | `market_sizing` | `medium` |

Note how the single source paragraph yielded 4 distinct verifiable claims. Each will be researched independently because they need different sources and have different verification strategies.
