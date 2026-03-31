# Main Demo Screening Depth Design

## Goal

Strengthen the credibility of the MVP by deepening the main demo case:

`Existing steel warehouse + rooftop PV | 既有钢结构仓库 + 屋面光伏`

This round is not about turning the product into a full engineering platform.
It is about making the main case feel like a real structural screening workflow instead of a presentation shell.

## Why This Round Exists

The current MVP already has:

- a stable single-page workbench
- bilingual reporting
- a rule-backed `Go / Conditional Go / No-Go` structure
- basic follow-up questions
- simple option comparison

What it lacks is engineering density.

Right now, the app can present a decision structure, but the connection between:

- what is asked
- why it matters
- how the decision is formed
- why one option is preferred

is still too thin.

This round fixes that specifically for the main demo scenario.

## Scope

### In Scope

Only deepen the main scenario:

- existing steel warehouse
- rooftop distributed PV
- incomplete drawings / imperfect site data
- limited shutdown tolerance

Three layers are enhanced together:

1. input parameters
2. screening rule bundles
3. option comparison depth

### Out of Scope

Still out of scope in this round:

- code-compliant structural calculations
- member-by-member verification
- connection design
- automatic drawing parsing
- cost estimation with real pricing databases
- standards engine for GB / AISC switching
- formal code citation system

## Product Outcome

After this round, the user should feel:

- the questions are more like a real screening checklist
- the decision is tied to concrete engineering conditions
- the options reflect different implementation paths, not just labels
- the report reads like a screening memo, not a chatbot summary

## Main Scenario Input Expansion

### Existing Inputs Kept

- project type
- building type
- structural system
- roof type
- intended modification
- estimated added load
- shutdown constraint
- drawing availability
- survey availability

### New Main-Case Inputs

Add the following fields for the main PV warehouse flow:

- `building_span_m`
- `column_spacing_m`
- `purlin_type`
- `roof_panel_type`
- `roof_panel_thickness_mm`
- `roof_rib_height_mm`
- `roof_attachment_preference`
- `corrosion_condition`
- `waterproofing_sensitivity`
- `restricted_installation_zones`
- `available_verification_path`

### Field Intent

#### Span and column spacing

These are not used for full structural calculation.
They are used for screening-level risk classification:

- longer span tends to correlate with higher reserve-capacity uncertainty
- larger framing modules increase caution when drawings are poor

#### Purlin / roof panel / rib height / panel thickness

These inputs support the roof-system screening layer:

- whether a feasible attachment path is likely
- whether local bearing / fastening questions become critical
- whether follow-up questions should focus on panel profile and support conditions

#### Attachment preference

Initial values:

- clamp-based
- penetrating attachment
- undecided

This is important because some roof systems can move from `Conditional Go` to effectively blocked if the preferred attachment path is incompatible with the roof build-up or waterproofing constraints.

#### Corrosion condition

Initial values:

- low
- moderate
- high
- unknown

This does not produce a design verdict by itself.
It raises screening caution and can strengthen the case for survey / verification before proceeding.

#### Waterproofing sensitivity

Initial values:

- low
- medium
- high

This is primarily used to shape option preference:

- clamp-based / restricted-zone installation may be preferred
- penetrating solutions become less attractive

#### Restricted installation zones

Free text or concise note for:

- skylights
- equipment zones
- weak zones
- maintenance corridors

This improves the realism of the option layer.

#### Available verification path

Initial values:

- drawings only
- survey only
- drawings plus survey
- no viable path yet

This becomes one of the most important feasibility-gate inputs.

## Screening Rule Bundles

The current rule engine is too flat.
This round introduces grouped rule bundles for the main demo.

### Bundle 1: Data Completeness Gate

Purpose:

- determine whether the project has enough information to move into structured verification

Illustrative triggers:

- drawings missing + no survey path
- no confirmation of roof panel system
- no attachment path clarity

Possible effects:

- add missing critical data
- downgrade confidence
- trigger `No-Go` if no viable verification path exists

### Bundle 2: Roof System Compatibility

Purpose:

- screen whether rooftop PV support is even practically compatible with the roof system

Illustrative triggers:

- profiled steel sheet but rib height / thickness unknown
- waterproofing sensitivity high with penetrating attachment preference
- roof panel type unclear and no survey path

Possible effects:

- add connection / roof compatibility risk
- generate targeted follow-up questions
- prefer clamp-based or restricted-zone options

### Bundle 3: Structural Reserve Capacity Risk

Purpose:

- screening-level caution around framing capacity uncertainty

Illustrative triggers:

- long-span steel framing with partial / missing drawings
- unknown purlin type
- added load above a simple screening threshold
- corrosion moderate / high with weak documentation

Possible effects:

- high reserve-capacity risk
- `Conditional Go`
- stronger recommendation for targeted verification before broad rollout

### Bundle 4: Construction / Operations Constraint

Purpose:

- capture whether the project is practically executable without unacceptable disruption

Illustrative triggers:

- limited shutdown + likely strengthening needed
- no restricted-zone strategy under active operations
- no phased verification plan

Possible effects:

- construction-stage risk
- operational disruption risk
- push preferred option toward lower-interruption strategies

### Bundle 5: Verification Path Gate

Purpose:

- explicitly answer whether there is a defendable path from screening to next-step engineering verification

Illustrative triggers:

- available verification path is `no viable path yet`
- drawings missing + survey unavailable
- key roof-system details unknown with no inspection route

Possible effects:

- `No-Go` if the project cannot be responsibly advanced
- otherwise `Conditional Go` with specific gating actions

## Option Comparison Upgrade

The option layer should stop being just a list of names.

Each option should include:

- title
- when it fits
- main constraint
- operational impact
- cost level
- schedule impact
- recommendation note

### Initial Main-Case Option Set

#### Option A: Restricted-Zone Installation

Use when:

- only parts of the roof appear suitable
- uncertainty is moderate but manageable
- operations cannot tolerate widespread strengthening

Characteristics:

- lower implementation disturbance
- moderate technical caution
- good for phased advancement

#### Option B: Local Strengthening Before Installation

Use when:

- installation is strategically valuable
- verification indicates local weak zones
- owner accepts moderate disruption

Characteristics:

- higher cost and schedule impact
- stronger structural confidence if verified
- suitable when broader installation coverage matters

#### Option C: Pause and Verify Before Scheme Selection

Use when:

- roof system details are too uncertain
- attachment path is not yet credible
- no defendable decision can be made responsibly

Characteristics:

- highest immediate delay
- best for risk containment
- often the correct answer when data is too poor

## Follow-Up Question Strategy

The follow-up layer should become more obviously engineering-driven.

Use a hybrid approach:

1. rule layer identifies missing critical parameters
2. explanation layer turns those gaps into natural-language prompts

Example:

If:

- roof type indicates profiled steel sheet
- rib height is missing
- panel thickness is missing

Then:

- rules flag roof attachment uncertainty
- the agent asks specifically for:
  - rib height
  - panel thickness
  - support / purlin relationship if needed

This preserves the architecture rule:

- engineering relevance from rules
- conversational quality from the explanation layer

## UI Changes

### Intake Panel

When the main demo scenario is selected:

- show the expanded warehouse + PV screening fields
- keep secondary scenarios lighter

This prevents overloading the whole product with fields that only matter for the main case.

### Decision Workbench

Enhance output sections so they feel more causally linked:

- key risks should reflect the new rule bundles
- missing data should feel specific, not generic
- recommended actions should mirror the gating logic
- options should display the new structured comparison fields

### Report Preview

Preview should show the richer option structure and more concrete missing-data / action phrasing.

The export remains bilingual Markdown.

## Report Changes

The report should read more like a screening memo and less like a generic result dump.

Add emphasis on:

- why the current decision was reached
- what blocks unconditional advancement
- what must be confirmed next
- why one option is preferred at this stage

## Success Criteria

This round succeeds if the main demo can convincingly show:

- more realistic engineering intake fields
- more defensible `Conditional Go` logic
- more specific follow-up questions
- more believable option trade-offs
- a report that reads like a screening deliverable

## Implementation Boundary

Do not broaden this into a multi-scenario overhaul.

Implementation should stay focused on:

- the main demo case first
- the rule structure that supports it
- the option comparison structure that makes it believable

Once the main case no longer feels like a shell, then it is worth deciding whether to port the same depth into the other scenarios.
