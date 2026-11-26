<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 网关、召回与上下文

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-012"></a>

## 检出能力依赖模型版本与上下文完整性（外部来源，未在本仓复现）

- 来源：Anthropic 2026-04-23 事故复盘。一个缓存清理 bug 穿透了多轮人工审查、自动审查、单元测试、端到端测试、自动化验证和内部试用；事后用 Code Review 回测同一 PR，在提供完整仓库上下文时 Opus 4.7 找到、Opus 4.6 未找到。
- 判据：引用任何自动审查结论时，必须绑定模型/规则版本与实际上下文范围（只给 diff 还是给全仓）；“某工具没发现问题”不能写成“不存在问题”（`R05`、`R15`）。复现或反证疑难缺陷时，优先补全仓库上下文，而不是在同一上下文里反复追问。
- 关键词：`validated_at: 无（外部来源，未在本仓复现）`、`validated_ref: anthropic.com/research/april-23-postmortem（2026-04-23）`、`applies_to: 使用 LLM 审查工具、复跑历史 PR、判断“工具零 findings”语义时`、`recheck_when: 工具默认上下文策略或模型版本变化时`。
- 边界：单一案例，不构成“新模型必然更强”的通用结论；不得据此把模型版本当作证据等级。

<a id="exp-038"></a>

## gh CLI 凭据失效时用 git credential 取回同一账号 token（不改动任何凭据状态）

- `validated_at: 2026-10-18`、`validated_ref: 本轮通知扫描（notif 抓取失败重试）`、`toolchain: gh 2.x / Git for Windows credential manager`、`applies_to: 本机 gh 全部只读与评论调用`、`recheck_when: gh 重新执行 `gh auth login`、或 hosts.yml 改回内联 oauth_token`。
- 现象：`gh api` 一律返回 `Get "https://api.github.com/...": EOF`，`gh auth status` 报 `The token in keyring is invalid`，但同一时刻 `curl` 与 Python `urllib` 直连 api.github.com 均正常 ⇒ 不是网络或代理问题，而是 gh 取不到可用 token。注意 EOF 是误导性症状，不要据此判断网络受限或去关沙箱。
- 处理：`git credential fill`（input: `protocol=https` / `host=github.com`）可拿到同一账号 token（`credential.https://github.com.helper` 链含 `gh auth git-credential` 与 `manager`）。把它注入 `GH_TOKEN` 后所有 `gh api` / `gh pr view` 恢复正常，剩余额度 5000 证明是认证态而非匿名态。写法：落一个 `ghw.sh` 包装脚本，内部 `export GH_TOKEN="$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')"` 再 `exec gh "$@"`；每轮 Bash 工具会重置 shell，逐条命令都要经过该包装。禁止回显 token（R14），只打印长度。
- 附带判据：`reviews` / `comments` 端点里 copilot 的评审可能是 **配额失败** 的空评审（正文 "reached their quota limit"，无行内线程）。不要把它当作"已审且无问题"的证据。

<a id="exp-068"></a>

## 镜像内 `PYTHONPATH` 注入不会自动进入测试自己 spawn 的子进程

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2197`（head `7b9ff4cb`，`tests/test_system_cli.py::test_codex_runners_report_non_utf8_cmd_errors`）、`applies_to: 用 `PYTHONPATH=<镜像>/src` 复用工作区 venv 跑隔离镜像的所有审查`、`recheck_when: 改为在镜像内建独立 venv 或以 `uv run --project` 执行`。
- 现象：被测用例内部用 `subprocess.run([sys.executable, "-X", "utf8", "-c", probe])` 再跑一个解释器，该子进程重新 `import powercontext`。只给 pytest 进程设 `PYTHONPATH` 时子进程也继承，但如果子进程拿不到（或夹具重置了环境），它会回落到工作区 editable 安装，于是「子进程版本」与「镜像版本」不同：本例首轮表现为 `Cannot run codex mcp list: [WinError 2]`（工作区旧实现仍用裸名 `codex`），第二轮才暴露真实断言。
- 判据与处理：读完用例先确认它是否 spawn 子进程；有则把 `PYTHONPATH` 写进**环境变量**（而非只用 `sys.path.insert` 包装），并让报错文本暴露被测实现（本例 `_run_codex_*` 的 `Cannot run <command>` 里含解析后的完整路径，正是最好的版本指纹）。报错里出现"被测包版本相关的旧符号/旧消息"时，先按镜像注入失败处理，不要归因 PR。

<a id="exp-071"></a>

## 流式请求的 idle 看门狗看到的是「模型事件流」，不是「字节流」

给推理请求加「chunk 间隔超时」时，最容易误判的一步是把"心跳/保活帧"当成会重置看门狗的活动。实测在 pydantic-ai 上不成立。

- **实战（PowerContext PR #2202，2026-10-23）**：`StreamingAggregateModel.request` 用
  `asyncio.wait_for(anext(events), idle_timeout)` 包住 `Model.request_stream()` 的迭代器。`events` 是
  `StreamedResponse.__aiter__`，它只代理 provider 的 `_get_event_iterator()`，而后者只对内容事件 yield。
- **事实链（`anthropic 0.117.0` + `pydantic-ai 2.29.0`）**：
  1. `anthropic/types/beta/beta_raw_message_stream_event.py` 的事件联合**没有 ping 成员**；
  2. `_base_client._process_response_data` 走 `construct_type`，对 `{"type": "ping"}` 返回
     `BetaRawMessageStartEvent`（`.type == "ping"`、`message` 未设置）；
  3. `AnthropicStreamedResponse._get_event_iterator` 命中 `isinstance(..., BetaRawMessageStartEvent)` 后走
     `if event.message is None: continue`（该分支原为 Bedrock 的无类型 chunk 而写），既不 yield 也不更新时间戳。
  ⇒ 心跳帧在 wrapper 层完全不可见，所谓 idle 是「两次被 yield 的模型事件之间的间隔」。
- **一行复现（无需网络）**：`anthropic._models.construct_type(type_=BetaRawMessageStreamEvent, value={"type": "ping"})`
  打印类型与 `message` 是否为 None 即可确认构造落点。
- **审查判据**：看到 `wait_for(anext(...))`、`asyncio.timeout` 包流、或"空闲 N 秒超时"时，先问三件事——① 迭代的是 provider
  事件还是原始字节流（是否包了 httpx stream）？② 文档/docstring 是否写 "between chunks"（chunk 在运维语义里包含心跳）？
  ③ 用例里有没有"只有心跳、没有内容事件"的窗口？三者都对不上即为 P2 措辞/覆盖缺口，而不是实现错误。
- **定级口径**：心跳不重置看门狗本身可以是取舍；可评论的是「文档与 docstring 声称 chunk 级、实现是事件级」以及缺少 ping-only 用例。
  影响有限（需要长窗口且期间无内容事件），按 P2。
- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2202`（head `de087fd0`，回复 4354525192）、
  `toolchain: anthropic 0.117.0 / pydantic-ai 2.29.0 / Python 3.14.3`、
  `applies_to: 任何在 provider 抽象层之上实现的流式空闲超时`、
  `recheck_when: anthropic SDK 把 ping 加入事件联合、pydantic-ai 改变 _get_event_iterator 的过滤方式、或改为在 transport 层计时`。

<a id="exp-082"></a>

## 归因 job 超时：用相邻 `PASSED` 时间戳算单条成本，并找同日对照 PR

**现象**：某 job 以 `The action '<name>' has timed out after N minutes` 结束，日志里没有断言失败，容易被当成 runner 抖动。

**判据**：
1. 从 job 日志提取相邻 `PASSED` 行的时间戳，算单条用例耗时（`%H:%M:%S` 相减），得到稳定的单条成本；
2. 用「剩余用例数 × 单条成本」验证是否必然超预算，而不是临界抖动；
3. 找一个**同日、同矩阵、同一 runner 类**的对照 PR（同仓库同时段），比较单条成本。差异显著时归因给 PR，
   而不是环境；
4. 若该 PR 引入了新的每用例初始化（迁移 DDL、建表、启动服务），把「初始化条数」也量化出来，作为因果证据。

**反例**：只在单个 job 上看到超时就写"CI 抖动"，或反之直接归因 PR 而不做同日对照——两者都缺证据。

`validated_at: 2026-10-27`；`validated_ref`: #2246 head `71d5b44a`（19/21 用例后 40 min 超时，单条 140–160 s）
对照 #2258 head `0614869d`（同 21 条用例，单条 90–100 s，26 min 完成）；
`applies_to`: 任何带步级超时的 e2e/acceptance job；`recheck_when`: job 预算或用例集合变化。
