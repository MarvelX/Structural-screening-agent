# BV PV Design Review Workbench Design

> Date: 2026-05-17
> Target role: BV PV civil / structural / mounting / foundation design review engineer
> Product positioning: A long-term portfolio tool that aims to cover the full design-review responsibility chain in the BV job description.

## 1. Product Goal

`BV PV Design Review Workbench` is not a one-off interview demo and not a generic AI chat tool.

The long-term goal is to turn the main responsibilities of a BV photovoltaic design review engineer into a structured workbench:

`Project Intake -> Review Basis -> Document Completeness -> Review Plan / ITP -> Technical Checks -> Risk & Nonconformity Register -> Optimization Advice -> Review Report -> Client Clarification`

The tool should help a reviewer answer four professional questions:

1. What exactly is being reviewed?
2. Which contract requirements, regulations, standards, and technical specifications govern the review?
3. What design risks, errors, omissions, or uneconomic choices are visible from the submitted package?
4. What report, clarification, and next action should be issued to the client, designer, or contractor?

## 2. Why This Fits the BV Role

The BV role is not mainly a product selection job. It is an independent technical review, quality assurance, and client-facing engineering judgment role.

The current `Structural-screening-agent` already proves several building blocks:

- deterministic screening logic instead of LLM-only conclusions
- review boundary control for screening-level engineering judgment
- evidence sufficiency checks
- basis and traceability output
- report preview and Markdown / Word / PDF export
- a working `Portal Frame Rooftop PV Screening` module

Therefore, this project should evolve from a narrow structural screening agent into a broader BV design review workbench, while keeping the existing portal-frame rooftop PV module as the first real technical review module.

## 3. JD Responsibility Mapping

| BV job responsibility | Workbench capability |
| --- | --- |
| Review drawings, calculation reports, technical specifications | `Design Document Checklist` and review package intake |
| Ensure review quality based on quality system and client requirements | `Review Gate` and report boundary statements |
| Interpret GB, IEC, AS/NZS, Eurocode and apply them in review | `Review Basis Builder` with multi-standard basis registry |
| Review contract, regulations, standards, project specifications | `Project Requirement Register` |
| Define design review plan, ITP, and procedures | `Review Plan / ITP Generator` |
| Execute or supervise design review and issue professional reports | `Technical Review Path` and `Design Review Report Composer` |
| Communicate with client, design institute, and contractor | `Technical Clarification Tracker` |
| Identify risks, errors, omissions, and uneconomic design | `Risk & Nonconformity Register` and `Optimization Advisor` |
| Check structural loads, connections, foundation bearing capacity | modular technical check scopes |
| Make independent technical judgments | deterministic review outcomes with traceability |
| Promote BV services and solutions | `Service Scope Recommendation` |
| Manage design review projects | `Review Status Dashboard` and action tracking |

## 4. Target Users

Primary user:

- BV civil / structural / mounting / foundation design review engineer

Secondary users:

- senior reviewer or technical approver
- client project manager
- design institute engineer
- EPC / contractor engineer
- internal BV business development or project manager

## 5. Product Boundary

The workbench is for structured design review support. It must not present itself as:

- a signed engineering design tool
- a full finite-element analysis platform
- an automatic CAD drawing reviewer
- a replacement for professional reviewer responsibility
- a complete electrical design checker

It can support electrical interfaces only where they affect civil, structural, foundation, mounting, cable tray, grounding, layout, constructability, or review coordination.

## 6. Long-Term Module Architecture

### 6.1 Project Review Intake

Collects and normalizes:

- project type: utility PV plant, rooftop PV, ground-mount PV, water infrastructure PV, retrofit, mixed scenario
- review stage: proposal, preliminary design, construction drawing, as-built, technical due diligence
- region and standards context
- client requirements
- contract and technical specification references
- submitted document list
- review scope and exclusions

### 6.2 Review Basis Builder

Builds the review basis from:

- national and international standards
- industry standards
- contract requirements
- client technical requirements
- project specification clauses
- BV quality or review procedure references

Initial standard contexts:

- GB
- IEC
- AS/NZS
- Eurocode
- AISC as an optional existing capability retained from the current project

Key PV-related basis candidates:

- GB 50797, PV power station design code
- GB 50017, steel structure design standard
- GB 50009, load code for building structures
- GB 50007, foundation design code
- IEC 62548, PV array design requirements
- AS/NZS 1170 series, structural actions
- Eurocode 0 / 1 / 3 / 7 family, as applicable

The workbench should avoid fake clause automation in the MVP. It should first track review basis entries, applicability, evidence requirements, and follow-up review requirements.

### 6.3 Design Document Checklist

Checks whether the submitted design package is reviewable.

Document groups:

- civil drawings
- steel structure drawings
- mounting structure drawings
- foundation drawings
- design calculation reports
- technical specification
- geotechnical report
- survey or as-built records
- layout drawings
- cable tray / grounding / interface drawings
- material and corrosion protection specifications

Outputs:

- complete / partial / missing status
- blocking missing information
- reviewable items
- assumptions and limitations
- requested supplementary documents

### 6.4 Review Plan / ITP Generator

Generates a project-specific review plan and inspection / test plan draft.

Plan sections:

- review scope
- review basis
- document review sequence
- technical check categories
- hold points and witness points
- client / designer / contractor clarification points
- report issue stages
- escalation criteria

This module directly targets a high-value part of the BV job description: defining and reviewing the project-specific design review plan, ITP, and related procedures.

### 6.5 Technical Review Path

The review path is modular. Each module can begin as checklist and rule-based review, then progressively add calculation support.

Initial review scopes:

- mounting structure
- steel structure
- concrete structure
- foundation and bearing capacity
- load calculation
- connection details
- corrosion and durability
- constructability and O&M access
- rooftop PV added-load screening

The existing `Portal Frame Rooftop PV Screening` capability becomes the first implemented technical check module.

### 6.6 Risk & Nonconformity Register

Tracks review findings as structured records.

Each finding should include:

- finding type: risk, error, omission, nonconformity, optimization opportunity
- severity: info, minor, major, critical
- discipline: civil, steel, mounting, foundation, load, interface, documentation
- basis reference
- evidence source
- reviewer comment
- recommended action
- responsible party
- report status: open, clarified, closed, excluded

### 6.7 Optimization Advisor

Suggests optimization directions without pretending to redesign the project.

Examples:

- review support spacing or layout consistency
- reduce unnecessary non-standard members
- clarify connection load path
- improve foundation type selection logic
- improve corrosion protection alignment with environment
- request more economical alternatives where safety margin appears excessive but evidence is incomplete

### 6.8 Design Review Report Composer

Generates a BV-style review report package.

Report sections:

- project information
- review scope
- reviewed documents
- review basis
- assumptions and limitations
- design review plan summary
- technical review findings
- risk and nonconformity register
- optimization recommendations
- requested clarifications
- conclusion and next actions

The report should explicitly state that the workbench supports review preparation and screening-level decisions, not signed final engineering approval by itself.

### 6.9 Technical Clarification Tracker

Supports communication with:

- client
- design institute
- contractor
- internal senior reviewer

Each clarification should track:

- question
- related document
- basis or finding
- responsible party
- due status
- received answer
- closure decision

### 6.10 Service Scope Recommendation

Maps project risks and document gaps to BV service opportunities.

Examples:

- independent design review
- construction drawing review
- foundation / geotechnical review
- factory or material inspection coordination
- site inspection support
- technical due diligence
- design optimization workshop

This supports the JD requirement to promote BV services and solutions without turning the tool into a CRM.

## 7. Phased Implementation

### Phase 1: Portfolio MVP

Goal: make the workbench credible for interview and portfolio use while retaining engineering substance.

Included:

- rename or add entry point for `BV Review Mode`
- project review intake form
- multi-standard review basis selection: GB / IEC / AS/NZS / Eurocode / AISC
- design document completeness checklist
- review plan / ITP draft generation
- risk and nonconformity register
- BV-style report composer
- existing portal-frame rooftop PV module as the first technical check
- showcase brief and talk track for the BV role

Not included:

- CAD parsing
- full automated code compliance
- full foundation calculation engine
- full PV electrical review
- signed engineering approval

### Phase 2: Technical Review Expansion

Goal: expand from one implemented technical module to a broader PV civil / structural review scope.

Candidates:

- mounting structure checklist and risk rules
- foundation review checklist and bearing capacity evidence path
- connection detail review checklist
- corrosion and durability review
- PV array layout and O&M access interface review
- basic cable tray / grounding interface checklist

### Phase 3: Calculation and Evidence Deepening

Goal: add more deterministic calculators and stronger evidence handling.

Candidates:

- foundation bearing capacity screening
- mounting structure load path screening
- connection force path screening
- wind / snow / seismic review basis routing
- geotechnical report extraction checklist
- evidence matrix by document source and finding

### Phase 4: Review Project Management

Goal: support ongoing review projects rather than one-off assessments.

Candidates:

- finding lifecycle tracking
- clarification history
- responsible-party status
- review dashboard
- report revision history
- service scope and fee discussion support

## 8. Integration With Existing Repository

Use the existing repository as the base.

Preserve:

- `Portal Frame Rooftop PV Screening` domain and tests
- deterministic screening kernel
- basis registry pattern
- report export pipeline
- bilingual output pattern
- Streamlit workbench structure

Add:

- BV-specific domain models
- BV review basis entries
- BV risk and nonconformity records
- BV report sections
- BV showcase documentation
- one UI mode or tab for the review workbench

Avoid:

- rewriting the current app from scratch
- deleting existing portal-frame screening functionality
- mixing all BV logic into the existing portal-frame domain without boundaries

## 9. Data Model Sketch

### BVReviewProject

- project_id
- project_name
- region
- review_stage
- project_type
- client_requirement_summary
- contract_requirement_summary
- standards_context
- review_scope
- exclusions

### ReviewDocumentStatus

- document_type
- status
- source
- revision
- blocking
- reviewer_note

### ReviewBasisEntry

- basis_id
- standard_context
- title
- applicability
- evidence_requirements
- review_requirements
- report_wording

### ReviewFinding

- finding_id
- type
- severity
- discipline
- summary
- basis_ids
- evidence_refs
- recommended_action
- responsible_party
- status

### ReviewPlanItem

- item_id
- phase
- discipline
- check_item
- method
- hold_or_witness_point
- output

## 10. UX Direction

The app should feel like an engineering review console, not a landing page.

Recommended top-level navigation:

1. `Assessment`
2. `Project Intake`
3. `Review Basis`
4. `Documents & ITP`
5. `Findings`
6. `Report Export`
7. `Portal Frame Module`

The first screen should show:

- current review conclusion
- open critical findings
- document completeness
- applicable standards
- report readiness

## 11. Testing Strategy

Phase 1 tests should cover:

- BV review project model validation
- standards context selection
- document checklist generation
- review plan generation
- finding severity and report grouping
- report preview includes BV sections
- existing portal-frame tests remain passing

The key regression rule:

`BV Review Mode must not weaken the existing portal-frame screening module.`

## 12. Portfolio Narrative

The intended interview story:

“I built this as a long-term design review workbench for PV civil, structural, mounting, and foundation review. The first implemented technical module is rooftop PV added-load screening for existing portal-frame buildings. Around that module, I designed the review basis, document completeness, ITP, finding register, optimization advice, and report composer to match the actual BV design review workflow.”

This narrative is stronger than a single calculator because it shows:

- engineering judgment
- review workflow understanding
- standards awareness
- product structure
- report and client communication awareness
- realistic boundary control

## 13. Success Criteria

Phase 1 is successful when:

- a reviewer can enter a PV design review project
- the app can show review basis and document completeness
- the app can generate a draft review plan / ITP
- the app can list structured findings and recommended actions
- the existing portal-frame screening module can be referenced as a technical check
- the exported report reads like a design review report rather than a generic screening summary
- tests confirm the new BV layer and existing screening layer both work
