# Setup — Personnaliser le template pour votre organisation

Vous venez de créer un repo depuis ce template. Suivez ces étapes **dans l'ordre** pour aboutir à une marketplace privée Cowork opérationnelle.

Durée totale : ~15 minutes.

---

## 1. Personnaliser les métadonnées (5 min)

### `.claude-plugin/marketplace.json`

- `name` : nom de votre marketplace en kebab-case, ex. `myorg-marketplace`.
- `owner.name` : nom lisible de votre organisation, ex. `MyOrg`.
- `owner.email` : adresse de contact admin marketplace.

### `README.md`

- Remplacer toutes les occurrences de `My Organization` / `myorg` par le nom réel de votre organisation.
- Adapter la liste des plugins si vous en retirez (cf. étape 2).

### `CONTRIBUTING.md`

- Remplacer `admin@myorg.example` en bas de fichier par votre adresse contact.

---

## 2. Choisir vos plugins d'exemple (5 min)

3 plugins d'exemple sont fournis. Ils utilisent **uniquement** le `WebSearch` / `WebFetch` natifs de Claude — zéro MCP, zéro API key, zéro Python. Ils marchent immédiatement.

Vous pouvez :

- **Tous les garder** (recommandé pour démarrer — utiles à toute organisation).
- **En retirer** : `rm -rf <plugin-name>` puis retirer l'entrée correspondante dans `.claude-plugin/marketplace.json`.
- **Les modifier** : éditer les `SKILL.md`, bumper la version dans `<plugin>/.claude-plugin/plugin.json`.

---

## 3. Valider en local (1 min)

```bash
python scripts/validate_marketplace.py
```

Critère de succès : `PASSED: marketplace is sync-ready`.

Si rouge, corriger les erreurs listées (typiquement : nom de dossier ≠ entrée `marketplace.json`, JSON mal formé, frontmatter SKILL manquant).

---

## 4. Commit initial + push (2 min)

```bash
git add .
git commit -m "init: customize marketplace for <VotreOrg>"
git push origin main
```

Vérifier que la GitHub Action **`validate-pr`** passe au vert sur ce premier push (onglet **Actions**).

---

## 5. Connecter à Cowork (5 min)

À faire **une seule fois**, par un **Owner** ou **Primary Owner** du plan Team / Enterprise :

1. Vérifier que **Cowork** et **Skills** sont activés pour l'organisation Claude.
2. Installer l'app GitHub **Claude** sur le dépôt que vous venez de créer : `Settings > GitHub Apps > Claude > Configure > sélectionner le dépôt`.
3. Dans Cowork : **Organization settings > Plugins > Add plugin > GitHub**.
4. Saisir `<votre-org>/<nom-du-repo>`.
5. Attendre la première sync, puis ouvrir le menu de la marketplace et activer **Sync automatically**.

À partir de là, chaque merge sur `main` déclenche une re-sync Cowork automatique.

Pour chaque plugin, configurer la préférence d'installation (**Installed by default** / **Available for install** / **Required** / **Not available**) dans **Organization settings > Plugins**.

---

## 6. Protéger `main` (1 min)

Pour empêcher tout push direct qui casserait la sync Cowork :

1. **Settings > Branches > Add branch protection rule** sur `main`.
2. Cocher **Require a pull request before merging** et **Require status checks to pass** (sélectionner `validate-pr`).

---

## Checklist finale

- [ ] `marketplace.json` ne contient plus `My Organization` / `admin@myorg.example`.
- [ ] `README.md` ne contient plus `My Organization`.
- [ ] `CONTRIBUTING.md` a une vraie adresse contact.
- [ ] Le validator passe en local (`PASSED: marketplace is sync-ready`).
- [ ] La GitHub Action `validate-pr` passe sur la première PR de baseline.
- [ ] La marketplace est connectée à Cowork et les plugins apparaissent dans **Browse plugins**.
- [ ] La protection de branche `main` est activée.

---

Une fois ces étapes franchies, voir [`CONTRIBUTING.md`](./CONTRIBUTING.md) pour le workflow d'ajout de vos propres plugins métier.
