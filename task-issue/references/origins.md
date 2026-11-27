<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 八、对 tack-harness 的参考范围

参考版本：提交 `396888a5424c5c649bc72b60c20f0ceb75579ae1`。本节只描述该固定提交中可核实的内容，不把本模板新增机制归因于 Tack，也不据此要求安装或运行 Tack。

- README §4.3 描述需求分析流程：`analyze` 产出分析材料；`spec` 形成顶层设计与公共契约；`plan` 形成详细设计、施工图和任务清单；`tech-design` 是按需将已确认的 spec/plan 整理为技术评审文档，不应描述成独立于 plan 的必经设计决策阶段。
- README 的 `spec` 命令说明包含产品/测试决策在该环节关闭；`plan` 读取已确认的 spec/analysis，细化接口、SQL、验证方式、上线流程、模块划分和任务依赖。
- `tack/harness/reference/to-tickets.md` 先按垂直切片提出任务，再在第 4 步向用户展示任务标题、阻塞关系和交付内容，询问粒度与阻塞边缘是否合适；第 5 步才把**批准的任务清单**写入 `plan.md` 和 `status.yaml`。该文件本身不要求创建 GitHub Issue。
- `tack/harness/template/plan.md` 是详细计划模板，记录任务范围、依赖、可并行内容、验收标准和验证方式。
- `tack/harness/template/run-instruction.md` 是脚本运行说明模板，覆盖运行准备、脚本顺序、依赖与必需文件，并规定失败停止、续跑和输出位置；运行结果不应反向改写该运行说明本身。
- README §4.4 明确 `testcode`、`test`、`run` 为按需命令，不在主链路中强制占位；该提交在 code 完成后不主动询问“是否测试”。本模板与之不同：对 Issue 中已明确为必要的验收项，执行者必须尝试验证；环境缺失或失败要如实记 BLOCKED / FAIL / NOT_RUN，不能静默略过。
- README §4.5 中 `/tack commit` 会直接提交而无需二次确认；`/tack push` 执行推送；`/tack merge` 合并后提交并推送。因此本模板必须独立核对用户权限和 Issue 动作栏，不能因工具默认行为而扩大授权。
- README 提及 `harness/agents/` 中的独立上下文角色（包括 code-reviewer），也包含按需代码审查能力。本模板增加的不是“独立上下文”这个概念本身，而是将独立验证 agent 固定到每个任务的检查点，定义快照绑定、CONTINUE / CORRECT / HOLD 状态转换、验证者只读交付快照以及红性探针边界。这些是本模板的额外设计，不描述为 Tack 的原生机制。

本模板借鉴 Tack 的垂直切片、任务计划和运行说明分层，同时将任务承载位置调整为经确认的 GitHub Issue，并增加权限交集、发布确认门、双 Agent 检查点、快照身份、验证状态机和停止条件。不要把 Tack 的命令或权限默认值直接移植为本模板的授权。

固定提交链接：

- https://github.com/frcoder-lh/tack-harness/tree/396888a5424c5c649bc72b60c20f0ceb75579ae1
- https://github.com/frcoder-lh/tack-harness/blob/396888a5424c5c649bc72b60c20f0ceb75579ae1/README.md
- https://github.com/frcoder-lh/tack-harness/blob/396888a5424c5c649bc72b60c20f0ceb75579ae1/tack/harness/reference/to-tickets.md
- https://github.com/frcoder-lh/tack-harness/blob/396888a5424c5c649bc72b60c20f0ceb75579ae1/tack/harness/template/plan.md
- https://github.com/frcoder-lh/tack-harness/blob/396888a5424c5c649bc72b60c20f0ceb75579ae1/tack/harness/template/run-instruction.md

---
