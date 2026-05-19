# Claude Cowork Marketplace — Template

Repo template pour créer rapidement une **marketplace privée Claude Cowork** pour votre organisation.

Cliquez sur **Use this template** en haut à droite pour bootstrapper votre propre marketplace en 30 secondes, puis suivez [`SETUP.md`](./SETUP.md) pour la personnaliser.

## Comment l'utiliser

1. Cliquez sur **Use this template** → **Create a new repository**.
2. Créez un repo **privé** dans votre organisation (ex. `myorgapp/claude-marketplace`).
3. Clonez-le localement et suivez [`SETUP.md`](./SETUP.md) pour personnaliser et connecter à Cowork.

## Ce que vous obtenez

- Structure de marketplace conforme aux contraintes Cowork (un dossier par plugin, `marketplace.json` à la racine, conventions kebab-case).
- **3 plugins d'exemple opérationnels** — `deep-research`, `fact-check`, `research-and-verify`. Ils utilisent uniquement le web search natif de Claude, **aucune dépendance externe** (zéro MCP, zéro API key, zéro Python).
- **Linter PR** (validator Python + GitHub Action `validate-pr`) déjà câblé. Toute PR non conforme est bloquée avant merge — votre `main` reste toujours dans un état syncable par Cowork.
- `README.md` + `CONTRIBUTING.md` déjà rédigés, à personnaliser.

## Pré-requis

- Plan **Claude Team ou Enterprise** avec Cowork activé pour votre organisation.
- Une **organisation GitHub** où vous êtes Owner (pour créer le repo et y installer l'app GitHub Claude).

## Plugins d'exemple inclus

| Plugin | Description |
|---|---|
| **[deep-research](./deep-research)** | Recherche approfondie 3-sources (web + projet + knowledge) produisant un référentiel markdown structuré. |
| **[fact-check](./fact-check)** | Pipeline générique extract-claims → deep-verify → verify-report pour vérifier les assertions d'un document. |
| **[research-and-verify](./research-and-verify)** | Orchestrateur qui chaîne deep-research + fact-check end-to-end. Exemple de plugin composé. |

Vous pouvez tous les garder, en retirer, ou les modifier après duplication — cf. `SETUP.md`.

## Contribuer

Une fois la marketplace personnalisée, voir [`CONTRIBUTING.md`](./CONTRIBUTING.md) pour le workflow d'ajout / mise à jour de plugin.

## License

Apache 2.0 — voir [`LICENSE`](./LICENSE).

Les `plugin.json` individuels gardent `"license": "proprietary"` car c'est la valeur par défaut côté plugin ; vous pouvez librement la changer si vous redistribuez vos propres plugins.
