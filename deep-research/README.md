# deep-research

Skill de recherche approfondie multi-sources qui produit un **référentiel markdown structuré** sur n'importe quel sujet technique ou métier.

## Objectif

Combiner trois sources de connaissance — recherche web, analyse du projet courant et knowledge interne — pour générer un référentiel organisé, sourcé et directement exploitable. Le référentiel peut ensuite alimenter le pipeline de fact-checking via le plugin `fact-check`.

## Pré-requis

- Accès web actif (outils `WebSearch` et `WebFetch`)
- Aucune dépendance Python, aucune clé API spécifique

## Modes de profondeur

| Mode | Recherches web | Contenu produit |
|------|---------------|-----------------|
| `quick` | 5-7 requêtes | 10-15 best practices, survol rapide |
| `deep` | 8-10 requêtes + cross-ref | 50+ règles, références académiques, comparaisons |

## Exemple d'usage

```
Utilise le skill deep-research pour faire une recherche approfondie sur la sécurité des webhooks.
Profondeur : deep. Fichier de sortie : ./securite-webhooks/referentiel.md
```

## Sortie

Un fichier `referentiel.md` structuré avec :
- Résumé exécutif
- Sections thématiques avec règles numérotées
- Sources et références pour chaque assertion
- Glossaire si pertinent

## Utilisation dans un pipeline

Ce skill est conçu pour être enchaîné avec le plugin `fact-check` :

1. `deep-research` → produit `referentiel.md`
2. `extract-claims` (plugin `fact-check`) → extrait les assertions vérifiables
3. `deep-verify` + `verify-report` → vérifie et produit le rapport final

Ou via l'orchestrateur `research-and-verify` (plugin dédié) qui enchaîne tout automatiquement.
