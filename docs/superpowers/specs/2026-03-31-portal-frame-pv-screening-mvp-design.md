# Portal Frame PV Screening MVP Design

## Goal

Redefine the product from a UI-first screening demo into a real screening-level structural review tool for a narrow, valuable engineering scenario:

- Existing single-story portal frame industrial buildings / warehouses
- Rooftop PV added load screening
- GB / AISC / Eurocode code-context support
- Screening-level structural review only

The MVP must produce a structural-engineer-readable conclusion backed by simplified calculations and explicit review boundaries. It must not present itself as formal design, full code checking, or a substitute for signed engineering calculations.

## Product Boundary

This MVP is for early-stage structural feasibility screening. It answers:

- Given known portal frame geometry, member information, steel grade, and existing evidence, can rooftop PV added load move forward to the next review stage?
- What is the current controlling concern: purlins, primary frame, missing evidence, or roof attachment uncertainty?
- What simplified calculation results support the conclusion?
- What information is still missing before a defendable formal review can proceed?

This MVP does not do the following:

- Full formal structural design
- Complete clause-by-clause code compliance automation
- 3D finite-element analysis
- Detailed connection design
- Full wind / snow / seismic automation across all load cases
- SAP2000 / Midas execution in the first version

## Recommendation

Adopt a medium-refactor path on top of the existing repository:

- Keep the new core package, persistence layer, report pipeline, and test harness
- Replace the current demo-oriented screening logic with a portal-frame-specific screening calculator
- Keep UI and workbench layers as thin consumers of the new engineering output
- Continue treating the existing rule engine as a compatibility adapter during migration

This is not a rewrite. It is a focused redefinition of the product around a single engineering use case.

## Architecture

The MVP should use a common engineering workflow across all supported standards, while keeping code-specific calculation packages separate.

Shared workflow:

1. Normalize project inputs into a portal-frame screening case
2. Check evidence sufficiency and identify missing critical inputs
3. Route to the selected code package: GB / AISC / Eurocode
4. Run simplified screening calculations
5. Synthesize engineering judgment
6. Generate a structural-review-style conclusion and next-step recommendations
7. Persist the case, calculations, and report

Separate code calculators:

- `gb_portal_frame_screening`
- `aisc_portal_frame_screening`
- `eurocode_portal_frame_screening`

The workflow is shared. The formulas, load-combination logic, and review basis are not treated as interchangeable.

## Structural Review Engineer Module

The new core should introduce a real engineering module with five responsibilities.

### 1. Input Normalizer

Convert raw user input into a calculation-ready screening case.

Responsibilities:

- Normalize geometry, member, material, roof, and load inputs
- Distinguish required vs optional fields
- Detect whether the case can support Level A / B / C screening
- Produce a missing-critical-data list before calculation starts

### 2. Code Router

Select the correct code package based on the chosen standard context.

Responsibilities:

- Choose GB / AISC / Eurocode calculation path
- Keep a consistent top-level interface for downstream reporting and persistence

### 3. Screening Calculator

Run simplified, explainable calculations suitable for early-stage screening.

Responsibilities:

- Convert rooftop PV added load into screening-level structural demand
- Run first-pass purlin screening
- Run first-pass primary portal frame risk screening
- Decide whether the case supports a defendable structural conclusion or should stop at evidence insufficiency

### 4. Engineering Judgment Synthesizer

Translate calculation outputs into structural engineering language.

Responsibilities:

- Identify the controlling concern
- State which conclusions are calculation-backed vs evidence-limited
- State which assumptions materially affect the result
- Convert numerical output into engineer-readable screening judgment

### 5. Next-Step Planner

Produce actionable engineering follow-up recommendations.

Responsibilities:

- Specify which drawings, calc sheets, member schedules, or field checks are still needed
- Indicate when the next step is formal analysis rather than more screening
- Reserve integration points for SAP2000 / Midas

## Input Design

The MVP should only collect inputs that materially affect portal frame rooftop PV screening.

### A. Project and Code Context

Required:

- Standard context: GB / AISC / Eurocode
- Building use: warehouse / factory / similar single-story industrial building
- Existing building flag
- Rooftop PV added-load scenario flag

Optional:

- Region / jurisdiction tag
- Project identifier

### B. Portal Frame Geometry and Structural System

Required:

- Span
- Bay spacing
- Eave height
- Roof slope
- Number of spans / frame arrangement
- Crane presence and range
- Portal frame type

Screening-required whenever available, otherwise tracked as missing:

- Rafter section
- Column section
- Purlin section and spacing
- Steel grade

### C. Loads and PV Added Load

Required:

- PV added dead load in kPa
- PV coverage: full roof or partial zone
- Basic roof build-up information
- Whether design load information exists

Recommended:

- Existing roof dead load
- Existing roof live load
- Whether wind / snow is likely controlling
- PV arrangement description

### D. Existing Evidence Chain

Required:

- Original structural drawings available?
- Original structural calculation report available?
- Member schedule available?
- Purlin layout record available?
- Site survey completed?
- As-built consistency confirmed?

Optional:

- Corrosion condition
- Deformation / leakage / retrofit history
- Roof system vendor information

## Screening Levels

The MVP should explicitly classify the case into one of three levels.

### Level A: Full First-Pass Screening

Enough data exists to run simplified structural screening and issue a numerical first-pass conclusion.

### Level B: Conservative Partial Screening

Some core data exists, but key uncertainties remain. The system can produce bounded or conservative screening output with explicit limitations.

### Level C: Evidence Sufficiency Only

The system must not pretend to calculate. It should stop at a professional statement that the available information is insufficient for a defendable structural conclusion.

## Calculation Scope

The MVP must be limited but real. It should calculate only what it can explain.

### Included in V1

1. Rooftop PV added load normalization

- Convert PV load input into a screening-level demand basis
- Distinguish full-roof vs partial-roof loading

2. Purlin-level first-pass screening

- First-pass bending / stress ratio
- First-pass deflection ratio
- Result classification: acceptable / review needed / not recommend direct progression

3. Primary portal frame risk screening

- Portal-frame-level risk identification using available geometry, member, material, and added-load inputs
- Where evidence is sufficient, produce simplified utilization / reserve judgment
- Where evidence is insufficient, explicitly stop at a non-defendable boundary

4. Evidence-governed conclusion boundary

- Distinguish calculable, conservatively screenable, and non-defendable cases

### Explicitly Out of Scope in V1

- Full 3D analysis
- Detailed joint checks
- Full second-order treatment across all conditions
- Full automated wind suction design path
- Seismic review
- Foundation and baseplate review
- Full cold-formed clause coverage
- Automatic SAP2000 / Midas execution

## Output Contract

The MVP output should read like a structural screening memorandum rather than a product demo.

Required output sections:

1. Review scope and boundary
2. Known input conditions
3. Simplified calculation results
4. Controlling concerns and engineering judgment
5. Preliminary structural conclusion
6. Recommended next-step review actions

The conclusion must use engineer-readable language such as:

- The project may proceed to the next stage of formal structural review under the current screening assumptions.
- Current screening indicates elevated risk at the purlin level and direct implementation is not recommended at this stage.
- The available evidence is insufficient to form a defendable conclusion on primary portal frame reserve.

The output must include calculation-backed values wherever available, not only narrative labels.

## Reporting Style

Report language must shift from product wording to structural review wording.

Preferred style:

- State load assumptions explicitly
- State simplified calculated values explicitly
- State which members or subsystems are likely controlling
- State what cannot be concluded because of missing evidence
- State the next required engineering action

Avoid demo-style language such as generic “Conditional Go” without supporting engineering content.

## Persistence

SQLite remains appropriate for the MVP.

The persisted record should retain:

- Input case snapshot
- Evidence sufficiency classification
- Code context
- Simplified calculation outputs
- Engineering judgment
- Report snapshot

The current persistence foundation can be reused and extended rather than replaced.

## Extension Interfaces

The MVP must reserve explicit extension points without implementing them yet.

Reserved interfaces:

- External analysis adapter for SAP2000
- External analysis adapter for Midas
- Calculation-report ingestion adapter
- Expanded code packages beyond initial screening formulas

These are future integration points, not V1 deliverables.

## Implementation Direction

Use the existing branch and repository foundation, but refocus the core around portal-frame rooftop PV screening:

- Rework the domain schema around portal frame structural inputs
- Replace the demo-style screening kernel with portal-frame screening calculators
- Preserve adapter layers temporarily
- Gradually move report generation to consume engineering outputs first
- Keep the UI frozen except where required to support the new input set and report content

## Success Criteria

The MVP is successful when:

- A structural engineer can input portal frame geometry, member and material information, evidence status, and rooftop PV added load
- The system produces a simplified structural screening result with actual calculation support
- The result clearly distinguishes calculation-backed conclusions from evidence-limited boundaries
- The language reads like a structural review note rather than a generic AI summary
- The design leaves clear extension points for SAP2000 / Midas integration and deeper code-package expansion
