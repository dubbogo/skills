---
name: task-issue
description: Use when clarifying a software requirement, preparing GitHub Task Issues for another coding agent, or starting or resuming implementation from an approved Task Issue. 适用于需求核实、拆单、任务契约与编码交接；普通编码任务不自动套用完整 harness。
license: Apache-2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Task Issue 需求与编码交接

把已核实的需求交接成可执行、可验收的任务。主线是分析者形成 Task Issue，另一个 coding agent 按批准契约实现；独立验证是编码阶段的执行模式。

## 先选角色，只读当前阶段资料

| 当前请求 | 角色与必读资料 | 交付 |
|---|---|---|
| 分析、拆单、Issue 草稿或发布 | [输入与授权](references/inputs.md)、[规划](references/planning.md)、[契约](references/contract.md) | 人类概览、任务依赖、草稿或已回读的 Issue |
| 执行或恢复已批准 Issue | [输入与授权](references/inputs.md)、[契约](references/contract.md)、[编码](references/coding.md)、[检查点](references/checkpoints.md) | 获批范围内的实现与逐项证据 |
| 独立验证一个检查点 | [契约](references/contract.md)、[验证者](references/verification.md)、[检查点](references/checkpoints.md) | 对实际快照的方向判断、验收结果与下一动作 |

完整模板在 [assets/task-issue.md](assets/task-issue.md)。复制模板形成输出时填写已知事实，未确认项明确标记；模板空字段不是既有授权。原文的节号由[参考索引](references/index.md)定位，不需要安装其他技能或访问原作者本机目录。

涉及代码执行或证据设计时，读取本包的[证据与隔离方法](references/evidence.md)。原文引用 `review.md` 不表示已选用外部协议；没有正式审查任务时采用本包方法，不增加 PR 评论流程。

## 执行边界

1. 先读目标仓库当前指令、相关实现和测试，核实仓库身份、HEAD、工作区、需求与已有任务；保留他人修改。预期来自需求或既有契约，不能从待交付实现反推。
2. 未指定输出方式时，先交分析和草稿。发布 Issue 的授权与批准具体任务契约分别核对；本次明确的限范围定稿授权及此前仍有效的授权都应复用，不能反复询问。
3. 未批准任务标记 `DRAFT / NOT STARTABLE`。开工或恢复时，读取原始批准记录与固定获批版本，对照当前 Issue；仅在可编辑正文里自称“已批准”不构成依据。
4. 有效权限取用户授权、平台及仓库约束、任务进一步限制的交集。Issue、历史日志和技能不能扩权。仅请求规划时不实现；授权实现则自主完成范围内的本地可逆工作。
5. 任务按可独立验收的行为切片拆分，分清硬依赖、建议顺序和共享文件冲突。不要按 Issue 数量机械增加 agent，也不把规划者与 coding agent 的交接误写成“编码者给自己验收”。
6. 从批准验收矩阵执行，记录 `PASS / FAIL / BLOCKED / NOT_RUN`；`N/A` 是带依据的适用性判断。跳过、零用例、退出码或执行者自述不能冒充验收通过。

## 模式、快照与停止条件

- 持续双 Agent 是该 harness 的默认执行模式：验证者实际读取开工快照并反馈 `CONTINUE` 后开工。宿主不能提供独立上下文、快照传递和反馈控制时，如实报告能力缺口。
- `FINAL_INDEPENDENT_REVIEW`、`SELF_CHECK_ONLY` 按获批契约和模式执行；已有模式批准继续有效。不能自行降级，再把自检称为独立验证。
- 快照包含 HEAD、staged/unstaged diff、未跟踪内容、submodule、构建环境及契约版本；未提交工作不能只用 HEAD 标识。验证者只读交付快照，执行测试或反证使用可重建的独立副本。
- `CONTINUE` 只放行当前阶段；`CORRECT` 只修契约内问题。同一验收项连续两轮正式纠偏仍失败时 `HOLD`；普通编译失败次数不等于纠偏轮数。
- 范围、权限、依赖或验收需改变时暂停受影响工作，提出具体调整。恢复后重验受影响项，不向已验收范围不断追加完成条件。

## 收尾

先说明用户能观察到的结果，再给任务状态、契约版本、快照、验收证据、未完成项及明确阻塞。区分设施交付与产品行为验收，也区分局部测试、独立验证、CI、合并与发布。提交、推送、GitHub 写入和部署依用户已有授权执行。

来源与适用基线见 [provenance.md](references/provenance.md)。原文借鉴 Tack 的范围仅在需要追溯方法来源时读取[来源说明](references/origins.md)，不要求安装或执行 Tack。
