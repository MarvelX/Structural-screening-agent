# BV PV Design Review Workbench Design

## Goal

将当前 `Structural-screening-agent` 升级为 `BV PV Design Review Workbench`，中文名为 `BV 光伏结构设计审核工作台`。

该工具面向第三方审核工程师，用于光伏电站土建、钢结构、支架、基础、连接节点与既有屋面增载相关设计审核。第一版目标是形成一个可运行、可解释、可导出的作品集级产品原型，而不是只写展示文档，也不是从零重建一个新项目。

## Product Positioning

一句话定位：

面向第三方审核工程师的光伏电站土建、钢结构、支架与基础设计审核工具，用于生成审核计划、校核路径、风险清单、优化建议和设计审查报告。

该定位将现有项目从单一场景：

`Portal-Frame Rooftop PV Screening`

扩展为更完整的审核工作台：

`BV PV Design Review Workbench`

原有门式刚架屋面光伏增载能力保留为首个结构审核场景模块，用于展示工具具备真实确定性 screening kernel，而不是只有表单和文案。

## Audience

### Primary Users

- 第三方设计审核工程师
- BV 类技术服务岗位面试官
- 光伏项目业主侧技术负责人

### User Needs

用户需要快速回答：

1. 当前提交资料是否足以进入设计审核。
2. 审核依据应覆盖哪些法规、规范、项目技术要求和合同要求。
3. 哪些设计对象需要校核，哪些暂时无法审核。
4. 当前主要风险、不符合项和阻塞项是什么。
5. 应如何组织 ITP、review plan、后续行动和设计审查报告。

## Recommended Approach

在现有仓库内增加 BV Review Mode，而不是新建独立项目。

### Why This Approach

现有项目已经具备 BV 工具需要的底座：

- 确定性结构初筛 kernel
- `GB / AISC / Eurocode` 标准路径
- basis traceability
- 资料完整性判断
- 风险识别
- Markdown / Word / PDF 报告导出
- Streamlit 可运行界面
- pytest 测试体系

直接复用这些能力，可以让第一版更像真实工程产品，而不是单独做一套静态展示。

### Rejected Alternatives

#### New Standalone BV Project

优点是命名干净，结构可以完全围绕 BV 场景重新设计。缺点是会重复实现报告、规则、导出、UI 和测试体系，短期内不如基于现有项目有说服力。

#### Showcase Documents Only

优点是最快。缺点是没有可运行产品，无法证明工具链、规则引擎和报告导出已经落地。

## MVP Scope

第一版选择作品集版，兼顾展示完整性和真实逻辑。它应覆盖 BV 岗位职责映射，同时保留工程边界。

### In Scope

1. Project Review Intake
   - 收集项目类型、国家或地区、设计阶段、适用标准体系、客户要求和提交资料状态。
   - 支持标准体系选择：`GB / IEC / AS-NZS / Eurocode`。

2. Review Basis Builder
   - 自动组织审核依据。
   - 第一版覆盖结构和设计审核相关依据，例如 `GB 50797`、`GB 50017`、`IEC 62548`、`IEC 61215/61730` 相关边界、`AS/NZS`、`Eurocode`、项目技术规格书和合同要求。
   - 对每条依据标注适用对象、触发条件、证据需求和后续审核动作。

3. Design Document Checklist
   - 对图纸、计算书、技术规格书、项目规范、合同技术条款和厂家资料做完整性检查。
   - 输出缺失资料、不可审核项和可进入技术校核项。

4. Structural Review Path
   - 按对象组织审核路径：
     - 支架结构
     - 钢结构
     - 混凝土结构
     - 地基与基础
     - 连接节点
     - 荷载计算
     - 屋面或既有结构增载
   - 既有门式刚架屋面光伏增载模块作为 `rooftop_existing_structure_added_load` 场景接入。

5. ITP & Review Plan Generator
   - 生成项目特定设计审核计划和检查与测试计划。
   - 输出审核阶段、审核对象、输入资料、审核方法、责任角色、阻塞条件和交付物。

6. Risk & Nonconformity Register
   - 输出设计风险、错误、遗漏、不经济之处和不符合项。
   - 每条记录包含风险等级、触发依据、影响范围、建议措施和是否阻塞报告签发。

7. Optimization Advisor
   - 不替代正式设计，仅输出优化方向。
   - 第一版建议覆盖支架布置、基础形式、连接路径、防腐等级、施工可行性和资料补充路径。

8. Design Review Report Composer
   - 输出 BV 风格设计审查报告：
     - 审核范围
     - 审核依据
     - 资料清单
     - 主要发现
     - 不符合项
     - 技术风险
     - 优化建议
     - 后续行动
     - 审核边界声明

### Out of Scope

- 不做完整有限元计算。
- 不自动审 CAD 图纸。
- 不冒充正式签章审核。
- 不做完整电气设计校核。
- 不新增遥测、分析埋点或外部网络调用。
- 不把 IEC 组件认证、逆变器、电气保护等非结构审核内容扩成主线；第一版只保留与结构接口有关的提示，例如接地、桥架、支架布置和设备荷载接口。

## Architecture

### Existing System To Preserve

以下现有能力应保留并继续复用：

- `core/kernel.py` 的 screening outcome 合同
- `core/basis_registry.py` 的依据注册模式
- `rules/*.yaml` 的规则与选项配置方式
- `presentation.py` 的卡片式视图模型
- `report_generator.py` 与 `report_export.py` 的报告导出路径
- `app.py` 的 Streamlit 单应用入口
- `tests/` 中现有行为回归测试

### New BV Layer

新增 BV 审核层，建议使用独立模块，而不是把 BV 逻辑塞进现有 portal-frame kernel：

- `src/structural_screening_agent/bv_review/`
  - `models.py`：BV 项目 intake、审核对象、资料状态、风险、不符合项、review plan 等领域对象
  - `basis.py`：BV 审核依据构建器
  - `checklist.py`：资料完整性检查
  - `review_path.py`：结构审核路径生成
  - `risk_register.py`：风险与不符合项生成
  - `review_plan.py`：ITP 与 review plan 生成
  - `report.py`：BV 风格报告内容模型
  - `workflow.py`：把 intake、basis、checklist、path、risk、plan 和报告汇总成一个审核结果

该目录只负责 BV 设计审核工作流。现有门式刚架 screening kernel 作为可选子模块被调用，不反向依赖 BV 层。

## Data Flow

1. 用户在 BV Review Mode 中输入项目基本信息、标准体系、审核对象和提交资料状态。
2. `workflow.py` 将输入转成 BV 审核 case。
3. `basis.py` 根据国家地区、标准体系、审核对象和资料状态生成审核依据。
4. `checklist.py` 判断资料完整性，标出缺失资料和不可审核项。
5. `review_path.py` 生成对象级审核路径，例如支架、基础、连接、荷载、既有屋面增载。
6. 如果审核对象包含既有屋面增载，workflow 将现有门式刚架 intake 映射到当前 screening kernel，并引用其控制路径、计算结果、依据和风险。
7. `risk_register.py` 生成风险和不符合项。
8. `review_plan.py` 生成 ITP 与 review plan。
9. `report.py` 汇总为 BV 风格设计审查报告内容。
10. 现有导出层继续负责 Markdown / Word / PDF 输出。

## UI Design

第一版保留 Streamlit 单应用，不新建前端框架。

建议将页面标题改为 `BV PV Design Review Workbench`，中文展示为 `BV 光伏结构设计审核工作台`。

页面结构建议：

1. `审核总览`
   - 当前审核结论
   - 阻塞项数量
   - 主要风险等级
   - 当前可审核范围

2. `项目资料`
   - 项目 intake
   - 国家或地区
   - 标准体系
   - 审核对象
   - 提交资料状态

3. `审核依据与路径`
   - Review Basis Builder
   - Structural Review Path
   - 现有 traceability 卡片复用

4. `ITP 与风险清单`
   - Review Plan
   - ITP 条目
   - Risk & Nonconformity Register

5. `报告导出`
   - BV 风格报告预览
   - Markdown / Word / PDF 下载

6. `场景模块`
   - 保留既有门式刚架屋面光伏增载筛查
   - 后续扩展照片辅助识别、外部计算接口和更细的基础审核

## Report Design

BV 风格报告应中文优先，必要术语保留英文识别。

报告章节：

1. 项目与审核范围
2. 审核依据
3. 提交资料清单与完整性状态
4. 审核路径与方法
5. 主要发现
6. 不符合项与阻塞项
7. 技术风险与优化建议
8. 既有结构增载筛查摘要
9. 后续行动
10. 审核边界声明

报告边界声明必须明确：

- 本工具用于设计审核前期组织、资料完整性判断、风险识别和 screening-level 技术路径梳理。
- 输出不替代正式设计、第三方签章、有限元计算、施工图审查或 BV 官方签发流程。
- 所有自动生成的不符合项和优化建议均需由合格工程师复核。

## Error Handling And Boundaries

- 当必要项目字段缺失时，系统应给出可读的缺失资料提示，而不是生成看似完整的审核结论。
- 当标准体系与审核对象不匹配时，系统应降级为 `review_required` 或 `manual_confirmation_required`。
- 当既有屋面增载场景资料不足时，应复用现有 level_c 逻辑，不应硬算檩条或主门架比值。
- 当报告内容缺少 BV 审核所需章节时，测试应失败。

## Testing Strategy

第一版应以单元测试和轻量集成测试为主。

需要新增或更新的测试方向：

1. BV intake model 能表达国家地区、标准体系、审核对象和资料状态。
2. Review Basis Builder 能根据 `GB / IEC / AS-NZS / Eurocode` 和审核对象输出对应依据。
3. Document Checklist 能把缺失资料映射为不可审核项和后续动作。
4. Structural Review Path 能按支架、钢结构、混凝土、基础、连接、荷载和既有屋面增载生成路径。
5. Risk Register 能输出风险等级、触发依据、影响范围、建议措施和阻塞状态。
6. Review Plan 能输出 ITP 条目、审核方法、责任角色和交付物。
7. 既有屋面增载对象能复用现有 screening kernel 结果。
8. BV 报告预览包含审核范围、依据、资料清单、主要发现、不符合项、风险、优化建议、后续行动和边界声明。
9. 现有 `pytest -q` 继续通过。

## Migration Strategy

### Phase 1: BV Domain Layer

新增 BV 领域模型、basis builder、checklist、review path、risk register、review plan 和 report composer。该阶段可以先不大改 UI，重点建立可测试的后端合同。

### Phase 2: Streamlit BV Review Mode

将 App 标题和 tab 结构升级为 BV 工作台，同时将现有门式刚架模块收纳为场景模块。保留当前输入能力，避免一次性删除已稳定功能。

### Phase 3: BV Report Export

复用现有 Markdown / Word / PDF 导出能力，新增 BV 风格报告预览与导出内容。

### Phase 4: Showcase Refresh

更新 README、demo guide、project brief 和截图，使外部展示从结构初筛工具升级为 BV 光伏结构设计审核工作台。

## Success Criteria

第一版完成后，应满足：

- 本地 Streamlit App 首屏明确显示 `BV PV Design Review Workbench`。
- 用户可以输入光伏设计审核项目资料并选择审核对象。
- 系统能生成审核依据、资料完整性检查、审核路径、ITP、风险与不符合项和优化建议。
- 既有门式刚架屋面光伏增载能力仍可运行并进入 BV 报告。
- Markdown / Word / PDF 报告导出仍可用。
- 测试覆盖新增 BV 领域逻辑和报告章节。
- `pytest -q` 通过。

## Non-Goals

- 不重写整个仓库架构。
- 不引入新的 Web 前端技术栈。
- 不接真实 BV 内部系统。
- 不接真实 Midas、SAP2000 或 CAD 自动解析。
- 不新增需要 API key 的功能。
- 不宣传为 BV 官方产品。
