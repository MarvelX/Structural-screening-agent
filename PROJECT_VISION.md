# BV PV Design Review Workbench｜长期产品目标

## 1. 产品定位

本项目基于现有 `Structural-screening-agent`，逐步构建一个面向 BV 光伏设计审核工程师岗位的工程审核工作台：

`BV PV Design Review Workbench`

它不是一次性面试 demo，而是一个长期作品集产品，目标是持续展示：

- 工程判断能力
- 标准理解能力
- 设计审核流程能力
- 风险识别能力
- 技术沟通能力
- 报告输出能力
- 工程工具产品化能力

本工具不做泛泛 AI 聊天助手，而是一个有明确工程边界、审核逻辑、证据链和报告输出能力的 PV design review workbench。

## 2. 长期覆盖范围

终局目标是尽可能覆盖 BV PV design review 相关岗位职责，包括但不限于：

- 光伏电站土建设计审核
- 钢结构设计审核
- 支架系统审核
- 基础设计审核
- 荷载与组合审核
- 连接节点审核
- 设计图纸审核
- 计算书审核
- 技术规格书审核
- 合同要求审核
- 法规标准审核
- 项目规范审核
- 设计审核计划
- ITP / Inspection and Test Plan
- 风险识别
- 不符合项登记
- 优化建议
- 技术澄清
- 服务范围建议
- 设计审查报告输出

## 3. 现有模块保护原则

现有 `Portal Frame Rooftop PV Screening` 是第一个真实技术审核模块，必须保留。

后续 BV 相关逻辑应在清晰边界下扩展，不应破坏现有功能。

原则：

- 不删除现有 Portal Frame Rooftop PV Screening 功能。
- 不把现有模块硬改成泛化工具。
- 新增 BV Workbench 层作为独立产品化框架。
- 技术审核模块可逐步接入 Workbench。
- 所有扩展保持小步、可验证、可回滚。

## 4. 核心工作流

产品主流程应逐步形成以下闭环：

```text
Project Intake
-> Review Basis
-> Document Completeness
-> Review Plan / ITP
-> Technical Checks
-> Risk & Nonconformity Register
-> Optimization Advice
-> Review Report
-> Client Clarification
```

每一步都应尽量形成结构化数据、规则判断、证据链和可导出的审核成果。

## 5. 产品边界

本工具必须明确表达：

- 它是 screening / review support 工具。
- 它不是正式签章设计。
- 它不是完整有限元分析软件。
- 它不能替代注册工程师或项目负责人最终判断。
- 它的输出应作为设计审核辅助、风险提示、资料完整性检查和技术沟通支持。

所有报告中应保留类似边界说明：

```text
This workbench provides rule-based screening and design review support only.
It does not replace formal engineering design, statutory approval, stamped calculation,
or project-specific professional judgment by qualified engineers.
```

## 6. 判断原则

结论优先来自：

1. 确定性规则
2. 审核依据
3. 标准条文映射
4. 输入数据
5. 证据链
6. 可追溯判断
7. 结构化风险等级

LLM 只用于：

- 辅助解释
- 报告润色
- 技术沟通草稿
- 澄清问题生成
- 审核意见组织
- 面试讲解材料生成

不允许直接由 LLM 无依据地产生工程结论。

## 7. 标准体系

长期应支持：

- GB
- IEC
- AS/NZS
- Eurocode
- AISC

现有 GB / AISC / Eurocode 能力继续保留。新增标准体系需要模块化管理，并尽量让每条规则包含：

- `rule_id`
- `applicable_standard`
- `clause_reference`
- `input_required`
- `check_logic`
- `severity`
- `evidence`
- `recommendation`

## 8. 功能与 BV 岗位职责映射

每个功能都应能回答：

```text
这个功能对应 BV 岗位 JD 中的哪一项职责？
它展示了什么工程能力？
它能在面试中如何讲解？
它能输出什么可展示成果？
```

建议长期维护映射文件：

`docs/bv-jd-feature-mapping.md`

示例：

```text
功能：Document Completeness Checker
对应职责：Review drawings, calculation reports, technical specifications and project documentation.
展示能力：资料完整性审核、项目规范理解、审核计划制定。
输出成果：Document Gap Register、Clarification List。
```

## 9. MVP 优先级

先做作品集版 MVP，再逐步扩展真实工程审核能力。

第一阶段 MVP：

1. BV Workbench 首页 / 项目入口
2. Project Intake 表单
3. Review Basis 选择与记录
4. Document Completeness Checklist
5. Portal Frame Rooftop PV Screening 接入
6. Risk & Nonconformity Register
7. Review Report 导出
8. Interview Story / Portfolio 页面

目标不是一开始覆盖所有标准，而是形成一个完整闭环。

## 10. 开发原则

每次开发前必须：

1. 检查现有代码结构。
2. 检查已有测试。
3. 明确修改范围。
4. 小步实现。
5. 补充测试。
6. 保留回滚可能。
7. 不破坏现有 Portal Frame 功能。

推荐开发节奏：

```text
Inspect -> Plan -> Implement -> Test -> Document -> Commit
```

## 11. 最终输出物

项目长期应形成以下成果：

- 可运行界面
- 结构化规则库
- 审核模型
- 输入数据模板
- 测试用例
- 风险登记表
- 不符合项登记表
- 设计审核报告导出
- 客户澄清问题清单
- 服务范围建议
- 面试讲解材料
- 项目 README
- 作品集展示页面
