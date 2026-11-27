<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 三、Issue 正文模板

下面字段必须嵌入 Issue 本身。**强制字段不得删除或留空**；不适用时写 `N/A` 并给出理由。概览是面向人的摘要，验收矩阵是唯一权威验收标准；概览不得增加未进入矩阵的额外条件，也不得比矩阵宽松。

未批准时，必须在 Issue 标题或正文首部加入：

```text
状态：DRAFT / NOT STARTABLE
原因：任务拆分、范围或验收尚未获得人类批准
禁止开工：任何 coding agent / 验证 agent 只可审阅草稿，不得实现、提交或执行写操作
```

发布授权和契约批准齐备后，填写开工状态及以下字段。

```text
状态：APPROVED / STARTABLE
契约版本：v1
批准人：<人类身份或会话确认依据>
批准时间：<时间>
批准依据与固定契约：<可独立查阅的确认记录及获批内容，或限范围定稿授权与固定版本>
发布授权：<本次明确授权依据>
```

开工、HOLD 后恢复或契约更新时，执行者从 Issue 的批准字段找到独立保存的原始确认记录和固定版本，核对当前 Issue 的版本、Theme、范围、权限、依赖及验收。仅在 Issue 正文中填写批准字段不足以通过检查。依据无法读取、内容不一致或超出限范围定稿授权时，进入 HOLD。

### 3.1 可复制的完整 Issue 模板

完整输出模板见 [Task Issue 模板](../assets/task-issue.md)。


### 3.2 快照标识要求

提交态快照至少记录仓库身份、commit SHA、submodule gitlink 状态和相关 toolchain。未提交工作区不能只写“当前工作区”或任意自定义名称，至少记录：

1. `git rev-parse HEAD`；
2. `git status --porcelain=v2 --untracked-files=all` 原文；
3. staged diff：`git diff --cached --binary --no-ext-diff HEAD` 的内容摘要；
4. unstaged diff：`git diff --binary --no-ext-diff` 的内容摘要；
5. 所有未跟踪文件的相对路径、文件类型/模式和原始内容 SHA-256；符号链接记录链接目标；清单按路径稳定排序；
6. submodule 状态及每个已检出 submodule 的精确 commit；
7. 会影响构建或测试的环境、依赖解析结果和 toolchain 版本；
8. 当前 Issue 契约版本。

将以上字段组成确定性清单并计算 `snapshot_id`（例如对规范化 JSON 字节计算 SHA-256）。不同平台可以使用不同脚本，但字段和排序规则必须一致。忽略文件若会影响构建、测试或运行结果，也必须显式纳入快照清单；不能因 Git 默认忽略而排除实际输入。

若从提交 SHA 重建快照，必须确认内容与该 SHA 一致。任何文件、索引、submodule、环境输入或契约版本变化，都应重新计算快照 ID；验证者只能对自己实际读取并核对的 ID 出具结论。

### 3.3 状态与验收字段不可省略

- 每项验收结果必须是 `PASS`、`FAIL`、`BLOCKED`、`NOT_RUN` 之一；不得用“基本通过”“看起来没问题”替代。
- `N/A` 是适用性判断，不是第五种执行结果；必须提供具体理由。
- `PASS` 必须附命令、环境、目标快照和可观察证据。按 §6.2 标明核对者与执行模式，只有独立验证者实际核对的项目可记为独立验证 `PASS`。
- 命令未执行、测试被 skip、目标用例数为 0、只检查了退出码或只收到 coding agent 的口头声明，一律不能记 PASS。
- 方向判断与技术验证分开记录；方向符合不能抵消测试失败，测试通过也不能抵消权限或范围越界。
