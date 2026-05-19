# Compact Verifier Agent Config

Référence courte pour les agents verify quand le prompt main est minimal (OPT-D).

## Méthode
1. Get today's date via `date +%Y-%m-%d`
2. Launch suggested + 1-3 complementary searches
3. Cross-reference ≥ `min_sources` independent sources (3 thorough, 2 quick)
4. Prioritize primary sources: papers, official docs, leaderboards officiels, analyst reports
5. Check publication date
6. Distinguish: verified / estimates / opinions

## ⚠⚠ File path strict (OPT-K) — RÈGLE CRITIQUE

**UN fichier par claim, nommé EXACTEMENT `{output_dir}/CLM-XXX.json`** où `XXX` est le claim_id à 3 chiffres.

**Si l'agent traite 3 claims (ex: CLM-001, CLM-002, CLM-004), il DOIT écrire 3 fichiers :**
- `{output_dir}/CLM-001.json`
- `{output_dir}/CLM-002.json`
- `{output_dir}/CLM-004.json`

**INTERDIT — fichiers agrégés / multi-claims :**
- ❌ `claims_verification.json`
- ❌ `verdicts.json`
- ❌ `verdict.md`
- ❌ `verification-results.json`
- ❌ `verification-report-p1.md`
- ❌ `clm-003-verdict.json` (préfixe lowercase ou suffix interdit)
- ❌ `CLM-001-verdict.json` (suffix interdit)
- ❌ `CLM-001_verdict.json` (suffix interdit)

**OBLIGATOIRE — un fichier `CLM-XXX.json` strict per claim, contenant un objet JSON unique avec `claim_id`, `verdict`, `confidence`, `evidence`, etc.** OPT-F (lecture partielle confirmed) et OPT-J (normalize) DÉPENDENT de ce naming. Le pipeline est cassé sans ça.

**Ne jamais écrire un objet `{"CLM-001": {...}, "CLM-002": {...}}` global. Toujours un fichier per claim_id.**

## Output JSON Schema (par claim, à `{output_path}`)
```json
{
  "claim_id": "CLM-XXX",
  "claim_text": "...",
  "verdict": "confirmed | partially_confirmed | unverified | contradicted | outdated",
  "confidence": 0.0-1.0,
  "summary": "<2-3 phrases>",
  "evidence": [
    {
      "source_url": "<url>",
      "source_type": "academic_paper|industry_report|official_docs|vendor_blog|news|forum",
      "source_date": "YYYY-MM-DD",
      "source_credibility": "high|medium|low",
      "relevant_finding": "<1-2 phrases>",
      "supports_claim": true|false,
      "notes": "<contexte>"
    }
  ],
  "nuances": "<contradictions/contexte manquant>",
  "recommendation": "keep as-is | reformulate with suggestion | remove | add source"
}
```

## ⚠ Verdict enum strict (OPT-G)

**`verdict` DOIT être exactement une des 5 valeurs ci-dessous (lowercase, snake_case) :**
- `confirmed` — sources convergent et supportent la claim
- `partially_confirmed` — claim partiellement vraie ou nuancée
- `unverified` — pas de source fiable trouvée
- `contradicted` — sources convergent contre la claim
- `outdated` — claim était vraie mais ne l'est plus

**Verdicts INTERDITS (causes d'échec validate_verdict.py) :**
- `VERIFIED`, `VERIFIED_PARTIAL`, `partially_verified` (utiliser `confirmed` ou `partially_confirmed`)
- `pass`, `fail`, `ok`, `nok`
- `FOUND_IN_SOURCES`, `NOT_FOUND` (utiliser `confirmed` ou `unverified`)
- Toute valeur en MAJUSCULES (snake_case lowercase obligatoire)

`confidence` DOIT être un nombre flottant entre 0.0 et 1.0 (jamais "HIGH", "MEDIUM", "LOW", null ou texte).

## OPT-I — Early stop sur convergence rapide

Pour `verdict = confirmed` avec `confidence ≥ 0.95` après les **2 premières sources convergentes**, ne pas chercher de 3ᵉ source même si `search_depth = thorough`. Économie ~5k tokens/agent.

Règle : si après 2 sources primaires (leaderboard officiel, doc officielle, paper académique) le score conf ≥ 0.95, écrire le JSON immédiatement.

## Compact Evidence Mode (OPT-E)
Si `verdict == "confirmed"` ET `confidence >= 0.95` : 
- `evidence` array peut être réduit à **1 entrée** (la plus solide)
- `nuances` peut être "" (vide)
- `summary` peut être 1 phrase

Si `verdict in {partially_confirmed, contradicted, unverified, outdated}` :
- `evidence` array doit avoir ≥ `min_sources` entrées
- `nuances` détaillées obligatoires
- `recommendation` actionnable obligatoire

## Self-check JSON
- verdict rempli
- ≥1 evidence (≥min_sources si verdict ≠ confirmed-haute-conf)
- chaque evidence a `source_url`
- confidence cohérente avec verdict
- JSON valide

## Response brevity (OPT-B)
**Après écriture des fichiers JSON, répondre en ≤ 200 caractères :**
```
Wrote N verdicts: CLM-XXX (verdict, conf), CLM-YYY (verdict, conf), ...
```
Pas de résumé verbeux. Pas de tableau. Pas de markdown développé. Le détail est dans les JSONs.
