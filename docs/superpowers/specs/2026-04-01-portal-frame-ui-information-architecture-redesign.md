# Portal Frame UI Information Architecture Redesign

## Goal

Replace the current single-page, information-dense Streamlit UI with a tab-based structural review interface that is easier for project managers and technical leads to scan.

The redesign must:

- reduce first-screen information overload
- remove mixed Chinese/English wording from the main UI
- make the evaluation outcome visually dominant
- separate calculations, basis/traceability, report export, and future calculation integrations
- preserve the current screening kernel, persistence, and report pipeline

This is an information-architecture redesign, not a new product scope.

## Problems in the Current UI

The current page has several structural issues:

1. Input, evaluation, basis, assumptions, report preview, and explanatory text all compete on one page.
2. Simplified calculation values and formulas are rendered in the same card body with no visual hierarchy.
3. Demo-era narrative panels and report-preview panels dilute the main engineering decision flow.
4. The main UI still carries mixed bilingual phrasing that is acceptable for exports but noisy for on-screen review.
5. The page still behaves like a "workbench + preview + demo shell" instead of a focused structural screening application.

## Product Direction

The main UI should now behave like a structural screening application for one specific workflow:

- enter portal-frame rooftop PV screening inputs
- review the current screening conclusion
- inspect the supporting basis and traces
- export the report
- understand where future integrations such as calculation sketches and Midas/SAP interfaces will plug in

## Information Architecture

The new main page should use five tabs:

1. `项目输入`
2. `评估结论`
3. `依据与追溯`
4. `报告导出`
5. `计算扩展`

The default open tab should be `评估结论`.

### Language Strategy

Main UI language must be strictly single-language:

- Chinese UI shows only Chinese
- English UI shows only English
- bilingual rendering remains only in exported reports

This applies to:

- section headings
- card titles
- helper notes
- tab labels
- report-preview labels embedded in the UI

## Tab Design

### 1. 项目输入

This tab replaces the current sidebar-heavy intake flow.

Layout:

- one in-page form
- grouped sections
- no extra narrative panels

Input groups:

1. `项目基本条件`
   - 规范体系
   - 建筑类型
   - 结构体系
   - 屋面类型
   - 拟改造内容
   - 新增荷载

2. `主门架参数`
   - 跨度
   - 柱距
   - 檐口高度
   - 钢材标号
   - 门架梁截面
   - 门架柱截面
   - 檩条形式
   - 檩条间距

3. `屋面与连接`
   - 屋面板类型
   - 屋面板厚
   - 波高
   - 连接偏好
   - 防水敏感性
   - 限制安装区域

4. `证据与复核路径`
   - 图纸完整性
   - 构件表状态
   - 节点连接资料
   - 厂家资料
   - 腐蚀状况
   - 现场调查
   - 可用复核路径
   - 停工约束

### 2. 评估结论

This is the default landing tab and must prioritize decision-making.

First-screen blocks:

1. `初步结论`
2. `控制因素`
3. `关键计算结果`
4. `证据状态`

Display principles:

- `初步结论` must be visually dominant
- `控制因素` must state the current governing item in one sentence
- `关键计算结果` must show values first and formulas second
- formulas should be visually weaker than result values
- `证据状态` should summarize readiness, not restate the whole evidence tree

### 3. 依据与追溯

This tab explains why the result was produced.

Order:

1. `触发的依据条目`
2. `输入追踪`

Display principles:

- basis entries should show title, citation, and basis id
- traces should show normalized field labels, not raw dotted paths where avoidable
- this page is for technical defensibility, not for the primary decision summary

### 4. 报告导出

This tab is an export center, not a full report-reading page.

Content:

- export button(s)
- short report summary
- small preview snippet only

It must not render the full report body in the same heavy way as the current UI.

### 5. 计算扩展

This tab is an interface-preparation page for future capabilities.

It should reserve clear slots for:

- `计算简图`
- `Midas / SAP`
- external calculation IO boundary
- future formal review integration notes

This tab is intentionally non-functional in V1, but its information architecture must make future expansion easy.

## Calculation Presentation Rules

The current "calculation + explanation + formula in one card" pattern should be replaced with explicit hierarchy.

For each key calculation item:

- primary display: item name + value
- secondary display: short interpretation
- tertiary display: formula

Recommended examples in `评估结论`:

- 檩条强度比
- 檩条挠度比
- 主门架梁筛查比值
- 主门架柱筛查比值
- 主门架控制筛查比值

Detailed formulas can remain visible on-screen, but they must not compete with the values.

## Display Contract Changes

The current `WorkbenchView` contract is too broad and reflects old page structure.

The redesign should move toward a tab-oriented presentation contract with focused view models for:

- input tab
- conclusion tab
- basis/traceability tab
- export tab
- extension tab

The redesign does not need to delete all old fields immediately, but the new UI should not be driven by the old monolithic view shape.

## Out of Scope

This redesign does not include:

- new structural calculation methods
- new persistence schema
- Midas or SAP execution
- calculation sketch generation
- report format redesign beyond what is needed for export-center integration

## Success Criteria

The redesign is successful if:

1. The main UI no longer feels like a stacked demo page.
2. The default screen makes the conclusion, controlling factor, and key calculations obvious.
3. The main UI is strictly single-language.
4. Basis/traceability information is separated from the main decision page.
5. Report export no longer dumps the entire report into the primary interaction flow.
6. A future calculation-extension tab exists with clear interface-preparation intent.
