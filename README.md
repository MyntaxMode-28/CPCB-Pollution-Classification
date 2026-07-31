# CPCB Classification of Industrial Sectors — Local App

An automated decision-support web application for calculating Pollution Index (PI) scores, sector classifications, consent fee requirements, and Environmental Compensation (EC) penalties based on CPCB guidelines.

---

## ⚡ Quick Start Guide (For Office / Supervisor Setup)

### Prerequisites
1. **Python 3.10+**: [Download Python](https://www.python.org/downloads/) *(Ensure "Add Python to PATH" is checked during install)*.
2. **Ollama**: [Download Ollama](https://ollama.com/) *(Required for local AI fallback suggestions)*.

### 1. Install Dependencies
Open terminal/command prompt in this project folder and run:
```bash
pip install flask rapidfuzz openpyxl pandas --break-system-packages

# CPCB Classification Tool — Local App

## What this is
A local version of the CPCB sector classification + Q-Flow assessment tool,
running as real Python code instead of a ChatGPT prompt. Same underlying
rules, but the search/scoring/lookups are deterministic — no hallucination
risk on the calculations, because nothing is "guessed" by an AI.

## Known fix vs. the ChatGPT version
Cross-checked against the original Custom GPT: a set of 6 cement plant PI
values (100/100/100/92/97/64) were present in the source data but mislabeled
under "Aluminium Smelter" due to a transcription gap in the original PDF
table. Corrected in `backend/seventeen_category.py` with a note attached
to every result so it's traceable.

## How to run it
1. Install dependencies (one-time):
   pip install flask rapidfuzz openpyxl pandas --break-system-packages

2. Start the server:
   python3 app.py

3. Open in your browser:
   http://127.0.0.1:5000

## What works right now (Day 1)
- Search by sector name → correct classification, sourced only from real data
- Multi-candidate selection (e.g. typing "cement" shows all valid sub-types)
- 17-category override applied automatically (Quarterly inspection)
- Q-Flow question-by-question assessment → PI calculation → category

## Not yet built
- EC (Environmental Compensation) penalty calculator UI (logic exists in
  backend/penalty.py, not wired into the frontend yet)
- CTE/CTO consent workflow and fee calculator
- search_key/aliases columns in the Excel itself (currently generated
  on-the-fly at load time instead)

## Optional AI layer (Day 2 addition)
Search now falls back to a local Ollama model ONLY when the exact/fuzzy code
search finds nothing — it suggests the closest real sector name, then the
SAME deterministic search re-runs on that suggestion. The AI never invents a
PI/category/fee value itself; it only helps aim the search.

To enable it:
1. Install Ollama: https://ollama.com
2. Run: ollama pull llama3.2
3. Make sure `ollama serve` is running (usually automatic after install)
4. Restart the app — it detects Ollama automatically, and works fine without it too.

## Newly wired this session
- backend/consent.py — CTE/CTO fee formula (CF = CI x SF x PIF) + corrected
  Jan-2026 CTO validity rule (supersedes the old fixed-years table)
- backend/ai_layer.py — the optional Ollama flexibility layer described above
- Bug fix: pandas NaN values (empty spreadsheet cells) were being sent as
  invalid JSON, silently breaking results for any sector with a blank
  Remarks column (this is why bakery returned nothing in testing)

## Day 2, part 2 — EC and Consent Fee now live in the UI
- Classification result screen now has two buttons: "Estimate EC" and "Calculate CTE/CTO fee"
- Both open real forms, submit to the already-tested backend, and render full breakdown tables
- Category dropdowns auto-fill from whatever sector/Q-flow result you just got, so the numbers
  are grounded in the actual classification instead of typed in blind
- Search results now show an "✨ AI suggested" banner when Ollama filled a gap that pure
  keyword search couldn't

## Debugging Ollama connectivity
1. Run `python3 test_ollama.py` — standalone check, isolates Ollama from the rest of the app
2. Once the app is running, visit http://127.0.0.1:5000/api/ai/status in your browser —
   shows connected: true/false directly, no terminal digging needed

## Bug fixed: AI suggestion redesigned
Original design asked the model to match a query against 400 full sector names verbatim —
too slow and too strict for a small local model to ever succeed. Redesigned so the model
only cleans up the query into a short phrase (e.g. "bekery shop thing" -> "bakery"), then
hands that to the SAME tested deterministic search. Faster, and the AI is no longer required
to reproduce exact text.

## Honesty flag added: Q-Flow scoring is provisional
`Only Q-flow.md` (source file) explicitly withheld the exact answer-to-score mapping
table ("not shown here to prevent disclosure"). The scoring in qflow.py assumes answers
map to severity levels in listed order — a reasonable inference, but NOT independently
confirmed against CPCB's real internal scoring key. The Q-flow result screen now shows
this caveat directly. Search results (spreadsheet-based) are unaffected — those are
100% sourced, not inferred.

## Added: consent/CTE/CTO processing time estimator
Consent Fee calculator now also shows statutory maximum decision timelines
(CTE: 30-60 days, CTO first: 30-90 days, renewal: 30-120 days depending on category),
sourced from the 2025 Uniform Consent Guidelines para 8.

## MAJOR UPDATE: Q-Flow rebuilt on real CPCB scoring tables
Previous Q-flow scoring guessed how multiple-choice answers mapped to scores, because
the source file withheld the exact mapping. User supplied the actual official CPCB
scoring tables (Table I: Water, Table II: Air, Table III: Waste) with real numeric
thresholds. Q-flow has been fully rebuilt around these:

- Water: now asks for actual BOD/COD (mg/l) and wastewater quantity (KLD) as numbers,
  scored against exact threshold bands from Table I
- Air: fuel quantity now asks for actual TPD by fuel category, scored against Table II
- Waste: hazardous waste quantity (TPA) and bed count now numeric, scored against Table III
- Pollutant TYPE questions (which pollutants, which fuel category) remain multiple-choice
  since the tables define these as categories, not thresholds — but the category-to-score
  mapping is now taken directly from the table, not guessed
- New file: backend/qflow_scoring.py holds all the real threshold functions, cleanly
  separated from backend/qflow.py (which just handles question sequencing/branching)
- Result screen no longer shows the old "provisional/unverified" warning — replaced
  with a note that scoring now uses official table thresholds

TODO: confirm exact booklet title/year for proper source citation in the code comments.

## UI/UX improvements — this round
- Sidebar step indicators are now clickable — jump directly to any section anytime
- Loading spinners added to search, EC calculator, and consent fee calculator (search can
  take a few seconds when the AI fallback kicks in — this was invisible before, now it isn't)
- Q-Flow now has a "Back" button — misclicking an answer no longer requires a full reset
- Q-Flow results now include a collapsible "Show how this was calculated" breakdown,
  listing exactly which official table row/threshold matched each answer — full transparency,
  not a black box
- Mobile layout polish: sidebar collapses to a horizontal pill-style nav under 800px width
- Bug fixed during this round: the qflow/back route lost its @app.route decorator during
  an earlier edit and silently 404'd — caught by testing before shipping, not left for the
  user to discover

## Fixed: silent AI failure with no feedback
Previously, if the AI fallback was attempted but failed (Ollama not running, timed out,
or its suggestion still didn't match anything), the app gave zero indication AI was even
tried — it just showed "no match," identical to when AI wasn't consulted at all. Now every
search response includes ai_attempted (true/false), and the UI shows one of three states:
(1) AI found a working suggestion, (2) AI suggested something but it still didn't match,
or (3) AI was attempted but Ollama didn't respond at all — with a direct link to
/api/ai/status for diagnosis.

## Fixed: EC/Consent applicability now shown immediately, no wasted form-filling
Previously you had to fill out and submit the full EC or Consent form just to discover a
White-category unit doesn't need it. Now the result screen auto-detects category and shows
either the two action buttons (Red/Orange/Green) or a plain "not required" note (White/
Not-in-ambit) — zero wasted clicks.

## Added: "Calculate both together" (Entry 06)
New combined panel — enter capital investment once, optionally tick "this unit has an
active violation" to also compute EC in the same submission. Both results render side by
side. Useful for the common real case where a unit needs both a consent fee estimate and
an EC penalty estimate at the same time.

## UI polish
Subtle hover shadow on result cards, button press feedback, checkbox styling.

## CRITICAL FIX (supervisor-identified): PIW/PIA formula bug
The Water and Air Pollution Index formulas were incorrectly using MAX(W1,W2,W3) and
MAX(A1,A2,A3) instead of the tables' actual specified formula: PIW = W1+W2+W3,
PIA = A1+A2+A3 (sum). Only the waste formula (PIH = H1+H2) was correct from the start.
This was a real accuracy bug, not a stylistic choice — in testing, the same input
scenario moved from PI 68.5/Orange (buggy) to PI 97.0/Red (correct) once fixed. Caught
by supervisor review of the calculation breakdown feature — a direct demonstration of
why the transparency/breakdown feature was worth building.

## Fixed: fuel quantity unit mismatch risk
Fuel consumption question previously always assumed TPD (tonnes/day) regardless of fuel
type. Gaseous fuel consumption is rarely tracked in tonnes in practice (more often kg/day
or volumetric) — entering a kg-based number into a TPD field would silently produce a
wildly wrong score. Added a unit selector (TPD / kg per day) with exact conversion.
Volumetric units (e.g. cubic metres of gas) are intentionally NOT offered, since accurate
conversion requires a fuel-specific density figure not available from a verified source —
better to ask the user to convert to kg themselves than to guess a density.

## Fixed: EC rupee factor (R) now adjustable, not hardcoded
CPCB's methodology permits R between Rs.100-500 with Rs.250 as a suggested default, not
a fixed value. Was previously hardcoded to 250. Now user-adjustable within that range in
both the standalone EC calculator and the combined panel.

## Cleaned up: internal/developer notes leaking into the UI
Removed: (1) an internal "pending citation confirmation" note that was rendering inside
the Q-Flow result screen, (2) internal audit commentary about the cement mislabeling fix
that was rendering inside search result notes (kept in code comments/README for
documentation, removed from what the end user sees).

## Renamed
Application renamed from "CPCB Classification Register" to
"CPCB Classification of Industrial Sectors" throughout (browser tab title, sidebar wordmark).

## Removed: "Both Together" combined panel
The combined CTE/CTO fee + EC calculator panel was removed per supervisor feedback
(unnecessary). Standalone EC and Consent Fee calculators remain, accessible individually
from the classification result screen as before.

## Added: named sector bar for Q-Flow, carried into the result
Q-Flow now has a persistent "Sector / activity name" field at the top, auto-filled from
the search box if you came from there. This name now displays as a title at the top of
the final classification result — so results are properly labeled instead of anonymous.

## Added: smart-default fuel unit selection
The fuel quantity unit dropdown (TPD / kg per day) now pre-selects based on the fuel
type chosen on the previous question — coal/liquid and biomass default to TPD (typically
tracked in tonnes at industrial scale), cleaner/gaseous fuels default to kg/day (more
commonly tracked by mass in practice). Still fully overridable if the user's actual data
is in a different unit. Applies correctly even when using the Back button.
