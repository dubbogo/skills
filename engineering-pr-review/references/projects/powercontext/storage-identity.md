<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# PowerContext：存储、身份与迁移

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="r-pc13"></a>

## R-PC13. 迁移版本号必须跨 PR 核对（并行 PR 会撞号）

本仓迁移链是**线性的 revision 号**（`p0001`…`p000N`），多个 PR 同时开时极易撞号；单独看每个 PR 都自洽，合并时才会暴露。

- **命中面**：新增 `src/powercontext/builtin/persistence/migrations/{,mysql_}resources/versions/pNNNN_*.py`、修改 `resources/manifest.json`（`revision_resources` / `sqlite_baselines` / `sqlite_fingerprints` / `affected_objects`）、或改 `migrations/mysql_schema.py` 的 `_REVISIONS` / `_statements`。任一命中即视为跨 PR 检查触发项。
- **判据**：对同批 OPEN PR 逐个 `git show refs/pr/<N>:<migration file>` 取 `revision` / `down_revision`，并 `git show refs/pr/<N>:.../manifest.json` 取 `revision_resources` 与 `sqlite_fingerprints` 的键。两个 PR 从同一 `down_revision` 分叉且 `revision` 相同即为撞号（2026-10-17 实例：#1813 `p0005_artifact_revision_metadata` 与 #2004 `p0005_atomic_memory_evidence`，另有 #2031 同批修改迁移连接层）。
- **失效机制（按严重度递增）**：① `_statements` / `revision_resources` / `sqlite_fingerprints` 以 revision 号为键，后写覆盖前写，一方的 DDL 不再执行；② `sqlite_fingerprints.pNNNN` 两侧取值不同时，被覆盖方的 SQLite 基线校验与 `test_mysql_migration_runner` 判红；③ alembic 版本目录出现两个同 id 脚本且 `down_revision` 相同。**不要只看文本冲突**——撞号在 git 层可能完全没有冲突。
- **处理**：后合入的一方改号为下一个空号并链到前一方，同步 `_REVISIONS`、manifest 四个键与 `affected_objects`；同时要求 PR 正文写明迁移号协调结论。审查者只提 Finding，不改文件。
- **2026-10-30 实例（PR #2296，`v1_4_1_*` 命名）**：master 已合入 #2192 的 `v1_4_1_005_atomic_memory_description`（`schemas/sqlite-v1_4_1_005.json` 用 `statement` 键描述 `pc_atomic_memory_current.description`），本 PR 用**同号且同名路径**描述 `pc_artifact_source_locators`（同一 `schemas/sqlite-v1_4_1_005.json` 用 `create` 键），改号面覆盖 `versions/`、`mysql/versions/`、两个 `schemas/*`、`manifest.json` 四个分区与 `vector_profile.sqlite_layouts`。
- **「已改号到下一个空号」有时效性，必须按答复之后推进的 master tip 重新核对一次**（2026-10-31 实证 #2270）：
  该 PR 2026-10-29 从 `v1_4_1_005` 改到 `v1_4_1_006` 时确属空号，之后 #2210 把 `v1_4_1_006_source_write_plugins`
  合进 master（指纹 `cacce80b…`，链 `004 → 005 → 006 → v1_5_0_001`），而 #2270 的 `v1_4_1_006_work_ledger`
  （指纹 `92eaad28…`，`down_revision = v1_4_1_004`）仍然占同一 id。判据不是看 PR 自己是否自洽（该 head 的
  `test_migration_revision_names.py` + `test_full_server_migrations.py` 23 passed），而是
  `git merge-tree --write-tree master refs/pr/<N>` 里是否出现 `CONFLICT (add/add)` 落在
  `mysql/versions/<rev>.py` 与 `schemas/{sqlite,mysql}-<rev>.json` 上（本次 31 处冲突里正是这三处）。
  结论应按「部分解决」表述：编号冲突的机制修了，具体编号又被占用。
- **新增判据：PR 的 `base.sha` 会滞后于分支真实 tip**。本次 PR API 在整轮 review 中一直报 `base.sha=91805efd`，而 `branches/master` 已是 `90355b8e`；撞号核对必须用 `gh api repos/{owner}/{repo}/branches/master --jq .commit.sha` 的最新 tip 去列 `migrations/server_resources/{versions,mysql/versions,schemas}` 的文件名与 `revision` 字面值，不能只看 `baseRefOid`。同一 head 上 `mergeable` 由 `MERGEABLE` 变 `CONFLICTING`（`mergeStateStatus: DIRTY`）是并行 PR 抬高 base 的信号；此时 `potentialMergeCommit` 消失，不得再拿旧值当合并结果证据。
- **连带面**：改号后 `release/upgrade-support.json` 的 `persistence_sha256` 必须重算（`scripts/upgrade_release_gate.py::managed_digest`），且 base 抬升会改 `openapi/powercontext.yaml` ⇒ 桌面端 `operations.json`/`ui/src/generated/*` 的 `contractSha256` 与 `compatibility.json` 的资格记录同时失效（本次 master 的摘要已是 `fd8f5dcf…`，PR 内仍是 `8f04516f…`）。

- **2026-11-16 三方同号实例（#2674 / #2639 / #2664）**：master tip `ad0d0206` 链尾仍是 `v1_5_0_005`，三个 open PR
  都是 `revision = "v1_5_0_006"` + `down_revision = "v1_5_0_005"`，`sqlite_fingerprints["v1_5_0_006"]` 三个不同值
  （`0b9eb7d9` / `9e49c26f` / `5adca391`），且都新增**同一路径** `mysql/versions/v1_5_0_006.py`（三个不同 blob：
  `94d34c4e` / `79c24c23` / `c839a142`）。取法：`git ls-tree -r --name-only refs/pr/<N> | grep v1_5_0_0` +
  `git show "refs/pr/<N>:<file>"` 读 `revision`/`down_revision` + 读 `manifest.json` 的 `sqlite_fingerprints`。
  本仓 `server_sources/1.4.0/manifest.json` **也要**跟着加同一个 revision（历史源链与新链各有一份 manifest，
  只改一份会让 `test_release140_server_migrations` 之类的断言停在 005），所以改号面是「两处 manifest 的四个分区」。
- **2026-11-17 复核（#2639 head `5de7fc4d`）**：三方同号仍在（#2664 `5adca391…` / #2674 `0b9eb7d9…` / #2639 `0e2f7a0d…`，
  master `ad0d0206` 链尾仍是 005）。判据可升级为**两个 PR ref 直接 merge-tree**：
  `git merge-tree --write-tree refs/pr/2639 refs/pr/2674` 打印
  `CONFLICT (add/add): .../server_resources/mysql/versions/v1_5_0_006.py`，并在
  `schemas/{sqlite,mysql}-v1_5_0_006.json` 上给出 stage 2/3 两个不同 blob；与 #2664 合并时同路径同样落在 stage 2/3。
  这比逐 PR 读 `revision` 更直接，一次同时暴露「同路径不同内容」与「manifest 键覆盖」两种形态。
  报告口径：本 PR 自身 `test_migration_revision_names.py` / `test_full_server_migrations.py` 全绿不构成反驳。
- **改号解除「同 id」不等于解除冲突（2026-11-18 实证 #2664 head `a8b248b7`）**：该 PR 已把 `v1_5_0_006` 改成
  `v1_5_0_007_context_diagnostics`（`revision="v1_5_0_007"`、`down_revision="v1_5_0_005"`），manifest 与
  `release/upgrade-support.json` 同步改到 007（`persistence_sha256 547734ac…`，master 侧 `ed13bc32…`）。
  但 #2639/#2674 仍是 `v1_5_0_006` + `down_revision="v1_5_0_005"`，master 链尾也仍是 005 ⇒ **三个 revision 都挂在
  005 上，任意两者先合入都会留下两个 head**（`alembic upgrade head` 报 multiple heads）。判据要从「id 是否相同」
  升级为「`down_revision` 是否指向同一 head」：`git ls-tree -r --name-only refs/pr/<N> | grep server_resources/versions`
  后逐个读 `revision`/`down_revision`，把 (down_revision → revision) 画成边，出现一个 down 有多个 children 即分叉。
  结论口径：报「撞号已解除 + 分叉风险仍在（后者需把 `down_revision` 改挂已合入 head）」，不要因为 id 不同就判无问题。

关键词：`validated_at: 2026-11-18`、`validated_ref: #2664 head a8b248b7 / #2639 head 5de7fc4d / #2674 head cd4de02c / #2674 head 2bdd5b77（同号方 #2639 head 737484db / #2664 head 28745f63，master ad0d0206）`、`dc9b6a175154be0a2c334e7c02c99c2df0da3651`（PR #2004 Head）、`8088d6b5eaad0a17195d5888602f768c09e300cd`（PR #1813 Head）、`20192d92491db0aba6e87fae7ed54d5f4ab531a3`（PR #2296 Head）、`90355b8e`（撞号时的 master tip）、`applies_to: master 及全部并行 OPEN PR`、`recheck_when: 迁移机制改为 alembic 自动生成 revision、或引入 revision 号分配登记表、或 PR API 的 base.sha 改为实时刷新`。

<a id="r-pc14"></a>

## R-PC14. 「启动期 ensure 加列」必须与离线迁移布局登记保持一致（已实证）

绕开迁移链、改在启动时用 `ensure_*_schema` 补列，会让 **离线迁移工具** 不再认识该库。判据与证据形态如下。

- **命中面**：新增 `src/powercontext/builtin/persistence/*_schema.py` 的 `ensure_*`、把它加入 `runtime/composition.py` 的 `open_builtin_contexts` 两处调用点、同时删除/回退某个 `migrations/{,mysql_}resources/versions/pNNNN_*.py`、或修改 `migrations/mysql_schema.py` 的 `_REVISIONS` / `_statements`。
- **判据**：`mysql_schema._matches()` 要求 **列集合完全相等**（`set(table["columns"]) != set(expected["columns"])` 直接 False）。只要启动期新增的列不在任何已登记 revision 的布局里，`MySQLSchema.identify()` 报 `incompatible_schema`（→ 外层 `unknown_baseline`）、`verify(inventory, <已戳 revision>)` 也报 `incompatible_schema`（对外表现为 `recovery_required: Partial DDL requires the original durable intent`）。两条路都断，等于该库再也无法 `server db-migrate plan/apply/verify`。
- **为什么 CI 全绿**：`tests/builtin/persistence/test_mysql_migration_runner.py` 的库由迁移链（冻结基线 + `p0001..p000N`）构建，**从不经过启动期 `ensure_*`**；把断言从 `p0005` 改回 `p0004` 仍然通过。也正因如此，"MySQL/OceanBase relies on the CI jobs" 一类答复必须用本节的探针反驳。
- **复现方式（Base/Head 对照，无需真实数据库）**：`MySQLSchema(bundle)._schemas["p000N"]` 的深拷贝 + 把启动期 ALTER 用 `_apply_statement()` 施加其上，得到 live 布局，再分别调用 `identify()` / `verify()`。旧 head 与当前 head 各跑一次即可看出差异。探针实例：`{WORKSPACE}\review\oceanbase-powercontext-pr-1813\probes\probe_mysql_layout.py`（旧 head 树放 `probes/old-head/tree`）。
- **不算回归的边界**：SQLite 侧应用直连 `create_all` 建出的库在加列前后都不匹配任何已登记 `sqlite_fingerprints`，属既有行为，不要据此判 PR 引入。
- **处理**：建议作者要么保留一个登记 revision 描述新列（启动期 ensure 只补更老的库），要么把新列纳入已登记布局并同步冻结快照，并补一条"Server 启动过的库仍能 `verify()`"的 MySQL/OceanBase 用例。审查者只提 Finding，不改文件。

关键词：`validated_at: 2026-10-17`、`validated_ref: cebd9af15ab9506ce3dddef8175a3060abc900b3`（PR #1813 Head，p0005 删除 + 启动期加列）、`8088d6b5eaad0a17195d5888602f768c09e300cd`（同一 PR 的对照 Head）、`toolchain: Windows / Python 3.14 / alembic（工作区 .venv）`、`applies_to: master 上 builtin/persistence 的启动期 schema 兼容层与 migrations 离线工具`、`recheck_when: mysql_schema 的 _matches 改为子集语义、迁移机制改回单一 alembic 链、或启动期 ensure 迁回迁移链`。

<a id="r-pc18"></a>

## R-PC18. Source 持久化 payload 的版本化与历史读回（2026-10-18 实证）

`src/powercontext/builtin/persistence/sources.py` 的 payload 同时承载「历史证据」与「今日解释」，改动它必须逐项核对四个面。

- **payload 字节 ≠ material**：`_StoredSourcePayload`（`extra="forbid"`）现在含 Server-owned header `source` / `source_keys`，写入用 `model_dump(mode="json", exclude_none=True)`；而 `_source_material_digest_material()` / `_source_material_digest()` 只哈希 `envelope.value`（material）。因此「重写整行 payload」不会改变 `material_digest`、binding 与 `journal_position`——这是 `_retain_native_header()` 敢在复放路径直接 `UPDATE payload` 的前提。审查看改动时先确认 digest 覆盖面，再判断字节级重写是否安全。
- **复放路径变成了写路径**：`add_with_status()` 在 `stored.value == source` 的幂等复放分支里对 native 行调用 `_retain_native_header()`（仅补 `source`/`source_keys`，`envelope.source is not None` 时直接返回）。同一函数的 `IntegrityError` 并发恢复分支**不**调用它 ⇒ 同一 legacy 行是否被补 header 取决于是否撞上并发插入；这属于机会式富化，不要按缺陷定级，但写 Finding 时要点明两条分支不一致。
- **历史读回的身份来源**：`_historical_source()` 优先用 `envelope.source`，并用 `source_keys` 中 material 实际存在的别名逐个核对（不一致抛 `IdentityMismatchError`）；identity 三键固定为 `name` / `definition_version` / `materialization`，**非 identity 字段仍取当前 definition**（`test_explicit_name_alias_evidence_survives_restart_without_the_native_definition` 断言 `description == "current description"`）。判据：作者宣称「保留身份」时要问清保留的是哪三键、其余字段取历史还是取今天。
- **旧版本可读性**：模型是 `extra="forbid"` ⇒ 新增 header 后，旧版本二进制读到新 payload 会 `InvalidStoredPayloadError`。本仓迁移是单向的，一般不作 Finding，但要在收尾里写明该边界。
- **2026-10-19 补充（head `8ee3aba7`）**：`_historical_source()` 在**适配器已被移除**时（`definition_for_name` 抛 `SourceDefinitionNotFoundError`）会跳过 `_normalize_native_material`，把原始 material 直接交给 `load_model(Source, ...)`。`Source`（`src/powercontext/sources/models.py:60`）**没有 `extra="forbid"`**，于是遗留 camelCase 键（如 `definitionVersion`）被静默丢弃、`definition_version` 落到 `Field(default="1")`。master 同形态是抛 `SourceDefinitionNotFoundError`（读取失败、身份不变）⇒ 这是行为变化，不是既有形态。影响不止展示：该版本参与 `_find_evidence_manifest()` 与 `_bound_evidence()` 的 `binding["definition_version"]` 比对，被改成 `"1"` 会让绑定判为未绑定、声明被静默丢弃。探针：`oceanbase-powercontext-pr-2004/probes/probe_legacy_camel_identity.py`。
- **验证方式**：`PYTHONPATH=<镜像>/src .venv/Scripts/python.exe -m pytest tests/builtin/persistence/test_sources.py tests/e2e/test_atomic_memory_source_evidence.py`（2026-10-18 实测 15 passed + e2e 通过）。Windows 上 `tests/builtin/persistence/test_database_backup_providers.py` 与 `test_database_migrations.py` 会成片红（`backup.py` 报 `OSError [Errno 9] Bad file descriptor`），与本类改动无关，按环境问题处理。

关键词：`validated_at: 2026-10-19`、`validated_ref: 8ee3aba7e99f34c1f296678a3fd3e3ff2f602b45`（PR #2004 Head）、`toolchain: Windows / Python 3.14.3（工作区 .venv，aiosqlite）`、`applies_to: builtin/persistence/sources.py 的 payload 结构、digest 与历史读回路径`、`recheck_when: `_StoredSourcePayload` 字段或 `extra` 策略变更、material_digest 定义改为覆盖整 envelope、`Source` 加上 extra 限制、或 payload 引入真正的版本迁移链`。

<a id="r-pc25"></a>

## R-PC25. 固定字节哈希的夹具必须在 `.gitattributes` 登记 `text eol=lf`（已实证）

`evaluation/` 下有「固定哈希」类资产：夹具的 SHA-256 被写进已提交的报告，并由用例断言工作树哈希等于该值。这类用例在 `core.autocrlf=true` 的 Windows 检出上恒红，因为比较的是工作树字节。

- **命中面**：任何 `read_bytes()` / `Path.read_text` 后接 `sha256` 并与仓库内常量或已 pin 报告比较的测试（2026-10-19 实例：`evaluation/memory/atomic_extraction/manifest.py::load_manifest` + `tests/test_manifest.py::test_pinned_reports_match_the_current_dataset_and_prompt_contract`），以及新增大体积 JSON/CSV 夹具的 PR。
- **既有约定**：`.gitattributes` 已为字节敏感资产登记 `text eol=lf`（`evaluation/memory/locomo/dataset/locomo10.json`、`e2e/bub/harbor-tasks/**`、`e2e/bub/tasks/*.yaml`、`integrations/**/skills/powercontext-project-context/**`）。新增夹具不在其中即为缺口；`.pre-commit-config.yaml` 的 `pretty-format-json` exclusion **不能**替代它（前者只管 hook 重写，不管 checkout 行尾）。
- **判据三步**：① `git cat-file -p <ref>:<path> | sha256sum` 得 blob 哈希；② 工作树文件 `sha256sum` 得检出哈希；③ 若两者不等且 `b.replace(b"\r\n", b"\n")` 后相等，即为纯行尾差异（`git archive` 与本机 checkout 在 `autocrlf=true` 下都会产出 CRLF，仅 `eol=lf` 登记的路径保持 LF）。
- **验证方式**：同一 head 两份树对照——原样检出跑出 `1 failed, 2 passed`；只把该夹具归一化为 LF（`probes/lf-eol/source`）后 `3 passed`。这就是最小反证，不需要真实 provider。
- **影响面判断**：若该测试目录已被写进 `pyproject.toml` 的 `testpaths`，则 Windows 贡献者跑 `pytest` 会整片变红；而 `windows-unit-portability` 只跑 `tests/builtin/runtime/test_artifact_processing.py`，CI 不会暴露 ⇒ 不能以「CI 全绿」否定该 Finding。
- **定级口径**：仅影响本地开发与可复现性，不改变产品行为 ⇒ P2；修复方向二选一（补 `.gitattributes`，或哈希前归一化并在文档把「exact bytes」改为「归一化字节」）。

- **2026-10-21 追加同类命中面**：`scripts/upgrade_release_gate.py::managed_digest()`（PR #2181 引入）对
  `MANAGED_INPUTS`（`builtin/persistence`、`builtin/code`、`server/identity.py`、`server/authz`、`limits.py`）
  的工作树字节取 sha256 并与 `release/upgrade-support.json::schema_review.persistence_sha256` 比较；该函数已并入
  `make check` 与 `make release-check`。同一 commit `d7f2d897` 上，CRLF 工作树得 `6b533d6e…`、逐文件归一为 LF 后得
  `ca3b475f…`（= 声明值）⇒ Windows 贡献者在**未改任何文件**时也会收到 `Persistence changed: update the compatibility
  review`，照提示改常量则会在 Linux CI 上失败。判据同本节三步；处理方向是哈希前归一化，或对这些路径声明 `text eol=lf`。

关键词：`validated_at: 2026-10-21`、`validated_ref: 3f6163cd00d186d7f018da45da9888c9c5f6579a`（PR #2078 Head）、`e4efb39bd6b8303a508c83fd5fcde5f99290b785`（PR #2078 base）、`d7f2d897e14e50243a7e2596b0223539edd74816`（PR #2181 Head，release gate digest 形态）、`toolchain: Windows / core.autocrlf=true / Python 3.14.3`、`applies_to: evaluation/ 下的固定哈希夹具与其报告、release/upgrade-support.json 的 persistence_sha256，以及任何对工作树字节取哈希并与仓库内常量比较的门禁`、`recheck_when: 仓库新增全局 .gitattributes 规则把 *.json 设为 eol=lf、load_manifest 或 managed_digest 改为归一化哈希、或 upgrade-policy-check 移出 make check`。

<a id="r-pc27"></a>

## R-PC27. 新增的 typed refusal 必须在**全部** CLI 入口收敛，而不只是迁移命令（已实证）

- **背景**：本仓会打开主库的 CLI 维护命令有 4 类：`server db-migrate`（走 `database_migration.py::_operator_errors`，契约是 `{"state":"blocked","error":<code>,"message":...}`）、`server processing-migrate`、`server atomic-memory-migrate`、`server atomic-memory-rebuild-projection`（走 `typer.BadParameter`，exit 2）、以及 `server identity-reset`（**无任何转换**，`server/identity.py::open_server_identity_repository` → `SeekDBProfile.open`）。`powercontext code` 也经 `SeekDBProfile.open`。
- **判据**：新增一个「预期内的拒绝」异常（本例 `LegacySeekDBDatabaseError`）时，`grep -rn "<ExceptionClass>" src/` 与 `grep -rn "SeekDBProfile\.\|SeekDBProfile(" src/` 必须覆盖上表全部入口；只在一个入口加 `except` 即为不完整。
- **可观察差异**：同一次拒绝下 `atomic-memory-migrate` 是 exit 2 + 指引文本，`identity-reset` 是 exit 1 + stdout 空 + 异常原样逃出（终端为 traceback）。身份轮换本身未执行，无数据风险 ⇒ 定级 P2。
- **探针**：`oceanbase-powercontext-pr-2031/probes/probe_identity_reset_r14.py`（stub `SeekDBProfile.open/open_existing` 直接抛异常，不打开数据库；同一脚本并排跑「已转换」与「未转换」的命令，输出 exit_code / exception / guidance 三列）。
- **同一提交的验收方式**：转换类改动的变异反证用 `oceanbase-powercontext-pr-2031/probes/mutate_r14.py` —— 回退 wrapper 后连接层用例必须恰好转红并复现原签名；回退 `echo=False` 后探针用例必须转红；删掉某个 CLI 的 catch 后该用例只有未被覆盖的参数仍绿。

关键词：`validated_at: 2026-10-19`、`validated_ref: b0e379f6aae5495220e7dba4206e24df03439cf5`（PR #2031 Head）、`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: master 上 server/cli.py 的维护命令与新增 typed refusal`、`recheck_when: 新增/删除打开主库的 CLI 命令、或 refusal 改由统一异常基类渲染`。

<a id="r-pc30"></a>

## R-PC30. SQLite 支持基线是 3.38，判"pre-3.35 兼容回归"前先核 `SQLiteProfile.open` 守卫（已实证）

- **判据来源**：`src/powercontext/builtin/persistence/sqlite/profile.py::SQLiteProfile.open` 在 `sqlite3.sqlite_version_info < (3, 38, 0)` 时直接抛 `PersistenceError("SQLite 3.38.0 or newer is required for retrieval")`（master `0da4436d` 实测）。⇒ `RETURNING`（3.35+）与 `AS MATERIALIZED`（3.35+）都在支持基线内，不构成兼容性回归。
- **本仓现状**：master 的 `sqlite/topic_memory_index.py`（4 处）与 `experience_index.py`（3 处）无条件使用 `AS MATERIALIZED`，没有任何版本门控；因此以"3.34 上语法错误"为由判 P2 会把 base 已有的支持基线误判成 PR 引入。
- **措辞陷阱**：`tests/builtin/persistence/test_topic_memory.py` 旧 docstring 写的是 "Simulate the pre-3.35 SQL restriction"，实际模拟的是「驱动不使用 RETURNING」（`reject_returning` 回调），不是"老 SQLite"。PR #2079 已把它改成 `Publish and retrieve revisions when the driver does not use RETURNING`——见到旧措辞不要据此推断支持 pre-3.35。
- **另一个常被误读的点**：PR 把某文件"改回 base"后，`git diff --name-status <base>...<head>` 会不再包含该文件，此时旧行内线程变 `outdated`；回复时应给 blob 身份（`git rev-parse <ref>:<path>` 两侧相同）而不是只写"已修复"。

关键词：`validated_at: 2026-10-21`、`validated_ref: 0da4436d866b8580ca0153fa40785dc94119e9f1`（master）、`76a8f713ee09bc2842e097bd201331d5841d782b`（PR #2079 Head）、`toolchain: -`、`applies_to: builtin/persistence/sqlite 的 SQL 语法与版本兼容性判定`、`recheck_when: SQLiteProfile.open 的版本守卫放宽/收紧、或 `AS MATERIALIZED` 被替换为条件化查询`。

<a id="r-pc31"></a>

## R-PC31. 原子记忆提取证据的去重判据必须按「规范化文本」比较，并区分「提示词载体」与「审计记录」

`src/powercontext/builtin/artifacts/atomic_memory/extraction.py::project_atomic_memory_evidence` 把 Source 正文放进
`AtomicMemoryEvidence.content`，同时把整份 `Source.model_dump()` 放进 `source_metadata`；后者是提取提示词的输入，
**不是**持久化审计记录（`source_metadata` 在 `src/` 内只有该文件读写）。要删重复正文的 PR（#2139、#2163、Issue #2137）
都改这里，审查判据如下。

- **写入侧事实**：`persistence/records.py::create_source` 写 `content = _canonical_source_text(payload)`
  （RFC 8785 规范化 JSON）并原样保留 `wire_content`。因此「结构化 wire 与正文重复」的判据是
  `rfc8785.dumps(wire_content) == content`，**不是** `wire_content == content`（dict 与 str 永不相等）。
  只比较对象时，真实采集（集成传结构化 JSON）仍会把正文送两遍：2026-10-21 实测 #2163 head `1c57cf4a`
  在 `{"text": <body>, "kind": "note"}` 下正文出现 2 次 / 738 bytes，#2139 head `7d44342e` 为 1 次 / 586 bytes。
- **必须区分的四类载体**：① `ContentSource.content`（可与 adapter 读回值比对，字符串相等即可删）；
  ② `wire_content`（按规范化文本判等）；③ observation 的 `payload.content`（仅当 `content` 来自 text-evidence
  投影、且 payload 内容与之相等时才可删）；④ 其他 projection 的 `value.content`（**不得**无条件剥离——
  `SourceProjection.output_class` 是任意 BaseModel，`value.content` 可能是与正文无关的另一种文本）。
- **验证方式**：探针 `oceanbase-powercontext-pr-2163/probes/probe_structured_wire.py`——用
  `AtomicMemoryExtractionInput(evidence=(...)).model_dump_json()` 统计正文出现次数，对同一场景在 Base/Head
  或多个 PR 树上并排跑，输出「次数 + bytes」，比断言 dict 键更直接。
- **测试覆盖陷阱**：只测「wire 不含正文」的用例自洽但不覆盖真实形态；要求作者补 `{"text": <body>, ...}` 结构性
  wire，以及「projection 的 content 与正文不同」两条。
- **跨 PR 协调**：同一函数同一插入点被多个 PR 同时改时，先比对去重边界（谁删 wire、谁删 payload、
  谁保留其他 projection），只推进一个；边界不一致会在后合入者处必然冲突。
- **2026-10-22 补充（head `8083f5f6`，规范化比较已落地）**：改用 `_text_of()`/`_repeats()`（`:133`/`:163`）
  之后，原生 capture 路径上 `content == _canonical_source_text(wire)` 恒成立 ⇒ `wire_content` 在**所有真实采集**
  里都会被删（探针对 `{"messages":[...]}` 也从「保留」变为删除，`629` → `506` bytes）。因此
  「wire 与正文不同 ⇒ 保留」这条分支只能由 **adapter 读回值与 wire 规范文本不一致**的夹具触发：
  单测 `test_wire_bytes_that_carry_something_else_survive` 手写 `read=_BODY` 才使它保持绿。
  审查同类去重修复时，探针须走真实 adapter，或显式构造 `read != _canonical_source_text(wire)`；
  否则会把「恒删」误读成「条件保留」。同一 head 实测：structured wire 3 份/867 B（base）→ 1 份/586 B，
  新测试文件 11 passed，把 `_repeats` 回退成对象相等后恰 `1 failed (2 == 1) / 10 passed`。

关键词：`validated_at: 2026-10-22`、`validated_ref: 8083f5f61e77a4cf3448689b75a2618ad22b2238`（PR #2163 Head，规范化比较落地）、`1c57cf4a6e2149857bb6e37104208cfbded775c0`（PR #2163 旧 Head）、`7d44342e51d995147beab3d7951c764067de6277`（PR #2139 Head）、`88899876b2ac7b38a11420f34f4ecf6da14dd65b`（base）、`toolchain: Windows / Python 3.14.3（工作区 .venv）`、`applies_to: master 上 builtin/artifacts/atomic_memory 的提取证据投影与任何「减少提取输入 token」的 PR`、`recheck_when: create_source 不再用规范化 JSON 写入 content、source_metadata 改由持久化路径消费、或项目引入按内容哈希去重的通用载体`。

<a id="r-pc47"></a>

## R-PC47. `pc_atomic_memory_current` 新增列只由启动期 `require_current_schema` 的 ALTER 补齐，不在迁移布局里

- **事实**：PR #2192 给 `atomic_memory_current_table()` 加了 `description VARCHAR(200) NULL`，并在共享基类
  `persistence/atomic_memory_index.py::require_current_schema` 里读 `information_schema`（sqlite 走 inspector）后执行
  `ALTER TABLE pc_atomic_memory_current ADD COLUMN description VARCHAR(200) NULL`；sqlite 与 oceanbase 两个子类的
  `prepare_schema` 都调用它。`persistence/migrations/atomic_memory_v1.py` 本次未改，`ensure_supported_atomic_memory_schema`
  只拒绝遗留表名与退役引用列，不做整表列集断言 ⇒ 启动期加列不会触发迁移校验器的 schema 拒绝（与 R-PC14 的失败形态不同）。
- **审查含义**：判「新列缺失」时先分路径——新库由 `atomic_memory_current_table()` 建表即带该列；已存在的库要走过一次启动期
  `prepare_schema` 才有；纯离线 `database migrate` 之后是否有该列取决于该命令是否也调用 `prepare_schema`（本轮未验证，属缺口）。
  旧行该列为 NULL 是设计内的（历史 revision 没有描述），`AtomicMemoryContent.description` 用
  `exclude_if=lambda v: v is None` 保持历史序列化不变，manifest 返回 `description: null` 合契约。
- **并发风险（未实证，写 Finding 前需先复现）**：`读列 → 缺则 ALTER` 不是原子的，多进程同时启动会在 MySQL/OceanBase 上撞
  `Duplicate column name`。单进程 personal server 不触发；要下结论必须先构造两个并发 `prepare_schema`。
- **`search()` 契约**：`_resolve_query_embedding` 返回 5 元组、`search()` 解包 4 元是本 PR merge 解析引入的致命错（见
  `review-experience.md` 的 merge-commit 条目），同一提交里 `:675` 还把 `embedding_fallback=` 传给 `_rerank` 而赋值已被删。

关键词：`validated_at: 2026-10-24`、`validated_ref: PR #2192 head 7cb90431f3ba7b03c8e1e06f05a073c85fb24256`（
`src/powercontext/builtin/persistence/atomic_memory_index.py:575-585`、`atomic_memory_index_schema.py:49`、
`runtime/atomic_memory.py:320-412`）、`applies_to: Atomic Memory 当前索引表与 recall manifest`、
`recheck_when: 该表的列改为走 `persistence/migrations/` 的版本化迁移、或 `database migrate` 开始调用 `prepare_schema``。

<a id="r-pc52"></a>

## R-PC52. 新增 revision 的 DDL 条数会乘进每个 e2e 用例的 bootstrap 预算（2026-10-27 实测）

- `Acceptance (oceanbase)` 的 40 分钟步预算按「21 条用例 × 单条 bootstrap 成本」计。新增 revision 的
  `sqlite-*.json / mysql-*.json` 语句数直接决定单条用例时长：每多一条 `ALTER TABLE ... ADD COLUMN` 都要在
  OceanBase 上跑一次 DDL。
- 实测对照（同一天、同一矩阵、同一 runner 类）：#2246（新增 21 条语句）单条用例 140–160 s，跑到 19/21 被
  `timed out after 40 minutes`；#2258（无 persistence 改动）单条 90–100 s，整批 26 分钟结束。
- 判据：当 PR 新增迁移且 `Acceptance (oceanbase)` 超时/接近超时时，先数
  `len(json.load(open(schema))["statements"])`，再用 job 日志里相邻 `PASSED` 时间戳算单条耗时，与同日其它 PR 对比，
  不要把超时当成 runner 抖动。
- 建议方向：多列合并为一条 `ALTER`，或把新增存储面的初始化移出每用例 bootstrap（参考 R-PC26 的预算分层）。

关键词：`validated_at: 2026-10-27`、`validated_ref: #2246 head 71d5b44a / #2258 head 0614869d / master cdb8da29`、
`applies_to: 新增或修改 persistence 迁移与 schema 资源的 PR`、
`recheck_when: upgrade_release_gate 的摘要口径、Acceptance 步超时、或 bootstrap 预算结构变化`。

<a id="r-pc57"></a>

## R-PC57. `sqlite-*.json` 与 `mysql-*.json` 的资源结构不同：判 DDL 预算只看 mysql，判 layout 漏项只看 sqlite（2026-10-29 实测）

`R-PC52` 把「新增 revision 的语句数」笼统归到两个资源上，实际两条路径用的是不同文件与不同字段：

- **OceanBase / MySQL 路径**：`server_resources/mysql/versions/<rev>.py` 只调 `context.config.attributes["execute_revision"](revision)`，
  实现在 `migrations/mysql.py` 的 `_upgrade()`：逐条执行 `self.schema.recovery(...).pending_statements`。
  语句来自 `schemas/mysql-<rev>.json` 的 `revisions[<rev>]["statements"]`（该对象只有 `statements` + `changes`，**没有 `layout`**）。
  ⇒ 判 `Acceptance (oceanbase)` 的 DDL 预算，只数这一处。
- **SQLite 路径**：`server_resources/versions/<rev>_*.py` 直接读 `schemas/sqlite-<rev>.json` 的 `statements` 逐条 `exec_driver_sql`。
  同一文件还有 `layout` 数组，是**累计期望状态**（`v1_5_0_001`：21 条 statements / 122 条 layout），不是本 revision 的增量。
  更早的 revision 用另一种格式（`v1_4_1_004` 顶层只有 `create`），不要按统一 schema 解析。
- **判据顺序**：① 数 `mysql-*.json` 的 `revisions[rev].statements` 判预算；② 数 `sqlite-*.json` 的 `statements` 判 sqlite/seekdb 侧
  （`ALTER ADD COLUMN` 在 sqlite 是元数据操作，7 条与 1 条的量级差不构成 Finding）；③ 核对新增 revision 的 `layout`
  是否含**主线期间新增的表**——实测 #2246 head `bd6c04b9` 的 merge 解析把主线 `v1_4_1_004` 带入的 `pc_access_owner_recovery`
  补进 `sqlite-v1_5_0_001.json` 的 `layout`（+6 行），这是必须项而非手滑：漏了才是缺陷。
- 该 +6 行在 `git merge-tree` 与 head tree 的差异里可见，是 `R-PC55` 里「人工解析改动」的一种合法形态：判它是补项还是误改，
  只需确认被补的表在主线的哪个 revision 注册过（`git grep <table> <base> -- src/powercontext/builtin/persistence`）。

关键词：`validated_at: 2026-10-29`、`validated_ref: #2246 head bd6c04b9、master 1f0afd6b`、
`toolchain: Windows / Python 3.14.3（工作区 .venv）+ git 裸克隆`、`applies_to: persistence 迁移新增 revision、DDL 预算归因、merge 解析复核`、
`recheck_when: `execute_revision` 改为同时读 sqlite 资源、`layout` 语义改为增量、或 schema 资源统一为一种格式`。

<a id="r-pc70"></a>

## R-PC70. 迁移链只能往 head 之后追加；改已登记 revision 的 `down_revision` 会让已 stamp 的库跳过新 revision（2026-11-02 实测）

#2270 把 `v1_4_1_007`（Work Ledger）插在 `v1_5_0_001` 之前——两份 `v1_5_0_001` 版本的 `down_revision`
由 `v1_4_1_006` 改成 `v1_4_1_007`（`git diff <base> refs/pr/<N> -- .../v1_5_0_001*.py` 只有这一行）。而
`v1_5_0_001` 正是下一个发行版（#2395）的迁移目标 ⇒ 已 stamp 成 `v1_5_0_001` 的库仍是 alembic head，
新 revision 永远不执行，`pc_work_*` 等表在这些库上缺失。

核对顺序：①`grep -n '^revision\|^down_revision' server_resources/versions/*.py` 取链；②`git show refs/heads/master:<该文件>`
比对 master 上的 `down_revision` 有没有被改写；③看 release-prep PR 的 `target_version` 是否就是被改写的那个 head。

关键词：`validated_at: 2026-11-02`、`validated_ref: #2270 head 5fa749d8（base 745ebf2e）、master 上 v1_5_0_001 down_revision=v1_4_1_006`、
`applies_to: 新增 Server 迁移 revision 的 PR`、
`recheck_when: 迁移框架改成按软件版本选链、或发布流程允许 repo 内改写已登记 revision`。

<a id="r-pc92"></a>

## R-PC92. 改「已有」OpenAPI 参数的 schema 也会穿透到 Dify 的 `contract.json` 与工具入参（2026-11-07 实测 #2502）

R-PC68 覆盖的是「新增 operation」的消费方清单；**修改已有参数 schema 走的是另一条链**，且只有 `dify-tools`
会失败。

- `integrations/dify/generate_contract.py` 把 OpenAPI 参数**原样**拷入 contract：
  `"parameters": operation.get("parameters", [])`；同一文件还用 path 参数派生工具入参
  （`tool_requests[op] = {"properties": {p["name"]: p["schema"] for p in parameters if p["in"] == "path"}, ...}`）。
  ⇒ 给 `scope_id` 加一个 `pattern` 会同时改变 `contract.json` 的 `parameters` 与 `tool_requests`，
  不只是校验文件不同步。
- 门禁：`make dify-test` 的 `generate_contract.py --check` 失败，日志原文
  `Dify contract/declarations require regeneration: integrations/dify/plugin/powercontext_dify/contract.json`
  （退出码 2），`dify-tools` 红并连带 `CI result` 红。
- 判据（不需要跑 CI）：`git show <head>:integrations/dify/plugin/powercontext_dify/contract.json` 里目标参数的
  schema 若缺新加的字段即为漂移；再对照 `make dify-test` 是否在该 PR 的 suite 里被选中（`dify` suite）。
- 实测：#2502 head `e455acfa` 给六个 `scope_id` 参数加 `pattern: '.*\S.*'`，Desktop 侧生成物与
  `compatibility.json` 都重算了（`contractSha256` `e0b4ef55…` 与 head openapi 复算一致），唯独 Dify
  `contract.json` 未重建 ⇒ `dify-tools` + `CI result` 双红。同位已有 hidb4ai 的 P2 线程，按 R12 补证并上调为 P1。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2502 head e455acfa（run 42183080282 / job 127801965354）`、
`toolchain: -`、`applies_to: 任何改动 `openapi/powercontext.yaml` 参数 schema 的 PR`、
`recheck_when: `integrations/dify/generate_contract.py` 的投影规则变化，或 Dify 改为只投影 operationId/路径`。

<a id="r-pc98"></a>

## R-PC98. 判「迁移手册登记完整性」不能按 `schemas/sqlite.json` 反查；`managed_digest` 可在裸克隆上直接复算（2026-11-07 实测 #2296）

- **`schemas/sqlite.json` / `mysql-s1300.json` 不含任何后续修订表**：实测 `pc_access_owner_recovery`（`v1_4_1_004`）、
  `pc_source_write_plugins`（`v1_4_1_006`）、`pc_atomic_memory_evidence`（`v1_5_0_002`）、
  `pc_artifact_source_locators`（`v1_5_0_004`）在全布局里出现次数**都是 0**。用 `grep <table> schemas/sqlite.json`
  判「迁移漏登记」会得到假阴性。判据是四处同时看：`versions/<rev>_*.py`、`schemas/sqlite-<rev>.json`、
  `mysql/versions/<rev>.py` + `schemas/mysql-<rev>.json`、`manifest.json` 的 `mysql_state_layouts`。
- **`managed_digest` 不需要 checkout**：`scripts/upgrade_release_gate.py::managed_digest` 只对
  `MANAGED_INPUTS`（`builtin/persistence`、`builtin/code`、`server/identity.py`、`server/authz`、`limits.py`）下
  `*.py|*.sql|*.json` 求 SHA-256（`
→
` 归一化）再对 `json.dumps(sort_keys=True)` 取 SHA-256。可直接在
  `--filter=blob:none` 的裸克隆上用 `git ls-tree -r -z --full-tree <rev> -- <path>` + `git cat-file blob` 复算，
  省掉整树导出。实测 #2296 head `bae2f3e7` 复算 `4d7d3eb3…`（241 文件）== 声明值，可据此排除「摘要未重算」类缺陷。
  注意：裸克隆若缺该提交的 blob，`cat-file` 会返回 128 ⇒ 先 `git fetch origin refs/pull/<N>/head:refs/pr/<N> --force`。
- **同一轮内 head 可能连续前移**：`#2296` 在一轮审查内经历 `bbf0c761 → b71cdfb3 → bae2f3e7`（两次都是 CI 失败后补测试），
  结论必须写明所依据的 head，且每次前移都要重看增量是否触及结论所依赖的文件（本例只动 `tests/**` 与 `docs/*/workflows/sources.md`，
  未触及 `docs/*/operate/database-migrations.md`）。
- 相关口径：新增修订后 `tests/builtin/persistence/test_mysql_initialization_preflight.py` 会因 `plan.revisions` 多一项而红；
  判「改测试是否放水」看同用例是否仍以字面量钉住 `plan.revisions`（本例仍在钉），把 `result.revision` 改成
  `runner.bundle.head` 本身不构成放水。

关键词：`validated_at: 2026-11-07`、`validated_ref: #2296 head bae2f3e7 / base ecf2e22a`、`applies_to: `src/powercontext/builtin/persistence/migrations/**` 与 `release/upgrade-support.json` 的门禁`、`recheck_when: `scripts/upgrade_release_gate.py` 的 `MANAGED_INPUTS`/归一化方式、manifest 布局字段、或迁移资源目录结构变化`。

<a id="r-pc111"></a>

## R-PC111. OceanBase 迁移作业预算：判据是 `ceil(收集数/分片数) × (逐用例超时+10) + 190`，收集数要实跑（2026-11-10 实测 #2515 / #2526）

`scripts/run_atomic_memory_clean_migration.py::assigned_nodes` 的硬上限是 `capacity = math.ceil(len(nodes) / count)`，
与 durations 无关（durations 只决定谁进哪个分片）。因此"步骤上限是否覆盖最坏路径"必须用**实际收集数**算，不能用
durations 文件的键数或 PR 正文里的用例数。`tests/test_oceanbase_ci.py::test_all_oceanbase_migration_step_budgets_cover_collected_cases_and_cleanup`
已把该公式固化为断言：`step_minutes*60 >= ceil(N/shards)*(case_timeout+10) + 190`，并另断言
`job_minutes >= sum(计时的测试步骤 + Pull/Start 两步) + 10`。

- 取 N 的命令（WSL，`-k oceanbase` 必须在收集阶段就带上，否则 N 是含 sqlite 腿的全量）：
  `python -m pytest --collect-only -q <files> -k oceanbase`，取输出末尾 `N/M tests collected` 的 N。
- `#2515` head `77b22dc5` 实测：clean-migration 34（→ 上限 17/片，110m 步骤 17×370+190=6480s=108m ✓）、
  grant 13（→7，65m ✓）、long-query 13（→7，40m ✓）、startup 3（→2，15m ✓）、scope-search 2（→1，10m ✓）、
  background-metrics 1（→1，15m ✓）；作业 295 ≥ 11+14+10+15+110+65+15+40+3+3=286 ✓。
- 反驳"已修"的最快办法是变异：把该步骤上限改回旧值（110→90），`tests/test_oceanbase_ci.py` 必须报
  `assert (90 * 60) >= ((17 * (360 + 10)) + 190)`。变异副本要整树复制（该用例 `cwd=root` 跑子进程收集）。
- 早期记录里的"clean migration 47 例"是 `-k oceanbase` 之外的合计，不要再用。

关键词：`validated_at: 2026-11-10`、`validated_ref: #2515 head 77b22dc5`、`toolchain: WSL + _shared/venv-wsl（3.13.11）`、
`applies_to: e2e-harness.yml 的 atomic-memory-clean-* / acceptance 作业`、
`recheck_when: run_atomic_memory_clean_migration.py 的分配算法、`.github/oceanbase-migration-durations.json` 的键集、
或 SUITES 列表变更`。

<a id="r-pc126"></a>

## R-PC126. 并发迁移 PR 的 revision ID 与合并图取证

- **链尾会变，不要沿用旧结论**：2026-11-19 起 master 链尾是 `v1_5_2_pr2639`（#2639 已合入），任何仍挂
  `v1_5_0_005` 的新迁移都会与 master 分叉。判断前先 `git ls-tree --name-only refs/heads/master:src/powercontext/
  builtin/persistence/migrations/server_resources/versions | tail`。
- **PR 号命名只消除 add/add 同名文件，不消除分叉**：2026-11-19 实测 #2583（`v1_5_2_001`）、#2664（`v1_5_0_007`）、
  #2674（`v1_5_2_pr2674`）三者各自对 master 单头、`server_bundle()` 均能加载，但任意两者的并集都是两个 head。
  因此「单 PR 线性」不能写成「可合入」，也不能把成对分叉记成某一方的 P1——它是合并顺序义务，重复开线程违反 `R12`/§8。
- **取证命令（Windows 本机）**：
  - 单 PR 单头：对 `<repo>/src/powercontext/builtin/persistence/migrations/server_resources` 与
    `.../server_resources/mysql` 各跑一次 `alembic.script.ScriptDirectory(path).get_heads()`；路径必须写成
    `D:/...`，写 `/d/...` 会得到 `Path doesn't exist`（Windows python 不认 MSYS 路径）。
  - 两 PR 合并图：`git merge-tree --write-tree refs/pr/A refs/pr/B` 取冲突清单；再把两者的 `versions/*.py` 复制进
    同一 `pkg/versions/`，`ScriptDirectory('pkg').get_heads()`（该 API 要父目录，直接指向 `versions/` 返回空列表）。
  - 语义级校验优于目录级：`server_bundle()` / `production_bundle()` 会连带校验 manifest、fingerprints 与 source overlay。
- **gateway 无法在 Windows 编译**：`crates/pc-gateway-core/src/uds_gate_client.rs` 用 `tokio::net::UnixStream`（仅 unix），
  Windows 上 `cargo test -p pc-gateway-core` 直接 `unresolved import`。Rust 行为证据只能取 Linux 侧 CI 或 WSL。

关键词：`validated_at: 2026-11-21`、`validated_ref: #2583 277bc236、#2664 9615dcf8、#2674 9a3a0ac4、master 2f4997d9`、
`toolchain: alembic 1.20.0 / Python 3.14.3（D:/test/github/powercontext/.venv）`、`applies_to: master`、
`recheck_when: 链尾 revision 变化、出现新的 revision 命名规则、或 bundle.py 的线性校验改动`。

**2026-11-21 追加（shared draft `000` 已落地，复核判据随之改变）**：master `AGENTS.md` 现在把
「schema 变更累积在同一个未发布 revision `000`」写成政策（`server_resources/versions/000.py` + 同名 mysql，
`down_revision` 为最后冻结头；后续 PR 改同一 draft 而不是新增 revision；在飞 PR 只把自己的剩余改动折入
shared `000`，并按已有 draft 协调 SQL/资源/指纹/布局/注册）。因此：
- 判「撞号已解」只看 `get_heads()==['000']` 不够，还要看 `git merge-tree --write-tree refs/pr/A refs/pr/B`
  的冲突集：2026-11-21 实测 #2583×#2664 = 14 个冲突路径、#2583×#2674 = 10、#2664×#2674 = 11，冲突点固定在
  `versions/000.py`、`mysql/versions/000.py`、`schemas/{sqlite,mysql}-000.json`、`manifest.json`、
  `server_sources/1.4.0/manifest.json`、`release/upgrade-support.json` 与两份 `database-migrations.md`。
  计数必须取「tree oid 之后到首个空行之间」的行，`grep -c .` 会把后面 20–30 行 `CONFLICT (...)` 提示一起数进去
  （曾据此把 14 误写成 46，已原地 PATCH 评论）。这是**union 义务**而不是缺陷；
- 旧线程里「后合入方改号 / 改挂 `down_revision`」的建议在 shared-`000` 下已失效，必须改述为「union 进已合入的
  `000`」；遗留方仍需按合并结果重算 `persistence_sha256`（#2583 `6fa8ab97`、#2664 `83c00d40`、#2674 `f00934f2`
  在各自 head 上均与 `managed_digest()` 复算值逐字相同）；
- 三份 PR 的 `versions/` 均为 14 个 revision、单头 `000`，`v1_5_2_001` / `v1_5_0_007` / `v1_5_2_pr2674` 已全部移除
  （`git ls-tree ... versions | tail` 末项即判定入口）。

<a id="r-pc127"></a>

## R-PC127. Topic 校验和定义变更会连「已完成」的 journal 一起拒绝；本仓 PR 整轮 run 被取消时 `Upgrade release gate` 必红（2026-11-19 实测 #2674 head 88f9a300）

1. **`_inspect()` 的兼容豁免把 `source` 条件取反了（不是「守卫不看 state」）**：`_inspect()` 里显式写了
   `evidence["checksum"] != self.checksum and not (evidence["source"] != "atomic-maintenance-sqlite-v1" and
   evidence["checksum"] == sha256(RESOURCE) == "f28d5c52…cc")`，第三个合取项取反后 **`source` 恰为
   `atomic-maintenance-sqlite-v1` 的 journal 反而被判未豁免**，只有 `budget-v0`/`attempts-v0` 那两类能过。
   实测（head 88f9a300，探针 `probes/p2674_guard_terms_probe.py` 逐项求值）：A revision=False、B checksum=True、
   C `source != v1`=False、D 与 E 均 True、F configuration=False ⇒ `B and not(C and D and E)`=True ⇒
   `recovery_required`；同一表达式对 `budget-v0`/`attempts-v0` 为 False（放行）。已发布 tag v1.5.0/1.5.1/1.5.2 的
   `topic_memory_recovery_schema.py` 都会产出该 source，`_finish()` 落盘后不删 journal ⇒ 影响面是所有在该布局上
   成功跑过 Topic 迁移的 SQLite 部署，不是「中断的少数部署」。
   **教训：判「哪一类被拒 / 哪一类被放行」时，必须把守卫按原式逐项求值（每个 `and`/`or`/`not` 打印布尔值），
   不能凭代码注释、命名或「设计取舍」的直觉归因。** 我在这条上连续误判两次（先归因为 checksum 定义变更，
   再归因为接受面选择），实际是单个 `!=` 写反。
   判「released journal 兼容」时先看用例 parametrize 的 source 集合：`test_released_topic_journal_resumes_with_original_backup`
   用的是 `_legacy()`（`budget_v0`/`attempts_v0`），覆盖不到 `atomic-maintenance-sqlite-v1`。
   另：本 head 的资源摘要只覆盖 `schema.json` 与 `atomic_maintenance_sqlite_v2.json`（不含 `README.md`，值 `4abf219b…`），
   而同一份 `database-migrations.md` 里仍写着「all files in its resource directory」，文档自查要按代码枚举核。
   **2026-11-20 复核（#2674 head `faccf373`）：同一份文件里两段互相矛盾**——`:382` 写「all files in its resource directory」，
   `:545` 写「cover `schema.json` 和 `atomic_maintenance_sqlite_v2.json`, excluding `README.md`」，中文侧 `:328` / `:425` 同形；
   代码与 `:545` 一致（`_resource_checksum()` 只摘要两个文件），且 `test_topic_resource_documentation_does_not_invalidate_plan`
   显式断言改 `README.md` 不改变 `plan_id` ⇒ 可用测试反证「all files」这句话。判据：文档类不一致先找同文件内的另一处表述与
   对应单测，能拿到测试反证即可定 P2，不必等作者解释。
2. **`verify_atomic_memory_aliases` 与 `verify_atomic_memory_current` 各走一遍同一身份集**：后者已对每个身份 `_record()`，
   前者从 `after=None` 重来并再 `_record()`（2 条单行查询/身份）⇒ 核验成本翻倍，且无 merged 时也照跑；
   `atomic_projection._state` 以 `require_alias_projection=True` 算计划，`plan()`/`verify()` 同样付这笔钱。
3. **整轮 run 被取消时的门禁判读顺序**：`upgrade-acceptance` 的 `if` 要求 `needs.tests.result ∈ {success, skipped}`，
   任一矩阵作业 `cancelled`（含 `timeout-minutes` 到期）即整 job skip；`Upgrade release gate` 在
   `SCOPE_RESULT=success && UPGRADE_SELECTED=true` 时走 `test "$UPGRADE_RESULT" = success` ⇒ gate 红、下游全 skip。
   判据：run 的 `conclusion`/`run_attempt` → `tests` 矩阵各结论 → `upgrade-acceptance` 的 `if` 输入 → gate 的 `env:` 段。
   此时属 `R15` 不可判定态（需重跑），不能写成「CI 红＝代码坏」。

关键词：`validated_at: 2026-11-21`、`validated_ref: #2674 head 9a3a0ac4`、
`toolchain: Windows / CPython 3.14.3（工作区 .venv）`、
`applies_to: 改动 topic_memory_recovery 校验和定义、atomic_memory_rebuild 核验流程，或判读本仓 PR 的 CI 门禁`、
`recheck_when: _inspect 改为按 state 分支、verify_atomic_memory_aliases 并入主循环、或 master.yml 的 upgrade-acceptance / upgrade-release-gate 改动`。

**2026-11-21 复核（#2674 head `9a3a0ac4`：上述取反条件已修）**：`_inspect()` 现在是
`evidence.get("checksum") != self.checksum and not (evidence["checksum"] == sha256(RESOURCE).hexdigest()
== "f28d5c52…cc")`——去掉了 `source` 合取项，把豁免钉在冻结 schema 哈希上。源码级判据之外，本条要求的反证形态
可直接复用 `probes/p2674_completed_legacy_journal_probe.py`：先用 monkeypatch 把 `_resource_checksum` 换成
「旧定义」（只摘要 `schema.json`）写出 `state=complete` / `source=atomic-maintenance-sqlite-v1` / `checksum=f28d5c52…`
的 journal，再让未打桩的 runner 跑 `plan()`/`verify()`。实测 head `ready`/`ready`，`faccf373` 为 `recovery_required`；
把 `and evidence.get("source") != "atomic-maintenance-sqlite-v1"` 加回一次性副本后，`plan` 与 `verify` 立即双双
`recovery_required` ⇒ 探针能区分两种实现，不能只凭作者或他人「已修」的结论结案。
同 head 的 `_resource_checksum()` 为 `4abf219b…`（仍是 `schema.json` + `atomic_maintenance_sqlite_v2.json`
两份），据此可判「作者回复说覆盖整目录」是措辞夸大而非实现偏差：接受面完整，文档也已在 en `:440-441` 与
`:603`、zh `:371` 对齐到两份文件。

**CI 红的基础设施三类（同日实测）**：`Upgrade release gate` 红先看 `upgrade-acceptance` 的 job 日志——
`git fetch-pack: invalid index-pack`、`codeload ... SSL`、`Parallel upgrade gate failed: urlopen SSL EOF`
属 runner 网络；`Acceptance (sqlite)` 里 `apt-get update ... exit code: 100` 属容器网络；
作业末尾 `Failed to CreateArtifact: ECONNRESET` 属上传中断（此时测试往往已经跑完）。三者都不是 PR 缺陷，
按 `R15` 记不可判定。

<a id="r-pc131"></a>

## R-PC131. `schema_release.py check --base-ref` 与"PR 实际执行树"不是同一棵树：旧 base 的 PR 会把已冻结 revision 判成新增（2026-11-21 实测 #2541）

- workflow 传 `--base-ref "${{ github.event.pull_request.base.sha }}"`，但 checkout 的是 **merge ref**（当前 master + PR）。
  PR 若长期未 rebase，其 `base.sha` 会早于某个已合入的冻结 revision，于是 `preserve_history` 在 heads 侧看到该 revision 是
  "新增"，而它的名字不匹配 `RELEASE_ID`（`v<major>_<minor>_<patch>`）⇒
  `Append only the shared 000 draft, or its single frozen release revision` ⇒ preflight 红 ⇒ 全 suite skip。
- 实例：#2541 base `e725225b`（2026-11-16）不含 `v1_5_2_pr2639_source_collection.py`，merge ref（master `2f4997d9`）含，
  于是这个**并非本 PR 改动**的文件被判成新增。该 PR 与迁移无关，修法只有 rebase。
- 判据：先 `git ls-tree refs/pr/<N>:…/versions | tail`（merge ref）对比 `git ls-tree <base.sha>:…/versions | tail`，
  两侧差异若全部是**已冻结** revision，即本条场景，不是 PR 缺陷；不要把它写成"迁移撞号"。
- 归因口径：这是 PR 侧的 rebase 义务（阻断 CI），但没有可锚定的 diff 行 ⇒ 按 `R11` Fallback 只写报告。
- **第二种签名：`Frozen migration history changed: server`（2026-11-25 实测 #2765 head `55f1d507` / base `1840db817`）**。
  base 侧仍是 `000.py` 草稿 + `v1_5_2_pr2639*`，master 之后把 `000` 冻结成 `v1_6_0`、把 `v1_5_2_pr2639` 改名成
  `v1_5_0_006`；`preserve_history` 比较 `old.revisions`（base）与 `new.revisions`（merge ref）前缀不等 ⇒ 报这条。
  **判定手法（两条命令即可定性，不需要装依赖跑 CI）**：
  ① 在 exact head worktree 上跑 `PYTHONPATH=$PWD/src python scripts/schema_release.py check --base-ref <base.sha>`
  ⇒ 输出 `Frozen migration history matches base: …`（通过）；
  ② 把当前 master merge 进 head 的**结果树**上跑同一条命令 ⇒ 复现 CI 的红。
  两者结论不同即证明失败来自 base 冻结推进（merge ref 带入新冻结 revision），不是 PR 改动。
  根因与上一条相同（`--base-ref` 取 base.sha、checkout 取 merge ref），差别只在错误文本：base 缺冻结 ⇒
  `Append only the shared 000 draft…`；base 早于改名/冻结 ⇒ `Frozen migration history changed: <source>`。
  连带后果：`CI preflight` 红 ⇒ 39–57 个 suite job 全 `skipped`，该 head 零测试覆盖（`R15` 不可判定）。

关键词：`validated_at: 2026-11-25`、`validated_ref: #2541 head 15314e09 / base e725225b / master 2f4997d9（run 44877681088 / job 136765886359）、#2765 head 55f1d507 / base 1840db817 / master e65423c6（run 45521127346 / job 138892953518）`、
`toolchain: -`、`applies_to: master`、
`recheck_when: schema_release.py 的 --base-ref 语义改为 merge-base、或 workflow 改为对 merge-base 比较`。

<a id="r-pc139"></a>

## R-PC139. 所有权写入的两套幂等键：审批重试 409 的成因与判定（2026-11-24 实测 #2787）

- **键派生不同 ⇒ 同 owner 不同 key 也冲突**：审批写 owner 用 `bounded_idempotency_key("candidate-artifact-owner", scope_id, candidate_id)`；
  创建与迁移用 `_base_owner_idempotency_key(resource)` = `base-artifact-owner:<sha256(resource.key)>`（`server/app.py`
  的 `_establish_base_artifact_owners` 与 `server/ownership.py` 同一派生）。`RelationalAccessRepository.establish_artifact_owners`
  **只有在 owner 与 idempotency_key 双匹配时才幂等返回**，否则抛 `AccessConflictError("artifact-owner")`。
  ⇒ 迁移先写、审批重试后到，必然 409；反之迁移遇到已存在的审批 owner 只在 `apply` 里记为 conflict 并保留原值。
- **判定顺序**：先比两条写路径的键派生，再比 owner；键不同才需要读回比对（`#2787` 的做法是冲突后
  `access.artifact_owner(resource)` 比 `attestation.proposed_owner`，不匹配则 `raise`）。创建路径键相同，因此不受影响，
  不要按"同样的代码形状"要求它加同样的读回。
- **`/v1/candidates/approve` 的 409 有两个来源**：`AccessConflictError` → `error.code = "artifact-owner"`；
  `CandidateTerminalError` → `"candidate_terminal"`（handler 在 `current.version != request.expected_version` 时 re-raise）。
  断言 409 时必须同时断言 `error.code`，否则两种情况无法区分。
- **e2e 单文件可直跑做 A/B 反证**：`tests/e2e/test_access_ownership_migration.py` 单文件约 40 个用例，`-k` 选 2 个参数约 8s；
  把 head 的测试文件注入 base 归档即可复现「master 上失败、head 上通过」，比逐个读调用链更有力（配合工作区 `.venv` +
  `PYTHONPATH=<mirror>/src;<mirror>/integrations/pydantic-ai/src;<mirror>/scripts`）。

关键词：`validated_at: 2026-11-24`、`validated_ref: #2787 head bdccfc4e / base 80c52f7b`、`applies_to: master`、
`recheck_when: candidate-artifact-owner 或 base-artifact-owner 键派生变化、establish_artifact_owners 的幂等判据变化、approve_candidate 的 owner 写入位置变化`。
