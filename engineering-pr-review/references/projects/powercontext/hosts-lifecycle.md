<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：宿主、并发与生命周期

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc04"></a>

## R-PC04. Pi 插件风险面

- 运行时第三方依赖只有两个：`@earendil-works/pi-coding-agent`（`defineTool`）与 `typebox`（`Type`）。其余全部是 `node:` 内置模块。
- `extensions/powercontext.ts` 的 `createRuntime()` 在插件加载时一次性 `resolveConfig()`，所有配置在 Pi 启动时定死；改环境变量必须重启 Pi。
- 环境变量 token 惯例：布尔类（`POWERCONTEXT_PI_CAPTURE_PROMPTS`、`..._FLUSH_ON_CAPTURE`、`..._ALLOW_INSECURE_HTTP`）经 `envBoolean` 统一 `toLowerCase()`，接受 `true/false`、`1/0`、`yes/no`、`on/off`；`envString` 会 `trim()` 且把空串视为未设置。新增的枚举型环境变量如果做精确字符串比较，就与既有惯例不一致，属于可评论点。
- `~/` 展开的既有约定：`optionalText(env.HOME) ?? homedir()` + `path.join(home, value.slice(2))`（见 `src/transport.ts` 的 `POWERCONTEXT_CLIENT_CONFIG_FILE`）。新增路径类配置应与之一致。
- 诊断链路：`runtime.diagnostic(event, error)` → `failureEvent` 归类 → `createDiagnosticEmitter`（按 `outcome` 做 60s cooldown）→ sink writer。诊断事件只含 `event` / `outcome` / `http_status` / `error_code` / `recovery`，**不含提示词或用户内容**，因此改 sink 不构成数据外泄风险。
- Pi TUI 用 stdout 做光标定位渲染：stderr 输出会串到输入栏。审查该插件的输出路径时，`src/commands.ts` 的 `console.log` 只在 `!context.hasUI` 时触发，不是 TUI 路径；真正的风险面是任何在 hook 内直接写 stderr 的代码。

<a id="r-pc07"></a>

## R-PC07. 宿主 hook 超时/预算：文档写的默认值不可信

- **代码是唯一基准**，默认值分散在两处，改一处无效：
  - `integrations/claude-code/plugins/powercontext/claude_code_settings.py`：dataclass 默认值（第 59-60 行）+ 同文件 `_environment_float("POWERCONTEXT_CLAUDE_REQUEST_TIMEOUT_SECONDS", default=3.0)` / `_environment_float("POWERCONTEXT_CLAUDE_HTTP_BUDGET_SECONDS", default=6.0)`（第 125-133 行）。
  - `integrations/codex/plugins/powercontext/settings.py`：`Field(default=3.0)` / `Field(default=6.0)`（第 128-129 行）。
- 实际默认值（两个宿主一致）：**请求超时 3.0 s、HTTP 预算 6.0 s**。
- 但 `docs/{en,zh}/docs/integrations/{claude-code,codex}.md` 的环境变量表仍写 **`1` / `4`**；截至 2026-09-23 在 master 与 PR #1708 head 上都是错的（base 起就错，非某 PR 引入）。
- 审查要求：任何新增文档里出现的 hook 超时数字，必须回到上述代码核对；沿用 1/4 的新增文案按 Finding 提出，并同时指出两张集成表已过期，避免两处互相印证错误数字。PR #1708 的 `docs/en/docs/workflows/repository-code.md:191` / `docs/zh/...:183` 即由此判 P2。
- **「宿主 hook 超时」与「插件请求超时」是两个量，文档常混写（2026-10-25 复核）**。插件侧 per-request 默认值：
  `claude-code` 3000 ms、`codex` 3000 ms（同 R-PC07 上文）、`kimi-code` 1000 ms（`shared/runtime.mjs` 的 `AbortSignal.timeout(1000)`）、
  `zcode` 1000 ms（`shared/transport.mjs` 的 `REQUEST_TIMEOUT_MS`）、`dsh` 1000 ms（`src/config.ts` 的 `DEFAULTS.requestTimeoutMs`）。
  宿主外层给 hook 的额度则是另一个数：`kimi-code` `kimi.plugin.json` 的 `timeout: 5`（秒）、`zcode` `hooks/hooks.json` 的
  5000/5000/1500 ms、`dsh` `DEFAULTS.timeoutMs` 4000 ms、`codex` 文档写明外层 hook 超时 10 s。
  ⇒ 文档写「keep it below the host's Hook request timeout, 1 second on Kimi Code, ZCode, and DSH and 3 seconds on the other Hook hosts」时，
  数字其实取的是插件 per-request 值，措辞却指向宿主外层额度；判 P2 前先确认这两种口径，别把「插件请求超时」当「宿主杀进程的时点」。

关键词：`validated_at: 2026-10-25`、`validated_ref: 7307e8e08fa230cac67743be7db77caa5e44302d`（PR #1708 Head，base `6fca8a75`）、`ddc14b0bad7a3dae70618ae72c4ac6e8de45420e`（PR #2231 Head，2026-10-25 五宿主超时复核）、`applies_to: master 上 integrations/{claude-code,codex,kimi-code,zcode,dsh} 及对应集成文档`、`recheck_when: 集成环境变量表的默认值列被修正、任一宿主的 hooks.json / plugin.json / config.ts 时额度变更、或 hook 默认值再次变更`。

<a id="r-pc17"></a>

## R-PC17. 工作区绑定键的身份语义必须跨宿主核对（本仓已有两套实现）

同一目录在不同写法下是否算"同一个工作区"，本仓各宿主并不统一；审查新增的 `kind: "workspace"` 绑定（或改其 key 计算）时必须横向比对。

- **两套实现**：`integrations/zcode/plugins/powercontext/shared/scope.mjs` 用 `realpathSync`（并叠加 `git rev-parse --show-toplevel`，子目录归到仓库根）；`integrations/claude-code/plugins/powercontext/scripts/workspace_scope.py` / `integrations/workbuddy/...` 用 `Path.resolve(strict=False)`。**kimi-code 的 `shared/runtime.mjs::workspaceKey()` 是唯一纯词法实现**（`resolve(cwd)` + sha256，子目录各自独立）。
- **后果不是报错，而是静默回落**：`builtin/scope/application.py::resolve_binding()` 的顺序是 explicit → binding_keys → default，且契约里 `allow_default` 默认 `true`。key 不命中 ⇒ 直接落到 Server 默认 Scope，客户端拿不到任何异常，于是记忆被写进错误的 Scope（2026-10-18 在 PR #2043 上按 P2 提出）。
- **必须实测的三类差异**：盘符/路径大小写（Windows 大小写不敏感但 hash 敏感）、junction/symlink 别名、`.`/`..` 与尾部分隔符（后者 `resolve` 会归一，前两者不会）。探针实例 `{WORKSPACE}\review\oceanbase-powercontext-pr-2043\probes\probe_workspace_key.mjs`：四种写法打印 hash，并用 `resolve_binding` 的判定顺序复现"落到默认 Scope"。
- **反向核对**：宿主文档若写 "SHA-256 of the normalized absolute working directory"，不要据此认定已做 canonicalization——`resolve` 只是词法规范化。e2e 里若把"别名与真实路径是不同身份"写成断言，要确认作者是否有意固定该行为，而不是测试掩盖了缺口。
- **相关的另一类缺陷**：`resolveScope()` 在**显式 Scope 已配置**时仍派生工作区键，会让 `isAbsolute` 校验变成 Hook 的硬前置（非绝对 `cwd` 从"照常注入"退化为 `workspace_required` 整条失败）。Base/Head 对照探针见 `probes/hook-cwd/probe_hook_cwd.mjs`。
- **2026-10-18 更新（head `6a514384`）**：kimi-code 已改为 `realpathSync.native` 方案（`resolve(cwd)` 后取真实路径，失败退回词法），`resolveScope()` 也已改成 `settings.scopeId ? [] : [workspaceKey(input.cwd)]`，上一轮两条 P2 均已解除。**残留形态**：`scripts/scope.mjs` 在 `loadSettings()` 之前就无条件调用 `workspaceKey(input.cwd)`，于是显式 Scope 下 `scope.mjs resolve` 不带 `--cwd`（或传相对路径）仍报 `workspace_required`，与"显式 Scope 解析不要求工作区键"的文档/正文表述冲突；测试夹具 `scope(action, scopeId, cwd = workspace)` 恒传 `--cwd`，故该分支天然无覆盖。审查同类 CLI 时的判据：**键计算发生的位置是否早于 Scope 模式判定**，以及夹具是否给所有调用都塞了默认路径参数。

关键词：`validated_at: 2026-10-18`、`validated_ref: f1908b8ea2897f91168a591b9a256200c8cfd646`（PR #2043 旧 Head）、`6a514384b02d1f78bd2a3679147b3ca739e9d25e`（PR #2043 新 Head，realpath 方案）、`toolchain: Node 22.22.2（Windows）`、`applies_to: master 上新增或修改 kind="workspace" 绑定的宿主插件`、`recheck_when: 任一宿主改为 realpath/canonical 方案、或 `resolve_binding` 的 allow_default 默认值变更、或新增 session 级绑定`。

<a id="r-pc20"></a>

## R-PC20. zcode 宿主插件的时序预算与「观察顺序」用例（已实证）

- 插件路径 `integrations/zcode/plugins/powercontext/`，**没有 `package.json`**（无 npm/pnpm 依赖，全部 `node:` 内置模块）⇒ 可直接 `node --test integrations/zcode/plugins/powercontext/tests/<file>.test.mjs`，无需安装（2026-10-19 实测 Node 22.22.2 / Windows）。
- **时序预算以代码为准**：`shared/transport.mjs` 的 `REQUEST_TIMEOUT_MS = 1000`（逐请求 `AbortSignal.timeout`）与 `HOOK_BUDGET_MS = 4000`（整条 hook）。`hooks/user_prompt_submit.mjs` 在 prepare 失败时只写 stage、**仍继续 capture** ⇒ "把 prepare 响应挂住"并不能阻止该 hook 抢到 `/v1/sources/content` 的 `position`。
- `tests/observations.test.mjs` 的 `latest-attempt order` 用例依赖的契约：先 spawn newer 的进程（stdin 先不给），再 spawn older 并等它的 prepare 到达（`slowReady`），随后才把 newer 的输入写入 stdin；older 的 prepare 响应由 newer 的 capture 释放（兜底 10s 定时器）。断言是「最新 attempt 的 `stages.capture.source_position == 1`」，因此这条断言直接等价于「谁先 POST `/v1/sources/content`」。
- 失败签名固定为 `2 !== 1`（older 抢先）。等量变慢已被事件同步化解；**非对称**停顿超过 1s 仍会复现，机制与判据见 `review-experience.md` 的「用事件同步替换定时等待」章节。
- **CI 归属不可混淆**：`zcode-acceptance.yml::controlled-cli` 跑在 **windows-latest**，命令 `node --test integrations/zcode/plugins/powercontext/tests/*.test.mjs`（含本用例）；`kimi-code-acceptance.yml::controlled-cli` 矩阵为 `[ubuntu-latest, windows-latest]`，跑 `plugin.test.mjs`，两者都不能代表对方的平台覆盖。
- 探针：`oceanbase-powercontext-pr-2051/probes/slow-hook-start.mjs`（两个 hook 进程等量延迟，用于复现 base 抖动）与 `probes/slow-newer-hook.mjs`（只延迟先启动者，用于暴露残留窗口）。

关键词：`validated_at: 2026-10-19`、`validated_ref: d8ec31490a39490880e372f8de178cccd9fcfb1d`（PR #2051 Head）、`f2808fb42db909e977dce96d0dd5c113736142c0`（base）、`toolchain: Node 22.22.2 / Windows`、`applies_to: integrations/zcode 插件的 hook 预算、observations 用例与 zcode-acceptance CI`、`recheck_when: transport.mjs 的超时/预算常量变更、observations.test.mjs 的顺序断言改写、或 zcode-acceptance.yml 的 runner 变更`。

<a id="r-pc21"></a>

## R-PC21. Desktop 的 qualification 记录必须与 bundled contract 对齐（文档引用同样受约束）

`desktop/src-tauri/src/connections/compatibility.json` 的记录靠 `contractSha256` 与构建内置契约绑定，只有匹配的记录才能让连接"可用"。

- **命中面**：`desktop/src-tauri/src/connections/compatibility.json`、`desktop/src-tauri/src/transport/operations.json`（生成物，含 `contractSha256`），以及 `desktop/README*.md` / `desktop/VALIDATION.md` / `docs/{en,zh}/development/desktop-delivery-plan.md` 中出现的任何 `sqlite-atomic-*` 记录 id（2026-10-19 追加：`docs/zh/development/desktop-delivery-plan.md` 第 159 行是第三个消费者，PR #2056 修 README/VALIDATION 时漏改，照做同样无法启用 Scope 选择）。
- **判据**：`connections/session.rs` 的 `compatible` 要求 `profile.compatibility` 对应记录的 `contract_sha256 == operations.json["contractSha256"]`，否则 `compatibility_verified=false`、`supported_operations` 为空，保存/搜索/选 Scope 全部不可用。所以文档给出的记录 id **不能取"最新那条"，必须取与 bundled contractSha256 相等的那条**。
- **2026-10-19 实例（PR #2056）**：bundled `contractSha256 = dae5feab…d14f`（Server `683e2db0`），而 `README.md` 与 `VALIDATION.md` 同时写着 `sqlite-atomic-caf2a35a-v1`（`e43c7034…7da7`），照做恒不可用；同一文件的另一段与新增用例 `bundled_qualification_allows_explicit_scope_browsing` 都指向 `sqlite-atomic-683e2db0-v1`，可反证文档笔误。
- **核对方式（无需构建）**：读两个 JSON 比对 `contractSha256` 与各记录 `contractSha256`，再 `grep -n "sqlite-atomic-" desktop/*.md` 逐条对齐；`cargo test` 的 `bundled_qualification_*` 用例只是同一事实的机器化版本。
- **边界**：历史记录的身份不可改写，新增记录不改变旧记录；"记录存在"不等于"对本构建可用"。

- **第四类消费者：`desktop/VALIDATION.md` 的验收叙述段落（2026-10-23 追加）**。`### macOS installed application workflow`
  这段以「在 normal release app 上 `explicitly selected <record-id>` 并完成保存/搜索/精确读取」的句式记录验收，
  记录 id 就是硬引用。PR #2056 head `17754f89` 的状态：同文件第 25 行已声明 current 记录是 `sqlite-atomic-d9a78567-v1`
  且 caf2a35a/683e2db0/cab054db 三条 `do not match this bundled contract`，而第 138 行的验收段落仍写
  `sqlite-atomic-caf2a35a-v1`。**判据不变：不匹配记录 ⇒ `compatible=false` ⇒ 该段描述的行为在当前 head 不可发生**；
  按 `compatibility.json` 与 `operations.json` 的 `contractSha256` 比对即可确认，无需构建。
  ⇒ 文档一致性检查应覆盖四类消费者：`README*`、`VALIDATION.md` 的 Compatibility scope、`docs/{en,zh}/development/desktop-delivery-plan.md`、
  **以及 VALIDATION.md 内的验收叙述**。后两类最易漏，因为它们不叫「选用指引」。

关键词：`validated_at: 2026-10-23`、`validated_ref: 17754f89771f9e1a6e90c7b50b7ff0f20e7f2f3e`（PR #2056 Head，bundled contract `a6758fd3…`）、`d46de401ce7812b364409b2ff07a6a6d5ebab65e`（2026-10-19 首次取证 Head）、`applies_to: master 上的 desktop qualification 与相关文档`、`recheck_when: operations.json 重新生成、compatibility.json 增删记录、或 desktop 文档改写选用指引`。

<a id="r-pc22"></a>

## R-PC22. `desktop/` 的文档中英必须同步（README 与 VALIDATION）

- **命中面**：`desktop/README.md`、`desktop/README.zh.md`、`desktop/VALIDATION.md`（无中文对照，但被 README 引用为唯一验证依据）。
- **判据**：`desktop/README.md` 用 `See [中文说明](README.zh.md)` 把中文版当作等价入口。新增平台、凭据后端、诊断命令或打包方式时，若只改英文版，中文读者会得到与本构建行为相反的说明（2026-10-19 PR #2056：英文首段已改为 Windows+macOS，中文仍是 Windows 专用，连卸载、构建前置、凭据存储、诊断 Job 描述都停留在 Windows）。
- **核对方式**：对英文版每个新增小节在中文版 grep 对应关键词（`macOS`、`Keychain`/`钥匙串`、`dmg`、`diagnostic-cli.json`）；命中 0 即为未同步。
- **定级**：用户可见文档缺平台支持说明按 P2，不因"代码没问题"降级。

关键词：`validated_at: 2026-10-19`、`validated_ref: d46de401ce7812b364409b2ff07a6a6d5ebab65e`（PR #2056 Head）、`applies_to: master 上 desktop/ 的 README 与 VALIDATION`、`recheck_when: 新增或移除 Desktop 支持平台、凭据后端或打包方式`。

<a id="r-pc26"></a>

## R-PC26. `code-seekdb` 的 bootstrap 步骤有 300 s 步预算，新增 e2e 不得多进程抢同一嵌入式引擎（已实证）

- **命中面**：`tests/e2e/test_database_bootstrap.py`（`-k seekdb`，由 `master.yml::code-seekdb (3.11, 3.14)` 的 step `Test database bootstrap with embedded seekdb without skips` 执行），以及任何在该 job 内新增/加重用例的 PR。
- **步骤预算**：该 step 的 `timeout-minutes` 是 5。超时后同 job 的 `Test unified migrations with embedded seekdb` 会变成 `skipped`，即该 head 上迁移验收**未执行**。
- **实测基线（2026-10-19）**：上一 head `2fef5fab` 的 3.14 同 step 41 s success；head `b0e379f6` 的 3.11 88 s success、3.14 312 s 超时 failure（job 118152425141）；master `e4efb39b` 同 job success。落在该 step 的 diff 只有新增的 `test_seekdb_legacy_migration_cli_preserves_json_with_sql_echo`。
- **判据（为什么归因这条用例）**：同一 head 另一版本绿 + 上一 head/base 同 step 绿 + 该 step 的 diff 面只有本用例，三条同时成立才可归因；只写「job 超时」没有证据价值。取 step 时间的方法见 `review-experience.md` 的「job 级 conclusion 会掩盖 step 级超时」。
- **机制**：本文件既有注释已写明并发覆盖只到 "one embedded owner process, not multiple engine-owner processes"。新增用例把同一 seekdb 目录交给 4 个独立子进程（每个 action 一次 `subprocess.run(..., timeout=45)`）再外加一次 `open_existing`，而 `asyncio.run(seed())` 与末尾 `verify_preserved()` 的 `SeekDBProfile.open_existing` **没有 timeout**：一旦子进程被 45 s 上限 kill 而引擎目录/锁未释放，这两个无界等待会吃掉整段预算。
- **审查要求**：新增 seekdb e2e 时，要求「跨进程开库次数」显式且最小（进程内复用同一 owner，仅保留一次跨进程以覆盖「CLI 是独立进程」这一事实），并给所有 `asyncio.run(<open>)` 加 `asyncio.timeout`。
- **2026-10-22 追加（同一 job，新失败形态：单用例自身预算）**：`code-seekdb (3.11)` 的 job `119624150671` 在
  `test_seekdb_legacy_choice_preserves_old_data_and_separates_new_database` 上跑满 `tests/fixtures/seekdb_legacy_choice.py`
  的 `asyncio.timeout(60)` 失败；同 head 的 3.14（job `119624150681`）该用例 **37.01 s** 通过。
  - **实测成本**：该夹具一个子进程内串行 7 次引擎 owner 打开（`SeekDBProfile.open` ×4 + 3 次 `app.router.lifespan_context`），
    每次 lifespan 都对同一嵌入式引擎重复整套 `CREATE TABLE IF NOT EXISTS`。同 step 其余用例 5–10 s，本用例独占 37–60 s；
    整段 bootstrap step 3.14 约 104 s / 300 s。
  - **判据**：失败阶段 `old data: reopening test` 的引擎快照里 `CREATE TABLE IF NOT EXISTS pc_agent_skill_targets (...)`
    已 `Time=22` 仍 `ACTIVE`，`__all_virtual_lock_wait_stat` 为空 ⇒ 重复建表的真实耗时，不是锁等待、不是死锁。
  - **预算层级**：`run_seekdb_scenario` 的 `subprocess.run(timeout=90)` > 夹具内 `asyncio.timeout(60)` ⇒ 父进程预算永不先到，
    失败信息只剩阶段名；CI 另外还加了 `-o faulthandler_timeout=60`，日志里会出现两个来源不同的 `Timeout (0:01:00)`。
  - **审查要求（补充）**：一个 seekdb 夹具只允许一次全量 schema 初始化；多次 `create_server_app(...).lifespan_context`
    必须复用同一 profile 或改用只读检查路径。三层预算（步骤 300 s > 父 `subprocess.run` > 子 `asyncio.timeout`）必须单调递减。

关键词：`validated_at: 2026-10-22`、`validated_ref: d8da2bcac2d15501105ae99c971fce23a604fde7`（PR #2031 Head，单用例 60 s 预算越界）、`b0e379f6aae5495220e7dba4206e24df03439cf5`（PR #2031 旧 Head，步骤 300 s 越界）、`2fef5fabe16961bbc1f76d10da6e13ca6242e9ad`、`toolchain: ubuntu CI（code-seekdb 3.11/3.14）`、`applies_to: master 上 code-seekdb job 与 tests/e2e/test_database_bootstrap.py`、`recheck_when: master.yml 的 code-seekdb step 拆分或 timeout 调整、或该 e2e 用例改为单一 owner 进程`。

<a id="r-pc28"></a>

## R-PC28. Desktop 的 OpenAPI→Rust 生成链：`generate:check` 通过 ≠ 生成物可编译

- 链路（PR #2113 起的布局）：`desktop/scripts/generate.mjs`（`--check` 即 `generate:check`）→ `pnpm exec openapi-generator-cli`（版本固定在 `desktop/openapitools.json`，模板 `desktop/scripts/openapi-generator/rust/model.mustache`）→ 生成 `desktop/src-tauri/src/transport/wire.rs` → `cargo run --example export_ipc` 产出 `desktop/ui/src/generated/ipc.ts`（`ipc:check` 校验）。
- **`generate:check` 只比对字节，不编译 TS**：`pnpm lint` 与 `pnpm build` 都会调用它，但 `tsc --noEmit` 只在 `typecheck` 与 `build` 步骤里跑。PR #2113 head `d46395e1` 的 `generate:check` 绿（日志 "Desktop contract matches OpenAPI."），`pnpm typecheck` 却报 13 条 `TS2304/TS2552`，且失败后其后的 `test`/`build`/`cargo fmt/clippy/test` 全部 skip ⇒ 该 head 的 Rust 侧没有 CI 证据。
- **两层"漏声明"判据**：① `wire.rs::declarations()` 由 `generate.mjs` 按**顶层 component schema 名**生成，`examples/export_ipc.rs` 直接 `.chain(wire::declarations(...))`；内联 enum 被生成器提升为独立 Rust 类型（`Type`/`Role`/`State`/`Stage`/`Effect`/`ShareUnit`/`MatchedBy`/`OutputKind`/`Reason`/`Configuration`/`BuiltinProfile`/`PromptCapabilityStatus`/`ExtractionObservationStatus`）后被字段按名引用，却不在该清单里 ⇒ `ipc.ts` 出现悬空类型名。② 模板对 `isMap`/`isNullable` 字段发 `#[ts(type = ...)]`，ts-rs 以该字面量替换真实类型，**可选性与 `| null` 一并丢失**：nullable `$ref` 会拼成空联合（`created_by?:  | null | undefined`，前导 `|` 合法所以 `tsc` 不报错），map 字段退化为必填 `Record<string, unknown>`。
- 核对方式（无需构建）：`grep -n "^export type \(Type\|Role\|State\)" desktop/ui/src/generated/ipc.ts` 命中 0 即悬空；`grep -n "?:  |" ipc.ts`；再用 `git show <base>:desktop/ui/src/generated/ipc.ts` 对照字段是否丢了 `?`/`| null`。CI 侧取 `desktop` 工作流 `windows` job 的 `pnpm typecheck` 段。
- 定级口径：生成物不可编译、job 红且后续验证被跳过 ⇒ P1；类型信息静默降级但当前无消费者 ⇒ P2。
- 附带：该链路新增 `@openapitools/openapi-generator-cli`（`desktop/pnpm-workspace.yaml::allowBuilds`），JAR 由 CLI 运行期下载，版本串固定但制品无哈希校验，离线环境无法复现生成。
- **2026-10-21 复审（head `08b78d48`）：两条均已修复**，且附带项升级为独立 Finding。
  `32ced081` 把 `declarations()` 改为从生成的 Rust 源码回扫 `pub (struct|enum)`，并在 `export_ipc.rs` 加
  `assert!(!output.contains("?:  |"))`；`model.mustache` 只在 `{{#isMap}}{{#isFreeFormObject}}` 发
  `#[ts(type = "Record<string, unknown>")]`，`{{^required}}` 走 `#[ts(optional)]`、`{{#isNullable}}` 单独发
  `#[ts(type = "... | null")]`。核验结果：`wire.rs` 声明 39→53、base 有而 head 缺失 0；`ipc.ts` 80 个
  `export type` 含全部 13 个此前悬空类型；CI `Desktop validation / windows`（job `118638863265`）的
  `pnpm typecheck`/`build`/`test`/`cargo clippy -D warnings`/`ipc:check` 全通过（此前失败后 skip 的步骤恢复执行）。
- **新增判据：用同契约的另一份生成物交叉验证 nullability，不能只读一份生成物就断言「nullable 丢失」。**
  `desktop/ui/src/generated/api.d.ts`（`openapi-typescript` 生成，本 PR 未修改）是独立消费者：对 26 个同名
  schema 逐字段比对 `optional`/`| null` 语义得 0 差异，据此否证了「head 系统性丢 `| null`」的初判 ——
  `ExtractionObservation.last_failure` 在 api.d.ts 中同样无 `| null`，base 的 `| null` 才是旧手写生成器的过度声明；
  `Capabilities.prompts` 在契约里无 `nullable`，同理。**反例方向**：只有两份生成物出现差异时才是生成链偏差。
- **残留覆盖边界（不是缺陷）**：`export_ipc.rs` 的断言只匹配 `"?:  |"`（optional+nullable），
  `required+nullable` 的失败形态是 `":  |"`，不含 `?`。当前契约与生成物无该形态。
- **新增 Finding 形态：`generate:check` 不是只读校验。** `generate.mjs` 顶层 `await generateRustModels()`
  无条件执行，`--check` 只在第 226 行之后比对字节 ⇒ `pnpm lint` 与 `pnpm build` 都因此依赖 PATH 上的
  `java`（JDK 11+，官方要求原文「You must have the `java` binary executable available on your `PATH`」）
  与首次访问 Maven Central 下载 JAR。CI 之所以绿是 `windows-2025` runner 预装 Temurin 17
  （PATH 含 `hostedtoolcache/windows/Java_Temurin-Hotspot_jdk/17.0.20-101/x64/bin`），
  而两份 README 的构建前置清单未列 Java ⇒ P2。核对方式：`grep -n "java|jdk" desktop/README*.md` 命中 0。
- **`installed-package` job 在 PR 上恒 SKIPPED**：`desktop.yml` 的条件是
  `github.event_name == 'workflow_dispatch' && inputs.installer_run != ''`，不是覆盖缺口，不要写成"验收未跑"的缺陷。
- **冲突与门禁**：`mergeable: CONFLICTING` / `mergeStateStatus: DIRTY` 时用 `git merge-tree --write-tree`
  定位冲突文件（本轮仅 `desktop/pnpm-lock.yaml`，源自 master `1d695664` 的 vite bump），
  属治理阻塞、不发代码评论；approval 需求按 R-PC02/R-PC12 另行计数。
- **2026-10-21 第三轮复审（head `e7ce9f38`，已 merge master `88899876`）：三条 Finding 全闭合。**
  `6f5d5074` 在 `desktop/README.md` 与 `README.zh.md` 第 20 行补 JDK 11+/`java` on `PATH` 并各加一段
  「`generate`/`generate:check` 走 Java Generator、首次可能从 Maven Central 下载 JAR、需网络」。
  「JDK 11」下限经上游 README 证实（`Java 11 runtime at a minimum`、安装前置 `* [Java 11]`），
  Generator 版本 `openapitools.json::version = 7.26.0` 未随合并漂移。`.mise.toml` 仍只 pin `node`/`pnpm`，
  不含 java（可选改进，非缺陷）。
- **判据修正：`wire.rs` 不变而 `ipc.ts` 变，未必是漂移。** `export_ipc.rs` 除 `wire::declarations()` 外还
  直接从业务模块导出类型（`diagnostics::{DiagnosticItem,DiagnosticKind,DiagnosticReport,HostDiagnostic}`、
  `connections::*`、`credentials::*`、`error::SafeError`、`ipc::FoundationInfo`）。本轮 master 把
  `HostDiagnostic.presence` 改名 `status`（`diagnostics.rs` blob `95740d75`→`2a998ec8`），PR 随之重新生成
  `ipc.ts`（blob `7bda98b3`→`7474c293`），而 `wire.rs` blob 不变（`73828fce`）——这是**正确**的，
  因为该结构体不来自 OpenAPI 契约。定位方法：先看 `ipc.ts` 里变动的类型名属于哪个 `use` 模块，
  再决定该查契约还是查业务结构体。
- **merge 上游后必须重跑生成链**：`generate:check`/`ipc:check` 能捕获上游字段重命名导致的生成物过期，
  但需要作者在 merge commit 里实际执行（本轮作者做了，CI 43 项全绿）。审查 merge commit 时优先核对
  「上游改了被导出类型 → 生成物是否同步」，而不是只看冲突是否解决。

- **复发形态（2026-10-23，PR #2056 新增 macOS 段落时重现）**：README 只在「Build on Windows」段补了 JDK 前置，
  新增的「Build on macOS」段（`desktop/README.md:126`、`README.zh.md:109`）只列 macOS 12 / Xcode CLI / Node / pnpm / Rust。
  判据不变：`package.json` 的 `lint` 与 `build` 都串 `generate:check`，而 `generate.mjs` 顶层无条件跑 Java Generator
  ⇒ **每个新增平台段落都必须重复 Java 前置**，不能只改已有平台段。CI 为绿不构成反证（`macos-15` 镜像预装 Temurin，
  与 `windows-2025` 同理）。`desktop/VALIDATION.md` 的「macOS native validation」命令清单同样漏该前置。

关键词：`validated_at: 2026-10-23`、`validated_ref: 17754f89771f9e1a6e90c7b50b7ff0f20e7f2f3e`（PR #2056 Head 的 macOS 段落复发形态）、`e7ce9f38ad7a77be40db3ab70d8b10320ea82b81`（PR #2113 Head，含 merge master `88899876`）、`08b78d48cbec96e75a13a3b960d5e7c46f0f1d0e`（上一 Head 修复态）、`d46395e132d476974813b020d6975053997bb67e`（旧 Head，两条 Finding 的来源）、`toolchain: CI windows job 118638863265 / 119188793670 + 提交树静态核对`、`applies_to: desktop/ 的 OpenAPI 生成链与 ipc.ts`、`recheck_when: generate.mjs 的模型清单或 declarations() 生成方式、模板 #[ts] 用法、export_ipc 的导出集合、api.d.ts 改由同一生成器产出、或 lint/build 不再串 generate:check`。

<a id="r-pc29"></a>

## R-PC29. `desktop/` 安装包验收按整句等待用户可见文案，改 `memory-messages.ts` 必须同扫三处 harness（已实证）

- **命中面**：`desktop/ui/src/app/memory-messages.ts`（`memoryMessages.zh` / `.en` 的全部用户可见文案），以及任何改动 `NoteForm` / `MemoryWorkspace` 成功态渲染分支的提交。
- **harness 契约**：`desktop/tests/installed_boundaries.py:50`、`desktop/tests/installed_lifecycle.py:44`、`desktop/tests/installed_workflow.py:198` 都是 `page.wait_text("保存成功。")`，判断的是 `document.body.innerText.includes("保存成功。")`——**整句子串**，不是前缀、不看 `role`。
- **失效机制**：PR #2135（head `66bf9b666a`）把有记录的成功文案从 `保存成功。` 改成 `保存成功，返回 N 条记录；每条都可以直接打开其精确版本。`，只有 `saved.length === 0` 的 `noEntry` 分支还以 `保存成功。` 开头。正常保存会返回 1 条记录 ⇒ 页面上不再出现该子串 ⇒ `wait_text` 抛 `HarnessFailure("installed_observation_timeout")`。
- **判据（CI 侧）**：`Desktop validation` 工作流 `windows` job 的 step 30 `Smoke test installed package`（`desktop/scripts/windows-smoke.ps1` → `desktop/tests/installed_ui.py`）；失败栈会指到具体 harness 行。归因三件套：同一 head 的两次运行签名相同（job 118998256779 / 118717975919，均为 `installed_boundaries.py:50`）、base 同 job success（`0da4436d` job 118648970585）、diff 面只有这几个文案与渲染分支。
- **提醒**：该 job 不是 ruleset 的 required check（R-PC02），但它是仓库唯一的安装包验收；不能因为"非 required"降级。英文侧 `Saved successfully.` 同样被改写，当前只是没有 harness 等待它。
- **处理**：文案改动与三处 harness 必须同一 PR 内对齐（或让成功文案保留以 `保存成功。` 开头的完整句）；审查者只提 Finding，不改文件。

关键词：`validated_at: 2026-10-21`、`validated_ref: 66bf9b666ade19ada146f83ab8cd5d98c18b436e`（PR #2135 Head，base `0da4436d`）、`toolchain: github-actions windows-latest（Desktop validation）`、`applies_to: desktop/ 的 UI 文案、NoteForm 成功态与安装包验收 harness`、`recheck_when: harness 改用 role/前缀断言、三处 wait_text 文案变更、或 memory-messages.ts 结构改写`。

<a id="r-pc33"></a>

## R-PC33. Server 托管文件日志：开关来源、单写者锁与「投递失败」计数语义（2026-10-22 实测）

审查 `server/logging.py` / 新增 `server/_log_transport.py` 或任何改动 Worker 日志通道的 PR 时，先固定下面五个事实，再判断"失败"是否真的失败。

- **开关不是只在配置里**：`ServerLoggingConfig.file` 默认 `false`（`settings.py`），但 `service/launcher.py::_service_logging()` 会在「stdout 被重定向」或 `sys.platform == "darwin"` 时把 `file` 设为 `True`（仅当用户没有显式设置该字段）。所以 Windows 服务是否写托管文件，取决于宿主是否重定向 stdout——读 `launcher.py` 的 `options.stdout` 判定，不要凭平台猜。
- **文件名由 role 决定**：`configure_server_logging(config, role=…)` 只接受 `{server, all, api, background, worker}`，文件名 `f"{role}.log"`；worker 角色在 `config.file` 为真且没有 channel 时**直接 ValueError**（`File logging workers require a Server-owned log receiver`），因此 Worker 必须由 `worker_logging(...)` 的 `prepare()` 提供 socketpair，不能只传 `WorkerLogging(config)`。
- **单写者锁**：`FileLock(str(filename) + ".lock", thread_local=False)` + `acquire(timeout=0)` ⇒ 同目录同 role 的第二个**进程**在启动阶段即抛 `filelock.Timeout`，且该异常不在 `launcher.main()` 的 `(ProtectedEnvironmentFileError, ServerConfigurationError)` 捕获范围内 ⇒ 服务以 traceback 退出。同进程内重复调用不受影响（filelock 按实例计数）。文档已声明"second Server with the same directory and role is rejected"，据此判"重复实例"而不是"日志丢失"。
- **失败计数只有一处出口**：`_FailureIsolatedHandler.handleError` → `_LOG_FAILURES += 1` 且首次写 `{"event":"observability.log_failed","outcome":"failure"}`；`log_record_failures()` 被 `server/operational_metrics.py` 投影成 `telemetry_log_records_dropped`。任何"正常路径也走 `_on_failure()`"的写法都会污染这个指标。
- **Windows 上对端关闭不是 EOF**：`LogReceiver._read` 里 `recv()` 在 Worker 被 `terminate()` 后抛 `ConnectionResetError [WinError 10054]`（Linux 返回 `b""`），落到 `except Exception` 就计一次投递失败。PR #2196 的 `tests/e2e/test_worker_logging.py::test_terminated_worker_does_not_interrupt_shared_log_output` 因此在 Windows 上失败（28 passed / 1 failed），而该文件只由 `master.yml::tests (x, e2e)`（ubuntu）执行、`windows-unit-portability` 不跑它 ⇒ CI 不会提示。判据与探针写法见 `review-experience.md` 的「对端进程被终止时 socket 读可能抛 ConnectionResetError」。

关键词：`validated_at: 2026-10-22`、`validated_ref: 717c8e5cfdab31c6b8b9efc81390f8aac421bd36`（PR #2196 Head）、`6934d30ce69089470543a9bb25d57f7400ca24e8`（PR #2197 Head，同批 `which()` 解析）、`toolchain: Windows / Python 3.14.3 / 工作区 .venv + ubuntu CI`、`applies_to: master 上 server/logging.py、server/_log_transport.py 与 service/launcher.py 的日志接线`、`recheck_when: ServerLoggingConfig 字段或默认值变更、_service_logging 的判定条件变更、日志改为多进程独立写同一文件、或 e2e 日志用例进入 Windows job`。

<a id="r-pc38"></a>

## R-PC38. `GenerationCache` 的 `PUBLICATION_WINDOW` 裁剪必须带 retained 差集（已实证）

`src/powercontext/builtin/code/cache.py` 的发布记录剪枝有两个独立缺口，`recover()` 的 abandoned 通路过测、窗口通路不过测。

- **缺口一：`recover()` 把刚算好的守卫丢掉。** `recover(deadline)` 先算 `retained = self._retained_identifiers()` 用于 abandoned 过滤（`:241-246`），
  随后因 `len(records) > PUBLICATION_WINDOW` 调用 `self._write_publications(records, deadline)`（`:250-251`），**该调用不接收 retained**，
  于是「目录已不存在、但 `current.json` 可达的 generation 仍拥有该标识」的记录在窗口里被回收 —— 正是它新 docstring 说要保住的状态。
- **缺口二：`publish()` 先写记录再 rename，新记录就是首个牺牲品。** `:346-352` 在 `os.replace()`（`:353`）之前写入
  `{"directory": directory.name, "state": "published"}`，此刻该目录必然不存在；`_write_publications` 的 stale 判据只有「记录的目录不存在」（`:294-302`）
  ⇒ `excess = len(records) - PUBLICATION_WINDOW` 全由这条新记录承担（旧的记录都还持有目录时），`remove_generation(attempt)` 在 rename 之前执行。
- **影响面按后端算**：SQLite 的 `remove_generation` 是空操作（行随目录），seekDB 是 `DELETE FROM pc_code_nodes/edges WHERE generation_id=%s`
  ⇒ `CodeService` 在 `begin_publication()` 与 `publish()` 之间写入的行被删，而 `manifest` 仍声明这些节点，读取成功但结果为空。
- **探针（Windows 不可跑，`cache.file_lock` 需 fcntl）**：WSL 下用 `importlib` 逐个装载 head 的
  `builtin/code/{errors,languages,models,capture,telemetry,graph,store,cache}.py`，只桩跨包依赖
  （`powercontext.errors.PowerContextError`、`powercontext._logging.{error_category,log_safely}`、`powercontext._code_validation.*`）
  与 `store.remove_generation`/`store.size`；实例 `oceanbase-powercontext-pr-2096/probes/r27/probe_cache_window.py`。
  保持「被 reader 钉住」的目录必须用**真实 flock**：同进程不同 fd 的 `LOCK_EX` 与 `LOCK_SH` 会冲突，`collect()` 才会拿到 `code_cache_busy` 而不删目录；
  换成 no-op 锁会让场景退化成「目录全被清掉」，缺口二不再复现。
- **实测（head `b5027a03`）**：`recover()` journal 63 条 → 不回收；71 条 → 回收 `1111…`（可达 generation 拥有的标识）；
  `publish()` journal 63 条 → 不调用 `remove_generation`；70 条 → 对**即将发布的那次 attempt** 调用。
- **修复方向与覆盖要求**：给 `_write_publications()` 传 `retained | {attempt}` 并据此过滤 `stale`；补两条用例 —— 钉住 N 个 generation 时
  `publish(attempt=…)` 不动该 attempt 的行，以及 journal 超窗 + 一个「目录被移走但标识可达」的记录仍被保留。
- **只按窗口断言会漏**：`test_the_record_window_never_drops_a_generation_that_still_exists` 走的是 `begin_publication()`（记录指向**现存**的 staging 目录），
  所以它既覆盖不到缺口一，也覆盖不到缺口二。

关键词：`validated_at: 2026-10-23`、`validated_ref: b5027a03ed1990c91221ac7d9ba6b7d90e9be69a`（PR #2096 Head，merge upstream 后）、
`1072176e99b52901e5561875fe3ef7d0e15360e0`（同一缺口的上一个 Head，`cache.py` blob `6b3da96b` 未变）、
`toolchain: WSL Ubuntu / Python 3.13.11（仅缓存模块）`、`applies_to: builtin/code/cache.py 的发布记录窗口、`recover()` 与 `publish(attempt=…)``、
`recheck_when: `_write_publications()` 改为接收 retained、`publish()` 改回 rename 后写记录、或 `PUBLICATION_WINDOW` 语义改变`。

<a id="r-pc39"></a>

## R-PC39. MiniMax 宿主适配：数据目录四级回落、`enabled` 在读侧与写侧语义不同、安装记录键 = `sha256(data_dir)`（2026-10-23 实测）

`src/powercontext/cli/minimax.py` 一个文件同时做三件事：定位 MiniMax 数据目录、判定该目录里 `mcp.json` 的 `powercontext` 条目是否生效、把它改写成当前 Server 端点。三者对同一份 `mcpServers.powercontext` 的读法不一致时，`setup` 与 `doctor` 会给出互相矛盾的结论。

- **数据目录优先级（`_data_dir()`，`:94-112`）**：`--minimax-data-dir` > `MINIMAX_DATA_DIR` > `MAVIS_DATA_DIR` > client settings 的 `minimax_data_dir`（`:100`）> `mcode marketplace list` 中唯一 `local` 项的 `path` 之父目录（`:102-109`）> `Path.home()/".minimax"`（`:112`）。`__init__`（`:232-245`）把前两级**重算一遍**喂给 `_command()` 与 `_data_dir()`；改一处忘另一处就会出现「命令取自 A 安装、插件写进 B 目录」。审查数据目录/命令解析改动时，这两个解析点必须并列读。
- **`enabled` 的两种语义**：`native_entry()`（`:250-255`）只在 `entry.get("enabled", True)` 为真时采用用户覆盖 `data_dir/mcp.json`，否则回落到打包插件的 `plugin/mcp.json`；`configure()`（`:307-338`）却用 `_mcp_entry(config)` 取 `existing`，而 `_mcp_entry()`（`:163-187`）只校验 `enabled` 是 bool、**不看其值**。同一个 `enabled: false` 条目：读侧当它不存在，写侧拿它当凭据载体与端点基线。
- **两个可复现后果（head `e089c858`，探针 `probes/r28/probe_disabled_entry.py`、`probe_disabled_auth.py`）**：
  1. 禁用条目带 `Authorization` 且原端点 ≠ 当前 `connection.server_url` ⇒ `:322-325` 抛 `MiniMax endpoint changed; provide a new authorization explicitly before moving credentials`。用户已显式禁用该条目，却被它的旧端点拦住，`setup` 无法重跑。
  2. 禁用条目无凭据 ⇒ `:326` 的 `entry.update(type=…, url=endpoint)` 无条件执行（`entry = dict(existing)` 保留 `enabled: false`），把用户手工配置的私有端点 `https://memory.example/mcp` 静默改成 `http://127.0.0.1:8000/mcp`；改写后 `native_entry()` 仍跳过它去看打包条目，`doctor` 与 `mcp.json` 指向不同端点。
- **判据（静态即可定案）**：`existing` 是否经过 `enabled` 过滤；`entry.update(url=…)` 在 `enabled` 为假时是否短路。修复方向：`configure()` 复用 `native_entry()` 的「生效条目」判定，或对 `enabled: false` 直接跳过改写；补「禁用 + `Authorization` + 端点不同」与「禁用 + 无凭据」两条用例。
- **安装记录键身份（`:247-248`）**：记录路径为 `powercontext_data_dir()/installations/minimax/<sha256(str(self.data_dir))>.json`，`install()`（`:268-269`）再用 `previous.get("data_dir") != str(self.data_dir)` 复验。数据目录换个写法（大小写、尾斜杠、symlink 解析结果）就是另一份记录 ⇒ 涉及「迁移/复用已有安装」的改动，必须确认这两处字符串化同源。

关键词：`validated_at: 2026-10-23`、`validated_ref: e089c8584cb8f2423973cc144800c8517561138e`（PR #2205 Head）、
`toolchain: Python 3.14.3 工作区 .venv / Windows`、`applies_to: src/powercontext/cli/minimax.py 与 tests/test_cli_minimax.py`、
`recheck_when: `native_entry()` 与 `configure()` 的条目判定合并、`enabled` 语义下沉到 `_mcp_entry()`、或数据目录解析引入新来源`。

<a id="r-pc40"></a>

## R-PC40. `desktop/` 验收 harness 走显式文件枚举，安装包验收步骤的结论可以直接引用（2026-10-23 实测）

- **静态检查清单是手写枚举**：`.github/workflows/desktop.yml` 的 `Check installed UI acceptance harness` step 里，ruff check / ruff format / ty check / ty check --python-platform linux 四条命令各自重复列出同样的 5 个文件（`installed_ui.py`、`installed_fixture.py`、`installed_workflow.py`、`installed_lifecycle.py`、`fixture_qualification.py`）。
- **判据**：`ls desktop/tests/*.py`（当前 8 个）与四条命令的文件集合求差。`real_cli.py` / `real_server.py` 由同文件第 113/116 行作为脚本执行；`installed_boundaries.py` 被 `installed_workflow.py:25` 导入、经 `installed_ui.py` 的 `exercise_memory` 在安装包验收里真实执行，却从未进入该清单 ⇒ 差集非空即为可评论的 P2（只影响静态检查覆盖，不影响产品行为）。PR 若在改这个清单时只补自己动过的文件，剩下的缺口仍成立。
- **安装包验收的覆盖面（可直接引用为证据）**：`Desktop validation / windows` job 的 step `Smoke test installed package`（`desktop/scripts/windows-smoke.ps1` → `desktop/tests/installed_ui.py`）。`installed_ui.py` 在 `report["stage"]` 序列里**无条件**执行 `exercise_single_instance` → `exercise_memory` → `exercise_forced_exit`，并以 `report["result"] = "passed"` 收尾 ⇒ 该 step success 即代表这些 harness 路径在真实安装包 + WebView2 上跑过，不要把「UI 改动只有 mock/合成 IPC 证据」写进结论。
- **应用内对话框取代 `window.confirm` 后，harness 改用 WebDriver 点按钮**：`installed_workflow.py::confirm(message, accept=)` 先 `element()`（20 s 轮询，等到出现且 enabled）取 `//div[@role='alertdialog' and @aria-modal='true']`，再用 `aria-describedby` 元素 `textContent` 与期望文案**精确比对**，不匹配即 `HarnessFailure`，然后点 `确认`/`取消`，最后等该提示消失。因此文案（`connectionMessages.zh.discard` / `.removeConfirm` / `memoryMessages.zh.retry`）与 harness 常量是硬契约，改文案必须同批改 harness。
- **Rust 导航白名单的结构**：`desktop/src-tauri/src/ipc.rs::allowed_navigation` 把 scheme/host 判定放在 `if cfg!(any(windows, android))` 分支内，`url.port().is_none()` 写在 if-else 之后。`if c {a} else {b} && x` 的 `&&` 作用于整个 if-else（见 `review-experience.md` 的同日条目）⇒ 行为等价于「分支命中且无端口」，**不是**功能回归；但负向对照组只写了 `tauri://localhost:8000`，Windows/Android 上真正依赖端口检查的 `http://tauri.localhost:8000` 没有断言。

关键词：`validated_at: 2026-10-23`、`validated_ref: b5a90f89bf5d27a083e70b381d3e9f7d36d32074`（PR #2188 Head，job 119733944707）、
`toolchain: Desktop validation windows-2025 / Node（CI 用 mise 22.19.0）/ pnpm 11.13.1 / rustc 1.96.0`、
`applies_to: desktop/tests 的验收 harness、.github/workflows/desktop.yml 的 harness 静态检查 step、desktop/src-tauri/src/ipc.rs 的导航白名单`、
`recheck_when: desktop.yml 的 harness 文件清单改为通配、installed_ui.py 的 stage 序列变更、或 allowed_navigation 改写为 origin 白名单`。

<a id="r-pc58"></a>

## R-PC58. 收紧 seekdb 的「只读不建库」必须按消费者扫 `runner.plan()` 的可写性，不能只补 Server 启动一处（2026-10-30 实测）

`MySQLMigrationRunner.plan()`（`migrations/mysql.py`）调 `self.connections.run(...)` 时**不传** `writable=True`，
只有 `apply()` 传。因此把 `MaintenanceConnections._seekdb` 的「数据库缺失」从「跳过、返回未初始化」改成
`raise MigrationError("database_missing")` 后，**所有「先 plan 再 apply」的可写工作流都在第一步失败**，
永远到不了带 `_provision_database` 的 `apply()`。

实测 #2031 head `6744505` 的 4 个 job 同签名红（父 head `cfec3159` 与 master `bf2ac1fc` 全绿）：

| job | 用例 | `writable` |
|---|---|---|
| `SeekDB managed startup regression (priority)` | `test_managed_startup_read_consistency.py::... [seekdb-server-False]` | False |
| `code-seekdb (3.11)` / `(3.14)` | `test_mysql_migration_schema.py::test_registered_next_revision_executes_directly_and_sequentially_on_real_seekdb` | False |
| `Atomic Memory clean migration (SeekDB)` | `test_atomic_memory_grant_migration.py::...[seekdb-False]` | False |

- **消费者清单**（收紧时逐项判定可写性）：`server/database_migration.py` 的 `plan()`/`apply()` CLI、
  `tests/e2e/server_storage.py::prepare_server_database`、`migrations/server_readiness.py::prepare_server_storage`、
  `migrations/mysql.py::verify()` 与 `status`。
- **判据顺序**：① `gh api .../commits/<head>/check-runs` 找同签名失败 job，再取 `actions/jobs/<id>/logs` 读 traceback 的
  `writable` 实参；② `git show <head>:src/powercontext/builtin/persistence/migrations/mysql.py` 确认 `plan()` 是否传
  `writable`；③ 对比父 head 与 master 的同名 job，排除基线滞后。
- 只补 `prepare_server_storage` 的 try/except（可在 `database.kind=="seekdb"` 时先 `run(..., writable=True)` 再重试 plan）
  属于"一个调用点兜底"，不等于修好：`migrate apply` 与 e2e 的 `prepare_server_database` 仍不可用。
- 若预期语义是"`migrate apply` 不再负责建库"，必须同时改 `docs/{en,zh}/docs/operate/database-migrations.md` 与
  `release/upgrade-support.json` 的 `schema_review.rationale`；当前 rationale 只写了 Server 启动会引导建库。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2031 head 6744505、父 head cfec3159、master bf2ac1fc`、
`toolchain: 引用 exact head CI（job 123582728692 / 123590672615 / 123590672780 / 123590674109）`、
`applies_to: `builtin/persistence` 的 seekdb/MySQL 只读收紧与迁移计划`、
`recheck_when: `plan()` 传入 `writable=True`、`require_existing_database` 的调用面变化，或 e2e 引导路径改为走 Server 启动`。

<a id="r-pc59"></a>

## R-PC59. 新增 OpenAPI operation 后，宿主生成物完备性必须按 **merge 结果** 判定（2026-10-30 实测）

PR 分支树里可能**根本没有**某个宿主目录：该宿主是 base 之后才合入 master 的。此时按分支树检查
`integrations/*/…generated*` 会得到"全部已同步"的错误结论，`pull_request` 触发的 check 却跑在 merge commit 上，
照旧红。

- 实例：#2192（base `1f0afd6b`，head `27d499e0`）新增 `POST /v1/recall/manifest`，同步了
  `integrations/{dsh,opencode,pi}` 的 `operations.generated.ts`、`integrations/dify/…/contract.json`、`desktop/ui/src/generated/*`，
  但 `integrations/cindy` 由 master `bf2ac1fc`（#1564，`feat(cindy): add scoped recall and automatic memory hooks`，
  2026-10-29 15:34）引入，晚于该 PR 的 base。`git ls-tree 27d499e0 integrations/` 无 `cindy`，
  `git grep get_recall_manifest 27d499e0 -- integrations/cindy` = 0；head 上的 `cindy-package` 确定性失败
  （run 40851969173 / job 123392312626，`make cindy-test` → `Makefile:188 Error 1`），日志里重新生成后多出
  `get_recall_manifest` 整段。
- **判据顺序**：① `git ls-tree <head> integrations/` 与 `git ls-tree refs/heads/master integrations/` 比目录集，
  找出 base 之后新增的宿主；② 对新宿主在 **merge 结果**（`git merge-tree --write-tree <head> master` 的树，或该 PR 的
  merge commit）上跑一次 `make <host>-test`，看生成物 diff 是否只多出新 operation；③ 只有在目录集一致时，
  才可以"其他宿主已同步"作为该宿主已同步的旁证。
- 修法：作者 merge 一次 master 后重跑生成命令提交；不是"补一个手写 operation"。
- 该红与 `required_status_checks` 无关（ruleset 9930477 没有该项），但 `make cindy-test` 属仓库门禁 ⇒ 按 §4 可定 P1。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2192 head 27d499e0 / base 1f0afd6b、master bf2ac1fc（#1564）`、
`toolchain: 引用 exact head CI（job 123392312626）`、`applies_to: `integrations/` 各宿主的 `*generated*` 契约文件与 `openapi/powercontext.yaml` 变更`、
`recheck_when: 仓库改为在 PR 分支上直接跑宿主包测试而非 merge commit、或新增宿主不再使用生成物`。

<a id="r-pc61"></a>

## R-PC61. 改了 `openapi/powercontext.yaml` 后，Desktop 产物要按**生成器**判，不是按 `contractSha256`（2026-10-30 实测）

`desktop/scripts/generate.mjs` 的 `outputs` 有四个产物，`--check` 对每个产物做**文本全等**比较：

| 产物 | 生成方式 |
|---|---|
| `src-tauri/src/transport/wire.rs` | openapi-generator（rust）→ 去 import → `rustfmt` |
| `ui/src/generated/api.d.ts` | `header + astToString(await openapiTS(contract))`（**全量 contract**） |
| `ui/src/generated/operations.ts` | `header + contractSha256 + operations`（reviewed 子集） |
| `src-tauri/src/transport/operations.json` | `{contractSha256, operations, discovery}`（reviewed 子集） |

而 `tests/test_desktop_contract.py` 只做两件事：读 `operations.ts`/`operations.json` 的 `contractSha256` 常量，与
`sha256(openapi/powercontext.yaml)` 比对。**手工改摘要能让 Python 门禁通过，但 `api.d.ts` 仍漂移。**

- 实测 #2270 head `11f4319c`：openapi 新增 `/v1/scopes/{scope_id}/operations`、`.../{operation_id}`、`.../cancel`、
  `.../retry`（+282 行），PR 只改了两个产物的 `contractSha256`（`c12901b8…`→`c7f00e81…`），`api.d.ts` 完全未改。
  `linux`/`windows`/`macos (macos-15)`/`macos (macos-15-intel)` 四个 job 同签名
  `Error: Contract drift: ui/src/generated/api.d.ts. Run 'pnpm --dir desktop generate'.`（run 40995611177）。
  父提交 `feb9e7f2`、`dd80249b` 这四个 job 全 success；同期 #2192（同样加 OpenAPI operation，head `4028045f`）的
  `linux`/`windows` 是 success ⇒ 归因本 PR。
- 反向确认（本例 `tests/test_desktop_contract.py` 在 exact head 副本 `2 passed`）：**不要**用 `make contract-test` 的绿
  去否定 desktop job 的红，两者覆盖面不同。
- 判据顺序：① `git show <head>:desktop/scripts/generate.mjs | sed -n '/const outputs/,/^}/p'` 取产物表；
  ② 对每个产物确认它的输入（全量 contract 还是 reviewed 子集）；③ 看 PR 是否改了全部产物；
  ④ 用父提交与同期改契约的 PR 的同名 job 排除基线。
- `operations.json` 的 reviewed 目录条数（本例前后都是 11）不变是正常的：新 operation 可以不进 reviewed 集合，
  但 `api.d.ts` 按全量 contract 生成，无法只排除某个 path。
- 修法：`pnpm --dir desktop generate` 后提交 `api.d.ts`（及可能变化的 `wire.rs`），不要手改摘要。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2270 head 11f4319c、父 feb9e7f2/dd80249b、#2192 head 4028045f`、
`toolchain: 引用 exact head CI（run 40995611177，job 123868189387/123868189660/123868189664/123868189587）+ 本机 exact 副本 pytest`、
`applies_to: 修改 openapi/powercontext.yaml 或 desktop/ 生成物的 PR`、
`recheck_when: generate.mjs 的 outputs 表或 --check 比较方式变化、test_desktop_contract.py 扩大覆盖面、desktop workflow 改名`。

<a id="r-pc67"></a>

## R-PC67. Desktop 的 Unix 诊断链路是「一份共享实现 + 两条平台 job + 一个共用探针」

`desktop/src-tauri/src/diagnostic_process_macos.rs` 由 `lib.rs` 以 `#[cfg(any(target_os = "macos", target_os = "linux"))]`
挂成 `diagnostic_process`，`tests/macos_diagnostics.rs` 与 `examples/diagnostic_cli_probe.rs` 也同时被两个平台编译。
开一个平台的 `cfg` 等于同时改变**另一个平台的验收面**，审查时要分三处看：

1. **共享实现**：`Group::drop` 用 `kill(-pid)` 杀进程组、`has_exited` 用 `waitid(P_PID, …, WEXITED|WNOHANG|WNOWAIT)`
   保留 pid 身份到清理之后。Linux 侧 `siginfo_t` 必须走 `si_pid()`（`unsafe` fn），macOS 是字段，否则编不过。
2. **平台 job**：`desktop-validation / linux` 会跑 `cargo test --manifest-path src-tauri/Cargo.toml`（含
   `tests/macos_diagnostics.rs`）。新增 `target_os = "linux"` 后必须先在 Linux 上跑过这组 integration test，
   不能只看 macOS 绿；`tests/ipc.rs`、`tests/macos_diagnostics.rs` 的 cfg 变化都要按此处理。
3. **共用探针**：`examples/diagnostic_cli_probe.rs` 同时被 windows job（`Check fixture qualification regressions`
   + `Test native diagnostics with isolated real CLI`）和新增的 linux 步骤执行。为让一侧通过而放宽断言
   （如把 `registration == "not_installed"`、`hosts.len() == 10` 放宽成"字段存在 / 非空"）会同时削弱另一侧，
   按 `R06A` 的"不得降低校验强度"处理，正确做法是按平台给期望值。

诊断的真实入口固定为 `service status --json` 与 `doctor <10 个宿主> --json`（`DiagnosticKind::arguments`），
宿主的注册文件是 `app_data_dir()/diagnostic-cli.json`，要求 `source: explicit_local_installation`、绝对路径、
文件名为 `powercontext`（Windows `powercontext.exe`）、sha256 64 位、大小 ≤ 64 MiB；POSIX 侧执行的是
`tempfile::tempdir()` 里 `0o500` 的**校验后副本**，因此 `TMPDIR` 必须可执行（`noexec` 挂载会让诊断恒失败）。

关键词：`validated_at: 2026-10-31`、`validated_ref: #2343 head 588174e7（job 124541552585）`、`applies_to: master`、
`toolchain: Rust 1.95.0 / cargo test --locked`、
`recheck_when: `desktop/src-tauri/src/diagnostics.rs` 的 `DiagnosticKind` 参数、`diagnostic_cli_probe.rs` 断言、
或 `desktop.yml` 的 linux/windows job 步骤变化`。

<a id="r-pc68"></a>

## R-PC68. 新增一个公开 OpenAPI 操作要同步 **五类** 消费方，其中两类不失败在 Python 侧

`openapi/powercontext.yaml` 加一个 operation 后，除生成物外还有两处「非代码清单」会红，且都不在 `tests/` 下：

1. **提交进仓库的插件 bundle**（R-PC66 的实例）：`integrations/dsh/plugins/powercontext/lib/index.js`、
   `integrations/cindy/plugins/powercontext-hooks/node/worker.cjs`。`make js-test` / `make cindy-test` 会在
   重建后对产物做 diff，缺行即 `Error 1`。**这些目录本 PR 可能一行都没改**（cindy 就是如此），所以判据不是
   "diff 里出现了哪些集成"，而是"仓库里还提交了哪些 bundle"：`git ls-files 'integrations/**/lib/*.js' 'integrations/**/node/*.cjs'`。
2. **`e2e/bub` 的访问审计分类集**：`e2e/bub/tests/test_access_audit.py` 的
   `test_every_server_wide_operation_is_classified_by_whether_it_returns_scope_content` 要求 OpenAPI 里
   所有 `x-powercontext-access.action == access.self` 的 operationId 集合**精确等于** `e2e/bub/src/powercontext_e2e/access_audit.py`
   的 `ACCESS_OPERATIONS`（`server` 资源走 `SERVER_WIDE_CONTENT_OPERATIONS | _SERVER_WIDE_WITHOUT_CONTENT`）。
   门槛在 `make harness-check`（`harness-validation / validate` job），报错形态是
   `Extra items in the left set: '<new_operation>'`。
3. 三宿主 `src/operations.generated.ts`（pi/opencode/dsh）；4. Python `http/_generated/`；5. `desktop/` 的
   `transport/operations.json` 与 `connections/compatibility.json`（新契约摘要必须有一条资格记录，见 R-PC61/R-PC62）。

复现命令（不 checkout 也能判）：`git ls-tree -r <head> --name-only | grep -E 'operations.generated.ts|lib/index.js|node/worker.cjs'`，
再对 bundle 反查该 operationId 是否出现。

关键词：`validated_at: 2026-11-01`、`validated_ref: #2361 head 18d8dd86（run 41312505106 / job 124871192360、124871192469、124871193100）`、
`applies_to: master 上任何新增/删除 OpenAPI 操作的 PR`、
`recheck_when: `Makefile` 的 `js-test`/`cindy-test`/`harness-check` 目标调整、`scripts/generate_js_operations.py` 改产物集合、
或 `e2e/bub` 的分类集改由 OpenAPI 自动生成`。

<a id="r-pc71"></a>

## R-PC71. JS 宿主 bundle 的「重建比对」可在 exact head 本地复现；判等必须做 LF 归一化（2026-11-03 实测）

`make js-test` / `make cindy-test` 的核心不是跑测试，而是 `git diff --exit-code` 对提交进仓库的 bundle 做逐字节
比对（`Makefile` 的 `js-test` 比 `src/operations.generated.ts` + `lib`，`cindy-test` 比
`integrations/cindy/plugins/powercontext-hooks/node/worker.cjs`）。本机没有 `pnpm`（也未全局安装）时仍可复现：

```bash
npm install --prefix <隔离目录> pnpm@10.18.3        # 不进全局 prefix，符合 R04
cd <head>/integrations/dsh/plugins/powercontext
<隔离>/node_modules/.bin/pnpm install --frozen-lockfile --config.auto-install-peers=false --store-dir <隔离 store>
<隔离>/node_modules/.bin/pnpm exec tsdown --config ../../../cindy/tsdown.config.ts   # 重建 cindy worker
<隔离>/node_modules/.bin/pnpm run build                                            # 重建 dsh lib
```

Windows 上两个产物的行尾行为不同：**dsh `lib/index.js` 与提交值字节相等**（无需归一化），
**cindy `worker.cjs` 只有头部那一段（许可注释，14 行）被写成 CRLF**，其余行 LF。因此 cindy 的判等一定要按
`replace(b"\r\n", b"\n")` 归一化后再比 sha256，否则会误判为「未重建」；Linux runner 上没有这个差异，
`git diff --exit-code` 干净即等价于归一化后相等。

另一个易误判点：`integrations/opencode/plugins/powercontext` 的 `lib/index.js` 操作键数在 **master 上就**少于
`src/operations.generated.ts`（2026-11-03 实测 master 149 vs 128、#2270 head 152 vs 126），`opencode-test`
也没有重建比对门禁 ⇒ 不能用「lib 里少了某 operation」直接判本 PR 漂移，必须先在同一 base 上取 src/lib 计数做对照。

关键词：`validated_at: 2026-11-03`、`validated_ref: #2361 head 17145bb1、#2270 head 5fa749d8`、
`applies_to: 改 openapi/powercontext.yaml 或宿主 plugin 生成物的 PR`、
`recheck_when: `integrations/*` 的构建脚本或 `pnpm` 版本管理策略改变、`opencode-test` 增加重建比对`。

<a id="r-pc74"></a>

## R-PC74. `code-seekdb` 分片 0 的 30 分钟取消是基线现象，归因前先查 base 提交的同名 job（2026-11-03 实测）

`code-seekdb (3.1x, 0)` 会在步骤 `Test unified migrations with embedded seekdb` 上跑满 30 分钟被取消
（`conclusion=cancelled`，job `started_at` 与 `completed_at` 正好差 30 分钟），聚合 job 随即报
`CI checks did not succeed: {'code-seekdb': 'cancelled'}`，`mergeable_state=unstable`。它是 **job 时长预算**，
不是该 PR 的缺陷：2026-11-03 实测 base `9c8f061c` 自身的 run 里 `code-seekdb (3.11, 0)`、`(3.14, 0)` 同样在 30 分钟
被取消，而 `(3.11, 1)`、`(3.14, 0)` 的后续 run 分别用 18–28 分钟通过；同一 head 上 #2425（未触及迁移）
与 #2304 都命中同一签名。

判据顺序：①取 `commits/{head}/check-runs` 找 `cancelled`；②读该 job 的 steps，确认 `cancelled` 落在
`Test unified migrations with embedded seekdb` 且时长≈30 分钟；③对 base 提交取同样的 check-runs，若同名分片
也有 30 分钟取消 ⇒ 判基线，不写 Finding，只在报告里记「需重跑该分片」。分片 0 比 1 更慢，别用"另一分片绿"否定。

关键词：`validated_at: 2026-11-03`、`validated_ref: base 9c8f061c（#2425 head 2d324ac4、#2304 head 8544da90）`、
`applies_to: 判 PR 的红色 check 归属时`、`recheck_when: 拆分 code-seekdb 分片、提高 job timeout-minutes 或迁移 bootstrap 预算变化`。

<a id="r-pc75"></a>

## R-PC75. Desktop 资格记录要按 `serverCommit` 的 openapi 摘要反查，而不是只看摘要字符串出现（2026-11-03 实测）

`compatibility.json` 的记录形如 `{id, serverCommit, contractSha256, artifactSha256, operations, evidence}`。
判「补了资格记录」的完整链条：①`sha256(LF(openapi/powercontext.yaml@head))` 等于 `operations.json:contractSha256`；
②存在某条记录其 `contractSha256` 与之相等；③该记录 `serverCommit` 是 head 的祖先，且
`sha256(LF(openapi@serverCommit))` 等于同一值；④`evidence` 指向的 `desktop/VALIDATION.md` 小节存在，
其中 wheel SHA-256 等于记录的 `artifactSha256`。只做②会漏掉"记录是照抄旧提交"的情形。

反证手法（`probes/` 副本，R04）：移除该记录后 `pytest tests/test_desktop_contract.py -q` 必须失败，
2026-11-03 实测失败文本为 `The bundled Desktop contract has no qualified profile for save, search and exact reads.`；
未移除时 3 passed。wheel 本身在无 GTK/WebKit 的机器上无法重建，`artifactSha256` 只能依赖记录与 CI，属可记录缺口。

关键词：`validated_at: 2026-11-03`、`validated_ref: #2304 head 8544da90 / 记录 sqlite-atomic-3cefa45a-v1`、
`applies_to: 改 openapi 后移动 Desktop 契约摘要的 PR`、`recheck_when: compatibility.json 结构或 test_desktop_contract.py 断言变化`。

<a id="r-pc76"></a>

## R-PC76. Codex 与 Claude Code 的 hook 实现是逐行同源的，改一处文档必须扫另一处（2026-11-03 实测）

`integrations/codex/plugins/powercontext/hooks/` 与 `integrations/claude-code/plugins/powercontext/hooks/` 里的
`prompt_privacy.py`、`prepared_context.py`、`recall.py` / `user_prompt_submit.py` 是同一套逻辑：两处都是
`safe_prompt = scrub_secrets(prompt, authorization)` → `_bounded_recall_query(safe_prompt)`，并按
`safe_prompt != prompt` 跳过整次 capture。因此「某宿主文档写错同一行为」几乎必然在两处同时成立。

#2446 把 `docs/en|zh/docs/integrations/codex.md` 的召回描述改成「先脱敏、去空白，再定界」，但
`docs/{en,zh}/docs/integrations/claude-code.md` 仍写「原样发送 / sent as submitted」。判据：改宿主文档前先用
`grep -rn "sent as submitted\|原样发送" docs/` 与插件目录 diff 找同源页；anchors 与宿主实现一起核。

关键词：`validated_at: 2026-11-03`、`validated_ref: #2446 head 519eb752（评论 r4453895184）`、
`applies_to: 改 docs/{en,zh}/docs/integrations/<host>.md 的自动捕获/召回描述`、
`recheck_when: codex 与 claude-code 插件不再共享 hooks 实现、或文档按宿主拆分独立维护`。

<a id="r-pc78"></a>

## R-PC78. 三个宿主的凭据处理不同源：表格里「某行没写脱敏」不是省略，而是事实（2026-11-03 实测 #2446）

审「数据流 / 捕获控制」类文档时，不能按行文推断脱敏：同一张表里部分行写 redaction、另一行未写，往往是实现差异。
2026-11-03 在 #2446 head `519eb752` 实测：

| 宿主 | 召回 query | 采集 Source | trace | 依据 |
|---|---|---|---|---|
| Codex | 先 `scrub_secrets` 去空白再定界；脱敏改变了 prompt 时整次 capture 跳过 | 原始 prompt（>200,000 字符或命中凭据则不采） | 只对 query 脱敏，注入内容原样 | `hooks/recall.py:156-169`、`hooks/prompt_privacy.py:39-47` |
| Claude Code | 与 Codex 逐行同源（见 `R-PC76`） | 同上 | 同上 | `hooks/user_prompt_submit.py:153-169` |
| Hermes | **不脱敏**，`query[:8192]` 直接进 `/v1/context/prepare` | 完整 user/assistant 文本（压缩前路径会 `redact_secrets`） | 只对 trace 的 query/注入文本脱敏 | `provider.py:821,840-841,870`、`client.py:298-314`、`helpers.py:111-127` |
| OpenClaw | **不脱敏**，`truncateUtf8(query, 8192)` 直接进请求 | 最后一条 user 文本加 `User: ` 前缀后按 JS 长度截断，无模式匹配 | 无独立 trace | `src/lifecycle.ts:415`、`src/content.ts:57-66`、`src/config.ts:20-45` |

判据：①对每行「Data sent」问「这条路径是否调用 `scrub_secrets` / `redact_secrets`」；②`grep -n "scrub_secrets\|_redact_secrets\|secret"` 该宿主插件目录，只命中 trace 或压缩前路径即说明召回未脱敏；③文档出现「any configured secret-detection rules」一类措辞时，先确认该宿主是否存在此类配置键——OpenClaw 的 11 个配置键里没有任何 secret/redaction 项，`docs/{en,zh}/docs/integrations/index.md` 的自动 prompt 隐私表也不含 OpenClaw。

关键词：`validated_at: 2026-11-03`、`validated_ref: #2446 head 519eb752（评论 r4453936763、r4453937121）`、
`applies_to: 改 docs/{en,zh}/docs/integrations/{codex,hermes,openclaw}.md 的召回/采集描述，或改这三个插件的数据路径`、
`recheck_when: 任一宿主新增凭据脱敏、或 index.md 自动 prompt 隐私表增删宿主`。

<a id="r-pc87"></a>

## R-PC87. `compatibility.json` 记录的 `evidence` 锚点要单独校验；`desktop/VALIDATION.md` 最容易被整文件 ours 解冲突（2026-11-06 实测 #2457）

每条资格记录的 `evidence` 形如 `desktop/VALIDATION.md#<anchor>`，指向该记录的唯一证据段。现有门禁
（`tests/test_desktop_contract.py`）只校验 `contractSha256` 与 operation 集合，**不校验锚点是否存在**，
所以整份 VALIDATION.md 被旧副本覆盖时 CI 全绿而证据指针已经断了。

- 判据（无需构建、不改被审仓库）：读 head 与 `origin/master` 两份 `desktop/VALIDATION.md`，按标题生成 GitHub 锚点
  （小写、去标点、空格转 `-`）求**集合差**，再把 `compatibility.json[*]["evidence"]` 的后半段套进去对账。
  #2457 实测：删 4 个章节 ⇒ 4 条记录悬空（`9f279e4e`/`a9f6fd36`/`4568b499`/`da44b918`），其中
  `sqlite-observability-4568b499-v1` 的 `de74d806…` 正是当时 master 的 bundled 契约摘要，属于「删掉现役记录的唯一证据」。
- 只看「有没有这条记录」不够：记录仍在数组里、`contractSha256` 仍自洽，只有锚点消失。
- 同一症状的伴生证据：master 侧出现的 probe 提交 OID（如 `e4d5e873…`/`581cf26b…`）与实测计数（133/183/62）
  在 head 归零，且 head 历史里有两个 `merge: sync ... with master` 提交 ⇒ 判为「冲突按 ours 整文件解」，
  修复要恢复整段，不是补一个指向别处的指针。
- 契约文本一改，bundled `contractSha256` 前移，VALIDATION.md 里「X matches the current bundled API contract」
  这类断言会立刻失效（#2457 第 182 行即此例：`de74d806…` ≠ `3ff44a9c…`），与 R-PC56/R-PC61 同族，改 openapi 后必须回扫这类措辞。

关键词：`validated_at: 2026-11-06`、`validated_ref: #2457 head a676623b（`desktop/VALIDATION.md`、`desktop/src-tauri/src/connections/compatibility.json`）`、
`applies_to: 任何改动 `openapi/powercontext.yaml` 或 `desktop/VALIDATION.md` 的 PR`、
`recheck_when: `tests/test_desktop_contract.py` 增加锚点校验、或 `desktop/scripts/generate.mjs` 改变 `evidence` 生成方式`。

<a id="r-pc104"></a>

## R-PC104. 判「分步上限 ≥ 逐用例超时之和」时分母要用实际收集数，不能取 durations 文件的键集（2026-11-09 实测 #2515）

- `.github/oceanbase-migration-durations.json` 是**某一次运行**的节点时长快照（自带 `source_commit`），不是当前收集集。
  master 或本 PR 新增用例后，新节点不在键集里；`assigned_nodes` 用全体中位数兜底，于是排序把它们放到最后、
  按"负载"而非"条数"分摊，**条数分布会随兜底假设翻转**。
- 取分母的方法：`pytest --collect-only -q -k oceanbase <该步骤的 --tests 列表>`（脚本本身也是用 `-k <backend>` 收集，
  例如 3 个 clean-migration 套件共收集 144、其中 oceanbase 47）。
- 实测对照（head `c63f9b42`）：clean-migration 收集 47 个 = durations 47 个 → 打包 22/25，`25×(360+10)+190=9,440s ≤ 9,600s`，
  等式成立；long-query 收集 13 个但 durations 只有 8 个（缺失的 5 个全在 master 新增的
  `tests/e2e/test_atomic_memory_fts_coverage.py`），按中位数 29s 兜底得 6/7，把缺失节点按同组在册量级（≥120s）代入则得 8/5，
  `8×(300+10)+190=2,670s > 2,400s`，翻转阈值落在 100–120s。
- `tests/test_oceanbase_ci.py::test_clean_migration_shard_budget_covers_slow_cases_and_keeps_cleanup_time` 只断言
  clean-migration 一个步骤（且 `nodes` 取自 durations 键集，本身看不见漂移）；改回 90 分钟会以 `5400 >= 9440` 失败，
  可作为该断言的负向对照。

关键词：`validated_at: 2026-11-09`、`validated_ref: #2515 head c63f9b42e6a15ce9d69fc61e56fe6b01d2b6184f`、
`applies_to: `.github/workflows/e2e-harness.yml` 中所有调用 `scripts/run_atomic_memory_clean_migration.py` 的步骤`、
`recheck_when: durations 文件刷新、`SUITES`/`--tests` 列表变更、分片数或 `--test-timeout` 变更`。

<a id="r-pc107"></a>

## R-PC107. `capture()` 的 `scope.lock` span 拓扑是 e2e 契约：把取锁移进 `memory.capture` 之内会静默打红（2026-11-10 实测 #2567）

- `tests/e2e/test_observability.py::test_memory_write_stage_spans_are_bounded_and_nested` 断言
  `powercontext capture_content_source` 的直接子 span 恰好是 `scope.lock` 与 `memory.capture` 各一个（`_only_child`）。
  `scope.lock` 由 `BuiltinRuntime._locked()` 用 `self._stage("scope.lock", ...)` 产生，父 span 就是**进入该上下文时的当前 span**。
- 因此凡是把 `_locked(...)` 从"stage 之外"挪到"stage 之内"的重构（本次是 `SourceCaptureCoalescer` 在 `_MEMORY_CAPTURE_STAGE`
  内部才 `async with lock`），`scope.lock` 会变成 `memory.capture` 的子 span，用例 `assert 0 == 1` 红，且 e2e 红会经
  `contains(["success","skipped"], needs.tests.result)` 让 31 个 suite job 全部 skip（本次同 head 的 OceanBase 验收因此零证据）。
- 归因手法：本地跑该单用例即可，42s 量级。`head` 1 failed / `merge-base` 1 passed 就是 PR 引入；不要因为"只是 trace 形状"
  判 P3，它拦的是强制 e2e 门禁。复现要带 `PYTHONPATH=<head>/src` 与 `psutil`（`server/process_metrics.py` 直接 import）。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2567 head d47f4279（head 1 failed 42.63s / merge-base 2291237a 1 passed 28.82s；CI job 129279017925）`、
`applies_to`：改动 ScopedSourceApplication.capture、_locked、_stage 或 trace 拓扑的 PR；`recheck_when`：该用例被重写、_locked 不再自建 span，或 e2e 门禁改为 required check。

<a id="r-pc110"></a>

## R-PC110. 改 `openapi/powercontext.yaml` 等于改 Desktop 契约摘要，并连带作废真机资格记录（2026-11-10 实测 #2580 / #2553）

- `desktop/scripts/generate.mjs` 把 `sha256(openapi 字节，CRLF→LF)` 写进 `desktop/ui/src/generated/operations.ts` 与
  `desktop/src-tauri/src/transport/operations.json` 的 `contractSha256`。`tests/test_desktop_contract.py` 的两个参数化用例强制它
  等于当前 openapi 摘要；`test_bundled_desktop_contract_has_a_qualified_business_profile` 又要求存在 `contractSha256` 相同的
  `connections/compatibility.json` profile。⇒ **即使只新增 schema、不改任何 path，也会同时打破这两层**，"纯文档性 schema"
  不是可忽略变更。
- 判 CI 红先看 preflight 是否倒在 `test_desktop_contract.py`：这类红是 PR 引入而非基线。#2580 加 `TaskStopReason` 后摘要
  `de74d806…`→`34cc6572…`，两个 manifest 未重生成，`make contract-test` 在 preflight 直接 `2 failed, 65 passed` exit 2，
  其余约 34 个 suite 被 skip ⇒ 该 head 上任何行为改动都拿不到 CI 验收证据。
- 真机资格记录绑定 `serverCommit` + 摘要（`desktop/VALIDATION.md` 的 `sqlite-…-v1`，含 wheel sha256 与 macOS 版本）。分支落后时
  几乎**必然**要跑第二次资格：先 `git merge-tree --write-tree --name-only <master> <pr>`，若冲突正好落在 `VALIDATION.md`、
  `compatibility.json`、`operations.json`、`operations.ts` 四个文件，则 rebase 后摘要必变，正文里"已 qualify"不能算完成
  （#2553：`ad2a39e2` = head = `8dc98e49`，master 已是 `93b733bd`，`mergeable_state=DIRTY`）。
- 无需 macOS 的复核手法：`sha256(openapi 字节.replace(b"\r\n", b"\n"))` 与三处记录逐一比对；`merge-tree --write-tree --name-only`
  定位冲突文件；在 exact head 镜像里跑一次 `pytest tests/test_desktop_contract.py` 区分"PR 引入"与"分支落后"。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2580 head 0b434770 / #2553 head 87d7b519`、
`applies_to`：任何修改 `openapi/powercontext.yaml` 或 desktop 生成物/资格记录的 PR；`recheck_when`：摘要算法变更、
profile 不再要求摘要相等、或 `desktop/scripts/generate.mjs` 改为只对 operation 签名。

<a id="r-pc114"></a>

## R-PC114. `desktop/scripts/generate.mjs --check` 可在本机全量复核 api.d.ts / operations.ts / operations.json（2026-11-12 实测 #2270 head 8faa8345）

- 直接在该 head 的 `desktop/` 下 `npm install yaml openapi-typescript@7.13.0` 会失败：
  `verbose stack TypeError: Cannot read properties of null (reading 'edgesOut')`（arborist 在
  `desktop/package.json` 的 devDeps peer 树上崩；node 22.22.2 / npm 10.9.7）。
- 可行做法：把 `openapi/` 与 `desktop/` 复制到探针根，在**探针根**放一个只含 `{"type":"module"}` 的 `package.json`，
  在那里 `npm install yaml@2.8.1 openapi-typescript@7.13.0`（实测 34 包 / 5 s）；ESM 解析向上找到 `node_modules`，
  脚本内的 `new URL("../openapi/powercontext.yaml", root)` 仍然成立。
- `generate.mjs` 顶层的 `generateRustModels()` 需要 `@openapitools/openapi-generator-cli` 的 jar 与 `rustfmt`。
  把 `const rustModels = await generateRustModels();` 换成 `""`、并从 `outputs` 中删除 `src-tauri/src/transport/wire.rs`
  一项后，`node desktop/scripts/generate.mjs --check` 覆盖 api.d.ts / operations.ts / operations.json 三项；
  一致时打印 `Desktop contract matches OpenAPI.` 且 exit 0。
- 判据：该命令 exit 0 才能判「生成物与契约一致」。手工改 `contractSha256` 只会让 `tests/test_desktop_contract.py`
  通过（它只比对常量），不构成一致；二者必须分开取证。
- 未覆盖：`wire.rs`（Rust 侧模型），报告中须单列。
- **打桩本身不能用 `Path.write_text()`（2026-11-13 实测 #2270 head db2c2cf6，假阳性一次）**：`license` 变量取自
  脚本**自身源码**（`readFile(new URL(import.meta.url))` 取到首个 `*/` 之前），所以在 Windows 上用 Python
  `write_text()` 改写 `generate.mjs` 会注入 CRLF，生成物头部随之变 CRLF，`--check` 报
  `Contract drift: ui/src/generated/api.d.ts`，而 diff 只在前 14 行（header）。必须 `write_bytes(text.encode())`
  或 `newline="\n"` 写补丁；出现「只差 header 行」的 drift 时先查打桩脚本自身的行尾。
- 该 head 的 yaml 已升到 `2.9.0`（`desktop/package.json`）；装错版本会影响判据可信度，装前先读 pin。
- 归档建探针树时必须 `git -c core.autocrlf=false -c core.eol=lf archive`，否则解出的 header/产物全是 CRLF。

关键词：`validated_at: 2026-11-13`、`validated_ref: #2270 head 8faa8345（openapi 02022649…，510 074 B）/ head db2c2cf6（54c69ae3…，511 348 B，--check exit 0）`、
`toolchain: node 22.22.2 / npm 10.9.7 / openapi-typescript 7.13.0 / yaml 2.8.1 / pnpm 10.18.3`、
`applies_to: 改动 openapi/powercontext.yaml 或 desktop 生成物的 PR`、
`recheck_when: generate.mjs 的 outputs 定义或顶层生成步骤、openapi-typescript 版本、desktop 生成流程变更`。

<a id="r-pc134"></a>

## R-PC134. 宿主包装标签有权威全集：`capture_ownership/host.py` 与 workbuddy hook 的四个标签，判"是否识别宿主提示块"以它们为准（2026-11-23 实测 #2771）

- 仓库里有两处一等公民定义：`evaluation/memory/capture_ownership/src/powercontext_eval_capture_ownership/host.py:87`
  与 `integrations/workbuddy/plugins/powercontext/hooks/workbuddy_powercontext_hook.py:77-80`，都是
  `("system-reminder", "conversation_history_summary", "cb_summary", "task-notification")`。
  hook 侧还有 `tests/workbuddy_plugin/test_hook.py:299 test_recall_query_keeps_the_current_turn_when_cb_summary_follows_it`
  专测"总结块跟在当前回合之后"的场景。
- 审任何"识别/跳过宿主提示块"的改动时，先拿这两个文件当标签全集基准：只认 `system-reminder` 的实现属于子集，
  要问清"网关模式下是否只存在这一类宿主"，否则后果是召回 query 变成包装正文 + `message_anchor`（`replay_cache.rs`）
  逐步漂移导致每次工具续写都重新 prepare。
- 反向也成立：改 hook 侧标签集必须同步评估网关侧 `turn_message.rs`，两处不一致会让同一宿主在 hook 模式与
  gateway 模式下行为分叉。
- Core 侧约束别猜：`src/powercontext/builtin/runtime/context_check.py::_validate_prepared` 只要求 prepared_contexts
  的 location 顺序递增、同指针内不重叠、字节内容与 reuse 证明一致，**不要求**锚在最后一条 user 消息，
  所以把注入点改到非末条 user 消息是合法的（#2771 的 pointer 断言 `/input/1/content/0/text` 即此）。

关键词：`validated_at: 2026-11-23`、`validated_ref: #2771 head d7529c12 / master b5177d87`、
`toolchain: 静态推导 + Core 源码核对`、`applies_to: master`、
`recheck_when: hook 或 capture_ownership 的标签集变化、网关新增宿主适配、或 Core 对 prepared_contexts 位置提出新约束`。

<a id="r-pc135"></a>

## R-PC135. 新增 `x-powercontext-scope-mode: current` 操作必须同步 Codex 插件 `_CURRENT_OPERATIONS`；参数化用例总带 `scope_id` 会掩盖缺项（2026-11-23 实测 #2725）

- 契约面：`integrations/codex/plugins/powercontext/hooks/bind_tools.py::_CURRENT_OPERATIONS` 是「按会话绑定的
  current Scope 注入」的权威集合，OpenAPI 的 `x-powercontext-scope-mode: current` 是它的来源；新操作只改 openapi
  与生成物（`operations.generated.ts` / `_generated/*`）不会自动进这个手写集合。
- 后果（实测）：钩子对 `operation not in _CURRENT_OPERATIONS and tool_input.get("scope_id") is None` 直接
  `return 0`（不给 decision ⇒ Codex 按 Agent 原样执行）。同一次探针里 `get_artifact` /
  `get_topic_memory_processing_status` 都拿到 `{'scope_id': 'bound-scope'}`，而 #2725 新增的
  `get_artifact_processing_status` 无输出；该操作 `scope_id` 是必填 path 参数 ⇒ 未省略 Scope 就会 4xx。
- **为什么 CI 是绿的**：`tests/codex_plugin/test_scope_binding.py::test_pre_tool_hook_binds_every_current_scope_operation`
  对每个 current 操作都传 `{"scope_id": "agent-selected"}`，缺项的成员仍会走 `resolve_scope_id` 并被覆盖成绑定值，
  所以照样通过。判「集合已同步」必须确认用例里存在**省略该键**的变体，而不是看它对集合做了参数化。
- 取证：按路径 `importlib` 加载钩子，monkeypatch `resolve_scope_id` / `CodexPluginSettings`，喂 stdin 比较三类操作
  的输出（探针 `_state/r109/probe_bind_tools_2725.py`）。钩子文件未被 PR 改动时，`git rev-parse` 两侧 blob 相同即可
  直接拿工作区副本当 head 证据（#2725：`7c82e0ea`）。

关键词：`validated_at: 2026-11-23`、`validated_ref: #2725 head f2b960a2 / master 95bc5733`、
`toolchain: CPython 3.14.3（工作区 .venv）`、`applies_to: master`、
`recheck_when: bind_tools.py 的分组集合改名或改为从生成物派生、或 codex 插件的 scope-mode 用例改为不带 scope_id`。
