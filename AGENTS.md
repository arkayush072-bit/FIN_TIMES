# Threshold — agent playbook

A static, design-first site for a residential real estate agent. One
page, no backend, no build step. Everything an owner asks for is an
edit to `public/index.html` followed by a deploy.

## Files

- `public/index.html` — the one-page site (hero → featured listings +
  sold strip → stats/about → buyers & sellers → neighborhood notes →
  testimonials → contact/fine print).

## Theme

All colors live in the `:root` token block at the top of `<style>`.
The page is warm white (`--cream`) with charcoal text (`--ink`);
`--umber` is the single accent (kickers, badges, step numerals,
rules) — change it once to re-tune the site. `--umber-soft` is its
lighter twin used only on the dark hero; keep them in the same family.

Fonts are Marcellus (display) + Inter (text) via Google Fonts.
Marcellus ships ONE weight (400) and no italic — never bold or
italicize it; `em` inside headings renders as accent color instead.
Swap the `<link>` and the `--display`/`--sans` tokens together.

## Images

Five slots, all absolute URLs (search "storage/sites/threshold" to
find every one): the hero CSS background in `.hero-bg` (16:9), three
listing photos (4:3 `<img>` inside `.card-media`), and the agent
portrait (3:4 in `.about-photo`). Every slot has a solid fallback
color (`--photo-fallback`) so a missing image never breaks the
composition. Replace by uploading the owner's photos and swapping
the references.

## Common asks

- **Listings** — each is a `.card` in `#listings`: street name in
  `<h3>`, one-line character in `.card-line`, specs and price in
  `.spec-row` (price is the `.price` span). "In contract" is the
  `.badge` span inside `.card-media`; add or remove it per card.
  Closed sales move to the one-line `.sold-strip` under the grid.
- **Phone / email** — the number appears in FOUR places (nav pill,
  hero-sub, contact button, footer); the email in two (contact,
  footer). Grep for the old value and update all of them.
- **Stats** — the `.stats` strip in `#about`: big numeral in `<b>`,
  label in `<span>`. Keep four cells or the grid re-flows oddly.
- **Rename / rebrand** — wordmark in nav + footer, `<title>`/OG tags,
  the favicon SVG letter, and the brokerage fine print (`.fineprint`)
  with agent name and license number.
- **New section** — copy an existing `<section>` shell and keep the
  `.reveal` class so the scroll animation applies.

## Constraints

- Keep it static. No frameworks, no IDX/MLS widgets, no contact
  forms — inquiries are a phone call or email by design.
- Don't inline new web-font `@import`s inside `<style>`; use `<link>`
  tags in `<head>` (faster, and the deploy linter prefers it).
- Preserve `prefers-reduced-motion` handling if you touch animations.
- The fine print (brokerage, license number, Equal Housing
  Opportunity) stays in `#contact` — update it, never drop it.
