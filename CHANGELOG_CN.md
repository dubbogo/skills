<!-- SPDX-License-Identifier: Apache-2.0 -->

# 变更记录

中文 | [English](CHANGELOG.md)

## v0.1.1 - 2026-11-27

- 新增任务 Issue 交接、Python 项目 Rust 优化、工程化 PR 审查三个独立技能。
- **破坏性变更**：将 `task-issue-harness` 技能重命名为 `task-issue`；升级前需删除旧安装目录，并将 `$task-issue-harness` 调用改为 `$task-issue`。
- 将 PR 审查技能重命名为 `pr-review`。
- 将 Python → Rust 技能命名为 `py2rust`，并将项目配置改为按目标仓库核实。
- 拆分参考流程，保留审查规则 ID，索引 10 个仓库规则及历史诊断。
- 退役冲突的历史线程处理，记录来源摘要与工作区修订。
- 增加离线校验、回归测试和 Linux/Windows CI 配置。
- 补齐双语社区文档、非官方中文许可证与各包分发声明。

已从 `main` 发布为 `v0.1.1`；不表示真实任务验收。
