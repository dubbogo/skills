<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# CI、构建与依赖

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-003"></a>

## Diff 完整性计数与非 ASCII 路径

- Git 可能把包含中文等非 ASCII 字符的路径写成带引号的 `diff --git "a/..." "b/..."` 头。使用 `^diff --git a/` 计数会漏掉这些文件，不能据此判断 GitHub Diff 截断。文件头应按 `^diff --git ` 计数，并与实时 `changedFiles`、REST 唯一 `filename` 数量及 exact Base/Head 的 `git diff --name-only` 交叉对账；只有这些证据仍不一致时才进入本地完整 Diff fallback。

<a id="exp-013"></a>

## Shutdown 与资源发布的同锁门禁

- 网络 listener、文件句柄或后台任务可能在关闭检查之后才完成创建时，仅在 shutdown 路径中 snapshot 并关闭已发布资源并不充分。资源发布点必须在与关闭标志相同的同步边界内再次检查状态；若关闭已先发生，应关闭尚未发布的局部资源并返回稳定的 closed 错误。并发回归测试应确定性控制锁和事件顺序，分别覆盖“资源先发布”和“关闭先发生”，不能只依赖概率 race 循环。

<a id="exp-016"></a>

## GitHub Actions 中 Go 工具的锁文件门禁

- Sonar `githubactions:S8545` 不把 `go install package@固定版本` 视为仓库锁文件约束。CI 安装 Go 工具时，应让版本来源于已提交的 `go.mod` / `go.sum`：适用时使用 `go install -mod=readonly package`，或在 Go 1.24+ 模块中声明 `tool` 并通过 `go tool` 调用。验证时要在 workflow 的实际模块目录执行安装，核对二进制模块版本、`go.mod` / `go.sum` 未被改写，并以新 Head 的 Sonar quality gate 与 open issues API 复检，不能只凭本地命令成功判断规则已清除。

<a id="exp-018"></a>

## 无 check 模式格式化器的只读门禁

- 格式化器没有只读检查模式时，应在临时镜像中执行格式化，再用 `git hash-object --path=<原路径>` 比较原文件与临时文件，使比较遵循仓库 clean filter，并证明 LF、`core.autocrlf=true` 的 CRLF、格式差异和 formatter 非零退出四类场景都不改变源文件字节或 Git 状态。文件枚举应先写入临时清单并检查退出码；`set -e` 不保证 process substitution 或循环输入端的生产者失败会传播，直接写成 `while ...; do ...; done < <(git ls-files ...)` 可能把不完整枚举误判为通过。

<a id="exp-021"></a>

## 离线 Git 证据与状态迁移门禁

- 离线验证器允许历史 PR Head 对象缺失时，不能同时把记录的 Head SHA 当作无需核验的自由字段。应将不可变 Base/Head/merge 身份固定到独立常量或等价可审计清单，并用“格式合法但对象不存在”的变异证明字段漂移仍会失败；对象缺失只能跳过依赖对象内容的附加检查，不能跳过身份检查。
- GitHub Actions run ID 是数字不等于它证明了目标提交。状态提升依赖 exact-main 成功证据时，必须把 run 绑定到 `conclusion=success`、exact Head SHA、目标分支和事件类型；若基础校验必须离线，应提供状态提升时必跑的 live-evidence 门禁，不能让任意成功 PR run 与另一个失败 main SHA 拼接为通过。
- 生命周期 self-test 的 mutation 不得依赖当前文本仍处于某个旧状态。每个 mutation 应显式构造矛盾、检查替换确实发生，并从所有允许的基线状态运行；否则 `pending → passed`、`implemented → verified` 等合法迁移会使替换成为 no-op，反而让必跑自测阻断状态机前进。
- 状态提升同时受多条祖先关系或多个证据字段约束时，失败路径齐全仍不能证明迁移可达。必须用仓库真实 Git 图构造至少一条正向状态：verification ref 严格后继 merge、`baseline_ref` 等同步字段推进后整体验证无错误；同时保留旧 baseline 被拒绝的回归。若成功依赖多字段原子更新，应在状态字段附近和可执行 gate 中写明同一合同。

<a id="exp-026"></a>

## Force push 后的审批与 CI 证据失效（ruleset 门禁）

- `validated_at: 2026-10-10`、`validated_ref: oceanbase/powercontext PR #1918`（`ae1edc48` force push 为 `d508f280`）。挂在被重写掉的历史提交上的 APPROVED 不再计入门禁：`reviewDecision` 回到 `REVIEW_REQUIRED`、`mergeable_state=blocked`，即使 `dismiss_stale_reviews_on_push: false`（该参数只管普通 push 保留旧审批，不管审批所在提交本身已不在历史中）。force push 后旧 Head 的绿色 CI 一律不得作为新 Head 的验证证据；新 Head 的 checks 需重新等待，必要时先在本地 exact 新 Head 副本跑关键测试填补缺口。对线程的 `in_reply_to` 回复不受 Head 变化影响（GitHub 自动映射到新 Head），但仍须核对新 Head 是否已改变被讨论的前提。

<a id="exp-036"></a>

## 「已接入 CI、不再跳过」的声明要同时核三步，且以 CI 运行结果为准

- `validated_at: 2026-10-17`、`validated_ref: oceanbase/powercontext PR #2025`（head `b08d0970`，run 39016923382 / job 117350868902 与 117350869128）。
- 现象：作者新增一个 dedicated job 让原本被 `importorskip` 跳过的用例真实执行，workflow 与新文档都写了「without skips」。只看 workflow 文本会得出「缺口已闭合」，但同一 head 上该 job 实际失败（新增的 OceanBase 验收步骤 20 s 内 `/health/live` 未就绪）。判据顺序：① 读 job 日志的真实命令与计数（本例 `20 passed in 65.94s`）；② 读该 job 阻止跳过的机制是否真能拦住；③ **用该 head 的 check 结论收口**——workflow 里写了步骤 ≠ 步骤跑绿。
- 阻止跳过机制的有效性判定：对「用 JUnit 断言拒绝 skipped」的写法，实测 pytest 在模块级 `pytest.importorskip` 失败时会写出一条 `<testcase classname="" name="<module>"><skipped message="collection skipped">`（探针 `oceanbase-powercontext-pr-2025/probes/junit-skip/report.xml`），因此「整个文件零用例」也能被拦住；但若收集阶段**没有任何节点**（如 `-k` 过滤后为空）则 XML 里根本没有该文件的 testcase，此时必须像本仓 `scripts/run_atomic_memory_clean_migration.py` 那样先做 `--collect-only` 并逐文件断言节点非空。
- 依赖闭环按 lock 判，不按 extra 声明判：`pyproject.toml` 的 `tracing-otlp` extra 只列了 exporter，但 `uv.lock` 中该 exporter 依赖 `opentelemetry-sdk`，所以只装该 extra 也能 import sdk；只看 pyproject 会误判成「job 会因缺 sdk 而挂」。
- 超时型用例失败要区分「慢启动」与「启动阻塞」：本例超时分支只打印了子进程输出（仅一行能力横幅），没有退出码与日志尾部，无法归因；写出 Finding 时应把这一可观测性缺口单列为修复方向，而不是替作者断言根因。

<a id="exp-048"></a>

## `pull_request` 的 CI 跑在 merge 树上：head 树自检通过不等于 CI 通过

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2031`（head `b0e379f6`，base `8567df45`，merge `04a53f41`）、`applies_to: 任何由 `pull_request` 事件触发、且门禁读取仓库内文件内容（版本号、契约摘要、生成物一致性）的 CI`、`recheck_when: workflow 显式 checkout `github.event.pull_request.head.sha`，或改用 `merge_group`/`push` 触发`。
- 现象：head 树自检 `make version-check` 通过（`openapi/powercontext.yaml` 与文档都是同代版本），但 CI 的 `quality` job 报 `Release version mismatch ... (expected 1.4.0)`。原因是 Actions 默认检出 `refs/pull/<N>/merge`：merge 树里 master 侧已把版本抬到 1.4.0，而 PR **新增**的那几行仍写着旧版号，于是 head 树自洽、merge 树不自洽。
- 判据：把三方都取出来比对，而不是只看 head —— `git show <head>:<file>`、`git show refs/pull/<N>/merge:<file>`、`git show <base>:<file>`。差异只在「PR 新增/修改的区域」出现时，说明是 PR 侧文本需要跟随 base 刷新（本例 rebase 后 `make version-bump` 即自动改写），不是实现缺陷。
- 报告口径：写清「head 树通过 / merge 树红」，并给出触发条件（base 侧已升版）；不要说成「CI 与本地不一致」这类无根因的表述。同类门禁还有契约摘要、生成代码一致性、翻译同步等一切「拿仓库内文件内容互相比对」的检查。

<a id="exp-050"></a>

## 同名 CI job 分属不同 workflow，`validate` 这类通用名必须按 `workflow_name` 取值

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2052`（head `6f136409`）、`applies_to: 引用 CI job 作为行为证据、且 job 名是 `validate` / `tests` / `quality` 这类跨 workflow 复用的通用名`、`recheck_when: workflow 重命名或合并`.
- 现象：同一 head `6f136409` 的 check-runs 里有两条 `validate`——`Skill guidance validation`（success）与 `E2E harness`（当时 queued）。若按 job 名取「最新一条」会拿到 queued，按「success 那条」又会把技能校验当成 `make harness-check` 的证据。取法：`gh api repos/<o>/<r>/actions/jobs/<job_id> --jq '.workflow_name'`，或 `gh api .../commits/<sha>/check-runs` 后按 `workflow_name` + `name` 分组再取最新 `started_at`。
- 判据补充：`gh pr checks` 与 check-run 名都不含 workflow 归属，报告里必须写清「哪个 workflow 的哪个 job」，否则「CI 绿」无法复核。本例正确证据是 `E2E harness / validate`（job 118485927443）日志里的 `make harness-check` → `271 passed`。

<a id="exp-052"></a>

## `mergeable_state=dirty` 要给出冲突文件，别只写"有冲突"

- `validated_at: 2026-10-30`、`validated_ref: oceanbase/powercontext PR #2031`（head `0cab7347`，base `fe50f894`）、`#2189`（head `939167b3`，master `4af95ce2`）、`applies_to: 需要说明"为什么不能合并"并且要落到可执行动作的报告`、`recheck_when: 改用 merge queue，或 GitHub 的冲突判定语义变化`。
- 取法（无需 checkout）：`git merge-tree --write-tree --name-only <base> <head>` —— 第一行是合并结果的 tree OID，随后直接列出冲突文件；本例输出 `e2e/bub/tests/test_harbor_job_config.py`（`CONFLICT (content)`），与 REST 的 `mergeable=false / mergeable_state=dirty` 互相印证。
- **`merge-tree` 的退出码必须单独捕获，不能被管道吞掉**：`git merge-tree ... | head -5; echo $?` 打印的是 `head` 的状态（恒 0）。2026-10-30 复核 #2189 时即因此把「有冲突」读成「干净」。正确做法是先重定向到文件再读 `$?`（`git merge-tree --write-tree a b > out 2>&1; echo $?`），并同时看输出里是否出现 `CONFLICT` 与 `100644 <oid> 2/3 <path>` 的冲突阶段行。`--write-tree` 有冲突时退出码为 1，tree OID 仍会被打印，所以「第一行有 OID」不能作为无冲突的证据。
- **PR 刚合入会让 `merge-tree` 报 add/add 假冲突**：同一轮里 master 从 `838f726c` 前移到 `4af95ce2`（#2189 的 squash 提交），此后再对仍标记为 open 的 #2189 跑 `merge-tree` 会得到 `CONFLICT (add/add)`——原因是同一批文件在两侧都以「新增」出现。判据是先查 `GET /pulls/<N>` 的 `state`/`merged_at`；`merged=true` 时该冲突只是「已经合过」，按「PR 已离场」跳过，不得当成回归或新 Finding。报告里 master tip 必须在同一轮内重取，不能沿用几十分钟前的值。
- 报告口径：合并维度写"存在冲突 + 文件名 + 需先同步 base"，不要与代码 Finding 混在一栏（冲突是治理状态，不是缺陷定级）。

<a id="exp-060"></a>

## 只有 lockfile 变更的依赖 PR：红 job 先按"同 workflow 相邻样本"归因，再谈因果

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #2141`（head `cd1ece6a5c`，唯一变更 `uv.lock`：uv 0.11.26→0.13.4 + 三处环境 marker 被删）、`applies_to: dependabot / renovate 之类只动 lock 或版本串的 PR，及其上出现的单点红 job`、`recheck_when: 方法类，长期有效`。
- 手法：取该 workflow 最近十余次 run 的全部 job 结论并排（`actions/workflows/<id>/runs` + `runs/<id>/jobs`），看"这个 job 名是否只在当前 head 红"。本轮 13 个样本里只有 PR head 红、base 与相邻 PR 全绿 ⇒ 单点样本不足以归因，也不能直接判抖动。
- 再看失败形态：本例是 `FAIL exit=124` + `Timeout (0:02:00)`，栈停在**首个** seekdb case 的 fixture setup（`asyncio.run` 里），不是断言、不是导入错误 ⇒ 属环境/引擎启动类，而不是 lock 语义问题。
- marker 被删要单独判语义：`importlib-metadata → zipp`、`opendalfs` / `powercontext-connector-opendal` 的 `python_full_version` 约束消失，需要回到清单确认真正的门在哪（本仓是成员 `requires-python = ">=3.12,<4.0"` 与根 `pyproject.toml` 的 dev 依赖 marker）——并用同 head 的 `tests (3.11, unit)` 结论反证低版本没被带坏，而不是凭 diff 猜。

<a id="exp-081"></a>

## 依赖 bump PR 要同时扫复合 action：dependabot 只覆盖 workflow

**现象**：5 个 dependabot 的 `build(deps): bump <action> from x to y` PR，diff 里每个文件都合理，
SHA 也确实是目标 tag（annotated tag 需 `git/tags/<sha>` 再解一层到 commit），但同一个 action 在仓库里仍有旧版本 pin。

**判据**：不要只读 diff。用固定 base 做**全仓计数**：

```bash
git grep -c "<owner>/<action>@" <base> -- '.github/'            # 每个文件几处
git grep -h -o "<owner>/<action>@[0-9a-f]\{40\} # [^ ]*" <base> -- '.github/' | sort | uniq -c
```

把「diff 覆盖的处数」与「全仓处数」对账。本轮实例：`astral-sh/setup-uv` 8 处（workflow 7 + 复合 action 1），
PR 只改 7 处；`actions/setup-python` 5 处（workflow 4 + 复合 action 1），PR 只改 4 处。漏掉的文件都是
`.github/actions/<name>/action.yml` —— dependabot 的 github-actions 生态系统扫描 `.github/workflows/**`，
复合 action 的 `uses:` 需要人工同改。

**影响要先量化再定级**：数一遍 `uses: ./.github/actions/<name>` 的调用次数（本轮 27 次 / 8 个 workflow），
再查被漏掉的版本里有哪些行为修复（本轮 setup-uv v10.3.1 的「并发上传同一 cache 的
`Unable to reserve cache with key ... another job may be creating this cache` 告警」）。只有落在
「有明确收益的局部维护问题」时按 P2，不要写成「依赖升级不完整 → P1」。

**门禁通常抓不到**：仓库若只有「pin 必须是 40 位 commit」这类不可变校验（本轮 `scripts/check_workflow_actions.py`
即如此，且被 `make check` 调用），旧 pin 依然是合法 pin，CI 全绿也能合入。判「CI 能兜住」之前先读那个脚本的断言范围。

关键词：`validated_at: 2026-10-26`、`validated_ref: PR #2242 head 7385ca95960e1eef9d8f709aaaa9106f903b8150`、
`PR #2241 head 701d5f62a63b15ffe890d85ba333539ee557615b`（base `31ecdd61`）、
`applies_to: 用复合 action（`.github/actions/**/action.yml`）承载 `uses:` 的仓库`、
`recheck_when: dependabot 开始覆盖复合 action、或仓库把一致性校验并入 CI`。

<a id="exp-085"></a>

## 跨 PR 撞号：`managed_digest` 一致、两边 CI 全绿、迁移测试全绿都不构成反驳

同一个仓库里有多个 OPEN PR 各自"新增一个迁移 revision"时，撞号不会在任何单 PR 的 CI 里暴露：两边的
`managed_digest` 都和各自 base 自洽，迁移测试（`test_migration_revision_names` / `test_full_server_migrations` /
`test_portable_storage_migration`）也都会全绿——因为它们只校验"本 PR 的 revision 与其 manifest 自描述一致"，
不校验"这个名字在别的分支上是否已被占用且内容不同"。

`2026-10-29` 实测（#2192 head `27d499e0` ↔ #2270 head `dd80249b`）：两个 PR 都新增 `v1_4_1_005`，
`server_resources/manifest.json` 里同名字段的 `sqlite_fingerprints` 分别是 `2e24be9f…` 与 `92eaad28…`；
同一轮里 #2004 `93ca5dfa` ↔ #2246 的 `v1_5_0_001` 同样撞号（`4817f09f…` vs `62ac36b0…`）。

判据与做法：
- 判据只有一条：**跨 PR 比对同一 revision 名的 `sqlite_fingerprints`（以及 `affected_objects`）**。
  名字相同而 fingerprint 不同 ⇒ P1，先合者定义 baseline，后合者必须 rebase 重新生成迁移。
- "两 PR 各自 CI 全绿"是这类问题的**典型反面证据**，不能当反驳；同理 `managed_digest` 相等只说明与自身 base 自洽。
- 审查单 PR 时就要扫一遍同批次其它 OPEN PR 的 `server_resources/manifest.json`（`gh api` 取 raw 即可，无需 checkout），
  成本远低于等 merge 后才发现迁移链分叉。
- 同一 PR 可能在两处都被记为撞号（本 PR 视角 + 对方视角），评论要写清"谁是先合者"取决于合并顺序，
  不要断言某一方"必须改"，而是要求先合者冻结、后合者 rebase。

关键词：`validated_at: 2026-10-29`、`validated_ref: #2192 head 27d499e0 ↔ #2270 head dd80249b`、
`applies_to: 任何「多 PR 并行新增迁移 revision」的仓库`、`recheck_when: 合并顺序变化后需重核`。

<a id="exp-086"></a>

## 汇总门禁类 PR：先确认它在 ruleset 里是不是 required check

把多个 workflow 收敛成单一 orchestrator + 一个 `ci-result` 汇总 job，看起来是"加了一道门"，但如果 ruleset 的
`required_status_checks` 是空的，这道门在合并上没有任何约束力——合并阻塞只来自 approval 数量。

`2026-10-29` 实测（#2285 head `b84f6681`）：`master.yml` 的 `ci-result` 的 `needs` 覆盖全部 job，
`tests/test_workflow_actions.py` 还用 `set(main["ci-result"]["needs"]) == set(main) - {"ci-result"}` 固化了这条契约，
但 ruleset 9930477 `required_status_checks=[]`、`required_approving_review_count=2`、`bypass_actors=OrganizationAdmin:always`。
同 PR 顺带修的 `upgrade-release-gate`（区分 not-required 与 missing acceptance）也要等该 job 变成 required 才对外生效。

判据与做法：
- 审这类 PR 时把"门禁是否真的 required"作为独立检查项：`gh api repos/{o}/{r}/rulesets/{id}` 看
  `required_status_checks` 与 `bypass_actors`，别只看 job 是否全绿、`needs` 是否齐全。
- 顺手核 job-level `if:` 的取消语义：写成 `if: always()` 的上游门禁在被取消的 run 上会重新起 runner 并必然失败
  （#2004 的 run `40857668988` 于 10:27:47Z 取消、`upgrade-acceptance=skipped`、gate 于 11:20:30Z 重起后
  `test "$UPGRADE_RESULT" = success` → exit 1）。这类红与代码无关，归因前先看上游 job 的 `result` 是否为 `cancelled`。
- 结论要落到"合并后在 ruleset 补 required check"这类可执行 follow-up，而不是泛泛说"门禁不完整"。

关键词：`validated_at: 2026-10-29`、`validated_ref: #2285 head b84f6681`、
`applies_to: CI 编排收敛 / 汇总门禁类 PR`、`recheck_when: ruleset 更新后`。

<a id="exp-096"></a>

## 覆盖类清单要按"元素"对账，不能按"摘要"对账；夹具从被测清单同源生成时 CI 绿是自证的

场景（`oceanbase/powercontext` #2220，2026-10-31）：桌面端新增 `get_stats` 操作，PR 同时改了四处——
`transport/operations.json`（加 `get_stats` 并换 `contractSha256`）、`connections/compatibility.json`
（资格记录）、`session.rs`/`discovery.rs`（门控）、`Statistics.tsx`（面板）。head 上 81 个 check 全 success，
PR 正文的清单也自洽，但把 gate 的求值链读出来结论是**面板恒不可用**：

- `session.rs` 判 `profile.compatibility == Some(&c.id)` 且 `contract["contractSha256"] == Some(&c.contract_sha256)`；
- `discovery.rs` 再判 `qualification.operations.contains(operation)`，`supported_operations()` 只收 `Qualified`；
- 改后唯一摘要落在 `sqlite-source-artifact-87b6fae2-v1` 这条记录上，它的 `operations` 只有 11 项、
  **不含 `get_stats`**；PR 侧新增的四条 `sqlite-stats-*` 在合并解析（head 与 master 取并集）后被 master 的四条
  `sqlite-artifact-*` 覆盖掉，摘要不同，压根进不了候选。

为什么 CI 没拦住：`desktop/tests/fixture_qualification.py` 用 `operations.json` **同源合成**资格记录，
`ui/tests/statistics.test.tsx` 手写 `supportedOperations` 常量。测试断言的是"给定资格记录后 UI 能渲染"，
而不是"随仓库发布的 `compatibility.json` 覆盖了新增操作"。

做法：

1. 覆盖判断一律展开成集合对账：把"需求清单"（`operations.json` 里新增/存在的 key）与"每条能被门控命中的
   记录的 `operations` 并集"分别导出，做差集；命中门控的条件（摘要相等）也要参与，不能对全部记录求并集。
2. 对账前先确定"合并后的真实文件内容"：把 head 与 master 的 JSON 按解析规则合并后再比对。只看 PR diff 里
   "新加了哪几条"会得到相反结论（本例 diff 里那四条是 `sqlite-stats-*`，合并后生效的是 `sqlite-artifact-*`）。
3. 检查夹具来源：若测试夹具从被断言的同一份清单派生（同源生成/手写常量），把 CI 绿降级为"无信息"，
   必须补一条"发布物自检"（读仓库里的 `compatibility.json` 断言覆盖）才算证据。
4. 结论表述要区分"功能没实现"与"被门控挡住"：本例代码与 UI 都在，只是永远拿不到 `Qualified`，
   所以是"新功能恒不可用"而不是"新功能有问题"，前者优先级更高（用户看不到任何降级提示）。

关键词：`validated_at: 2026-10-31`、`validated_ref: powercontext #2220 head 9e7d8d8d / master 0b0a1c71`、
`applies_to: 任何用"资格/白名单/兼容性清单"做运行期门控的仓库`、
`recheck_when: 门控从"记录级"改成"操作级并集"，或夹具改为消费产品侧清单时`。

<a id="exp-097"></a>

## workflow 里 suite job 的 `skipped` 可能是「被别的 job 级联跳过」，不等于路径未命中

现象：PR 明确改了某个 suite 的目录，该 suite 的 job 却是 `skipped`，而相邻的 `docs-tests` 等正常执行；
读 `if` 才发现多数 suite job 同时依赖"路径选中"和"测试矩阵结果"，任一 `tests (*)` 红就会把所有 suite job 一起 skip。

判据（`oceanbase/powercontext` #2349，2026-11-01，run 41270509778）：

- `dify-tools` 的 `if` 为 `needs.quality.result == 'success' && contains(fromJSON('["success","skipped"]'), needs.tests.result)
  && fromJSON(needs.quality.outputs.suites || '{}').dify`；
- 该 run 的 `CI preflight`（job 名 `quality`）日志里 `scripts/ci_changes.py` 打印 `"dify": true`，路径确实命中；
- 但 `tests (3.12, e2e)` 红 ⇒ `needs.tests.result == 'failure'` ⇒ `dify-tools` 被 skip。

做法：

1. job 为 `skipped` 时先取"suite 选择结果"（本例读 preflight 日志的 JSON 输出），再取 `needs.*.result`，
   两者合起来才能判断是"未命中路径"还是"被级联跳过"。
2. 后者对该 PR 的改动等于**零覆盖**：不能在结论里写"该 suite 绿"，也不能把它当作"已验证"。
   需要补本地实跑、或引用另一 head（同一 PR 的后续 run）里该 suite 真正执行的记录。
3. 级联根因常与本 PR 无关（本例是 zcode e2e 超时）。归因该红可按 R05 处理，但**覆盖缺口不能因此消失**，
   要在收尾对账里单列。
4. **`cancelled` 也在这个白名单之外**（2026-11-08，powercontext #2526 head `105e7a94`，run 42390978248：
   `cancel-in-progress: true` 被后续 run 顶掉，`tests (3.12, e2e)` 为 `cancelled`）。此时 `CI preflight` 仍打印
   全套 `"<suite>": true`，但 30 个 suite job 全 `skipped`，sink job 连 check run 都不产生。判断顺序因此是：
   先看 `commits/{head}/check-runs` 里失败项是"红"还是"取消"，再看 run 的 `conclusion`；`cancelled` 既不是失败
   也不是覆盖证据，且会推翻上一轮"CI 已覆盖"的结论。同名 job 在不同 workflow 里带前缀（`harness-validation / Acceptance (oceanbase)`），
   按精确名 grep 会误判为"没有这个 job"。

关键词：`validated_at: 2026-11-01`、`validated_ref: powercontext #2349 head 007f5f8b`、
`applies_to: 用 `needs.<job>.result` 做 suite 门禁的 GitHub Actions 工作流`、
`recheck_when: suite job 的 `if` 去掉对测试矩阵结果的依赖，或改成 `always()` + 独立 gate 时`。

<a id="exp-099"></a>

## fork PR 的 workflow run = `action_required` 时，「0 个 check run」不是 CI 通过，是等维护者批准

现象：PR 有最新 head，但 `GET /commits/<sha>/check-runs` 返回 `total_count: 0`（或只有
`CI preflight` 一条 pending），PR 页面也没有红叉。用 `mergeable_state` 判是 `blocked`，看起来只是缺审批。

判据（`oceanbase/powercontext` #2307，2026-11-01，head `7f2bcf27`，fork = `ztelur/powercontext`）：

```bash
gh api "repos/{owner}/{repo}/actions/runs?branch=<head.ref>&per_page=10" \
  --jq '.workflow_runs[] | "\(.name) \(.head_sha[0:8]) \(.status) \(.conclusion)"'
# Gateway   7f2bcf27 completed action_required
# Main      7f2bcf27 completed action_required
```

`action_required` = 该 run 已创建但在等有写权限者批准（fork PR 的首次/每次推送审批）。此时：

- 没有 check run 落地，所以"检查列表为空"与"检查全绿"在 API 上看起来一样，但含义相反。
- 也不能把 `action_required` 当作"CI 失败"归责作者——它是流程未执行。
- 收尾对账必须写成「验证证据：具体缺口（该 head 无任何 CI 结果，Gateway job 未执行）」，并按 `R05` 判断
  是否需要本地补证据；不要用 base 分支配对掩盖。

做法：

1. 判 `head.repo.fork` 与 `actions/runs?branch=` 的 `conclusion`，再看 `check-runs`；三步任一缺失都可能误判。
2. 见 `action_required` 时，先看同一 PR 是否**曾有**已批准的 run（`attempt`/更早 head），只有旧 head 的绿
   不能迁移到新 head。
3. 需要在本轮给结论时，用本地可执行验证补足（Rust 用 `cargo test --locked`，Python 用镜像 venv），并把
   "未执行 CI"单列为缺口，不写成"CI 通过"。

关键词：`validated_at: 2026-11-01`、`validated_ref: powercontext #2307 head 7f2bcf27（fork ztelur/powercontext）`、
`applies_to: 来自 fork 的 PR，或需要审批才能运行 workflow 的仓库`、
`recheck_when: 仓库启用 fork workflow 自动运行、或改用 `pull_request_target` 批准策略时`。

<a id="exp-109"></a>

## 本机 `.venv312` 的 `asyncio.run` 整体挂死：asyncio 探针改在 WSL 侧跑（2026-11-06 实测）

`{REPO}\.venv312\Scripts\python.exe`（3.12.13）里 `asyncio.run(asyncio.sleep(0, result=42))`
**永不返回**，`timeout` 到点被 kill（exit 124）。`WindowsProactorEventLoopPolicy` 与
`WindowsSelectorEventLoopPolicy` 表现相同；不涉及网络、不涉及任何项目代码。因此「探针没输出」不要先怀疑
被测代码——先跑这条最小用例。

- 判据：`python -c "import asyncio;print(asyncio.run(asyncio.sleep(0,result=42)))"` 挂住即环境问题。
  同一条在 WSL 侧 `{WORKSPACE}\review\_shared\venv-wsl`（3.13.11）立即返回。
- 影响：任何 `asyncio.run` / `pytest` 异步用例 / ASGI 探针在本机该 venv 下都会「无输出且不退出」；
  与项目无关（master 工作区同样如此）。取证改在 WSL：`PYTHONPATH=/mnt/d/.../src`，宿主路径换 `/mnt/d/`。
- 挂起判定不能靠 `asyncio.wait_for`：当被测协程吞掉取消（Starlette `BaseHTTPMiddleware` 会）时
  `wait_for` 自身也会挂住。用 `asyncio.wait({task}, timeout=N)` 拿 `pending` 集合，print 后 `os._exit(0)`
  收尾，避免解释器退出时再等那些任务。
- 不要把 WSL venv 的 starlette/fastapi 版本差异当成行为结论：本轮 WSL 侧是 starlette 1.10.0 / fastapi 0.162.0，
  宿主 `.venv312` 是 1.3.1 / 0.139.2；`BaseHTTPMiddleware` 的「无响应即 RuntimeError」在两版都存在，
  但涉及版本敏感行为的结论要写明工具链版本。

关键词：`validated_at: 2026-11-06`、`validated_ref: 本机 `.venv312` 3.12.13 / WSL venv 3.13.11`、
`applies_to: 本机 Windows 侧所有 asyncio 探针`、`recheck_when: 更换工作区 venv 或 Python 版本`。

<a id="exp-110"></a>

## head 上的「已解决」不覆盖合并结果：摘要类门禁要按 merge-tree 结果树复算（2026-11-07 实测）

**现象**：线程回复声称已修、head 上摘要与声明值相等、该 head 的 CI 全绿；PR 随后变成 dirty，冲突文件恰好就是承载摘要的那几个清单。此时「取我们/取他们」两种解冲突方式都只对应各自的树，合并结果上摘要必然失配，门禁在合并后的首跑就红。

**做法**：
- 取结果树与冲突清单：`git merge-tree --write-tree --name-only <base-tip> <head>`（第一行是结果树 OID，其后是冲突文件）。只读，不需要 checkout。
- 看冲突块：`git show <结果树>:<path>`，确认冲突是否正好落在摘要行/资格记录上。只有摘要行冲突时最危险——看起来"改一行就行"，实际两个候选值都不对。
- 摘要一律按结果树复算：结果树的值通常是**第三个值**，既不等于 head 也不等于 base。「head 自洽」不等于「合并结果自洽」。
- 行为反证要跑两侧：把结果树 `git archive` 到 `probes/`，按 A 侧解冲突跑真实入口，再按 B 侧解冲突跑一次，两次都失败才能写"两侧都不对"；把声明改成复算值再跑一次，必须 exit 0，才能证明那个值是对的。
- 报告措辞：head 范围只能写"该 head 上已修复"；合并结论必须独立写"合并结果树是否自洽"。

**实测（#2270，head `8464c739` / master `9a424e77`）**：
- `managed_digest`：head `6f826ce3…`（244 个受管文件，= 声明值）、master `53f1fd23…`（237）、`merge-tree` 结果树 `c4c51692…`（244）；文件集差异只有 master 侧更新的 3 个 `builtin/code/*.py`，来源是 #2425 的 merge commit `b22de226`。
- 把结果树解出来跑 `python scripts/upgrade_release_gate.py`：保留 PR 侧摘要 → `Upgrade release gate failed: Persistence changed (file set or content; CRLF/LF normalized)` exit 1；保留 master 侧 → 同样 exit 1；改成 `c4c51692…` → exit 0。
- 同一 PR 的契约摘要：head `e958f47c…` / master `9aabe256…` / 结果树 `5e371014…`，而结果树的 `compatibility.json` 48 条记录里没有 `5e371014…`。

关键词：`validated_at: 2026-11-07`、`validated_ref: oceanbase/powercontext #2270 head 8464c739 + master 9a424e77`、
`applies_to: 任何带摘要/资格记录清单、且已进入 dirty/CONFLICTING 的多轮 PR`、
`recheck_when: 摘要算法、受管文件集或合并策略变化`。

<a id="exp-111"></a>

## OOM/资源类缓解措施必须在同一 head 的构建日志里验证「配置生效 + 仍然失败」两段

现象：PR 用一个配置项宣称修掉 exit 137（OOM），审查时容易只看 diff 是否合理就放过。

判据与取证（2026-11-07 实测 oceanbase/powercontext #2432 的 `website/next.config.mjs`）：

1. 先取该 job 的完整日志（`gh api repos/{owner}/{repo}/actions/jobs/<job_id>/logs`），确认**配置被读取**——
   Next.js 会在构建开头打印生效配置（本次是 `· cpus: 2`），并在使用处打印实际并发（`Collecting page data using 2 workers ...`）。
2. 再确认**同一段日志里仍然失败**：本次后面紧跟 `Killed` → `[ELIFECYCLE] Command failed with exit code 137` →
   `make: *** [Makefile:293: docs-test] Error 137`。两者同时成立 ⇒ 缓解措施对该 runner 无效，不能按"已修复"合并。
3. 退出码语义要先分清：127 = 命令不存在（工具安装问题），137 = SIGKILL（多为 OOM 或超时被杀），
   124 常见于 `timeout` 包裹。不要把它们都写成"构建失败"。
4. 只降并发数不等于降峰值内存：单次 page data 收集的内存占用与 worker 数无关时，需要
   `NODE_OPTIONS=--max-old-space-size`、换更大内存的 runner，或把该改动拆出 PR。

相关：`review.md` `R05`（工具结果异常先归类 PR/基线/环境）与 `R06A`（测试与缓解措施的真实性）。

关键词：`validated_at: 2026-11-07`、`validated_ref: oceanbase/powercontext #2432 head 3736c1f2（run 42268108682 / job 128070216681）`、`applies_to: 任何以配置/参数调整宣称修复 OOM、超时或资源耗尽的 PR`、`recheck_when: 目标 runner 规格、构建工具版本或日志格式变化`。

<a id="exp-112"></a>

## CI 分步预算与作业上限是两个数：改 workflow 必须把两者对账

现象：把一个大步骤拆成多个带 `timeout-minutes` 的步骤后，各步上限之和可能超过 job 级上限；
此时真正的失败形态是**作业在最后一步中途被取消**，而 `if: always()` 的汇总/门禁步骤根本不会执行，
于是"选中的工作必须成功"的断言形同虚设，日志只显示 job 超时。

判据：把每个步骤的 `timeout-minutes` 与 job 的 `timeout-minutes` 相加对账，并额外计入没有独立步骤的
teardown、证据上传时间。注释里的"保持既有预算"不算证据——本次 #2526 注释这么写，实际由 65 分钟涨到 80 分钟。

相关：`review.md` §2.1（执行预算）与 `R06A`（把断言放进能失败的路径）。

关键词：`validated_at: 2026-11-07`、`validated_ref: oceanbase/powercontext #2526 head 10173320 / base 9a424e77`、`applies_to: 任何在 reusable workflow 里拆分带超时步骤的 PR`、`recheck_when: 作业或步骤超时配置变化`。

<a id="exp-114"></a>

## 新用的序列化关键字要对照依赖下限：CI 锁的版本不等于声明支持的版本

现象：PR 用 `Field(exclude_if=lambda v: v is None)` 让可选字段在序列化时整体消失，CI 全绿、PR 自带用例也全绿，
但 `pyproject.toml` 声明的是 `pydantic>=2.10,<3`，而 `exclude_if` **只有 2.12+ 才实现**；在 2.10/2.11 上它被当作
多余的 Field 参数丢弃，只发一条 `PydanticDeprecatedSince20`（Extra keys: 'exclude_if'），字段照常输出 `"field": null`。

判据与取证（2026-11-07 实测 oceanbase/powercontext #2296 head `fe761522`，`sources/models.py:78`）：

1. 先读 `pyproject.toml`/`uv.lock` 两处：`>=` 下限与 lock 实际版本常常相差多个 minor。lock 决定 CI 看到的语义，
   下限决定用户装到旧环境里的语义，两者不同就要单独验证。
2. 造一个**同 Python 系列的最低支持版本环境**（本次 3.13 + `uv pip install --no-deps pydantic==2.11.9 pydantic-core==2.33.2`；
   注意 3.14 上装旧 pydantic 需要现编 pydantic-core，会静默保留新版），再跑 PR 自带的用例。
   本次 2.11.9 下 `tests/test_source_locators.py` 直接 2 条红，断言正是 `assert 'locator' not in {...'locator': None}`。
3. 判断影响面要沿序列化函数走：`model_dump_json()` 参与去重的调用点（`review/service.py::_unique_sources`、
   `artifacts/merge.py`、`atomic_memory/reconciliation.py`）在旧版本上会得到不同的键 ⇒ 同一份数据在不同环境
   去重结果不同，属于跨环境不一致，不只是"多一个 null"。
4. 修法二选一并写清：抬下限到 `pydantic>=2.12,<3`，或用 `field_serializer` / `model_serializer` 显式跳过 `None`；
   并要求一条在最低支持版本上运行的用例。
5. **复核"已修"时按三点验收**（2026-11-08 实测 #2296 head `aa77ac80` 已修）：①下限版本下同一断言必须真的失败
   ——本例 `tests/test_source_locators.py:41` 用的是 `model_dump(mode="json")`（不带 `exclude_none`），2.11.9 下
   `2 failed`、2.12.0 下 `17 passed`，若断言写成 `exclude_none=True` 则新旧版本都绿、门禁形同虚设；②CI 必须真的
   执行该断言——本例 `master.yml:294-298` 用 `uv run --with 'pydantic==2.12.0'` 跑三个文件，`unit (3.11)` job 日志
   `97 passed` 才算证据，"新增了步骤"不等于"步骤跑过"；③三处锁文件（根 `uv.lock`、`e2e/bub/uv.lock`、
   `evaluation/uv.lock`）都要 ≥ 新下限，否则只在某一个子环境里被解析回旧版本。
   反向取证也可只用探针：同一探针脚本在 2.11.9 输出 `{'locator': None}`、2.12.0 输出不含该键，
   `inspect.signature(pydantic.Field)` 的 `exclude_if` 有无即版本分界。

相关：`review.md` `R06A`（测试真实性）与 `R01`（声明依赖属于 PR 前置事实）。

关键词：`validated_at: 2026-11-08`、`validated_ref: oceanbase/powercontext #2296 head fe761522（pydantic 2.11.9 vs 2.13.4）/ head aa77ac80（已修复核，2.12.0 97 passed）`、`applies_to: 任何新用 pydantic/jsonschema/framework 序列化关键字、或改契约可选字段编码的 PR`、`recheck_when: 依赖下限调整、pydantic 主版本升级或该字段的编码约定变化`。

<a id="exp-122"></a>

## 判定"该 head 的 CI 到底跑没跑"：先查同 head 的 run 数，再谈 cancelled 的成因

引用 CI 作证据前，`commits/{sha}/check-runs` 的 conclusion 计数只说明"有没有结论"，不说明"为什么没有"。规则是：
先用 `actions/runs?head_sha={sha}` 把该 head 的 run 全列出来——若同一 head 只有一条 run 且 `conclusion=cancelled`，
就不能把它读成"被后来的 push 顶掉"（那是 `cancel-in-progress` 的常见解释，前提是存在更新的 run）；此时它只是
"没有任何可判定结论"，属验证缺口，不是 PR 缺陷，也不是通过。

判读顺序：① `check-runs` 里各 job 的 conclusion 分布（`cancelled` / `skipped` / `failure` 分开数）；② 该 run 的
`status`/`conclusion`/`run_attempt`；③ `actions/runs/{id}/jobs` 里各 job 的 `started_at`/`completed_at`——同一秒内
一批 job 同时变成 `cancelled` 说明是运行级取消，而不是某条测试失败级联；④ 再查 `actions/runs?head_sha=` 判断是否
另有更新的 run 可引用。只有 ④ 找到更新的 run 时，才能说"旧 run 被新推覆盖"。

实测（2026-11-10，oceanbase/powercontext #2526 head `0eacec40`）：44 个 check 中 7 success、13 skipped、24 cancelled；
run 42776126403 `conclusion=cancelled`，`actions/runs?head_sha=0eacec40` 只返回这 1 条 ⇒ 无法归因，`tests (3.13/3.14,
unit|e2e)`、`Acceptance`、`upgrade-acceptance` 全为零覆盖。同一分支历史里另有 4 条 `cancelled`（`42646678849`、
`42630081073`、`42609231972`、`42604251063`），说明该分支的取消不是孤例，报告里要写成"该 head 无验收证据"而不是
"CI 通过"或"CI 被新提交顶掉"。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2526 head 0eacec40（run 42776126403）`、
`applies_to: 任何用 GitHub Actions 结果做合并证据的仓库`、
`recheck_when: 仓库的 `concurrency` 配置或 runner 池变更`。

<a id="exp-125"></a>

## license-eye 的豁免是按后缀列举的：新增图源后缀会让 CI preflight 整轮红

**现象**（2026-11-12，oceanbase/powercontext #2588 于 head `e5c5fa4a`）：Docs-only PR 新增 3 个 `.mmd`（Mermaid 源）
与对应 `.svg`，`CI preflight` 直接红：

```text
INFO Totally checked 3727 files, valid: 2654, invalid: 3, ignored: 1070, fixed: 0
WARNING Failed to determine the comment style of file: docs/assets/blog/.../memory-validation.mmd
ERROR the following files don't have a valid license header: (上述三个 .mmd)
```

**根因**：`.licenserc.yaml` 的 `paths-ignore` 逐条列举，只登记了 `**/*.svg` 与 `**/*.mermaid`
（后者注释写明 "license-eye cannot determine the comment style of Mermaid diagrams"），没有 `**/*.mmd`。
license-eye 对无法判定注释风格的文本后缀直接判 invalid，不会自动跳过。

**判据与处理**
1. 非 `.md/.json/.svg` 的新增资源（图源、录制、补丁、证书等）一律先比对 `.licenserc.yaml` 的
   `paths-ignore`，同名族不同后缀（`.mermaid` vs `.mmd`）是最常见漏点。
2. `invalid: N` + `Failed to determine the comment style` 同时出现，即可定性为「后缀未豁免」，
   而不是内容缺头；补头对无注释风格的后缀无效，正解是加 ignore 或改后缀。
3. 影响面按 `R-PC03` 读：preflight 红 ⇒ 全部 suite 级联 `skipped`，PR 新增的用例零执行，
   首轮结论里不得写「CI 已覆盖」。
4. 这类 finding 在发布前必须重新取 head：本次开头的 `-59` 行提交（删除 `.mmd`）在 20 分钟内落地，
   pre-publish 复检直接把 P1 作废，避免了错误行内评论。**门禁类 finding 的时效最短**。

**关键词**：`validated_at: 2026-11-12`、`validated_ref: oceanbase/powercontext #2588 head e5c5fa4a（run 43146850196 / job 130946562568）`、
`applies_to: 使用 Apache skywalking-eyes / license-eye 的仓库，与新增纯文本资源后缀相关`、
`recheck_when: .licenserc.yaml 改为通配目录级 ignore，或 license-eye 版本升级到支持自动识别新后缀`。

<a id="exp-128"></a>

## 「逐字节重放」类门禁要检查写入侧换行策略；适配器测试要先确认 `integrations/<host>` 的 import 源（2026-11-12 实测 #2529 / #2527）

**现象一（假缺陷：产品写入侧）**：`evaluation/.../report.py` 用 `Path.write_text(_json(payload), encoding="utf-8")`
写 `report.json` / `report.md` / `run-manifest.json`，而单测断言「重放产物与仓库内固定产物逐字节相同」。
在 Windows 跑 `pytest evaluation/memory/prepared_context_budget/tests` 稳定红 2 个用例，报
`assert b'{
 … }
' == b'{
 … }
'`（截断显示里看不出差异）。把生成物 CRLF→LF 后与固定产物
逐字节相同（本轮 2857 / 302 个 CRLF 对）⇒ 唯一差异是 `write_text` 未传 `newline="
"`。

**现象二（同一批失败里的假缺陷：断言侧路径拼写）**：另一条断言写 `str(tmp_path.resolve())`（Windows 反斜杠），
而被测代码刻意用 `as_posix()` 记录路径以保证记录与机器无关，两者在 Windows 必然不等。判「哪边错」的依据是
**记录侧要不要跨机器可比**：这里要，所以改断言而不是改产品。

**现象三（假缺陷：import 源）**：`tests/langgraph_adapter` 等用 `pytest.importorskip("powercontext_langgraph")`，
共享 venv 里装了一份**旧版**适配器 wheel。只把镜像 `src` 放进 `PYTHONPATH` 时，根包 `powercontext` 指向镜像，
但 `powercontext_langgraph` / `powercontext_langchain` / `powercontext_pydantic_ai` 仍来自 `site-packages`，
于是「注入文本仍是旧的 trust 句子」被当成 PR 的断言写错（3 个假红）。把这些包在镜像里的
`integrations/<host>/src` 前置进 `PYTHONPATH` 后 188 passed。

**判据与处理**
- 见到「逐字节 / 哈希相等」类断言在 Windows 红、Linux 绿，先按 `Path.write_text` 与 `open()` 文本模式的换行
  翻译定位，再判它是产品写入侧（要加 `newline="
"`）还是断言侧；只在 ubuntu 跑的 CI job 对该类门禁是零覆盖，
  必须按 `R15` 记为不可判定，不能写成「CI 绿所以没问题」。
- 跨包适配器/插件仓库里，`PYTHONPATH` 必须同时前置根包 `src` **和**每个被测分发包所在目录；判定方法与
  「镜像 + 共享 venv」那条一致，但对每个 `import` 进来的分发包各查一次 `__file__`，别只看根包。
- 同一批 Windows 红里，逐条区分「产品写入侧 / 断言侧 / import 源」三类，再决定是否定级；三类都可能与 PR
  改动无关，混在一起会整批误报。

**关键词**：`validated_at: 2026-11-12`、
`validated_ref: oceanbase/powercontext #2529 head 56114890、#2527 head 59205a11`、
`toolchain: Python 3.14.3 / pytest / Windows + core.autocrlf=true`、
`applies_to: 带「固定产物可重放」门禁的仓库；多分发包（集成适配器）仓库的镜像测试`、
`recheck_when: 该仓库把 evaluation-tests 换成多平台矩阵，或 report 写入改用 `Path.write_bytes`/`newline="
"``。

<a id="exp-138"></a>

## 判「CI 红是否与本 PR 相关」用另一 head 本地复跑同用例（2026-11-14 实测 #2550）

**现象**：#2550 只改 `integrations/` 下 61 个文件，但 `tests (3.11, e2e)` 红在
`tests/e2e/test_dream_usage.py::test_memory_dream_approval_embedding_usage_survives_replay_and_restart`
（实际 `{'requests':0,'input_tokens':0}`，期望 `1/7`）。路径上完全无关，但「无关」需要证据。

**核验**：同一提交内容在另一 PR head（#2628 镜像）上本地跑该用例 **6 passed**；`git diff --stat`
确认该 PR 未触碰 `tests/e2e/`、`src/`；再核 `Upgrade release gate` 红为
`UPGRADE_SELECTED=true` / `UPGRADE_RESULT=skipped` 的级联，不是新增失败。

**结论**：跨 head 复跑同一条用例是成本最低的排除法：同一份 `master` 基线、不同 PR head、
本地能过 ⇒ 红是环境或并发抖动，不是该 PR 引入。写进结论时要给出两边的命令与计数。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2550 head 993b682d`、
`applies_to: 改动面与失败用例路径不相交、但 CI 仍红的 PR`、
`recheck_when: 仓库把 e2e 拆成按模块触发的分片任务`。

<a id="exp-143"></a>

## 新 CI 作业「时长异常短」不等于空跑，取 job 日志的 `collected/passed` 行（2026-11-14 实测 #2649）

**现象**：#2649 新增 `bub-host` 作业，check run `success`，但整 job 仅 57 秒，其中 `Install the pinned Bub host`
（`make harness-sync`，`uv sync --project e2e/bub --locked`）占 **1 秒**。按常理 1 秒装不完一套 harness，
容易误判为「环境已存在 ⇒ 用例被 skip ⇒ 新覆盖是空的」。

**核验路径**：`commits/<sha>/check-runs` 取 `details_url` → `actions/jobs/<job_id>` 看 `steps[]` 起止 →
`gh run view --job <job_id> --log` 里 grep `collected|passed|skipped|failed`。本例得到
`collected 5 items` 与 `5 passed in 31.22s`，即 5 个用例真实执行；1 秒是自托管 runner 复用了已有 venv。

**规则**：判「新作业是否真的覆盖」不能只看 conclusion 或时长，必须落两行证据——实际收集数与实际通过/跳过数。
`if:` 跳过的 job 结论是 `skipped`（bucket=skipping），而 `success` 也可能是「收集到 0 个用例」之外的假象，
两者都要用日志行区分。**注意 pytest 收集 0 个会以退出码 5 让 step 红**，所以看到 `success` + 极短时长，
优先怀疑 harness 复用或 `-k` 过滤，而不是怀疑覆盖。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2649 head 8444d210 / job 132397592880`、
`applies_to: 引用 CI 作为验证证据、且本 PR 新增或改动 CI 作业`、
`recheck_when: 作业改为 ubuntu-24.04 托管 runner 或 harness 不再缓存`。

<a id="exp-145"></a>

## `commits/<sha>/check-runs` 默认只给 30 条：漏作业会直接导致「该作业不存在」的错误结论（2026-11-15 实测 #2630）

REST `GET /repos/{owner}/{repo}/commits/{sha}/check-runs` 不带 `per_page` 时按 30 条返回，`total_count` 仍是全量
（本轮 #2630 head bd057c3f 为 85）。抓下来 grep `e2e|gateway` 得到空集，据此会误判「head 上根本没有 e2e 作业」，
而实际 `tests (3.12, e2e)` 就在第二、三页且为 success——足以把已修复的发现重复报一遍。

判据与做法：先看 `total_count` 与 `len(check_runs)` 是否相等；不等就补 `?per_page=100&filter=all` 重取，
或按 `--paginate` 展平后再筛选。凡是「某作业没跑 / 不存在 / 没被触发」这类否定性断言，必须先证明返回未截断。

**关键词**：`validated_at: 2026-11-15`、`validated_ref: oceanbase/powercontext #2630 head bd057c3f`、
`applies_to: 任何仓库的 check-runs 取证`、`recheck_when: GitHub 调整该端点默认分页`。

<a id="exp-154"></a>

## 同一 SHA 的 check-runs 可能含同一次 run 的多次重试：判读前先按 `check_suite` 取最新 attempt（2026-11-24 实测 oceanbase/powercontext #2749）

- 现象：`commits/<sha>/check-runs?filter=all` 对一个 head 返回 86 条，其中同一个 `actions/runs/<id>` 出现三套
  `tests (3.11, unit) / (3.12, e2e) / (3.14, unit)`，结论分别是 failure / cancelled / cancelled。直接按「有 failure 就算红、
  有 cancelled 就算不可判定」汇总，会把重试前的旧 attempt 当成本 head 的当前结论，得出「本 PR 同时红在三个作业」。
- 判据：以 `check_suite.id`（或 `details_url` 里的 `actions/runs/<id>`）分组，组内按 `started_at` 取最新一次 attempt，
  再逐作业读步骤结论。重试之间的 cancelled/failure 只说明当时被打断，不构成当前证据。
- 落地：先列 `{group: max(started_at)}`，只对最新 attempt 里的失败 job 拉 `actions/jobs/<id>` 的 steps 与日志；
  对失败 job 的 `--log-failed` 若只回落到 cleanup 段，改用 `actions/jobs/<id>` 的 steps 定位到具体步骤再取整段日志。
- 附带：`gh api actions/jobs/<id>/logs` 在非 git 目录下会报 `failed to determine base repo`，要在仓库目录执行或带 `-R`。

`validated_at: 2026-11-24`、`validated_ref: #2749 head ec5218ee（check suite 121437460262）`、
`applies_to: GitHub Actions 上开了自动重试或人工 rerun 的仓库`、`recheck_when: 仓库关闭 job 级重试或改用 merge queue 单一 SHA`。

<a id="exp-156"></a>

## 判「零 CI 覆盖」和「CI 红是否与本改动相关」的两步取证（2026-11-24 实测 oceanbase/powercontext #2615 / #2602）

- 零覆盖判据：`commits/<head>/check-runs` 与 `commits/<refs/pull/N/merge>/check-runs` **两条 SHA 都要查**，
  两者 `total_count` 都是 0 才算零覆盖；只看 head 会把「检票跑在合并 SHA 上」误判成「CI 没跑」。再看
  `commits/<sha>/check-suites` 的 `status/conclusion`：`action_required` + `latest_check_runs_count: 0` 等于
  「工作流在等维护者批准」，属于零覆盖而不是绿，报告里必须写成不可判定（R15），不能写「CI 通过」。
- 归因判据：失败 job 的 `check-runs/<id>/annotations` 只给 `Process completed with exit code 2.` 和 `.github` 路径，
  **拿不到测试名**；必须 `actions/jobs/<id>/logs`（跟随重定向取整段日志）再 grep `FAILED tests/` 与 `^E `，
  才能确认失败用例是否落在改动面。同一 head 同时有 success 分片时，用「成功分片覆盖改动面、失败分片在无关模块」
  这一对照支撑「红为抖动」的结论，比只说「看起来无关」可核验。
- 交叉印证：失败用例落在本 PR 未触碰的模块（如 `test_sqlite_profile.py::... database is locked`、
  `test_server_metrics_process.py::... assert 200 == 401`）时，再核对 PR 的 files 列表既不含该模块、也不含其调用面
  （persistence / metrics 鉴权），才把结论写成环境或既有抖动。
- 附带：`gh pr checks <N>` 在非 git 目录下直接失败（`fatal: not a git repository`），要么加 `-R owner/repo`，
  要么全程改用 `gh api`。

`validated_at: 2026-11-24`、`validated_ref: #2615 head 1b3c6318（check_suite action_required）/ #2602 head 4e1706ec（5 个 job 红）`、
`applies_to: GitHub Actions 上区分「没跑」与「跑挂了」的审查结论`、`recheck_when: 仓库改用 merge queue 或对首次贡献者默认放行工作流`。

<a id="exp-157"></a>

## PR 的 base 不是默认分支时，整层可能零 CI：先看 workflow 的 `pull_request.branches` 过滤（2026-11-25 实测 oceanbase/powercontext #2653）

- 现象：堆叠 PR（base = `codex/dsh-handoff-preflight`，父 PR #2602）的 `commits/<head>/check-runs` 的 `total_count` 为 0，
  但 PR 状态是 `mergeable_state: clean`、不是 Draft、也没有 `action_required`。这与「等维护者批准」「fork 限制」都不同。
- 判据：读 base 分支上的 workflow 触发条件。本仓 `.github/workflows/master.yml` 写的是
  `on.pull_request.branches: [master]`，因此任何指向 feature 分支的 PR 都不会触发整套 CI——不是没跑成功，是压根不触发。
  区分方法：`action_required` 说明工作流在等人批准；`total_count: 0` 且 workflow 的 `branches` 过滤不含该 base，
  说明「结构上不会跑」。
- 处理：报告里写成 R15 的「零覆盖」并说明成因（堆叠 PR），不要写成「CI 通过」；同时明确要求本地跑该层的
  单元测试并把结果写进三态结论的「验证证据」字段，因为父层合入后这一层会被重新触发，届时才有 CI。
- 附带：堆叠判定不要只看分支名，取父 PR 的 `headRefOid` 与当前 PR 的 `base.sha` 比对相等（本轮 3bbbf527 相等），
  再确认 `gh pr diff` 返回的就是本层增量。

`validated_at: 2026-11-25`、`validated_ref: #2653 head f21d79f2（base 3bbbf527 = #2602 head）`、
`applies_to: 使用堆叠 PR 且 workflow 限定 branches 的仓库`、`recheck_when: master.yml 的 pull_request 触发条件变化，或仓库改用 merge queue`。
