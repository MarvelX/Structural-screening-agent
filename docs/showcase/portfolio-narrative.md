# Portfolio Narrative

这页用于面试或作品集讲解，回答一个问题：

> 为什么 `BV PV Design Review Workbench` 不是普通 demo，而是一个和 BV 光伏结构设计审核岗位强相关的工程化产品原型？

## 一句话定位

这是一个面向第三方光伏设计审核工程师的 screening-level / review-support 工作台。它把光伏项目的资料完整性、审核依据、审核计划、工程师门禁、确定性计算、风险 / RFI 和报告草稿组织成一条可追溯工作流。

## 岗位职责映射

完整 JD mapping 见 [docs/bv-jd-feature-mapping.md](../bv-jd-feature-mapping.md)。面试时可以把当前 MVP 讲成 7 个产品模块：

| 岗位职责 | 当前产品表达 |
|---|---|
| 审核图纸、计算书、技术规格书和地勘资料 | `Project Review Intake` 与 `Design Document Checklist` |
| 解读 GB / IEC / AS/NZS / Eurocode 等标准 | `Review Basis Builder` 与 basis traceability |
| 定义审核计划、ITP 和程序 | `ITP & Review Plan Generator` |
| 拆分土建、钢结构、支架、基础、连接和荷载路径 | `Structural Review Path` |
| 校核荷载、连接、地基承载力等关键问题 | 既有门刚筛查模块、Foundation Engine、Superstructure Engine |
| 识别风险、不符合项、遗漏和不经济之处 | `Risk & Nonconformity Register` 与 `Optimization Advisor` |
| 出具设计审查报告并维护 RFI 闭环 | `Design Review Report Composer`、RFI register、报告草稿门禁 |

## 为什么先做工作流产品化

第三方审核不是一次性聊天，而是长周期、多资料、多责任方的工程过程。当前 MVP 先把确定性底座搭起来：

1. 资料进入 `ProjectReviewState`，保留项目、阶段、资料版本和 RFI 状态。
2. Agent 产物进入结构化 Pydantic contract，不允许只留下自然语言总结。
3. 工程师通过 Human-in-the-loop 队列批准或驳回 Agent 产物。
4. 关键字段必须被工程师确认并锁定，才能进入计算。
5. 报告草稿被门禁阻塞，直到资料、计算、RFI 和工程师复核满足条件。

这条路线符合 [docs/pv-design-review-multi-agent-goal.md](../pv-design-review-multi-agent-goal.md)：先工作流产品化，再逐步 Agent 化。

## Human-in-the-loop 的产品价值

这个项目没有把结构安全结论交给 AI。Agent 只负责资料整理、审核项组织、风险措辞和报告草稿，工程师仍然保留关键判断权：

- 字段候选值可以修改、确认或排除。
- 计算输入必须被锁定。
- Agent 产物必须经过 approve / reject。
- 未关闭 RFI 和被驳回 Agent 产物会阻塞报告草稿。
- 报告输出保留 screening-level / review-support 边界。

## A+B 双计算引擎

当前地面固定支架方向采用 A+B 双计算引擎作为确定性内核：

- Foundation Engine：基础抗拔、地基承载力、输入完整性和结构化错误。
- Superstructure Engine：上部构件强度、稳定、长细比和材料 / 截面参数完整性。

它们的作用不是替代正式计算书，而是提供筛查级、可追溯、可复核的判断依据。后续可以继续扩展连接节点、风雪荷载组合、基础抗倾覆和腐蚀耐久路径。

## 当前 MVP 能展示什么

- BV 审核总览：项目 scope、审核对象、资料完整性、风险和报告预览。
- 评估结论：控制因素、关键计算结果、证据状态和下一步动作。
- 依据与追溯：标准路径、触发条件、证据需求和输入来源。
- 报告导出：Markdown / Word / PDF。
- 门刚场景模块：保留既有 Portal Frame Rooftop PV Screening 作为第一个真实技术审核模块。
- RFI 闭环：资料变更、字段 diff、增量复核和报告草稿阻塞。

## 当前边界

这个作品集原型必须清楚声明边界：

- 不替代正式设计。
- 不替代 BV 官方签发。
- 不替代注册工程师或资深工程师最终判断。
- 不做完整 CAD 自动审图。
- 不做完整有限元分析。
- 不做完整电气设计审核，只保留结构接口相关提示。

## 面试讲法

可以按下面顺序讲 3 分钟：

1. 我先说明岗位理解：BV 光伏设计审核的核心不是“画图”，而是资料、依据、校核、风险、RFI 和报告责任边界。
2. 我展示 `BV Review` tab：说明如何从项目 intake 进入审核 basis、document checklist、ITP 和 risk register。
3. 我展示 Human-in-the-loop：说明 AI 不做最终工程判断，工程师通过门禁锁定参数和 Agent 产物。
4. 我展示 A+B 双计算引擎：说明结构风险来自确定性 calculation run，而不是自然语言猜测。
5. 我展示报告和 RFI：说明这个工具最终服务第三方审核交付，而不是停留在聊天界面。

## 下一步补强

- 把 foundation evidence path 做细：地勘参数、桩型、承载力、抗拔和抗倾覆。
- 增加连接节点 force path 和腐蚀耐久 review rules。
- 给 report revision history 和 issue closeout 增加项目管理视图。
- 在保持工程师门禁的前提下，再接入 MiniMax API 做结构化资料抽取和报告草稿。
