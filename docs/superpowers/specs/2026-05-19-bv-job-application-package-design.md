# BV Job Application Package Design

## Goal

为 `BV PV Design Review Workbench / BV 光伏结构设计审核工作台` 制作一套用于岗位投递的展示包，使 HR 和技术经理在极短时间内理解两件事：

1. 候选人真正理解光伏结构设计审核工作流  
2. 候选人已经把这套审核工作流产品化，并做出了可运行原型

这套展示包不是普通作品集，也不是单纯产品官网，而是一个**岗位定制投递包**。

## Audience

### Primary

- HR / 招聘专员
- 非结构专业但需要快速判断岗位匹配度的招聘协同方

### Secondary

- 技术经理
- 结构审核负责人
- 可能参与复核的部门负责人

## Positioning

本投递包采用以下表达顺序：

1. **先证明候选人懂岗位**
2. **再证明候选人做出了与岗位一致的产品**

因此，首页和附件的表达重点不是“我做了一个漂亮产品”，而是：

> 我理解第三方光伏结构设计审核的真实职责，并把这套职责拆成了可运行、可追溯、可交付的工程审核工作台。

## Language Strategy

- 以**中文**为主
- 关键产品名与少量专业名词保留英文
- 不做中英并列双语布局
- 避免面向 HR 的阅读负担过高

## Deliverables

第一版交付包含四项：

1. **公开展示页**
   - 可公开访问的静态页面
   - 用于邮件正文中的主链接
2. **1 页 PDF**
   - 作为正式附件
   - 用于 1 分钟内完成“岗位匹配证明”
3. **6-8 页 PPT**
   - 用于技术面或二面时快速讲解
   - 也可作为补充附件发送
4. **邮件正文**
   - 直接可投递
   - 强调岗位相关性、链接与附件价值

## Non-Goals

以下内容不在本轮范围内：

- 不开发新的审核计算功能
- 不修改 `BV Review` 后端逻辑
- 不接入新的外部结构分析软件
- 不把投递站做成营销风格官网
- 不做复杂 CMS、表单收集或登录功能

## Core Narrative

整套投递包围绕同一叙事主轴：

### Narrative 1: 我懂岗位

候选人理解的不是抽象“结构设计”，而是第三方审核语境下的：

- 审核范围定义
- 审核依据构建
- 资料完整性判断
- 风险与不符合项识别
- 审核计划与 ITP
- 结构校核路径
- 设计审查报告输出

### Narrative 2: 我做出了产品化证明

候选人不仅会讲工作流，还把这套流程做成了：

- `Project Review Intake`
- `Review Basis Builder`
- `Design Document Checklist`
- `Structural Review Path`
- `ITP & Review Plan Generator`
- `Risk & Nonconformity Register`
- `Design Review Report Composer`

### Narrative 3: 我知道当前边界

候选人不会把 demo 冒充成熟商业系统，而是明确说明：

- 当前是 screening / review-support level
- 当前首个场景模块聚焦门式刚架屋面光伏增载
- 质量体系流转、项目协同、外部软件接口仍是下一步补强项

## Public Site Design

### Site Role

公开展示页是整个投递包的**主入口**。  
它的任务不是完整替代简历，而是：

- 让 HR 愿意继续看
- 让技术经理在 2-3 分钟内判断这是强相关候选人
- 把 PDF / PPT / GitHub / 产品演示链接组织到一个统一入口

### Information Architecture

公开展示页采用 6 段结构：

#### 1. Hero

包含：

- 姓名或候选人身份标题
- 目标岗位标签
- 一句话价值主张
- 主按钮：`查看产品展示`
- 次按钮：`下载 PDF`
- 补充按钮：`下载 PPT` / `查看 GitHub`

Hero 的 headline 不写空泛口号，而写明确岗位价值，例如：

> 面向第三方光伏结构设计审核岗位的工程化作品证明

#### 2. Why Fit

用 4-6 个高密度条目说明候选人与 JD 的直接对应关系，例如：

- 独立审核图纸、计算书与技术规格书
- 解读并应用 GB / IEC / AS/NZS / Eurocode
- 输出 review plan、ITP、risk register、design review report
- 对荷载、节点、基础承载路径做 screening-level 校核

#### 3. Product Proof

展示当前产品的 4 个关键界面：

- BV 审核总览
- 评估结论
- 依据与追溯
- 报告导出

每张图只绑定一个结论，不堆砌描述。

#### 4. Why This Is Not Just An AI Demo

用短段落或卡片说明：

- 确定性 screening kernel
- basis / traceability
- 风险与不符合项结构化输出
- 设计审查报告导出

#### 5. JD Mapping

用简洁表格展示：

- JD 条款
- 对应产品模块
- 当前覆盖度
- 下一步补强项

这一段直接服务技术经理。

#### 6. Action Footer

底部固定提供：

- 公开 demo / GitHub / PR
- PDF 下载
- PPT 下载
- 邮箱 / 电话 / 微信（如提供）

### Visual Direction

视觉风格遵循以下原则：

- 工程与审核语境
- 安静、专业、密度适中
- 避免营销型 hero、大面积渐变和装饰性卡片堆叠
- 首屏必须让人立刻知道这是**光伏结构设计审核**相关产品，不是泛 AI 页面

## PDF Design

### Role

PDF 是 HR 最容易真正打开的附件，因此它必须承担“快速解释”的责任。

### Format

- 1 页 A4
- 中文为主
- 高信息密度，但不拥挤

### Content Blocks

建议结构：

1. 标题区
   - 姓名
   - 目标岗位
   - 产品名
2. 核心结论区
   - 我对岗位的理解
   - 我已经做出的产品证明
3. 能力映射区
   - 3-5 条 strongest evidence
4. 截图区
   - 2-3 张关键界面缩略图
5. 链接与联系方式区
   - 公开页面
   - GitHub
   - 联系方式

### PDF Success Criteria

读者在 1 分钟内应能回答：

- 这个人是不是在认真投这个岗位
- 这个人是不是理解 BV 第三方审核工作的结构
- 这个产品是不是能证明他的能力

## PPT Design

### Role

PPT 不是给 HR 首看，而是给技术面和后续沟通使用。  
它要比 PDF 更完整，但仍然克制。

### Page Structure

建议 6-8 页：

1. 我是谁 / 我为什么投这个岗位
2. 我对该岗位工作流的理解
3. 我做的产品：BV PV Design Review Workbench
4. 产品模块与 JD 职责映射
5. 关键界面与工程判断证明
6. 当前边界与下一步补强项
7. 为什么我适合这个岗位
8. 联系方式 / 链接

### PPT Tone

- 专业
- 不讲空话
- 不做模板化“自我吹捧”
- 把产品当证据，而不是把产品当唯一主角

## Email Copy Design

邮件正文必须足够短，目标是让 HR 愿意转发。

正文结构：

1. 我是谁
2. 为什么投这个岗位
3. 这个产品为什么与岗位强相关
4. 链接与附件说明
5. 简短礼貌收尾

禁止：

- 大段自我介绍
- 冗长项目经历罗列
- 堆砌技术名词

## Reuse Strategy

优先复用现有材料：

- `README.md`
- `docs/showcase/demo-guide.md`
- `docs/showcase/project-brief.md`
- `docs/showcase/assets/*.png`

新的投递包不重复发明叙事，而是将现有 BV Workbench 内容转成：

- 对外公开页面
- PDF 信息摘要
- PPT 讲述序列
- 邮件投递文本

## Implementation Boundaries

第一版实现应优先选择：

- 静态站点技术栈
- 本地可预览
- 可部署到 GitHub Pages / Vercel / Netlify
- PDF 与 PPT 文件在仓库内可追踪

不应该在第一版引入：

- 后端服务
- 数据库
- 复杂动画系统
- 账号系统
- 额外云依赖

## Success Criteria

如果这套投递包有效，HR 或技术经理在看到它之后，应形成以下判断：

1. 候选人不是泛泛做 AI demo，而是真的理解岗位职责
2. 候选人能把工程审核逻辑抽象成结构化产品
3. 候选人具备技术判断、产品组织和表达能力
4. 候选人值得进入面试环节

## Recommended Execution Order

实现顺序固定为：

1. 公开展示页
2. 1 页 PDF
3. 6-8 页 PPT
4. 邮件正文

这样可以最大化复用同一套叙事与视觉资产，减少重复劳动，并让 PDF / PPT 从已经完成的公开页中抽取内容，而不是各写各的。
