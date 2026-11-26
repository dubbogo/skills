---
name: engineering-pr-review
description: Use when reviewing a GitHub pull request, re-reviewing an updated Head, reconciling earlier findings, or assessing current merge readiness under an engineering review protocol. 适用于有证据的 PR 审查与复审；仅本地代码修改不自动触发完整 PR 流程。
license: Apache-2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# 工程化 GitHub PR Review

以当前仓库身份和精确快照审查 changed surface，结论来自源码或实际验证。用户另有指定协议时，使用选定版本；不叠加两份通用协议，也不让旧 review 技能覆盖本次协议的分级、评论和状态边界。

## 状态门禁先于 Diff

先读[协议范围与授权](references/protocol/00-scope.md)及[预检规则 R01–R04](references/protocol/01-preflight.md)，核实 `owner/repo`、repository id、PR、`state`、`isDraft`、目标分支和 Base/Head。

**非 OPEN PR 停止；Draft 默认跳过。** 只说明原因，不获取 Diff、不建镜像、不运行测试、不发评论。普通“工业标准审查”“再看一轮”或批量请求不等于明确要求审查 Draft；只有用户明确要求审查 Draft 才例外。

## 按阶段取资料

| 阶段或风险 | 读取 |
|---|---|
| 通过门禁后获取、核对 Diff 与调用链 | [§2 流程与 Diff](references/protocol/02-diff.md) |
| 需要完整源码、执行测试或探针 | R03/R04；[§3 工具、真实性与 CI 归属](references/protocol/03-validation.md) |
| 形成问题及定级 | [§4 Finding 与敏感信息](references/protocol/04-findings.md)，按 changed surface 取[§5 质量矩阵](references/protocol/05-quality.md) |
| 用户授权发布行内问题 | [§7 发布、回读、去重](references/protocol/07-comments.md) |
| Head 更新、旧问题改判或处理线程 | [§8 复审与止损](references/protocol/08-rereview.md) |
| 判断能否合并 | [§9 合并结论](references/protocol/09-merge.md) |
| 给当前用户交付 | [§10 收尾对账](references/protocol/10-report.md) |
| AI 辅助风险、获授权维护规则、环境诊断 | 按[协议索引](references/protocol/index.md)读取 §6、§11–§13 |

通过状态门禁后，从[项目索引](references/projects/index.md)按精确 `owner/repo` 选规则；特别区分 `apache/dubbo-getty` 和 `AlexStocks/getty`。再按路径、符号、风险读取相关条目，不加载其他仓库的规则。经验仅从[诊断索引](references/experience/index.md)按需检索，不是默认新增的门禁。

## 证据与发布约束

- 获取完整文件列表与 Diff，对账唯一文件数；审本层 stacked 增量，不把累计改动归责当前层。源码读取与本地执行按需要选择，不强制 checkout。
- 不切换用户开发目录。主证据 checkout 只读；不可信代码执行先核实 R04 隔离。独立目录不是沙箱，无合格隔离则采用源码证据或经核实的 CI，明确行为证据缺口。
- 先运行与实际风险相关的最小检查；同 SHA、平台和选择集的可信 CI 可复用。分清 PR 新增、Base 既有、工具与环境失败，不无目的重复全仓测试。
- CI 的关联 SHA 与实际 checkout SHA 分别记录。关联 H、实际 merge M 的成功是 M 的集成证据；不直接写成 H-only，也不只因两个 SHA 不同就宣告失效。核对真实命令、平台、目标包、用例数和关键 step。
- Finding 必须有位置、触发条件、实际影响、证据及修正方向，并排除未被本 PR 扩大的基线问题。缺测试、工具告警和个人偏好不直接映射为 P1；P0/P1/P2 由实际影响决定。
- 显式选用本协议执行 review 时，按 §0.3 的默认约定发布有证据的问题行内评论；用户要求仅本地报告时禁止发布。自动发现技能本身不授予新外部写入权限，已有授权继续有效。
- 发布前复核状态、Head、Finding 前提、当前 Diff 锚点及完整线程；Head 漂移先停止发布并复核，不能只替换 `commit_id`。按根因去重，已有同根因线程只补实质证据。HTTP 响应中断先查是否落库，不盲目重发。
- 只用具体问题行内通道；无线程且无相关可评论行时保留聊天报告。禁止 Conversation 总结、文件级凑锚点、Approve、Request Changes；Resolve/Unresolve、push、merge 等需用户对该动作的授权。

## 收尾和时效

自然中文，Findings 在前，不表扬、不凑意见。分别给代码审查、验证证据、GitHub 条件的结论；缺权限不是“无规则”，绿色 CI 或 MERGEABLE 不自动等于可合并。报告精确快照、覆盖范围、实测与源码判断、评论账目及缺口。合并建议不授权 merge。

历史项目条目保留验证日期、固定引用和适用范围；导入日期不刷新其验证日期。缺少元数据或前提变化时仅作调查线索，不能凭旧规则作当前归责或合并结论。稳定规则 ID 不重排；本包是新的维护源，原作者工作台无需存在。导入范围及修订见 [provenance.md](references/provenance.md)。
