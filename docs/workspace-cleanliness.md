# Workspace Cleanliness Policy

This repository is a long-running product workspace for the BV PV Design Review Workbench. Keep source changes small, tracked, and reviewable. Local runtime state and generated artifacts should stay out of Git.

## Ignored Local Artifacts

The following patterns are intentionally ignored:

- `__pycache__/`
- `*.py[cod]`
- `.pytest_cache/`
- `.DS_Store`
- `*.egg-info/`
- `.local_data/`
- `.venv/`
- `tmp/`
- `.superpowers/`
- `.pycache-check/`
- `* 2.py`
- `* 2.md`
- `* 2/`

## Safe cleanup candidates

These files and folders are local artifacts and can usually be cleaned after a status check:

- Python cache directories covered by `__pycache__/` and `*.py[cod]`
- Pytest cache covered by `.pytest_cache/`
- macOS metadata covered by `.DS_Store`
- temporary verification outputs under `tmp/`
- temporary compile cache under `.pycache-check/`
- packaging metadata covered by `*.egg-info/`

## Requires confirmation

Do not delete `* 2.py` or `* 2.md` duplicate local copies unless the user explicitly asks. They are known local duplicate files in this workspace.

Do not commit local runtime state. The `.local_data/` folder may contain persisted Streamlit demo or workflow state and should be reviewed before deletion.

Do not delete `.venv/` unless the environment will be rebuilt. It is local dependency state, not product source.

Do not delete `.superpowers/` unless the current planning or brainstorming state is no longer needed.

## Commit Gate

Before committing product work:

1. Check Git status and confirm only intentional tracked files changed.
2. Keep ignored artifacts out of Git.
3. Run the fastest relevant test first, then the broader suite for user-facing workflow changes.
4. Do not remove protected portal-frame capability or tests as part of cleanup.
