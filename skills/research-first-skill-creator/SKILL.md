---
name: research-first-skill-creator
description: "Create or update skills for coding workflows with a research-first process, including web browsing and reviewing existing skills in popular public repositories before drafting SKILL.md, scripts, references, or assets."
---

# Research-First Skill Creator

## Workflow
1. Clarify scope with concrete usage examples and desired outcomes.
2. Run research phase before drafting any skill files.
3. Synthesize findings into concise guidance and reusable patterns.
4. Plan reusable resources: scripts, references, and assets.
5. Create or update the skill files.
6. Validate the skill folder.

## Research Phase
- Use web browsing to find current guidance and existing skills in popular public repositories.
- Prefer official or curated sources; verify recency and relevance.
- Capture findings in `references/research-notes.md` using the template in `references/research-notes-template.md`.
- Seed research with `references/default-repos.md` and optionally run `scripts/scaffold_research_notes.py` to prefill sources.
- Record source URLs, dates, and short takeaways. Include what to reuse and what to avoid.

## Synthesis Rules
- Convert research into actionable guidance, not long quotes.
- Extract reusable patterns (workflows, scripts, checklists).
- Identify gaps that need user input (assets, internal docs, examples).

## Build Steps
- Initialize the skill folder using the standard skill structure.
- If the initialization script cannot run, create files manually and keep structure identical.
- Write concise SKILL.md instructions in imperative form.
- Add references and scripts only when they are truly reusable.
- Add `agents/openai.yaml` with `display_name`, `short_description`, and a `default_prompt` that mentions `$research-first-skill-creator`.

## Validation
- Run the validation script if available.
- Fix naming or frontmatter issues before shipping.

## Files
- `references/research-notes.md`: research log for this skill.
- `references/research-notes-template.md`: template to use when creating research notes.
- `references/default-repos.md`: default public repositories to scan.
- `scripts/scaffold_research_notes.py`: generate a starter `research-notes.md` from the template and repo list.
