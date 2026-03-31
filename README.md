# Structural Screening Agent

Bilingual Streamlit workbench for early-stage structural feasibility screening in retrofit projects.

## Positioning

- Primary scenario: existing steel warehouse + rooftop PV
- Product mode: AI decision assistant, not a generic chatbot and not a pure calculator
- Primary outputs: `Go / Conditional Go / No-Go`, management summary, top risks, missing data, phased recommended actions, option comparison, bilingual report
- UI mode: Chinese / English switchable interface
- Export mode: bilingual same-line Markdown report

## Intended Users

- Project development managers evaluating whether a retrofit deserves further engineering effort
- Owner-side or EPC-side decision makers who need a structured early-stage screening memo
- Teams coordinating drawings, surveys, shutdown windows, and next-step verification scope

## What The Demo Actually Does

- Screens retrofit feasibility at `screening memo` level rather than code-compliant structural design level
- Uses a deterministic rule core for `Go / Conditional Go / No-Go`
- Deepens the main demo with a more realistic warehouse + rooftop PV checklist:
  - building span
  - column spacing
  - purlin type
  - roof panel system
  - panel thickness / rib height
  - attachment preference
  - existing member schedule / section schedule status
  - connection detail record status
  - roof vendor data status
  - corrosion condition
  - waterproofing sensitivity
  - restricted installation zones
  - available verification path
- Adds an executive-facing management summary layer:
  - current decision
  - primary constraint
  - next step
  - preferred path
- Adds drawing-facts and evidence-strength framing instead of pretending to auto-parse drawings:
  - drawing facts summary
  - verification readiness
  - assumptions and limits
- Adds screening-level engineering checks rather than a fake calculation engine:
  - reserve capacity screening
  - attachment feasibility screening
  - check-to-action linkage
- Generates structured option comparison instead of plain option labels:
  - priority rationale
  - fit when
  - main constraint
  - operational impact
  - cost level
  - schedule impact
  - recommendation note
- Adds light-weight standards context:
  - `GB`
  - `AISC`
  - `Eurocode`
  This only marks which review path should govern the next-stage engineering check.
- Keeps LLM responsibility limited to explanation and follow-up phrasing, never final feasibility judgment

## How To Use

1. Select a case from the sidebar case library and confirm the basic project inputs.
2. Enter the current documentation status, shutdown constraint, and the main-case evidence fields when applicable.
3. Review the decision banner and the management summary first.
4. Check drawing facts, verification readiness, engineering checks, and check-to-action linkage.
5. Review top risks, missing data, and the phased action groups (`Must Do`, `Parallel Track`, `Later Step`).
6. Compare the preferred path against backup options, then export the bilingual markdown report for team discussion or consultant handoff.

## Current Scope

- Not a replacement for structural engineering design or sign-off
- No member-by-member checks, no code-compliant calculation engine, no automatic drawing parsing
- No direct procurement instruction, fabrication detailing, or signed engineering conclusion
- Engineering checks are still `screening-level judgments`, not formal member, connection, or stability verification

## Standards Context

- `GB` currently adds follow-on review notes pointing toward `GB 50017` and roof attachment review
- `AISC` currently adds follow-on review notes pointing toward `AISC 360`
- `Eurocode` currently adds follow-on review notes pointing toward `Eurocode 3`
- Current standards selection does **not** mean the product already performs the full corresponding code calculation chain

## Current Decision Stack

- Decision banner: `Go / Conditional Go / No-Go`
- Management summary: current decision, primary constraint, next step, preferred path
- Drawing facts summary: manually curated drawing and vendor facts rather than automatic extraction
- Verification readiness: `Ready / Partial Ready / Not Ready`
- Engineering screening checks: reserve capacity and attachment feasibility
- Check-to-action linkage: explains why a given engineering check leads to a must-do action and keeps a given path on top
- Phased action groups: `Must Do / Parallel Track / Later Step`
- Standards context: which code path should govern the next-stage engineering review

## LLM Providers

- Supported providers: `mock`, `openai`, `minimax`, `gemini`
- `mock` is the default fallback mode for stable local use without any API key
- Copy `.env.example` to `.env` or export environment variables in your shell
- `Minimax` uses the official OpenAI Python SDK compatibility endpoint
- `Gemini` uses the official `google-genai` SDK

Example:

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here
python -m streamlit run app.py
```

## Run

```bash
python -m pip install -e ".[dev]"
python -m streamlit run app.py
pytest
```
