# Streamlit Demo Deploy

## Target

- Platform: Streamlit Community Cloud
- Entrypoint: `app.py`
- Branch: `main`
- Public URL: `https://bv-pv-design-review-workbench.streamlit.app/`

## Deployment Notes

- `requirements.txt` uses `-e .` so Community Cloud installs the local package together with the dependencies declared in `pyproject.toml`.
- The public build is intended for portfolio review and demo walkthroughs.
- The app should keep the existing `BV Review` workflow and the portal-frame scenario module unchanged.
- The top of the app should show a public-demo boundary note so visitors understand this is screening-level only.

## Post-Deploy Verification

- Open the app root and confirm the title is `BV 光伏结构设计审核工作台`.
- Confirm the top banner contains `Public Demo`.
- Confirm the tabs include `BV 审核总览`, `评估结论`, `依据与追溯`, `报告导出`, and `门刚场景模块`.
- Confirm report downloads still render for both the BV review preview and the portal-frame flow.
