# DESIGN.md — CPCB Classification Register

Design system reference for the CPCB Sector Classification & Compliance Tool.
Any AI tool (Antigravity, Claude, etc.) or human designer should read this in full
before generating or modifying UI. This document is the source of truth for visual
and interaction decisions — prefer it over default/generic styling choices.

---

## 1. Concept & Design Philosophy

This is a **regulatory compliance instrument**, not a consumer app, a SaaS dashboard,
or a chatbot. The visual language should feel like an official government case file /
gazette ledger reimagined for screen — authoritative, precise, unhurried — while still
feeling modern and responsive to use. Think: the physical weight and trustworthiness of
a stamped government document, expressed through a clean digital interface.

**Emotional target:** "I trust this number." Not "this app is fun." Confidence and
legibility outrank playfulness at every decision point. Where personality is allowed
(micro-interactions, the rubber-stamp motif, subtle motion), it should reinforce the
"official record" feeling, never undercut it.

**Explicitly avoid:**
- Generic SaaS-dashboard look (soft blue/purple gradients, rounded pill everything,
  Inter font, card-shadow-heavy layouts) — this is the default AI-generated aesthetic
  and must be actively avoided.
- Playful/consumer tone (bright saturated colors, bouncy animations, emoji-heavy copy
  outside of small functional status icons already in use).
- Dense "enterprise software" clutter (cramped tables, tiny text, no breathing room).

---

## 2. Color System

Colors are drawn from official document/ledger conventions, not arbitrary brand colors.
Red/Orange/Green/White are NOT decorative — they are the actual CPCB regulatory
categories, so their use as accent colors is semantically grounded, not decorative.

| Token | Hex | Usage |
|---|---|---|
| `--ink` | `#232B36` | Primary text, sidebar background, headers |
| `--paper` | `#F7F5F0` | Main background (warm off-white, not pure white) |
| `--paper-raised` | `#FFFEFB` | Cards, inputs, elevated surfaces |
| `--rule` | `#D8D3C4` | Borders, dividers, dashed rule lines |
| `--gold` | `#A8791F` | Accent — active states, links, eyebrow labels, seal |
| `--red` (Category) | `#B23A30` | Red category badge only |
| `--orange` (Category) | `#C47A2C` | Orange category badge only |
| `--green` (Category) | `#3F6B4A` | Green category badge only |
| `--white-cat` (Category) | `#7A7568` | White category badge only |

**Rule:** Red/Orange/Green/White tokens are reserved exclusively for category badges
and category-linked UI (e.g. a Red-category result card's accent). Never use them as
general-purpose UI accent colors (buttons, links, etc.) — that would dilute their
regulatory meaning. General UI accents use `--gold` and `--ink` only.

---

## 3. Typography

| Role | Font | Notes |
|---|---|---|
| Headings | Cambria / Source Serif 4 | Serif — evokes official document/gazette typesetting |
| Body | Calibri / IBM Plex Sans | Clean, highly legible sans, no personality competing with data |
| Data / figures / code | Consolas / IBM Plex Mono | ALL numeric values (PI scores, ₹ amounts, table thresholds) render in mono — reinforces "this is measured data, not prose" |
| Eyebrow labels / meta | Mono, uppercase, letter-spaced | Section labels ("Entry 01", "Table I row W1-3") |

**Rule:** Any number that came from a calculation or lookup (PI, ₹ fee, day counts,
thresholds) must be in the mono font, even inline in a sentence. This is a deliberate,
consistent signal that distinguishes "this is data" from "this is explanation."

---

## 4. Layout & Spacing

- Two-column shell: fixed dark sidebar (case-file navigation) + light main workspace.
  Do not switch to a top-nav or full-width single-column layout — the sidebar-as-ledger-
  spine is core to the concept.
- Generous whitespace in the main workspace — this is a document to be read carefully,
  not a dashboard to be scanned quickly. Err toward more breathing room, not less.
- Base spacing unit: 4px grid. Card padding: 20–24px. Section spacing: 32–40px between
  major blocks.
- Max content width in workspace: ~820px — keeps line length readable, avoids the
  "stretched enterprise table" look on wide monitors.

---

## 5. Components

### 5.1 Sidebar / Case File Navigation
- Dark (`--ink`) background, numbered steps ("01", "02"...) in mono type.
- Steps are clickable (jump-to-section), with a filled gold dot marking the active step
  and a hollow/muted dot for inactive steps.
- The "CPCB" wordmark renders as a rotated, bordered "seal" chip — a literal nod to an
  official stamp, reused as the app's logo mark.

### 5.2 Category Badge
- Pill-shaped, slightly rotated (-2deg), bordered in the category's color, text in that
  same color. The rotation is intentional — evokes a rubber-stamped approval mark
  without literally drawing a stamp graphic.
- **Interactive enhancement to add:** on first render of a result, the badge should
  animate in with a quick "stamp impact" — scale from 1.15 → 1.0 with a short
  ease-out (~180ms), simulating a stamp being pressed down. Subtle, not cartoonish.

### 5.3 Result Cards / Spec Tables
- Tables use a dark-header-row / light-body pattern, single hairline row dividers
  (`--rule`), no zebra striping (zebra striping reads as generic spreadsheet, not
  official document).
- Cards get a very subtle hover elevation (soft shadow, already implemented) — signals
  interactivity without looking like a consumer product card.

### 5.4 Buttons
- Primary actions: solid `--ink` fill, `--paper` text, small scale-down (0.98) on
  press for tactile feedback (already implemented).
- Secondary/navigational actions: text-only, gold, underlined — matches the "reference
  citation" visual language, not a boxed button (keeps hierarchy clear).
- Q-Flow answer buttons: bordered, left-aligned text (never centered — these read as
  a numbered list of options, not generic pill buttons).

### 5.5 Forms
- Numeric inputs for Q-Flow should show the expected unit as placeholder text (already
  implemented: "mg/l", "KLD", "TPD") — never leave a numeric field without unit context.
- **To add:** inline soft-validation hint below numeric fields showing a plausible
  typical range in muted gray text (e.g. "Typical range: 100–5,000 mg/l") — non-
  blocking, addresses the "what if I mistype a number" concern without adding friction.

### 5.6 Loading States
- Small circular spinner (gold, on `--rule` track) + plain-language status text
  ("Searching for…", "Calculating…") — already implemented. Never use a generic
  full-page spinner or skeleton screens; this app's operations are fast enough that a
  small inline indicator is honest about what's happening.

### 5.7 Transparency / Breakdown Disclosure
- The `<details>`-based "Show how this was calculated" pattern (already implemented)
  should be extended visually: when expanded, each breakdown line should render as a
  small mono-font "ledger entry" with a thin left border, reinforcing the audit-trail
  feeling — this is a genuine differentiator from the original system and should look
  distinctly more trustworthy than a plain bullet list.

---

## 6. Motion & Interaction Principles

1. **Motion should feel mechanical/deliberate, not bouncy.** Ease-out or linear timing,
   never elastic/spring easing. Durations 120–220ms for most UI feedback.
2. **Every async action needs visible feedback within 100ms** — loading spinner, button
   disabled state, or immediate optimistic UI change. No silent waiting (this was a
   real bug fixed earlier in this project — do not regress it).
3. **State transitions between panels** use a short fade+slight-rise (already
   implemented via `.panel.active` fade-in) — keep this consistent for any new panel.
4. **Category badge "stamp" animation** (see 5.2) is the one place a slightly more
   expressive motion is welcome — it's the emotional payoff moment of the tool.

---

## 7. Data Visualization Direction (future enhancement)

Currently PI is shown as a plain number + category badge. A more interactive/
professional treatment would add a **horizontal PI gauge**: a thin bar from 0–100,
with the White/Green/Orange/Red zone boundaries marked (25/55/80), and a small marker
at the computed PI value. This turns an abstract number into an immediately-scannable
visual, and reinforces the category thresholds educationally. Use category colors for
the zone segments; keep the marker itself in `--ink` or `--gold` so it doesn't blend
into whichever zone it's in.

---

## 8. Accessibility

- Minimum contrast: body text on `--paper` must meet WCAG AA (already satisfied by
  `--ink` on `--paper`).
- All interactive elements (sidebar steps, Q-Flow options, buttons) must have visible
  focus states, not just hover states — add `:focus-visible` outlines in `--gold` where
  missing.
- Category badges must never rely on color alone — always paired with the text label
  (Red/Orange/Green/White), which is already the case; preserve this.

---

## 9. Voice & Copy Tone

- Formal but not bureaucratic-dense. Prefer plain verbs over nominalized bureaucratic
  phrasing ("this doesn't apply" not "non-applicability is noted").
- Status icons (✅ ⚠️ ℹ️ ❌ ⏱ ✨) are used sparingly and consistently for their
  established meaning (success/caution/info/no-match/time/AI-assisted) — do not
  introduce new emoji meanings without updating this section.
- Disclaimers stay short, appear once per result, and are visually de-emphasized
  (smaller, muted color, dashed top border) — present but not alarming.

---

## 10. What NOT to do (explicit anti-patterns)

- Do not introduce a second accent color beyond gold — resist the urge to add blue
  links or purple highlights typical of SaaS templates.
- Do not round corners aggressively (max 4px radius anywhere) — sharp/near-sharp
  corners reinforce the document/ledger feeling; heavy rounding reads as consumer app.
- Do not add background gradients, glassmorphism, or drop shadows beyond the subtle
  card hover effect already specified.
- Do not center-align body text or form labels — left-alignment throughout, consistent
  with document conventions.
- Do not replace the serif/sans/mono three-font system with a single font — the
  distinction between heading/body/data is load-bearing for legibility of this
  specific tool.
