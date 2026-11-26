<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# Python 项目 Rust 优化参考索引

保留源文档节号；按当前单元风险加载。原文 `issue-harness.md` 的授权、契约与检查点方法在本包 [task-contract.md](task-contract.md) 中给出可独立执行的摘要；任务显式采用完整 harness 时仍以该任务选定的完整契约为准。原文 `review.md` 的证据方法在门禁与统计章节内落实，不自动开启 PR review。

| 原节号 / 标题 | 本包位置 |
|---|---|
| 0. 使用方式与任务参数 | [setup.md](setup.md) |
| 1. 角色、目标与范围 | [baseline.md](baseline.md) |
| 2. 当前事实基线：先核实，再复用 | [baseline.md](baseline.md) |
| 3. 正确性与执行边界 | [correctness.md](correctness.md) |
| 4. 分析阶段：交付可评审的选型计划 | [planning.md](planning.md) |
| 5. 单元实施循环 | [implementation.md](implementation.md) |
| 6. 桥接、打包与回滚 | [packaging.md](packaging.md) |
| 7. 门禁与完成标准 | [gates.md](gates.md) |
| 8. 差分格式与语义矩阵 | [semantics.md](semantics.md) |
| 9. 跨会话状态与证据 | [state.md](state.md) |
| 10. 统计口径与汇报纪律 | [reporting.md](reporting.md) |
| 11. 每个单元的交付格式 | [delivery.md](delivery.md) |
| 附：可直接使用的短提示词 | [daily.md](daily.md) |
