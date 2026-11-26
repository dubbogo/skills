<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：网关、召回与上下文

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc46"></a>

## R-PC46. 两处易误判的归因：`locomo_plus` 不经过流式聚合；Desktop 三条红 job 的仓库基线签名（2026-10-24 实测）

**A. `evaluation/memory/locomo_plus` 不构造 `StreamingAggregateModel`。**

- 事实：`evaluation/memory/locomo_plus/models.py::open_model` 直接 `resources.enter_async_context(infer_model(name, provider_factory=...))`，
  `generate()` 走 `agent.run(...)`（非 `request_stream`）⇒ 该 harness 的推理路径上不存在 `src/powercontext/builtin/inference/pydantic_ai.py`
  的 `StreamingAggregateModel`，因此它新增的 `InvalidInferenceOutputError` detail（如 `provider stream ended without a completion signal`）
  **不可能**进入 `evaluation/memory/locomo_plus/runner.py::describe_error`。
- 判据：`runner.py` 的 `_KNOWN_DETAILS` 只是该 harness 的「可原样复制 detail」白名单；判断「PR 新增 detail 是否必须登记」前，先确认该 harness
  能否产生该错误。不可达 ⇒ 无实际影响，按 §4「说明实际影响、排除未扩大范围」不得开 Finding（2026-10-24 PR #2202 head `255d0969` 实例：
  两项候选 detail 未登记，但 harness 不流式，主动放弃发布）。
- 若要主张可观测性损失，替代证据应是「harness 使用的 `generate()` 路径也能产出该 detail」，而不是「白名单里少了字符串」。

**B. Desktop 三条红 job 属仓库基线，不据 job 名归责 PR。**

- 签名：`windows` / `macos (macos-15)` / `macos (macos-15-intel)` 三 job 均红在
  `desktop/src-tauri/tests/session.rs:289` 的 `bundled_qualification_allows_explicit_scope_browsing`，消息
  `the shipped preview needs a qualified Server for its current contract`（bundled `compatibility.json` 的资格记录与当前契约不匹配）。
- 归因判据（两条同时成立才算基线）：① 本 PR 的 `files` 里没有 `desktop/` 改动；② 同一时段**其它未改 `desktop/` 的 PR** 出现同签名红
  （2026-10-24 实测：#2202 `255d0969`、#2122 `e1002a7a`、仅改 `uv.lock` 的 #2214 `20aeed53` 三例同签名）。
- 边界：master `1da99747` 上没有这两个 job 的 check run，因此这组证据**不能**证明「master 自己跑也红」，只能证明「与 PR 改动无关」；
  要在报告里写成「master 基线失败」，须先在 master 上取得同一 job 的红证据，否则按「仓库基线状态被 desktop 流水线暴露」表述。
- 阅卷要点：#2096 这类「checks 全绿 + 无 CR + 仅差 approval」的 PR，用 `mergeable_state == blocked` + approval 计数表述，不要写成「CI 红/代码有问题」。

关键词：`validated_at: 2026-10-24`、`validated_ref: PR #2202 head 255d09695eabdb55c9519c8ab29b03398689ee67`、
`PR #2122 head e1002a7a4fc8fc73eab409768f6e15f142276568`、`PR #2214 head 20aeed53`、`master 1da997476651c2850ff7141e2b7cd512d0152a90`、
`toolchain: pydantic-ai 2.29.0（uv.lock 同版本）`、`applies_to: 本仓 evaluation harness 的 detail 白名单判断、desktop 流水线红 job 的归因`、
`recheck_when: locomo_plus 改为走 Runtime 的流式装配、`_KNOWN_DETAILS` 改为自动派生、desktop 资格校验通过或 `compatibility.json` 补齐当前契约记录`

<a id="r-pc112"></a>

## R-PC112. `scope.lock` 必须是 capture application span 的兄弟节点，位置由 `_capturing()` 的两个上下文管理器顺序决定（2026-11-10 实测 #2567）

`ScopedSourceApplication.capture()` 把 lock 作为 `_capturing()` 传给 coalescer；`_capturing()` 里必须先
`async with self._runtime._locked(scope_id)` 再 `with self._runtime._stage(_MEMORY_CAPTURE_STAGE, ...)`。
顺序反过来（stage 在外、lock 在内）时 `scope.lock` 变成 `memory.capture` 的子节点，
`tests/e2e/test_observability.py::test_memory_write_stage_spans_are_bounded_and_nested` 会在 `_only_child`
处报 `assert 0 == 1`。该用例不在 PR 的 diff 里，是本仓库既有的可观测性契约。

- 复核命令（WSL）：`PYTHONPATH=<mirror>/src:<pydeps> python -m pytest tests/e2e/test_observability.py -q`，
  单用例约 25s、整文件 18 passed 约 250s。
- 变异反证：交换这两个上下文管理器的嵌套顺序即精确复现 `assert 0 == 1`，说明该断言真的守住了拓扑。
- 该 PR 曾因这一处失败导致 31 个 suite job 级联 `skipped`（`needs.tests.result` 不含 failure），复验时不要只看
  `tests (*, e2e)` 一条，要看同一 head 的 suite job 是否真的跑过。

关键词：`validated_at: 2026-11-10`、`validated_ref: #2567 head 3562556f`、`toolchain: WSL + _shared/venv-wsl（3.13.11）`、
`applies_to: 任何把 Scope 锁/批次合并移进 `_stage` 或改写 capture 路径的 PR`、
`recheck_when: `_MEMORY_CAPTURE_STAGE` 常量、`_stage`/`_locked` 实现或 test_observability.py 的 span 契约断言变更`。

<a id="r-pc140"></a>

## R-PC140. 网关的"跳过召回"要分成 prepare / 注入 / 证据三步判；工具续写不注入会丢掉整回合的召回块（2026-11-24 实测 #2792）

- **三步不可合并**：`prepare`（向 Core 查询）→ `inject`（把块前置到最后一条用户消息，只改外发请求体）→
  `prepared_contexts`（送 `check` 时声明位置与 binding）。只跳过 `prepare` 是省一次服务调用；连 `inject` 一起跳过，
  模型在该回合后续请求里就没有召回内容了。判据是 `Executor::enrich` 的早退**在不在 `self.replays.get` 之前**：
  在之前 ⇒ 三步全跳；在之后且只对 `cached.is_none()` 生效 ⇒ 只跳查询。
- **客户端不会保留注入内容**（仓库自己的文章写明）：`docs/en/blog/posts/magpie-gateway-powercontext-memory.md`
  说 "The client usually knows nothing about it, so its history still contains only `U1` and `A1`"，并要求
  "Reusing that turn's reference block … keeps the context from changing halfway through tool execution"；
  配图 `docs/assets/blog/.../prompt-prefix.*.svg` 写 "The next request must replay the exact R1 block"。
  ⇒ 非用户回合不注入 = 工具续写阶段召回消失 + 前缀在 R1 处发散、provider 前缀缓存失效。改这块必须同时改这两份文档。
- **测试怎么读**：`sends(&gate)` 返回 `(body, declared)`；`declared.is_empty()` 就是"该次发送没有注入"。
  #2792 把 `a_replayed_tool_continuation_is_not_injected` 断言成 `sent[1].1.is_empty()`，等于把"续写不注入"写进测试，
  但同一 PR 正文仍声称 "A replay hit still injects the prepared block" —— 正文与 head 不一致时按 R02 当过期描述处理。
- **CI 证据是合并结果而非 head-only**：`gateway.yml` 的 check job 是 `cargo fmt --check` + `clippy --all-targets -D warnings`
  + `cargo test --locked --workspace`；日志首行 `HEAD is now at <merge> Merge <head> into <base>`，
  例如 #2792 为 `764a1a7 Merge 5cb73db5 into 5eb3f92f`。引用时按 R16 归为合并结果验证，并记下合并基准。
- **`base.sha` 可能滞后于 `branches/<base>`**：#2792 的 `pulls/2792` 报 `base.sha=95bc5733`，同一时刻
  `branches/master=eb695a10`，而 CI 合并基准又是 `5eb3f92f`。三点 Diff 一律用 `merge-base`，不要拿 `base.sha` 当分支 tip；
  跨仓 PR（`isCrossRepository=true`，head 在 `lizining1231/powercontext`）同样适用。

关键词：`validated_at: 2026-11-24`、`validated_ref: #2792 head 5cb73db5 / merge 764a1a7 / base 5eb3f92f / prior head 6f7bef9b`、
`toolchain: rust 1.95.0（CI）/ 1.96.0（本机，仅 types/protocol 可构建）`、`applies_to: master`、
`recheck_when: enrich 的早退位置或 replay 键变化、blog 的 prompt-prefix 章节改写、gateway.yml 的测试步骤变化`。

<a id="r-pc141"></a>

## R-PC141. 旧上游 URL 变量转为「启动致命」后，`var_os` 语义让测试里的「置空串」变成启动失败（2026-11-25 实测 #2630 / #2815）

- **判据是 `var_os(...).is_some()` 不是非空**：`gateway/crates/pc-gateway-app/src/main.rs` 对
  `PC_GATEWAY_UPSTREAM_URL` / `_CHAT` / `_RESPONSES` 三个变量做 `std::env::var_os(name).is_some()`，
  命中即 `tracing::error!` + `exit(2)`。#2815 的新用例 `chat_cost_extraction_extends_the_admitted_chat_prefix`
  为了压掉继承值写成 `("PC_GATEWAY_UPSTREAM_URL_RESPONSES", "")`，空串同样命中 ⇒ 子进程启动即退出；
  `gateway_behaviors.rs` 的 harness 只对 `Address already in use` 重试，其余启动退出直接判失败。
- **上游配置模型换代的连带面**：#2630 把 harness 从 `PC_GATEWAY_UPSTREAM_URL_CHAT/_RESPONSES` 迁到
  `PC_GATEWAY_UPSTREAM_PROFILE` / `PC_GATEWAY_UPSTREAM_PROFILE_RESPONSES`（2630 head 的
  `gateway/crates/pc-gateway-app/tests/` 已无任何 URL 变量）。任何在飞的 gateway PR 只要**新增**了 URL 变量用法，
  就会在 #2630 之后变红；检查手法：`git diff master <head> | grep '^+' | grep PC_GATEWAY_UPSTREAM_URL`。
- **文档侧同样两极**：`docs/{en,zh}/docs/operate/{deploy-server,install-gateway}.md` 已声明旧变量导致启动失败，
  而 `docs/*/docs/integrations/{langchain,langgraph,openclaw,pydantic-ai}.md` 仍让读者「设置
  `PC_GATEWAY_UPSTREAM_URL_RESPONSES`」。这批内容已在 master（#2759 一类文档 PR 合入），按 R-PC132 不能算在
  单个在飞 PR 头上，但报告里应作为仓库级不一致列出。
- **`PC_GATEWAY_API_KEY` 的必要性已扩到回环**：`main()` 的 `gateway_credentials` 对缺失直接 `ok_or` 退出，
  且要求与 `PC_GATEWAY_CORE_TOKEN` 不同（`if api_key == core_token` ⇒ exit）。核 install-gateway 文档时以此两条为准。

关键词：`validated_at: 2026-11-25`、`validated_ref: #2630 head 2530384e19 / #2815 head c9ededd12a`、
`toolchain: rust 1.95.0（CI）/ cargo test -p pc-gateway-protocol 本机可跑`、`applies_to: master`、
`recheck_when: main.rs 的旧变量拒绝名单或 gateway_credentials 变化、harness 的 env 注入方式变化、install-gateway 文档改写`
