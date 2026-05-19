# research-and-verify

Orchestrateur **non-interruptif** du pipeline complet `deep-research` + `fact-check`. Une seule interview de 6 questions, puis exécution automatique des 4 phases jusqu'au rapport final.

## Objectif

Produire un référentiel thématique factuel et vérifié en une seule commande, sans interruption entre les phases. Conçu pour les sujets techniques ou métier où la fiabilité des sources est critique.

## Pré-requis CRITIQUES

Ce plugin orchestre des skills provenant de deux autres plugins. Les deux doivent être installés :

- Plugin **`deep-research`** — fournit le skill `/deep-research` (phase 1)
- Plugin **`fact-check`** — fournit les skills `/extract-claims`, `/deep-verify`, `/verify-report` (phases 2-4)

Sans ces deux plugins installés, le pipeline échouera en phase 1 ou 2.

Autres pré-requis :
- Accès web actif (`WebSearch`, `WebFetch`)
- Outil `Agent` disponible (pour les agents de vérification parallèles)

## Interview à 6 questions

Au démarrage, le wrapper collecte une seule fois :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `$subject` | Sujet de la recherche (slug du dossier de sortie) | — |
| `$context` | Contexte / stack / projet (optionnel) | vide |
| `$depth` | Profondeur (`quick` ou `deep`) | `deep` |
| `$max_claims` | Nombre max de claims à extraire (1-25) | 20 |
| `$threshold` | Filtre du rapport (`all`, `confirmed-only`, `high-confidence-only`) | `all` |
| `$outdir` | Dossier de sortie | `$CWD/<slug>/` |

## Garantie non-interruptive

Une fois l'interview et la question de pré-vol (overwrite / resume / abort) répondues, **le pipeline s'exécute jusqu'à la fin sans aucune question supplémentaire** sur le chemin nominal. Seules des erreurs réelles (fichier de sortie manquant, 0 claims extraits, verdicts partiels) peuvent interrompre.

> « There is no editorial gate between extraction and verification. »

Si tu veux éditer `claims.yaml` à la main avant la vérification : interrompre, éditer, relancer avec `resume` — les phases déjà complétées seront sautées.

## Sorties produites

```
$outdir/
  |-- referentiel.md          # Phase 1 : deep-research
  |-- claims.yaml             # Phase 2 : extract-claims
  |-- verdicts/
  |   |-- CLM-001.json        # Phase 3 : deep-verify
  |   `-- CLM-XXX.json
  |-- report.md               # Phase 4 : verify-report (filtré par $threshold)
  `-- prompt-retour.md        # Optionnel : si session lourde (deep + max_claims >= 20)
```

## Exemple d'usage

```
Lance research-and-verify sur le sujet "sécurité des webhooks".
```

Le wrapper pose ses 6 questions, puis enchaîne automatiquement les 4 phases.

## Reprise après interruption

```
Lance research-and-verify — outdir existant : ./securite-webhooks/
Choisir : resume
```

Les phases dont la sortie existe déjà sont sautées. La vérification reprend là où elle s'est arrêtée.
