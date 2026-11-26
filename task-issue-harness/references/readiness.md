<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 附：启用前检查清单

- [ ] 本次需求、仓库和当前基线已核实。
- [ ] 已按 §2.1 对照人类确认结果或明确给定的定稿边界核对契约。
- [ ] 发布授权与契约批准依据均已核对。
- [ ] Issue 状态为 `APPROVED / STARTABLE`，当前正文与原批准记录和固定版本一致。
- [ ] 执行者权限与外部系统读写权限已逐项明确；空白项均按拒绝处理。
- [ ] 直接/间接依赖、lockfile、toolchain、replace/patch 和 stacked PR 增量已核对。
- [ ] 验收矩阵包含边界值、空值语义、异常路径、配置消费闭环和适用的红性验证。
- [ ] 适用的独立验证使用独立会话、独立工作区和只读交付快照。验证运行和探针使用各自独立副本。
- [ ] 已按 §6.2 确认宿主支持的执行模式，并取得对应的开工放行。
- [ ] PASS 证据绑定实际 snapshot_id、契约版本、环境和具体命令；coding agent 的声明未被当作独立证据。
- [ ] CONTINUE / CORRECT / HOLD 规则、两轮纠偏上限和 HOLD 恢复责任已明确。
- [ ] 敏感数据、凭据和日志按适用共享规则处理。
- [ ] Tack 参考只按指定提交描述，没有把本模板新增能力归因给 Tack。
