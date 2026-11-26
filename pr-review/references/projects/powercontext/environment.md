<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：平台、工具与环境

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc05"></a>

## R-PC05. 无网络时的本地验证方式（该仓库 TS 插件）

本机沙箱对 `npm registry` 与 `github.com:443`（git over HTTPS 走 127.0.0.1 代理）均不可达，`pnpm install` 无法执行。此时按以下方式仍可获得可执行证据：

1. 用 `gh api repos/oceanbase/powercontext/tarball/<headRefOid>` 取 Head 归档，**用 Python `tarfile` 解压**（`tar -xzf` 对该文件会报 `unexpected end of file`），去掉顶层目录写入 `source/`。
2. 把 `src/`、`extensions/`、`package.json` 复制到 `probes/<case>/`，为其建立两个最小桩：
   - `node_modules/@earendil-works/pi-coding-agent/index.js` → `export function defineTool(spec) { return spec }`
   - `node_modules/typebox/index.js` → `export const Type = new Proxy({}, { get: () => mk() })`（`mk` 返回可无限链式调用的函数）
3. 用 Node 原生类型擦除直接运行 `.ts`（node ≥ 22.18 默认开启，实测 22.22.2 可用），通过 `powercontextPi({ on, registerCommand, registerTool })` 这个公开入口构造 handler，即可复现 `tests/extension.spec.ts` 的场景；`vi.stubEnv` / `vi.stubGlobal` / `vi.spyOn` 可直接用改 `process.env`、改 `globalThis`、替换 `console.warn` 代替。
4. 变异式反证：在 `probes/mutant-run/` 里把 `extensions/powercontext.ts` 的 sink 还原成 `createDiagnosticEmitter((line) => console.warn(line))`，同一探针必须失败，才能证明新回归测试有效。
5. 该结果是**重建探针**，不等同于 `pnpm test`；收尾对账里必须写明未运行项目测试套件、平台差异（Windows vs ubuntu）与未覆盖范围。

关键词：`validated_at: 2026-09-11`、`validated_ref: 7307e8e08fa230cac67743be7db77caa5e44302d`、`toolchain: node 22.22.2（Windows 沙箱）`、`recheck_when: 插件引入除 typebox / pi-coding-agent 之外的运行时依赖，或沙箱恢复依赖安装能力`。

<a id="r-pc09"></a>

## R-PC09. Python 侧的可执行审查方式（裸克隆 + archive + 复用工作区 venv）

要把任意 PR 的 head 跑起来，不需要装依赖，也不需要 checkout 用户开发目录：

1. `git clone --bare --filter=blob:none https://github.com/oceanbase/powercontext.git <镜像>/source/repo.git`（约 5 MB，blob 按需拉取）；
2. `git fetch --no-tags origin refs/pull/<N>/head:refs/pr/<N>`；用 `git merge-base --is-ancestor <base> refs/pr/<N>` 确认 base 关系，`git cat-file -e <sha>^{commit}` 固定对象；
3. 只导出需要的子树，避免全树 checkout：`git archive refs/pr/<N> src tests > tree.tar`，再用 **Python `tarfile`** 解压（`tar -xzf` 对 git archive/base 产物也会偶发报错）；
4. 跑测试时复用用户开发目录的 venv 解释器并让它导入镜像源码：
   `PYTHONPATH=<镜像>/tree/src <repo>/.venv/Scripts/python.exe -m pytest <目标文件> -q -p no:cacheprovider`。
   `PYTHONPATH` 优先于 editable 安装的 `.pth` finder，已验证 `powercontext.__file__` 指向镜像（venv 为 Python 3.14.3，`aiosqlite 0.22.1` / `httpx 0.28.1` / `sqlalchemy 2.0.51`）。
5. **Windows 上能跑的范围**：`builtin/persistence`（SQLite 族）、`builtin/artifacts`、`builtin/runtime` 的纯逻辑与 SQLite 用例都可以直接跑（实测 `test_sqlite_profile.py` 16 passed、回忆权重四文件 100 passed）。`builtin/code` 仍受 R-PC06 的 POSIX 限制。e2e 与 OceanBase/seekdb 用例不在此列。
6. 镜像内探针脚本放 `probes/`，输出重定向到 `evidence/*.out`；探针跑挂时用 `Get-CimInstance Win32_Process | Where-Object CommandLine -like '*probe*'` 收尸（本机 `bash` 内调 PowerShell 会被安全策略拒绝，必须走 PowerShell 工具）。

关键词：`validated_at: 2026-10-09`、`validated_ref: 1140bd71d79ffe6de8cdf4d91f35e9f23ea4bdff`（PR #1782 Head）、`78721714f9b7cf9deee4489d15574bf9bc030c92`（PR #1891 Head）、`toolchain: Windows / Python 3.14.3 / aiosqlite 0.22.1`、`applies_to: 任意 PR 的 Python 侧验证`、`recheck_when: 工作区 .venv 被重建或升级、仓库改为 non-editable 安装、pytest 配置新增 addopts 依赖`。

<a id="r-pc44-01"></a>

## R-PC44. Desktop 只有 Windows（`nsis`）与 macOS 打包形态，平台分支判据是「macOS vs 其余」（已实证）

- **事实**：`desktop/src-tauri/tauri.conf.json` 的 `bundle.targets` 仅 `["nsis"]`；`desktop.yml` 只有 `windows` / `macos` /
  `installed-package` 作业与 `macos` 矩阵，无 Linux 打包作业。`desktop/README.md` 的构建说明覆盖 Windows 与 macOS。
- **Tauri 打包 origin**：Windows / Android 是 `http://tauri.localhost`，macOS（与 Linux）是 `tauri://localhost`。
  因此 `allowed_navigation` 用 `cfg!(target_os = "macos")` 分派（macOS 拿 `tauri://`，其余拿 `http://tauri.localhost`）对**已发布的**平台等价，
  不要因为"Linux 落到 http 分支"判 Finding；Linux 不在此仓打包范围。
- **回归保护要求**：端口/用户信息这类否定条件必须写在**每个**分支表达式内（`… && url.port().is_none()`），并同时保留
  `http://tauri.localhost:8000`（Windows 侧唯一能被端口条件拦住的形态）与 `tauri://localhost:8000` 的负向断言。
  只断言 `tauri://localhost:8000` 在 Windows 上会被 scheme 判断提前拦掉，等于没测端口条件。
- **2026-10-24 更新（PR #2223）**：判据被改成 `cfg!(any(windows, target_os = "android"))` ⇒ `http://tauri.localhost`，其余
  （macOS + **Linux** + iOS）⇒ `tauri://localhost`。逐平台比对：Windows/macOS 行为与旧规则完全相同，**只有 Linux/iOS 变了**；
  而 `tauri.conf.json` 的 `bundle.targets` 仍是 `["nsis"]`、`desktop.yml` 仍无 Linux job ⇒ 该分支在任何 runner 上都不会被断言，
  把判据改回 `cfg!(target_os = "macos")` 也全绿。因此：
  ① 不要因为"Linux 走到 `tauri://`"本身判 Finding（Windows/macOS 无回归）；
  ② 若 PR 宣称修 Linux 打包导航，只能提「`cfg!` 是编译期常量 ⇒ 无法在不跑 Linux 的前提下断言该分支」这一条可执行建议
  （把平台决定提为可传参函数后逐平台断言），不要要求新增 Linux 打包 job 作为合入条件——那超出现有打包范围；
  ③ 记录测试覆盖时按「CI 只有 windows + 2×macos」表述，别把 PR 正文的手工 Ubuntu 冒烟当成门禁证据。
- **2026-10-25 复核（PR #2223 head `9016f57f`，② 的建议已落地）**：`ipc.rs` 现为
  `packaged_origin(target_os: &str) -> Option<(&'static str, &'static str)>`（`"windows" | "android"` ⇒ `http`/`tauri.localhost`，
  `"linux" | "macos" | "ios"` ⇒ `tauri`/`localhost`，其余 `None`）+ `current_target_os()`（仍由 `cfg!` 决定）+
  `packaged_navigation_allowed(url, target_os)`，单元测试对五个目标串逐项断言接受与拒绝。因此**平台分支已被现有
  `desktop.yml` 的 `cargo test`（`windows`、`macos (macos-15)`、`macos (macos-15-intel)` 三 job，均 success）执行到，
  不需要新增 Linux job**；再有人提「该分支在任何 runner 上跑不到」属重复 Finding，应直接引用本条的 CI 证据。
  同一修复的连带事实：未知 target（`current_target_os()` 返回 `"other"`）由「落到 `http://tauri.localhost`」变成
  「拒绝打包源」，但因 `bundle.targets` 仍只有 `["nsis"]`，任何发布产物都不受影响（对应 ① 的边界）。

关键词：`validated_at: 2026-10-25`、`validated_ref: e3070c69c80e4fdebcd15d100b08c06745635cd8`（PR #2188 Head）与
`PR #2223 head 5debe085eb18c062afbea8255349f2f9aed6798a`（`desktop/src-tauri/src/ipc.rs:59-63`、`tests/ipc.rs:115-124`）、
`9016f57ff9b6880f13459670e2d83babd32fb577`（PR #2223 Head，参数化后的三平台 `cargo test` 覆盖）、
`applies_to: desktop 的导航白名单与平台分支判据`、
`recheck_when: `bundle.targets` 增加 Linux 目标、或 `desktop.yml` 新增 linux 打包/测试作业`。

<a id="r-pc64"></a>

## R-PC64. 回复里的「已加进 Windows 专用 job」要按 job 的步骤与事件类型核，而不是按 PR 的 check 名核（2026-10-30 实测）

#2304 的回复声称把两条用例加进 `windows-unit-portability`。核法：

- 步骤是否存在：`grep -n "offline ownership migration" .github/workflows/master.yml`，并确认该步骤
  在 **master** 上不存在（`git show master:.github/workflows/master.yml`）⇒ 属本 PR 新增，不是既有的。
- 步骤跑什么：`windows-unit-portability` 的 `Verify offline ownership migration on Windows` 逐条列出
  两个目标（含参数化用例的全部 id），与本 PR 改动的文件对得上。
- 是否真跑过：该 job 属 `Main` workflow 的矩阵，PR 刚推时 `gh pr checks` 只有 `changes / detect` 与
  少数 job，`tests`、`windows-unit-portability` 要等 `changes` 出结果才出现。此时「本地 exact head 在
  Windows 上跑通 + 变异反证」是可接受的替代证据，但必须在报告里写成「CI 未完成」，不能写成「CI 绿」。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2304 fec062d5`、
`applies_to: 依赖 `windows-unit-portability` / `windows` 这类平台专用 job 作为回归证据的回复`、
`recheck_when: master.yml 的 job 拆分或 changes 过滤逻辑变化`。

<a id="r-pc89"></a>

## R-PC89. `api.d.ts` 是否真的重生成：可在无 pnpm 环境下逐字节重建（2026-11-06 实证 #2270）

`desktop/scripts/generate.mjs` 的 `ui/src/generated/api.d.ts` 输出是
`header + astToString(await openapiTS(normalizeNullableReceiptRefs(contract)))`，**没有 prettier、没有 banner 处理**；
`header` = `generate.mjs` 自身文件头（`gen.split(" */")[0] + " */\n\n"`） + `// Generated from openapi/powercontext.yaml. Do not edit.\n`。
`contractSha256` = `sha256(openapi/powercontext.yaml 原文，仅把 CRLF 归一化为 LF)`，可直接用 Python 复算。

- 本机 `pnpm --dir desktop install` 会因 `packageManager: pnpm@11.13.1` 的原生二进制缺失而失败，但 **npm 通道可用**：
  在 `probes/` 下 `npm install --silent openapi-typescript@<generate.mjs 依赖的版本> yaml`，再用 `node` 跑一个
  复刻 `normalizeNullableReceiptRefs` 的最小脚本，即可得到与 CI `pnpm generate:check` 等价的比较。
  #2270 head `8464c739` 实测：重建 444986 B 与提交件**逐字节相等**，path 键 145 条与 openapi 145 条一致，
  含 4 个新 operation；同 head 的 `desktop-validation / linux|windows|macos×2` 均 success。
- 判「修好了手改摘要」只需要这一个等式；**不要**用「path 出现次数」「operations 数量变化」代替，两者在只改摘要时都不会动。
- 与 R-PC61/R-PC62/R-PC87 的关系：这三条判资格记录与锚点，本条判**生成物本体**是否由生成器产出。

关键词：`validated_at: 2026-11-06`、`validated_ref: #2270 head 8464c739（`desktop/ui/src/generated/api.d.ts`、`openapi/powercontext.yaml`）`、
`toolchain: node 22.22.2 / npm 10.9.7 / openapi-typescript 7.13.0`、
`applies_to: 任何改动 `openapi/powercontext.yaml` 或 `desktop/ui/src/generated/*` 的 PR`、
`recheck_when: `desktop/scripts/generate.mjs` 的 `outputs`、header 拼装或 `normalizeNullableReceiptRefs` 变化，或 openapi-typescript 版本变化`。

<a id="r-pc91"></a>

## R-PC91. 新增的回归步骤要放在「能让它失败的路径所命中的 suite」里（2026-11-06 实测 #2517）

`.github/ci-paths.toml` 的 `[checks]` 把 suite 映射到 job，`scripts/ci_changes.py` 只在对应 suite 为 true 时
调度该 job。把校验步骤放进错的 job，CI 全绿也说明不了它跑过。

- 实测 #2517：为上一轮 P1（适配层导入依赖了未发布的 core 符号）新增的
  `Verify standalone LangChain adapter with released core` 落在 `isolated-installations`，
  而该 job 只由 `packaging` suite 选中；`packaging` 的 patterns 不含 `integrations/langchain/**`
  （只有 `integrations/langchain/pyproject.toml` 在 `full` 里）。所以「只改 `middleware.py`」这类 PR 不会跑它，
  恰好漏掉它要防的形态。
- 判据：改动一行 `pyproject.toml` 会让 `full` 触发全部 suite，因此必须分别看「改 pyproject」与「只改源码」
  两条路径的 `select_suites()` 结果，不能只看本 PR 的 CI 是否绿。
- 同类缺口还有：新增用例用 `pytest.importorskip(<未声明依赖>)`，该依赖不在任何依赖组里 ⇒ 整份文件静默 skip
  （实测 #2517 的 `langfuse`；全仓仅测试文件出现该名字）。判据：`git grep -l <pkg>` 只命中测试文件即为信号。

关键词：`validated_at: 2026-11-06`、`validated_ref: #2517 head a408ddec`、
`applies_to: 任何新增 CI 步骤或新增 `importorskip` 用例的 PR`、
`recheck_when: `.github/ci-paths.toml` 的 `packaging`/`full` patterns 或 `tests` 依赖组变化`。

<a id="r-pc97"></a>

## R-PC97. 网关 Rust 代码的行为证据归属：`gateway-validation / check` 跑 `cargo test --workspace`，Python e2e 作业自带 cargo，但本机 Windows 跑 loopback 用例会误报（2026-11-07 实测 #2506/#2523）

- **Rust 行为证据的唯一常规通道**是 `gateway-validation / check`（`.github/workflows/gateway.yml`，ubuntu-latest，
  `cargo fmt --all --check` + `cargo clippy --all-targets -D warnings` + `cargo test --locked --workspace`）。
  它由 `[suites].gateway = ["gateway/**", ".github/workflows/gateway.yml"]` 选中；只改 `tests/**` 不触发。
  之前记录里把它当"网关全绿"即可，不必在宿主机重跑 cargo workspace。
- **Python e2e 作业可以跑 Rust**：`tests (x, e2e)` 的 PATH 已含 `/home/runner/.cargo/bin`（job 128297453344 日志可见），
  所以 `tests/e2e/test_gateway_authentication.py` 里 `shutil.which("cargo")` 为 None 的静默 skip 分支在 CI **不成立**；
  该文件通过 `pytest.skip` 只在缺工具链时兜底，判定"这条用例有没有真跑"要看该作业整体结论，不能用"没装 Rust"推定 skip。
- **本机 Windows 反例（重要，避免误报 PR）**：`cargo test -p pc-gateway-transport --test buffer_limit_nonstreaming`
  在 head `a1707cde` 与 base `b8b18909` 上**同样失败**，两个用例都得到
  `Indeterminate(TimeoutAwaitingResponse)`（期望 `IncompleteResponse(BufferLimitExceeded)` / `Delivered`），
  单文件耗时 10.0s 即固定超时。凡是这台机器上的 loopback 超时类 Rust 集成测试，**必须先跑 base 对照**才能归因。
  纯逻辑 crate（`pc-gateway-protocol`、`pc-gateway-evidence`）在本机可正常执行（30 passed / 0 failed，cargo 1.96.0）。
- 报告口径：本机 transport 失败写"环境 + 基线，base 同样失败"，PR 归因只引用 ubuntu 的 `gateway-validation`。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2506 head a1707cde / base b8b18909、#2523 head 3a75cd53（job 128297453344、128304042737）`、`applies_to: `gateway/**` 与 `tests/e2e/test_gateway_*.py``、`recheck_when: gateway.yml 的测试命令、e2e 作业的 PATH/工具链安装、或新增依赖 UDS/loopback 的用例`。

<a id="r-pc100"></a>

## R-PC100. `migrations/pinned.py::_PinnedConnection` 不是完整 `AsyncConnection`：新代码取 `connection.sync_engine` 会打穿历史迁移路径（2026-11-08 实测 #2498）

- `pinned()` 返回的是 `_PinnedConnection`，只代理 `connection` / `dialect` / `execute` / `exec_driver_sql` / `scalar` /
  `scalars` / `run_sync` / `stream`，**没有 `__getattr__`**。任何按 `AsyncConnection` 写的辅助方法（典型：取
  `sync_engine` / `engine` 做 pool 级缓存键）在历史转换里必然 `AttributeError`。
- 调用链：#2498 在 `oceanbase/atomic_memory_index.py::initialize()` 新增 `_supports_native_fts(connection)` 并在首行取
  `connection.sync_engine.pool`；而 `migrations/historical.py` 的 `HistoricalNativeAtomicIndex(OceanBaseAtomicMemoryIndex)`
  继承该 `initialize`，其 connection 来自 `pinned()` ⇒ `tests/builtin/persistence/test_mysql_migration_runner.py::
  test_historical_memory_upgrades_and_resumes_native_ddl[oceanbase-*]` 三个参数全红（`Recall effort (OceanBase)`，
  job 128534580508，head `775e574f`），即带历史 atomic memory 的 OceanBase 部署升级会在转换阶段中断。
- 判据：改 persistence/index 侧"从连接上取 engine/pool"的代码前，先
  `grep -n "pinned(" src/powercontext/builtin/persistence/migrations`；判 PR 引入还是基线，比较 base 同文件是否已有该属性访问
  （本例 base `74617893` 的该文件无任何 `sync_engine` 引用）。
- 本机最小复现（不需要 OceanBase）：`_PinnedConnection(SimpleNamespace(dialect=None))` 上
  `hasattr(conn, "sync_engine") is False`，属性集恰为上面八个。评论时把它和真实 CI 栈帧并列，比只贴日志更难被反驳。
- 其他包装类同理会踩：新增"按 engine/pool 缓存能力"的逻辑时，缓存键应从 profile/engine 一侧显式传入，而不是从方法入参的
  connection 上反推。

关键词：`validated_at: 2026-11-08`、`validated_ref: #2498 head 775e574f28099adec6c848cf5b63e5ddc7391eb9 / base 74617893`、
`applies_to: `src/powercontext/builtin/persistence/**` 与 `migrations/**``、`recheck_when: pinned.py 增加属性转发或 `__getattr__`、
`initialize()` 的 connection 契约变更、或历史转换退出 `pinned()``。

<a id="r-pc103"></a>

## R-PC103. 本机无法为 `pc-gateway-core` 提供行为证据：Windows 缺 UDS、WSL 缺链接器（2026-11-09 实测 #2451）

- `cargo test -p pc-gateway-core` 在 Windows 宿主上**必然编译失败**：`crates/pc-gateway-core/src/uds_gate_client.rs`
  无条件 `use tokio::net::UnixStream`，Windows 的 tokio 该符号被 `#[cfg(all(unix, ...))]` 裁掉（E0432）。
  即网关 crate 事实上只支持 Unix 目标，本机不要把它当"可本地复跑"的模块。
- WSL 兜底同样不可用：`/mnt/d` 上直接 `cargo test` 报 `the self-contained linker was requested, but it wasn't found`，
  加 `-C link-self-contained=no` 后改为 `collect2: fatal error: cannot find 'ld'`（缺 binutils/lld）。
  因此 Rust 侧行为证据只能引用 exact head 的 `gateway-validation / check`（其 `cargo test --workspace` 会打印
  新单测名，例如 `capture_coverage::tests::shared_capture_coverage_contract ... ok`，可作为"该用例真的执行"的证据）。
- `tests/e2e/` 的 Python 用例在本机可 `--collect-only`（约 16 s 收集完成），但**实跑会挂死**：`tests/e2e/test_capture_coverage.py`
  4 项实跑 900 s 零输出被 timeout（exit 124）。判覆盖时用 `--collect-only` 证明用例在 CI 的 `make e2e-test` 选择集内，
  再用 exact head 的 `tests (3.x, e2e)` 汇总数（如 1477 passed）作为执行证据，不要声称"本地复跑通过"。
- 非 e2e 的集成用例（`tests/integrations/*`、`tests/integration_conformance/*`）在本机可正常跑（同一镜像
  `uv sync --frozen --no-install-project` + `PYTHONPATH=<mirror>/src`），适合承担本轮行为证据。

关键词：`validated_at: 2026-11-09`、`validated_ref: #2451 head 9c5e59ee4f22（run 42393916562）`、
`toolchain: rustc 1.96.0 (Windows) / rustc 1.95.0 (WSL) / Python 3.13（uv 0.11.2）`、
`applies_to: gateway/ 下的 Rust crate 与 tests/e2e 的本地执行`、
`recheck_when: uds_gate_client 增加 cfg 门控、仓库改为跨平台网关、或本机 WSL 补齐 binutils/lld`。

<a id="r-pc119"></a>

## R-PC119. `tests/e2e/plugin_server.py` 只按 POSIX 启动：本机跑插件 e2e 必须走 WSL，且 venv 元数据要与 head 同版本（2026-11-15 实测 #2616）

- 夹具用 `Path(sys.executable).with_name("powercontext")` 拉起 Server：Windows 上真实文件是
  `powercontext.exe`，`subprocess_exec` 找不到路径 ⇒ 报
  `can't open file '...\Scripts\powercontext'`。改走 WSL（本项目 e2e 的 CI 平台就是 ubuntu），
  或在 `probes/` 副本里把该行改为按 `os.name` 择名——后者属平台适配，必须在证据里标注。
- **venv 的 dist-info 版本必须与 head 同源**：复用别轮留下的 venv 时，其 `entry_points.txt` 里的
  `[powercontext.cli]` 仍指向旧模块（如 `code = powercontext.builtin.code.cli:app`，该文件在当前 master 已不存在）
  ⇒ Server 启动即 `RuntimeError: Cannot load CLI command provider 'code': missing module`，
  而 `cli/app.py::_load_command_providers` 只按**已安装** dist-info 的 `requires()` 判角色（见 R-PC65），
  源码侧怎么看都自洽。正确做法：在 `probes/<case>/` 里 `uv sync --locked`（需 `SETUPTOOLS_SCM_PRETEND_VERSION`
  与 workspace 成员），用该 venv 的 `powercontext` 脚本启动，`PYTHONPATH` 指到要验证的 src。
- **插件家族的读授权是两层**：HTTP 层 `server/app.py::_authorize_checks`（按 operation 的
  `AccessRequirement` 解析 `scope.read`）与 `builtin/plugins/host.py` 的四处 `require("scope.read")`。
  实测把 host 层的 `scope.read` 直接 `return`，`tests/e2e/test_plugin_access.py` 仍 2 passed（等价变异，被路由门禁掩盖）；
  把 `authorize()` 里的 `scope.read` 检查跳过才会转红（`assert 200 == 403`，跨 Scope 家族列表）。
  ⇒ 判「读授权 e2e 有没有回归保护」的变异点必须选 HTTP 层，否则会误判用例无效。

关键词：`validated_at: 2026-11-15`、`validated_ref: #2616 head 6d847297（test_plugin_access.py blob 58a41233、
host.py 984bcac8、app.py f87ca5ff）`、`toolchain: WSL Ubuntu / Python 3.13.11 / uv sync --locked`、
`applies_to: 改动 src/powercontext/builtin/plugins/、src/powercontext/server/plugins.py、tests/e2e/test_plugin*.py 的 PR`、
`recheck_when: plugin_server.py 的启动方式改变、访问控制从 server/app.py 下移到 host、或 CI 改跑 windows 的 e2e`。

<a id="r-pc120"></a>

## R-PC120. embedding profile 切换的「journal transition」机制：OceanBase 目前没有记录路径（2026-11-16 实测 #2615）

- `MigrationBundle` 把 `ServerVectorProfile.checksum` 混进**每个** revision 的 checksum
  （`migrations/bundle.py`，`inputs["server_vector_profile"]`）。切换 embedding profile 后，
  `server_bundle(embedding_profile=old)` 与 `(new)` 的 `checksums` 会有 12/12 个 revision 不同（#2615 实测）。
- 因此维护日志 `maintenance.json` 的 `release_checksums` 必须与「记录时的 profile」配对校验：
  `migrations/profile_transitions.py::verify_embedding_profile_evidence` 在没有 transition 时退回
  `verify_release_checksums(recorded, 当前 profile checksums)` ⇒ 直接 `checksum_conflict`。
  `MySQLMigrationRunner._inspect`（`plan`/`verify`/`apply` 都走它）与 SQLite 的 `plan` 都会撞上这条。
- **判「切换后能不能用」不要只看 startup**：OceanBase 的 `prepare_server_storage` 分支只做
  `check_server_layout` + `check_server_schema`，**不**校验 release checksums；红会推迟到下一次
  `powercontext server db-migrate plan|verify|apply`（或 atomic-projection / processing 维护、升级验收）。
- `begin_embedding_profile_transition(previous)` 的 `previous` 取自**当前 declared storage profile**，
  激活成功后它就等于 target ⇒ `accept_embedding_profile_switch(previous=target, target=target)` 返回空链，
  **事后无法补记**。所以「激活前有没有写 journal」是唯一机会。
- #2615 head `9275f2cc` 的 `server/cli.py` 只在 `SQLiteConfig` / `SeekDBConfig` 下构造 runner
  （`if not dry_run and isinstance(database, (SQLiteConfig, SeekDBConfig))`，`else None`），OceanBase 落到
  `journal is None`，两处保护（缺 journal 即拒绝、写 pending transition）整体跳过 ⇒ OceanBase 上 apply 退出 0 但日志永久不可验证。
- 复算工具：`server_bundle(embedding_profile=...)` 直接算两套 `checksums` 比对，不需要 checkout，也不需要数据库；
  探针见 `D:/test/github/review/oceanbase-powercontext-pr-2615/probes/probe_journal_gap.py`。

关键词：`validated_at: 2026-11-16`、`validated_ref: #2615 head 9275f2cc（profile_transitions.py blob a930e9f1、bundle.py 153-155、cli.py 690-716）`、
`applies_to: 改动 embedding profile / vector 声明 / 维护日志校验的 PR`、
`recheck_when: 维护日志结构或 checksum 组成变化、topic-memory-reindex 的 runner 构造条件变化、profile_transitions 被并入其他模块`。
