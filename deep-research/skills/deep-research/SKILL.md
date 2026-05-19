---
name: deep-research
description: >
  Conduct systematic deep research on any technical topic by combining web search,
  project/codebase analysis, and AI knowledge into a comprehensive, structured markdown
  referential. Use this skill whenever the user asks to research best practices, build
  a referential, do a deep dive, investigate a technology, compare approaches, or collect
  state-of-the-art knowledge on a subject. Also triggers on: "recherche approfondie",
  "deep search", "deep dive", "best practices", "état de l'art", "benchmark technologies",
  "construire un référentiel", or any request that implies gathering, cross-referencing,
  and synthesizing knowledge from multiple sources into a structured deliverable. Even if
  the user just says something like "I need to understand X thoroughly" or "what are the
  best ways to do Y", use this skill.
---

# Deep Research

You are conducting a deep research process. The goal is to produce a comprehensive,
structured markdown document that synthesizes knowledge from three complementary sources
into a single, actionable referential.

## Why three sources matter

No single source is sufficient:
- **Web search** brings the latest community consensus, official docs, and battle-tested advice — but it's generic and may not fit the user's context.
- **Project/codebase analysis** reveals the conventions already in place — the implicit rules nobody documented. Ignoring them leads to referentials that clash with reality.
- **AI knowledge** fills gaps, resolves contradictions, and provides the structural backbone — but can hallucinate or be outdated without the other two as anchors.

The power is in the cross-referencing: when all three sources agree, you have high confidence. When they disagree, that's where the most valuable insights live.

## The Process

### Phase 1 — Understand the scope

Before researching anything, clarify:
1. **What** is the subject? (e.g., "unit testing best practices", "API security", "CI/CD pipeline design")
2. **What context?** Is there a specific tech stack, framework, or project? If so, which one?
3. **What's the intended use?** A team referential? A personal learning doc? A decision-making comparison?
4. **What depth?** Quick overview (10-15 best practices) or exhaustive referential (50+ rules with examples)?

If the user hasn't specified these, ask briefly. Don't over-interview — make reasonable assumptions and state them.

### Phase 2 — Source 1: Deep web search

Search the web broadly and deeply. This isn't a single query — it's a multi-pass search strategy:

1. **Official documentation** — Start with the official docs for the relevant technology/framework. These are the ground truth.
2. **Community consensus** — Search for guides, tutorials, and articles from recognized sources (e.g., Martin Fowler, ThoughtWorks, major tech blogs, conference talks).
3. **Real-world experience** — Look for postmortems, lessons learned, common mistakes, "things I wish I knew" articles.
4. **Quantitative data** — If relevant, find benchmarks, performance comparisons, adoption statistics.

For each search pass:
- Use multiple search queries with different angles (e.g., "best practices", "common mistakes", "advanced patterns", "production tips")
- Cross-reference findings — if 3+ independent sources agree on a practice, it's high-confidence
- Note disagreements and controversies — these are valuable, not problems to hide

**Search budget (token efficiency)** :
- **Cap général : 8-10 web searches** dans le main context
- **Sujet duo comparatif (X vs Y bien défini, ex: Claude vs GPT) : cap réduit à 5-7 searches** (OPT-H — P2 a montré que 8e search apportait surtout confirmation marginale). Économie ~6k tokens.
- **Sujet large/exploratoire** : cap à 8-10 reste valide.

Chaque search injecte ~2-3k tokens de résultats. Beyond 10 searches, le ratio signal/bruit s'effondre. Pour couverture plus large, déléguer searches additionnelles à un sub-agent qui retourne uniquement sa synthèse — main context reste clean.

**Output cap**: keep the synthesis under **25k characters** (~6k tokens). Anything longer is usually padded — tighten or split by topic.

Organize findings into categories as you go. Don't just dump a list — structure emerges from the research.

### Phase 3 — Source 2: Project/codebase analysis (if applicable)

If the user has a project or codebase available, analyze it:

1. **Identify existing patterns** — What conventions are already in place? What naming patterns, file structures, architectural choices exist?
2. **Extract implicit rules** — The codebase has habits, good or bad. Surface them explicitly.
3. **Measure current state** — If measurable (e.g., test coverage, code complexity, dependency count), get the numbers. They serve as a baseline.
4. **Spot gaps** — What's missing compared to the web research findings?

If no project context is available, skip this phase and note it in the output. The referential is still valuable — it just won't be contextualized.

### Phase 4 — Source 3: AI knowledge synthesis

Contribute your own knowledge:
- Fill gaps that neither web search nor codebase analysis covered
- Provide the conceptual framework that ties everything together
- Add nuance: "this practice is great for small teams but breaks down at scale"
- Flag areas where your knowledge might be outdated (and say so)

### Phase 5 — Consolidation

This is where the magic happens. Merge the three sources into a single, coherent referential:

1. **Deduplicate** — Same advice from multiple sources? Merge into one entry, note the convergence.
2. **Flag contradictions** — When sources disagree, present both sides with context. Don't silently pick one.
3. **Prioritize** — Not all practices are equally important. Organize by impact.
4. **Contextualize** — If project analysis was done, annotate each practice with its current status in the project (already followed / partially followed / not followed / contradicted).
5. **Make it actionable** — Each practice should be specific enough that someone can act on it without further research.

## Output Format

Produce a structured markdown document following this template:

```markdown
# [Subject] — Referential of Best Practices

> **Scope:** [what this covers]
> **Stack:** [relevant technologies, if applicable]
> **Sources:** Web research + [Project analysis | AI knowledge only]
> **Date:** [date of research]
> **Depth:** [number of practices collected]

## Executive Summary

[3-5 sentences: what are the most important takeaways?]

## Table of Contents

[auto-generated from sections]

## Category 1: [Name]

### Practice 1.1 — [Short title]

**Priority:** [Critical | Important | Recommended | Nice-to-have]
**Confidence:** [High (3+ sources agree) | Medium (2 sources) | Low (single source or AI-only)]

[Description of the practice — what it is, why it matters]

**Example:**
[Concrete code snippet or configuration example when relevant]

**Project status:** [Already followed | Partially followed | Not followed | N/A]

### Practice 1.2 — [Short title]
...

## Category 2: [Name]
...

## Contradictions and Open Questions

[List any cases where sources disagreed, with context for each side]

## Sources

[List the key sources consulted, grouped by type]
```

Adapt this template to the subject — not every field makes sense for every topic. The structure should serve the content, not the other way around.

## Important Guidelines

- **Be honest about confidence levels.** A practice backed by official docs + community consensus + your own knowledge is high-confidence. A practice you found in one blog post is low-confidence. Say so.
- **Don't pad.** If you found 12 solid practices, don't stretch to 20 with filler. Quality over quantity.
- **Include the "why".** For each practice, explain why it matters — not just what to do. People follow advice better when they understand the reasoning.
- **Make contradictions visible.** When the web says one thing and the existing codebase does another, that's the most actionable finding. Highlight it.
- **Stay practical.** The output should be something a developer can pin to their wall (metaphorically) and reference daily. Avoid academic abstractions.
- **Cite your sources.** When a practice comes from a specific article or doc, say so. This lets the user dig deeper if they want.
