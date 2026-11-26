<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 七、最短日常调用

已有主模板时，每次可以只发：

```text
按“需求分析 → 已批准 task Issue → 双 Agent 执行”模板处理 <需求链接>。
先核实需求和代码，再给人类可读概览、任务拆分和完整 Issue 草稿。
为总需求和子任务定义 Theme，写清允许范围、禁止事项、依赖、权限、边界值、空值语义、配置消费闭环、验证方式和停止条件。
验收矩阵是唯一验收依据；强制项不得省略，不适用必须说明理由。
默认等待我确认任务粒度、范围和验收后再发布 Issue；不要把“创建 Issue”理解为已经批准具体契约。
每条开发线配一个 coding agent 和一个独立验证 agent；验证者必须读取实际快照，不接受 coding agent 的总结作为 PASS 证据。
说明需要几个人类负责人、几对 agent、怎样并行，以及宿主如何传递产出和控制检查点。
模型未指定时不绑定 DeepSeek 或其他特定模型。
本次执行者权限：<逐项填写；未列出的提交、推送、PR、评论、合并、部署和外部写操作均不允许>。
Issue 发布授权：<无 / 我确认草稿后发布 / 明确授权直接发布>。
契约确认：<待确认 / 已明确批准的版本 / 明确授权在指定边界内定稿并开工>。
```

若本次只要草稿，明确写“仅输出分析和 Issue 草稿，不写 GitHub”。授权直接发布和授权在指定边界内定稿并开工时，分别填写对应字段。
