<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：审查、契约与公共行为

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc01"></a>

## R-PC01. 仓库与集成布局

- 主干 Python 包：`src/powercontext/`，测试 `tests/` 与 `tests/e2e/`，OpenAPI 契约 `openapi/powercontext.yaml`（生成物 `src/powercontext/http/_generated/` 禁止手改）。
- 多宿主集成各自独立成包，**互不共享代码**，改一个宿主的插件不影响其他宿主：
  - `integrations/pi/plugins/powercontext`（TypeScript + pnpm，本文主要涉及）
  - `integrations/dsh/plugins/powercontext`
  - `integrations/opencode/plugins/powercontext`
  - `integrations/openclaw/plugins/memory-powercontext`
- 各 TS 插件自带 `pnpm-workspace.yaml` / `pnpm-lock.yaml` / `package.json`，可单独安装与测试，无需整仓依赖。
- `AGENTS.md` 是 Python 侧规则；`integrations/` 下没有子级 `AGENTS.md`，TS 插件沿用各自 README 与仓库 CI。
- 用户可见集成文档在 `docs/en/docs/integrations/<host>.md` 与 `docs/zh/...`，含逐条 `POWERCONTEXT_*` 环境变量表。改动插件的环境变量或默认行为时，两处表格都要同步，仅改插件 README 不够。

<a id="r-pc06"></a>

## R-PC06. native code 模块（`src/powercontext/builtin/code/`）

- 入口：`CodeService`（`service.py`）→ `capture` / `extract` / `resolve(_polyglot)` / `store`(SQLite) 或 `seekdb` / `query` / `cache`；`CodeApplication` 是 Runtime facade；CLI entry point `powercontext code`（`code` extra + `[project.entry-points."powercontext.cli"] code`）。
- **仅 POSIX**：`cache.file_lock()` 里 `import fcntl`，`worker.py` 里 `import resource`。Windows 上任何构建/查询一律 `CodeError("unsupported_code_platform")`。`uv.lock` 中 `tree-sitter*` 五个包**都有 Windows wheel**，所以 `pytest.importorskip("tree_sitter")` 在 Windows 上**不会跳过**，必须用 `sys.platform` 守卫才能避免整片测试失败。文档把「Windows/macOS 未验证」写在 `docs/*/docs/workflows/repository-code.md`。
- **本地验证走 WSL**：该模块不能在 Windows 上跑。可用 `wsl.exe -d Ubuntu -- bash -lc 'cd <副本>; UV_CACHE_DIR=<隔离目录> uv sync --locked --extra code && uv run --locked --extra code python -m pytest <文件> -q'`（实测 3.11–3.14 之外用 3.13.11，`uv sync` 约 70s）。`tests/e2e/test_native_code_seekdb.py` 在默认环境（无 `--extra seekdb`）会正常 skip，不会造成收集错误。
- CI：新增 job `code-seekdb`（ubuntu-latest，3.11/3.14，`make code-seekdb-test`）；`tests` job 只在 ubuntu 上跑，`windows-unit-portability` 只跑 `tests/builtin/runtime/test_artifact_processing.py`，**Windows 侧的 code 测试失败不会被 CI 发现**。
- 审查重点面（本轮已核对无误，可直接复用）：操作级 `AccessRequirement(action="scope.read")` 由 `_add_route` 自动装配；仓库根只来自服务端配置，HTTP 不能传路径；`relative_path()` + 逐组件 `O_NOFOLLOW` 防穿越；`_git()` 固定参数、清空 `GIT_*`、`core.hooksPath=/dev/null`；SQL 全参数化、FTS 词由 `identifier_terms()` 提取后双引号转义。
- **`builtin/code` 用例的双重平台门控（2026-10-21 追加）**：新增的 `tests/builtin/test_code_publication.py` 同时带 `pytest.importorskip("tree_sitter")` 与 `pytestmark = skipif(os.name != "posix")`。tree-sitter 只在 extra `code` 里，而 CI 的 `tests (x, unit)` 走 `uv sync --frozen` 安装 `[dependency-groups].dev`（含 `powercontext[code]`）⇒ ubuntu 上**真跑**；Windows 上恒 skip，本地跑出的 "skipped" 不是证据。此类用例的门禁证据要么用 WSL 镜像 venv（`source/tree/.venv/bin/python -m pytest tests/builtin/test_code_publication.py`，实测 9 passed），要么引用同 head 的 `tests (x, unit)`；seekDB 侧用例属 `make code-seekdb-test`（`code-seekdb` job）而非 unit job。

关键词：`validated_at: 2026-10-21`、`validated_ref: e1abff306494a2dfbbb65a9e2fadfeced466a1c2`（PR #1708 Head，base `6fca8a75`）、`1072176e99b52901e5561875fe3ef7d0e15360e0`（PR #2096 Head，双重门控实证）、`toolchain: WSL Ubuntu / Python 3.13.11 / uv 0.11`、`applies_to: master` 上的 native code 模块、`recheck_when: builtin/code/ 目录重构、换锁机制或去掉 fcntl/resource 依赖、pyproject 的 dev 组去掉 powercontext[code]、或 CI 新增 Windows/macOS 的 code 测试 job`。

<a id="r-pc08"></a>

## R-PC08. `builtin/code/process.py` 批次重试的前进不变式（已实证）

- `_batch()` 的第二个返回值就是 `_monitor()` 的 `current`，语义是「退出时正在解析的文件索引」，**不是**「失败索引」；命名有误导，读代码时容易误判 `failed is None` 的含义。
- `extract_jobs` 第 115 行按 `complete` 过滤 `pending`，第 113-114 行在 `complete` 为空时 `raise CodeError("code_parser_failed")`。因此循环**每轮至少消费 1 个文件**，迭代次数上界 = 文件数，**不存在**「原地重试直到耗尽 build deadline」的路径；`failed is None` 只表示「本批不写失败诊断」，不等于无进展。
- 复现方式（Windows 上可直接跑，`process.py` 的导入链不依赖 `fcntl`）：桩替换 `process._batch`，按场景返回 `(complete, current, reason)` 并记录每轮 `pending`；本轮镜像内脚本为 `probes/loop/probe_progress.py`。
- 该模块真正的缺口是 `_progress()` 未把 `ValueError`（缺 `:` 的行、非整数负载）归一化成 `code_parser_failed`，会由 `service._build()` 兜底成 `code_build_failed`（PR #1708 已在 `process.py:28` 提评论）。
- 通用方法论部分见 `review.md` §8（否定性断言先做桩实证再反转）。

关键词：`validated_at: 2026-09-23`、`validated_ref: e1abff306494a2dfbbb65a9e2fadfeced466a1c2`（PR #1708 Head）、`toolchain: Windows / Python 3.14.3（本地 venv，仅用作解释器）`、`applies_to: master 上 src/powercontext/builtin/code/process.py`、`recheck_when: process.py 的 worker 协议、重试循环或 _batch/_monitor 返回契约变更`。

<a id="r-pc11"></a>

## R-PC11. 缺陷位于 PR 正文（非 Diff 行）时的发布路由

本仓 PR 正文常自带"user-facing changes / codes a model can newly observe / testing"清单，其中的事实错误**无法作为行内评论落到 `Files changed`**。`review.md` R11 既要求 Finding 锚定 Diff 行，又禁止退化为 Conversation 评论，此处的路由是：

- **与既有线程同根因** → 按 R12 在该线程下补充回复（不是第二次提出同一问题）。实例：PR #1883 正文列了 `request_too_large`，在 head `7d16522a` 全仓（`*.ts/*.py/*.md/*.js`）**命中 0 处**，而本 PR 真正发布的 413 码是 `handoff_report_too_large`；该问题同根于线程 `4216321836`（"分支无法命名 Server 真实码"），故回复该线程 → `discussion_r4226655772`。
- **无同根因线程、且没有任何可评论的 Diff 行** → 按 R11 fallback 只记入报告 Summary 并标注"未发布及原因"，不发 Conversation 评论。

配套硬性动作：发布前仍须复检 `headRefOid == reviewedHeadOid`（本次 = `7d16522ae3147638ccef0eeb81feafb0eaa2381c`），发布后按 `review.md` R12 复检 head、线程身份字段与去重状态，核验响应 `body`/`html_url`、确认未重复创建。正文类问题的定级上限按"有明确收益的局部维护问题"处理，措辞须写明**无需改代码**，避免作者误以为要改实现。

关键词：`validated_at: 2026-10-09`、`validated_ref: 7d16522ae3147638ccef0eeb81feafb0eaa2381c`（PR #1883 Head）、`applies_to: master`、`recheck_when: review.md R11/R12 修改、仓库引入 PR 模板校验（如自动核对正文错误码）`。

<a id="r-pc12"></a>

## R-PC12. `CHANGES_REQUESTED` 是独立阻塞项，且本仓无人可旁路（2026-10-09 实证）

回答"某 PR 现在能 merge 吗"时，**必须把批准数与变更请求分开判**，且不能用"补一个 approval"推断变更请求会自动消失。

- **语义**（GitHub 文档《Approving a pull request with required reviews》原文）：`Request changes` 本身**不阻塞合并**，除非 ruleset / 经典分支保护配置了 `require a pull request`；一旦配置，且提出者具备 `admin`/`owner`/`write` 权限，则该 PR **"cannot be merged until the same collaborator submits another review approving"**。⇒ 解除条件是**同一人再次提交批准评审**；别人补 approval 无效，他本人只回 `COMMENTED` 也无效。本仓 ruleset `9930477` 含 `pull_request` 规则，满足前置条件。
- **旁路主体的现状（2026-10-17 复核，已变更）**：ruleset `9930477` 的 `bypass_actors` **不再是空数组**，现为 `[{actor_type: "OrganizationAdmin", bypass_mode: "always", actor_id: null}]`，`updated_at: 2026-10-12T06:39:58+08:00` ⇒ **组织管理员可旁路**。2026-10-09 的旧结论"本仓无人可旁路"（当时 `bypass_actors: []`，`AlexStocks` 权限 admin、批准 1/1 仍 `blocked`）只对该日期前的配置成立，**不得再作为当前判据**。同时 `required_approving_review_count` 已由 1 上调为 **2**。
- 陈述"能不能合"时按以下顺序：① 数实际 approval 是否达 **2**；② 查是否有未解除的 `CHANGES_REQUESTED`；③ 再回答"组织管理员是否愿意旁路"——旁路是治理动作，审查者只给路径与证据，不代为执行。
- **"唯一阻塞"要可证，不能靠排除法口头断言**：先逐项取证其余闸门（本仓常见取值 `required_status_checks` 数量 0、`required_review_thread_resolution: false`、`require_code_owner_review: false`、`required_reviewers: []`、`require_last_push_approval: false`、`draft: false`、`mergeable: true`），再核 `require_extra_approval_for_unattributed_changes: true` 是否触发——判据是 `pulls/<N>/commits` 里 `author.login` 为空的提交数，本仓 2026-10-09 实测 #1873 为 14/14 归属 `Teingi`、未归属 0，故不触发。
- **dismiss 的边界**：`dismissal_restriction.enabled: false` + `allowed_actors: []` ⇒ 未限定可 dismiss 的主体，有写权限即可，且必须填写理由（理由进入 PR 会话）；dismiss 后该评审状态变为普通 comment，阻塞解除，已有 approval 不受影响。这是**治理动作**，审查者只提供路径与证据，不得代为执行。
- **`dismiss_stale_reviews_on_push: false` 的连带含义**：作者推新提交**不会**清除 `CHANGES_REQUESTED`，所以"作者说已修"≠"闸门已开"，两者必须分开表述（#1873 实例：作者已逐条回 "Fixed in c6d3d2e2" 且代码层面经独立核对确已落实，但闸门依旧关闭）。

关键词：`validated_at: 2026-10-17`、`validated_ref: 9c132a53961571fb89adc8e8d19b910bd329521f`（PR #1873 Head 的阻塞实证，历史）、`ruleset 9930477 updated_at 2026-10-12T06:39:58+08:00`（approval=2、bypass_actors=OrganizationAdmin:always 的当前证据）、`applies_to: master 及其上的全部 PR`、`recheck_when: ruleset 9930477 的 pull_request 参数或 bypass_actors 变更、改用经典 branch protection`。

<a id="r-pc15"></a>

## R-PC15. 新增文档里的版本号必须登记到 `scripts/release_version.py`（已实证）

- `REFERENCE_PREFIXES` 是**唯一**的版本同步清单，`--write` 与 `--check` 共用它；没有登记的文件既不会被更新，也不会被 `make version-check` 发现偏差。
- 当前已登记：`openapi/powercontext.yaml`、三份 `README*`、`docs/{en,zh}/docs/get-started/{quickstart,install-and-run}.md`、`integrations/dsh/plugins/powercontext/README.md`。**`docs/{en,zh}/docs/get-started/manual-start.md` 未登记**（PR #2046 合并后在 master `f2808fb4` 上仍如此），两份文档各含 3 处 `1.3.0`（`powercontext[cli,server]==`、`powercontext[client]==`、`--ref powercontext-v`）。
- 审查判据：新增/改名的用户可见安装文档只要出现 `powercontext[...]==X.Y.Z` 或 `powercontext-vX.Y.Z`，就核对该路径是否在 `REFERENCE_PREFIXES` 内；不在即提 Finding（`INSTALL_REFERENCES` 两个前缀已能匹配上述三种写法）。
- 非破坏核对：`python -c "import sys;sys.path.insert(0,'scripts');import release_version as rv;print(sorted(p.relative_to(rv.ROOT).as_posix() for p in rv.planned_updates(rv.ROOT,'9.9.9')))"`，看目标文件是否出现在会重写的集合里。
- 不要因为 `make version-check` 通过就认为版本一致；它只检查已登记文件内部的自我一致性。

关键词：`validated_at: 2026-10-17`、`validated_ref: f2808fb42db909e977dce96d0dd5c113736142c0`（master，PR #2046 合并提交）、`toolchain: -`、`applies_to: master 上的文档与发布脚本`、`recheck_when: REFERENCE_PREFIXES 增删条目、或 release_version.py 改为按目录扫描`。

<a id="r-pc16"></a>

## R-PC16. `e2e/bub` 的跨 Scope 污染判定依赖 Access audit（已实证）

`e2e/bub` 用服务端 Access audit 推断 ON 臂是否"到达了其他 Scope"，审查此类改动必须回到服务端事实，不能只看 harness 侧的集合常量。

- **数据面**：审计事件 = 每条授权决策（`authz/service.py::_record_decision`，http/mcp 请求在一次请求结束时批量落库）。
  `transport` 取值 `http` / `mcp`（内部桥，`app.py::_access_audit_context` 里 `is_internal_bridge()`）/ `server` / `background`，
  只有前两者算 agent 请求。`operation` 就是 OpenAPI `operationId`（MCP 复用同一 id），**另有三处伪 operation**：
  `candidate_permissions`、`review_catalog_change`、`review_candidate_target`，不要在契约里找它们。
- **契约边界**：`POST /v1/access/list-audit` 的 `limit` 上限 **500**（`ListAccessAuditRequest`）；`time_range.start >= end` 服务端直接 400；
  读取需要 `server.admin`；`deployment_id` 与服务器不一致会 400（`authz/profiles.py::validate_action_resource`），
  所以"部署 id 写错"会在预检阶段失败，不会静默变成空审计。
- **"被拒请求不算到达"成立的前提**：组件路由在读取内容**之前**调用 `access.require_all(...)`，因此 denied ⇒ 未返回内容。
  反例边界：`require_scope_content_ready` 在授权通过后另行抛 `artifact_owner_pending`（无 denied 事件），这类请求拿不到内容却仍会计入 reached（保守过报）。
  审查时若作者进一步收窄判定，要求给出对应的审计事实依据。
- **验证方式（镜像内，无需真实服务端）**：`PYTHONPATH=<镜像>/src` 复用工作区 `.venv` 跑
  `probes/run_mirror_pytest.py e2e/bub/tests/test_access_audit.py`（2026-10-18 实测 16 passed）；
  变异反证：把 `reached_another_scope` 里的 `not access.request_rejected` 单行改回 `access.allowed`，
  应当**恰好**两条 rejection 用例转红、其余 14 条仍绿（实测 2 failed / 14 passed）。
- **CI 归属**：`e2e/bub/tests` 由 **`E2E harness` 工作流的 `validate` job**（`make harness-sync` + `make harness-check`）执行，
  含 `ruff check/format`、`ty check --project e2e/bub` 与 `pytest e2e/bub/tests`；
  `master.yml` 的 `tests (x, e2e)` 只跑根 `tests/e2e`，**不含** `e2e/bub`。引用 CI 为证据时必须引用前者。
  本地缺 `harbor`（`uv sync --project e2e/bub` 才装）时 `test_paired.py` 无法收集，此时用该 job 的同 head 日志替代。

关键词：`validated_at: 2026-10-18`、`validated_ref: d1ab2965b8e56aa3df7dfec0fe008136ca3776ed`（PR #2035 Head）、`toolchain: Windows / Python 3.14.3（工作区 .venv）+ ubuntu CI（e2e/bub 项目环境）`、`applies_to: master 上 e2e/bub 的跨 Scope 判定与 Access audit 依赖`、`recheck_when: access_audit.py 的分类集变更、Access audit 契约（transport/operation 语义、limit、time_range、permission）变更、或 e2e-harness.yml 的 validate job 改动`。

<a id="r-pc19"></a>

## R-PC19. MySQL 兼容 DDL 里的用户可控标识符必须按 driver paramstyle 转义 `%`（已实证）

`builtin/persistence/bootstrap.py` 用 `exec_driver_sql` 直接下发 `CREATE DATABASE ... \`<name>\``，而数据库名是用户配置值。

- **命中面**：`bootstrap.py` 的 `creation_statement()` / `ensure_database()` / `require_existing_database()`，或任何把用户可控名称拼进 MySQL 兼容 DDL 的 `exec_driver_sql` 调用。
- **判据**：`validate_database_name()` 只禁反引号、斜杠、反斜杠、点、控制字符与系统库名，**允许 `%`**。SQLAlchemy `exec_driver_sql(statement)` 无参数时以空序列下发，pymysql / aiomysql / asyncmy 的 `mogrify` 在 `args is not None` 时执行 `query % args`，于是语句里的单个 `%` 被当作格式符，抛 `TypeError: not enough arguments for format string`（或缺参数错误），表现为"启动建库失败 / 管理员指引里出现错误语句"。因此凡 `dialect.paramstyle ∈ {format, pyformat}` 且语句含用户可控文本，驱动路径必须先 `%`→`%%`；**错误信息与管理员照抄的语句保留单 `%`**。
- **验证方式（无需真实数据库）**：测试假引擎的 `exec_driver_sql` 内加一行 `statement = statement % ()` 即精确复现驱动语义；变异反证——删掉转义后，恰好含 `%` 的参数化用例转红、普通名用例仍绿（2026-10-18 实测 5 failed / 59 passed，探针 `probes/mutate.py` + `probes/mutant-percent/`）。
- **边界**：本机没有真实 MySQL/OceanBase 实例，真实驱动行为只有假引擎与 e2e 覆盖；引用该结论时说明这一点，不要把假引擎结果当成真实服务端已验证。

关键词：`validated_at: 2026-10-18`、`validated_ref: 2fef5fabe16961bbc1f76d10da6e13ca6242e9ad`（PR #2031 Head）、`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: master 上 builtin/persistence 的 MySQL/OceanBase/seekdb 建库与标识符拼接路径`、`recheck_when: bootstrap.py 改为参数化 DDL、SQLAlchemy 改变 `exec_driver_sql` 的空参数语义、或驱动换用 qmark 风格 paramstyle`。

<a id="r-pc23"></a>

## R-PC23. Server metrics 的两个投影边界：readiness 白名单与 snapshot 异常（已实证）

审查 `src/powercontext/server/metrics.py` 或任何新增指标时，先确认指标取的是哪一份事实，再看失败路径是否真被计数器覆盖。

- **readiness 有两个来源，指标只取其中一个**：`_ServerReadinessProbe._check()` → `runtime.readiness()`（runtime/database/inference.*/`artifact_processing.*`）；而 HTTP 契约 `/health/ready`（`server/app.py::get_readiness`）之后还会合并 `_access_readiness_checks()`，`authentication_provider`/`access_provider` 为 `not_ready` 时改判 `not_ready` 并返回 503。`observe_readiness` 的白名单只含 `database`/`runtime`/`inference.{generation,embedding,rerank,decision}` ⇒ 会出现「endpoint 503 / `readiness_state{state="ready"} 1`」。
- **snapshot 异常落在 try 之外**：`_MetricsEndpoint` 写 `set_processing_families({} if supervisor is None else supervisor.family_status)`，property 在参数求值阶段执行；`_ProcessingMetricsCollector.replace()` 自身防御式实现不会抛 ⇒ `metrics_collection_failures_total` 恒 0，真实失败表现为 `/metrics` 整体 500（与文档「失败时保留上一次 snapshot」相反）。
- **探针**：`oceanbase-powercontext-pr-2025/probes/probe_readiness_metric.py`（enforced + 把 `access.readiness()` 置 False）、`probes/probe_collection_failure.py`（把 `ArtifactProcessingSupervisors.family_status` 换成抛异常的 property；注意 `artifact_processing_families=("memory",)` 需要可重建模型，配 `InferenceConfig(generation_model="test")` 才能在 TestClient 里起 supervisor）。
- **审查判据**：新增 readiness/collection 类指标时，要求作者给出「与 `/health/ready` 同源」或「显式声明不含 access 检查」的取舍，并要求失败路径有「仍返回 200 + 计数 +1」的用例，而不是只覆盖正常渲染路径。

关键词：`validated_at: 2026-10-19`、`validated_ref: 802f5bb2e2e4051c04ff06c121d2868e976a83cb`（PR #2025 Head）、`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: master 上 server/metrics.py 的 readiness 与 processing 投影及 `_MetricsEndpoint` 调用点`、`recheck_when: `_MetricsEndpoint` 改为快照式刷新、`observe_readiness` 改为消费合并后的 checks、或 `set_processing_families` 改签名`。

<a id="r-pc24"></a>

## R-PC24. 删除/重命名 `src/powercontext/cli/` 的模块级入口必须扫两份 e2e 消费者（已实证）

本仓有**两套**独立引用 CLI 模块级函数的 e2e 测试，分属不同 CI job；只改其中一套会让另一套在合并 master 后 AttributeError。

- **两套消费者**：`tests/e2e/`（由 `master.yml` 的 `tests (x, e2e)` 跑）与 `e2e/bub/tests/`（由 **`E2E harness` 工作流的 `validate` job** 跑，命令 `make harness-check`）。同名的 kimi 入口在两处都被调用：`tests/e2e/test_kimi_code_host.py` 与 `e2e/bub/tests/test_harbor_job_config.py`（后者第 872 行 `kimi_setup.install_kimi_plugin(...)`）。
- **实例（PR #2052，head `62f2bacb`）**：`2da90ac2 refactor(cli): unify agent setup through thin native adapters` 删除了 `kimi_code.install_kimi_plugin`，同时改了 `tests/e2e/` 的调用，但漏掉 `e2e/bub` 那份 ⇒ 合并 master 后 `validate` 报 `AttributeError: module 'powercontext.cli.kimi_code' has no attribute 'install_kimi_plugin'`（job 118006128400，2 failed / 269 passed）。
- **判据**：`git grep -n "<symbol>" <head>` 必须覆盖 `src/ integrations/ tests/ e2e/ scripts/ docs/`；只出现在 `tests/` 一份消费者里即为不完整重构。合并 master 后 head 与 master 的差集要重新扫一遍（本地分支删除的符号 + master 新增的调用点是最常见组合）。
- **归属陷阱**：同一 job 在 master 上可能已经因**另一种失败形态**而红（本例 master `e4efb39b` 的 `validate` 是同两个 kimi 用例的 `assert {...} == {...}` 不一致）。判断"本 PR 是否新增断裂"要比对**失败签名**（异常类型/断言位置），不能只看 conclusion；report 时必须写清"修掉本条不会自动让该 job 变绿"。
- **验证方式**：读 `validate` job 日志的 `short test summary info` 段（`gh api repos/.../actions/jobs/<id>/logs`），并把 master 同 job 的日志并排比对；不要用 `pr checks` 的总体状态代替。

关键词：`validated_at: 2026-10-19`、`validated_ref: 62f2bacb1ec2025688daef3031da24bf061b9248`（PR #2052 Head）、`e4efb39bd6b8303a508c83fd5fcde5f99290b785`（base/master，同 job 不同败因）、`toolchain: -`、`applies_to: master 上 src/powercontext/cli 的模块级入口及其 e2e 消费者`、`recheck_when: e2e/bub 迁出 tests/e2e 之外、`make harness-check` 目标变更、或 CLI 入口改为类/包导出`。

<a id="r-pc35"></a>

## R-PC35. 新增 Server 开关：`_BASE_ENVIRONMENT`、`.env.example`、两份 configuration.md 与 provider 前缀白名单必须四向对齐（2026-10-23 实测）

审查任何新增 `InferenceConfig` / `RuntimeConfig` 字段（尤其是"把某个行为切成 auto/disabled"的开关）时，按下面四处逐个核对，缺一即为可评论的 P2。

- **`_BASE_ENVIRONMENT`（`src/powercontext/cli/config.py`）**：`powercontext config init` 写出的 env 集合；新字段通常要在这里登记默认值。
- **`.env.example`（仓库根）**：113 个键的运维模板，由 `tests/test_server.py::test_env_example_loads_server_settings` 解析。它**不是**由 `_BASE_ENVIRONMENT` 生成（另有 `.github/workflows/build-artifacts.yml` 生成的 `powercontext.env.example`），必须手工同步。判据：把两边键集求差，正常情况下 `_BASE_ENVIRONMENT - .env.example` 应为空；PR #2202 的 `GENERATION_STREAMING` 与 `GENERATION_STREAM_IDLE_TIMEOUT_SECONDS` 是当时唯一的两个缺口。
- **两份 `docs/{en,zh}/docs/operate/configuration.md`**：表格行要同批出现，默认值与环境变量名的 JSON 形态（`Literal["auto","disabled"]`）一致。
- **行为白名单而非"兼容性"措辞**：`_open_pydantic_ai_model` 的 `auto` 分支按 `model_name.split(":", 1)[0] in _STREAMING_AGGREGATED_PROVIDERS` 精确匹配（当时为 `{anthropic, openai, openai-chat, openai-responses}`）。文档写"OpenAI-compatible"会覆盖到未列入的前缀（`openrouter:` 在 `_MODEL_ENVIRONMENT_HINTS` 里且 `OpenRouterModel` 继承 `OpenAIChatModel`，流式完全可用），而实现未命中时既不打日志也不报错 ⇒ 开关静默失效、无从诊断。判据：把 `_MODEL_ENVIRONMENT_HINTS` 与包内 `infer_model` 支持的 provider 前缀和该白名单求差，再对照文档措辞。
- **补充判据（2026-11-05 实测 #2435 head `ce0e256f`）**：`_BASE_ENVIRONMENT - .env.example` 求差**看不到**「只出现在 `Settings` 而未进 `_BASE_ENVIRONMENT` 的可选开关」。该 head 新增
  `prefix_extraction_gateway_url` / `_headers` / `_cached_input_ratio`（`builtin/runtime/config.py:331-333`）三个字段，
  两份 `configuration.md` 都已加表行，`.env.example` 却一行没有（该段只到 `..._GENERATION_MODEL_CONTEXT_WINDOW_TOKENS=125000`，
  其后直接是既有 headers 注释示例）。所以第四个控制是 `Settings.model_fields` 的 env 别名集 - `.env.example` 键集，
  而不是 `_BASE_ENVIRONMENT`；「同类可选开关本来就不登记 `_BASE_ENVIRONMENT`」不能当作不登记模板的理由。
- **登记「已修」的验收口径（2026-11-16 实测 #2435 head `67fcfdaa`）**：模板里这些可选开关是**注释行**，而
  `test_env_example_loads_server_settings` 开头就 `if not assignment or assignment.startswith("#"): continue`
  ⇒ 作者回「该测试通过」不构成这三行被覆盖的证据，判「已解决」只能靠 exact head 的文件字节。两个必查点：
  ① `git rev-parse <head>:.env.example` 与下载内容 `git hash-object` 相等，确认读到的就是 head 版本；
  ② `.env.example` 是否在 `git merge-tree --write-tree master refs/pr/<N>` 的冲突列表里——不在列表即自动合并，
  再 `git rev-parse <结果树>:.env.example` 应与 head blob 全等（本次 `3a594ead`），修复才不会在解冲突时丢失。
  同理，`headers` 类开关要回到字段类型确认 secret 处理（本次 `dict[str, SecretStr]`，`repr=False`）。

关键词：`validated_at: 2026-10-23`、`validated_ref: de087fd06da6c2837d38a588ca3879bae33a4b4c`（PR #2202 Head）、`toolchain: pydantic-ai 2.29.0 / Python 3.14.3 工作区 .venv`、`applies_to: Server env 模板、docs 配置表与 `_open_pydantic_ai_model` 的 provider 白名单`、`recheck_when: `_BASE_ENVIRONMENT` 增删键、`.env.example` 改由脚本生成、或 provider 白名单调整`。

<a id="r-pc36"></a>

## R-PC36. 评估 harness 提交的 report 绑定 `code_sha`：merge 上游运行时改动后必须重算或在报告内标注（2026-10-23 实测）

`evaluation/memory/capture_ownership`（以及同类 harness）把度量结果作为**受版本控制的产物**提交：`reports/<run>/report.json` 带 `code_sha` / `lock_sha256` / `harness_sha256` / `config_sha256` / `analysis_sha256`。其 `README.md` 明确规定 lock 绑定 "production and evaluation source file hashes … code commit"，"A changed dataset/code/configuration is rejected before replay"，"do not reuse a reviewed output under a different lock"。

- **命中面**：PR 里既有 `tests/**` 的期望值变更（说明运行时行为变了），又有 `reports/**` 的提交产物；尤其是 `merge upstream/master` 这种把上游运行时改动带进来的提交。
- **判据**：`report.json` 的关键指标（如 `rows[].occupancy.text_carriers`）在 head 上的取值由**当前运行时**决定。可用 CI 反推：`evaluation-tests` 跑 `make evaluation-unit-test`，它显式列出 `evaluation/memory/capture_ownership/tests` 且 `-m "not live"`（同时 `uv sync --extra capture-ownership`），因此 `test_replay.py` 的断言在 CI 里真的执行；该 job 绿 ⇒ head 的取值就是断言里的值。
- **实例（PR #2122，head `f71f6955`）**：merge 解析把 `joined-source-v1` 的 `text_carriers` 从 2 改成 1（master 的证据压缩只保留一份正文，见 R-PC31），CI 绿 ⇒ head 得到 1；但提交的 `reports/qwen-flash-20261020/report.json` 里该 arm 38 行仍全是 2，`code_sha` 仍是 PR 首个提交 `2c21132b` ⇒ 报告在 head 上按自身契约已不可复现，读者会误当当前度量。定级 P2（证据可追溯性，`decision` 由 `critical_candidates` 推出、不由 occupancy 推出，结论不反转）。
- **可复用结论**：`code_sha` 存在不等于产物有效；要看"产出它的运行时"是否等于 head。报告带 `code_sha` 只解决"可追溯到哪个提交"，不解决"是否仍描述当前代码"。

关键词：`validated_at: 2026-10-23`、`validated_ref: f71f6955fd61a85e02dba4b295f40f92f20d281b`（PR #2122 Head）、`2c21132ba5dd1caa986484b8d71e1504f0dca3e2`（report 内 code_sha）、`toolchain: -`、`applies_to: evaluation/**/reports 下受版本控制的度量产物与其 tests 期望值`、`recheck_when: 新增/重跑 harness 报告、tests 期望值随运行时变更、或 Makefile 的 evaluation-unit-test 选择集调整`。

<a id="r-pc37"></a>

## R-PC37. 生命周期边界的 flush 调用预算按 Scope 重置，不按边界累计（2026-10-23 实测）

`integrations/{pi,openclaw}` 两个插件的 checkpoint flush 都写成「外层遍历 pending Scope、内层重试 `flushMaxCalls` 次」，
于是**一个生命周期边界上的总请求数 = pending Scope 数 × flushMaxCalls**，而两份文档把它读作边界级上限。

- **命中面**：`integrations/openclaw/plugins/memory-powercontext/src/lifecycle.ts` 的 `flush()` 与其在 `session_end`
  （遍历 `pendingScopes`）、`gateway_stop`（遍历 `pendingPositions`）、`before_compaction` 的调用点；
  `integrations/pi/plugins/powercontext/src/flush.ts::createPendingSourceFlusher().flushAll()`；
  以及 `docs/{en,zh}/docs/integrations/{openclaw,pi}.md`、`integrations/openclaw/README.md` 中关于 `flushMaxCalls` 的措辞。
- **判据（文档自相矛盾）**：`docs/en/docs/integrations/pi.md` 的 "Pre-compaction checkpoint" 段落写
  "Each lifecycle boundary makes at most `POWERCONTEXT_PI_FLUSH_MAX_CALLS` calls ... Queue waiting, all pending Scopes,
  and retry calls share that boundary budget"，而**同一文件**的环境变量表写 "Maximum flush attempts for one pending Source"；
  `openclaw.md` / README 写 "the plugin makes at most `flushMaxCalls` calls ... within a one-second boundary budget"。
- **实测（真实模块，非重写）**：`probes/budget/probe_flush_budget.mjs` 只桩掉
  `openclaw/plugin-sdk/string-coerce-runtime` 与 PowerContext client，直接调用 `registerPowerContextLifecycle` 注册的 handler：
  `gateway_stop` + 2 个 pending Scope + `flushMaxCalls=1` → **2** 次 `/v1/memory/flush`；`session_end` 同场景同样 2 次；
  1 个 Scope + `flushMaxCalls=2` → 1 次（`acknowledged && !remainingWork` 提前 break）。
- **量级**：上界 `|pending| × flushMaxCalls`；openclaw `MAX_SESSION_SCOPES = 32`、`flushMaxCalls ≤ 16` ⇒ 单边界最多 512 次。
  `createClosingSignal()` 的 1 s 只约束墙钟，不约束请求数，所以「有 1 s 预算」不能用来反驳调用次数超限。
- **跑探针的前置**：插件源码是 ESM + `.js` 后缀指向 `.ts`，Node 类型擦除不会改写后缀 ⇒ 需为每个 `.ts` 生成
  `export * from "./<name>.ts";` 的同名 `.js` 转发文件，并给 `node_modules/openclaw` 写 `exports: {"./plugin-sdk/*": "./plugin-sdk/*.js"}`。
  动态 `import()` 必须用 `pathToFileURL()`，否则 Windows 上报 `ERR_UNSUPPORTED_ESM_URL_SCHEME`（protocol 'd:'）。
- **定级与处理**：Server flush 请求数超配置上限、且文档与实现冲突 ⇒ P2。二选一：把计数提升到边界级（两宿主同改），
  或把三处文档改成 per-Scope 表述；并补一条「两个 pending Scope + `flushMaxCalls=1`」的用例。

关键词：`validated_at: 2026-10-23`、`validated_ref: 4c0dca21a5913f5d2d22524ba600c14a73ab86e1`（PR #2180 Head，merge 上游后）、
`toolchain: Node 22.22.2 / Windows`、`applies_to: integrations/{pi,openclaw} 的 checkpoint flush 预算与相关文档`、
`recheck_when: flush 计数改为跨 Scope 共享、flushMaxCalls 语义改写、或 MAX_SESSION_SCOPES/closing 预算调整`。

<a id="r-pc42"></a>

## R-PC42. 用户显式要求时才提交 `APPROVE`，且必须自带范围与 AI 参与声明（2026-10-23 实测）

`review.md` §0.3 / R11 默认禁止用 Approve / Request Changes 改变正式审查状态，本仓额外注意两点：

- **触发条件**：只有用户明确说"approve / 批准 / 没问题就过"时才可提交 `APPROVED`。**不得**由"无 P0/P1"自行推导；
  存在未解决 P2 也不构成自动否决，但正文必须列出这些非阻断项，且明确写 "non-blocking / do not block merge"，
  避免作者误读为可忽略的阻断项。
- **正文必备要素**：`reviewed head OID`（提交前再核对一次 `headRefOid == reviewedHeadOid`，本次 = `17754f89`）+
  审读范围（文件数 / 增删行 / 覆盖面）+ 阻断结论（"无 P0/P1"要写明判定依据来源，不用"AI 已检查"当证据）+
  非阻断项清单 + **AI usage statement**（模型辅助读 diff 与 CI 日志、由本人账号提交并承担责任、merge 责任仍归人类维护者）。
- **机制**：`gh pr review <n> --approve --body-file <path>`。正文含反引号时**必须**先用 Write 落文件再 `--body-file`，
  否则 bash 命令替换会截损正文。提交后核对 `latestReviews` 里本人状态变 `APPROVED`、`reviewDecision` 由
  `REVIEW_REQUIRED` 变 `APPROVED`、`gh api .../pulls/<n>` 的 `mergeable_state` 由 `blocked` 变 `clean`
  —— 本次 #2056 两处均转绿（`AlexStocks` + `hidb4ai` 两条 APPROVED 满足 ruleset 9930477 的
  `required_approving_review_count: 2`）。

关键词：`validated_at: 2026-10-23`、`validated_ref: 17754f89771f9e1a6e90c7b50b7ff0f20e7f2f3e`（PR #2056 Head）、
`applies_to: 本仓所有 PR 的审批动作`、`recheck_when: ruleset 9930477 的 required_approving_review_count 变更、或 review.md §0.3/R11 修改`。

<a id="r-pc45-01"></a>

## R-PC45. `compatibility.json` 的资格记录是「按 Server commit 追加」的数组，并行 PR 撞 `contractSha256` 时要按双记录冲突处理

- **数据结构**：`desktop/src-tauri/src/connections/compatibility.json` 是**数组**（不是对象，别写 `comp.get('records')`），每条记录含
  `id` / `serverCommit` / `contractSha256` / `artifactSha256` / `operations` / `evidence`；`desktop/scripts/generate.mjs` 从 OpenAPI 生成的
  `transport/operations.json` 提供 `contractSha256` 与 `operations`。数组顺序即「当前记录」的判定依据，新记录一律追加在末尾。
- **现象**：两个并行 PR 可能同时新增资格记录且共用同一个 `contractSha256`（同为某次上游契约快照），但 `id`、`serverCommit`、
  `artifactSha256` 与 `operations` 集合不同（多一条 `get_server_info` 之类的 discovery 操作）。两条都在数组末尾追加 ⇒ 后合入者必冲突；
  手工解冲突时若两条都留，仓库里会同时存在两条「当前记录」，而 `desktop/README.md` / `VALIDATION.md` 等文档各自只认自己那条，
  资格校验的期望值就取决于读哪份文档。
- **判据**：`contractSha256` 相同**不等于**同一条记录可复用——只要有 `serverCommit` 或 `operations` 差异，就必须保留不同 `id`；
  审查单个 PR 时无法从该 PR 内部看出冲突，必须跨 PR 比对同仓当前所有 OPEN PR 对同一文件的追加。
- **处理**：① 在 `compatibility.json` 的追加行上指出冲突与「双当前记录」后果，要求作者说明哪条在另一 PR 合入后胜出、或改写 `id`/合并为一条；
  ② 核对本 PR 记录的 `operations` 与 manifest 的 operations 集合逐项一致、`operationFeatures` 覆盖齐全、`artifactSha256`/`contractSha256`
  与文档述及值一致——这些对得上仍然不够，冲突风险独立存在；③ 不要因为 `files` 里只看到一行新增就判为低风险。

关键词：`validated_at: 2026-10-24`、`validated_ref: PR #2078 head 0e6d53f713283049999ef7a963b2119b68c27e46`（新增 `sqlite-atomic-15fd9ec8-v1`，10 operations）
与 `PR #2212 head b3ec0e462970f0885c935bb5be916fecac5857a0`（新增 `sqlite-atomic-c535d816-v1`，11 operations 含 `get_server_info`），
两者 `contractSha256` 同为 `5878999c…`、`serverCommit` 与 `artifactSha256` 不同、均追加在数组末尾；
`applies_to: desktop 资格化记录与 `transport/operations.json` 生成物`、`recheck_when: `generate.mjs` 改变记录键（如改用 map 按 `contractSha256` 去重）、
或 `compatibility.json` 改为按 `serverCommit` 索引的对象结构`。

<a id="r-pc49"></a>

## R-PC49. third-party action 的 pin 在 `.github/actions/**/action.yml` 里另有一套，dependabot 不管

- **事实**：本仓把 `actions/setup-python` 与 `astral-sh/setup-uv` 同时钉在两个位置——各 workflow 的直连步骤，以及
  复合 action `.github/actions/setup-python-env/action.yml`（setup-python 在 `:26`、setup-uv 在 `:31`）。
  base `31ecdd61` 上 setup-uv 共 8 处 pin（workflow 7 + 复合 action 1），setup-python 共 5 处（workflow 4 + 复合 action 1）。
- **现象**：dependabot 的 bump PR 只改 workflow 里的 7 处 / 4 处，复合 action 保持旧 pin（`# v10.0.0` / 旧 v7 commit）。
  合并后同一 action 在同一 workflow 内出现两个不同 SHA：`master.yml` 的直连步骤是新版，经
  `uses: ./.github/actions/setup-python-env` 的 16 处仍是旧版。
- **影响面**：该复合 action 被 8 个 workflow 调用 27 次，即多数 job 拿不到新版的修复（如 setup-uv v10.3.1 的
  并发缓存上传告警抑制）。
- **门禁抓不到**：`make check` 的 `workflow-actions-check` 走 `scripts/check_workflow_actions.py .github/workflows .github/actions`，
  该脚本只断言 pin 是 40 位 commit（外加 YAML 重复键检查），不校验同一 action 的 SHA 唯一性 ⇒ 旧 pin 合法，`quality` 仍绿。
- **审查动作**：审 bump PR 时不要只读 diff；用 `git grep -c "<owner>/<action>@" <base> -- .github/` 与 diff 覆盖处数对账，
  漏项落在 `.github/actions/**` 就按 P2 提「同 PR 一并更新」，并把调用次数与被漏版本的行为修复写进评论。
  核对 SHA↔tag 时注意 annotated tag 要 `git/tags/<tag 对象 sha>` 再解一层；`pypa/gh-action-pypi-publish` 的
  `release/v1` 是**分支**（`branches/release/v1` 的 head 即 pin 目标），不是 tag。

关键词：`validated_at: 2026-10-26`、`validated_ref: PR #2242 head 7385ca95960e1eef9d8f709aaaa9106f903b8150`、
`PR #2241 head 701d5f62a63b15ffe890d85ba333539ee557615b`、`PR #2239 head fe180855b79731dc96fdf3018fdb5ebad474f208`、
`base 31ecdd61beadb7ac8de5da20998dead9a9e07845`、`applies_to: 本仓所有 third-party action 的 bump PR`、
`recheck_when: `.github/actions/` 增加新的复合 action、dependabot 开始覆盖复合 action、或
`check_workflow_actions.py` 增加一致性断言`。

<a id="r-pc50"></a>

## R-PC50. Atomic Memory 的 `description` 有三条互不相同的语义，动它就是动公开往返契约

- **三条路径（PR #2192 head `46e3a3dd` 实测）**：
  1. 显式写入：`_AtomicMemoryMergeService.prepare_change`（`artifacts/atomic_memory/service.py:328-333`）对
     `change`/`merge` 计划里 `description is None` 的 draft 填 `default_description(text)`（单行、超 200 字符截 199 + 省略号）。
     `AtomicMemoryService.create` / `create_many` 也走这条 merge 计划 ⇒ 调用方提交的内容会被改写；
  2. 模型产出：`AtomicMemoryCandidate.description`（`extraction.py:107`）与
     `AtomicMemoryReconciliationContent.description`（`reconciliation.py:110`）是**无默认值的必填**字段，且
     `extra="forbid"` ⇒ 模型漏字段时在结构化生成器内失败，**不进入**域级 `_invalid(...)`；
  3. 守卫：`_AtomicMemoryMergeService.commit_window`（`service.py:351-355`）对仍为 None 的 draft 抛
     `InvalidMemoryCandidateError("canonical", "description is required for new writes")`，走完 `prepare_change` 后不可达。
- **e2e 断言面（改任一条都会打红 4 个 `tests (x, e2e)` job）**：
  `tests/e2e/test_builtin_runtime.py::test_atomic_memory_create_many_returns_exact_current_records` 断言
  `created.records` 的内容与提交值逐字段相等（description 必须为 None）；
  `tests/e2e/test_atomic_memory_reconciliation_retry.py` 的 3 条断言 `error.operation == "atomic-memory-reconcile"` 与
  `REVISE_RULE in error.detail`，其 `_Provider` 返回的 candidates/content 都不带 description。
- **判据**：看到「新增/必填 description」类改动，先确认它是(a) 只作用于模型候选、还是(b) 也改写显式写入；再确认结构化输出
  必填字段会不会抢在域级校验之前失败（后者决定 `retry_feedback` 是否还带规则文本、`operation` 是否还叫
  `atomic-memory-reconcile`）。两者都用 head 的 e2e 失败签名核对，并与 master 的同名 job 对比排除基线。
- **CI 位置**：这 4 个失败只见于 `tests (3.11/3.12/3.13/3.14, e2e)` 的 `Run end-to-end tests` step，`tests (x, unit)` 是绿的
  ⇒ 只读 unit 结论会漏掉。

关键词：`validated_at: 2026-10-26`、`validated_ref: PR #2192 head 46e3a3dd6b28368c0d8a238140a7e856de26b693`
（run `40260522246`，`4 failed / 1128 passed`）、`master 31ecdd61beadb7ac8de5da20998dead9a9e07845`（同 4 job success）、
`applies_to: Atomic Memory 的 description 列与提取/调和（extraction/reconciliation）输出契约`、
`recheck_when: description 改为可选并在域层派生、`test_atomic_memory_reconciliation_retry.py` 的夹具补齐该字段、
或 `prepare_change`/`commit_window` 的派生与拒绝语义合并`。

<a id="r-pc43-02"></a>

## R-PC43. 发布类 PR（`chore(release): prepare vX.Y.Z`）的对账基线（2026-10-23/26 两次实测）

发布 PR 的 diff 往往只是机械替换，风险集中在三处：**版本引用是否漏改**、**发布说明是否与真实合并集合一致**、**同版本条目的并发写入**。

- **版本引用漏改**：不要靠 grep 猜，直接在被审 head 的镜像里跑
  `python scripts/release_version.py --check`（输出 `Release references match X; …`）并调
  `rv.planned_updates(rv.ROOT, '<ver>')`，返回 0 才说明 `REFERENCE_PREFIXES` 全部命中。补充 grep
  `powercontext-v<旧版>` 与 `==<旧版>`（排除 `website/src/lib/releases.ts` 历史条目、`docs/*/rfcs`、
  `pylibseekdb>=1.4.0.post1` 这类第三方约束与 pnpm/uv 锁文件）确认没有脚本覆盖不到的指令。
- **发布说明对账**：把「上一版 tag → base」之间**全部已合并 PR** 取出来逐条映射到 notes 条目。计数必须用
  `gh pr list --state merged --limit 200 --json mergedAt` 后在本地按 `mergedAt > <tag 时间>` 过滤：
  `--search "merged:>DATE"` 会少返回（实测 86 vs 99），据此写数字会被作者反驳。
- **判断"是否新增"要看上一版 tag 的文档，而不是看本 PR 的 diff**：本次 `db-migrate status/plan/apply/verify`
  + `--backup-confirmed`/`--maintenance-confirmed` 在 `powercontext-v1.4.0` 的
  `docs/*/docs/operate/database-migrations.md` 就已齐备，notes 却写成 1.4.1 新增 ⇒ 误归因。判据：
  `git show "refs/tags/<旧tag>:<path>" | grep <能力关键词>`，命中即旧能力。
- **交叉一致性**：notes 声称的能力要与同 head 的安装/运维文档同调。示例冲突：notes 宣布统一升级流程，
  而 `docs/*/get-started/install-and-run.md` 仍写 `server_ready=false` / "不构成完整生产升级路径"。
- **并发写入**：`website/src/lib/releases.ts` 的 `releases[0]` 是固定插入点，而 `releases.test.ts` 断言
  同一 `version` 只出现一次 ⇒ 任何"自带同一版本条目"的在途 PR（本次 #2168）都会与发布 PR 冲突，
  后合并方测试失败。发现后应在同一线程指出，而不是分开提。
- **不要误判 `serverCommit`**：本仓兼容记录允许指向非 master 的分支提交（`sqlite-atomic-98275dbb-v1`
  的 compare 结果为 `diverged`，`cab054db`/`d9a78567`/`caf2a35a` 才是 master 祖先）⇒ "记录必须指向 master
  提交"是错误判据，不要据此开 Finding。
- **可核验的伪身份细节**：wheel 名 `powercontext-<ver>.dev<N>+g<sha>` 的 `N` 可用
  `git rev-list --count <上一版tag>..<sha>` 复核；`desktop/VALIDATION.md` 里的"N packaged files"可用
  `git ls-tree -r <sha> | grep -E '^src/(powercontext|powercontext_service_bootstrap)/' | grep -v .pyc | wc -l`
  复核。两者吻合说明证据链真实，但不等于 sha256/manifest 已验（要写明未验证）。

关键词：`validated_at: 2026-10-26`、`validated_ref: 80047b999442d3419eb887560ec559d7939fac53`（PR #2245 Head，
`chore(release): prepare v1.4.1`）、`applies_to: 所有 `chore(release): prepare v*` 类 PR`、
`recheck_when: scripts/release_version.py 的 REFERENCE_PREFIXES 变更、website/tests/releases.test.ts 断言调整、
或 releases.ts 插入点结构变化`。

<a id="r-pc44-02"></a>

## R-PC44. 发布 PR 声称"另一 PR 的能力"时，必须跨 PR 对齐（2026-10-26 实测 #2245 ↔ #2168）

发布 PR 常被要求把**尚未合并**的功能写进 notes（发布节奏依赖某个大 PR 先落地）。此时不要停在"能力不在 base 里 ⇒ 误归因"，
要判断"这是有意的依赖声明还是无据吹牛"，并检查依赖落地时需要人工解决的部分。

- **先看正文的依赖声明**：本次 #2245 正文首行写 "Depends on #2168 … Merge #2168 first and retain a single v1.4.1
  website entry"。有这句话时，notes 描述未合并能力**不是**缺陷；缺这句话才是。作者的修订 commit
  （`docs(release): clarify …`）会同时改正文，**复审必须重读 body，不能只读 diff**。
- **用 blob 哈希判定"是否抄自另一 PR"**：`git rev-parse refs/pr/<A>:<path>` 与 `refs/pr/<B>:<path>` 相等即字节相同。
  本次两篇安装页 EN/ZH 与 #2168 完全一致（`be7f2f89` / `255791b5`）⇒ 说明作者是**取用了 #2168 的生成产物**，
  而不是独立重写。顺着这条线去 #2168 找生成器，即可拿到"区段由谁维护"的权威答案。
- **验证生成器/策略文件是否同批存在**：`install-and-run.md` 的 `<!-- upgrade-support:start -->` 区段只被
  #2168 的 `scripts/upgrade_release_gate.py` 解析（`require(len(matches)==1)`，notice 文案在其 `NOTICE` 常量里）。
  逐个 `git cat-file -e refs/pr/<A>:<path>` 确认该文件在**被审 PR** 里是否存在：
  `release/upgrade-support.json`、`scripts/upgrade_release_gate.py`、`scripts/run_upgrade_release_gate.py`、
  `tests/release_upgrades/`、`.github/workflows/upgrade-release.yml`。缺失 ⇒ 文档里的"已检查"是悬空声明，
  但**仅在依赖 PR 未合并时为问题**；用"该分支不可单独发布"表述，不要写成永久缺陷。
- **文档交叉引用要落到节级别**：新写的 `see [Preparing a release](../../development/releasing.md)` 指向的
  节（"Database upgrade support"）由 #2168 添加；用 `git show refs/pr/<A>:docs/en/development/releasing.md | grep -c <节标题>`
  失败即可证明。注意 `docs/<lang>/development/` 会被 `prepareDevelopmentContent` 发布到站点，不是仓库内死链，
  所以 link 校验（`validate-links.ts`）不会报错 —— 这类问题 CI 抓不到，只能人读。
- **合并冲突预判**：两 PR 改同一文件同一 region 且替换文本不同 ⇒ 冲突；替换文本相同 ⇒ 无冲突。
  本次两类都出现：`tests/test_release_version.py` 同删 4 行、替换串不同（本 PR 断言更短）⇒ 冲突且"取短版会弱化断言"；
  `scripts/release_version.py` 改动行相同 ⇒ 可自动合并。**纯文本可合并 ≠ 结果正确**：`releases.ts` 两 PR 各插一条
  `v1.4.1`，`website/tests/releases.test.ts:38` 断言同版本唯一 ⇒ 文本合并成功但 master 上测试失败。
- **建议答复形态**：给出"依赖先落地后，本 PR 的哪几个 hunk 变成 no-op"的清单（本次 3 处：`release_version.py`、
  `test_release_version.py`、两篇安装页），让作者可以反向瘦身；再列需人工决定的唯一一条 notes 归属。
- **已 resolve 的线程不算已修复**：本次上一轮 P1 被作者 resolve 并 `isOutdated=true`（`line` 变 null）。
  `isResolved` 只表示作者处理过，必须按新 head 复核内容。结论是"实质已修复但引入新依赖" ⇒ 不复用已 resolve 线程、
  也不开同文案重复帖，而是在**改写后的同一行新 head** 上开新线程，首句明确承接旧线程 id（本次 r4375168200 承接
  r4374916520），并把"已解决部分"先写清楚再列残余，避免作者误读为全盘否决。

关键词：`validated_at: 2026-10-26`、`validated_ref: 025646d9d1ca8917d4e97fede54fbe879009d82a`（PR #2245 Head，
第二次复审）、`依赖对象: PR #2168 Head eb91c22a`、`applies_to: 发布 PR 依赖未合并功能 PR 的所有情形`、
`recheck_when: #2168 合并（需重核 #2245 是否瘦身、releases.ts 是否只剩一条 v1.4.1）、
upgrade_release_gate.py 的 NOTICE 文案变更、或 releases.test.ts 唯一性断言调整`。

<a id="r-pc45-02"></a>

## R-PC45. "有改动"但 `headRefOid` 没变 = base 前进导致冲突（2026-10-26 实测 #2245 第三次复审）

用户复报"PR 有改动"时，**第一步永远是比对 head**：若 `headRefOid` 与上轮相同而 `mergeable` 从 `MERGEABLE` 变
`CONFLICTING`（`mergeable_state=DIRTY`），说明是 base 推进而非作者提交。此时不要重复审读代码，改为审"合并结果"。

- **`merge-tree` 定位冲突，三方可比定位"谁还活着"**：`git merge-tree --write-tree master head` 直接列出冲突文件；
  再对 PR 的每个变更文件取三方 blob（base / master / head）：
  `m==h` ⇒ 已在 master（该 hunk 是 no-op，应在 rebase 时丢弃）；`m==base` ⇒ PR 仍有效；`m!=base && m!=h` ⇒ 需人工合并。
  本次 #2245：24 文件中 **16 个 no-op**、1 个可自动合并（`release_version.py`，取 master 侧以免丢掉新注册的
  `release/upgrade-support.json`）、7 个冲突。**这个分类表就是最高价值的 review 产出**，比逐行读 diff 有用。
- **squash 合并会让 `--is-ancestor` 误判**：`#2168` 以 `e273457d feat(…)(#2168)` 单提交进 master，
  `git merge-base --is-ancestor refs/pr/2168 refs/heads/master` 返回**假**。判"某 PR 是否已合入"要看
  `git log --oneline master | grep "(#2168)"` 或比较内容 blob，不能用祖先关系。
- **"两侧都改"里最危险的两种**：
  ① 测试被弱化/丢覆盖（本次 `tests/test_release_version.py` 的 PR 侧丢了 `release/upgrade-support.json` 夹具条目、
  断言串更短）⇒ 冲突解决取错侧会静默降级，CI 全绿；
  ② 唯一性断言撞车（`releases.test.ts` 断言同版本条目唯一，两 PR 各插一条 `v1.4.1`）⇒ 文本可合并但 master 上测试失败。
- **不要想当然认为"同键即违规"**：两侧对同一契约摘要 `c12901b8…` 各登记一条兼容记录，看似违反"唯一资格化"，
  但 master 上 `5878999c…` 早已被 `1da99747-v1` 与 `8f10c560-v1` 复用 ⇒ 重复摘要是既有做法，不是缺陷。
  真正的缺陷是**叙述冲突**：README/VALIDATION 各写一次"current contract is qualified by <自己的记录>"。
  判据：先 `git show master:<path> | python -c '统计 contractSha256 重复'`，有先例就别开 Finding。
- **rebase 后要重跑的最小集**：`release_version.py --check`（或 `make version-check`）、`make contract-test`、
  `make release-check`、`pnpm --dir desktop generate:check`、`pytest tests/test_desktop_fixture_qualification.py`。
  同时**在 master 的镜像里先跑一遍**这些检查，确认"master 自洽"——本次 master `e273457d` 通过 69 测试且版本检查为
  "Release references match 1.4.1"，因此可以明确告诉作者"冲突不阻塞发布，release 准备已在 master"。
- **发布 PR 的存废判断**：若依赖 PR 已把整个版本准备做完（openapi 版本、README、安装页、生成物全部就绪），
  原发布 PR 只剩极少数独有内容 ⇒ 建议给出"保留哪两处 / 还是整体关闭"的选择，而不是要求作者硬 rebase 24 个文件。

关键词：`validated_at: 2026-10-26`、`validated_ref: e273457d`（master，含 squash 合并的 #2168）与
`025646d9`（PR #2245 Head）、`applies_to: base 前进导致 PR 变 CONFLICTING 的所有复审`、
`recheck_when: #2245 rebase 完成、或规则改成 rebase-only（届时 no-op hunk 会被自动丢弃，本节仍适用）`。

<a id="r-pc51"></a>

## R-PC51. 动了 persistence 就必须同改 `release/upgrade-support.json`；判红先算 `managed_digest`（2026-10-27 实测）

- **门禁位置**：`make check` → `upgrade-policy-check` → `scripts/upgrade_release_gate.py`，要求
  `release/upgrade-support.json.schema_review.persistence_sha256 == managed_digest(root)`。任何新增/修改
  `src/powercontext/builtin/persistence/**`（含 `migrations/server_resources/**` 的 manifest、schemas、versions）
  都会改变该摘要。
- **一次 GateError 会红一片 job**：#2246 head `71d5b44a` 的 `quality`、`tests (3.11–3.14, unit)`（各 4 条
  `test_repository_baseline_covers_all_three_databases[*]`）、`upgrade-acceptance / Prepare upgrade artifacts and matrix`
  全部是同一签名 `Persistence changed (file set or content; CRLF/LF normalized): update the compatibility review`。
  因此看到多条 unit job 红时先算摘要，不要逐个当独立缺陷。
- **判定方法（不需要跑 CI）**：在 exact head 副本上
  `python -c "import sys;sys.path.insert(0,'scripts');import upgrade_release_gate as g;from pathlib import Path;print(g.managed_digest(Path('.')))"`
  与声明值比对；不相等即 `quality` 必红。`git archive` 出来的树是 LF，可直接与作者在 Linux 上算的值对齐。
- **对照判据**：同日 #2258（base `cdb8da29`）同一批 job 绿 ⇒ 排除基线；#2192 的 `fix27` 同时改了该文件 ⇒ 同仓已有正确做法。
- **锚点选择**：PR 通常不碰 `release/upgrade-support.json`，直接把评论挂在新增 revision 的注册行
  （`migrations/server_resources/manifest.json` 的 `"vX_Y_Z_NNN": [`）即可满足 R11。
- **反向场景（2026-10-28 实测，R39）**：PR **完全没碰** `MANAGED_INPUTS` 也会中同一签名——只要它的 base 早于上游修复。
  判别只需一步：算 **base** 的 `managed_digest` 并与声明值比对，**不相等即基线滞后，与 PR 无关**；此时要求作者 rebase，
  不要在 PR 内找缺陷。实测三例同批：`#2205` base `927bb6ee` → `f0a1d364…` ≠ 声明 `9b67d639…`（同 PR head `dfa6d6a5`
  31 文件全不含 `persistence/`、`server/identity.py`、`server/authz`、`limits.py`）；`#2278` head `57fc4d25` 仅 2 文件却红
  `quality` + 4×`tests (x, unit)` + `upgrade-acceptance`；`#2220` 同签名 2 红。对照：master `aedf7beb` = `99d448c2…` 与声明
  一致、`bad4c0c2` = `9b67d639…` 一致、`refs/pr/2220` = `9b67d639…` 一致 ⇒ 摘要口径本身没坏，是 base 停在修复之前。
  修复来源为 `de435aa3`、`59572c6b`（#2212），在 `927bb6ee` 之后推进。
- **附带签名**：同一批里 `tests (x, e2e)` 的 `tests/e2e/test_owner_recovery_http.py::test_http_creation_and_restart_recover_the_original_owner`
  → `MigrationError: incompatible_schema` 也是这条上游修复的另一面，不要单独当 e2e 缺陷逐条开。
- **revision「改名」也会改摘要（2026-11-04 实测 #2270）**：`managed_digest` 对 `{"相对路径": sha256}` 整体取摘要，
  所以把 `versions/v1_4_1_007_work_ledger.py` + `schemas/{sqlite,mysql}-v1_4_1_007.json` 重命名成 `v1_5_0_002` 同样
  改变摘要，即使没有新增 revision。实测 `20bd4624`（作者称 "Resolved for good"）改了 9 个受管输入、`git show
  --name-only` 里 `release/` 为 0 条 ⇒ 声明值仍是旧 `0577c14e…`，复算 `1b482cd3…`，`load_policy()` 抛
  `GateError`。**文本层同一证据**：`upgrade-support.json` 的 `rationale` 仍写 `v1_4_1_007`（2 次）、`v1_5_0_002` 0 次，
  而 manifest 已无 `v1_4_1_007` ⇒ 该文件确实没跟着改。
- **方法对照（无 checkout 也可做）**：同一复算在 base tip 上必须等于 base 自己的声明值；相等才证明算法/环境没问题。
  没有工作树时直接按 `git ls-tree -r <commit> -- <MANAGED_INPUTS>` + `git cat-file blob` 逐 blob 取
  LF 归一化 sha256 再拼总摘要，与归档树 `read_bytes()` 的结果逐位相同，可交叉验证。
- **`MANAGED_INPUTS` 不止 persistence（2026-11-07 实测 #2516）**：清单是
  `src/powercontext/builtin/persistence`、`builtin/code`、`server/identity.py`、`server/authz`、`limits.py`。
  只改 `server/authz/**`（新增 `AccessAction`/`AccessRole` 等）**同样必须重算** `persistence_sha256`：
  #2516 改动 30 文件、persistence 目录 0 条，声明值从 base 的 `53f1fd23…` 移到 `ebd4962b…`，
  按 manifest 复算 `ebd4962b…` 与声明一致。判据顺序：先确认改动是否落在上述五个路径内，再决定要不要重算，
  不要以「没碰 migrations」为前提跳过。
- 关键词：`validated_at: 2026-11-04`、`validated_ref: #2270 head a8cb90ee / master 63e9665c / 旧值 d9f33be3`、
  `applies_to: 任意重命名或改动 persistence 资源的 PR`、`recheck_when: managed_digest 口径或 MANAGED_INPUTS 变化`。
  `toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: 任意 PR 的 unit/quality/upgrade-acceptance 红`、
  `recheck_when: managed_digest 口径、upgrade-support.json 结构或 MANAGED_INPUTS 集合变化`。

<a id="r-pc54"></a>

## R-PC54. 复算 `managed_digest` 的取数方式；merge result 上的 upgrade-acceptance 红先比对修复提交时间（2026-10-28 实测）

`R-PC51` 要求判红前先算 `managed_digest`，取数方式错会让这一步变成不可用的等待。

- **不要逐 blob 读**：在 `--filter=blob:none` 的裸克隆里对每个受管文件执行 `git cat-file blob <ref>:<path>`，会逐个触发网络取数；
  2026-10-28 对 PR #2246 的 21 文件级复算跑到 4 分钟仍未返回（进程被终止，无输出）。
- **一次打包再本地复算**：
  `git archive <ref> src/powercontext/builtin/persistence src/powercontext/builtin/code src/powercontext/server/identity.py src/powercontext/server/authz src/powercontext/limits.py release/upgrade-support.json scripts/upgrade_release_gate.py scripts/upgrade_release_matrix.py > t.tar`
  （实测 14 s / 4.8 MB）→ Python `tarfile` 解压 → `sys.path.insert(0, '<tree>/scripts'); import upgrade_release_gate as g; g.managed_digest(root)`。
  **必须一并导出 `scripts/upgrade_release_matrix.py`**，否则 import 阶段直接 `ModuleNotFoundError`（该模块在 `upgrade_release_gate` 顶层被导入）。
- **判据**：digest == `release/upgrade-support.json::schema_review.persistence_sha256`。实测 #2246 head `bd6c04b9`
  两侧同为 `3d2cd63941d27bb384bc4aea705c51e300a2b2138e4390eb6e5fdd76974e2da2`，同 head 的
  `upgrade-acceptance / Prepare upgrade artifacts and matrix` = success，可交叉确认。
- **merge result 上的 `upgrade-acceptance` 红要按时间归因**：PR #2189（22 文件，不含 `scripts/`、`release/upgrade-support.json`
  与 persistence）的 `Upgrade release gate` + `upgrade-acceptance / Prepare …` 双红来自 run `40438105189`（`2026-10-27T02:23Z`），
  签名 `tests/test_upgrade_release_gate.py::test_parallel_workers_reject_changed_preparation_inputs[checkout] - DID NOT RAISE GateError`。
  根因是 workflow 导出的 `PC_UPGRADE_SOURCE_SHA` 让 `[checkout]` 只改 `GITHUB_SHA` 无效，由 master `8893b02e`（#2256，`2026-10-27 20:57+08`）
  修掉，**晚于该 run** ⇒ 归为 base 滞后，要求用含该修复的 master 重跑，不在 PR 内找缺陷。
  判据顺序：失败 run 的 `created_at` → 修复提交在 master 的 `%ci` → 二者先后；再看 PR 文件集是否含触发面。

关键词：`validated_at: 2026-10-28`、`validated_ref: #2246 head bd6c04b9 / 9fe2e682、#2189 head 287dfc58、master 27404931`、
`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: `scripts/upgrade_release_gate.py` 的 digest 复算与 `upgrade-acceptance` 红归因`、
`recheck_when: `MANAGED_INPUTS` 集合或 `managed_digest` 口径变化、`upgrade_release_matrix` 不再被 gate 顶层导入、或 #2256 的 fixture 修复被回退`。

<a id="r-pc55"></a>

## R-PC55. head 是 merge commit 时必须复算自动合并树，逐文件核对人工解析改动（2026-10-28 实测）

本仓 PR 习惯用 "Merge branch 'master' into <branch>" 推进 head，冲突解析不进任何单独提交，
`gh pr view --json files` 只给"净差异"，看不出解析被人手改过什么。

- **枚举方法**：`git rev-list --parents -n 1 <head>` 取两个父 → `git merge-tree --write-tree <p1> <p2>` 得自动合并 tree
  → 与 `git rev-parse <head>^{tree}` 比对。不同则 `git diff --stat <clean> <actual>` 列出全部人工改动。
  实测 #2192 head `23c28277` 相对自动合并多删了 2 个文件片段（50 行），#2210 head `753b1a1d` 多改了 20 余个文件
  （含 `release/upgrade-support.json`、`manifest.json`、`v1_4_1_004→005` 改名），都是仅看 diff 无法定位的解析动作。
- **必查两类删除**：① 被删的赋值/变量是否仍被下文引用（#2192 删掉 `started = asyncio.get_running_loop().time()`
  而 `embedding_wait_seconds = ... - started` 仍在 ⇒ 每次 `search()` 抛 `NameError`，exact head 副本
  `tests/e2e/test_recall_embedding_timeout.py` 8 failed，master 同文件 7 passed）；② 被删的用例是否属于刚合入 master 的
  另一 PR（同例被删的 `test_one_budget_bounds_the_embedding_waits_of_a_preparation_across_scopes` 正是 #2231 的护栏）。
- **迁移版本号在解析里被改名时**（本例 004→005）要连带核对：`manifest.json`、`schemas/*.json` 两份、
  `server_sources/1.4.0/manifest.json`、`release/upgrade-support.json` 的 `persistence_sha256` 与 rationale 是否同时改到；
  本仓 `managed_digest` 会在 `quality` 的 `upgrade-policy-check` 上兜住 digest，但兜不住 rationale 与文档。
- **判红先后**：本仓 `make check` 自 #1564 起包含 `upgrade-policy-check`。因此"quality 报 Persistence changed"先算
  该 PR base 的 digest（例：master `927bb6ee` 自身 computed `f0a1d364` ≠ declared `9b67d639`，是 base 已坏，由 #2212 的
  `de435aa3/59572c6b` 修复），再看 head tree 与当前 master 的合并树是否一致；不要直接把该红判给 PR。

关键词：`validated_at: 2026-10-28`、`validated_ref: #2192 head 23c28277、#2210 head 753b1a1d、#1564 head 77efe430`、
`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: head 为 merge commit 的 PR 与 `quality` 的 persistence 红`、
`recheck_when: 仓库改为 rebase 流程，或 `make check` 不再包含 `upgrade-policy-check``。

<a id="r-pc56"></a>

## R-PC56. 提高 prompt 契约版本必须同步重算 pinned evaluation report（2026-10-28 实测）

`evaluation/memory/atomic_extraction/tests/test_manifest.py::test_pinned_reports_match_the_current_dataset_and_prompt_contract`
断言 `manifest.prompts == prompt_run_identities()`，而 `run-manifest.json` 里的两条 prompt 身份由**两处**声明决定：

- `src/powercontext/builtin/artifacts/prompt/builtin.py` 的 `definition_version`（`powercontext.prompt.atomic-memory.extract.vN`）；
- `src/powercontext/builtin/artifacts/atomic_memory/extraction.py` 的 `atomic_memory_extraction_instructions_version()`（`powercontext.atomic-memory.extract.{profile}.vN`）。

实测 #2192 head `ce87f441` 把两者分别提到 `v2` / `v3`，而 `evaluation/memory/atomic_extraction/reports/atomic-extraction-20261019-03/run-manifest.json`
仍是 `v1` + `coding|conversation.v2`，且本 PR 139 个文件不含该目录 ⇒ `tests (3.11|3.12|3.14, unit)` 三个 job 同签名失败
（`test_manifest.py:86` 后接 `make: *** [Makefile:53: unit-test] Error 1`）。master `27404931` 仍是 `v1` + `v2`，与 pinned report 自洽，
因此该红不是基线滞后。

- **判据顺序**：① 比对 `builtin.py` 与 `extraction.py` 的版本字符串（不要只看其中一个）；② 读 pinned report 的 `prompts`；
  ③ 核对 PR 文件集是否含 `evaluation/memory/atomic_extraction/reports/**`；④ 用 master 同名文件确认基线自洽。
- **语义要求**：指令正文或输出 schema 变化（本例新增必填 `description` 与 `DESCRIPTION_RULES`）时，旧报告不再对应 head 的 prompt，
  即便测试通过也不能用其准确率数字作为本 PR 的证据。修法二选一：重跑评测提交新 report，或显式把旧 report 标注为历史版本并补一份与当前身份对齐的报告。
- `tests (*, unit)` 在 ruleset 9930477 里不是 required check，但 `make test` 是 AGENTS.md 声明的仓库门禁 ⇒ 按 §4 仍可定 P1。

- **正向复算配方（2026-11-04 #2359 实测，用于确认「没跑的旧报告」而不是「改了没重跑」）**：不要只读 `run-manifest.json`，
  在 exact head 上重算一遍编译摘要再比对：

```python
from powercontext.builtin.artifacts.prompt.builtin import builtin_prompt_definitions
from powercontext.builtin.artifacts.memory.prompts import MemoryExtractionProfile
d = {x.key: x for x in builtin_prompt_definitions(MemoryExtractionProfile.CODING)}
print(d["atomic_memory.extract"].resolve("scp_x", None).compiled_digest)   # 与 report 的 prompts.*.compiled_digest 比对
```

  同时 `sha256(open(cases/atomic-extraction-vN.json,'rb').read())` 必须等于 report 的 `dataset.manifest_sha256`，
  且 cases 文件的 case_id 集合与上一版逐项相同（允许改一个 case 的措辞，但不允许静默删 case）。
  本轮三个值全部对上（`853d22ab…`、`43e6381c…`、`dc7a06e5…`）⇒ 该项无 Finding，不必要求重跑评测。

关键词：`validated_at: 2026-11-04`、`validated_ref: #2192 head ce87f441、master 27404931（版本漂移反例）；#2359 head 319862a1（摘要全部对上的正例）`、
`toolchain: 正向复算用工作区 .venv（Python 3.14.3）直接调用 PromptDefinition.resolve；反例引用 CI run 40668587726`、
`applies_to: `evaluation/memory/atomic_extraction/` 的 pinned report 与 atomic-memory prompt 版本变更`、
`recheck_when: pinned report 改为按 dataset 自动生成、`prompt_run_identities()` 改口径，或该测试被移出 unit 套件`。

<a id="r-pc60"></a>

## R-PC60. `Acceptance (oceanbase)` 的 40 分钟步预算由 runner 波动主导，不能按新增 DDL 条数外推（2026-10-30 实测）

`R-PC52` 提示新增 revision 的语句数会乘进每个 e2e 用例的 bootstrap，容易被读成"语句多 ⇒ 必然超时"。实测三个 head
跑同一 22 用例选择集（`collected 80 items / 58 deselected / 22 selected`），耗时与语句数**不成正比**：

| PR | head | 本 PR 新增 mysql 语句 | 结果 |
|---|---|---|---|
| #2192 | `27d499e0` | 1 | 22 passed in 2135s（35:35） |
| #2246 | `bd6c04b9` | 10 | 22 passed in 1958s（32:38） |
| #2270 | `1fa2a0c5` | 15 | 19/22 后 40 分钟被杀（run 40915372614） |

- 判据：先取同一步骤在其他 head（或 master）上的历史耗时区间；预算已被基线吃掉 80%+ 时，单次超时按
  环境问题处理并请求重跑，不据此判 PR 引入。单用例 111s → 155s 的差异同样出现在未改 persistence 的 PR 上。
- 反向要求：只有在 base/head 同一 run 的**逐用例**耗时对照都指向新增 DDL 时，才把超时归给语句数。
- **红必须落到 step，不能停在 job 名（2026-10-30 追加）**：`gh api .../actions/jobs/<id>` 取 `steps[]` 后再判定。
  `Atomic Memory clean migration (OceanBase)` 4 秒失败的责任在聚合 job「Require every shard to succeed」，真实失败点是
  shard 1/3 子 job，不能读成迁移本身秒退；`Acceptance (oceanbase)` 的 `Verify OceanBase Atomic Memory, HTTP and archive
  regressions` step 04:34:44→05:14:57 = 40m13s 才是步预算超时（#2246 head `0d78bcb1`，job 123882185452）。
  同一 job 名在不同推送上可分别为 success（39m07s）与 failure（40m13s）⇒ 余量 <5% 时只报告耗时，不重开 P2。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2192 head 27d499e0（job 123401174814）、#2246 head bd6c04b9（job 123329009541）、#2270 head 1fa2a0c5（run 40915372614）、#2246 head 0d78bcb1（jobs 123882185452 / 123890358863 / 123871832368）`、
`toolchain: 引用 exact head CI（ubuntu-latest + OceanBase 容器）`、`applies_to: `e2e-harness.yml` 的 `Acceptance (oceanbase)` 步骤预算与超时归因`、
`recheck_when: 该步骤的 `timeout-minutes` 或用例选择集变更、runner 规格变化`。

<a id="r-pc62"></a>

## R-PC62. 契约摘要前移后，`compatibility.json` 必须同时出现同摘要的资格记录（2026-10-30 实测）

`desktop/src-tauri/tests/session.rs` 的 `bundled_qualification_allows_explicit_scope_browsing` 从
`include_str!("../src/transport/operations.json")` 取 `contractSha256`，再到 `state.compatibility_profiles`
里找 `contract_sha256` 相等的记录，找不到就在 `expect("the shipped preview needs a qualified Server for its current contract")`
处 panic。所以「摘要前移」是**两个动作**：改 `operations.ts`/`operations.json` 的摘要，**并**在
`desktop/src-tauri/src/connections/compatibility.json` 追加一条同摘要记录
（`serverCommit` / `artifactSha256` / `operations` / `evidence`），同时在 `desktop/VALIDATION.md`
加对应的 qualification 小节并改掉 "The current contract has the source-specific qualification …" 指向的 id。

- 实测 #2270 head `cf81c1a8`（R-PC61 那批生成的后续提交，增量只有 `ui/src/generated/api.d.ts` +266）：
  `Desktop contract matches OpenAPI` 已通过，但 `linux`/`windows`/`macos×2` 四个 job 全部换成
  `panicked at tests/session.rs:307:10` 同签名失败（run 40999962235，job 123881806924/123807243/123807209/123807075）。
  本 head `operations.json` 摘要 `c7f00e81…`，`compatibility.json` 14 条记录里无一条匹配（master `bf2ac1fc`
  的 `c12901b8…` 能匹配）⇒ 归因本 PR。
- 同日对照 #2304 head `a4dc0b11`（77 checks 全 success）是正确形态：摘要 `e37820ef…` + 追加
  `sqlite-atomic-15c9d932-v1` 记录（`serverCommit 15c9d932`、`artifactSha256 7c943cb6…`、11 项 operations）+ VALIDATION.md 小节。
- **合并 master 会让摘要变成第三个值（2026-11-02 实测 #2304）**：`0ba2f199`（`merge: sync master into ownership migration`，
  父 `126244e9` 与 `252ecac0`）两个父各自自洽——`f369ea3e` 的 `4aeefdd6…` 命中 `sqlite-atomic-581be595-v1`、
  master `252ecac0` 的 `c9002430…` 命中 `sqlite-atomic-2d782c2a-v1`——合并后却是 `c1bbeb2a…`，36 条记录里一条都不命中。
  原因是本 PR 改的 `openapi/powercontext.yaml` 与 master 的变更合成新契约，摘要因此重算。
  后果不是"四个 desktop job 红"，而是 `make contract-test` 先在 `CI preflight` 里红
  （`tests/test_desktop_contract.py::test_bundled_desktop_contract_has_a_qualified_business_profile`，
  `1 failed, 61 passed`），随后 32 个 job 全部 skipped、`Upgrade release gate` 因 `SCOPE_RESULT: failure` 连带判红，
  该 head 等于零行为测试。⇒ 判据补一步：摘要变更类 PR **每同步一次 master 都要重跑资格**，且
  "两个父都自洽" 不能推出 "合并结果自洽"，必须直接在 head 树上比 `operations.json["contractSha256"]` 与
  `compatibility.json[*]["contractSha256"]`（这里是 head 树本身失败，与 CI 检出哪棵树无关）。
- 判据：`contractSha256` 变更的 PR，必须同时用脚本比对
  `operations.json["contractSha256"] ∈ {c["contractSha256"] for c in compatibility.json}`（本机一条 Python 表达式即可），
  并核对 VALIDATION.md 的 "current contract has …" 句子。只比 `api.d.ts` 逐字节与 `tests/test_desktop_contract.py`
  都会漏掉这一层。
- 与 `R-PC45（compatibility.json 的资格记录）` 的区别：该条判的是**多个并行 PR 共用同一 `contractSha256` 却追加互斥记录**（合并后两条"当前记录"）；
  本条判的是**单 PR 内摘要前移但完全没有记录**。
- **摘要相等不等于 operation 覆盖（2026-10-31 实测 #2220）**：`operations.json` 的 operation 清单由
  `desktop/scripts/generate.mjs` 的 `wanted` 决定，与 `contractSha256`（`openapi/powercontext.yaml` 的字节哈希）
  是两件事。新增一个 operation 可以**不改摘要**，此时上面那条"摘要 ∈ 记录"的比对仍然通过，但
  `discovery.rs::assess` 的 `known = qualification.filter(|q| q.operations.contains(operation))` 落空，
  该 operation 得到 `Unverified(QualificationRequired)`，`supported_operations()` 不含它。
  #2220 head `9e7d8d8d`：bundled 摘要 `37936d78…`，唯一同摘要记录 `sqlite-source-artifact-87b6fae2-v1`
  只列 11 项不含 `get_stats`；四条 `sqlite-stats-*` 含 `get_stats` 但摘要为 `5878999c…`/`3165f114…`/`c12901b8…`，
  因 `session.rs` 要求 `profile.compatibility == c.id && bundled_contract == c.contract_sha256`，永远选不中
  ⇒ 统计面板恒 `unavailable`，IPC `session.rs::snapshot()` 也返回 `CompatibilityUnverified`，而 head 81 checks 全 success。
  判据加一步：`set(operations.json["operations"]) ⊆ set(record["operations"])`，其中 `record` 是摘要相等的那条。
- **CI 绿是自证式的**：`desktop/tests/fixture_qualification.py` 直接读 `operations.json` 合成资格记录
  （摘要与 operation 同源，必然覆盖），经 `#[cfg(feature = "ci-fixtures")]` 注入；`ui/tests/statistics.test.tsx`
  手写 `supportedOperations`。凡断言"面板/命令可用"的用例，都要问一句：它用的资格记录是产品 `compatibility.json`
  里的，还是从被测清单现生成的。

关键词：`validated_at: 2026-11-02`、
`validated_ref: #2220 head 9e7d8d8d、#2270 head cf81c1a8（父 11f4319c）、#2304 head a4dc0b11 / 0ba2f199（合并 master 后摘要变第三值）、master 0b0a1c71 / 1c52626d`、
`toolchain: 引用 exact head CI（run 40999962235）+ 本机 exact head/base 副本 JSON 比对（SQLAlchemy 2.0.51 仅 R-PC62 无关）`、
`applies_to: 修改 openapi/powercontext.yaml、desktop/src-tauri/src/transport/operations.json 或 generate.mjs 的 wanted 清单的 PR`、
`recheck_when: session.rs 的资格用例改名/改判据、compatibility.json 结构变化、generate.mjs 开始生成资格记录、
fixture_qualification.py 改为消费产品 compatibility.json`。

<a id="r-pc63"></a>

## R-PC63. 写进 env 文件的 `POWERCONTEXT_SERVER_DATABASE_URL` 必须用 `Path.as_posix()`（2026-10-30 实测）

`--env-file` 走的是 dotenv 解析，`\` 是转义符。把 `tmp_path / "x.db"` 的原生 Windows 路径直接拼进
`f"...DATABASE_URL=sqlite+aiosqlite:///{tmp_path / 'x.db'}"`，env 解析后变成
`sqlite+aiosqlite:///C:Usersalex...`，CLI 侧报 `sqlite3.OperationalError: unable to open database file`；
在进程内直接构造 `SQLiteConfig(url=...)` 不受影响，因为不经过 dotenv。

- 实测 #2304：head `a4dc0b11` 的 `tests/e2e/test_access_ownership_migration.py` 整文件在 Windows 上
  1 failed / 11 passed；head `fec062d5` 把两处改成 `(tmp_path / 'x.db').as_posix()` 后，同两个文件
  在 Windows 上 34 passed。变异反证：把这两处改回原生路径，同一条命令变 3 failed
  （`test_offline_cli_checks_future_background_principal_before_enforcement` +
  `test_offline_migration_preserves_external_owner_evidence[False|True]`），失败行是 `unable to open database file`。
- 判据的落点要看清：`test_access_ownership_migration.py` 的 env 行写的是 `{database.url}`，
  修复发生在 `SQLiteConfig(...)` 构造处（`as_posix()`），只 grep env 行会误判"没修"。
  反向也要看：同文件其它 `SQLiteConfig(url=f"sqlite+aiosqlite:///{tmp_path / 'x.db'}")`
  用于进程内设置，不是缺陷。
- CI 覆盖：`windows-unit-portability` 只在 `e2e` 跑 ubuntu，本类缺陷不会在 PR 上变红，也不会被
  `tests (3.x, e2e)` 抓到；#2304 已在该 job 里显式加了
  `tests/e2e/test_access_ownership_migration.py::test_offline_cli_checks_future_background_principal_before_enforcement`
  与 `tests/e2e/test_owner_recovery_http.py::test_offline_migration_preserves_external_owner_evidence` 两个目标。
- 基线残留（master `4af95ce2`，非任何在审 PR 引入，只记录不阻断）：
  `tests/test_config_wizard.py:568` 仍是
  `f"...DATABASE_URL=sqlite+aiosqlite:///{tmp_path / 'context.db'}"`。
- **该规则同样管新增测试本身**（2026-11-06 实测 #2270 head `95e1626f`）：
  `tests/test_server_migration_cli.py:32` 把 `Path` 直接插进 env 文件的 URL，Windows 上该文件
  `1 failed`，报的是 `migration_locked`（不是 `unable to open database file`）——同一根因换了症状，
  只按错误文本搜索会漏判。判据仍是「写入 env 文件的 URL 是否 `as_posix()`」：换成
  `database.as_posix()` 后 `plan`+`apply` 返回 0、`pc_schema_revision=v1_5_0_004`、
  `pc_work_items` 存在。该文件不在 `windows-unit-portability` 的步骤清单里，CI 全绿也发现不了。

关键词：`validated_at: 2026-11-06`、`validated_ref: #2304 head a4dc0b11 → fec062d5、#2270 head 95e1626f、master 4af95ce2`、
`toolchain: Windows + 工作区 .venv（Python 3.14.3），PYTHONPATH 指向 exact head 的 src`、
`applies_to: 往 `--env-file` 写 SQLite/OceanBase URL 的 e2e 与 CLI 用例`、
`recheck_when: dotenv 实现或 `--env-file` 解析路径变化、windows-unit-portability 覆盖集合调整`。

<a id="r-pc65"></a>

## R-PC65. `cli/app.py` 的命令注册由 dist-info 的 extras 元数据决定，不是源码（2026-10-30 实测）

`server` / `config` / `setup` / `code` / `service` / `archive` 这些子命令不是 `create_cli()` 里静态注册的，
而是 `_load_command_providers()` 用 `entry_points(group="powercontext.cli")` 动态加载，并用
`_role_available(extra, requires("powercontext"))` 按 extras 声明的依赖逐个核验版本。因此：

- 源码里看得到 `src/powercontext/server/cli.py:app`，不等于运行时会注册 `server` 命令；没装 `[server]` extra
  或 dist-info 缺 `Requires-Dist`，该命令就静默消失（`No such command 'server'.`）。
- 审「新增子命令 / 新入口」类 PR 时，要同时核 `pyproject.toml` 的两个位置：
  `[project.entry-points."powercontext.cli"]` 的条目，与 `[project.optional-dependencies]` 里对应 extra
  的依赖声明；只加 entry point 不加 extra 会被 `available_roles` 挡掉。
- 审 UDS 这类「只有前台 `server run` 支持」的特性时，`_OPTIONAL_COMMAND_ROLES` 的映射也要跟着看：它把
  `powercontext.server.cli:app` 与 `powercontext.service.cli:app` 都绑到 `server` 这个 extra，
  所以「personal service 不支持 UDS」的限制在 CLI 层是三条独立守卫（`service/controller.py` 的
  `preview_definition`、`service/launcher.py` 的端点校验、`ops/` 的 `configuration_transport_unsupported`），
  不是一处。

验证方式（隔离镜像，不装项目）：

```bash
UV_PROJECT_ENVIRONMENT=<venv> uv sync --frozen --no-install-project
# dist-info 需自带 entry_points.txt 与 Requires-Dist: powercontext[server,...]
PYTHONPATH=<mirror>/src <venv>/bin/python -c "from powercontext.cli.app import main; import sys; sys.argv=['pc','--help']; main()"
```

命令表里没有 `server` 就是环境残缺，不要据此判 PR 删了子命令。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2312 head 1e2538d7`、`applies_to: master`、
`toolchain: uv 0.11.32 / Python 3.13（WSL）`、
`recheck_when: `powercontext/cli/app.py` 的 `_load_command_providers` / `_OPTIONAL_COMMAND_ROLES` 变化，
或 `pyproject.toml` 的 extras 与 entry-points 调整`。

<a id="r-pc69"></a>

## R-PC69. 发布说明里的每条能力必须能用 `git ls-tree` 在本 head 上点到（2026-11-02 实测）

`website/src/lib/releases.ts` 是官网稳定版 changelog 的唯一数据源（"Only stable releases belong here"），
而 release-prep PR 为了"一次写完"会把**尚未合并**的 PR 能力写进这一版。判据不是措辞，而是**该 head 的树里有没有那个入口**：

```bash
git --git-dir=<bare> ls-tree -r refs/pr/<N> --name-only | grep -E '^gateway/|migrations/(historical|mysql_compatibility|sqlite_compatibility)\.py'
```

#2395（`chore(release): prepare v1.5.0`，head `53bc5689`）把 "Rust PowerContext Gateway debuts in alpha" 与
"Upgrade supported historical Server databases in place" 写成 1.5.0 既有能力，但 `gateway/` 只存在于 #2307 分支，
`historical.py`/`*_compatibility.py` 只存在于 #2394；两个 PR 均 OPEN。定级 P2（可恢复的文档错误），
影响面是"tag 落地顺序"：tag 早于这两个 PR ⇒ 官网与 GitHub Release 声明不存在的 `/gateway/v1`
与不存在的迁移能力。

同类核对还适用于 `release/upgrade-support.json` 的 `target_version` 与两份 `operate/database-migrations.md`
的链尾：本 head 的 `down_revision` 链必须真的以文档写的那个 revision 结尾（`grep -n '^revision\|^down_revision' versions/*.py`）。

关键词：`validated_at: 2026-11-02`、`validated_ref: #2395 head 53bc5689（base 5c249808）`、
`applies_to: 任何 `chore(release)` / `docs(release)` 类 PR`、
`recheck_when: `website/src/lib/releases.ts` 换数据源、或发布流程改成"tag 后再补 changelog"`。

<a id="r-pc73"></a>

## R-PC73. extras 漏声明只能由「只装目标 extras」的安装用例发现（2026-11-03 实测 #2388）

新增一条顶层 `import` 到 `src/powercontext/server/**` 时，依赖必须落在 `builtin` 或 `server` extra 里，不能只落在
`code`。判据不是静态读 `pyproject.toml`，而是按文档推荐组合真装一遍：

```bash
SETUPTOOLS_SCM_PRETEND_VERSION=1.5.0 uv build --wheel --out-dir evidence/dist   # 在 exact head 的镜像里
uv venv probes/venv
VIRTUAL_ENV=probes/venv uv pip install "evidence/dist/powercontext-1.5.0-py3-none-any.whl[cli,server]"
probes/venv/bin/python -c "import powercontext.server.factory"
probes/venv/bin/powercontext --version
```

2026-11-03 实测 #2388 head `69a82da3`：`psutil` 只在 `extra == 'code'`，而 `server/process_metrics.py:24` 顶层导入、
经 `server/metrics.py:54` 与 `server/factory.py:115` 进入每个 Server 启动路径 ⇒ 上述命令分别报
`ModuleNotFoundError: psutil` 与 `RuntimeError: Cannot load CLI command provider 'server': missing module 'psutil'`
（`cli/app.py` 把 provider 加载包在整棵命令树外，连 `--version`/`setup` 一起失败）。注意 master 的
`psutil` 带 `sys_platform == 'darwin'` 标记、`server/metrics.py` 也不导入它，所以"master 上能跑"不能反证。

为什么 CI 看不见：dev/CI 环境装了全部 extras，任何 `import` 都会成功；`tests/native/test_installation.py` 走的是
从分支造 wheel 再装 `[cli,server]` 的路径，只有当它在**同一 job 里再导入 `powercontext.server.factory`** 时才算覆盖。

- extras 交叉核对表（2026-11-03 实测，改动 extras 时按此表重算）：`server`/`ops` 都只继承 `builtin`，`cli` 只继承
  `builtin`+`client` ⇒ 任何 `server/**`、`cli/**` 新增的顶层导入都不能落在 `code`。
- 修复确认（2026-11-03 复验，head `6e07f281`）：`psutil>=7.2,<8` 已加入 `server` extra（`ops` 经继承获得，三份
  `uv.lock` 同步）。同一探针下 `import psutil, powercontext.server.factory` 与 `powercontext --version` 均通过。
  另可用 AST 扫 `server/**` 顶层导入做闭包核对，比逐个读 pyproject 更快定位下一个同类缺口。

关键词：`validated_at: 2026-11-03`、`validated_ref: #2388 head 69a82da3`、
`applies_to: 修改 pyproject.toml extras 或给 src/powercontext/{server,cli}/** 增加顶层导入的 PR`、
`recheck_when: extras 结构改变、server/ops/cli 的继承关系改变、安装测试增加 extras 组合矩阵`。

<a id="r-pc77"></a>

## R-PC77. 加密准入类修复要单独证明「测试能检出过滤器被删」（2026-11-03 实测 #2429）

#2429 用 `declared_encrypted_fields` 只把 `"encrypted": true` 的参数值记入回执，修掉了「普通参数值取得准入证明」。
但把该过滤改成「所有参数都算声明加密」后，`tests/builtin/runtime/test_context_check_encrypted.py` 仍 18/18 通过：
`test_only_declared_encrypted_arguments_are_receipted` 的请求里没有 `TOOLS`（等价于没有任何声明），
`test_ordinary_tool_arguments_do_not_displace_encrypted_values` 的普通值放在数组里，被 `isinstance(argument, str)`
提前过滤。变异后可用公开路由复现行为差异：release 带 `spawn_agent`（`task_name="helper"` 未声明加密），
把 `"helper"` 当作 `agent_message` 的 `encrypted_content` 重放 ⇒ 未变异 `withhold (encrypted-origin-unverified)`，
变异后 `allow ()`。

判据顺序：①定位承载过滤的函数；②在 `probes/` 副本里删掉过滤条件；③跑目标测试文件（不是单条用例）；
④若仍全绿，用公开路由写一条探针证明行为确实变了。这属于 `R06A` 的关键回归反证，不是"缺测试"级别的意见。

**2026-11-16 复核（同一 head `dfbce7e0`）**：过滤仍在 `encrypted_items.py:155`，作者补的用例在
`test_context_check_encrypted.py:394`（`test_an_undeclared_argument_of_a_declared_tool_proves_nothing`），
exact head 24 passed；同一变异（放宽为 `isinstance(schema, dict)`）仍只打红该用例（`1 failed / 23 passed`，
失败点 `:405 assert 'allow' == 'withhold'`）。但**该修复在合并结果树上不自动成立**：
`git merge-tree --write-tree master head` 的 16 个冲突里有 4 处落在 `runtime/context_check.py`，其中两处正好压住本修复的两侧——
`policy.inspect_json(... admit_encrypted=True)`（PR）对 master 的 `policy.enforcing or phase == "before_send"` 条件，
以及 `granted["encrypted_fields"]`（PR）对 master 的 `granted["endpoint"]`（配套新字段
`ContextCheckResult.target_endpoint/target_protocol`）。解冲突必须四者并存，取任一侧都会丢功能；
`encrypted_items.py` 与测试文件在结果树里与 head blob 全等（`c58cb5e5` / `cb0d4fee`）。

关键词：`validated_at: 2026-11-16`、`validated_ref: #2429 head dfbce7e0（评论 r4453896470；merge-tree 结果树 a5ee0041）、#2429 head 0e350152（probes/probe_declared_filter.py）`、
`applies_to: 改 src/powercontext/builtin/inference/encrypted_items.py 或 runtime/context_check.py 的准入过滤`、
`recheck_when: 声明加密字段的判据改变、或测试改成带 TOOLS 的请求形状`。

<a id="r-pc79"></a>

## R-PC79. macOS DMG 打包步骤是本仓最拥挤的争用点：三个 open PR 同改一段，且「恢复动作」必须自己可失败（2026-11-04 实测）

`.github/workflows/desktop.yml` 的 `macos` job「Build unsigned macOS app and DMG」在 2026-11-04 同时被三个 open PR 修改，
语义互斥，判 merge 时不能只看各自的 `CI result`：

| PR | head | 对该段做的事 | 与其余两个的关系 |
|---|---|---|---|
| #2388 | `a53af9db` | 只加注释 + `include-hidden-files: true`（`50080989`） | 与判据无冲突 |
| #2393 | `ffc80542` | 保留 shell 循环，加 `capture_macos_state`、`retried=true` 输出、`include-hidden-files` | 判据行是 merge-base 旧写法（见下） |
| #2306 | `5f783f29` | **整段删除**，改为 `run: python3 scripts/build_macos.py` | 会连带删掉 #2393 的「恢复后仍上传诊断」能力 |

- **判据来源**：master `2853ed98` = `grep -Eq "hdiutil: (create failed - Resource busy|couldn't eject .* - Resource busy)"`；
  #2393 head 仍是 `grep -Fq 'hdiutil: create failed - Resource busy'`（merge-base `e192e08c` 的旧写法）。
  改用 `-Fq` 后，「eject 时资源占用」这种真实形态不再重试——这正是 #2306 head 上 `macos-15-intel` 红的原因。
- **`desktop/scripts/build_macos.py` 的失败语义（已实证）**：`:55` 的 `subprocess.run([hdiutil,"detach","-force",dev], check=True)`
  在图像仍被占用时返回 16，`CalledProcessError` 从 `main()` 的重试循环逸出 ⇒ attempt 1/3 即退出，后续 attempt 与
  `pnpm tauri bundle` 都不执行。恢复动作必须 `check=False` 后降级为「记录 + 继续下一次 attempt」，或在循环内 try 住。
- **测试判据**：`tests/test_desktop_macos_bundle.py` 的假 `hdiutil` 只断言参数后 `exit 0`，因此 detach 失败分支零覆盖；
  参数化用例的 `busy` 序列只输出 `create failed` 形态，因此判据收窄也不会变红。要求两组用例：detach 返回非 0 仍有后续 attempt、
  `couldn't eject` 形态仍触发重试。
- **`tests/test_desktop_macos_workflow.py`（#2393）的计数口径**：成功时循环 `break`，不会执行 `capture_macos_state`，
  所以 state log 数的期望是 success=0 / busy,success=1 / failure=1 / busy,failure=2 / busy×3=3；复核脚本行为时按这个模型对账，
  别把「成功也写 state log」当成漏写。

关键词：`validated_at: 2026-11-04`、`validated_ref: #2306 head 5f783f29（run 41803592923 job 126498786985、评论 r4466582249）、
#2393 head ffc80542（评论 r4466579605）、#2388 head a53af9db、master 2853ed98`、
`toolchain: GitHub macOS runner（macos-15-intel / macos-15）`、
`applies_to: .github/workflows/desktop.yml 的 macos job 与 desktop/scripts/build_macos.py`、
`recheck_when: 该步骤被任一 PR 合并/改写、`hdiutil` 重试判据再次变动、或 desktop packaging 改为统一脚本`。

<a id="r-pc80"></a>

## R-PC80. `/openapi.json` 不在 `_PUBLIC_PATHS`：CLI 侧的「契约探测」在 enforced 部署上恒 401（2026-11-05 实测 #2495）

`src/powercontext/server/middleware.py:35` 的 `_PUBLIC_PATHS` 只有 `/`、`/docs`、`/health/live`、`/health/ready` 与四条
`/v1/skill/remote/*`；`/openapi.json` 不在其中。装上 `AuthenticationMiddleware` 后匿名请求得 401（实测 `probes/probe_openapi_auth2.py`
输出 `/openapi.json anon=401 auth=200`，`/health/live`、`/health/ready` 均 200；不装中间件的 app 上 anon 也是 200）。

- 判「CLI 探测契约会不会恒 DEGRADED」不能举 `TestClient(app)` 无中间件的结果为证，会把结论判反。要么把
  `AuthenticationMiddleware` 装进 ASGI 栈再试，要么直接读 `_PUBLIC_PATHS` 与该路径对账。
- 本仓已有正确通道：`cli/authorization.py:129 read_stored_authorization(path, *, server_url)`；而
  `cli/system.py:970 _request_json` 只发 `Accept`/`User-Agent`。凡新增 CLI 直连探测，先问「这条路径在不在 `_PUBLIC_PATHS`，
  不在就必须先解析已存凭据」。
- 失败文案同样可评论：把 401 折进 DEGRADED 后提示 "expose the contract at the configured endpoint"，是把认证问题说成部署问题——
  enforced 默认配置下用户没有任何「expose」动作能消除它。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2495 head 42a6d912（评论 r4479124009、probes/probe_openapi_auth.py、probe_openapi_auth2.py）`、
`toolchain: Python 3.14.3 工作区 .venv（httpx + starlette TestClient）`、`applies_to: cli/*.py 里对 Server 的直连探测、middleware.py 的 `_PUBLIC_PATHS``、
`recheck_when: `_PUBLIC_PATHS` 增删 `/openapi.json`、CLI 探测改走已存凭据、或 DEGRADED 文案改写`。

<a id="r-pc81"></a>

## R-PC81. 根级 opaque 豁免必须逐个 key 白名单：`before_release` 没有 `_REQUEST_FIELDS` 这层过滤（2026-11-05 实测 #2486）

`builtin/inference/model_payload.py:225` 是 `contains_opaque_content` 的协议分支：`openai-responses` 时根级 dict 里出现任意
`_OPAQUE_KEYS`（`image`、`image_url`、`audio`、`input_audio`、`video`、`file_data`、`file_id`、`file_url`、`encrypted_content`）
即返回「含不可检内容」⇒ 整个根对象免检、直接 allow。`privacy.py` 在 before_send 与 before_release 两条分支都调它，
但只有 before_send 另有 `set(value) - _REQUEST_FIELDS[protocol]` 的请求字段白名单。

- 新豁免要写成具体 key 集合（本例只该放行 Responses 回显的 `image` 设置对象），不能用 `key in _OPAQUE_KEYS` 整类判断。
- 两条分支各起一条探针：同一 payload 在 `before_release` 与 `before_send` 下结论必须一致；不一致说明豁免只被其中一条路径兜住。
- 嵌套位置要单独试。#2486 head `8b61f73d` 上根级 6 个 key 全部 allow，而 output reasoning 的 `encrypted_content`、
  output part 的 `image`、`image_generation_call`、input item 的 `image_url` 仍 withhold ⇒ 缺口只在根级，不是全链路失效。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2486 head 8b61f73d（评论 r4479123182、probes/probe_root_opaque.py、evidence/probe_root_opaque.{base,head}.txt）`、
`toolchain: Python 3.14.3 工作区 .venv`、`applies_to: model_payload.py 的 `contains_opaque_content` 与 privacy.py 的 admit 分支`、
`recheck_when: `_OPAQUE_KEYS` 增删、before_release 引入请求字段白名单、或 Responses 载荷结构变化`。

<a id="r-pc82"></a>

## R-PC82. 核销「加密回执跨目标复用」：target 绑定是 `sha256([endpoint, protocol])`，对照必须改同一 profile 的 endpoint（2026-11-05 实测 #2429）

head `dfbce7e0`：`context_check.py:181 _target_identity(profile)` 对 `[profile.endpoint, profile.protocol]` 取 sha256，
`:611` 写入回执 claims 的 `target`，`:656` 在 `_presented_proofs` 里 `or claims.get("target") != target: continue`。

- 复现要改**同一 profile 的 endpoint**（`targets["test"].model_copy(update={"endpoint": ...})`）。换成另一个 profile 名会让
  `claims["target_profile"]` 先失配，命中的是旧判据，新绑定根本没被测到。
- 断言成对写：未改配置 `decision == "allow"`，改 endpoint 后 `reason_codes == ("encrypted-origin-unverified",)`。
  只断 withhold 一侧会漏掉「绑定过严把正常重放也拒了」。
- 该身份不含凭据/请求头/模型：同一 endpoint 上轮换密钥不作废回执，这是设计（能解密同一密文的仍是同一上游），不要当遗漏报；
  除非改动让同一 endpoint 真的换了可读者。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2429 head dfbce7e0（回复 r4479142259、tests/builtin/runtime/test_context_check_encrypted.py:247）`、
`toolchain: Python 3.14.3 工作区 .venv（该文件 24 passed）`、`applies_to: runtime/context_check.py 的回执签发与校验`、
`recheck_when: 回执 claims 结构变动、或 `_target_identity` 纳入更多 profile 字段`。

<a id="r-pc84"></a>

## R-PC84. 新增 e2e 用例是否真在 OceanBase 上跑，要按「fixture skip 条件 + OB 作业显式清单」两处对账（2026-11-05 实测 #2498）

`tests/e2e/conftest.py` 的 `migration_backend` 参数是 `("sqlite", "seekdb", "oceanbase")`，后两者分别要
`POWERCONTEXT_TEST_MIGRATION_SEEKDB=1` 和 `POWERCONTEXT_TEST_MIGRATION_OCEANBASE_URL`，否则 `pytest.skip`。
`migration_index()` 在 sqlite 下返回 `SQLiteAtomicMemoryIndex`，**只有** seekdb/oceanbase 才构造
`OceanBaseAtomicMemoryIndex`。所以「某个 e2e 文件测了 OB 路径」这个结论必须两步都成立：

1. 文件确实进了设置该环境变量的作业。这些作业没有全量跑 `tests/e2e`，而是逐个点名：
   `atomic-memory-clean-oceanbase-shards` 的默认清单来自
   `scripts/run_atomic_memory_clean_migration.py:27-29`（migration_evidence / grant_migration / migration_vector），
   其余步骤再点名 long-query（`test_atomic_artifact_search_http.py` + `test_atomic_memory_long_fts_query.py`）、
   scope-search、background-metrics、startup-snapshot；`Recall effort (OceanBase)` 也是固定文件 + `-k oceanbase`。
2. 文件在 head 上被某处引用：`git grep -ln <文件名> refs/pr/<N>` 应为非空。

只看 master 的 e2e 套件会得出相反结论：那里没有 OB URL，两个参数直接 skip，实际只跑 SQLite。
mock 单测（`_Connection`/`_Result` 返回固定行）只能证明路由分支，不证明 SQL 可执行。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2498 head c3f730ef（评论 r4481707763、e2e-harness.yml 与 run_atomic_memory_clean_migration.py 的 SUITES）`、
`applies_to: tests/e2e 下以 migration_backend 参数化的用例、以及任何新增 OceanBase SQL`、
`recheck_when: OB 作业改成跑整个 tests/e2e 目录、SUITES 变动、或 fixture 参数化/环境变量改名`。

<a id="r-pc85"></a>

## R-PC85. 能力探针必须与生产语句同形：字面量 options 通过不代表绑定参数可用（2026-11-05 实测 #2498）

`_NATIVE_FTS_PROBE` 用字面量 `MATCH(searchable_text^1, 'powercontext', 'operator=or;minimum_should_match=1')` 探测，
而生产语句是 `_NATIVE_FTS_MATCH = "MATCH(searchable_text^1, :fts_query, :fts_options)"`。探针只覆盖语法/特性缺失
（1064/1235/1305 才降级，其余 DBAPIError 直接抛出），不覆盖「能解析字面量、拒绝绑定 options」这一类。

- 审这类能力协商时，逐项比对探针语句与生产语句的差异（字面量 vs 绑定、列/索引名、arg 个数），差异项就是降级路径的盲区。
- 结论只能写成「降级覆盖 1064/1235/1305」，不要写成「引擎不支持时会自动回退」。
- 本机没有 OceanBase 实例，不能把这条升级为 P0/P1；按 §4 记为验证缺口或 P2 的覆盖建议。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2498 head c3f730ef（oceanbase/atomic_memory_index.py 的 `_NATIVE_FTS_PROBE` 与 `_NATIVE_FTS_MATCH`）`、
`applies_to: oceanbase/atomic_memory_index.py 的 `_supports_native_fts` 及任何 capability probe`、
`recheck_when: 探针语句或生产语句任一改动、或降级错误码集合变动`。

<a id="r-pc86"></a>

## R-PC86. 窗口兄弟项的相关性门槛要和投影输入同源：`atomic_memory_embedding_input(kind, text)` 不含 description（2026-11-05 实测 #2489）

`AtomicMemoryProjectionPublisher.prepare()` 的投影输入是 `input_text = atomic_memory_embedding_input(kind, body)`
（`f"{kind}\n{body}"`），`searchable_text = analyze_text(input_text)`，embedding 也是 `model.embed((input_text,))`；
`description` 只进 `content_hash`，不进检索与向量。因此窗口内未发布候选要和已发布记忆用同一门槛比较，
必须用 `related_window_match(request, item.content.kind, item.content.text, vectors.get(atomic_memory_embedding_input(...)))` —
带 description 或换用别的拼接会立刻与索引侧不一致（描述里有查询词时尤其明显）。

- 判等手法：拿 `AtomicMemoryProjectionPublisher.prepare()` 的 `searchable_text`/`embedding` 与
  `related_window_match` 的输入逐字比对，比跑 e2e 更快定位偏差。
- `tests/e2e/test_atomic_memory_vector_index.py::test_unindexed_items_match_the_related_threshold_the_index_applies`
  是现成的对照（`enumerate_related_with_heads` 与 `related_window_match` 逐模式断言同集合），改门槛逻辑时先跑它。
- 本机 sqlite 下该文件 13 passed / 14 skipped；seekdb/oceanbase 参数按 R-PC84 处理。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2489 head 84b9011a（`atomic_memory_processing.py::related_window_match`、`persistence/atomic_memory_index.py::prepare`）`、
`applies_to: runtime/atomic_memory_processing.py 的窗口比较与 persistence/atomic_memory_index.py 的投影输入`、
`recheck_when: 投影输入改成含 description、或 `related_window_match` 的入参增加字段`。

<a id="r-pc90"></a>

## R-PC90. `create_app(middleware=...)` 传入的中间件位于两层 `BaseHTTPMiddleware` **之内**：不发送响应就会变成 500（2026-11-06 实测 #2512）

`src/powercontext/server/app.py::create_app` 在构造 `FastAPI(middleware=list(middleware))` 之后，用
`@app.middleware("http")` 依次注册 `negotiate_dream_contract` 与 `attach_request_id`；装饰器走
`add_middleware`，而 Starlette 的 `add_middleware` 是 `user_middleware.insert(0, ...)`。因此最终顺序
（外→内）是 `HttpRequestId → HttpAdmission → attach_request_id → negotiate_dream_contract →
[调用方 middleware 列表] → 路由`。经 `app.add_middleware(...)` 在 `create_app` 返回后再注册的中间件则位于
`attach_request_id` 之外。

判据与后果：若某个中间件在「读了正文但决定不回应」时直接 `return`（典型：读到 `http.disconnect` 后
`_receive_body()` 返回 `None`），只要它位于 `BaseHTTPMiddleware` 之内，外层 `call_next` 就取不到响应并抛
`RuntimeError: No response returned.`，再被 `ServerErrorMiddleware` 变成 500 + ASGI 回溯；在
`BaseHTTPMiddleware` 之外则干净返回、无响应、无 500。

- 实测 #2512（把正文读取从 `add_middleware` 移入 `middleware=`）：head `c77ccbeb` 在「已认证」与
  「`access.mode=disabled`」两种形态下都是 `RuntimeError` + 500；merge-base `c4b9b540` 两种形态都干净返回。
  未认证请求不受影响（认证先拒绝，`receive_calls=0`，正文读取根本没发生）。
- 因此「认证先于读正文」这类重构必须同时决定：断开路径是否保留在 `BaseHTTPMiddleware` 之外，或显式给
  客户端一个 `http.response.start`；只搬中间件不改断开语义会引入该回归，且新增的 401 用例覆盖不到它。
- 探针形态：直接 `asyncio.run(app(scope, receive, send))`，`receive` 先回 `http.request`（`more_body: true`）
  再回 `http.disconnect`，`send` 收集 `http.response.start`。**不要**用 `asyncio.wait_for` 等「能吞取消」的结构
  判定挂起，用 `asyncio.wait({task}, timeout=...)` 后 `os._exit` 收尾。

关键词：`validated_at: 2026-11-06`、`validated_ref: #2512 head c77ccbeb / merge-base c4b9b540`、
`applies_to: 任何调整 `src/powercontext/server/*` 中间件顺序或注册方式的 PR`、
`recheck_when: `create_app` 改用 `add_middleware` 注册 `attach_request_id`/`negotiate_dream_contract`、或 Starlette 的 `BaseHTTPMiddleware` 空响应处理变化`。

<a id="r-pc94"></a>

## R-PC94. 三个摘要/资格位置会在 dirty 时同时冲突，且两侧取值都不是合并结果树的值（2026-11-07 实测 #2270）

同一份 openapi 与 persistence 内容被三处独立门禁绑定，master 前进后会在同一批文件上产生"只冲突一行"的形态，
按常规「取一侧」解冲突必然让门禁红：

| 位置 | 门禁 | 取值来源 |
|---|---|---|
| `release/upgrade-support.json` `schema_review.persistence_sha256` | `make upgrade-policy-check` → `scripts/upgrade_release_gate.py::load_policy` | `managed_digest(ROOT)`：`builtin/persistence`、`builtin/code`、`server/identity.py`、`server/authz`、`limits.py` 下 `.py/.sql/.json`，CRLF→LF，排序 JSON 再哈希 |
| `desktop/src-tauri/src/transport/operations.json`、`desktop/ui/src/generated/operations.ts` 的 `contractSha256` | `pnpm --dir desktop generate --check`（`desktop/scripts/generate.mjs` 逐文件文本全等） | `sha256(raw openapi 文本, CRLF→LF)`（`generate.mjs` 的 `const digest = createHash("sha256").update(raw.replaceAll("
","
"))`） |
| `desktop/src-tauri/src/connections/compatibility.json` 的 qualification 记录 | `desktop/src-tauri/tests/session.rs::bundled_qualification_allows_explicit_scope_browsing` | 从 `operations.json` 取 `contractSha256`，在 profiles 里找同摘要记录，找不到 `.expect(...)` panic |

- 实测：head `8464c739` → `managed_digest 6f826ce3`（= 声明值）、`openapi e958f47c`（= 三处一致）；master `9a424e77` → `53f1fd23` / `9aabe256`；`git merge-tree --write-tree origin/master refs/pr/2270` 结果树 `616e2e5f` → `c4c51692` / `5e371014`，两个冲突块里的候选值分别是 head 与 master 各自的值，都不等于结果树的。
- 行为反证（`probes/r71/merge`，`git archive` 结果树后按侧解冲突）：保留 PR 侧 → `Upgrade release gate failed: Persistence changed (file set or content; CRLF/LF normalized)` exit 1；保留 master 侧 → 同样 exit 1；写入 `c4c51692…` → exit 0。
- 资格记录侧不需要跑 cargo：结果树的 `compatibility.json` 共 48 条 `contractSha256`，不含 `5e371014…`，即已可判定该用例会 panic。
- 结论口径：这类线程只能写"在该 head 上已修复"；只要 PR 是 `CONFLICTING`/`dirty`，报告里必须另写合并结果树的复算值，不能把 head 的自洽当成可合并依据。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2270 head 8464c739 / master 9a424e77 / 结果树 616e2e5f`、
`applies_to: 任何改动 `openapi/powercontext.yaml` 或 `builtin/persistence|code` 的 PR`、
`recheck_when: `generate.mjs` 摘要算法、`managed_digest` 的 `MANAGED_INPUTS`、或 qualification 记录格式变化`。

<a id="r-pc99"></a>

## R-PC99. 基于旧 merge-base 的 PR 会把「已合入 master 的修复」显示成本 PR 新增；两侧取值不同时会覆盖 master 更严格的版本（2026-11-07 实测 #2518）

- 现象（#2518，head `a7f24f8d`，base `9a424e77`，master tip `ed8902b2`）：
  - `.github/workflows/master.yml` 的 `Prepare a writable license-eye prefix` + `INSTALL_DIR` 与 master **字节一致**，
    在 PR diff 里却以「新增 10 行」出现 ⇒ 该段已由别的 PR 合入，本 PR 这段是死改动。
  - `website/next.config.mjs` 两侧不同：PR 加无条件的 `experimental: { cpus: 2 }`，master 已是
    `experimental: { cpus: process.env.CI ? 1 : 2 }` ⇒ 按 PR 侧合并会把 CI 的 worker 上限从 1 退回 2。
- 判据（不要用 PR diff 判断"本 PR 引入"）：`git show <master tip>:<path>` 看 master 取值；
  `git diff <PR head> <master tip> -- <path>` 看两侧实际差异；`mergeable_state=dirty` 时优先核「同位置双侧新增」。
- 处理与报告口径：这类 hunk 写作「与 master 重复 / 会覆盖 master 更严格取值」，建议从 PR 移除或按 master 取值 rebase；
  不写成"PR 新增缺陷"，也不把 `mergeable=false` 当作与技术无关的治理问题。
- 同一轮的基线对照：master tip `ed8902b2` 自身 `CI result` / `CI preflight` / `Upgrade release gate` 红
  （preflight 的 license-eye 安装与 `upgrade-acceptance / Prepare` 的 `twine check` 报
  `InvalidDistribution: ... '2.5' is not a valid metadata version`）⇒ 判某个 PR 的 CI 失败前，先取 master tip
  同窗口的失败项；PR 只出现 `CI result` 这类聚合失败、且失败根因落在工具链步骤时，归环境/基线。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2518 head a7f24f8d / base 9a424e77 / master ed8902b2`、
`applies_to: 任何长时间未 rebase 的 PR，尤其是 CI/工作流与 website 配置类改动`、
`recheck_when: master.yml 的 license-eye 步骤、website/next.config.mjs 的 experimental 段、或打包/twine 工具链升级`。

<a id="r-pc101"></a>

## R-PC101. OceanBase `SHOW PARAMETERS` 在 `--skip-column-names` 下的列位固定：`name`=5、`value`=7（awk 1-based）（2026-11-08 实测 #2526/#2498/#2518）

- 4.x 输出列序：`zone, svr_type, svr_ip, svr_port, name, data_type, value, info, section, scope, source, edit_level,
  default_value, isdefault`（官方文档一致）⇒ `awk '$5 == "datafile_size" && $7 == "4G"'` 与 Python 的
  `{row[4]: row[6]}` 都是对的，`row[4]` 不是 `data_type`。
- 复核方式：只有当仓库里已有**真实**用例能证明列位时才信本地 fixture——`tests/test_oceanbase_ci.py` 的 stub 是按实现写的 7 列
  （`server, 2882, zone, scope, name, type, value`），单靠它不能证明真实容器一致；#2498 的 `e2e-harness.yml` 里那段
  awk 是在真实容器上跑绿的独立实现，两处列位一致才算交叉验证。
- 同源风险：`ALTER SYSTEM SET datafile_*` 之后参数生效有延迟，判"配置已生效"必须轮询 `SHOW PARAMETERS` 而不是只看 SET 的返回。

关键词：`validated_at: 2026-11-08`、`validated_ref: #2526 head 105e7a94、#2498 head 775e574f（`Atomic Memory native FTS (OceanBase)` success）`、
`applies_to: `.github/workflows/*.yml` 与 `scripts/oceanbase_ci.py` 里解析 `SHOW PARAMETERS` 的代码`、
`recheck_when: OceanBase 镜像大版本变更（输出列增删）、或改用 `GV$OB_PARAMETERS` 查询`。

<a id="r-pc105"></a>

## R-PC105. `evaluation/memory/**/tests` 能否被执行由 `testpaths` + `Makefile::evaluation-unit-test` 两处枚举共同决定，缺一处等于从未跑过（2026-11-09 实测 #2529）

- 收集入口只有两个：`pyproject.toml` 的 `[tool.pytest.ini_options] testpaths = ["tests", "evaluation/memory/atomic_extraction/tests"]`
  （`make test` / `make unit-test` 走它），以及 `Makefile` 的 `evaluation-unit-test` 目标，后者**显式枚举**五个目录：
  `evaluation/artifact_evolution/tests`、`coding/swebench_pro/tests/unit`、`coding/work_continuity/tests/unit`、
  `memory/longmemeval_v2/tests`、`memory/capture_ownership/tests`（外加根环境跑的 `agent_tool_recovery/tests`）。
- 因此新建 `evaluation/memory/<新套件>/tests/` 时，两处都不改就**一个新用例也不会执行**；CI 里没有任何"跑整个 evaluation 目录"的作业。
  本次 `#2529` 的 `prepared_context_budget/tests`（29 个用例，含唯一校验 pinned report 的用例）正是这种状态。
- 判据：`grep -n "evaluation/" Makefile` 看 `evaluation-unit-test` 的枚举，再 `grep -n testpaths pyproject.toml`；
  收尾报告里"用例已通过"只能写成手工执行，不能写成 CI 覆盖。
- 配套陷阱：这类套件常把夹具摘要写进生成的报告，再断言"重放逐字节相等"。CRLF 工作树上摘要必然不同 ⇒ 必须在
  `git -c core.autocrlf=false archive` 的 LF 副本里重跑才能判 PR 缺陷（见 `review-experience.md` 的行尾条目）。

关键词：`validated_at: 2026-11-09`、`validated_ref: #2529 head 5411017c28d8c323bdd7664adcc11107e4bb81e7`、
`applies_to: `evaluation/memory/**/tests/` 下的新套件与其 Makefile/CI 接线`、
`recheck_when: `testpaths`、`evaluation-unit-test` 的枚举列表或 CI 的 evaluation 作业变更`。

<a id="r-pc106"></a>

## R-PC106. Issue 前提核验：grep 断言须同大小写同范围重跑，Allowed 文件集必须覆盖 Observable behavior（2026-11-09 实测 #2559/#2560/#2561）

- issue 正文里的 `git grep` 结论一律按**原样大小写 + 原样路径范围**重跑；`grep -E "UNVERIFIED"` 与 `grep -iE "unverified"` 在
  同一基线上是 1 vs 45 命中，凭前者写"该机制不存在"会漏掉 `runtime/models.py:185`、
  `http/_generated/models.py:817`/`schema.py:8507` 这类公开契约里的同义状态值。
- 判"某能力完全没有对应物"之前，先查**同义槽位**：`HandoffContent.omissions` 的 docstring 是
  "unavailable **or not verified**"（`builtin/artifacts/handoff/models.py`），`working_note` 已是 Atomic Memory kind
  （`atomic_memory/extraction.py`、`memory/prompts.py`），Dream `revise_topic_memory` 已要求保留
  "hypotheses, ruled-out causes, open questions"。缺独立标签 ≠ 缺机制。
- 验收里出现 `## <Section>` 时，先确认该表面是否真的产出 Markdown：`HandoffService.render()` 返回
  `model_dump_json(indent=2)`，`##` 分节只在 `server/dashboard/markdown.py::handoff_markdown` 与
  `builtin/handoff_report/rendering.py::_scope_section`；分节标签走 `CATALOGS[language]`，改分节即改中英标签表。
- 检查 issue 的 Allowed 文件集能否覆盖它自己的 invariant：`HandoffGenerationOutput` / `HandoffContent` 是 schema 约束输出，
  改结构化槽必须动 `handoff/models.py` 与渲染器；只开放 `prompts.py` 就只能得到自由文本。
- 写"已合并/已修复"的编号先分辨 issue 与 PR：`#2438` 是 issue，落地代码在 PR `#2452`（merge commit `f5a4f30a`）；
  `#2436` 也是 issue，其正文里的字段名（如 `candidate_count_basis`）在 master 上 0 命中属正常，不可当现状引用。

关键词：`validated_at: 2026-11-09`、`validated_ref: master 2291237a7809410ea0dc8f19f2de149573af8378`、
`applies_to: 本仓库 issue 合理性审查与"缺机制"类断言`、`recheck_when: Handoff/Topic Memory 提示词或渲染器重构、
working_note 语义变更、#2436/#2520 落地`。

<a id="r-pc108"></a>

## R-PC108. `TopicMemoryWorkBlock` 没有 `stage` 字段：`classify_block_code` 只有 `stage == "topic_memory"` 才出诊断（2026-11-10 实测 #2568）

- `builtin/artifacts/topic_memory/processing.py::TopicMemoryWorkBlock` 的字段只有
  `block_id/attempt_id/scope_id/binding_name/source_after/source_through/budget_source_through/legacy_source_through/
  target_source_through/attempts/requests/tokens/error_code/last_error_code/blocked_at/retried_at/retry_request_generation`；没有 `stage`。
- `processing_diagnostics.classify_block_code(stage, code)` 是 `return _topic_memory_diagnostics(code) if stage == "topic_memory" else None`
  ⇒ 任何 `getattr(block, "stage", None)` 写法拿到的都是 `None`，诊断恒为 `None`。判"诊断字段是否真的产出"要用真实模型构造
  block 跑一遍，不要接受 `Mock(stage="topic_memory")`；`TopicMemoryProcessingStatus` 的字段是
  `state/source_cursor/source_head/target_source_through/block`。
- 同一处的状态语义以 `runtime/processing_observation.py::observe_processing` 为准：`requested > handled` → `pending`、
  `dirty > clean` → `dirty`、`handled` → `acknowledged`、否则 `idle`。把 `source_cursor/source_head` 赋成
  `clean_generation/dirty_generation` 会让 `pending_inputs` 与 `outstanding_work` 恒等，并丢掉 "已受理未 ack" 的 pending。

- **durable block 的 `stage` 只有一个取值。** `runtime/processing_contracts.py::ArtifactProcessingBlock` 全仓唯一构造点是
  `runtime/topic_memory_scope.py:88`（硬编码 `stage="topic_memory"`），唯一抛出点是同文件 `:173` 的
  `ArtifactProcessingBlockedError(block)`，唯一消费点是 `runtime/artifact_processing.py:1338` 的
  `classify_block_code(block.stage, block.error_code)`。因此**任何新增的 `elif stage == "<family>"` 分支在只加分支、
  不加生产者时都是死代码**（2026-11-11 复核 #2539 新增 `stage == "dream"`：`git grep -n 'stage="dream"' src/` 无命中，
  对应单测直接调 `classify_block_code("dream", ...)`，不覆盖生产行为）。判据：先 `git grep -n "ArtifactProcessingBlock(" src/`
  数构造点，再看新分支的 stage 字面量是否有生产者；只有测试直调就按"未覆盖生产路径"处理。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2568 head dcc582e7`、
`applies_to`：任何新增 processing 状态/诊断投影的改动；`recheck_when`：TopicMemoryWorkBlock 增加 stage 字段，或 observe_processing 的状态机变更。
（durable block 段：`validated_at: 2026-11-11`、`validated_ref: oceanbase/powercontext #2539 head f7bdb2e5`、
`recheck_when: 出现非 topic_memory 的 ArtifactProcessingBlock 构造点`）

<a id="r-pc109"></a>

## R-PC109. Source plugin 的 4xx 不会变成 `REJECTED`：服务端 409 会穿到 `business()` 把 collect 实例置 `failed`（2026-11-10 实测 #2546）

- `ConnectorRunSession.submit()` 只捕获 `ConnectorSubmissionRejectedError`（`sources/connectors.py`），而该异常在全仓只有
  **一个**抛出点：`client/ingestion.py` 的本地 4 MiB 预检（`observation exceeds ... bytes`）。服务端返回的 409/422
  （`source_conflict`、`invalid_source_ingestion`）走 `ServerResponseError`，**不会**转换成 item outcome。
- 因此 connector 里 `if receipt.status != ACCEPTED: ...` 这类分支对"同 identity 不同 content"的冲突实际不生效；异常穿过
  `ConnectorLifecycle.run` → `RemoteConnectorWorker` → `PluginContext.run_batch`（`observer.interrupted` 后 re-raise）→
  `apply()`（只捕获 `ManagementError(stale-target)`）→ `source_management/runtime.py::business` 把
  `self.local["status"]` 置为 `failed`。`local["run_id"]` 未变时不会重建 Context，实例停在 failed 直到 run_id 改变。
- 审查此类 connector 时，判断"冲突/拒绝是否被逐条记录"不能看有没有 `!= ACCEPTED` 分支，要顺着
  `_RemoteConnectorSourceSink.submit` → `submit_materialized_observation` 看是否吞掉 `ClientError`。
- 可达性判据：内容型插件的 identity 若取自**原始**文本（`codex-user-prompt:sha256(scope,session,turn,raw)`，与 live hook
  `hooks/recall.py` 同源），而写入的是脱敏文本，则"live hook 已写入原文、collect 再写入脱敏版"必然产生同 id 不同 payload；
  该场景已写在 `docs/en/docs/workflows/source-plugins.md`（"redacted history overlapping an existing raw capture"）。
- 修复方向：把 409 `source_conflict` 转成 `session.reject(item_id, definition, "redaction_conflict")` 后继续（`reject` 不中断循环），
  或让 sink 把 4xx 统一转成 `ConnectorSubmissionRejectedError`。注意 `ConnectorLifecycle.run` 只在
  `COMPLETE && checkpoint != previous && not unsafe` 时提交 checkpoint ⇒ 有 rejected item 时每轮都会重投，靠 Server 端的
  identity 幂等（`sources.py::add_many_with_status` 对相同 payload 返回已有行）兜底。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2546 head a4e06970`、
`applies_to`：新增/修改 Source plugin connector 的提交与错误处理；`recheck_when`：`ConnectorSubmissionRejectedError` 新增抛出点、
sink 开始转换 `ClientError`、或 `business()`/`run_batch` 改为捕获并重试。

<a id="r-pc116"></a>

## R-PC116. 「head 自洽」与「合并结果自洽」是两个判据，且两者对摘要的影响方向相反（2026-11-13 实测 #2270 head eb6a9dc7）

对改动 `persistence/` 或 `openapi/` 的长期分支 PR，判「已解决」时必须在同一轮里算两棵树：head 与
`git merge-tree --write-tree master refs/pr/<N>` 的结果树。两者不能用同一套结论：

- **`persistence_sha256` / `managed_digest`：两棵树可以相等，而且相等才是正常的**。受管输入
  （`src/powercontext/builtin/{persistence,code}`、`server/identity.py`、`server/authz`、`limits.py`）若不在冲突
  文件列表里，master 的新提交不会改变结果树的受管集合。本次 master `1cb0e75d` 上结果树（tree `2af2c1da`）
  与 head 都是 `d81b7d0e…`，即此前「合并树摘要两边都不对」的 Finding 已闭合——不要因为 PR 是 `dirty` 就
  假定结果树摘要必然失配。
- **`contractSha256`：只要 master 动过 `openapi/powercontext.yaml`，结果树摘要必然是第三个值**。本次结果树
  为 `54c69ae3…`（511 348 B），head `02022649…`（510 074 B）、master `e1ff2e3a…`（500 422 B）。因此
  「结果树摘要 ≠ 声明值」在 `dirty` 状态下是**必然且可预期**的，作者 rebase 后重新生成即可；它与
  「作者声称已对齐但 head 未变」是两类问题，不得据此重发同一 P1（§8 收敛）。

判据与做法：
1. 先 `git merge-tree --write-tree master refs/pr/<N>`；退出码 1 只表示有冲突，结果树仍可读。
2. 把结果树 `git archive <tree> src scripts release` 导出到 `probes/mergetree/tree`，用该树自己的
   `scripts/upgrade_release_gate.py::managed_digest` 复算；脚本需要 `scripts/` 同级加入 `sys.path`
   （`from upgrade_release_matrix import …`）。
3. 契约摘要按 `sha256(LF(git show <ref>:openapi/powercontext.yaml))` 三处并列，不要混用工作树字节
   （Windows `git archive` 会产出 CRLF）。
4. 结论里必须写「哪棵树、哪个值、是否必然」，否则会把 rebase 的正常要求误报成回归。

关键词：`validated_at: 2026-11-13`、`validated_ref: #2270 head eb6a9dc7 / master 1cb0e75d / merge-tree 2af2c1da`、
`applies_to: 改动 persistence 受管输入或 openapi/powercontext.yaml 的 PR`、
`recheck_when: MANAGED_INPUTS 清单、release/upgrade-support.json 的校验方式或 desktop 摘要生成流程变更`。

<a id="r-pc117"></a>

## R-PC117. 归档镜像里复核生成物：`generate_api.py --check` / `generate_js_operations.py --check` 直接可跑；`ty check` 不能用于定级（2026-11-13 实测 #2516 / #2244）

hand-merge 之后的「生成物是否真的重生成」不要靠肉眼比 diff：

1. `PYTHONPATH=<mirror>/source/head/src python scripts/generate_api.py --check`（Python 模型/operations）与
   `python scripts/generate_js_operations.py --check`（各宿主 `operations.generated.ts`）。两者都不需要 `uv`，
   退出码 0 即与 `openapi/powercontext.yaml` 自洽。注意 `cmd | tail` 打印的是 `tail` 的退出码，必须先
   `> log 2>&1` 再读 `$?`（同 `review-experience.md` 的 merge-tree 条目）。
2. `tests/test_desktop_contract.py` 只比对 `operations.json` / TS 常量 / `compatibility.json` 三者**之间**的
   `contractSha256`，不会回到 openapi 复算；它通过不等于「摘要等于当前 openapi 归一化值」（见 R-PC110）。
3. `ty check` 在归档镜像里会因 `pyproject.toml` 的 venv/`python-version` 配置失败
   （`does not point to a Python executable or a directory on disk`，exit 2）。加 `--python <本机 venv python>`
   能跑，但在 Windows 上会把 `socket.AF_UNIX` / `os.O_NOFOLLOW` / `fcntl` 等成员报成 ~90 条诊断——全部是
   环境假阳性，不得据此定级；镜像上的类型证据只能引用 CI。

关键词：`validated_at: 2026-11-13`、`validated_ref: #2516 head e27ef2d9 / #2244 head 1b26eb3b`、
`applies_to: 改动 openapi/powercontext.yaml 或移动审计包的 PR`、
`recheck_when: 生成脚本改名、Makefile 的 contract-test 目标改变、或 ty 配置调整`。

<a id="r-pc118"></a>

## R-PC118. `git show "refs/pr/<N>:<path>"` 在 Git Bash 下会被 MSYS 把冒号翻成分号（2026-11-13 实测 #2471）

现象：`git show refs/pr/2471:.github/workflows/master.yml` 报
`ambiguous argument 'refs\pr\2471;.github\workflows\master.yml'`。前缀 `MSYS_NO_PATHCONV=1` 即可，不必绕
`ls-tree` + `cat-file`。读点目录下的文件（`.github/...`）尤其容易命中。

关键词：`validated_at: 2026-11-13`、`validated_ref: #2471 head c5b9a19a`、`applies_to: 本机 Git Bash / MSYS 环境`、
`recheck_when: Git for Windows 的 MSYS 参数转换策略变化`。

<a id="r-pc121"></a>

## R-PC121. 两类「master 基线红」，归因前先在这两个位置对账（2026-11-16 实测 #2620）

- **`evaluation-tests` 的三个 pinned replay 用例在 master 上是红的**：
  `test_the_pinned_report_replays_byte_for_byte`、`test_the_recorded_command_replays_from_the_repository_root`、
  `test_the_reports_are_written_with_lf_on_every_platform`。判据：这三例只读
  `evaluation/memory/prepared_context_budget/`，若 PR 未改该目录却看到失败，先 `git diff <base> master -- <该目录>`
  是否为空；为空即基线红。**修复在 #2630**（head `6adbdc01` 起 36 passed），合入前不要把它记成任何 PR 的新增问题。
- **`native-service / {windows-task-scheduler, linux-systemd-user, macos-launchagent}` 三平台同红**：
  `tests/native/test_personal_service_lifecycle.py` 硬编码 `assert result["revision"] == "v1_5_0_004"`，
  而 `server_resources/manifest.json` 的 `revision_resources` 已到 `v1_5_0_005` ⇒ 断言取到 `v1_5_0_005`。
  该 job 由路径触发（`src/**/migrations/**`、`release/upgrade-support.json` 等），所以只有特定 PR 会看到它。
- **两处精确签名（2026-11-17 复核 #2620 head `eb40c9a9`）**：native-service 失败的是
  `test_native_public_migration_switches_an_installed_130_service[startup-retry]` 与 `[switch-retry]`，断言在
  `tests/native/test_personal_service_lifecycle.py:405`
  （`assert result["database_state"] == "ready" and result["revision"] == "v1_5_0_004"`，实际取到 `v1_5_0_005`），
  同 job 结果 `2 failed, 16 passed, 3 skipped`；evaluation-tests 是 `3 failed, 134 passed`，失败用例就是上面三例
  （job 日志的 `FAILED ...` 行可直接核对，无需展开 traceback）。
- **master tip 自身此刻也是红的（2026-11-17 实测 `fd165838`）**：`tests (3.12, e2e)` failure + 三条 `tests (*)` cancelled
  ⇒ 48 个 suite job `skipped`，另有 `Upgrade release gate` / `Nightly and manual acceptance report` 红。
  判「本 PR 的 check 为什么没有 suite 覆盖」之前先看 master tip，别把继承来的 skip/红写成本 PR 造成的。
- **`CI preflight` 的 `ty check` 红会连带 38 个 suite `skipped`（2026-11-20 实测 master `b64ee80b`）**：签名是
  `error[not-subscriptable] ... --> src/powercontext/server/dashboard/content.py:284:88`，来自 #2698、修复在 #2725（未合入）。
  判据：`CI preflight` 的 `Run checks` 步骤末尾 `make: *** [Makefile:46: workflow-actions-check] Error 1`，上面一行即 ty 诊断；
  此时 PR 的 `tests (*)` 全 `skipped`、`CI result` 与 `Upgrade release gate` 同时红。**同一时段 4 个 PR（#2674/#2700/#2708/#2729）
  全红同签名**，按 `R15` 记「不可判定 / 零覆盖」，不能写成某个 PR 的缺陷。反向对照：#2664 的 preflight 跑在破坏性提交之前，
  53 success 含 `tests (3.11 unit)/(3.12 e2e)/(3.14 unit)` + `Acceptance (sqlite)` ⇒ 同一天不同 PR 的覆盖度可以完全不同。
- **`gateway-validation / check` 的 `capacity_process.rs` 端口争用抖动（2026-11-25 实测 #2816 head `5c615121`）**：
  失败用例 `capability_contract_and_positive_integer_capacity_are_required`，栈为
  `crates/pc-gateway-app/tests/capacity_process.rs:171` 报 `gateway exited during startup: exit status: 101`，
  子进程 `crates/pc-gateway-app/src/main.rs:361` 报 `bind: Os { code: 98, kind: AddrInUse }`（日志里
  `pc-gateway listening (port takeover mode) addr=127.0.0.1:37375`），同文件另 11 例通过。判据：失败文本是 `AddrInUse`
  而非断言失败，且 PR 文件集不含 `gateway/`；同一时刻 master tip 的同名 job success ⇒ 环境抖动，不计 PR 缺陷。
- 两处都属于「master 自身红」，但 `CI result` 聚合 check 同样红 ⇒ 仍会挡住 `mergeable_state`；报告里要分开写
  「代码问题 / 基线红 / 环境」三者。
- **`harness-validation / Acceptance (sqlite)` 的当前基线签名（2026-11-25 实测 master `e65423c6` 与 #2816/#2725 同签名）**：
  `make: *** [Makefile:178: harness-compose-acceptance] Error 1`，起于 `make harness-compose-acceptance` 之后约 19–22 分钟，
  日志无断言失败行（镜像是 `powercontext-e2e-sqlite-*`，收尾 `Removing Volume …harbor-docker-data`）。
  判据：master tip 同 job 同签名即基线，不按 PR 新增问题记。
- **suite job 全 `skipped` 要先读 preflight 打印的 suite map 才能定性（2026-11-25 实测 #2771/#2700）**：
  `scripts/ci_changes.py` 输出逐项布尔（如 `"gateway": true, "tests": false`），gateway-only 的 PR 会 legitimately
  skip 39 个 python/dify/host job；这不是 `R-PC03` 说的 fail-fast 级联。判据：`CI preflight` success 且 map 中该 suite 为
  `false` ⇒ 覆盖边界按路径划定；map 为 `true` 而 job `skipped` ⇒ 才是级联跳过、零覆盖。

关键词：`validated_at: 2026-11-25`、`validated_ref: #2620 head 4b9d5d6e（run 43709140727：job 132948228522 evaluation、
132948230449/132948230465/132948230434 native-service）、#2630 head 6adbdc01、master b64ee80b（preflight job 135986494237）、
#2708 head 1d4794cd（job 136012091222）、master e65423c6（Acceptance sqlite job 139006997223）、#2816 head 5c615121
（gateway job 138928503481 / Acceptance job 138929294185）`、`toolchain: ubuntu-latest / Python 3.12`、
`applies_to: 任一 PR 的 check-runs 判读`、`recheck_when: #2630 合入、native 测试的版本断言更新、或 evaluation 目录再变动`。

<a id="r-pc122"></a>

## R-PC122. 两条本仓专属的判读手法：`generate_integration_lifecycle.py --check` 需要 `.git`；`managed_digest` 必须三处同时命中才算方法可信（2026-11-17 实测 #2628 / #2647）

- **`--check` 在无 `.git` 的归档镜像里必然 exit 128**：`unlisted_copies()` 调
  `git ls-files --cached --others --exclude-standard`，`fatal: not a git repository` ⇒ 整段 traceback。
  此时不要下「生成副本漂移」的结论，改用等价手法逐份比对：源码在 `src/powercontext_integration_lifecycle/<name>`，
  每份副本 = 2 行生成头 + 源码正文，因此**同源副本之间应当彼此逐字节相同**（#2647 实测 7 份全部 `8dd1e424`，
  源码 `78ee65e0` 只差头部）。漂移判据用「同一 `<name>` 的所有副本 sha256 是否唯一」即可，不需要 git。
- **`managed_digest` 先做三点自证再判 head**：把 `<base>`、`master`、`<head>` 三个树各算一次，与各自声明的
  `persistence_sha256` 比对；只有三处全部命中，head 的结论才可信。#2628 实测 `base 303b32cc=1bcfbd39`、
  `master fd165838=0fe382bd`、`head 892e761c=608646ab` 三处均命中，说明算法与输入集合（`MANAGED_INPUTS` 五项）用对了。
  同一轮里曾因 `managed_digest(Path('.'))`（相对根）得到一次**假 MISMATCH**，改用绝对 `Path` 才对齐——
  算法对 CRLF 已归一化（`read_bytes().replace(b"\r\n", b"\n")`），所以归档树与工作树应当同值，
  出现不一致先怀疑调用方式，不要先写 P1。
- **TS 副本的登记面是 #2636 与 #2644 的交叉点**：`TYPESCRIPT_COPIES` 里 `{_OPENCLAW}/src/transport.ts` 已登记，
  说明 openclaw 参与生成链；而 `prompt-privacy.ts` 只列 `_DSH`/`_OPENCODE`/`_PI`。#2636 另以
  `{_OPENCLAW}/src/secrets.ts` 手写同一份规则（与 `integrations/lifecycle/prompt-privacy.ts` 除 2 行注释外逐字节相同）
  ⇒ 判「文档声称遵循同一策略」是否成立，要看它是否进了 `TYPESCRIPT_COPIES`，而不是看内容是否相同。
- **不 checkout 也能算 `managed_digest`（2026-11-17 追加）**：按 `MANAGED_INPUTS` 逐项
  `git ls-tree -r --format='%(objectname) %(path)' <ref>` 取 blob，再 `cat-file -p` 取字节、`\r\n→\n` 后
  按 `json.dumps(sorted)` 复算，结果与在 checkout 上调用 `scripts/upgrade_release_gate.py::managed_digest()` 完全一致
  （本轮 #2692 / #2688 / #2518 三个 PR 均命中：base 与 master tip `0fe382bd`、#2692 head `3f459b56`、
  #2688 head `ff07eab3`、#2518 head `e616b281`）。这比解归档更快，也不会被 archive 的行尾导出方式影响。

关键词：`validated_at: 2026-11-17`、`validated_ref: #2628 head 892e761c / base 303b32cc、master fd165838；#2647 head 3dabdb17；
#2636 head 6c90ea55；#2644 head b91159a4`、`toolchain: Windows / CPython 3.14.3（工作区 .venv，sha256sum + 纯函数导入）`、
`applies_to: 改动 integrations/** 的生成副本、或改 `release/upgrade-support.json::persistence_sha256` 的 PR`、
`recheck_when: generate_integration_lifecycle.py 的 unlisted 判定改为不依赖 git、MANAGED_INPUTS 变化、或 TYPESCRIPT_COPIES 结构变化`。

<a id="r-pc124"></a>

## R-PC124. 「新增 real-host e2e 作业」的验收判据：先核作业是否真跑，再核它与既有 suite 的覆盖分工（2026-11-17 实测 #2685 / #2686）

本仓近一轮大量新增「用真实宿主 CLI 跑插件链路」的作业（`openclaw-package`、`codex-host`、`bub-host`、
`claude-code-host`）。这类 PR 的 Diff 几乎全是测试 + CI，静态审读看不出强弱，必须按下面三步取证：

1. **作业名来自 `.github/ci-paths.toml` 的 `[gate]` 映射**，不是 job 名猜的：`openclaw = ["openclaw-package"]`、
   `claude_code = ["claude-code-host"]`。判定「改动会不会触发它」只需跑 `tests/test_ci_changes.py`（含
   `test_changed_shared_input_requires_its_consumers_in_result_gate` 的路径→suite 表）。
2. **`commits/<head>/check-runs?per_page=100` 里出现该作业且 success 只是第一步**；真正判「非空跑」看
   `gh run view --job <job_id> -R oceanbase/powercontext --log | grep "passed"`：#2685 为 `7 passed in 93.44s`、
   #2686 为 `4 passed in 28.67s`，与两个测试文件的用例数一致；同时确认 workflow 里有 `test -x "$<HOST>_CLI_BIN"`
   守卫（夹具在缺二进制时 `pytest.skip`，守卫把这变成硬失败）。
3. **同一文件在 `tests (x, e2e)` 里恒 skip**（夹具只在设置了 `OPENCLAW_CLI_BIN` / `CLAUDE_CODE_CLI_BIN` 时运行），
   所以该路径的覆盖**只**来自新作业；不要因为 `tests (x, e2e)` 绿就写「已有覆盖」。

配套注意：`claude-code-host` 固定 `runs-on: ubuntu-24.04` 并 `grep -qw avx2 /proc/cpuinfo`（Claude Code 的 linux-x64
二进制要 AVX2，自托管轻量 runner 可能没有）；`openclaw-package` 用 `mise exec node@24.15.0 --` 包住 npm/pytest，
而 `codex-host` 直接 `npm install`——`mise-action` 已把 node 放进 PATH，两种写法都成立，别把差异当缺陷。

关键词：`validated_at: 2026-11-17`、`validated_ref: #2685 head 9bd87bbe（job 133871995752）、#2686 head 03b4eda1（job 133870338902）`、
`toolchain: ubuntu-24.04 / node 24.15.0`、`applies_to: 改动 .github/ci-paths.toml、.github/workflows/master.yml 的宿主作业、或 tests/e2e/test_*_service_chain.py 的 PR`、
`recheck_when: ci-paths.toml 的 [gate] 映射或 suite 列表变化、宿主 CLI 版本的 pin 方式变化、或作业改用自托管 runner`。

<a id="r-pc125"></a>

## R-PC125. 「自动 prompt 隐私」共享规则只认裸键名：带前缀的键（`DB_PASSWORD=`、`db-password=`、`X-Api-Key:`）不会被脱敏（2026-11-18 实测 #2703）

`src/powercontext_integration_lifecycle/prompt_privacy.py::scrub_secrets` 是 hooks 与进程内适配器共用的唯一识别规则，
其赋值分支带 `(?<![\w-])`，因此键名前一个字符是 `_` 或 `-` 时整条不匹配。实测（head 578b1184）：

| 输入 | 共享规则 | Hermes 自带 `redact_secrets` |
|---|---|---|
| `DB_PASSWORD=hunter2` | 原样 | 原样 |
| `db-password=hunter2` | 原样 | 脱敏 |
| `X-Api-Key: hunter2` | 原样 | 脱敏 |
| `Authorization: Bearer …` | 脱敏 | 脱敏 |

判读要点：

1. **哪些路径只有共享规则**：`scripts/integration_lifecycle` 生成的 TS/JS 副本（dsh/openclaw/opencode/pi/kimi-code/
   zcode/cindy）、四个进程内 Python 适配器（hermes/langchain/langgraph/pydantic-ai）。它们既不跑 Hermes 的
   `SECRET_PATTERNS`，也没有第二道规则，所以上表前三类会**原样进 recall query、原样被捕获**。
2. **Hermes 的 trace 比 wire 严**：`prefetch` 的 trace 事件先 `_redact_secrets` 再 `_automatic_recall_query`，
   而真正发出去的 query 只过共享规则 ⇒ 本地 JSONL 里显示 `[REDACTED]`、Server 端仍收到明文。核对「是否脱敏」时
   不能只看 trace，必须看 `turn.queries` / `/v1/context/prepare` 的 `query` 字段。
3. **取证手法**：`tests/inprocess_adapter_turns.run_turn(adapter, prompt, monkeypatch=…, home=…, capture=True)`
   会把真实适配器跑在一个记录型 Server 上，直接返回 `queries/captures/requests`；写一条 20 行的探针即可复现，
   不必起真 Server。`monkeypatch` 参数只需一个有 `delenv` 的对象。
4. 判断「PR 是否扩大」：该缺口本身在共享源里早于 #2703（hooks 从 #2636/#2644 起就用它），所以按 `§4` 只能算
   base 缺陷；新 PR 的责任面是「把 surface 扩到新适配器 + 文档声称覆盖常规凭据赋值」。写 Finding 时把这个归属讲清楚，
   否则会被作者按「不在本 PR 范围」驳回。

关键词：`validated_at: 2026-11-18`、`validated_ref: #2703 head 578b1184、#2704 head c05dfc72`、
`toolchain: Python 3.14.3 / 工作区 .venv（D:/test/github/powercontext/.venv）`、
`applies_to: 任何改动 prompt 隐私、recall query 脱敏、或 capture 跳过逻辑的 PR`、
`recheck_when: prompt_privacy.py 的正则、_redact_secrets 的 SECRET_PATTERNS、或 tests/fixtures/automatic_prompt_privacy.json 变化`。

<a id="r-pc132"></a>

## R-PC132. PR 面里出现的 hunk 可能已由 master 合入；判「本 PR 新增 / 与在飞 PR 冲突」前先比 blob（2026-11-22 实测 #2727）

- #2727（`fix(dashboard): narrow prompt revision selection` 一类提交）在 `server/dashboard/content.py` 有一段 12 行改动，
  与主题无关、且看起来会和在同一函数上重写的 #2721 冲突；`git merge-tree --write-tree refs/pr/2721 refs/pr/2727`
  也确实报 `content.py` 与 `profile.html` 冲突。
- 实测反证：`git ls-tree master -- src/powercontext/server/dashboard/content.py` 与 head 的 blob 都是 `a9dce2b0`，
  `git diff master refs/pr/2727 -- <path>` 为空 ⇒ 该改动已由 master 的 `3720f29b` 合入，PR 侧没有新增内容，
  merge-base 陈旧才让它在 Files changed 里出现。
- 判据：①先比 `refs/pr/<N>` 与当前 `master` 的同路径 blob（`git rev-parse`）；②相同即不计为本 PR 新增，也不作为
  「与某 PR 冲突」的依据；③两个 PR 分支之间的 `merge-tree` 不等于合并结果（本轮 #2721 对 master 干净、对 #2727 才冲突）。
- 反向：`git diff master refs/pr/<N>` 会把 master 之后他人合入的改动显示成本 PR 的删除，只用于单文件比对，不用于
  统计新增面。

关键词：`validated_at: 2026-11-22`、`validated_ref: #2727 head 5d25170b / master 1840db81 / content.py blob a9dce2b0`、
`toolchain: git 2.55.0`、`applies_to: master`、
`recheck_when: Files changed 的基准改为 merge-base 以外口径，或仓库强制在飞 PR rebase`。

<a id="r-pc137"></a>

## R-PC137. `contents` raw 接口对大文件会返回空/EOF，取 blob 要走 `git/blobs`；作者回复里的摘要值只对当时的 head 成立（2026-11-24 实测 #2728 / #2765）

- `GET /repos/{o}/{r}/contents/<path>?ref=<sha>` + `Accept: application/vnd.github.raw` 对 200 KB 以上的文件
  （本次 `migration_resources/server_baselines/1.3.0/oceanbase.json` 263 KB、`server_sources/1.4.0/schemas/*.json`
  169–405 KB）会返回 0 字节，`gh` 报 `EOF`，重试无效；`contents` 列表接口对同一 sha 正常。改用
  `GET /repos/{o}/{r}/git/blobs/<blob_sha>`（`encoding: base64`）逐个补齐即可，257 个受管文件里 17 个走这条路径。
- 复算 `managed_digest`（`scripts/upgrade_release_gate.py`）的取数是「`MANAGED_INPUTS` 下 `.py`/`.sql`/`.json`
  的全集 + 每文件 sha256（先把 CRLF 归一成 LF）→ `json.dumps(sort_keys=True)` 再 sha256」。本次 #2728 head
  `b91714174f` 复算 `b8cb0b81…` 与 `release/upgrade-support.json` 声明一致。
- **回复里的摘要值不能当结论**：作者 11-22 的回复引用 `af6277a1…`（当时 head `305b79f`），11-23 再推一个
  commit 后同一字段已刷新为 `b8cb0b81…`。判「摘要是否同步」必须在当前 head 复算，不能比对回复文本。
- 同一 PR 内 `mergeable_state` 与 check 数会随 rebase 大变：#2728 从 `blocked` 变 `blocked`（approval 仍 0），
  但资格记录的 `contractSha256 90571f6b…` 与 `operations.json` 一致，说明资格记录是随生成物刷新的。
- 视觉缩进误判（#2765）：`activates = ...` 单独一行，其后的 `if activates and slot ...` 只门控 slot，
  而 `plugins.deny` / `plugins.allow` 的 `if` 与它同级。凭缩进读多条件守卫时容易把该行当成后续块的外层条件；
  判之前应把该函数的 `if/elif/else` 逐行取出行号与缩进宽度，或直接看 AST / 行号范围。

关键词：`validated_at: 2026-11-24`、`validated_ref: #2728 head b91714174f / #2765 head f60e2d36f3 + original 3249902308`、
`toolchain: CPython 3.13.12`、`applies_to: master`、
`recheck_when: 生成脚本改为 streaming 下载、MANAGED_INPUTS 变更、或 GitHub contents 接口上限调整`。
