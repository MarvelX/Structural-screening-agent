# BV JD Feature Mapping

本文件用于把 BV 光伏结构设计审核岗位职责映射到 `BV PV Design Review Workbench` 的现有产品模块、当前覆盖度和下一步补强项。它可以直接用于作品集、面试讲解或岗位投递材料。

## 使用方式

- 面试开场：说明这个项目不是泛用 AI demo，而是把第三方光伏设计审核岗位拆成可运行、可追溯、可测试的工作台。
- 技术讲解：从“资料 - 依据 - 审核计划 - 工程师门禁 - 确定性计算 - 风险 / RFI - 报告”串起完整链路。
- 边界说明：明确当前是 screening-level / review-support 工具，不替代正式设计、不替代 BV 官方签发、不做完整 CAD 自动审图、不做完整有限元分析。

## JD 条款 - 产品模块 - 当前覆盖度 - 下一步补强项

| JD 条款 | 产品模块 | 当前覆盖度 | 下一步补强项 |
|---|---|---|---|
| 负责对光伏电站项目的土建、钢结构、支架及基础工程设计图纸、计算书和技术规格书进行独立、全面的审核 | `Project Review Intake`、`Design Document Checklist`、`Structural Review Path`、地面固定支架人工确认表、既有屋面门式刚架筛查模块 | 已覆盖资料状态录入、结构图纸 / 计算书 / 技术规格书 / 地勘报告 / 厂家资料 / 合同要求的完整性检查；已按支架、钢结构、混凝土、基础、连接、荷载、既有屋面增载拆分审核路径 | 增加更细的支架构件、基础、连接节点、腐蚀耐久和施工可行性 checklist；后续接入解析脚本或 OCR，但不做完整 CAD 自动审图 |
| 根据公司质量体系、客户要求和相关标准，确保设计审核工作的质量 | `ProjectReviewState`、阶段状态机、工程师确认门禁、报告草稿门禁、Agent engineer review queue | 已有资料门禁、计算门禁、Agent 产物复核、报告草稿阻塞理由和结构化 evidence；客户要求可进入 intake 并影响审查范围 | 增加质量体系模板、审核人 / 复核人角色、内部审核记录和项目级审批日志 |
| 解读设计规范、国家和国际标准（如 GB, IEC, AS/NZS, Eurocode 等）并应用于审核实践 | `Review Basis Builder`、标准体系选择、basis traceability、`GB / IEC / AS/NZS / Eurocode` 映射 | 已支持 GB、IEC、AS/NZS、Eurocode 标准体系选择，并把适用依据映射到 review objects 和报告依据章节 | 增加条文级 clause reference、风 / 雪 / 地震荷载路径和地区化规范适用性提示 |
| 审查并理解适用的合同要求、法规、技术标准和项目规范 | `Project Review Intake`、客户要求输入、`Review Basis Builder`、合同资料 checklist | 已把合同技术要求作为资料项，支持客户要求文本进入项目 intake；basis builder 可把项目规范和合同要求作为审核依据的一部分 | 增加合同条款摘录、法规清单、项目规范差异记录和合同优先级冲突提示 |
| 定义和审查项目特定设计审核计划、检查与测试计划及相关程序 | `ITP & Review Plan Generator`、`ReviewPlanAgentOutput`、review plan 表 | 已根据项目阶段、资料状态和审核对象生成 ITP / review plan，包含方法、责任角色、交付物和阻塞条件 | 增加公司程序模板、hold / witness / review point 分类和可导出的 ITP 表格 |
| 执行或监督设计审核工作，并出具专业的设计审查报告 | `Local Agent Workflow Runner`、`Risk & NCR Agent`、`Design Review Report Composer`、Markdown / Word / PDF 导出 | 已支持本地 deterministic agent workflow、工程师复核队列、报告草稿门禁、BV 风格报告预览及 Markdown / Word / PDF 导出 | 增加报告 revision history、审核人签名状态、RFI closeout 后的再签发流程；继续声明不替代 BV 官方签发 |
| 保持内外部沟通，与客户、设计院及承包商进行技术联络 | `RFIItem`、RFI register、客户回复、增量复核触发、`Foundation Review Evidence Path` 草稿 RFI | 已有 RFI 问题编号、责任方、触发依据、所需资料、状态、客户回复和是否触发增量复核；报告门禁能识别未关闭 RFI；基础证据路径可把地勘参数证据缺口转换为工程师复核后的草稿 RFI，例如 `foundation_evidence_blocked_geotechnical_parameters` | 增加客户、设计院及承包商联系人视图、澄清历史、会议纪要和责任方 SLA |
| 识别设计中的潜在风险、错误、遗漏及不经济之处，并提出优化建议 | `Risk & Nonconformity Register`、`Optimization Advisor`、report findings | 已生成风险 / 不符合项 / 优化建议，风险带等级、触发依据、影响范围、建议措施和是否阻塞报告签发 | 增加成本 / 施工可行性维度、典型错误库、优化建议分类和关闭验证要求 |
| 对结构荷载计算、连接节点设计、地基承载力计算等进行校核 | 既有门式刚架屋面光伏 screening kernel、Foundation Engine、Superstructure Engine、Calculation Check Agent、基础证据路径 | 已有屋面光伏增载筛查；地面固定支架已接入基础抗拔 / 地基承载力筛查和上部构件强度、稳定、长细比筛查级计算接口；计算结果保留运行记录和结构化错误；基础证据路径会在地勘报告、地基承载力特征值或桩侧阻力标准值证据不足时阻止计算并生成草稿 RFI | 增加连接节点 force path、风 / 雪 / 地震荷载组合、基础抗倾覆、构件库和更强的单位校验 |
| 独立就设计相关的技术问题做出判断和决策 | 工程师数据锁定、Agent review approve / reject、报告草稿门禁、签发边界声明 | 已实现人工确认字段、锁定计算输入、批准 / 驳回 Agent 产物、阻塞报告草稿和结构化 evidence；系统把独立技术判断保留给工程师，不让 Agent 直接作结构安全结论 | 增加多级 reviewer、判断依据备注、争议项记录和复核意见追踪 |
| 向客户推广 BV 的服务与解决方案 | `Service Scope Recommendation` 方向、job application microsite、作品集 narrative | 当前 README、showcase 和 job application 页面已把工具定位为第三方光伏设计审核工作台，能展示 BV 服务与解决方案价值：资料审查、风险发现、RFI、报告交付 | 增加服务范围建议模块，把资料缺口和风险项映射到可建议的 BV 服务包，但避免变成 CRM |
| 负责设计项目管理工作 | `ProjectReviewState`、阶段状态、RFI 状态、calculation run history、agent event trace、责任方 SLA 视图 | 已有项目状态、阶段流转、资料版本、RFI、工程师确认、Agent 事件追踪和报告门禁证据；RFI、增量复核和 Agent 复核待办已带打开时间，可在责任方视图中显示超期状态和最早到期日 | 增加项目 dashboard、任务责任人、时间线、报告 revision history 和长期状态持久化视图 |

## 当前覆盖度总结

当前产品已经覆盖岗位职责中的核心审核链路：

1. 项目 intake：项目类型、国家 / 地区、设计阶段、标准体系、审核对象、客户要求、资料状态。
2. 审核依据：GB / IEC / AS/NZS / Eurocode 和项目资料的 basis traceability。
3. 资料完整性：结构图纸、计算书、技术规格书、地勘报告、厂家资料、合同要求。
4. 技术路径：支架、钢结构、混凝土、基础、连接、荷载、既有屋面增载。
5. 多 Agent 工作流：资料接收、依据整理、审核计划、结构路径、计算校核、风险 / NCR、报告编制。
6. 工程师门禁：字段确认、计算锁定、Agent 产物批准 / 驳回、报告草稿门禁。
7. 确定性计算：屋面门刚筛查、基础筛查、上部支架构件筛查，均保留输入和运行记录。
8. RFI 闭环：客户补资、版本差分、增量复核、未关闭 RFI 阻塞报告草稿；基础证据路径可生成 `foundation_evidence_blocked_geotechnical_parameters` 等草稿 RFI。
9. 报告输出：BV 风格报告预览，Markdown / Word / PDF 导出。

## 面试表达建议

可以用下面这段话概括项目价值：

> 我没有把这个岗位理解成“让 AI 自动审图”。第三方光伏设计审核的核心是资料完整性、规范依据、工程计算、风险判断、RFI 闭环和报告责任边界。所以我把岗位职责拆成一个可运行的 BV PV Design Review Workbench：Agent 负责资料整理和文案草稿，确定性规则和 Python 计算引擎负责工程底座，工程师通过门禁确认关键参数和最终判断。

## 边界声明

本项目当前是 screening-level / review-support 工作台：

- 不替代正式设计。
- 不替代 BV 官方签发。
- 不替代注册工程师或资深工程师的最终判断。
- 不做完整 CAD 自动审图。
- 不做完整有限元分析。
- 不做全电气设计校核，只保留与结构审核相关的接地、电缆桥架和布置接口提示。
