---
name: HomePowerRebate
description: Verified home energy rebates by city, with the top-rated local installers. Honest, warm, Grade-6.
colors:
  ink: "#0a2a2e"
  ink-soft: "#1a3d42"
  paper: "#faf7f2"
  paper-warm: "#f5efe5"
  teal: "#0d4f5c"
  teal-deep: "#08363f"
  amber: "#d4751c"
  amber-bright: "#e88a2e"
  amber-text: "#a4540a"
  amber-text-deep: "#8a4607"
  sage: "#6b8e7f"
  green-money: "#2d6a4f"
  rule: "#d9d0c1"
  card-rule: "#e3dacb"
  muted: "#4a5f62"
  pill-open-bg: "#e3f1e8"
  pill-open-text: "#1f5a3d"
  pill-soon-bg: "#fdeccf"
  pill-soon-text: "#8a4a06"
  pill-closed-bg: "#f3dcdc"
  pill-closed-text: "#8a2b2b"
typography:
  display:
    fontFamily: "Fraunces, 'Fraunces Fallback', Georgia, serif"
    fontSize: "clamp(36px, 5.2vw, 72px)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  amount:
    fontFamily: "Fraunces, 'Fraunces Fallback', Georgia, serif"
    fontSize: "clamp(26px, 2.2vw, 32px)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Fraunces, 'Fraunces Fallback', Georgia, serif"
    fontSize: "clamp(27px, 2.5vw, 36px)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.018em"
  title:
    fontFamily: "'Inter Tight', 'Inter Tight Fallback', sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.35
  body:
    fontFamily: "'Inter Tight', 'Inter Tight Fallback', sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "'Inter Tight', 'Inter Tight Fallback', sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.3
rounded:
  pill: "999px"
  card: "18px"
  box: "14px"
  field: "8px"
spacing:
  gutter: "clamp(16px, 3.2vw, 56px)"
  article: "clamp(800px, 56vw, 900px)"
  container: "clamp(1180px, 90vw, 1440px)"
  rail: "clamp(300px, 21vw, 340px)"
components:
  button-primary:
    backgroundColor: "{colors.amber-text}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    padding: "14px 22px"
  button-primary-hover:
    backgroundColor: "{colors.amber-text-deep}"
  button-dark:
    backgroundColor: "{colors.teal-deep}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "11px 20px"
  rebate-card:
    backgroundColor: "#ffffff"
    rounded: "{rounded.card}"
    padding: "22px 22px 20px"
  status-pill-open:
    backgroundColor: "{colors.pill-open-bg}"
    textColor: "{colors.pill-open-text}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
  status-pill-soon:
    backgroundColor: "{colors.pill-soon-bg}"
    textColor: "{colors.pill-soon-text}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
  status-pill-closed:
    backgroundColor: "{colors.pill-closed-bg}"
    textColor: "{colors.pill-closed-text}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
  chip:
    backgroundColor: "#ffffff"
    textColor: "{colors.teal-deep}"
    rounded: "{rounded.pill}"
    height: "44px"
---

# Design System: HomePowerRebate

## Overview

**Creative North Star: "The Honest Ledger"**

Every page answers one question: what can this home claim, and who can install it. The design treats money like a ledger entry: the amount comes first, in a warm serif, and every figure carries its status, its source and the date it was last checked. Nothing on the page is louder than the amount, and nothing is styled to sell.

The world is paper and deep teal. Pages sit on warm off-white paper; heroes and the footer are deep teal with a soft amber glow. Amber is the one accent: it marks the next action and the brand's "Power", and it is used sparingly. Type pairs Fraunces (amounts, headings) with Inter Tight (everything you read or tap). Copy is Grade-6 and the layout is one reading column with one left edge.

The system is shared, not per page: tokens and chrome live in `_partials/nav-footer.html` (built into `/assets/site.css`), page families in `_partials/templates/<family>.css`, words in `_partials/glossary.json`, status pills in `scripts/status_pills.py`. Generators emit classes; the restamp applies the design.

**Key Characteristics:**
- Amount first: the number leads the hero and every rebate card.
- Status always in words, never colour alone.
- One accent (amber) for actions; teal for structure; green only for money.
- One reading column, 17px body, 68ch line length.
- Generated at scale: change the shared file, never a page.

## Colors

Warm paper and deep teal, with one amber accent and one money green.

### Primary
- **Deep Harbour Teal** (teal-deep): heroes, footer, dark buttons ("Pick your city"), focus ring on light surfaces.
- **Harbour Teal** (teal): links, secondary structure, chip hover borders.

### Secondary
- **Ember Amber** (amber): brand "Power", accent bars above h2, borders and dots. Not for text or white-text buttons on light backgrounds (fails contrast).
- **Ember Amber, text weight** (amber-text): every amber button background (white text 5.4:1) and amber hover text. Hover goes one step darker (amber-text-deep).
- **Glow Amber** (amber-bright): focus ring and highlights on dark teal only.

### Tertiary
- **Ledger Green** (green-money): rebate amounts on open programs. Closed or limited programs grey the amount out.

### Neutral
- **Warm Paper** (paper): page background. **Warm Paper, deeper** (paper-warm): callouts and table heads.
- **Ink** (ink) and **Ink, soft** (ink-soft): headings and body text. **Muted** (muted): secondary text.
- **Rule** (rule) for dividers; **Card Rule** (card-rule) for card and table borders.

### Named Rules
**The One Accent Rule.** Amber marks the next action. If two amber buttons are visible at once on a phone, one of them goes.

**The Words Not Colour Rule.** Every status, every chart series and every error says what it is in words; colour only repeats it.

## Typography

**Display Font:** Fraunces (with Georgia)
**Body Font:** Inter Tight (with a metric-matched fallback)

**Character:** a warm, slightly old-fashioned serif for money and headings, with a plain, tight sans for reading and tapping. The serif carries trust; the sans carries clarity.

### Hierarchy
- **Display** (600, clamp(36px, 5.2vw, 72px), 1.04): page h1 on blog and program heroes. On rebate pages the hero amount takes this size and the h1 drops to 22 to 32px under it.
- **Amount** (600, clamp(26px, 2.2vw, 32px), 1.08): rebate card amounts; the lead card goes to 44px.
- **Headline** (600, clamp(27px, 2.5vw, 36px), 1.12): h2, with a 44 by 4px amber bar above it.
- **Title** (700, 16px, 1.35): card titles (h3).
- **Body** (400, 17px, 1.7): paragraphs and lists, max 68ch.
- **Label** (700, 13px): pills, eyebrows, sources. 13px is the floor for any text.

### Named Rules
**The 13px Floor Rule.** No text below 13px, anywhere.

**The Sentence Case Rule.** Headings, buttons and pills use sentence case ("See my rebates", "Check first"). The footer column links are the one Title Case list.

## Layout

One reading column (--article, 800 to 900px plus gutters) with one left edge; the hero is full-bleed but its text aligns to the column. From 1180px, long pages add a sticky side panel (--rail) with "On this page" and one call to action; below 1180px the same list folds under the hero. Region hubs use a wider container (--container). Phones are the default: 390px is the design width, every tap target is at least 44px, and the menu slides away while reading down.

## Elevation & Depth

Mostly flat paper. Cards sit on a soft two-layer shadow (--shadow-card) with a 1px card-rule border, and lift 2px on hover with a deeper shadow. Heroes get depth from colour (radial amber and sage glows on teal), not shadow.

### Shadow Vocabulary
- **Card at rest** (`0 1px 2px rgba(10,42,46,.04), 0 8px 24px -12px rgba(10,42,46,.14)`): rebate, FAQ and installer cards.
- **Card on hover** (`0 2px 4px rgba(10,42,46,.05), 0 18px 36px -16px rgba(10,42,46,.24)`): with a 2px lift; none when reduced motion is on.

## Shapes

Soft and friendly, never sharp. Cards 18px, boxes and callouts 14 to 16px, fields 8px, and every button, chip and pill fully rounded (999px). Callouts carry a 5px amber left border; h2s carry a short amber bar.

## Components

### Buttons
- **Shape:** fully rounded (999px).
- **Primary:** amber-text background, white text, 700 weight. Labels follow the glossary: "See my rebates", "Estimate my rebates", "Request my quotes" (installer forms only).
- **Hover / Focus:** one step darker; focus is a 3px teal ring with a white halo on light surfaces, amber on dark ones.
- **Dark:** teal-deep with paper text ("Pick your city", the first sibling chip).

### Chips
- **Style:** white, card-rule border, teal-deep text, 44px tall; the first chip ("Back to … hub") is filled teal-deep. On phones the row scrolls sideways.

### Cards / Containers
- **Corner Style:** 18px.
- **Background:** white on paper; the first open rebate card spans the row with a faint green wash.
- **Shadow Strategy:** card at rest, lift on hover.
- **Border:** 1px card-rule.
- **Internal Padding:** 22px (18px on phones).

### Status pills
- **Style:** fully rounded, 13px, 700, sentence case, a 7px dot in the text colour. One design for rebate cards and hub tables.
- **Tones:** Open (green); Starts soon, On hold, Paused, Check first (amber); Closed (red); Info (grey). The mapping from a fact's status lives in `scripts/status_pills.py`.

### Navigation
- **Style:** sticky paper bar with blur; logo, "Find an Installer", "See my rebates", "Blog", search and "Pick your city". On phones it slides away on scroll down and returns on scroll up.

### Rebate card (signature)
Money first: the status pill, then the amount in Fraunces green, then the program title (h3), then one plain sentence of conditions. A card that links somewhere is clickable as a whole.

## Do's and Don'ts

### Do:
- **Do** put the amount first, in the hero and on every rebate card.
- **Do** show status as a word from `scripts/status_pills.py` and a source link with a date for every figure.
- **Do** use the tokens (`var(--teal-deep)`, `var(--card-rule)`, `var(--radius-card)`) in new CSS, not hex.
- **Do** change the shared partial, a template family file or a generator, then restamp; check with `scripts/check_consistency.py`.
- **Do** keep every tap target at 44px or more and every text at 13px or more.

### Don't:
- **Don't** put white text on plain amber (#d4751c) or amber text on white; use amber-text.
- **Don't** show two amber calls to action on one phone screen.
- **Don't** invent a new pill colour, label or button wording; add it to the glossary or `status_pills.py` first.
- **Don't** paste shared CSS into pages or style the menu, footer or breadcrumb from a template variant (`strip_variant_chrome.py --check` fails).
- **Don't** use decorative gradient text, side-stripe borders on cards, or stock imagery; the brand is in the numbers.
