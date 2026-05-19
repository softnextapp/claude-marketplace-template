# Contributing

Guide pour ajouter ou mettre à jour un plugin dans votre marketplace Claude Cowork.

## Modèle de release

- **Dépôt = source de vérité.** Pas de fichiers `.plugin` zippés commités. Cowork lit directement l'arborescence source du dépôt.
- **Merge sur `main` = release.** Chaque PR mergée déclenche une re-sync Cowork (si « Sync automatically » est activé côté admin). Pas de tag, pas de build CI obligatoire.
- **Versionnage = honor system.** Bumper `version` dans `.claude-plugin/plugin.json` est une bonne pratique pour la traçabilité, mais Cowork ne gate pas les updates — la prochaine sync remplace la version précédente.

## Structure attendue

```
claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json              ← index des plugins
├── <plugin-name>/                    ← un dossier par plugin, à la racine
│   ├── .claude-plugin/
│   │   └── plugin.json               ← manifest du plugin (DANS le sous-dossier)
│   ├── README.md
│   └── skills/
│       └── <skill-name>/
│           └── SKILL.md
├── README.md
└── CONTRIBUTING.md                   ← ce fichier
```

**Règles strictes** (Cowork échoue la sync sinon) :

- Le nom du plugin doit être en **lowercase-with-hyphens** (`my-plugin`, jamais `My-Plugin`).
- `.claude-plugin/plugin.json` doit exister dans chaque dossier de plugin avec au minimum `name`, `version`, `description`.
- Le `source` dans `marketplace.json` doit être un chemin **relatif** à la racine du dépôt (`./my-plugin`).
- Chaque SKILL.md sous `skills/` doit avoir un frontmatter YAML avec `name` et `description`.

## Ajouter un nouveau plugin

1. **Créez le dossier** à la racine, en kebab-case : `my-plugin-a/`, `my-plugin-b/`, etc.
2. **Ajoutez `<plugin>/.claude-plugin/plugin.json`** :
   ```json
   {
     "name": "my-plugin-a",
     "version": "0.1.0",
     "description": "Description en une phrase.",
     "author": { "name": "My Organization" },
     "license": "proprietary"
   }
   ```
3. **Ajoutez vos skills** sous `<plugin>/skills/<skill-name>/SKILL.md` (frontmatter `name` + `description` obligatoires).
4. **Ajoutez un `<plugin>/README.md`** expliquant ce que fait le plugin et comment l'utiliser.
5. **Ajoutez une entrée dans `.claude-plugin/marketplace.json`** :
   ```json
   {
     "name": "my-plugin-a",
     "source": "./my-plugin-a",
     "description": "Même description qu'au-dessus."
   }
   ```
6. **PR → review → merge.** Cowork resync automatiquement.

## Mettre à jour un plugin existant

1. Éditez ce qui doit changer (SKILL.md, templates, scripts).
2. **Bumpez `version`** dans `<plugin>/.claude-plugin/plugin.json` selon SemVer :
   - patch : correction (typo, bug mineur)
   - minor : nouvelle skill, nouveau template
   - major : breaking change pour les utilisateurs
3. PR → review → merge.

## Supprimer un plugin

1. Supprimez le dossier `<plugin>/` complet.
2. Retirez l'entrée correspondante dans `.claude-plugin/marketplace.json`.
3. PR → merge.
4. Cowork retire le plugin du catalogue à la prochaine sync. Les utilisateurs perdent l'accès au prochain refresh de leur session.

## Checklist PR

Avant de demander une review :

- [ ] Le nom du plugin est en kebab-case
- [ ] `<plugin>/.claude-plugin/plugin.json` parse en JSON valide
- [ ] La version est bumpée si du contenu a changé
- [ ] `.claude-plugin/marketplace.json` parse en JSON valide et liste le plugin
- [ ] Chaque SKILL.md modifié a un frontmatter YAML avec `name` et `description`
- [ ] Aucun secret (API key, token) en dur — utiliser les variables d'environnement

La GitHub Action `validate-pr` (voir `.github/workflows/`) lance ces checks automatiquement. Si elle échoue, le merge est bloqué.

## Pourquoi c'est important

Une sync Cowork qui échoue **retire temporairement les plugins de l'UI de l'équipe** jusqu'à ce que la sync suivante réussisse. D'où l'intérêt de la validation pré-merge — c'est l'assurance que `main` est toujours dans un état syncable.

## Référence

- Doc officielle Cowork : https://support.claude.com/en/articles/13837433
- Exemple de structure : https://github.com/anthropics/knowledge-work-plugins
- Reference plugin schema : https://code.claude.com/docs/en/plugins-reference

## Questions

<!-- Remplacez par votre contact admin marketplace. -->
admin@myorg.example
