<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 11. 每个单元的交付格式

```markdown
## 单元：<函数/算法边界>；桥接：<方案>；状态：<已验证/部分验证/阻塞>

- 概览与范围：<用户可观察变化、批准目标、不变量与非目标>
- 快照：<契约版本、参考/实现提交、相关 diff 与新增文件、实际构建身份和平台>
- 方向与独立验证：<符合/偏离/证据不足；自检/最终独立/过程独立；对应快照的反馈>
- 执行路径：<真实公开入口、扩展路径/身份、强制 Rust 的证据>
- 行为：<相关测试命令、结果、skip/阻塞、日志路径>
- 差分：<有效 N；一致/mismatch/未比较；规则与未覆盖契约>
- 处理路径：<R、F、E 与分母；不可测写 N/A>
- 性能：<负载、构建档位、桥接成本、样本/统计量、结果及限制>
- 门禁与产物：<逐项 PASS/FAIL/BLOCKED/NOT_RUN/不适用及依据；Rust、tool gate、项目检查、wheel 安装及 CI 实际选择集>
- 兼容与回滚：<持久化/API 影响、回滚验证、未验证项>
- 结论：<代码问题、证据缺口、默认入口接入状态；适用时另列审批/合并/发布状态>
- 下一步：<当前批准范围内的待办，或需要决定的具体变化>
```

分析阶段交付候选排序和可执行计划即可，不填虚构的 Rust 覆盖率，不宣称迁移完成。
