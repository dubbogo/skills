<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：CI、构建与依赖

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc02"></a>

## R-PC02. 分支门禁（master ruleset）

- 经典 branch protection 未启用（`/branches/master/protection` 返回 `Branch not protected`），门禁在 ruleset 里：`master` = ruleset id `9930477`。
- 该 ruleset **没有 `required_status_checks` 规则**，因此 `gh pr checks <no> --required` 返回 `no required checks reported ...` 且退出码 1 属正常现象，不是证据缺口。给出结论时必须结合 ruleset 判断，不得据此判为"required check 缺失/异常"。
- ruleset 实际包含：`deletion`、`non_fast_forward`、`pull_request`（**`required_approving_review_count: 2`（2026-10-12 由 1 上调）**，`require_last_push_approval: false`，`required_review_thread_resolution: false`，`require_extra_approval_for_unattributed_changes: true`，允许 merge/squash/rebase），以及 `copilot_code_review`（`review_on_push: true`、`review_draft_pull_requests: false`）。
- **`bypass_actors` 已不再是空数组**：2026-10-12 起为 `[{actor_id: null, actor_type: "OrganizationAdmin", bypass_mode: "always"}]` ⇒ 组织管理员可旁路该 ruleset。判断"能不能合"时要按"需 2 个 approval、组织管理员可旁路"陈述，不要沿用早期"无人可旁路"的结论（见 R-PC12 的关键词修正）。
- **不要用 `merge_state_status` 当阻塞证据**：该字段由 GitHub 懒计算，REST 单次读取经常返回 `null`（本机 2026-10-09 实测 7/7 均为 `null`，落盘快照亦然）。`null` 只表示"尚未计算"，既不代表可合并也不代表 `BLOCKED`；写成"七个 PR mergeStateStatus: BLOCKED"是**无证据断言**。判阻塞一律回到 ruleset。
- **可用 `mergeable_state` 交叉验证**（与上一条是**两个不同的字段**）：2026-10-09 实测同一响应内 `merge_state_status: null` 而 `mergeable_state: "blocked"`。后者是合并框的判定结果，取值 `clean`/`blocked`/`behind`/`dirty`/`draft`/`unstable`/`unknown`。结论里若要写"被阻塞"，应引用 `mergeable_state`，并说明它由哪个闸门触发。
- 阻塞的实际来源**至少有两类**，须分别判断：① `required_approving_review_count: 1`（缺 1 个 approving review）；② 未解除的 `CHANGES_REQUESTED`（见 R-PC12）。两者相互独立——补齐 approval **不会**顺带解除变更请求。结论中必须区分"策略阻塞"与"代码问题"。注意 `reviewDecision`（`REVIEW_REQUIRED` 等）只出现在 GraphQL，本机 GraphQL 通道不可用时取不到，不要凭印象补写。

关键词：`validated_at: 2026-10-17`、`validated_ref: 7307e8e08fa230cac67743be7db77caa5e44302d`（PR #1562 Head）、`toolchain: -`、`applies_to: master`、`recheck_when: ruleset 9930477 变更、启用经典 branch protection、或新增 required_status_checks`。

<a id="r-pc03"></a>

## R-PC03. CI 真实命令与覆盖范围

- `Main` 工作流（`.github/workflows/master.yml`）中与本仓库 TS 插件相关的 job：

| job | 命令 | 覆盖内容 |
|---|---|---|
| `pi-package` | `make pi-test` | `pnpm --dir integrations/pi/plugins/powercontext install --frozen-lockfile` + `test` + `run typecheck` |
| `dsh-package` / `opendal-package` | 同构的 `make <host>-test` | 对应宿主包 |

- `pi-package` 运行在 **ubuntu-latest**，工具链由 `mise` 按 `.mise.toml` 固定为 `node 22.19.0` + `pnpm 11.13.1`。
- **没有 Windows / macOS 的 TS 插件测试 job**（`native-service.yml` 的 windows/macos 只覆盖原生服务）。因此依赖 `node:path.join` 结果做字面量断言的测试在 Windows 上会红而不被 CI 发现；审查此类断言时必须手动核对平台语义。
- 触发条件：PR 改动 TS 插件源码/测试/配置，或本地无法安装依赖需要引用 CI 作为替代证据时，必须按 R05 核对真实命令、平台与选择集——`pi-package` 的 job 名不能替代 `make pi-test` 的内容；核对时读 job 日志里的 `Test Files` / `Tests` 计数与 `tsc --noEmit` 行。
- **suite job 的 `skipped` 有两种成因，必须区分（2026-11-01 实证 #2349）**：`master.yml` 里绝大多数 suite job 的 `if` 同时含
  `fromJSON(needs.quality.outputs.suites || '{}').<suite>` **和** `contains(fromJSON('["success","skipped"]'), needs.tests.result)`。
  后者意味着**任何一个 `tests (*)` job 红，所有 suite job 全部 skip**，即使该 suite 的路径确实命中。判据：先读
  `quality`（job 名 `CI preflight`）日志里 `python3 scripts/ci_changes.py` 打印的 `"<suite>": true|false`（本次 `"dify": true`），
  再看 `needs.tests.result`；`suite=true` 而 job skipped ⇒ 被级联跳过，该 PR 对应路径**零覆盖**，不得写成"该 suite 绿"或
  "CI 已覆盖"。本次 `tests (3.12, e2e)` 红导致 `dify-tools` skip，PR 新加的 `integrations/dify/tests/test_plugin_contract.py`
  断言整轮未执行。
- **`quality` 本身红时同理，且更彻底（2026-11-02 实证 #2396）**：`quality` 失败后 `needs.quality.outputs.suites` 为空，
  `fromJSON(... || '{}').<suite>` 全部取不到 ⇒ **所有** suite job 无论路径是否命中都 skip；`upgrade-acceptance` 等也
  连带 `skipping`/`fail`。此时 check 列表里通常只剩 `license/cla` 是 `pass`。判据：先看 `CI preflight` 的 `Run checks`
  步骤结论与 `make: *** [Makefile:NNN: <target>] Error N` 那一行，再谈 suite 覆盖；不得因为"suite 显示 skipping"就把
  该 PR 写成"已跑过 CI"。本次 `#2396` 的 `tests (*)` 一个未跑，新增用例零 CI 证据。
- **`tests (*)` 是 `cancelled` 时同样触发全量 skip（2026-11-08 实证 #2526）**：`contains(fromJSON('["success","skipped"]'), ...)`
  不含 `cancelled`。`Main` run 42390978248 整体 `conclusion=cancelled`（`cancel-in-progress: true` 被后来的 run 顶掉），其中
  `tests (3.12, e2e)` 为 `cancelled` ⇒ `CI preflight` 明明打印全 `true`（含 `harness` / `oceanbase_acceptance` / `upgrade`），
  仍有 30 个 suite job `skipped`，`Acceptance (oceanbase)` 连 check run 都没产生。判据：先取
  `commits/{head}/check-runs` 看是「红」还是「取消」，再看 run 的 `conclusion`；`cancelled` 不等于失败，但也**不是**覆盖证据，
  且往往意味着上一轮 report 里的"CI 已覆盖"必须撤回。另注意 `e2e-harness.yml` 的 job 名字带 workflow 前缀
  （`harness-validation / Acceptance (oceanbase)`），只按精确名匹配会误判为"没有该 job"。

- **`cancelled` 的成因还包括 matrix `fail-fast`，且 `Upgrade release gate` 的红常是"级联"而非策略缺陷（2026-11-08 实证 #2296）**：
  `tests (3.11, e2e)` 红后，同 workflow 其余 matrix leg（`tests (3.12, e2e)`、`(3.13, unit|e2e)`、`(3.14, unit|e2e)`）
  被标为 `cancelled`，再经上一条的 `contains(["success","skipped"], needs.tests.result)` 使 30 个 suite job 全部 `skipped`
  （本次含 `desktop-validation`、`harness-validation`、`code-seekdb`、`windows-unit-portability`、`upgrade-acceptance`）。
  `Upgrade release gate` 的失败日志只有一行 `##[error]Process completed with exit code 1.`，判据在其脚本：
  `if [ "$SCOPE_RESULT" = success ] && [ "$UPGRADE_SELECTED" = false ]; then test "$UPGRADE_RESULT" = skipped; else test "$UPGRADE_RESULT" = success; fi`
  ——本次 env 为 `UPGRADE_SELECTED: true`、`UPGRADE_RESULT: skipped`（升级验收被级联跳过），即红同源于 tests 红。
  **判读顺序**：先看 `commits/{head}/check-runs` 里 tests 是红/取消，再看该 job 的 `SCOPE_RESULT/UPGRADE_SELECTED/UPGRADE_RESULT`
  三个 env，最后在 head 本地跑 `python scripts/upgrade_release_gate.py`（本次 exit 0 且输出
  `Upgrade policy: upgrade-required; ...`）以排除 `release/upgrade-support.json::persistence_sha256` 真的过期。
  不要把该 check 的红当成第二个独立缺陷。

关键词：`validated_at: 2026-11-08`、`validated_ref: #2349 head 007f5f8b（run 41270509778）、#2396 head 7e6f6803（run 41430808818 / job 125228607409）、#2526 head 105e7a94（run 42390978248）、#2296 head aa77ac80（run 42380498052 / job 128436321006）`、`toolchain: node 22.19.0 / pnpm 11.13.1`、`recheck_when: .mise.toml、Makefile 的 pi-test 目标、master.yml 的 suite job `if`、matrix fail-fast 设置或 ci_changes.py 变更`。

<a id="r-pc10"></a>

## R-PC10. CI 作业全集（2026-10-09 实测）

`master` 的 `Main` 等 workflow 对同一 head 会产生 **25–26 个 check run**：`tests (3.11/3.12/3.13/3.14)`、`Acceptance (sqlite)`、`Acceptance (oceanbase)`、`code-seekdb (3.11/3.14)`、`quality`、`validate`、`Check License Header`、`dify-tools`、`evaluation-tests`、`check-website`、`website-link-validation-windows`、各宿主包 job（`pi-`/`dsh-`/`opencode-`/`openclaw-`/`opendal-package`）、`hermes-skills`、三平台服务化 job（`linux-systemd-user`/`macos-launchagent`/`windows-task-scheduler`）、`windows-unit-portability`。因此"25/25 绿"是可信的覆盖面描述，但 ruleset 里**没有** required checks —— 出现单项红（如 `tests (3.12)`）时先按 §9 的第 2 种情况逐项说明，再判是否本 PR 引入：**本仓历史上出现过与被审 PR 无关的 `tests (3.12)` 时间敏感用例抖动**（`test_model_usage_recorder.py::test_flush_waits_only_for_its_entry_prefix`，1 秒写预算路径）。

关键词：`validated_at: 2026-10-09`、`validated_ref: 7d16522ae3147638ccef0eeb81feafb0eaa2381c`（PR #1883 Head）、`87fceeb7bbc703b6d2efa2003277e40b0fc2262b`（PR #1873 Head）、`applies_to: master`、`recheck_when: .github/workflows/* 增删 job、ruleset 新增 required_status_checks`。

<a id="r-pc32"></a>

## R-PC32. 新增 `builtin`/`images` 模块后必须核 extra 的模块级导入闭包（已被 CI 抓到一次）

`pyproject.toml` 的 extras 是**声明式**的：把新模块并进 `builtin/runtime` 的模块级导入链，会让
`pip install "powercontext[builtin]"` 立即 import 失败，而 `tests (x, unit)` / `quality` 因为工作区已装
`server`+`cli` 依赖而完全看不到。

- **命中面**：在 `src/powercontext/builtin/**` 新增模块并在 `builtin/runtime/application.py`（或
  `builtin/runtime/__init__.py`）的模块层导入；同时新增/调整 `pyproject.toml` 的 `builtin`、`images`、
  `seekdb` 等组合型 extra。
- **当前 extras 事实（2026-10-21）**：`builtin` = aiosqlite/alembic/apscheduler/filelock/httpx/jsonschema/jieba/
  packaging/pydantic-ai-slim/pydantic-settings/pyyaml/pyobvector/pymysql/sqlalchemy/sqlite-vec/tzdata；
  **`platformdirs` 只在 `server` 与 `cli`**；`images` = `powercontext[builtin]` + `pillow`；`seekdb` = `powercontext[builtin]` + pylibseekdb。
- **实例（PR #1956，head `3fde6d5f`）**：新增 `builtin/images/service.py:64` 的
  `from powercontext.paths import powercontext_data_dir`（`paths.py` 模块级 `from platformdirs import user_data_path`），
  经 `builtin/runtime/application.py:151` 进入 builtin 的模块级导入链 ⇒ `isolated-installations (3.11, builtin)`
  job 119297345299 与 `(3.14, builtin)` job 119297345844 双红，`ModuleNotFoundError: platformdirs`。
- **实例（PR #2313，head `328f6680`，2026-10-31）**：新增 `builtin/runtime/context_bindings.py:26` 的模块级
  `from cryptography...`，经 `builtin/runtime/__init__.py`（本 PR 新增 `context_check` 导出）与
  `application.py:205` 进入 builtin 闭包。真实链路：`powercontext.ops` → `server.configuration` →
  `server.settings` → `builtin.runtime.config` → `builtin.runtime` → `application` → `context_bindings`，
  于是 `scripts/prepare_managed_resources.py`（第 48 行 `from powercontext.ops.resources import ...`）
  一被导入就要求 `cryptography`。**修法不是补 extra**：`Managed resource candidates` 的前置步骤要求
  `find_spec('cryptography'|'jieba'|'maturin') is None`（三包由 pinned input preparation 产出），受控
  producer 环境永远不会有它 ⇒ `Candidate windows-x86_64` / `macos-arm64` / `macos-x86_64` 三个 job 同签名
  `ModuleNotFoundError: No module named 'cryptography'`（run 41090034852），base 分支 `677f8885` 同三 job
  全 success、`git grep 'from cryptography' -- src` 在 base/master 均为 0 ⇒ 判定为 PR 引入无争议。只能延迟导入
  （函数内导入或 `TYPE_CHECKING`），并加一条"无 `cryptography` 的解释器里 `import powercontext.ops` 成功"的回归。
- **受控 producer 环境排除清单（2026-10-31 实测）**：`Managed resource candidates` 的执行环境刻意不含
  `cryptography`、`jieba`、`maturin`。任何进入 `powercontext.ops` 模块级闭包的新模块都不能在模块层导入它们；
  该 job 的三条日志路径（`Candidate <target>`）也因此是"optional 依赖被模块级牵入"最快的探测器。
- **判据（无需真实安装）**：只统计**模块级**（`Module.body` 与 `ClassDef` 体，不含函数体与 `TYPE_CHECKING`）
  `powercontext.*` 导入闭包，base 与 head 各算一次；base 不含 `powercontext.paths`、head 含 ⇒ PR 引入。
  函数内的延迟导入会把闭包算大，所以必须排除函数体，否则误判成 base 也有问题。
- **CI 归属**：`isolated-installations (<py>, <角色>)` 矩阵逐角色装 wheel 再跑 `scripts/ci_role_smoke.py`；
  `(x, builtin)` 与 `(x, builtin,cli)` 是不同角色，前者才等价于"只装 builtin"。base `2d11abd6` 的 run
  39602208746 里八个角色全 success，所以该红是本 PR 引入而不是基线。
- **修复方向**：把缺失依赖补进对应 extra（与 `server`/`cli` 对齐），或让新模块不依赖 `paths`（配置注入 / 延迟导入）。
- **附带核对**：`images` extra 只组合 `builtin` + pillow，因此 builtin 的依赖缺口会同时让 `powercontext[images]` 不可用；
  新增 extra 时要把它引用到的所有 extra 一并列进验证矩阵。

关键词：`validated_at: 2026-10-31`、`validated_ref: 328f66801ed6afb0352dc5dff7d9e138f60c9d11`（PR #2313 Head，run 41090034852）、`677f8885fe4df917481b6417f0fd0df55dfc1496`（2313 stacked base，三 job success）、`3fde6d5f443526274cb66e347cc326e3ebe4609a`（PR #1956 Head）、`2d11abd6ab24592427cc4a42132101ef77884245`（base/master，run 39602208746）、`toolchain: -`、`applies_to: pyproject.toml 的 extras、src/powercontext/builtin 的模块级导入链，以及 powercontext.ops 的导入闭包`、`recheck_when: extras 增删依赖、builtin/runtime 或 ops 的导入面变化、managed-resource producer 的排除清单变化、或 isolated-installations 的角色矩阵调整`。

<a id="r-pc34"></a>

## R-PC34. `cli/system.py` 的宿主可执行文件解析只在 `windows-unit-portability` 的专用 step 里被执行

- **命中面**：改 `src/powercontext/cli/system.py` 的 `_run_codex_json` / `_run_codex_mcp_list` / `_probe_codex_mcp_status`，或改 `tests/test_system_cli.py` 里带 `@pytest.mark.skipif(sys.platform != "win32")` 的 shim 用例。
- **CI 覆盖面（2026-10-23 实测）**：`Main / windows-unit-portability`（head `7b9ff4cb`，job `119823007299`）除既有的 `tests/builtin/runtime/test_artifact_processing.py` 等步骤外，另有专用 step `Verify Codex resolves and launches cmd shims on Windows`，按 node id 选跑 5 个用例（其中 1 个参数化 ⇒ `6 passed`）。这些用例在 ubuntu 的 `tests (x, unit)` 里恒 skip，所以「unit job 绿」不构成它们被执行过的证据；引用时必须写明该 job + step 名与计数。
- **本地复跑的假红**：夹具会把 `PATH` 收窄成只含临时 shim 目录，此时 cmd.exe 仍执行 `HKCU\Software\Microsoft\Command Processor\AutoRun`；AutoRun 命令在窄 PATH 下报错会进入 shim 的 stderr，使「相邻子串」断言（如 `"failed: codex failure:"`）在本机必红、在 CI 全绿。判据与处理见 `review-experience.md` 的「cmd `AutoRun` 会污染 shim 的 stderr」。
- **不要在仓库内直接执行**：这些用例只在 Windows 有意义；Linux 容器里得到的是全 skip，不是通过。

关键词：`validated_at: 2026-10-23`、`validated_ref: 7b9ff4cba125adb344eac595fcaa4fda9b1b08c2`（PR #2197 Head，job `119823007299` step 8）、`toolchain: windows-2025 runner / Python 3.12.10 / 本机 Windows + 工作区 .venv`、`applies_to: src/powercontext/cli/system.py 及其 Windows 专用 shim 用例`、`recheck_when: master.yml 增删 windows portability 的 pytest 选择集、或 shim 用例改为跨平台`。

<a id="r-pc41"></a>

## R-PC41. macOS 诊断进程组的 reap/kill 顺序，与 Desktop macOS CI 的覆盖基线（2026-10-23 实测）

审查 `desktop/src-tauri/src/diagnostic_process_macos.rs`（PR #2056 新增）或任何 POSIX 进程组清理代码时：

- **`kill(-pgid)` 必须发生在子进程被回收之前**。`Child::try_wait()` 返回 `Ok(Some(_))` 时已执行 `waitpid`，
  子进程被 reap、PID 归还内核；此后 `Group::drop` 再 `kill(-pgid, SIGKILL)`，若该 PID 已被复用为新的进程组 leader，
  信号打到无关进程组。PR #2056 head `17754f89` 的顺序是主循环 `try_wait()` → `break Ok` → `drop(group)` → `child.wait()`，
  即正常完成的每次诊断都走这条。超时/取消路径不受影响（`try_wait` 返回 `None`，PID 仍被占用）。
- **修复方向**：`libc::waitid(P_PID, pid, &mut si, WEXITED | WNOHANG | WNOWAIT)` 检测退出但暂不回收 → `kill(-pgid)` → `child.wait()`；
  不能靠「先 kill 再 wait」，因为退出检测本身就依赖 reap。
- **测试盲区**：现有三个用例断言的是「后代/launcher 是否还活着」与耗时上界，无法区分「回收前 kill」与「回收后 kill」。
  见到 `assert elapsed < 2s` 一类断言不要当作该顺序已受保护。
- **Desktop macOS CI 的覆盖基线（可直接引用）**：`Desktop validation` 工作流新增 `macos` job，矩阵 `[macos-15, macos-15-intel]`
  （`macos-15-intel` 是有效的 Intel runner label）；步骤为 `pnpm install --frozen-lockfile` → `lint` → `test` → `build` →
  `cargo fmt/clippy/test` → `ipc:check` → `credential_probe` → `pnpm desktop:build` → 上传 `bundle/dmg/*.dmg`。
  **无 `pnpm typecheck` 独立 step，但 `build` 内含 `tsc --noEmit`**，不要据此判为缺口。实测 job `119738990580`（macos-15）
  日志含 `Running tests/macos_diagnostics.rs` 与 `4 passed`，以及 lib 单测 `9 passed` ⇒ `#![cfg(target_os = "macos")]` 文件
  确实在 CI 执行，可作行为证据。
- **Node 版本分层**：`desktop/.mise.toml` = node `24.14.1`（与 `desktop/package.json::engines` 一致），根 `.mise.toml` = `22.19.0`；
  `mise-action` 设 `working_directory: desktop` 时按层级读到 desktop 的那份 ⇒ 引用「CI 用 node 22.19.0」只对根目录 job 成立。
- **`[tool_alias] pnpm = "npm:pnpm"` 是合法的 backend alias 语法**（mise 文档「Backend aliases」首例 `node = "core:node"`），
  不要按「无效字段」判 Finding；它把 pnpm 固定到 `npm:` backend，`[tools] pnpm = "11.13.1"` 仍负责版本。

关键词：`validated_at: 2026-10-23`、`validated_ref: 17754f89771f9e1a6e90c7b50b7ff0f20e7f2f3e`（PR #2056 Head）、
`toolchain: Desktop validation macos job 119738990580（macos-15）/ 119738990907（macos-15-intel），Node 24.14.1 / pnpm 11.13.1 / rustc 1.95.0`、
`applies_to: desktop/src-tauri 的 macOS 诊断进程管理、desktop.yml 的 macos job、desktop 与根目录的 mise 配置分层`、
`recheck_when: Group 的清理改为 waitid、macos job 增删步骤或矩阵、或 desktop/.mise.toml 与根 .mise.toml 版本收敛`。

<a id="r-pc43-01"></a>

## R-PC43. `quality` 的 `ty-check` 钩子覆盖 `tests/`：断言 `logging` 的动态 `extra` 字段必须走 `getattr` / `cast`（已实证）

- **现象**：新增测试写 `assert warnings[0].operation == "generate"`（`caplog.records` 的元素），pytest 通过，但 `ty check` 报
  `error[unresolved-attribute]: Object of type 'LogRecord' has no attribute 'operation'`，`quality` 与同样跑 hooks 的作业一起红。
- **根因**：`event` / `operation` / `unit` 是 `log_safely(..., extra={...})` 写进 `LogRecord.__dict__` 的动态属性；
  `logging.LogRecord` 的声明类型没有这些成员。运行期可见 ≠ 静态可解析。
- **判据**（PR #2202 head `9ab5fc8c`）：`tests/builtin/runtime/test_generation_streaming.py:52-53` 两处诊断；
  job `120264382971`（`quality`）与 `120264422367`（`Recall effort (OceanBase)`）都停在 `ty check ... Failed`，
  随后 `make: *** [Makefile:37: workflow-actions-check] Error 1`；master `1da99747` 的 `quality` 为 success、该文件不在 master ⇒ PR 新增。
- **处理**：断言改成 `getattr(record, "operation", None)`，或 `cast(Any, record)` 后取值；不要用 `# type: ignore` 掩盖，
  也不要因为"pytest 绿"判定该断言无需修改。
- **推广**：本仓任何对 `caplog` / `LogRecord` 的断言都受此约束；`ty` 的选择集包含 `tests/`，`ruff` 通过不代表 `ty` 通过。

关键词：`validated_at: 2026-10-23`、`validated_ref: 9ab5fc8c6858feddf588798422dade144f483439`（PR #2202 Head）、
`toolchain: prek hooks + ty（quality job），master 基线 1da99747`、
`applies_to: 本仓涉及 `log_safely` / `caplog` 断言的测试`、`recheck_when: `ty` 的选择集或 `ty-check` 钩子配置变更`。

<a id="r-pc48"></a>

## R-PC48. 「靠 socket 背压制造丢包」的用例在 Windows 上不成立；`windows-unit-portability` 自 #2196 起也跑日志 e2e

- **事实（2026-10-25 实测，PR #2196 head `921894c0`）**：`tests/e2e/test_worker_logging.py` 新增的
  `test_discarded_worker_record_is_counted_in_prometheus` 用 `setsockopt(SO_SNDBUF, 4096)` + 阻塞接收线程的办法让
  200,000 字符的 Worker 记录在 `sendall` 时超时，从而在 `LogReceiver._close_channel` 留下残余缓冲、把
  `telemetry_log_records_dropped_total` 抬 1。ubuntu 的四个 `tests (x, e2e)` 全绿，**Windows 上恒定失败**
  （`AssertionError: assert 0 == (0 + 1)`）：`SO_SNDBUF` 只限制发送端，Windows 的接收窗口能整条吸收该记录，
  `sendall` 直接成功、父进程把整行落盘（探针里 `background.log` 400,608 字节、含 `Large observation`），
  关闭时缓冲为空 ⇒ `on_drop` 不触发。
- **判据**：看到「小 `SO_SNDBUF`/`SO_RCVBUF` + 停顿消费者 ⇒ 期望丢包」的用例，先查三件事：① 记录是否真的没送达
  （读产物文件、数 stderr 的 `observability.log_failed`）；② 发送端是否真超时（`LogSender.send` 的超时是 0.05 s，
  Windows/loopback 上多半一次写成功）；③ 平台矩阵里是否有 Windows 执行该用例。
- **正确写法**：丢包路径要确定性驱动，而不是依赖内核缓冲——向 socketpair 写入「一条完整记录 + 一条截断记录」后
  正常关闭，`_close_channel` 必然统计 1 条残余；队列满路径则让 `deliver` 抛 `Full`。
  本轮探针：`D:	est\github
eview\oceanbase-powercontext-pr-2196\probes\probe_partial_close.py`（得到
  `delivered=['delivered-record']`、`drop_counts=[1]`）与 `probe_drop_metric2.py`（Windows 上整行送达的反证）。
- **CI 归属**：`Main / windows-unit-portability` 在本 PR 里新增了 step `Verify spawned worker logging on Windows`
  （`uv run --locked --no-sync pytest -q tests/e2e/test_worker_logging.py`），即该文件的多平台覆盖由 **这一个** job 承担；
  `tests (x, e2e)` 只跑 ubuntu。判「日志/进程边界改动是否有 Windows 证据」时引用该 job + step 名，别引用 e2e job。
- **PR 自身加的 step 变红要按本 PR 引入处理**：该 step 由本 PR 的三行 workflow 改动引入，master 上没有，所以「master 绿」
  不是免责证据；归类为 P1 并在评论里写明 head 的 job/step 与失败签名。

关键词：`validated_at: 2026-10-25`、`validated_ref: 921894c0c37e5f41c33729b197eeaf624f5e3500`（PR #2196 Head，job
`121156274990`；含 `fix(logging): count receiver-confirmed log loss` 增量）、`toolchain: Windows / Python 3.14.3 工作区
.venv；ubuntu-latest + windows runner`、`applies_to: `tests/e2e/test_worker_logging.py`、`LogReceiver` 相关用例与
`windows-unit-portability` 的选择集`、`recheck_when: 该用例改为确定性驱动、`_log_transport.py` 传输契约变更、或
`windows-unit-portability` 的 pytest 选择集调整`。

<a id="r-pc53"></a>

## R-PC53. 仓库没有 `pytest-asyncio`：异步用例必须自带 `asyncio.run` 包装（2026-10-27 实测）

- 判据链：`pyproject.toml` 的 `[tool.pytest.ini_options]` 只有 `testpaths` / `pythonpath` / `markers`，**没有 `asyncio_mode`**；
  `[dependency-groups].dev` 与 `uv.lock` 全文只有 `pytest` / `pytest-cov`（无 `pytest-asyncio`）；CI 的 `tests` job 走
  `make unit-test` = `uv run python -m pytest --doctest-modules --ignore=tests/e2e`，`.github/actions/setup-python-env` 只做
  `uv sync --frozen`，不会注入插件。
- 因此新增的 `async def test_*` 若不加包装，会在四个 Python 版本的 unit job 全部失败，报
  `async def functions are not natively supported`。仓库既有做法是模块内自建装饰器 + `asyncio.run`
  （`tests/builtin/runtime/test_topic_memory_application.py` 的 `@wraps` 包装），或直接把用例写成同步函数并在函数体内 `asyncio.run(...)`。
- 取证方式（无需 CI）：在 exact head 副本上按 CI 同一选择集跑目标文件
  `PYTHONPATH=<tree>/src <venv>/python.exe -m pytest --doctest-modules -q <file> -p no:cacheprovider`，看是否有
  `async def functions are not natively supported`。
- 注意区分：`competition/` 自带 `pytest.ini`（`asyncio_mode = auto` + `-p pytest_asyncio.plugin`）并在
  `competition/requirements.txt` 里声明插件，那里裸 `async def` 可以跑；**根 `tests/` 不行**。不要因为 competition 下能跑就推断 `tests/` 也能跑。
- 反向情形：若某 PR 想把 `pytest-asyncio` 引入 dev 组，那是仓库级变更（依赖 + `asyncio_mode`），应按独立提交审查，并核对
  `--doctest-modules` 下的收集行为。

关键词：`validated_at: 2026-10-27`、`validated_ref: #2271 head 39548bc0 / #2231 head fdadc435`、
`toolchain: Windows / Python 3.14.3（工作区 .venv，pytest 9.1.1）`、`applies_to: 根 tests/ 下所有新增测试`、
`recheck_when: pyproject 的 pytest 配置、dev 依赖组或 uv.lock 引入 pytest-asyncio/anyio 插件、或 Makefile 的 unit-test 目标变更`。

<a id="r-pc66"></a>

## R-PC66. 提交进仓库的生成 bundle 必须有「重建后逐字节比对」的门禁，否则会在无关 PR 里漂移（2026-10-31 实测）

本仓有三类提交生成物的插件目录，门禁强弱不同：

| 生成物 | 门禁 | 是否比对 |
|---|---|---|
| `integrations/cindy/plugins/powercontext-hooks/node/worker.cjs` | `make cindy-test` 里的 `git diff --exit-code -- .../worker.cjs` | **是** |
| `integrations/opencode/plugins/powercontext/lib/{index,tui}.{js,d.ts}` | `make opencode-test` = `install / test / typecheck / build`；#2322 head `9b91089c` 起追加 `git diff --exit-code -- .../lib` | 2026-10-31 前**否**，之后**是** |
| `desktop/ui/src/generated/*`、`desktop/src-tauri/src/transport/operations.json` | `generate:check` / `make contract-test`（见 R-PC28、R-PC61） | 视产物而定 |

后果实测（#2322 head `d2d8c7b5`）：`lib/index.js` 长期落后于 `src/operations.generated.ts`，一个只修 404 分类的
PR 被迫带上 11 个 operation（`get_recall_manifest`、`pc_source_*`、`source_*`）共 158 行无关生成内容——因为 #2192
与 #2210 合入时都没重建 bundle。`package.json` 的 `files` 只发布 `lib/*`，`src/` 不随包分发 ⇒ 陈旧 bundle 等于
功能缺失，而 CI 全绿。

审查要点：

- 修改 `src/**` 同时提交 `lib/**` 的 PR，先确认 `pnpm run build` 的产物与提交内容**逐字节相同**
  （`diff <(tr -d '\r' < built) <(tr -d '\r' < committed)`；本机 Windows 生成 CRLF，仓库 blob 是 LF）。
- 生成物随 PR 出现与本 PR 主题无关的大段 hunk，不要当成"顺手整理"放过：先判是漂移补票还是新逻辑，
  再按维护性给 P2（本仓已有 `cindy-test` 的正面先例，建议照抄 `git diff --exit-code`，Windows 差异可用
  `--ignore-cr-at-eol`）。
- 反向也要核：`OPERATIONS` 这类表被声明为"没有工具从中注册"时，逐个核对消费方（本仓为
  `src/client.ts` 的存在性检查与 `src/invoke.ts` 的 `scopedPayload`），不能只信 PR 正文。
- **契约变更必须让 `cindy` bundle 同步，而这类红只能在 merge ref 上看到**（2026-10-31 实证 #2270 head
  `886a0cfb`）：`Main` 的 `cindy-package` job 是 `pull_request` 事件、`actions/checkout` 默认检出
  `refs/pull/<N>/merge`，工作树里同时有 master 的 `integrations/cindy/` 与本 PR 的 `openapi/powercontext.yaml`。
  若 `integrations/cindy/` 是在本 PR 的 merge-base **之后**才进 master，PR head 的树里根本没有这个目录
  ⇒ 本地 `make cindy-test` 无从复现，只能引用该 job 的日志（本次失败 diff 是 4 个新 operation 的纯新增条目）。
  定位失败步骤用 job 的 `steps[]` 名称，不要只按 job 名判断。
- **新增「重建后逐字节比对」门禁时，必须在 merge 结果上验证，分支树自洽不算通过**（2026-11-01 实证 #2322
  head `9b91089c`）：该 head 的 `Makefile:213` 已加 `git diff --exit-code -- integrations/opencode/plugins/powercontext/lib`，
  分支树 `OPERATIONS` 141 条与 `lib` 141 条一致，本地 `make opencode-test` 能过；但 `opencode-package`
  检出的是 `ddcc12b7`（`Merge 9b91089c into 176b3f92`），其中 `src/operations.generated.ts` 148 条、`lib` 141 条，
  重建后 `lib/index.js`/`lib/tui.js` 各多 77 行（7 个 `*_artifact_plugin` 操作，来自已合入的 #2246），门禁必红。
  判据：对 **head 树 / `refs/pull/<N>/merge` 树 / base tip** 三处分别数 `OPERATIONS` 条目
  （`src/operations.generated.ts` 用 `^  [a-z_]+: \{`，`lib/index.js` 用 `^\t[a-z_]+: \{`），三者一致才算通过；
  head 一致而 merge 不一致 ⇒ 作者需把 base 并入后重建 bundle，否则合入即把红带到 master。
  同一 OID 上的 `lib` 落后条数可作 base 侧欠账的量化证据（本次 master `176b3f92` 为 148/126，差 22）。
- **同一 PR 内的同根因会分批修复：只修被点名的那一个宿主，其余宿主的同类漂移仍在**（2026-11-05 实证 #2270
  head `906beaed`）：`cindy` 已补齐（blob 64624 B vs 重建 64638 B，LF 归一化相等）、`dsh` 逐字节相等（162591 B），
  但 `opencode` 的 `lib/index.js` / `lib/tui.js` 仍落后（93654 → 94783、74860 → 75989，各差 1129 B），
  而同插件 `src/operations.generated.ts:28-31` 已声明 4 个新 operation。核对顺序：先按 R-PC59 找 base 之后新增的宿主，
  再对每个宿主分别重建比对；不能用"被回复的那一个宿主已修"推断其余已修。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2322 head d2d8c7b5 / 9b91089c（merge ddcc12b7）、#2270 head 886a0cfb / 906beaed`、`applies_to: master`、
`toolchain: pnpm 10.18.0 / node 20+`、
`recheck_when: `Makefile` 的 `opencode-test` / `cindy-test` 调整，或 `integrations/*/plugins/*/package.json`
的 `files`/`build` 变化`。

<a id="r-pc72"></a>

## R-PC72. 「release-aware」调用必须对**已发布版本的 CLI** 验证，分支 CI 永远看不到它（2026-11-03 实测）

`website/public/install.{sh,ps1}` 这类安装器会在装完包之后调用 `powercontext setup ...`。协议要求：凡 PR 声称
「按目标版本选择调用形态」，判据只能是 PyPI 上已发布 wheel 的真实 CLI，不能是分支源码或分支 wheel。

实测手法（隔离，R04）：`uv venv` + `uv pip install "powercontext[cli,server]==<版本>"`，
然后原样跑安装器的调用串。2026-11-03 对 1.4.0（当时的最新稳定版）得到：

- `setup --source oceanbase/powercontext --ref powercontext-v1.4.0 codex` → `Error: No such option: --source`，exit 2。
  1.4.0 与 1.3.0 的 `setup_app` 仍是 Typer **group**（`no_args_is_help=True`），`--source`/`--ref` 挂在
  `@setup_app.command("codex")` 上；把 `setup` 统一成 `@setup_app.callback(agents, source, ref, ...)` 只存在于
  master（未发布）⇒ 「默认装 latest 再 `--host`」在真实环境全线失败。
- `powercontext[cli]==1.4.0`（`--profile client` 的 requirement）连命令都没有：
  `Error: No such command 'setup'`。**同一安装器在两个 profile 下能力不同**，验证必须两个 profile 各跑一次。
- `powercontext --version` 打印裸 `1.4.0`，版本正则因此通过，失败点落在 `uv tool install` 已经替换环境**之后**
  （`install.sh` 尾部 `fail`）⇒ 结论要写「退出码 + 失败发生在哪一步」，不能只写「脚本报错」。
- 自检覆盖不到：装完只验 `--help` / `capabilities --help` / `config init --help` / `server run --help`，
  `setup` 的形态没有任何前置探针。

CI 为什么是绿的（R-PC03 的推论要用在这里）：`installation.yml` 用 `SETUPTOOLS_SCM_PRETEND_VERSION` +
`uv build --wheel` 从**分支**造 wheel，`tests/native/test_installation.py` 里 `--host` 只出现在失败路径
（`--host codex --no-hosts` 冲突、`--host unknown-host`）⇒ 绿色矩阵只证明分支 CLI 可用，不证明已发布版本可用。

同一类判据的两个坑（实测，别再踩）：

- `https://astral.sh/uv/<ver>/install.sh` 会 **301** 到
  `https://releases.astral.sh/github/uv/releases/download/<ver>/uv-installer.sh`，最终的 `APP_VERSION` 是对的。
  不 `curl -L` 跟到终点、只看首个响应体，会误判「钉版本被忽略」。
- USTC 的 `github-release` 镜像每个仓库只保留**最新版目录 + `LatestRelease/`**（uv 只有 `0.13.6`/`LatestRelease`），
  所以任何钉住旧版本的镜像路径都是 404；这类「镜像分支实际从未执行」的判断要靠列目录，不能只靠 fallback 成功。
- `uv python find --system` **仍会返回 uv 托管解释器**（uv 0.11.2 Windows、0.11.32 Linux 实测：`uv python install 3.12`
  之后 `find --system` 直接返回 `~/.local/share/uv/python/...`）⇒ 不要据 help 文案
  「Only find system Python interpreters」推断 `ensure_python` 收尾会失败。

关键词：`validated_at: 2026-11-03`、`validated_ref: #1892 head 07810b1f（base e03f54ee）、PyPI powercontext 1.4.0 / 1.3.0 标签`、
`applies_to: 改 website/public/install.{sh,ps1}、任何「按目标版本选择调用形态」的安装器或 CLI 适配 PR`、
`recheck_when: `setup` 恢复子命令形态或再次统一、`installation.yml` 增加真实发布版本矩阵、镜像站保留历史版本`。

<a id="r-pc83"></a>

## R-PC83. 改 `desktop.yml` 的 macOS 打包步骤必须同步 `tests/test_ci_pipeline.py`（2026-11-05 实测 #2306）

`tests/test_ci_pipeline.py::test_macos_build_retries_only_busy_disk_images`（`01ebe73b` 引入、`2722e8f8` 加固）不是读 YAML 断言，
而是 `next(step["run"] for step in workflow("desktop.yml")["jobs"]["macos"]["steps"] if step["name"] == "Build unsigned macOS app and DMG")`
取出该步骤的 **run 文本**，再 `subprocess.run([bash, "-c", command], cwd=tmp_path)` 真跑，最后断言返回码属于该参数化用例的期望值
**并**读 `tmp_path/.artifacts/macos-build.log`。

- 因此把该步骤换成 `python3 scripts/build_macos.py` 之类的外部入口，会让 tmp_path 里找不到脚本 ⇒ 返回码 2（`can't open file`）、
  日志文件缺失 ⇒ 用例必红。改这个步骤的 PR 必须同时改该用例的驱动入口，否则合并即打断 master。
- `id: macos_build` / 每次尝试的 `capture_macos_state` 状态日志 / `echo 'retried=true' >> "$GITHUB_OUTPUT"` 是 #2393 的诊断契约：
  上传条件是 `failure() || steps.macos_build.outputs.retried == 'true'`。换入口时丢掉它们，「重试成功」那一类运行就不再上传诊断。
- 判「本 head CI 绿」不能覆盖此风险：该用例文件在本 head 上不存在（由 master 侧提交引入）。基线过旧（本例 base 落后 98 个提交）时，
  对改动 CI 步骤的 PR 一律先 `git merge-tree --write-tree <master tip> <head>` 拿冲突清单，再按 master 侧新增的测试文件反查是否被破坏。
- 顺带：`gh pr diff` 用 merge-base 三点式，`mergeable` 字段会先 UNKNOWN 后 CONFLICTING，判阻塞以本地 `merge-tree` 为准更稳。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2306 head bc54b211（评论 r4480950819、master tip 20f64d72、probes/ci-pipeline/）`、
`applies_to: `.github/workflows/desktop.yml` 的 macos 作业与 `tests/test_ci_pipeline.py``、
`recheck_when: 该用例改名/改驱动方式、macOS 打包步骤换入口、或 #2393 的诊断上传条件变动`。

<a id="r-pc88"></a>

## R-PC88. master 的 `gateway/crates/pc-gateway-core/src/lifecycle.rs` 缺 license header ⇒ `CI preflight` 红 ⇒ **全部 suite job skip**（2026-11-06 实测）

`.licenserc.yaml` 的 `Check License Header` 会扫全树；本日 master 树上该文件首行是 `use crate::ManagedOutcome;`，
缺 Apache header，于是任何未自带该修复的 PR 都在 `CI preflight` 失败：`quality` 红 ⇒ `needs.quality.outputs.suites`
为空 ⇒ 所有 suite job（含 `tests (*)`、`desktop-validation`…）全部 `skipping`，只剩 `license/cla` 是 pass。
判据就是 R-PC03 那条，但套用顺序是：先看 `Check License Header` 那行 `invalid: 1` 的文件名，再看 `CI result`
——**不要**把 `tests (*) skipped` 读成「该 suite 与本 PR 无关」。

- 实测对照：#2505（1 文件测试修复）与 #2500（博客）与 #2396 三个 PR 同签名红在同一个文件上；#2457 与 #2270
  因为在 head 上补了该 header 而 `CI preflight` success。
- 归纳：#2270 分支上 `lifecycle.rs` 已有 header、master 没有 ⇒ 说明这是 base 侧缺陷，不归责单个 PR；
  在它修进 master 之前，**任何 PR 的 suite 覆盖都要用本地/其它平台补**，不能引 CI 作证据。
- 关联：#2504（单文件「restore the license header on the managed-call lifecycle」）与 #2457 都在同一位置加 header，
  两处 header 的 license URL 缩进不同（4 空格 vs 无缩进），合并时按文件冲突处理，别按「同一修复可自动合并」预期。

关键词：`validated_at: 2026-11-06`、`validated_ref: master 69b2d7e2 / run 42153866834（job 127683257158）、#2457 head a676623b、#2270 head 95e1626f`、
`applies_to: 本日 master 基线；`recheck_when: master 的 `lifecycle.rs` 补上 header、或 `.licenserc.yaml` 的 header/ignore 规则变化`。

<a id="r-pc93"></a>

## R-PC93. 网关的 listener 门禁 ≠ 端口收口：`PC_GATEWAY_API_KEY` 只覆盖 `/gateway/*`（2026-11-07 实测 #2523）

- 路由形状：`main.rs` 的 `router()` 只有 `/healthz`、`/gateway/v1/chat/completions`、`/gateway/v1/responses`
  三条显式路由，其余全部落到 `proxy::fallback`（`pc-gateway-app/src/proxy.rs`），而 `fallback` 把
  `parts.headers` 原样转给 Core，网关侧不鉴权。密钥只在 `ingress::ingress_model` 校验。
- 因此组合部署（`PC_GATEWAY_CORE_UDS`，Rust 持有公网 TCP 端口）里，代理面能否访问取决于 Core 自己：
  `create_app` 在未配置 `AccessControlService` 时把 `app.state.access_mode` 置为 `disabled`，
  该模式下 `access_control_for_mode()` 返回 `None`、`/v1/*` 全部不鉴权。
- 判据：任何「非 loopback 必须有 key」「端口已收口」类声明，都要先确认保护范围是 listener 还是 `/gateway/*`；
  该 PR 自带用例即证据——`/v1/capabilities` 用网关 key 是 401、用 Core token 是 200。
- 复核方法：`gh api repos/oceanbase/powercontext/contents/<path>` 取 head 的 `main.rs`/`proxy.rs`/`app.py`
  三处即可判定，不需要起进程；`socket`/`is_loopback` 语义只在需要证明 `::ffff:127.0.0.1` 被当作非 loopback 时
  才需要跑二进制。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2523 head cc63c92b（同 tree 的 3f9c2cfd）`、
`toolchain: -`、`applies_to: `gateway/crates/pc-gateway-app/**` 的鉴权与监听策略变更`、
`recheck_when: `router()` 增删显式路由、`proxy::fallback` 开始注入 Core 凭据，或 `access_mode` 默认值变化`。

<a id="r-pc95"></a>

## R-PC95. `CI preflight` 红在 `Check License Header` 且日志含 `license-eye: command not found` ⇒ 工具安装问题，不是本 PR 引入（2026-11-07 实测 #2526）

- 现象：`quality`（job 名 `CI preflight`）第 4 步 `Check License Header` 结论 `failure`，日志只有
  `/home/runner/_work/_temp/<uuid>.sh: line 1: license-eye: command not found` 与
  `##[error]Process completed with exit code 127`（exit 127 = 命令不存在，不是许可头违规）。
- 后果：`quality` 一红，`needs.quality.outputs.suites` 为空 ⇒ 全部 suite job skip（与 `R-PC03` 的
  「`quality` 本身红」同一后果、不同成因，见 `R-PC88`）。本次 #2526 的 34 个 suite job 全部 skipping，
  `CI result` 与 `Upgrade release gate` 连带红，PR 自身新增测试零 CI 证据。
- 归因判据：**同时间段其它 PR 的 preflight 绿 ⇒ 不是仓库基线**（#2432 18:2x 的 preflight `SUCCESS`）；
  该步骤只在 `apache/skywalking-eyes/header` 安装 PATH 上失败，源码与 `.licenserc.yaml` 未参与。
- 已知修复形态：#2432 在 `master.yml` 的 `quality` 里先建一个可写目录写进 `GITHUB_PATH`，再把
  `INSTALL_DIR` 传给 action；#2525 是另一条独立改动。核对时按 job 实际步骤判定，不看 PR 标题。
- 报告口径：该类失败可写"本 PR 无 CI 证据"，但不得写成"PR 引入 CI 失败"；同时记录本地已跑的替代证据。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2526 head 10173320（run 42255009856 / job 128019774357）、#2432 preflight SUCCESS（run 42268108682）`、`applies_to: master 的 `quality` 作业`、`recheck_when: `master.yml` 的 `Check License Header` 步骤或 skywalking-eyes 版本/安装方式变化`。

<a id="r-pc96"></a>

## R-PC96. `e2e-harness.yml` 的 acceptance：分步 `timeout-minutes` 之和可能超过作业上限，`if: always()` 的门禁步骤因此永不执行（2026-11-07 实测 #2526）

- acceptance 作业上限 `matrix.database == 'oceanbase' && 75 || 40`；拆步后逐步上限是
  `oceanbase_setup` 15 + `native_acceptance` 50 + `acceptance_scenarios` 15 = **80 > 75**（replay+原生同时选中时）。
  base 里数据库启动也在同一个 50 分钟步骤内，合计 65，另留 10 分钟给证据扫描与 teardown。
- 触发面很宽：`oceanbase_acceptance` 已在 `[shared.runtime].suites` 里 ⇒ 任何 `src/**`、`openapi/**`、
  `pyproject.toml`、`uv.lock` 改动都同时选中两个范围，即最常见的一类 PR。
- 影响不只是慢：作业被整体取消时 `Require all selected acceptance work and evidence`（`if: always()`）
  不会执行，失败表现在 job 超时而非"哪一段验收没跑"，与作者写的"未选中的工作被刻意跳过、选中的必须成功"门禁意图相反。
- 审查要求：改这个 workflow 时把「分步上限之和 + teardown」与作业上限对账，并核对
  `tests/test_e2e_workflow_contract.py` 是否有对应用例；只断言 `matrix.*`、`if:` 与 `if-no-files-found` 不够。
- 不要用注释当预算证据：本 PR 的注释写"保持既有总预算"，实际数字已从 65 涨到 80。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2526 head 10173320、base 9a424e77`、`applies_to: `.github/workflows/e2e-harness.yml` 的 acceptance 作业`、`recheck_when: acceptance 作业的步骤拆分、`timeout-minutes`、或 `machine.harness/oceanbase_acceptance` 的 scope 归属变化`。

<a id="r-pc102"></a>

## R-PC102. CI 步骤上限必须 ≥ 每片用例数 × 逐用例超时：改分片数时要重算，不能只换实测均值（2026-11-08 实测 #2515）

- `.github/workflows/e2e-harness.yml` 的 `atomic-memory-clean-oceanbase-shards` 从 3 片降到 2 片后，
  `Run clean migration evidence, grants and vectors` 的 `timeout-minutes: 90` 与 `--test-timeout 300` 不再自洽：
  该组 `SUITES` 共 47 个用例（`.github/oceanbase-migration-durations.json` 实测合计 2543.7s），二分片 ⇒ 24 个/片
  ⇒ 最坏 24 × (300 + 10s kill-after) = 124 分钟 > 90 分钟；三分片时 16 个/片 = 82.7 分钟仍在范围内。
- 判据：任何"改 shard 数 / 改 per-case timeout / 改步骤上限"的 PR，必须按 **最坏情况**（片内用例数 × (timeout + kill-after)）
  对账步骤上限，而不是用 durations 均值。均值只对"总时长估算"有效，不能替代超时上界。
- 同作业其余三步仍自洽，可作对照基线：`background-metrics`（1 用例 / 10 分钟）、`startup-snapshot`（≤2 × 310s + 180s
  = 13.3 分钟 / 15 分钟）、`long-query`（4 × 310s + 180s = 23.7 分钟 / 30 分钟）。
- 附带：`scripts/run_atomic_memory_clean_migration.py` 的 `nodes.txt` 写的是**完整收集列表**（不是本片选中列表），
  所以步骤里 `test "$(wc -l < .../nodes.txt)" -eq 3` 在改分片数后仍成立——排查这类断言时先看脚本写文件的位置。

关键词：`validated_at: 2026-11-08`、`validated_ref: #2515 head 50895fe2952508009fbf9442795267f753566bc6（base ed8902b2）`、
`applies_to: `.github/workflows/e2e-harness.yml` 的 OceanBase 分片作业与 `scripts/run_atomic_memory_clean_migration.py``、
`recheck_when: 分片数、`--test-timeout`、步骤 `timeout-minutes` 或 `SUITES` 集合变更`。

<a id="r-pc113"></a>

## R-PC113. Memory 契约门禁在 JS 与 Python 两侧各有一份 fixture，修一侧不会让 `dsh-package` 转绿（2026-11-12 实测 #2270 head 95e0a357）

`dsh-package` job 里有两条独立路径都会读「已安装插件是否声明 `powercontext.memoryProtocol = atomic-artifact-v1`」：

- step 6/8（node 套件）：`integrations/dsh/plugins/powercontext/tests/runtime/setup.test.mjs`
  用 `writeFileSync(source/package.json, {...})` 造假插件；缺声明时 setup 以 `plugin_memory_protocol: unverified` 退出 1。
- step 11 `Verify DSH setup with customized profiles`：Python 套件 `tests/test_dsh_transport.py`，
  `plugin_source`（假插件的 manifest）与 `dsh_profile`（profile 写 `{"dsh":{"profile":{"bundles":[]}}}`）同样不含声明，
  `doctor dsh --profile web` 经 `installed_memory_protocol(None, "dsh")` 判 DEGRADED，退出码 1，
  `assert result.exit_code == 0` 在 `tests/test_dsh_transport.py:1072` 失败。

判据（同一 PR 两个 head 对照）：`638ec461` 未补 JS fixture 时 step 6 success、**step 8** `Test built plugin in the real DSH runtime` failure、step 9-12 skipped；补了 JS fixture 的 `95e0a357` 上 step 6-10 success、**step 11** failure、step 12 skipped。即修一侧只把失败点往后推一节，`dsh-package` 仍红。

- 归因注意：master 上该 job 常在 step 6 先红（如 `tests/status-http.spec.ts` 的 `expected 'skipped' to be 'appended'`），
  step 11 被 skip ⇒ 后置 step 没有基线对照，不能据此判「基线也红」或「PR 引入」。
- 复核手法：先读 job 的 `steps[]` 结论定位到具体 step，再取该 step 日志里的 `FAILED … - AssertionError`，不要停在 job 名。
- 该声明由 #2495 引入（`src/powercontext/cli/memory_protocol.py`）；凡 rebase 过 #2495 的 PR 都要同时核这两条 fixture。

关键词：`validated_at: 2026-11-12`、`validated_ref: #2270 head 95e0a357`、
`applies_to: 改动 integrations/dsh 插件或其 tests 的 PR`、
`recheck_when: memory_protocol.py 的 MEMORY_PROTOCOL 常量、setup.test.mjs 或 test_dsh_transport.py 的 fixture 变更`。

<a id="r-pc115"></a>

## R-PC115. 三个宿主的 bundle 在 pnpm 10.18.3 下与 CI（pnpm 11.13.1）重建结果字节相同（2026-11-12 实测 #2270 head 8faa8345）

- `make cindy-test` 的等价命令：在 `integrations/dsh/plugins/powercontext` 下 `pnpm install --frozen-lockfile --ignore-scripts`
  再 `pnpm exec tsdown --config ../../../cindy/tsdown.config.ts`；重建 `integrations/cindy/plugins/powercontext-hooks/node/worker.cjs`
  为 65 220 B，sha256 `e7acfdc5…`，与提交 blob 字节相等（CRLF 0/0）。
- 同 head 另两个 bundle 同样字节相等：`integrations/dsh/plugins/powercontext/lib/index.js` 155 284 B（`pnpm run build`）、
  `integrations/opencode/plugins/powercontext/lib/{index,tui}.js` 95 696 / 78 133 B。
- 因此本机 pnpm 10.18.3 与 CI 的 pnpm 11.13.1 在 lockfile 固定的 tsdown 0.16.8 上不产生字节差异，
  可用作「bundle 未重建」类结论的正向证据。
- 轻量前置判据：契约 `operationId` 全集（本 head 152 个）必须全部出现在各宿主产物中；缺失即 stale，无需重建。

关键词：`validated_at: 2026-11-12`、`validated_ref: #2270 head 8faa8345`、`toolchain: pnpm 10.18.3 / tsdown 0.16.8`、
`applies_to: 改动 openapi/powercontext.yaml、integrations/{dsh,opencode,cindy} 生成物的 PR`、
`recheck_when: 各插件 package.json 的 build 脚本、tsdown 版本或 pnpm-lock.yaml 变更`。

<a id="r-pc123"></a>

## R-PC123. 迁移/门禁的「接受面」扩到新资源文件时，派生校验和必须同步扩容（2026-11-17 实测 #2674）

`topic_memory_recovery_schema.py` 的 `_atomic_maintenance_layouts()`（head `89a763e4` 的 `:171-201`）
从同目录新文件 `migration_resources/topic_memory_recovery/atomic_maintenance_sqlite_v2.json` 读取第二套
pristine 布局，于是「一个已由 `atomic-memory-migrate --action apply` 初始化的 SQLite 库是否算基线」
改由该文件决定；但 `_resource_checksum()`（`:108-109`）只 `sha256(schema.json)`，而它被
`runner.checksum`（`:256`）、`_inspect` 的 `plan_changed`（`:358`）、journal `evidence["checksum"]`（`:368`）
与 `plan_id` 的 `bundle_checksum`（`:421`）共同使用。

判据（任一满足即可写成 Finding，级别按是否可导致错误迁移决定，本例 P2）：

1. 用 `grep -n "<判定函数>(" ` 找派生摘要的全部消费点，再核对它的输入集合是否等于新增的读取点集合；
2. 直接构造「只改新资源文件」的副本，重算 `_resource_checksum()` / `plan_id`，值不变即证明盲区；
3. 追这条摘要的失败语义：本例收紧接受面时 `execute()` 的 `recovery_layout()` 守卫会抛
   `unknown_baseline`（`:503-507`）而不是 `plan_changed`，放宽时零信号 —— 失败分类错位本身也是证据。

修法：把资源目录下文件按 `(相对路径, 字节)` 排序后整体摘要，并补「改新资源后 checksum 必须变化」的测试。
同类面还有 `scripts/upgrade_release_gate.py::MANAGED_INPUTS`（`src/powercontext/builtin/persistence` 下
`.py/.sql/.json` 全收）——新增 json 会改 `persistence_sha256`，改完必须重算 `release/upgrade-support.json`。

**2026-11-17 追加（head `cd4de02c` 已按上条修法改为目录摘要；该修法自带两个反作用，均实测）**：
`_resource_checksum()` 现为 `rglob("*")` 全目录摘要，而目录里除 `schema.json` 外还有
`atomic_maintenance_sqlite_v2.json` 与 `README.md`。

1. **摘要定义变化 ⇒ 发布版写入的 journal 永久失效**。同一份 `schema.json`（blob 与 `powercontext-v1.5.2`
   逐字节相同，sha256 `f28d5c52…`）：v1.5.x 的旧定义算出 `f28d5c52…`，新定义算出 `884836e6…`。
   把中断后 journal 的 `checksum` 改回旧值（其余字段、资源、数据库一律不动），`plan()` 抛
   `recovery_required: Keep the original Topic migration resources, configuration and evidence.`；
   而 `docs/{en,zh}/docs/operate/database-migrations.md` 同时禁止「Do not move evidence to an empty
   directory to bypass a recovery error」⇒ 中断 + 升级后没有受支持的前进路径。
   判据成立的前提是「已发布 journal 真实存在」：`powercontext-v1.5.{0,1,2}` 三个 tag 都含
   `migrations/topic_memory_recovery.py` 且都用旧定义，故不是假想形态。
2. **文档文件进入摘要 ⇒ 纯文档修订令在飞计划失效**（`README.md` 追加 1 字节：`884836e6…` → `28fc4e9d…`，
   `plan()` 抛 `plan_changed`），与「只覆盖控制 DDL 与接受面的资源」这条自述矛盾。

审查要求：把摘要范围从「目录全部文件」收紧或放宽时，必须同时回答「同一份资源在旧版本算出的值
是否仍被接受」；摘要定义类改动要附一条「旧值 journal + 新资源 resume」用例，不能只用
「资源内容被改动 ⇒ 拒绝」覆盖。

关键词：`validated_at: 2026-11-17`、`validated_ref: #2674 head 89a763e4（review r4594705425）、cd4de02c（r4596109693 的目录摘要反作用）、master fd165838`、
`toolchain: Windows / CPython 3.14.3（工作区 .venv）`、`applies_to: 改动 persistence/migration_resources/** 或任何以摘要绑定计划的 PR`、
`recheck_when: _resource_checksum() 改为目录摘要，或 Topic 维护流程改为把布局快照写入 schema.json 内部、或 journal 增加版本化重签路径`。

<a id="r-pc128"></a>

## R-PC128. 迁移命名门禁上线前必须枚举在飞迁移 PR：`vX_Y_Z_prNNNN` 会被新的 `000` 政策判红（2026-11-19 实测 #2713 / #2674）

- `scripts/schema_release.py::preserve_history()` 对 additions 只留两条出口：等于 `000`，或 `RELEASE_ID.fullmatch`（`v<major>_<minor>_<patch>`）。
  `v1_5_2_pr2674` 不匹配 ⇒ 抛 `Append only the shared 000 draft, or its single frozen release revision`。
- 判据：把「本 PR 合入后的链」按 `base 分支 chain + 本 PR 新增 revision` 复算一遍，逐个跑 `RELEASE_ID.fullmatch`；
  同时 `gh pr list --state open` 扫所有改 `server_resources/versions/*` 或 `mysql/versions/*` 的 PR，看它们的新增 revision 是否落在新门禁的接受面之外。
- 实例：#2713 在 `master.yml` 用 `github.event.pull_request.base.sha` 跑 `check --base-ref`，合入后 #2674（`revision = "v1_5_2_pr2674"`，open）rebase 即红；
  已合入的 `v1_5_2_pr2639` 两侧都属 `frozen`，`preserve_history` 只看 additions，所以不受影响——问题只在新增侧。
- 处置：命名政策要与在飞 PR 的兼容性一起评审（豁免 / 先合顺序 / 改草稿），不能只论证 `000` 政策本身自洽。

关键词：`validated_at: 2026-11-19`、`validated_ref: #2713 head fa34dc35 / #2674 head faccf373`、
`applies_to: 新增或修改迁移命名、链校验门禁的 PR`、
`recheck_when: preserve_history 的 additions 判据、RELEASE_ID 正则或 AGENTS.md 的迁移政策再次变更`。

<a id="r-pc129"></a>

## R-PC129. `make check` 的 prek/ty 挂在 `workflow-actions-check` 下；`pretty-format-json` 覆盖 `desktop/**`（2026-11-20 实测 #2728）

1. **`check` 目标本身没有配方**：`Makefile` 的 `check:` 只有依赖列表（version-check / upgrade-policy-check /
   workflow-actions-check / integration-manifest-check / integration-guidance-check / integration-lifecycle-check），
   而 `uv lock --locked`、`uv run prek run -a`、`uv run ty check` 这几行写在紧随其后的 `workflow-actions-check:` 配方里
   （`Makefile:46` 起）。`AGENTS.md` 说 `make check` 会跑全部 pre-commit hooks，与实现不符——判"hook 会不会红"时
   必须看这份配方本体，别只看依赖名或文档描述。CI 的 `CI preflight` 就是 `run: make check`，失败样式是
   `make: *** [Makefile:46: workflow-actions-check] Error 1`。
2. **`pretty-format-json` 覆盖 `desktop/src-tauri/src/connections/compatibility.json`**：该 hook 的 `exclude` 只列
   `.devcontainer/devcontainer.json`、两个 evaluation 数据集、`gateway/.../republic/cases/*.json`。手工往这个上千行数组
   追加资格记录时，只要新对象的 `{` 缩进比邻居少两个空格，hook 就会 `Fixing file` 并 exit 1 ⇒ preflight 红、下游全 skip。
   `json.loads` 通过、`tests/test_desktop_contract.py` 全绿都不能证明该文件过门禁。
   复现（本机已有 `prek.exe`，无需联网）：`probes/<name>/` 里 `git init` → 只留该 hook 的 `.pre-commit-config.yaml` →
   放入原文件 → `prek run pretty-format-json --all-files`。
3. **`MANAGED_INPUTS` 覆盖 `builtin/persistence/**`，连只读投影也算**：`records.py::_source_record` 只是把已存的
   `metadata` 投影到 `SourceRecord`，同样使 `managed_digest` 变化 ⇒ `release/upgrade-support.json` 的
   `schema_review.persistence_sha256` 必须同 PR 重算，否则 `scripts/upgrade_release_gate.py` 直接
   `Persistence changed`（#2728 head a79edde7：实际 `af6277a1…` vs 声明 `2fe54cca…`）。判"这 PR 要不要动 upgrade-support.json"
   的唯一判据是 `git diff --name-only` 是否命中那五个 MANAGED_INPUTS 路径，不看改动语义。

关键词：`validated_at: 2026-11-20`、`validated_ref: #2728 head a79edde7 / #2724 head 5cf3e97a`、
`toolchain: prek + pre-commit-hooks v6.0.0（Windows 工作区 .venv）、CPython 3.14.3`、`applies_to: master`、
`recheck_when: Makefile 的 check/workflow-actions-check 配方、.pre-commit-config.yaml 的 hook 或 exclude、或
upgrade_release_gate.py 的 MANAGED_INPUTS 变化`。

<a id="r-pc130"></a>

## R-PC130. 新增 `__init__.py` 是 license 门禁最常见的漏点；`CI preflight` 红等于全 suite 零覆盖（2026-11-21 实测 #2546）

- `license-eye`（`apache/skywalking-eyes`）只按**文件首行**判 Apache-2.0 头，不看包结构。本仓新建 Python 包时最常漏的是
  `__init__.py`：#2546 的 `integrations/codex/memory_source_plugin/__init__.py` 与 `integrations/codex/source_plugin/__init__.py`
  首行直接是 docstring，preflight 日志逐条列出这两个路径后 `exit 1`。
- 判据链：`CI preflight` 红 → `quality` 失败 → `needs.quality.outputs.suites` 为空 → `master.yml` 里 38 个 suite job 全部
  `skipped`（含 `*-host`、`tests (*, e2e)`），接着 `Upgrade release gate` 以 `UPGRADE_SELECTED=true` + `UPGRADE_RESULT=skipped`
  报红。**后两者是级联，不是第二、第三个缺陷**，别分别在两个位置开线程。
- 取证：`gh api repos/<owner>/<repo>/actions/jobs/<job_id>/logs` 后 grep
  `don't have a valid license header`，能直接拿到文件清单；`.licenserc.yaml` 只 ignore `**/*.svg`，新增 PNG/JSON 不受影响，
  但新增 `.py` 一律需要头。
- 修法：把同目录兄弟文件的 13 行 header 补到首行（空行保留在 header 之后）。

**2026-11-23 追加（`tests` 矩阵红 ⇒ `gateway-validation` / `desktop-validation` 整体 skip）**：#2790 改了
`gateway/crates/pc-gateway-app/src/main.rs`，`quality` 也把 `gateway` 组算进去了，但 `gateway-validation` 仍是
`skipped`。原因是它的 `if` 同时要求 `needs.quality.result == 'success'` 与
`contains(fromJSON('["success","skipped"]'), needs.tests.result)`；当轮 `tests (3.14, unit)` 与两个 e2e 分片红
（`test_bub_compose_startup` 60s 超时、`test_extraction_diagnostics`、`test_codex_service_chain`，三例都不在本 PR
改动面）⇒ 新增的 `binary_cli.rs` 与 `--version/--help` 路径零 CI 覆盖。判读顺序：`suites` 里是否含该组 →
`needs.tests.result` → 该 job 的 `if` 表达式；三者都成立才能写"这次 Rust 改动有 CI 覆盖"。这类 red 属 `R15`
不可判定，报告写"需重跑"，不要写成 PR 缺陷。

关键词：`validated_at: 2026-11-21`、`validated_ref: #2546 head 879a4379（run 44881228712 / job 136776749373）`、
`toolchain: apache/skywalking-eyes（CI preflight）`、`applies_to: master`、
`recheck_when: .licenserc.yaml 的 paths/ignore 变化、preflight 换 header 检查器、或 master.yml 的 suite `if` 条件变化`。

<a id="r-pc133"></a>

## R-PC133. Rust 侧 `-D warnings` + 固定工具链：新增 `x % n == 0` 直接让 gateway-validation 红，且 Tests 被 skipped（2026-11-22 实测 #2775）

- gateway CI 固定 `1.95.0`，`cargo clippy --all-targets -- -D warnings`。clippy 1.95 的 `manual_is_multiple_of` 已进入默认组，
  所以 `messages.len() % 2 == 0` 这类旧写法会报 `error: manual implementation of .is_multiple_of()`，改写为
  `is_multiple_of(2)` 或显式 `#[allow]`。
- 关键后果不是"一行 lint"：`gateway-validation / check` 里 Clippy 在 Tests 之前，clippy 一红，同 job 的
  `Tests`、`Install protocol runner dependencies`、`Upstream protocol compatibility suites` 全部 `skipped`
  （#2775 的 step 8–19），聚合 `CI result` 同红 ⇒ 该 PR 的 continuation/前缀续写在 CI 里**零测试覆盖**。
  报告必须写"Tests 被跳过"，不能写成"gateway 测试已通过"或"只有 lint 问题"。
- 判据顺序：`actions/jobs/<id>` 看 step conclusion（别只看 job 名）→ 失败 step 的日志第一条 `error:` → 若为 clippy/format，
  按 `R-PC130` 同样的"门禁级 vs 测试级"分类处理；门禁级红时下游套件的绿/跳过都不算覆盖。
- 反例参照：#2776 的 `gateway-validation / check` 是真跑完的（fmt + clippy + workspace test 都 success），
  同样是 gateway-only PR，却因 Rust 侧唯一差异（无 `% 2`）而绿 ⇒ 这类红是 PR 引入，不要归为基线抖动。

关键词：`validated_at: 2026-11-22`、`validated_ref: #2775 head a3552eda（run 45044681761 / job 137280542571）、#2776 head da38ec86`、
`toolchain: Rust 1.95.0 / clippy manual_is_multiple_of`、`applies_to: master`、
`recheck_when: gateway 固定工具链版本变化、workflow 把 Clippy 移到 Tests 之后、或 clippy lint 组调整`。

<a id="r-pc136"></a>

## R-PC136. gateway 的 protocol/types crate 可在 Windows 跑单测与 clippy；只 archive `gateway/` 会让协议套件假红（2026-11-23 实测 #2792）

- 可用面：`pc-gateway-types` 只依赖 serde/bytes，`pc-gateway-protocol` 再加 uuid/thiserror ⇒ 这两个 crate 在 Windows
  上能编译、跑单测、跑 `clippy --all-targets -- -D warnings`。R-PC126 的「Windows 不能编译 gateway」只对
  `pc-gateway-core` / `pc-gateway-app`（`tokio::net::UnixStream`）成立。
- 前提：`cargo test -p ...` 仍要解析整个 workspace（`pc-gateway-auth` 依赖 `fs2`），`--offline` 会直接
  `no matching package named fs2 found`；联网解析一次后才能离线复用。本机 rustc/cargo 为 1.96 而 CI 固定 1.95，
  clippy 结论要标明版本差异。
- **镜像必须补 `tests/fixtures/`**：`gemini::tests::goose_shared_envelope_vector_and_text_expectation` 按
  `CARGO_MANIFEST_DIR/../../../tests/fixtures/oauth/upstream/provider-vectors.json` 读夹具，只解 `gateway/` 时
  报 `Os { code: 3, kind: NotFound }` ——那是镜像缺文件，不是 PR 缺陷。补该文件后 #2792 为 5 passed + 9 passed。
- `rustfmt --edition 2021 --check <单文件>` 不需要构建或解析依赖，可用来判 `cargo fmt --check` 门禁（#2792 全绿）。

关键词：`validated_at: 2026-11-23`、`validated_ref: #2792 head 6f7bef9b`、
`toolchain: rustc 1.96.0 / clippy 0.1.96 / rustfmt 1.9.0（CI 固定 1.95.0）`、`applies_to: master`、
`recheck_when: gateway 引入 unix-only 依赖到 types/protocol、Cargo.lock 变化、或 CI 工具链版本调整`。

<a id="r-pc138"></a>

## R-PC138. 门禁级红的两类新形态：`ty` 对 dict 字面量 `**` 展开的推断、license-eye 判不了 `.txt`；install.sh 与 gateway 分发契约（2026-11-24 实测 #2816 / #2811）

- **`ty` + dict 字面量 + `**` 展开**：#2816 的新测试里 `runtime = {"artifact_processing_families": ()}` 被推断成
  `dict[str, tuple[()]]`，随后插入 `int` 值成 `dict[str, int | tuple[()]]`，`RuntimeConfig(**runtime)` 每个字段都是具体类型，
  于是 `Makefile:49 workflow-actions-check` 里一次性报 **83 条** `error[invalid-argument-type]`，全部落在同一行
  （`tests/test_tag_limits.py:47:35`）。修法是逐字段构造或用能让 ty 通过的类型标注；判据仍是 R-PC129/R-PC130 的门禁级红
  （preflight 红 ⇒ 39 个 suite job skipped ⇒ 新增用例零执行），`Upgrade release gate` 是级联。
- **license-eye 判不了 `.txt`**：#2811 新增 `docs/benchmarks/token-savings/steering.txt` 时，日志先打两条
  `WARNING Failed to determine the comment style of file`，最后把它连同 4 个无头的 `.py` 一起列进
  `don't have a valid license header` ⇒ preflight 红。`.txt` 加头会破坏内容语义，正确做法是改可判定风格的扩展名，
  或在 `.licenserc.yaml` 里显式登记该路径。注意 `.licenserc.yaml` 只 ignore `**/*.svg`，新增 `.py`/`.txt` 都会被判。
- **`website/public/install.sh --gateway` 与发布流水线的三处契约**（改 install 脚本必须同时核这三处）：
  ① 资产名 `powercontext-gateway-$VERSION-$TARGET.tar.gz`，与 `.github/workflows/gateway-distribution.yml`
  的 `archive=` 行一致；② `.sha256` 文件格式是 `"{hash}  {name}
"`（`scripts/gateway_distribution.py` 的
  `f"{sha256(archive)}  {archive.name}"`），install 用 `read -r expected name` 解析，两空格会被折叠；③ 身份串
  `pc-gateway {version} ({commit}; {target})` 来自 `gateway/crates/pc-gateway-app/src/main.rs` 的 `--version`，
  install 用 `"pc-gateway $VERSION ("*"; $GATEWAY_TARGET)"` 匹配，`target` 是矩阵里的
  `x86_64|aarch64-unknown-linux-gnu` / `*-apple-darwin`，macOS 门槛与 workflow 的 `MACOSX_DEPLOYMENT_TARGET: '15.0'` 同源。

关键词：`validated_at: 2026-11-24`、`validated_ref: #2816 head e9a21c1760（run 45326786769 / job 138218203821）、#2811 head 615cc3db89（run 45345813464 / job 138279968087）、master 5eb3f92f`、
`toolchain: ty（uv.lock 固定）/ apache/skywalking-eyes`、`applies_to: master`、
`recheck_when: pyproject.toml 的 ty/ruff 配置或 .licenserc.yaml 变化、gateway 分发脚本改名、install.sh 的资产命名或 --version 格式调整`。

<a id="r-pc142"></a>

## R-PC142. `TurnKind::Empty` 与 `RecallPolicy::allows_prepare` 是两套语义：判「某尾部形态会不会丢召回」必须同时读两处（2026-11-26 实测 #2792 head ac477151）

- **判召回是否发生只看两个条件**：`gateway/crates/pc-gateway-core/src/executor.rs` 的
  `RecallPolicy::allows_prepare()` 为 `kind == UserTurn || reprepare`；`reprepare` 只在「复用证明失效后的重试」
  置位，不覆盖新回合的第一次请求。所以任何被判成 `Empty` / `AssistantOnly` / `ToolContinuation` 的请求，
  只要 `ReplayCache` 里没有该 anchor 的条目，就会走 `prepare_skipped()`。
- **`turn_kind` 的分类不等于「是不是续写」**：`pc-gateway-protocol/src/turn.rs` 把尾部 system/developer 判成
  `Empty`，而 `AssistantOnly` 的注释明写「既不是工具续写，也不跳过召回」。两者对同一形态给出相反结论时，
  以 `RecallPolicy` 为准（真正决定召回）。
- **`ReplayCache` 不会自愈**：anchor 由 `replay_cache.rs::message_anchor()` 按「截至最后一条 user 消息」计算；
  `[user, developer]` 有 anchor，但准备从未发生就永远没有条目，同回合重试仍跳过 ⇒ 该回合永久无召回。
  这与「只丢第一次请求」不同，报告里要分开写。
- **两侧路由都要查**：Responses 的 `role:"developer"` item 经入口封装为 `Role::Tool` 承载、
  `responses_item_turn_kind()` 再按 item 自身 role 还原；Chat 的 `to_canonical_chat` 直接映射 `developer → Role::Developer`。
  两条路由的 `[user, developer]` 尾部都落到 `Empty`。
- **`e2e/bub/tests/**` 的执行位置**：`master.yml` 的 `bub-host` 只跑 `tests/e2e/test_bub_service_chain.py`；
  包内用例（含新增的 `e2e/bub/tests/test_bub_prompt_privacy.py`）由 `harness-validation / validate` 的
  `make harness-test`（`uv run --project e2e/bub pytest e2e/bub/tests` 之前还有 `ty check`）执行。
  判「新 bub 用例是否真跑」看该 job 日志里的 `make harness-test` 与 `N passed`（#2820 本轮为 414 passed in 22.08s），
  不要去找 `bub-host`。

关键词：`validated_at: 2026-11-26`、`validated_ref: #2792 head ac477151d16f`、`#2820 head f08ad372714b`、
`applies_to: gateway/ 的召回策略与 e2e/bub 用例执行路径`、
`recheck_when: executor.rs 的 RecallPolicy、replay_cache.rs 的 anchor 计算、turn_kind 的分类表，或 master.yml 的
bub-host / e2e-harness 步骤变化`
