# External Showcase Materials Design

## Goal

Produce a compact, public-facing showcase package for the current `Structural-screening-agent` branch that helps two audiences understand the project quickly:

- Hiring reviewers evaluating technical depth and product-definition ability
- Owner-side technical managers evaluating engineering usefulness and decision value

The package should make it clear that this is not a generic AI chatbot or a UI-only demo. It should present the project as a portal-frame rooftop PV screening-review tool with explicit engineering boundaries.

## Audience and Messaging

### Primary Message

This project is a screening-level structural review tool for existing portal-frame buildings under rooftop PV added load scenarios.

### Secondary Message

The project also demonstrates the ability to turn a real engineering workflow into a productized system:

- engineering object model
- deterministic screening kernel
- standards-context routing
- assumptions and traceability
- exportable review summary

### Language Strategy

- Chinese-first narrative
- Limited English terminology only where it helps recognition (`screening kernel`, `traceability`, `portal frame`)
- No bilingual same-line treatment in the main showcase materials

## Deliverables

### 1. README

The README becomes the GitHub front door.

It should cover:

1. What the project is
2. What problem it solves
3. Why it is different from a generic AI demo
4. Key engineering capabilities
5. Current scope and limitations
6. Quick local demo run instructions
7. Links to additional showcase docs

The README should avoid:

- old “decision workbench” positioning language
- overemphasis on bilingual UI mechanics
- long changelog-style detail
- claims that imply formal design or full code-checking automation

### 2. Screenshot Assets

Produce exactly three screenshots, all in Chinese UI:

1. `assessment-overview`
   - decision, controlling factor, key calculations, evidence status
2. `basis-traceability`
   - basis references, trigger conditions, evidence requirements, input traceability
3. `report-export`
   - export actions and report preview

Each screenshot should support one message only and avoid very long full-page captures.

### 3. Demo Guide

Create a short document that explains:

- how to start the demo in three minutes
- which tabs to inspect first
- what each tab proves
- what the current demo does not claim to do

This document is not developer documentation. It is a guided viewing note for external reviewers.

### 4. One-Page Project Brief

Create a one-page Chinese project brief for hiring reviewers and owner-side technical managers.

It should include:

1. One-sentence positioning
2. Problem statement
3. Core capabilities
4. Why it is not a generic AI demo
5. Current technical boundary
6. Why the project is representative of broader engineering/product leadership ability

## Screenshot Generation Approach

The screenshots should be generated from the current local Streamlit app rather than manually cropped from arbitrary browser states. The goal is repeatable assets.

The implementation may use a browser automation script (for example Playwright) to:

- open the local app
- navigate to the required tabs
- wait for content
- capture stable screenshot files under a dedicated docs asset directory

## File Strategy

### README

- Modify: `README.md`

### Showcase Docs

Create a dedicated docs folder for public showcase materials:

- `docs/showcase/demo-guide.md`
- `docs/showcase/project-brief.md`
- `docs/showcase/assets/`

### Screenshot Script

If needed for repeatability:

- `scripts/capture_showcase_screenshots.py` or a similar focused helper

The script should be narrow in scope and only serve the screenshot capture task.

## Success Criteria

The work is successful if:

- A GitHub visitor can understand the project within one minute
- A technical manager can understand the engineering purpose and current boundary without reading code
- The README no longer reads like an internal development memo
- The screenshot set cleanly demonstrates decision view, traceability, and exportability
- The project brief can be sent as a standalone introduction

## Non-Goals

- Rewriting product UI
- Expanding engineering scope
- Adding new computational behavior
- Building a separate marketing site
- Reworking repository architecture
