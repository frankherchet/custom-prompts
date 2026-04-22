---
name: html-presentation-deck
description: Use when the user wants a beautiful, structured HTML presentation generated from an analysis, memo, research note, or slide outline. This skill is for premium standalone slide decks with clear narrative structure, strong visual hierarchy, and reusable style systems, especially when the user wants technical, editorial, BMW-like, OEH-like, or other polished presentation directions.
---

# HTML Presentation Deck

## Overview

This skill turns analysis into a polished HTML slide deck. It is optimized for standalone, keyboard-navigable presentations with strong thesis-driven slides, disciplined visual systems, and style references that help avoid generic AI-slop.

## When To Use This Skill

- The user has a topic analysis, memo, or wiki note and wants slides from it.
- The user wants an HTML deck rather than only markdown bullets.
- The user asks for a beautiful, premium, structured, editorial, technical, BMW-like, or OEH-like presentation.
- The output should be presentation-ready, not just a content dump.

Do not use this skill when the user only wants a plain outline, speaker notes without design, or a PowerPoint-specific artifact without HTML.

## Output Default

- Default to a standalone HTML presentation.
- Each slide should be a separate full-screen section with keyboard navigation.
- Prefer polished CSS tokens, clear layout primitives, and a small amount of meaningful motion.
- When the user wants style variants or comparison directions, prefer one deck with a theme switcher instead of multiple duplicated HTML files.
- Only generate `reveal.js` or `Marp` if the user asks or if the repo already centers those formats.

## Workflow

### 1. Read The Source Analysis First

- Start from the strongest existing analysis, memo, or source note.
- Extract:
  - the core thesis
  - the major claims
  - the natural slide sequence
  - the evidence that anchors the deck
- If the analysis is messy, rewrite the presentation logic before writing any HTML.

### 2. Build The Narrative Before The Design

- A good deck is not "title plus bullets". It is a controlled sequence.
- Default narrative spine:
  1. title / thesis
  2. problem framing
  3. model or system explanation
  4. key distinctions or architecture
  5. practical flow or example
  6. grounding / evidence / close
- Compress aggressively. One slide should carry one real idea.

### 3. Choose A Style Reference Deliberately

Pick exactly one primary style reference unless the user asks for a blend.

- For dark, technical, manifesto-like decks:
  - read `references/oeh-dark-technical.md`
- For premium, cool, BMW-adjacent light decks:
  - read `references/premium-light-blue.md`
- For warm editorial beige decks:
  - read `references/light-beige-editorial.md`

Do not mix all three at once. Use one dominant system.

### 4. Prefer Themeable Architecture When Variants Matter

If the user wants multiple visual directions, comparison views, or an easy style toggle:

- build one HTML deck, not three duplicated decks
- keep slide markup identical across themes
- switch design through root-level CSS custom properties and minimal component overrides
- add a small top-right theme control with an icon or compact button
- persist the chosen theme in `localStorage` when the output is standalone

The preferred mechanism is:

- `document.documentElement.dataset.theme = "theme-name"`
- theme-specific token blocks under `:root[data-theme="..."]`
- one lightweight JS controller for toggle, menu state, and persistence

Use the bundled CSS references as the source of truth for theme tokens:

- `assets/themes/premium-light-blue.css`
- `assets/themes/oeh-dark-technical.css`
- `assets/themes/light-beige-editorial.css`

When the deck topic is technical, architectural, or systems-heavy, the switchable theme set should usually include `oeh-dark` as one of the visible options, not only as a hidden reference.

### 5. Translate The Style Into Concrete Tokens

For every deck, define:

- background color strategy
- ink / muted / line / card / accent tokens
- border radius family
- shadow intensity
- headline font behavior
- monospace usage rules
- grid primitives such as `grid-2`, `grid-4`, `card`, `terminal`, `source`, `chrome`

Use a real system. Do not improvise random CSS per slide.

### 6. Write Slides As Structured Objects

Each slide should usually have:

- eyebrow
- title
- optional subtitle
- one structural content block:
  - two-column layout
  - 4-card stack
  - terminal plus explanation
  - flow strip
  - source grounding block
- footer or progress chrome when appropriate

Avoid:

- bullet soup
- giant centered paragraphs
- decorative gradients with no structural purpose
- 8 different component ideas on one slide
- fake technicality
- generic "innovative / transformative / seamless" phrasing

### 7. Keep The Deck Browsable

- Make the HTML readable in source form.
- Use named CSS classes instead of giant inline style blobs.
- Keep slide order obvious.
- Add keyboard navigation for standalone decks.
- Ensure mobile still loads even if the deck is designed for desktop presentation.
- If a theme switcher is present, keep it compact and non-disruptive during presentation mode.

## Quality Bar

- The deck must feel authored, not autogenerated.
- Slides should have tension, hierarchy, and pacing.
- Headlines should sound like claims, not labels.
- Visual style must match the subject matter.
- A technical deck should look technically intentional.

## Good Trigger Examples

- "Turn this analysis into a beautiful HTML presentation."
- "Build a polished standalone slide deck from this memo."
- "Create a BMW-like presentation from this architecture note."
- "Make a technical dark HTML deck from this analysis."
- "Generate structured HTML slides from this wiki page."

## References

- Style systems:
  - `references/oeh-dark-technical.md`
  - `references/premium-light-blue.md`
  - `references/light-beige-editorial.md`
- CSS theme references:
  - `assets/themes/oeh-dark-technical.css`
  - `assets/themes/premium-light-blue.css`
  - `assets/themes/light-beige-editorial.css`
- Starter asset:
  - `assets/structured-html-deck-template.html`

## Working Rule

Default to editing or creating a real HTML artifact, not just describing one. If the user has already provided analysis, go straight from analysis to deck structure to HTML implementation. When theme variants are relevant, default to one deck with a built-in theme switcher rather than separate duplicated outputs.
