# fact-check

Pipeline de **fact-checking générique en 3 étapes** pour valider les assertions factuelles de n'importe quel document ou texte.

## Objectif

Extraire les claims vérifiables d'un document, les soumettre à une vérification multi-sources via des agents parallèles, puis produire un rapport de confrontation actionnable.

## Inputs acceptés

Le skill `extract-claims` accepte trois modes d'entrée :

**Chemin de fichier** (Mode A) :
```
Lance extract-claims sur le fichier ./mon-rapport.md
```
Formats supportés : `.md`, `.txt`, `.pdf`, `.docx`, `.pptx`.
Pour `.pptx`, recommander le plugin marketplace `pptx` ou installer `python-pptx` (`pip install python-pptx`).

**Texte brut passé en paramètre** (Mode B) :
```
Lance extract-claims sur ce texte : "Notre solution réduit les coûts de 40%
et le marché adressable est de 2,5 milliards d'euros en 2024."
```
Le YAML de sortie contiendra `source: "inline-text"` et un `source_excerpt` pour la traçabilité.

**Auto-discovery** (Mode C) : sans input, le skill scanne le répertoire courant et demande confirmation.

## Pré-requis

- Accès web actif (outil `WebSearch`) pour la phase de vérification
- Outil `Agent` disponible pour le lancement des agents parallèles
- Pour les fichiers `.pptx` : plugin `pptx` du marketplace ou `python-pptx`

## Skills inclus

| Skill | Étape | Rôle |
|-------|-------|------|
| `extract-claims` | 1 | Extrait les assertions vérifiables → `claims.yaml` |
| `deep-verify` | 2 | Lance des agents de vérification en parallèle → `CLM-XXX.json` |
| `verify-report` | 3 | Confronte les verdicts et génère `report.md` |

## Workflow complet

```
1. /extract-claims   → éditer claims.yaml si souhaité (optionnel)
2. /deep-verify      → agents lancés en parallèle (haiku par défaut)
3. /verify-report    → rapport markdown final
```

Chaque étape peut être relancée indépendamment (reprise sur `resume`).

## Note sur l'usage combiné

Ce plugin peut être utilisé seul (étapes manuelles) ou orchestré par le plugin `research-and-verify` qui enchaîne `deep-research` + les 3 étapes de `fact-check` en une session non-interruptive.
