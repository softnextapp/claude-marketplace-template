# Setup — Personnaliser le template pour votre organisation

Vous venez de créer un repo depuis ce template. Suivez ces étapes **dans l'ordre** pour aboutir à une marketplace privée Cowork opérationnelle.

Durée totale : **~25 minutes**.

> ⚠️ **Ne pas activer la protection de branche `main` avant l'étape 7.** L'étape 5 fait un push direct sur `main` qui serait bloqué sinon.

---

## 1. Réécrire le README.md (10 min)

Le `README.md` actuel décrit **ce template**, pas votre marketplace. **Remplacez-le intégralement** par une version qui parle à votre équipe. Modèle minimal :

```markdown
# <VotreOrg> Marketplace

Marketplace privée <VotreOrg> pour les plugins Claude Cowork. Ce dépôt contient le code source des plugins distribués à l'équipe via Cowork.

## Pour l'équipe — Comment installer les plugins

1. Ouvrir Claude Cowork.
2. **Browse plugins**.
3. Cliquer **Install** sur les plugins <VotreOrg>.

## Plugins

| Plugin | Description |
|---|---|
| **[deep-research](./deep-research)** | … |
| **[fact-check](./fact-check)** | … |
| **[research-and-verify](./research-and-verify)** | … |

## Contribuer

Voir [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Support

admin@votreorg.example
```

Adaptez la table des plugins selon ceux que vous gardez (étape 3).

---

## 2. Personnaliser `.claude-plugin/marketplace.json` (2 min)

- `name` : nom de votre marketplace en kebab-case, ex. `votreorg-marketplace`.
- `owner.name` : nom lisible de votre organisation.
- `owner.email` : adresse de contact admin marketplace.

---

## 3. Personnaliser `CONTRIBUTING.md` (2 min)

Tout en bas du fichier, sous `## Questions`, **supprimer le commentaire HTML** `<!-- Remplacez par votre contact admin marketplace. -->` et remplacer `admin@myorg.example` par votre adresse contact réelle.

Optionnel : remplacer les exemples `my-plugin-a` / `my-plugin-b` / `My Organization` dans le corps du fichier par des exemples qui parlent à votre équipe.

---

## 4. Choisir vos plugins d'exemple (3 min)

3 plugins d'exemple sont fournis. Ils utilisent **uniquement** le `WebSearch` / `WebFetch` natifs de Claude — zéro MCP, zéro API key, zéro Python. Ils marchent immédiatement.

Vous pouvez :

- **Tous les garder** (recommandé pour démarrer).
- **En retirer** : `rm -rf <plugin-name>` puis retirer l'entrée correspondante dans `.claude-plugin/marketplace.json`.
- **Les modifier** : éditer les `SKILL.md`, bumper la version dans `<plugin>/.claude-plugin/plugin.json`.

---

## 5. Valider en local + commit + push initial (3 min)

```bash
python scripts/validate_marketplace.py
# Doit afficher : PASSED: marketplace is sync-ready

# Supprimer ce SETUP.md (il n'a plus d'utilité une fois la perso faite)
rm SETUP.md

git add .
git commit -m "init: customize marketplace for <VotreOrg>"
git push origin main
```

Vérifier que la GitHub Action **`validate-pr`** passe au vert sur ce push (onglet **Actions**).

---

## 6. Connecter à Cowork (5 min)

À faire **une seule fois**, par un **Owner** ou **Primary Owner** du plan Team / Enterprise :

1. Vérifier que **Cowork** et **Skills** sont activés pour l'organisation Claude.
2. Installer l'app GitHub **Claude** sur ce dépôt : `Settings > GitHub Apps > Claude > Configure > sélectionner le dépôt`.
3. Dans Cowork : **Organization settings > Plugins > Add plugin > GitHub**.
4. Saisir `<votre-org>/<nom-du-repo>`.
5. Attendre la première sync, puis ouvrir le menu de la marketplace et activer **Sync automatically**.

Pour chaque plugin, configurer la préférence d'installation (**Installed by default** / **Available for install** / **Required** / **Not available**) dans **Organization settings > Plugins**.

---

## 7. Activer la protection de `main` (1 min)

**Maintenant seulement**, pour empêcher tout push direct ultérieur qui casserait la sync Cowork :

1. **Settings > Branches > Add branch protection rule** sur `main`.
2. Cocher **Require a pull request before merging** et **Require status checks to pass** (sélectionner `validate-pr`).

---

## Checklist finale

- [ ] `README.md` réécrit, ne parle plus de "template" ni de "Use this template".
- [ ] `marketplace.json` : `name`, `owner.name`, `owner.email` personnalisés.
- [ ] `CONTRIBUTING.md` : commentaire HTML retiré, contact admin réel renseigné.
- [ ] `validate_marketplace.py` → `PASSED: marketplace is sync-ready`.
- [ ] `SETUP.md` supprimé du repo.
- [ ] GitHub Action `validate-pr` verte sur le push initial.
- [ ] Marketplace connectée à Cowork ; les plugins apparaissent dans **Browse plugins**.
- [ ] Protection de branche `main` activée avec `validate-pr` en status check requis.

---

Une fois ces étapes franchies, voir [`CONTRIBUTING.md`](./CONTRIBUTING.md) pour le workflow d'ajout de vos propres plugins métier.
