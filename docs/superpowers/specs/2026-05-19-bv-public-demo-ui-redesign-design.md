# BV Public Demo UI Redesign

## Goal

对当前公开在线 demo 与投递展示页进行一次统一的前端 UI 重构，使其更接近 `design-md` 的视觉气质，但仍保持工程审核工具应有的克制、清晰和高信息密度。

本轮重构要同时解决两个问题：

1. 当前在线 demo 的视觉表现仍然偏默认 Streamlit，产品感和审核工作台气质不够统一
2. 当前中英文切换存在混杂现象，中文页面仍会出现英文 UI 碎片

本轮目标不是做新功能，而是把现有 BV Workbench 和投递展示页收口成一套可对外展示的统一界面语言。

## Scope

本轮范围只包含：

- 在线 Streamlit demo 的界面重构
- `docs/job-application/` 投递展示页的界面重构
- 中英文文案切换与翻译收口
- 与上述 UI 行为直接相关的测试更新

本轮不包含：

- 结构审核内核变更
- `core/` 下任何计算逻辑调整
- BV Review 领域模型调整
- Portal Frame screening 逻辑调整
- 新增外部软件接口
- 新增登录、权限、数据库或后端服务

## Product Constraint

必须保留并明确以下边界：

- 这是 screening-level / review-support 工具
- 不替代正式结构设计、签章计算、法定审批或有限元分析
- `Portal Frame Rooftop PV Screening` 作为既有真实技术模块必须继续保留

本轮重构只能改变呈现方式，不能削弱现有审核工作流表达，也不能让产品看起来像营销页或泛 AI demo。

## Visual Direction

### Reference, Not Copy

视觉参考来自 `design-md`，但不直接复制其版式。只吸收这些特征：

- 留白干净
- 浅色主背景
- 单一克制强调色
- 操作按钮和状态提示的清晰层级
- 更接近“编辑器 / 工作台”的产品气质，而不是营销官网

### Chosen Direction

本轮采用：

> 全浅色、克制、工程化、信息层级清晰的统一工作台风格

不采用：

- 大面积深色 hero
- 强烈渐变背景
- 装饰性卡片堆叠
- 紫色 / 深蓝大面积氛围化色板

### Palette

视觉系统应遵循以下约束：

- 背景：极浅灰白
- 主内容面板：白色
- 分隔：轻边框与极轻阴影
- 文字：深灰而非纯黑
- 强调色：单一蓝色，仅用于关键动作、选中态、重点状态

### Tone

页面要传达：

- 这是结构设计审核工作台
- 这是可运行的工程化产品
- 这是用于专业判断支持的工具

页面不要传达：

- 营销官网
- 花哨作品集
- 通用 AI 助手

## Language Strategy

### Single-Language UI Rule

在线 demo 的界面语言必须严格单语：

- 中文页面只显示中文 UI
- 英文页面只显示英文 UI

允许保留英文的范围只有：

- 产品正式名 `BV PV Design Review Workbench`
- 已定义的标准名或规范简称，如 `GB`、`IEC`、`Eurocode`
- 用户自己输入的原文内容

除此之外，不允许在中文页面出现英文 UI 标签、按钮、告警、标题、区块名、状态文案或 demo 提示。

### Translation Ownership

当前散落在 `app.py` 中的硬编码文案，应统一收口到翻译层或集中式标签映射中。

本轮至少要统一以下类型：

- 顶部说明
- tab 名称
- 区块标题
- 指标卡标题
- 按钮文案
- 警告与提示语
- BV Review 相关摘要区块标题
- 公共演示边界声明

目标不是“减少混杂”，而是**消灭界面层混杂**。

## Streamlit Demo Redesign

### Page Role

在线 demo 的首页不是投递落地页，而是真实工作台的公开演示入口。

因此它必须满足两类读者：

- HR：第一眼知道这是结构审核工具，不是聊天界面
- 技术经理：点进去后能直接看到审核路径、依据、风险、报告导出

### Layout Strategy

整体继续保留现有 tab 工作流，不重写业务层。

页面结构应调整为：

1. 浅色顶部总览区
2. 清晰的产品边界说明
3. 主要工作 tab
4. 面板化内容区

### Top Overview Area

顶部总览区保持全浅色，不使用深色条带。

应包含：

- 产品标题
- 一句定位
- 公开 demo 边界提示
- 作品集 / 演示用途说明

视觉要求：

- 信息一屏内可扫完
- 重点在结构审核工作台定位，而不是视觉装饰
- 关键提示要明显，但不能像错误告警

### Tabs

必须保留当前工作流上的 6 个 tab：

1. `BV 审核总览` / `BV Review`
2. `评估结论` / `Assessment`
3. `项目输入` / `Project Input`
4. `依据与追溯` / `Basis & Traceability`
5. `报告导出` / `Report Export`
6. `门刚场景模块` / `Portal-Frame Scenario Module`

本轮不改 tab 结构，只改：

- tab 标题文案来源
- tab 内部视觉层级
- 模块间距
- 指标卡与分节样式

### BV Review Tab

这是当前公开 demo 的关键入口，需要重点重构视觉层级。

当前问题：

- 分节标题比较像表单堆叠
- 指标卡不够稳定
- 风险、依据、路径、ITP 的信息密度高，但扫描效率一般

重构后应达到：

- 输入区更像审核录入面板
- 结论指标卡更像审核总览卡
- 四块核心信息（basis / path / risk / plan）有一致的面板语言
- 报告预览区和导出动作有明确收口

### Other Tabs

`Assessment`、`Basis & Traceability`、`Report Export`、`Portal-Frame Scenario Module` 保持原有信息架构，但统一以下视觉规则：

- 分节标题层级一致
- 卡片边距一致
- 数值优先于解释
- 次级说明弱化
- 边界说明不重复堆叠

## Job Application Showcase Redesign

`docs/job-application/index.html` 必须与在线 demo 形成一套统一语言。

### Site Role

展示页仍承担：

- 投递首入口
- 对 HR 的快速解释
- 对技术经理的能力映射
- 跳转在线 demo 与下载附件

### Visual Rule

展示页不能继续保留当前“轻营销 landing page”气质，而应调整为：

- 浅色背景
- 更克制的首屏
- 更像工程产品封面而不是求职海报
- 更强的信息层级与表格/模块秩序

### Consistency Requirements

展示页与在线 demo 必须在以下方面统一：

- 色板
- 按钮语义
- 标题层级
- 产品命名
- 边界表达
- 中英用词口径

## Implementation Boundaries

本轮改动应优先限制在以下文件：

- `app.py`
- `src/structural_screening_agent/localization.py`
- 如有必要，少量新增 UI helper 文件
- `docs/job-application/index.html`
- `docs/job-application/styles.css`
- 相关测试文件

只有在 `app.py` 已明显过载、且小范围抽 helper 能显著降低混乱时，才允许新增轻量 UI helper。  
不做大规模页面组件化重写。

## Testing Requirements

本轮至少应覆盖这些验证：

1. `app.py` 编译通过
2. Streamlit smoke test 通过
3. 中文界面关键文案不再包含已知英文碎片
4. 英文界面不直接渲染中文固定文案
5. 展示页静态内容与链接断言仍通过

测试重点不在像素级视觉快照，而在：

- 页面可运行
- 结构未破坏
- 单语规则被约束

## Success Criteria

本轮重构成功的标准是：

1. 在线 demo 的首页与 BV Review 区域明显更像工程工作台，而不是默认 Streamlit 页面
2. 投递展示页与在线 demo 呈现为同一套产品语言
3. 中文页面不再出现英文 UI 混杂
4. 英文页面不再出现中文固定界面文案
5. 现有 BV Review 与 Portal Frame 工作流仍能正常运行
6. 改动范围保持在 UI 与翻译层，不侵入审核内核
