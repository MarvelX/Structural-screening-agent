# 光伏电站设计审核多 Agent 工作流系统目标文档

## 1. 文档目的

本文档固化 `BV PV Design Review Workbench` 的下一阶段目标：从当前的 BV 设计审核工作台，演进为面向第三方光伏结构设计审核岗位的多 Agent 工作流系统。

本目标文档是后续开发的上位约束，优先级高于单个功能想法。任何 Agent 化、计算引擎、报告导出或交互界面扩展，都必须服从本文档中的工程责任边界。

## 2. 核心指导思想

先工作流产品化，再逐步 Agent 化。

系统不追求全自动设计审核，也不让大模型直接给出结构安全结论。正确分工是：

- 确定性规则、表单、状态机和计算引擎负责工程判断底座。
- Agent 负责资料整理、参数抽取、审核项组织、风险措辞和报告草稿。
- 工程师负责关键参数确认、质量门禁、技术判断和最终签发前确认。

一句话总纲：

```text
本系统以地面固定支架为首个落地场景，通过 MiniMax Agent 完成资料抽取、依据整理、风险措辞和报告草拟；通过工程师确认门禁锁定关键参数；通过 Python A+B 双计算引擎完成基础与上部构件的筛查级确定性校核；最终由工程师确认后形成第三方设计审查报告和 RFI 清单。
```

## 3. 首个落地场景

第一阶段聚焦：

```text
地面固定式光伏支架设计审核
```

优先覆盖：

- 光伏组件与固定支架结构体系
- 檩条、横梁、立柱、斜撑等上部构件
- 桩基、地基承载力、抗拔和抗倾覆
- 风荷载、雪荷载、自重和最不利内力
- 支架与基础、地基、排水、电气接地和电缆桥架接口

暂不覆盖：

- 跟踪支架完整控制系统审核
- 柔性支架完整动力分析
- 屋面夹具完整节点设计
- 全站自动 CAD 几何审图

## 4. 系统架构

系统采用三层架构：

```text
UI Layer
Streamlit 工程师工作台
支持场景 A 直接修改、人工确认和质量门禁

Workflow Layer
Orchestrator 状态机
7 个专业 Agent
项目状态、版本、RFI 和人工确认

Domain Kernel
Twin Calculation Engines
纯 Python 确定性计算引擎
规则表、Pydantic 校验和结构化错误
```

## 5. 长周期工作流与状态持久化

第三方设计审核不是一次性对话，而是数天到数周的异步流程。系统必须支持项目状态持久化。

核心状态包括：

- 项目基础信息
- 当前审核阶段
- 文件与资料版本
- 已抽取字段
- 审核依据
- 审核计划和 ITP
- 技术审核路径
- 计算运行记录
- 风险与不符合项
- RFI 和客户回复
- 工程师确认状态
- 报告草稿和版本

推荐状态流：

```text
Intake
-> Document Check
-> Basis Build
-> Review Plan
-> Engineer Data Lock
-> Calculation Check
-> Risk Register
-> Report Draft
-> Engineer Approval
-> Issue / RFI Closeout
```

每个阶段都应支持：

- `pending`
- `running`
- `blocked`
- `waiting_for_client`
- `waiting_for_engineer`
- `approved`
- `rejected`

MVP 阶段可以先用 SQLite 或本地 JSON 持久化，后续再迁移到 PostgreSQL。

## 6. 专业 Agent 矩阵

第一版规划 7 个专业 Agent。所有 Agent 输出必须是结构化数据，不允许只输出自然语言段落。

| Agent | 职责 | 落地策略 |
|---|---|---|
| Document Intake Agent | 资料完整性检查与核心参数抽取 | 计算书优先，图纸材料表辅助；不直接让 LLM 读取整本长文档后自由总结 |
| Basis & Code Agent | 标准、合同、法规和项目规范识别 | 根据国家、合同和项目要求推荐标准组合，最终由工程师确认锁定 |
| Review Plan Agent | 生成设计审核计划与 ITP | 根据项目阶段、资料状态和审核对象生成步骤快照 |
| Structural Review Agent | 拆分技术审核路径 | 拆成上部构件、基础抗拔、地基承载力、连接节点和接口风险链路 |
| Calculation Check Agent | 参数对齐与工具调用 | 将确认后的参数组织为 Pydantic 输入，调用 A+B 双计算引擎 |
| Risk & NCR Agent | 风险与不符合项草拟 | 将确定性计算结果和资料缺口转换为 TIC 风格整改措辞 |
| Report Composer Agent | 报告与 RFI 拼装 | 按报告模板拼装审核范围、依据、发现、风险、RFI 和边界声明 |

## 7. MiniMax API 使用边界

MiniMax API 用于 Agent 层，不用于直接产生工程安全结论。

允许用途：

- 资料摘要
- 字段候选值抽取
- 审核项组织
- 风险说明草拟
- RFI 文案草拟
- 报告段落初稿
- 中英文表达润色

禁止用途：

- 直接判断结构是否安全
- 直接判断满足规范
- 直接替代计算书
- 直接替代工程师签发
- 在缺少依据时生成确定性结论

所有 MiniMax 输出必须经过：

1. JSON 结构校验
2. Pydantic 类型校验
3. 证据来源校验
4. 工程师确认或规则校验

## 8. 资料抽取策略

MVP 不做“把几百页 PDF 直接丢给 LLM”的方案。

资料处理采用：

```text
文件解析 / OCR / 表格抽取
-> 关键词和章节定位
-> 结构化字段候选值
-> Agent 归纳与解释
-> 工程师确认锁定
```

每个抽取字段必须包含：

- 字段名
- 候选值
- 单位
- 来源文件
- 页码或章节
- 原文片段
- 置信度
- 是否人工确认
- 是否进入计算

关键字段示例：

- 基本风压
- 雪荷载
- 地基承载力特征值
- 侧阻力标准值
- 桩径
- 桩长
- 桩间距
- 支架倾角
- 立柱截面
- 横梁截面
- 檩条截面
- 钢材材质
- 最不利轴力
- 最不利弯矩
- 最不利剪力

## 9. 场景 A：工程师确认锁定机制

场景 A 是 MVP 的核心交互。

Agent 抽取出的支架规格、桩基尺寸、地勘参数和最不利内力，先进入 Streamlit 的 `st.data_editor`。

工程师可以：

- 修改字段值
- 修改单位
- 删除错误字段
- 补充缺失字段
- 标记来源不可信
- 锁定进入计算的数据

只有工程师点击“数据确认锁定”后，系统才能把数据传给确定性计算引擎。

未锁定数据不得进入：

- 基础验算
- 上部构件验算
- 报告结论
- 风险等级最终判断

## 10. A+B 双计算引擎

结构安全判断必须来自纯 Python 确定性引擎。

### 10.1 基础验算引擎 A

基础验算引擎用于筛查级校核：

- 单桩极限抗拔承载力
- 地基承载力
- 基础抗倾覆提示
- 输入参数完整性
- 地勘资料缺口

输入示例：

- 桩径
- 桩长
- 桩型
- 土层参数
- 侧阻力标准值
- 地基承载力特征值
- 上部结构反力

输出示例：

- 抗拔承载力比
- 地基承载力比
- 是否超过筛查阈值
- 缺失参数清单
- 工程师复核建议

### 10.2 上部支架构件验算引擎 B

上部支架构件验算引擎用于筛查级校核：

- 立柱强度应力比
- 立柱稳定性应力比
- 横梁强度应力比
- 檩条强度应力比
- 构件长细比提示
- 材料和截面参数完整性

输入示例：

- 构件类型
- 截面规格
- 钢材材质
- 截面面积
- 惯性矩
- 截面模量
- 计算长度
- 最不利内力

输出示例：

- 强度应力比
- 稳定性应力比
- 长细比
- 控制构件
- 超限项
- 风险等级建议

### 10.3 工具调用与防呆

每个计算工具必须有 Pydantic 输入模型。

如果出现以下情况，引擎必须返回结构化错误，不允许带病运行：

- 缺少必要字段
- 单位不明确
- 荷载为非法值
- 截面规格无法识别
- 材料强度缺失
- 地勘参数缺失
- 计算路径不适用当前项目

## 11. 4 大质量门禁

系统必须设置 4 个质量门禁。

### 11.1 资料门禁

资料不完整时，不允许输出完整技术结论。

典型阻塞：

- 缺少计算书
- 缺少结构图纸
- 缺少地勘报告
- 缺少支架厂家资料
- 缺少最不利内力

### 11.2 依据门禁

没有明确标准、合同或项目规范依据时，不允许输出正式审核判断。

标准可以由系统推荐，但必须由工程师确认锁定。

### 11.3 计算门禁

结构安全相关风险必须来自：

- 确定性计算结果
- 明确规则
- 资料缺口
- 工程师确认

不得由 Agent 直接生成。

### 11.4 签发门禁

报告草稿可以自动生成，但最终定稿必须经过工程师确认。

系统不得提供“AI 自动签发”能力。

## 12. 版本差分与 RFI 闭环

系统必须支持资料版本变化。

当客户补交资料或设计院修改图纸后，系统应形成：

```text
ProjectIntake V1
-> ProjectIntake V2
-> Field Diff
-> Affected Review Items
-> Incremental Recheck
```

优先实现字段级 diff：

- 新增字段
- 修改字段
- 删除字段
- 来源变化
- 是否影响已确认计算
- 是否重开风险项

RFI 应支持：

- 问题编号
- 责任方
- 触发依据
- 所需资料
- 当前状态
- 客户回复
- 是否关闭
- 是否触发增量复核

## 13. MVP 范围

第一阶段 MVP 做：

1. 项目状态模型
2. 资料版本模型
3. 抽取字段模型
4. 工程师确认模型
5. RFI 模型
6. 计算运行模型
7. Streamlit 人工确认入口
8. 地面固定支架参数表
9. A+B 双计算引擎接口草案
10. 报告草稿输入结构

第一阶段不做：

- 完整 CAD 审图
- 完整 OCR 流水线
- SAP2000 / PKPM / STAAD 实时集成
- 有限元分析
- AI 自动签发
- 客户自助门户
- 大规模项目协同系统

## 14. 与现有项目的关系

当前仓库已经具备：

- BV Review Mode
- Review basis
- Document checklist
- Risk register
- Review plan / ITP
- Report preview and export
- Portal Frame Rooftop PV Screening
- 光伏支架 3D 展示 tab

下一阶段不是推倒重来，而是在现有基础上新增：

```text
Persistent Project Review State
+ Review State Machine
+ Human Approval Gates
+ Ground-mounted PV structure spec
+ A+B deterministic calculation interfaces
```

现有 `Portal Frame Rooftop PV Screening` 必须继续保留，作为屋面光伏增载技术审核模块。新地面固定支架工作流作为第二个技术场景模块接入。

## 15. Phase Roadmap

### Phase 1：结构化工作流底座

目标：把业务流程对象化，不写任何 AI 调用。

交付：

- `ProjectReviewState`
- `ReviewPhaseStatus`
- `DocumentVersion`
- `ExtractedField`
- `PVStructuralSpec`
- `EngineerApproval`
- `CalculationRun`
- `RFIItem`
- `RiskRegister`
- Streamlit 人工确认入口

### Phase 2：Agent 结构化输出

目标：接入 MiniMax API，但只输出 JSON 结构化结果。

交付：

- Document Intake Agent prompt
- Basis & Code Agent prompt
- Risk & NCR Agent prompt
- Report Composer Agent prompt
- JSON schema / Pydantic 校验
- evidence trace 字段

### Phase 3：场景 A 工程师确认工作台

目标：让工程师可以直接修改、确认和锁定 Agent 抽取的数据。

交付：

- `st.data_editor` 参数表
- 字段确认状态
- 数据锁定按钮
- 解锁重审机制
- 质量门禁状态卡

### Phase 4：A+B 双计算引擎集成

目标：接入基础验算和上部构件验算的确定性 Python 工具。

交付：

- Foundation Engine
- Superstructure Engine
- Pydantic 输入模型
- structured error
- calculation run history
- risk trigger mapping

### Phase 5：报告与 RFI 闭环

目标：将审核结果形成可交付报告草稿和客户澄清清单。

交付：

- RFI register
- issue closeout status
- report draft composer
- Word / Markdown export
- review revision history

## 16. 成功标准

本目标达成后，系统应能做到：

1. 支持一个地面固定支架项目从资料输入到报告草稿的完整审核链路。
2. 所有关键参数都有来源、版本、置信度和人工确认状态。
3. 所有结构风险都有触发依据，不来自无约束自然语言生成。
4. 工程师可以在界面中修改、确认、驳回和锁定 Agent 输出。
5. 计算结果来自确定性 Python 引擎，并保留运行记录。
6. RFI 补资后可以通过版本差分触发增量复核。
7. 报告输出明确声明 screening-level / review-support 边界。

## 17. 最近开发切入点

下一步建议只做 Phase 1。

优先实现：

```text
ProjectReviewState
PVStructuralSpec
ExtractedField
EngineerApproval
CalculationRun
RFIItem
StateRepository
Streamlit 多 Agent 工作流 / 人工确认入口
```

这一步完成后，再决定是否引入 MiniMax、LangGraph、PostgreSQL 或更完整的文件解析流水线。
