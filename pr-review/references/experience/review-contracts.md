<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 审查、契约与公共行为

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-001"></a>

## 跨平台原生编译缓存

- CI 在共享构建脚本中新增 `CC` / `CXX` / compiler wrapper 时，必须沿每个操作系统的实际调用链检查最终编译器，不能用 workflow 某一步的 OS 条件推断脚本内赋值不会生效。Windows/MSVC 路径应从 job 日志核对 `cc-rs` 最终命令，并用 exact Base/Head 的同类 job 区分 PR 回归与平台基线。
- 增加 `actions/cache` 前先检查工具链 setup action 是否已经隐式启用缓存及其实际缓存路径。若两套 action 同时包含 `target`，应指定唯一 cache owner；手写 key 至少覆盖 toolchain、target triple、profile、native compiler 和 feature 等会改变产物身份的维度，并从 job 日志核对恢复路径与下载规模。

<a id="exp-002"></a>

## GitHub 行内评论写入

- `gh api` 创建行内评论若在响应阶段返回 `EOF`、超时或连接中断，服务端是否已落库是不确定的。重试前必须重新获取当前 Head、Diff 和已有 review comments，并按评论正文/路径/行号去重；确认未落库且目标行仍属于当前 hunk 后，才按同一 Head 最多重试一次，避免重复评论。
- Windows 上的评论抓取脚本若用 Python `subprocess` 的 `text=True` 读取 `gh` 输出，会继承本地 GBK 等默认编码；Copilot 评论中的智能引号或 emoji 可能触发 `UnicodeDecodeError`。应仅为该进程设置 `$env:PYTHONUTF8='1'` 后重跑，并用 REST review comments 与 GraphQL review threads 交叉核对；首次失败归类为工具环境问题，不能据此判断评论缺失。
- PowerShell 循环中的 hashtable 属性传给 `gh api -F` 时必须使用子表达式，例如 `-F number=$($item.pr)`、`-F in_reply_to=$($item.id)`；直接写 `$item.pr` 可能被序列化成 `System.Collections.Hashtable.pr` 并返回 422。422 明确未创建评论时，仍应重新核对 Head/comments 后按协议重试一次，不能只修参数后盲重放。
- 向已 resolved 的 review thread 追加 reply 不会自动把线程恢复为 unresolved。用原线程去重残留根因后，最终必须重新读取 GraphQL `isResolved/isOutdated` 并在报告中明确状态；不得把成功回复冒充为线程已重新阻断，也不得未经授权主动 Unresolve。
- 自动审查声称双语入口文件内容对调时，先固定当前 `headRefOid`，同时读取本地 exact-Head blob 和 GitHub raw blob，核对文件名、语言切换链接、正文语言及被引用标题的真实归属。若两侧均证明 `README.md` 为英文、`README_CN.md` 为中文等既定合同，在线程中给出行号和 blob 证据；只有用户明确授权时才 Resolve，不制造无意义的交换提交。

<a id="exp-004"></a>

## 评论窗口内的 same-tree Head 变更

- 评论提交窗口内 `headRefOid` 发生变化时，即使新旧 commit 的 tree OID 和完整 PR Diff 完全相同，也要停止旧快照收尾：核对 Base、父提交、tree OID 和 Diff，checkout exact 新 Head，重跑受影响的动态探针与门禁，再重新获取 comments/threads。只有 same-tree 已被 Git 对象证明且新 Head 复验结果一致时，才能复用源码推导；不能仅凭 commit message 或 Diff 文件大小判断等价。
- Head 前移期间创建的行内评论可能在响应或后续 REST 查询中被 GitHub 映射到新 Head。必须同时核对 `original_commit_id`、当前 `commit_id`、`position`，以及 GraphQL thread 的 `isOutdated`；评论仍位于当前 Diff 时保留并记录竞态，不盲目删除或重复提交。

<a id="exp-005"></a>

## 发布前远端分支租约

- commit 或 push 前必须重新比较 PR 实时 `headRefOid`、本地 upstream 和本轮审查基准。若远端在本地验证期间被 force-push 或增加了非本任务提交，禁止用 force-push 覆盖；保留本地提交，重新审查远端变更后决定适配，或改用唯一新分支创建明确说明重叠关系的独立 PR。

<a id="exp-006"></a>

## 公开类型与指标状态演进

- Rust 公开 trait 增加可选能力时，优先提供语义安全的默认方法，避免让现有外部实现立即编译失败；应增加一个只实现旧方法集的兼容性测试，证明新版本仍接受旧实现。
- 可序列化公开结构新增非 `Option` 字段时，必须验证旧载荷反序列化；适用时用结构级或字段级 `#[serde(default)]`，并以缺少新增字段的旧 JSON/配置夹具建立回归测试。
- 指标 tracker 新增累计状态时，必须同步审查构造、快照、聚合、序列化和 `reset()` 五条路径；测试应执行“记录非零值 -> reset -> 全量快照归零”，避免 reset 后残留新指标。

<a id="exp-008"></a>

## Rust exact 测试命令

- Rust libtest 的 `--exact` 匹配完整测试名。定向命令必须使用包含模块路径的名称，例如 `parse::tests::test_name`，并核对输出确实为 `running 1 test`；退出码为 0 但显示 `running 0 tests` / `filtered out` 不能作为 TDD 或回归证据。

<a id="exp-010"></a>

## 审查报告的证据边界

- 看到底层方法缺少局部锁时，必须继续追踪正式入口、命令元数据和上层调度门禁；若完整调用期间已有共享写锁或串行化保证，不得把底层 check-then-act 直接报告为客户端可达竞态。
- 汇总型审查文档只有在固定适用 Base/Head、逐条提供可定位证据并移除“待确认”结论后，才能作为权威状态入口；agent 报告、过期行号和互相矛盾的范围声明不能由“已人工验证”的总括语句替代。

<a id="exp-011"></a>

## 审查收敛与噪声度量（外部来源，未在本仓复现）

- 来源：Claude Code 团队 2026-10-15 公开的审查流程。其自述一个 CLI PR 一夜经历 50 余轮审查；对审查器反复标出的问题做 `git blame`，约 59% 是首轮审查前就存在的老代码，审查器很少发现新 bug，只是每轮多挖出几个旧的。
- 判据：复审的收敛性必须与召回率一起度量。连续多轮只挖出基线旧代码时，说明增量审查已失效，应按类指出全部实例并要求回到方案层，而不是逐 commit 追打（对应 `review.md` §8）。噪声代价在 AI 作者场景更高：人可一秒忽略 nit，agent 会去修，产生新 commit 和新一轮审查。
- 噪声度量口径：按作者对每条评论的实际反应分类（已修 / 反驳成立 / 说明是有意行为 / 忽略），并在已知干净的 PR 上统计“会引导人做有害改动”的误报；不能用“抓到更多问题”单独证明审查变好。
- 关键词：`validated_at: 无（外部来源，未在本仓复现）`、`validated_ref: claude.dev/blog/solving-code-review-at-anthropic/（2026-10-15）`、`applies_to: 设计或调整 AI 审查流程、复审策略时的方法参考`、`recheck_when: 该流程公开描述变更，或本仓积累出自己的轮次与误报数据后改用本仓数据`。
- 边界：外部单一组织实践，未在本仓 PR 上复现；不得据此直接支持门禁结论或“可 Merge”判断。

<a id="exp-014"></a>

## 配置互换测试的夹具可区分性

- 测试证书链、密钥、trust collection、主备配置或成对转换时，先比较夹具指纹或规范化内容。若两个输入实际相同，即使逐字节断言最终字段也无法检测路径互换。应使用语义有效且彼此不同的夹具，并显式断言其可区分性；必要时再加入错误配对或变异式反证。

<a id="exp-015"></a>

## 组合 Writer 的字节计数语义

- 包装器若先调用底层 `Write`、再执行 `Flush`、同步或提交，后续阶段失败时仍应返回底层已经消费的 `n` 与错误；返回 `0, err` 会错误暗示调用方可以安全重发全部输入。回归测试应让底层 writer 只在后续阶段失败，并同时断言错误身份和已消费字节数，避免普通成功路径掩盖计数错误。

<a id="exp-017"></a>

## GitHub Actions OIDC 凭据隔离

- PR workflow 中需要 `id-token: write` 的上传 job 不应 checkout 或执行 PR 可控代码。先在无 OIDC 权限的测试 job 生成固定名称 artifact，再由仅含 artifact 下载和官方上传 Action 的独立 job 使用 OIDC；上传失败必须传播为 check 失败。最终验证要从当前 Head 的 job 日志同时确认 artifact 身份、OIDC 成功和上传工具实际结果，不能只凭 workflow 静态结构或 job 绿色结论推断凭据边界正确。

<a id="exp-020"></a>

## Markdown 控制面合同的可执行验证

- 用 Markdown 承载 Requirement、Decision、工作包或验收状态时，验证器只能解析明确声明为权威的结构化顶层条目，并先剔除注释、围栏代码和缩进示例；全文件正则搜到相同 ID 不能证明定义、引用或状态闭包。门禁应同时固定规范计数、必需字段、关键门禁文本和 exact Base-to-Head 产物集合，并用变异测试逐项证明重复、缺失、伪造引用、错误状态、断链和未闭合围栏都会非零失败；registry 文件缺失等输入错误必须返回稳定诊断，不能泄漏为 traceback。

<a id="exp-022"></a>

## 潜在合并树的本地精确预检

- PR 分支修复冲突但禁止 merge/rebase 时，可先把暂存区写成 tree，用 `git commit-tree` 创建不更新任何分支引用的临时 Head，再对实时目标分支执行 `git merge-tree --write-tree`。合并成功后以返回的 tree 创建临时 synthetic merge commit 和独立 worktree，运行交叉影响最大的测试、Lint 与格式门禁；GitHub 重算完成后，必须核对 `potentialMergeCommit` 的两个父 SHA 及 tree SHA 与本地结果完全一致，才能把本地预检归因到当前潜在合并结果。若 GitHub 只把 checks 挂到 PR Head 而非潜在合并提交，应在收尾中明确这项证据边界，不能声称潜在合并 SHA 本身已有 check-run。

<a id="exp-025"></a>

## Agent 工具的工作目录漂移与镜像污染

- `validated_at: 2026-10-10`、`applies_to: WorkBuddy/CodeBuddy 桌面端 Bash 工具 + 独立镜像审查`。该环境的 Bash 工具在每轮调用之间会把 cwd 重置回用户工作区，且调用方极易在后续命令里漏掉 `cd` 前缀。后果是 grep/sed/pytest 以相对路径静默落到用户工作区或错误镜像，制造"旧测试 + 新源码"的混合证据（PR #1918/#1914 审查中实际发生：一轮 pytest 报 10 处失败全部为目录污染假象）。对策：镜像内所有读取与测试一律用绝对路径；每个命令链开头断言 `pwd`；对镜像内关键文件先 `git hash-object` 与 `files` API 的 blob SHA 对账再使用；发现混合证据后必须整批重跑，不得只重跑失败项。
- `gh api <list> --paginate --slurp` 的输出把每一页再包一层外层数组（`[[{...}]]`），展平时需检测 `len(obj)==1 and isinstance(obj[0], list)` 后解包一层，否则会把元素当列表处理。

<a id="exp-027"></a>

## 评论正文含反引号时禁用 bash 内嵌字符串提交（正文会被命令替换截损）

- `validated_at: 2026-10-12`、`validated_ref: oceanbase/powercontext PR #1935`（head `f466ce7f`，评论 id 4243604152/4243604287）。
- 现象：用 `python -c "..."`（外层双引号）内嵌三引号字符串构造含反引号的评论正文时，bash 把正文里的 `` `...` `` 当命令替换执行——API 调用成功落库，但所有反引号片段被替换为空串，正文静默截损（stderr 里有 `command not found` 噪声是唯一线索）。`gh api -X POST .../pulls/{n}/comments` 的响应对此无法察觉，必须发布后回读 body 核验。
- 处理：正文一律先用 Write 工具落成 JSON 文件再 `--input` 提交；发现截损后用 `PATCH repos/{owner}/{repo}/pulls/comments/{id}`（注意本机 `pulls/{n}/comments/{id}` 单评论路径返回 404，全局 `pulls/comments/{id}` 路径可用）原地修正，禁止重复创建。定级不受影响时无需删除重发。

<a id="exp-028"></a>

## 共享裸克隆的 master ref 会陈旧，「master 现在」类结论必须先强刷

- `validated_at: 2026-10-15`、`validated_ref: oceanbase/powercontext PR #2000`（错误评论 4273482110 + 线程内更正 4273532879）、`applies_to: 复用共享 `--filter=blob:none` 裸克隆的所有审查`、`recheck_when: 复用超过当日的共享镜像时`。
- 现象：共享裸克隆 `source/repo.git` 的 `origin/master` 停留在数日前（当时 6b719516），而「master 现在如何」的比较全部基于它。后果有两类：① 反向结论——把陈旧 master 当作「已前进」，对 #2000 发布了「契约 SHA 已过时需再生成」的错误评论（实际当前 master 恰好就是 PR 的值，且修复已被 #1988 先合入）；② 误报缺失——#1990 事实核验把当前 master 上存在的文件报成缺失。
- 判据与处理：任何「相对 master 现状」的比较前，先 `git fetch origin master:refs/heads/master --force` 并将本地 tip 与 GitHub 实时 `baseRefOid` 对账（`baseRefOid` 即当前目标分支 tip，可用 `gh pr view --json baseRefOid` 取得）；不一致必须重刷后重新取证。已发布的错误结论按 review.md §8 处理：先实证再反转，在原线程补充更正，不删除原评论。

<a id="exp-029"></a>

## 矩阵 job 单版本失败不得直接归因 PR

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #2005`（head `2392a670`，`tests (3.12, unit)` 与 `tests (3.14, e2e)` 红）。
- 判据三选三齐才可归因 PR：① 同一测试族在**其它版本 job 上全绿**（本例 unit 3.11/3.13、e2e 3.11/3.12/3.13 均通过，仅 3.12-unit 与 3.14-e2e 红）；② 失败形态是**时序/启动竞态**（本例为「不应出现 `artifact_processing.failed` 事件」的时序断言，以及 `uvicorn Server.started == False`）；③ PR 修改的**目标 job 通过**（本例 e2e-harness 中新增「9 个用例必须全部执行」断言的 `Recall effort (OceanBase)` 为 success）。
- 反向教训：矩阵中某个版本失败极易被写成「CI 红 → 不合入」。正确做法是把「红在哪一版本、同族是否全绿、目标 job 是否绿」三件事写进收尾，再决定是否升级为 Finding；只有单版本独占失败且无因果路径时，归为环境噪声且**不计入 PR 结论**。
- 另一条易错项：`check-runs` 端点会同时返回**同一 job 名在新旧两批 run 里的多条记录**，直接按结论计数会把「新批次被取消（cancelled）」误读成失败。门禁快照必须**每个 job 名只取 `started_at` 最新的一条**，并单独确认是否存在仍在进行的 run。

<a id="exp-030"></a>

## 对称修复必须逐消费者核验（序列化面不止两个）

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #2004`（head `3305b6bb`；声明 `model_json_schema(mode="serialization")`、payload `model_dump(mode="json", by_alias=True)`、信封身份校验 `validate_envelope_identity()` 按字面键读取）。
- 现象：作者按「声明 schema ↔ 传输 payload 命名不一致」修复后，两侧确已同源；但同一表征还有**第三个消费者**——信封身份校验的键名。子类配置 `ConfigDict(alias_generator=to_camel, populate_by_name=True)` 时，别名生成器会连带重命名**继承而来的**信封字段（`definition_version` → `definitionVersion`），于是 payload 与声明自洽，却在接受侧抛 `ValueError: projected Source payload … does not match its envelope`。
- 判据与处理：验证别名类修复时，先枚举该表征的所有消费者（生成侧、传输侧、校验侧、指纹/摘要侧），并对扩展点**允许的最宽泛别名形态**取证——本仓新增测试只覆盖字段级 `serialization_alias`，一条就通过；必须补 `alias_generator`（作用于全部字段含继承字段）这一形态，否则「已修复」的结论会覆盖不到真实缺口。可复现脚本保留在审查镜像 `probes/envelope_alias_repro.py`。
- 附带技巧：`git archive` 产物在本机 `core.autocrlf=true` 下带 CRLF，与 GitHub contents API 的 LF 内容直接做 sha256 比对必然不等；比对前先做 `\r\n` → `\n` 归一化（归一化后逐字相同即证明「镜像 == Head」）。

<a id="exp-031"></a>

## 库行为假设类 Finding 先读实现再定级

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #2019`（指标命名候选被自行否决）。
- 教训：以「某库会自动追加/剥离名称后缀」为前提的命名类 Finding，必须先读 `site-packages` 实现再定级。实例：`prometheus_client` 的 `CounterMetricFamily.add_metric()` **无条件**追加 `self.name + '_total'`，只在名字已以 `_total` 结尾时于构造阶段剥离一次，因此自定义 collector 手写 `_total` 全名是正确的，原「缺 `_total`」的候选不成立。
- 处理：被自我否决的候选**不入档、不发评论**，但在收尾报告里留一行「已否决 + 依据」，防止下一轮重复推导同一错误结论。

<a id="exp-033"></a>

## 平台专属失败必须先分辨「产品缺陷」与「测试夹具平台差异」

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #1561`（head `776a8fdb`；新评论 4293611535，收尾评审 5546464590）、`applies_to: 本机 Windows 跑 Linux 侧测试套件的所有审查`。
- 同一轮里出现两个「只在 Windows 红」的用例，判定相反：① `test_archive_cli_dry_run_checks_existing_sqlite_uri_target[absolute|escaped]` 是**产品缺陷**——CLI 的存在性检查把 `file:///C:/…` 解析成 `/C:/…`，于是 dry-run 静默退回空的内存库校验并返回假绿（`assert 0 == 3`）；② `test_archive_restores_package_files_and_topic_search_after_restart[sqlite]` 是**夹具差异**——夹具用 `Path.write_text("…\n")` 落盘，Windows 文本模式把 `\n` 翻译成 `\r\n`，而断言比对的是 `b"…\n"`。判据：不要从断言与失败文本推断，直接写探针调用被测内部函数（本例 `_database_file_exists`）并打印中间产物（解析出的 filename），即可看出「错误结果」还是「测试自己造错了输入」。
- 第二道判据是**CI 是否可能发现**：读 `runs-on: windows-*` 的 job 实际执行了什么命令，而不是看它存在与否。本仓 `master.yml::windows-unit-portability` 只跑 `make opendal-test`，Python 测试套件在 Windows 上从不执行 ⇒ 这类缺陷天然对 CI 隐形，评审须自行承担该平台的验证责任，并在收尾里写明「该结论仅本机平台可复现」。
- 第三类（2026-10-18 新增）：**`monkeypatch.setenv("HOME", tmp_path)` 在 Windows 上不构成隔离**。Python 的 `Path.home()` 在 Windows 走 `USERPROFILE`/`HOMEDRIVE+HOMEPATH`，忽略 `HOME`，于是夹具以为被隔离，被测代码仍读真实用户目录。实测（PR #2052）：`test_setup_transport.py` 的 autouse 夹具设了 `HOME=tmp`，但 `existing_native_endpoint("workbuddy")` 经 `workbuddy_home() → Path.home()` 读到本机真实的 `~/.workbuddy/mcp.json`（内含 `127.0.0.1:8000`），把 `.env` 里的 `POWERCONTEXT_SERVER_HTTP_PORT=18000` 覆盖掉，两个用例红在 `18000 != 8000`。判据：同一用例在 ubuntu CI 绿、本机 Windows 红，且失败值恰好等于本机真实配置 ⇒ 先按「夹具/平台差异」处理。取证只需一行探针：设 `HOME` 后同时打印 `os.environ["HOME"]` 与 `Path.home()`（探针 `oceanbase-powercontext-pr-2052/probes/probe_home.py`）。
- 第四类（2026-10-23 新增）：**断言建立在被 monkeypatch 的 `HOME` 上，真实写入目标却是 `Path.home()`**。PR #2205 的 `tests/test_cli_minimax.py` 用 `monkeypatch.setenv("HOME", tmp_path)` 做隔离，被测 `MiniMaxInstaller` 走 `_data_dir()` 的默认分支（`Path.home()/".minimax"`）与 `powercontext_data_dir()`，在本机 Windows 上把插件写进了真实的 `C:\Users\<me>\.minimax`；断言随即因为去 `tmp_path` 下找文件而失败，且**审查机的真实家目录被污染**（本例已把该目录整体移入审查镜像 `oceanbase-powercontext-pr-2205/evidence/test-home-leak/minimax/` 留证）。判据与处置：跑「装到用户目录」这类用例前，先确认隔离变量与被测代码的真实取值来源一致（Windows 需 `USERPROFILE`，更稳的是直接 patch `Path.home` 或被测的根目录解析函数）；一旦发现用例写了真实家目录，先移出取证再继续，并在 Finding 里如实写明「本机跑该用例会写入真实家目录」——这本身是可评论的测试缺陷，不按纯夹具差异放过。
- 与前两类的处置差异：`Path.home()` 这类问题必须先确认**被测解析代码是否被本 PR 修改**（本例 `resolve_setup_endpoint`/`_saved_setup_endpoints` 与 base 逐字相同 ⇒ 非本 PR 引入），再决定是否只记为缺口而不发评论；不要因为「测试是本 PR 新加的」就把它算成 PR 缺陷。

<a id="exp-034"></a>

## 文档里的全局不变量要按「记录族」逐族核验消费者的覆盖面

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #1561`（新评论 4293611962）、`applies_to: 「启动即拒绝不完整状态」这类跨族承诺`。
- 现象：文档写「Normal Server startup still rejects incomplete projections」，作者自带的 e2e 用例也确实断言了拒绝行为——但该用例的作用域里含 Topic Memory 产物，触发的是 Topic 侧的不变量；换成只含 Atomic Memory 产物的作用域，正常启动与 `open_builtin_runtime` 都放行、搜索命中数为 0（探针 `probe_incomplete_projection.py`）。作者没有错，是**承诺的措辞比实现覆盖面宽**。
- 判据：对「某状态会被拒绝/被校验」的全局承诺，先 `grep` 该状态标志（本例 `projections_ready`）的全部消费者，看它落在哪些族；消费者只有一处且只放宽某一族的校验时，承诺对其余族不成立。再用「最小作用域 + 必然失败的注入点」构造状态（本例：只放 1 个 atomic-memory 产物 + `projection_rebuilder` 必抛），逐入口（contexts / runtime / server）验证是否放行。
- 顺带可复用的判据：同一 PR 内若某重建函数与其既有同类实现（本例 `rebuild_atomic_memory_projection`）在「投前锁 + 逐条 CAS + 终态全量校验」上不同级，把差异写成**并列事实**（不单独要求改动），既指出风险又不把文档已声明的前提当作缺陷。

<a id="exp-035"></a>

## 已 resolved 线程的「残留形式」应新开评论并交叉引用，不复活原线程

旧条目的“追加回复会自动恢复 unresolved”及“同根因残留另开线程”处理已退役。按 R12 核对完整线程、同根因优先复用；回复不等于改变 resolved 状态。Resolve/Unresolve 依 §8 的明确授权执行。原始现象仅作历史调查来源，不据此创建重复线程。

<a id="exp-037"></a>

## 通知驱动增量审查的「自我噪声」（updated_at 变化 ≠ 有新外部活动）

- `validated_at: 2026-10-17`、`validated_ref: oceanbase/powercontext PR #1813/#2025/#2048`（head `cebd9af1`/`802f5bb2`/`1787c1a2`）、`applies_to: 以 notifications + last_run_at 判增量的自动化审查`、`recheck_when: 状态文件改为记录「上次已见评论 id 水位」或改用 GraphQL updatedAt 的评论级游标`。
- 现象：上一轮的行内评论/评审推送晚于写回 `last_run_at`（本轮实测：`last_run_at=14:48:49Z`，自己的评论落在 `15:10–15:12Z`），于是下一轮把「自己造成的 `updated_at` 变化」重新判成增量，四个条目里三个是自我噪声，一个是 MERGED 通知。
- 判据（逐条核对，不靠 `unread`，也不靠 `updated_at` 单字段）：① `headRefOid` 是否等于 `last_reviewed_head`；② `pulls/<N>/comments`、`issues/<N>/comments`、`pulls/<N>/reviews` 过滤 `updated_at > last_run_at` 后，`user.login` 是否只有本账号（含并发身份 `hidb4ai`）；③ `pulls/<N>/commits` 最后一条 `committer.date` 是否早于上一轮审查时间。三条都指向「无新增外部活动」即按增量去重规则跳过，不重开线程、不重复审查。
- 处理：跳过也要写回该条目的 `last_seen_updated_at`，并把 `last_run_at` 取本轮**实际开始**时间而不是上一轮开始时间，否则同一批自我评论会被反复重扫；`MERGED`/`CLOSED` 的通知按 R02 停止，只记录合并 SHA 与遗留未发布的 Finding。

<a id="exp-039"></a>

## `pr view --json baseRefOid` 不是目标分支当前 tip

- `validated_at: 2026-10-18`、`validated_ref: oceanbase/powercontext #2043(baseRefOid 06794f66)、#2031(8567df45)，同刻 master tip caf2a35a`、`applies_to: 所有以 baseRefOid 作为"当前 master"的比较`、`recheck_when: 依赖 baseRefOid 做祖先关系或版本对照`。
- 现象：同一时刻四个 PR 返回三种 baseRefOid，其中两个等于各自 merge-base 的历史值、两个等于当时 tip。把它当"目标分支现在"会得到错误的祖先/缺失判断（与"共享裸克隆 master 陈旧"同类后果）。
- 处理：需要当前 tip 时用 `git ls-remote origin refs/heads/master` 或 `gh api repos/{owner}/{repo}/git/ref/heads/master`；baseRefOid 只用于记录 PR 快照里的字段值，不用于"现在"类结论。

<a id="exp-041"></a>

## 分平台失败先用同镜像 Base 树比对失败集合

- `validated_at: 2026-10-18`、`validated_ref: oceanbase/powercontext #2031（tests/test_database_migration_cli.py 本机 11 failed）`、`applies_to: 在本机跑 Linux 侧测试套件、且失败集中在 PR 仅微改的文件的场景`。
- 处理：在同一镜像里按 merge-base 建一棵 Base 树（`git archive <merge-base>` + Python tarfile 解压），用同一个 runner 跑**同一个文件**，把两侧 `^FAILED` 列表排序后 `diff`；集合完全相同即环境基线，只需记录（本例全部是 Windows `WinError 32` 文件占用导致 `Path.rename` 失败）。这比逐条读失败文本更快，也能避免把平台差异写成 PR 阻断。

<a id="exp-042"></a>

## 「布局校验器不再认识该库」类结论先核 bundle 覆盖面与可达版本

- `validated_at: 2026-10-18`、`validated_ref: oceanbase/powercontext PR #1966`（head `9f3c9cd4`，base `f2808fb4`）、`applies_to: 迁移/基线校验器（identify/verify/_matches）与启动期 schema 门槛类改动`、`recheck_when: 校验器改为子集语义、或 bundle 覆盖面扩大到全库`。
- 现象：本轮两次把「启动期新增表/列 ⇒ 离线迁移校验器失效」当成 P1，两次都在取证后推翻——(1) 该离线 bundle 的冻结快照本来就只含 5 张 artifact 表，budget 表在 base 上同样不在其中；(2) 被 `unknown_baseline` 拒绝的「无 Topic work 表但含其他业务表」这个组合只存在于引入该表之前的版本，而该表已随 v1.0.0 发布，已发布版本不可达，且文档明确写为有意边界。
- 判据（三问，全部先于定级）：① 该对象在 base 上是否已不在校验器的注册集合内（`set(expected["tables"])` 与 frozen 快照对照）？在则不是本 PR 引入；② 受影响的库形态在**已发布版本**上是否可达（用 `git log -S<表名>` 找引入提交，再 `git tag --contains` 看是否已在 tag 内）？不可达则不是用户面回归；③ 仓库文档是否已把该拒绝写成有意边界（`docs/*/operate/*.md` 的 "rejected before writes" 一类措辞）？已写明则降级为 runbook 缺口，不按缺陷定级。
- 处理：这类结论必须给出「校验器注册集合 + 触发库形态 + 版本可达性」三项证据；只给「新增对象不在 pNNNN 里」的推导不成立。探针可静态重建（frozen 布局 + 启动期 DDL 后调 `identify()`/`verify()`），但必须同时说明重建是否遗漏了真实库的其余表，否则结论不可用。

<a id="exp-044"></a>

## 符号链接后接 `..` 的 realpath 差异只在 POSIX 成立

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2043`（head `6a514384`）、`applies_to: 任何"先 `path.resolve` 再 `realpath`"的路径身份计算`、`recheck_when: 改为对原始路径直接 realpath、或宿主只接受规范化绝对路径`。
- 现象与判据：`resolve()` 是词法折叠，`realpath(原始路径)` 是内核语义。输入 `<dir>/link/../other`（`link` 为符号链接）时，POSIX 上两者不同（内核先跟随 link 再 `..`），Windows 上相同——Win32 在接触 reparse point 之前就按词法折叠 `..`。
- 因此**不能**在 Windows 上测过就否定该缺陷，也不能在 POSIX 上测过就断言三平台都中招。两侧都要取证：WSL/真实 symlink（`os.path.realpath` 对照 `normpath` 后 realpath）与 Windows junction（`realpathSync.native` 对照 `resolve`）。
- 报告口径：把触发条件收窄到"调用方传入的 `cwd` 自身含符号链接分量 + `..`"（宿主传入的规范绝对路径通常不含 `..`），并说明 CI 矩阵是否覆盖该平台与夹具是否真的构造了 `..` 形态。

<a id="exp-046"></a>

## base 上已红的 job：「同一 job 红」不等于「同一原因红」，必须比对失败签名

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2052`（head `62f2bacb`，base/master `e4efb39b`）、`applies_to: 任何需要判断"本 PR 是否引入 CI 断裂"的审查`、`recheck_when: CI 改为 required status checks、或 job 合并/拆分`.
- 现象：PR 的 `validate` job 失败（`AttributeError: module 'powercontext.cli.kimi_code' has no attribute 'install_kimi_plugin'`），而 master 同一 job 也失败 —— 但 master 的失败是**同两个用例**的 `assert {...} == {...}` 键值不一致。只看 conclusion 会得出"base 已红，与本 PR 无关"，从而漏掉 PR 新增的 import/属性级断裂。
- 判据：① 取 PR head 与 base 各自的 job 日志 `short test summary info`，比对**异常类型与断言位置**，不一致即为独立断裂；② 若 PR 侧是 `AttributeError`/`ImportError` 一类，直接 `git grep <symbol> <head>` 全仓（含 `e2e/`、`tests/`、`scripts/`、`docs/`）确认是否只剩单份消费者；③ 报告需同时写清"本条修掉后该 job 是否可能变绿"，避免作者误以为一次修复解决全部红项。
- 附带：`gh pr checks <n>` 只返回已产生的 check run 与 status；某 head 可能 `total_count=0` 但存在一条 `license/cla` status（PR #2033 实测），此时"CI 全绿"无从谈起，验证证据只能来自本地执行，必须在收尾里写明。

<a id="exp-051"></a>

## 「生成物与契约一致」不等于「生成物可编译」：漂移检查绿了还要看消费者编译

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2113`（head `d46395e1`，base `fe50f894`）、`applies_to: 用 codegen 替换手写类型映射、并把生成物提交进仓库的改动（OpenAPI→TS/Rust、proto→TS、schema→Zod 等）`、`recheck_when: 生成脚本改为在 CI 里强制 `tsc`/类型检查，或生成物不再入库`。
- 现象：`generate:check` 报"契约一致"，`pnpm typecheck` 却报 `TS2304: Cannot find name 'Type'` 等 13 条。原因不是漂移，而是**导出清单不闭合**——被字段按名引用的类型（生成器把内联 enum 提升成的独立类型）从未写进消费者文件。
- 判据三步：① 在生成物里 grep 报错符号，确认它**只被引用、从未声明**；② 回到生成脚本看导出集合是怎么枚举的（本例只遍历顶层 schema 名）；③ 对照基线（`git show <base>:<generated>`）确认这类字段旧版是 `string`/内联联合，从而排除"本来就没有这个类型"。
- 处理要求：把"生成物能编译"当成门禁的一部分——`generate:check` 之后必须跟一次类型检查（或让 check 目标包含它）；报告时写清失败步骤之后的步骤全部 skip，别把"其他 job 绿"当成编译证据。
- 另一类同源陷阱：注解式类型覆盖（ts-rs 的 `#[ts(type = "...")]`、TypeScript 的 `as`）会连带丢掉可选性与 nullability。判据是**对照生成前的基线字段**是否从 `?: X | null` 退化为必填或空联合；空联合（`?:  | null`）在 TS 里语法合法，不会报错，属于静默降级。

<a id="exp-054"></a>

## 判"过度检测"之前，先确认测试是否显式主张该行为

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2078`（head `9dc46a34`，文件 `evaluation/memory/atomic_extraction/scoring.py`）、`applies_to: 泄漏/禁用词/口令/正则守卫类的启发式改动（指令泄漏检测、敏感词、PII 过滤、模板识别）`、`recheck_when: 作者删除或改写对应断言用例`。
- 本轮差点发出的 P2：新 head 把 `使用 uv 作为 Python 依赖管理工具。` 判为 AI 指令泄漏（旧版放行），初判"过度检测"。回到 `tests/test_scoring.py::test_chinese_use_with_as_or_for_is_instruction_leakage`，作者用 `使用中文作为默认语言。` / `使用 uv 为项目安装依赖。` 显式断言这类**无主语中文「使用…」按祈使处理**——判为泄漏是设计选择，不是缺陷。
- 判据顺序：① 先在该模块的测试里 grep 待判样本的句式或关键词；② 命中即视为已声明语义，需要在报告里写明"与作者显式断言一致"，而不是发 Finding；③ 只有"测试主张的语义与实现不符"，或"实现把测试没覆盖的常识句式判错"，才算过度检测。
- 反例约束：构造对照时至少给两组——一组该命中（`删除旧记录。`）、一组该放行（`保留率为 99%。`、`检查结果显示超时。`）。只有"两个方向都对"，才能得出"未发现新的过度检测"这个结论；只测放行方向会把漏检当正常。

<a id="exp-055"></a>

## 回复里的修复 commit 可能不存在于任何远端 ref，只能按内容核对

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2096`（head `48cc4190`，回复声称 "Fixed in `ccec4880`"）、`applies_to: 「回复声称已在某 SHA 修复」的核验`、`recheck_when: 方法类，长期有效`。
- 现象：`git cat-file -e ccec4880^{commit}` 在按 `refs/pull/<N>/head` fetch 的 `--filter=blob:none` 克隆中直接失败——该 SHA 不在当前 head 历史里（作者本地提交或重写历史后的旧 SHA）。若据此判"未修"或去 `git show` 会误判。
- 处理：一律以 head 上的**内容**取证（断言语句、字段名、模板分支、CI 该 head 的 job 结论），回复里的 SHA 只作为线索；报告里写"声称的 SHA 无法解析，按 head 内容核对已落实"，不要把 SHA 不存在当成未修复的证据。

<a id="exp-057"></a>

## "先把记录写进去再改名"的修复，会让新记录成为窗口裁剪的首选受害者

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2096`（head `1072176e`，`src/powercontext/builtin/code/cache.py`）、`applies_to: journal/manifest 与目录 rename 配套的发布协议（先写记录后 rename、先 rename 后写记录两种顺序都算）`、`recheck_when: 作者给窗口裁剪加上 retained 差集，或 PUBLICATION_WINDOW 语义改变`。
- 顺序修复会**转移**缺陷而不是消除：为了让"rename 后崩溃"可回收，改成 rename 前写入记录，于是记录里的目录在写入瞬间必然不存在 ⇒ 在一个"目录缺失即回收"的窗口裁剪里，这条新记录就是最优先的 stale 候选，`remove_generation()` 在 rename 之前就把即将发布的行删掉。判据：读裁剪函数用的是"目录存在"还是"该 id 是否仍被 pointer 可达"。
- 影响面取决于 store：SQLite 的 `remove_generation` 是空操作（行跟着目录走），seekDB 是 `DELETE ... WHERE generation_id` ⇒ 同样的逻辑缺陷只在远程表后端上变成静默数据丢失。**定级时必须按"行外置后端"算**，不能因为默认后端无害就降级成 P3/不报。
- 「守卫写在 A 函数里」不等于「A 的所有调用路径都被保护」：`recover()` 自己会因 `len(records) > WINDOW` 回头调用裁剪函数，那条路径上没有它刚算好的 retained 集合 ⇒ 守卫自我失效。检查同类代码时先列出"谁能触发裁剪"，逐个比对是否都拿到保留集合。

<a id="exp-059"></a>

## 改用户可见文案前，先找按"整句 innerText"等待的 UI 验收 harness

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #2135`（head `66bf9b666a`，`desktop/ui/src/app/memory-messages.ts`）、`applies_to: 任何把界面文案当契约的安装包/E2E 验收（`wait_text` / `getByText` / `innerText.includes`）`、`recheck_when: 方法类，长期有效`。
- 现象：文案从 `保存成功。` 改成 `保存成功，返回 1 条记录；…` 后，组件测试全绿（它断言新文案），安装包验收却超时——harness 等的是**含句号的整句子串**，新文案用逗号替换了那个句号。
- 判据顺序：① `git grep -n "<旧文案片段>" -- <宿主目录>` 找出所有 harness 等待点（本仓三处，分属 boundaries/lifecycle/workflow）；② 确认旧文案在什么分支还会原样出现（这里是"0 条记录"分支）——只覆盖该分支的正常路径必然失败；③ 归因要拿"同 head 两次运行签名相同 + base 同 job success + diff 面只有文案"三件套。
- 处理建议的优先级：先让文案保留旧句开头（最小改动、不动 harness），再考虑把 harness 改成 `role`/前缀断言；只改一处 harness 会留下同根因的另两处。

<a id="exp-063"></a>

## 文档宣称「与某 RFC 的词表一致」时，必须逐值对回 RFC 原文

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #2144`（head `9ea45fe5`，`docs/en/docs/workflows/prepare-context-text.md` 与 `openapi/powercontext.yaml` 的 `reason` description）、`applies_to: 新增枚举/错误码并声称复用既有规范（RFC、OpenAPI、上游错误码表）词表的地方`、`recheck_when: 方法类，长期有效`。
- 手法：`grep -n "<字段名>" docs/*/rfcs/*<编号>*` 取规范原文，把所有取值列全，再与新增枚举取差集。本轮 "RFC 1435 `fallback_reason` 减 `none`" 实际是四个值里的两个（还漏 `reused_fts_fallback`），而该值恰好对应运行时会走到的"扩充轮复用 FTS 结果"路径。
- 定级：若只是描述性文档/契约描述写错、实现本身自洽 ⇒ P2 且明确写"无需改实现"；若实现真的少了规范要求的取值或语义 ⇒ 按行为影响升级。措辞里要把差集写全（"四个中的两个错误类别"），不要写"减 X"，否则读者无法判断还有哪些值不可达。

<a id="exp-064"></a>

## 冗余实现会让单行变异失效：验证回归保护应回退整文件而非改一行

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #2089`（head `de5cc27b`，`runtime/topic_memory_processing.py` 的 internal_ids 传递）、`applies_to: 判断"新增测试是否真的保护了本次修复"，尤其修复点可能有多处冗余登记时`、`recheck_when: 方法类，长期有效`。
- 现象：把新增的那一行（`internal_ids=(*internal_ids, *(item.proposal_id for item in inputs ...))`）删掉，目标用例仍全绿；再把同函数上游的 `known_ids.update(...)` 也删掉，仍全绿。原因是这两处互为冗余——任一条都能让被测 ID 进入白名单，单行变异被另一处遮蔽，于是"变异不红"并不意味着测试无效。
- 正确做法：用 `git show <pre-fix-sha>:<path>` 把**整份**文件（必要时连同其依赖的 admission/validation 文件）回退到修复前版本，只保留 head 的测试，再跑同一批用例。本例这样得到 `14 failed / 72 passed`，且失败项精确覆盖两个线程场景（5 个 `test_generation_retains_stage_ids_and_merged_inputs` 参数 + 解码证据/展示包裹用例）⇒ 反证成立。
- 判据：单行变异全绿时先问"这个修复是否被别处重复提供"，而不是直接判定测试无效；只有在整文件回退仍全绿时，才可写"测试不保护该回归"。
- 评论写法：把两种结果都写清（单行变异不红的原因 + 整文件回退的失败清单），否则读者会以为你只做了形式化验证。

<a id="exp-070"></a>

## 度量产物带 `code_sha` 只解决可追溯，不解决"是否仍描述当前代码"

评估/基准类 PR 常把 report.json 作为受版本控制的证据提交，并记录 `code_sha`。审查时容易止步于"产物与 manifest 哈希自洽"。

- **实战（PowerContext PR #2122，2026-10-23）**：`tests/test_replay.py` 的期望被 merge 解析从 `text_carriers == 2` 改成 1（上游运行时不再重复正文），CI 的 `evaluation-tests` 真的执行该用例且绿 ⇒ head 只能得到 1；但提交的 `report.json` 里同一 arm 的 38 行仍全是 2，`code_sha` 固定在该 PR 首个提交。报告自带 harness README 写明"code 变更即拒绝重放、不要复用旧输出"。
- **判据**：先确认 CI 的选择集是否真的包含被测断言（`make evaluation-unit-test` 里是否显式列出该目录、是否 `-m "not live"`、是否装齐 extra），再用"CI 绿 ⇒ 断言值即 head 值"反推产物是否过期。只看 report 内的哈希自洽会漏掉这一类。
- **处理**：能行内锚定就用期望值变更的那一行发评论；建议二选一——同 PR 内重跑并更新 report（`code_sha` 随之前移），或明确标注该指标描述的是哪个提交。

<a id="exp-072"></a>

## 复核「已回复线程」时 head 只是 merge 上游：先逐文件比对 PR 侧 blob，再决定重跑范围

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2096`（`1072176e` → `b5027a03`，后者是前者 merge `upstream/master`，中间层 434 文件变更）、
  `applies_to: 作者用 `Merge remote-tracking branch 'upstream/master'` 推进 head 的回复核验`、`recheck_when: 方法类，长期有效`。
- 现象：head 变了、`git diff <old> <new>` 有几百个文件、CI 全部重跑，很容易被当成「必须全量重审」而放弃复用，或反过来只看 commit message 就断定「只合了上游、未改代码」。
- 判据：`git diff --name-only <old> <new> -- <本 PR 文件清单>` 为空**不等于** PR 内容未变（上游可能改到同文件），正确做法是逐文件比 blob：
  `git rev-parse <old>:<path>` 与 `git rev-parse <new>:<path>`，全等才可复用该文件的源码证据与探针结论。本例 7 个 PR 侧文件全部全等
  （`cache.py` `6b3da96b`、`tests/builtin/test_code_publication.py` `fa34e377`），于是源码证据整体复用、只补一次当前 head 的探针实跑与 CI 重取。
- 报告口径：写「head 变更是 merge 上游，PR 侧 N 个文件 blob 未变」，并另列新 head 的 CI 结论；新 head 的 CI 若仍在跑，明确写成验证缺口，
  不能拿旧 head 的绿 check 顶替（`R02` 的快照语义）。

<a id="exp-075"></a>

## 结合性/优先级类断言先跑一行探针，别用"看起来属于哪个分支"定级

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2188`（`desktop/src-tauri/src/ipc.rs::allowed_navigation`）、`toolchain: rustc 1.96.0 / Windows`、`applies_to: 任何"某条件被挤出作用域/未生效"的语法层推导`、`recheck_when: 方法类，长期有效`。
- 事实：Rust 中 `let p = if c { a } else { b } && x;` 的 `&&` 作用于**整个 if-else 表达式**（实测 `if true { true } else { false } && false` → `false`）。因此"端口检查只看得到 else 分支"这类读法不成立；靠缩进/视觉结构判断会既可能误报回归，也可能掩盖真实的测试缺口。
- 手法与成本：把可疑表达式抽成独立的几行 `main.rs`，本机 `rustc main.rs -o probe && ./probe` 即可（无需 cargo、无需依赖）。同一手法适用于三元/空合并（TS `a ?? b || c`）、`match` 后接运算符等。
- 报告口径：先用探针证明"当前行为正确"，再把 Finding 落在**回归保护**上（缺负向用例 + 结构易被后续改动破坏），并按 P2 定级；不要写成"功能回归"。

<a id="exp-077"></a>

## 归档副本缺少 `.git` 时，用「哑 gitdir + alternates」满足被测试代码的 `git rev-parse`

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2122`、`applies_to: 用 `git archive` 解压的只读副本中，测试/工具会调用 `git -C <root> rev-parse HEAD` 的场景`、
  `recheck_when: 测试改为读取环境变量或清单文件获取 commit`。
- 手法（不改主证据副本）：在 `probes/` 下建一个哑 gitdir：
  - `HEAD` 内容必须是 `ref: refs/pr/<N>`（直接写 SHA 会报 `not a git repository`）；
  - `objects/info/alternates` 指向共享裸克隆的 `objects`（用 `D:/...` 形式，别用 `/d/...`）；
  - 仍需真实 ref 文件 `refs/pr/<N>`（内容为 SHA），否则 `rev-parse HEAD` 报 `unknown revision`。
- 运行方式：`GIT_DIR=<哑 gitdir> PYTHONPATH=... pytest ...`，子进程继承 `GIT_DIR`，测试内的 `git -C <root>` 因此可用。
  全程不动 `source/` 的受版本控制文件、索引与 refs（`R04`）。

<a id="exp-078"></a>

## PR head 是 merge commit 时，`gh pr diff` 展示的是「冲突解析结果」，其中的删除往往是合并丢代码

**现象**：`gh pr diff` 里出现一行看似作者主动的删除（例：`-        mode, vector, query_embedding, embedding_calls, embedding_fallback = await ...` 变成四元解包），
但分支自己的提交从未碰过该行；真实原因是一次 `Merge branch 'master' into <branch>` 的冲突解析，把 master 上新增的返回值/传参丢掉了。

**判据与手法**（都只读，不改主证据副本）：

1. 先看 head 是不是 merge commit：`git log -1 --format='%H parents=%P' <head>`。两个父提交 ⇒ Diff 基准按 `merge-base(baseRefOid, head)` 取，
   当 master 已被合入 head 时，该基准通常就是被合进来的 master 提交本身，于是 `gh pr diff` 实际在展示「master 版本 → 冲突解析结果」。
2. 直接把两份 blob 对起来看，比读 hunk 更准：`git diff <merged-master>:<path> <head>:<path>`，再用
   `git show <merged-master>:<path> | grep -n '<symbol>'` 找被丢的赋值/传参是否在别处仍被引用。
3. 多返回值函数是重灾区：只删了左侧解包目标、右侧仍 `return a, b, c, d, e` ⇒ 每次调用抛
   `ValueError: too many values to unpack (expected 4)`；只删了赋值、右侧仍在别处 `kwarg=<name>` ⇒ `NameError`。
   两者都可能被「先抛的那个异常」掩盖，所以**要同时核 `return` 点与所有使用点**，不要只修一处。

**定位速度**：先在本地 exact head 树跑本 PR 自己新增的测试（新用例常直接踩中）；再在 CI 日志里
`grep -c "too many values to unpack"` 与 `grep -n "FAILED tests"`，若同一 head 几十次命中，就是合并解析错误而非环境抖动。

**反例边界**：不能因为 `gh pr diff` 里有删除就判作者改了逻辑；也不能因为本地只跑了一条用例通过就认为 head 自洽——先确认 head 是否刚 merge 过 master。

关键词：`validated_at: 2026-10-24`、`validated_ref: PR #2192 head 7cb90431f3ba7b03c8e1e06f05a073c85fb24256`（父提交 `8f44c20f` + `1da99747`，
`src/powercontext/builtin/runtime/atomic_memory.py:590` 与 `:675`）、`applies_to: 任何 head 为 merge commit 的 PR`、
`recheck_when: 无（判据与 Git 对象语义绑定）`。

<a id="exp-083"></a>

## 一处修复改到多条等价分支时，对**每条分支**分别做变异，并跑该模块的整个相关选择集

现象：某 PR 为同一语义修正了两处实现（存储层 A 与查询层 B 各有一段「预算/额度耗尽后是否仍可用缓存值」的判据），
新增用例只构造了 A 先成功、B 后超时的顺序。把 A 的判据回退成修复前形态，新增用例精确打红（`1 failed`）；
把 B 的判据回退成修复前形态，把目标文件、同主题的 timeout 测试文件与该配置的单元测试一起跑，仍是 `53 passed`，
与 head 逐条相同 —— 说明 B 侧改动完全没有回归保护，而且新加的文档句对 A、B 两个通道同时成立。

判据与做法：
- 先按「同一个不变式 / 同一句文档承诺」把改动归组，再对每组各做一次单行变异，**不要只变异新增用例直接覆盖到的那一处**。
- 变异后的验证范围要覆盖该模块的**相关选择集**（目标文件 + 同主题测试文件 + 相关配置单测），只跑 `-k <新用例名>` 会把
  「同模块其它用例能兜住」和「完全没人兜」混为一谈。
- 报告时把两次变异的命令与结果并列写出来：一侧 `1 failed`、另一侧全套仍全绿，这个对照本身就是 Finding 的证据，
  比"建议补测试"有力得多。
- 反向也要核：若某侧变异不红但该分支本就不可达（死分支），那是另一类问题（可删除或与实现不符），定级理由要换成可达性论证。

关键词：`validated_at: 2026-10-27`、`validated_ref: #2231 head fdadc435`、`applies_to: 任意「一处修复多处分支」的 PR`、
`recheck_when: -`。

<a id="exp-084"></a>

## 枚举 merge commit 的"人工冲突解决改动"：把自动合并树复算出来逐文件比对

head 是 merge commit 时，`R` 提到的「diff 里的删除往往是合并丢代码」需要一种可枚举的做法，而不是靠读 diff 猜。
做法（无需 checkout，全部在裸克隆里完成）：

1. 取两个父：`git rev-list --parents -n 1 <head>`；不是两个父就跳过。
2. 复算自动合并：`git merge-tree --write-tree <parent1> <parent2>`，输出第一行就是 git 本来会生成的 tree OID。
3. 比实际 tree：`git rev-parse <head>^{tree}`。两者相同 ⇒ 没有任何人工解析改动，可以只按增量提交审。
4. 不同 ⇒ `git diff --stat <clean_tree> <actual_tree>` 精确列出人工改动的文件与行数，再对每个文件看 `git diff <clean_tree> <actual_tree> -- <path>`。
   这一步把"合并提交里到底被手工动了什么"从猜测变成清单，且与 diff 大小无关。

`2026-10-28` 实测（#2192 head `23c28277`）：相对自动合并树，人工解析额外删除了 `runtime/atomic_memory.py` 5 行、
`tests/e2e/test_recall_embedding_timeout.py` 45 行。前者删掉的是 `started = asyncio.get_running_loop().time()`，
而同一函数的 `embedding_wait_seconds = ... - started` 仍在 ⇒ 每次 `search()` 都抛 `NameError`（exact head 副本 8 failed，
master 同文件 7 passed）。后者删掉的正是另一 PR 刚合入、且**恰好覆盖这段计时**的用例——两处删除叠加，
使合并结果既坏又缺护栏。

判据：
- 只审"人工解析改动"这部分，不要被 merge commit 的总体 diff 体量吓退；也不要因为 `mergeable=true` 就认为合并是干净的。
- 删除型解析最危险：先看被删的行是否还被引用（赋值/变量/参数），再看被删的测试是否覆盖被改的生产代码。
- 「合并带进了对方的测试」与「合并把对方的测试删了」是相反的两件事，必须分别核对两棵树里该文件的行数与用例名。

关键词：`validated_at: 2026-10-28`、`validated_ref: #2192 head 23c28277`、`applies_to: 任意 head 为 merge commit 的 PR`、
`recheck_when: -`。

<a id="exp-087"></a>

## 并行 PR 各自 `mergeable: true` 不代表合并后能编译：必须比对被改函数的签名与调用点

GitHub 的 `mergeable` 只把 PR 与其 **base** 比较，看不到另一个并行 PR 对同一文件的语义改动。实测
`oceanbase/powercontext` #2306（head `05465421`）在 `desktop/src-tauri/src/connections/session.rs` 新增 5 处
`self.identity_unchanged(&api, &identity, generation)`（三参），而同期打开的 #2291（head `4bc80aac`）把同一函数改成四参
`identity_unchanged(&self, api, original, server_id, generation)` 并改写了全部既有调用点；两个 PR 与 master 分别都是
`mergeable: true`，但任一方后合入都会得到 `this function takes 4 arguments but 3 were supplied`，master 构建直接红。

判据与做法：
- 同批 review 里出现 ≥2 个 PR 改同一源文件时，逐个 `git diff <base> <head>` 取被改函数的完整签名，比对**新增调用点**的参数个数，
  而不是只看两侧是否都绿、是否都 `mergeable`。
- 冲突面不止文本：同一函数体内的不同补丁（本例 `if use_as_active` 内外各加一次 `inner.reports.remove(id)`）、
  同一 JS 函数的两套重写（`App.tsx::receiveState` 分别用 `acceptedGeneration` / `currentState` ref）、
  以及同一 e2e harness 方法（`installed_workflow.py::activate`）都会被 Git 判为"可自动合并"或需要人工解析，
  人工解析恰恰最容易漏参数。
- 定级参考：编译/构建必红按协调问题定 P2 并给出合入顺序与具体补参位置；若两边会**静默**产生不同语义
  （如迁移版本号撞号）则按 P1。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2306 head 05465421、#2291 head 4bc80aac`、
`applies_to: 同一仓库存在多个并行 OPEN PR 改同一批文件`、`recheck_when: 任一 PR 合入或 rebase 后`。

<a id="exp-088"></a>

## 生成物里的「契约摘要」不等于生成物：摘要校验通过 ≠ 产物已同步

新增/修改 API 契约后，仓库常见两类检查：① 生成器 `--check`（把重新生成的结果与提交物做**文本全等**比较）；
② 单独的契约测试（只比对生成物里的 `contractSha256` / digest 常量）。只做 ② 的仓库里，**手工改摘要**可以让 ② 通过，
而 ① 仍会红，于是"本地 `make check` 绿、CI desktop/host job 红"。

实测 `oceanbase/powercontext` #2270（head `11f4319c`）：`openapi/powercontext.yaml` 新增 4 个
`/v1/scopes/{scope_id}/operations*` path（+282 行），PR 只把 `desktop/src-tauri/src/transport/operations.json` 与
`desktop/ui/src/generated/operations.ts` 的 `contractSha256` 从 `c12901b8…` 改成 `c7f00e81…`，
`desktop/ui/src/generated/api.d.ts`（9344 行）完全没动 ⇒ 四个 desktop job（linux/windows/macos×2）
同签名 `Error: Contract drift: ui/src/generated/api.d.ts`。而 `tests/test_desktop_contract.py` 只校验摘要常量，
在 exact head 上 `2 passed`。

判据与做法：
- 先读生成器脚本的 `outputs` 表，确认**每个产物**从哪个输入生成、`--check` 的比较粒度（文本全等 / 语义 / 只比摘要）。
- 再列「谁校验这些产物」：若只有摘要常量被测试，而产物本身由另一条 CI 步骤比较，就必须以那条步骤的日志为判据。
- 只看 `git diff --stat` 会漏：本 PR 的 desktop 改动只有 2 行（摘要），漂移发生在**未出现在 diff 里**的文件。
  做法是把契约输入（openapi/schema）与生成物清单取交集，逐个确认"输入变了、产物是否跟着变"。
- 对照排除基线：取父提交与同期另一个同样改契约的 PR 的同名 job 结论。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2270 head 11f4319c / 父 feb9e7f2 / #2192 head 4028045f`、
`applies_to: 有代码生成链（openapi→SDK/宿主包）且提交生成物的仓库`、
`recheck_when: 生成器脚本的 outputs 表、--check 比较方式或契约测试范围变化`。

<a id="exp-090"></a>

## 伪造成 dist-info 会让 Typer 的 entry-point 命令全部不注册（2026-10-30 实测）

在隔离镜像里跑 CLI 子进程类 e2e 时，为省掉 `uv sync`（镜像缺 `.git` 会让 hatch-vcs 构建失败）常会手写一个
最小 dist-info。若只写 `METADATA`（Name/Version）+ `WHEEL` + 空 `RECORD`，`importlib.metadata.requires()`
返回空，`powercontext/cli/app.py::_load_command_providers()` 的 `_role_available(extra, requirements)`
对所有 extra 判 False ⇒ `server`/`config`/`setup` 等 provider 一律跳过，CLI 只剩内容命令。

表现为 e2e 报 `No such command 'server'.`，看起来像 PR 删了子命令，实际是环境残缺。判据：

- `python -c "from powercontext.cli.app import main; import sys; sys.argv=['pc','--help']; main()"` 手动看命令表，
  与 `pyproject.toml` 的 `[project.entry-points."powercontext.cli"]` 对照；表里少了 provider 命令就是环境问题。
- 补两样东西即可恢复：`METADATA` 里加 `Requires-Dist: powercontext[server,builtin]`（让 `_role_available`
  走 `name == "powercontext"` 的分支），以及 `entry_points.txt` 里照抄 pyproject 的 `[powercontext.cli]` 段。
- 更省事的替代：`UV_PROJECT_ENVIRONMENT=<venv 在镜像外> uv sync --frozen --no-install-project` 装依赖，
  再用 `PYTHONPATH=<mirror>/src` 跑；但**不要**因此认为 e2e 的 CLI 路径已验证——没装 dist-info 就跑不了。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2312 head 1e2538d7、WSL Ubuntu + Python 3.13 venv`、
`toolchain: uv 0.11.32 / pytest 9`、
`applies_to: 用 `python -c` 起子进程跑 CLI 的 e2e，且宿主用 editable 安装（editable finder 会遮蔽镜像 src）`、
`recheck_when: cli/app.py 的 provider 加载逻辑或 pyproject 的 entry-points 变化`。

<a id="exp-091"></a>

## `git merge-tree --write-tree` 的自动合并树里带着冲突标记，不能直接拿来判「删测试」

`git merge-tree --write-tree A B` 在两侧改动同一区域时，**仍然返回 tree OID**，只是冲突文件的内容里保留了
`<<<<<<< A` / `>>>>>>> B` 标记行。把它与人工解析后的 merge commit 树 diff，会看到成批的「删除」——那些
被删的行其实是冲突标记和另一侧的旧断言，不是作者删掉 master 的测试。

实测 `oceanbase/powercontext` #2004 的 merge commit `5da4f757`（父 `08a4386b` + master `90355b8e`）：
自动树 `1818f664` vs 实际树 `00088044` 统计出 `23 files, +94 −291`，其中 `tests/test_migration_revision_names.py`
的「−17」全部是标记行与被合并掉的旧 revision 断言；人工解析的结果是两侧并集（保留 master 的 `v1_4_1_005`
与本 PR 的 `v1_5_0_001`/`v1_5_0_002`）。

判据与做法：
- 先 `git grep -n '^<<<<<<< '` 检查自动树里是否残留标记；有标记就说明该 diff 只能用来**定位**人工解析了哪些文件，
  不能用来判断增删性质。
- 判「是否丢了 master 的改动」要正向核：把 master 侧新增的 revision/断言逐条在 head 树里 grep 到，而不是数行数。
- 真正要报的是「解析结果是否吞掉某一侧」；解析成并集属正常，不要因为 diff 里有大片 `−` 就报 P1。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2004 5da4f757（auto 1818f664 / actual 00088044）`、
`applies_to: head 为 merge commit、需要按 R-PC55 复算自动合并树的 PR`、
`recheck_when: git 版本的 merge-tree 实现变化（`--write-tree` 的冲突输出格式）`。

<a id="exp-092"></a>

## 一个大 PR 里出现两个同构目录时，先判「陈旧副本」再判「设计」

新增大功能 PR 偶尔会带进一份**本地误拷贝**：同一套源码在仓库里出现两次，其中一份是早些时候的快照。
它不会被任何构建或 CI 命中（没有 workspace 清单、没有 job），所以在 diff 里看着像正常新增。

判据（三步，全部只用 git，不需要 checkout）：
- **文件数 + 清单四件套**：顶层 `Cargo.toml`（workspace）、`README`、`.gitignore`、以及随后某个修复提交新增的
  测试文件。副本缺这几样，基本就是"拷完才提交"的形态。
- **逐文件 diff**：`git diff <ref>:A/path <ref>:B/path` 若出现成片的 `−N`（例如 60/38/32 行），说明副本停在某个
  历史 submit 上，而不是有意分流；**没有差异的文件反而是更强的证据**——纯重复，无任何设计理由。
- **构建归属**：`git grep -n cargo -- .github` 只有 desktop 的 job 命中 ⇒ 新 workspace 与副本都不参与构建，
  于是"CI 全绿"对这些文件既不是支持也不是反驳。

实测 `oceanbase/powercontext` #2307（head `301d54ef`）：`gateway/`（43 文件，含 workspace 清单、README、
`.gitignore`、`buffer_limit_nonstreaming.rs`）与误拷贝的 `powercontext/gateway/`（39 文件，四样全缺，
`ingress.rs` 少 60 行、`render.rs` 少 38 行、`reqwest_transport.rs` 差 48/32 行），后者新增 4901 行。

处理：报"整目录删除"，不要试图判定哪份"更正确"；若两份都有 CI 覆盖，则升级为需要维护者裁决的重复实现问题。
同时把"新 workspace 是否进入 CI"单列一条，避免用同一线程混谈两种根因。

关键词：`validated_at: 2026-10-31`、`validated_ref: #2307 head 301d54efc0ffd9b16f84518a0991731f19ef622a`、
`applies_to: 新增大目录/新 workspace 的 PR，尤其单 PR 新增行数 > 3k`、
`recheck_when: 仓库引入 `**/Cargo.toml` 或 monorepo 目录扫描类检查后`。

<a id="exp-093"></a>

## 判「PR 的红 job 属于 base」：用 base commit 的 push run 做 job 名集合差分，再抽一条签名

现象：一个只改 `integrations/**` 与文档的 PR 出现 `tests (3.11..3.14, unit)`、`quality`、
`Upgrade release gate`、`upgrade-acceptance / Prepare upgrade artifacts and matrix` 七项红；
另一个改 desktop 的 PR 是同一批七项。直觉上"两个 PR 都红"更像基线，但要给出证据。

做法（比逐个翻日志快，且不依赖猜测）：

1. `gh api "repos/{o}/{r}/actions/workflows/master.yml/runs?branch=master&per_page=5"` 找 `head_sha`
   等于 PR 的 `baseRefOid` 的那次 push run。多 workflow 时对每个相关 workflow 各查一次
   （`e2e-harness.yml` 常单独红）。
2. `gh api ".../actions/runs/{run}/jobs?per_page=100" --paginate --jq '.jobs[] | select(.conclusion=="failure") | .name'`
   拿到基线失败 job 名集合，与 PR 的 `gh pr checks --json name,bucket` 失败集合做差：
   完全相同 ⇒ base 红，PR 不承担；差出来的项才是本 PR 引入，再拉该 job 日志取签名。
3. base 的 run 若是 `cancelled`，不能当"绿"用——换上一个成功的 master run，或明确记录该 job 的
   基线不可判定。

实测（`oceanbase/powercontext` 2026-10-31）：base `0c1dfc28` 的 master push run 41081320129 失败 job 集合
= PR #2322 / #2291 的七项同名 job；`e2e-harness.yml` 的 run 41081320353 只失败
`Recall effort (OceanBase)`，也正是这两个 PR 多出来的那项。另有 PR 的
`Atomic Memory clean migration (OceanBase)` 红是真实库 `(1205, 'Lock wait timeout exceeded')`
（`test_atomic_artifact_query...` 类用例不在该 PR 变更面内），属环境抖动，要单独说明而不是并进基线。

关键词：`validated_at: 2026-10-31`、`validated_ref: powercontext base 0c1dfc28 / PR #2322 d2d8c7b5`、
`applies_to: GitHub Actions + 分支保护未设 required checks 的仓库`、
`toolchain: gh 2.x`、
`recheck_when: workflow 名称或 job 矩阵调整、仓库启用 required_status_checks 后`。

<a id="exp-094"></a>

## `gh api` 的 POST 会出现 EOF，而 GET 正常：按请求重试，不要据此判断写操作失败

现象（`oceanbase/powercontext` 2026-10-31）：`gh api` 读请求偶发 `unexpected EOF`，写请求
（`POST .../pulls/N/comments`）连续 3 次 `Post "...": EOF`，第 4 次成功；同一时段的
`POST .../pulls/N/comments/{id}/replies` 一次成功。用裸 `urllib` 复现到
`http.client.RemoteDisconnected: Remote end closed connection without response`，说明是链路侧
中断而非 4xx/5xx。

处理：

- 写操作不要"失败即放弃"，也不要"失败即重复提交"——失败后先 `GET` 同名资源确认是否已落库
  （例如 `pulls/N/comments?per_page=100` 数量），确认未落库再重试；重试上限 4 次、间隔 5–6 s 足够。
- 一旦重试成功，用返回的 `id` / `html_url` 记录，不要再用列表接口的"最后一条"推断（并发会话会插队）。
- `gh` 的报错文本与 HTTP 状态不同：`EOF` / `unexpected EOF` 属传输层，不代表 422 行号失败，按 `R12`
  的行号失败处理流程会走错分支。

关键词：`validated_at: 2026-10-31`、`validated_ref: powercontext #2322 / #2004 评论发布`、
`applies_to: 本机 Git Bash + gh CLI 的 GitHub 写入`、`toolchain: gh 2.x / Python 3.14 urllib`、
`recheck_when: 换网络出口或改用 API 代理后`。

<a id="exp-095"></a>

## 生成器产物的复核可以完全不落地：用 blob 级复算代替 checkout

场景：仓库把若干 helper 源码集中到 `src/<pkg>/`，再由生成器抄进各宿主插件目录，`--check` 用一个需要 `.git` 的
`git ls-files` 做完整性扫描（powercontext #2318）。此时既不该在开发目录跑生成器，也不必为跑 `--check` 造一个
带 `.git` 的镜像。

做法（只需对象库）：

1. `git show <ref>:<源文件>` 取源码文本，按生成器的插入规则（本例：license 头之后、首个非 `#` 行之前插两行 marker）
   复算期望文本；
2. 对每个目标 `git show <ref>:<目标>` 逐字节比较，输出 OK/DRIFT；
3. 完整性另查一遍：`git ls-tree -r --name-only <ref> -- integrations/ | grep -E '/(helper1|helper2)\.py$'`
   与生成器的映射表比对，确认没有"存在同名副本但未登记"的宿主。

判据：12/12 逐一 OK 且映射表覆盖全部同名文件 ⇒ 可以断言"生成物与源一致、无漏登记"，比读 PR 正文的
"已重新生成"强得多。注意 `git ls-tree` 的 pathspec 别写成 `'integrations/*/plugins/*'`（git 的 pathspec 与
shell glob 语义不同，会返回空结果被误读成"没有副本"），用目录前缀 `-- integrations/` 再 grep 文件名。

关键词：`validated_at: 2026-10-31`、`validated_ref: powercontext #2318 head 62f23f2a`、`applies_to: 任意带生成器的仓库`、
`recheck_when: 生成器改用哈希清单或 `.gitattributes` 影响行尾时`。

<a id="exp-098"></a>

## 校验型守卫把「低危冗余」升级成「该 Scope 处理永久停摆」

现象：PR 新增一条输出校验规则（形状/一致性检查），单看 diff 只是"多拒绝一种模型输出"，CI 全绿，
新用例也只断言"该请求失败、游标不动"。实际后果是整个作用域的后续输入全部不再被处理。

判据（`oceanbase/powercontext` #2358，2026-11-01，head `9f6c39e4` / base `0a98473a`）：

- 校验通过 `output_check` 抛 `InvalidInferenceOutputError` ⇒ 模型在请求预算内可纠正；预算耗尽则整次
  `flush()` 失败。
- 关键在失败后的收口：该错误不在可缩减集合里（只有 `InferenceTimeoutError(operation="generate")` 与
  `atomic-memory-input-budget` 会缩窗并保存游标），于是窗口既不发布也不推进游标。
- 探针（同一 provider、同一 SQLite 路径）连调三次公共 `flush()`：head 3/3 失败、`cursor()==0`；再采集一条
  与该事实**无关**的 Source 仍失败 ⇒ 后续输入全被挡住。base 3/3 成功、`cursor()==2`。
- 另查预算下限：`max_requests` 常见定义为 `ge=1`，此时 `retries=max_requests-1=0`，模型一次都看不到反馈，
  守卫退化成硬失败。这一维度最容易漏——只跑默认配置的用例永远看不到。

做法：

1. 看到新增 `validate_*` / `output_check` 规则，先查该错误在调用方是否落在"可降级/可缩窗"的分支，
   而不是只看它是否被正确抛出。
2. 复现用**公共入口连续调用两次以上**，再加一条与失败窗口无关的新输入，证明不是"一次失败"而是"持续阻塞"。
3. 同时按最小合法配置（预算下限）跑一遍，区分"有纠正窗口"与"零纠正窗口"。

关键词：`validated_at: 2026-11-01`、`validated_ref: powercontext #2358 head 9f6c39e4 / base 0a98473a`、
`applies_to: 带输出校验与重试预算的生成管线（任一仓库）`、
`recheck_when: 校验错误被并入缩窗/丢弃路径，或处理器增加失败上限与降级策略时`。

<a id="exp-101"></a>

## 「缺陷所在文件不在 diff」不等于 Fallback：先找同根因的可评论行

`R11` 的 Fallback 门槛是「无法锚定到**任何**可评论的 Diff 行」。我把它读成「缺陷所在的文件不在
diff 内就进 Fallback」，于是把一个文档陈旧类 Finding 只写成 Conversation 评论。

GitHub 的硬限制确实存在，但只在**直接**锚定时生效：`POST pulls/{n}/comments` 的 `path` 必须出现在该 PR 的
files 列表里，`line` 必须落在该文件的某个 hunk（含上下文行）内，否则 422
`Pull request review thread line must be part of the diff`；`subject_type: "file"` 的整文件评论同样要求文件在 diff 内。
**没有**任何 API 能给未改动文件挂评论。

真正的做法是找同根因的另一处改动行：

1. 「第 N 份拷贝没同步」类 Finding 天然有多个落点。用 `git diff base head -- <doc>` 看 PR 实际改了哪几句，
   再把评论挂到**被改的那一句**上，正文里点名陈旧拷贝的 `文件:行号`。
2. 这不是错误归因——同根因、同句子、同一处判断，锚点只是"这句话被改过的兄弟副本"，同时给维护者一个
   在 `Files changed` 里可见、可 resolve 的线程。
3. 判据自检：发布前问一句「这个根因在 diff 内有没有**同一个事实**的其他表述？」先 `git grep` 关键短语的
   其他出现位置，再决定是 Fallback 还是换锚点。

反例（正确做法）`#2395`：陈旧句在 `tests/release_upgrades/README.md:10-11`（不在 diff），同句在
`docs/en/docs/operate/database-migrations.md:99` / `:115` 被本 PR 改过 ⇒ 挂 `:99`，正文引用 README 原文。

关键词：`validated_at: 2026-11-02`、`validated_ref: powercontext #2395 head c91bddcb（discussion_r4440199167）`、
`applies_to: 文档/清单/版本号多副本同步类 Finding，以及任何"缺陷位置在 diff 外"的情形`、
`recheck_when: R11 的 Fallback 判据被改写时`。

<a id="exp-102"></a>

## 「按结构判定同一布局」必须先确认比较是双向的：单向 `differences()` 看不见多出来的对象

现象：一个"宽松吸收历史库"的新分支让维护命令接受了本应拒绝的库，CI 里 5 条既有用例变红
（`DID NOT RAISE MigrationError` / `assert status.exit_code != 0` 得到 `0`）。

判据与三步诊断：

1. **读比较函数的方向**。名为 `differences(connection, expected)` 的实现常常只回答"expected 里有、库里没有或定义不符"，
   对"库里多出来、expected 没声明"的表/索引/触发器不作答（本例只把未登记的 trigger 算作问题）。用它当身份判据
   ⇒ 多一张表的库被当成同一布局。真正建立身份的是另一种手段（本例是整库 `sqlite_inventory` 指纹），回退到结构比较
   就等于把指纹这一层保护静默去掉。
2. **别只看新写的测试**。这类回归最容易由"旧契约的用例"抓到：`git grep -l 'never falls back' 或 'unknown_baseline'`，
   然后在**同一解释器下**分别跑 base 树与 head 树（`git archive` 到 `probes/base-<sha>`），差异即 PR 引入。
3. **CI 的 short test summary 比 job 名可靠**：`gh api repos/{o}/{r}/actions/jobs/<job_id>/logs` 里的
   `FAILED ...` 行给出精确用例与断言，能直接把"新能力"和"被取消的旧契约"对上。

写 Finding 时的定级口径：既有测试固化的"拒绝未知布局"属于安全/数据完整性边界，PR 静默放宽且不改写这些测试
⇒ P1（必测 job 红 + 契约被单方面取消），即使没有真实数据损坏路径。

关键词：`validated_at: 2026-11-02`、`validated_ref: oceanbase/powercontext #2394 head 86e53a30 / base 252ecac0（run 41414091139 job 125177588026）`、
`applies_to: 任何新增"结构/指纹回退"或"宽松吸收旧布局"分支的迁移、导入、schema 兼容层`、
`recheck_when: 比较函数改成双向、或框架改为按显式版本号而非结构判定来源`。

<a id="exp-103"></a>

## 回复线程的请求体只能是 `{"body": ...}`

`POST /pulls/{n}/comments/{id}/replies` 会拒收 `in_reply_to`（`"in_reply_to" is not a permitted key`），
也会拒收 `commit_id`/`path`/`line`/`side`（`"commit_id", "line", "path", "side" are not permitted keys`）。
落盘 payload 时只写 `body`；需要行内定位时才用 `POST /pulls/{n}/comments`。

**路径必须带 PR 号**：2026-11-17 实测把 replies 也写成「全局形」`POST /pulls/comments/{id}/replies` 会直接 404
（`gh: Not Found`），且耗时一轮才定位。这与单行评论的 PATCH 恰好相反——`PATCH /pulls/comments/{id}` 才是全局形，
`PATCH /pulls/{n}/comments/{id}` 才是 404。两条路径的「全局 vs 带 PR 号」不可互推。

关键词：`validated_at: 2026-11-02`、`validated_ref: GitHub REST pulls comments reply 端点`、`applies_to: 所有行内线程回复`。

<a id="exp-104"></a>

## 重试循环里的「恢复动作」自身会失败：`check=True` 把可恢复失败变成整轮中止

审「失败后清理再重试」的实现时，恢复动作（detach / unlink / kill / rollback）与原操作**同等**需要失败语义，
不能假设恢复一定成功。2026-11-04 #2306 head `5f783f29` 实测：`desktop/scripts/build_macos.py:55` 用
`subprocess.run([hdiutil, "detach", "-force", dev], check=True)` 清理 busy 的临时 DMG；该 detach 在 macOS runner 上
返回 16（图像仍被占用，日志里随后出现 `Terminate orphan process: ... diskimages-help`），`CalledProcessError`
从 `main()` 的 `for attempt in range(1,4)` 逸出 ⇒ attempt 1/3 即 exit 1，第 2、3 次与后续 `bundle` 重试都没跑。

- 判据：①恢复动作是否 `check=True` / 抛异常；②异常能否被重试循环捕获；③调度层是否有「恢复失败就放弃」的显式决定。
  与它替换掉的「只 grep 日志再重试原命令」的实现对比，若恢复路径更脆，就是回归。
- 常见反证缺口：测试里的假工具（`hdiutil`、`rsync`、`kill`）只断言参数后 `exit 0`，从不返回非 0 ⇒ 恢复失败分支零覆盖。
  审查时要求「恢复动作返回非 0 仍有后续 attempt」的用例。

关键词：`validated_at: 2026-11-04`、`validated_ref: oceanbase/powercontext #2306 head 5f783f29（run 41803592923 job 126498786985）`、
`applies_to: CI 重试脚本、构建/打包恢复逻辑、任何「先清理再重试」的代码`、
`recheck_when: 该脚本改为在恢复失败时回退到全量重试，或测试补上非 0 恢复用例`。

<a id="exp-105"></a>

## 某行「看起来没改」但 base 已改：用 `git log -S` + merge-base 判差异来源

PR 的 diff 里出现一行旧写法（例如只匹配一种错误文本的 `grep`），先别当成 PR 引入的缺陷，也别当成基线问题：

```bash
MB=$(git merge-base <master> <pr-head>)
git cat-file -p $MB:.github/workflows/desktop.yml | grep -n '<旧写法>'   # merge-base 是什么
git log --oneline -S'<新写法片段>' -- <file>                              # 谁在 base 上改的
git cat-file -p <master>:.github/workflows/desktop.yml | grep -n '<该行>'  # master 现在是什么
```

2026-11-04 #2393（head `ffc80542`）即此形态：head 是只匹配 `create failed` 的 `grep -Fq`，master `2853ed98` 已扩成
`grep -Eq "(create failed|couldn't eject)"`，而 merge-base `e192e08c` 仍是窄写法 ⇒ 差异来自 base 前进，GitHub 报 `dirty`，
冲突正好落在这行。定级按「合并时若取 PR 版本是否丢能力」判 P2，并要求补上被丢形态的用例；不要按「PR 引入回归」定 P1。

关键词：`validated_at: 2026-11-04`、`validated_ref: oceanbase/powercontext #2393 head ffc80542 / master 2853ed98 / merge-base e192e08c（评论 r4466579605）`、
`applies_to: `mergeable_state=dirty` 且 diff 内出现明显落后写法的 PR`、`recheck_when: 该 PR rebase 后重新核对`.

<a id="exp-106"></a>

## 反证不必回退文件：在同栈的另一个 PR head 上跑当前 head 的测试（2026-11-05 实测）

- 触发：修复跨多个文件时（如加密回执的 target 绑定要在 `context_check.py` 的签发与校验两处同时改），单行变异会被另一处遮蔽，
  逐文件 `git show <pre-fix>:<path>` 回退要改好几处、还容易漏依赖文件。
- 手法：先找一个**不含该修复**的 head 当对照树。2026-11-05 的 #2429 与 #2435 共享 9 个提交，#2429 head `dfbce7e0`
  只多出 target 绑定等 6 个提交 ⇒ #2435 head `ce0e256f` 就是天然对照。用
  `PYTHONPATH=<对照树>/src <venv>/python -m pytest <head 的测试文件>`：对照树 `FAILED … Right contains one more item:
  'encrypted-origin-unverified'`，真实 head 同文件 `24 passed` ⇒ 该用例确实能检出缺陷。
- 先验证对照有效：`git log <merge-base>..refs/pr/A` 与 `..refs/pr/B` 求提交集合差，确认对照 head 缺的正被验证的那个提交。
  否则它可能只是别处有等价实现，红绿都说明不了问题。
- 读法：对照 head 可能同时缺别的改动，只看到红不够——回读失败断言与行号，确认失败点落在目标判据上（本例失败项正是新增的 reason code）。
- 局限：两 PR 无共享栈、或修复已在 master 时，退回整文件回退手法；两种都全绿才可写「测试不保护该回归」。

关键词：`validated_at: 2026-11-05`、`validated_ref: oceanbase/powercontext #2429 head dfbce7e0 对照 #2435 head ce0e256f（回复 r4479142259）`、
`applies_to: 跨文件修复的回归保护判定`、`recheck_when: 两个 PR 合并后对照树消失`。

<a id="exp-117"></a>

## 纯性能 PR 的"机制无断言"缺口：用退化变异判定测试是否真的覆盖了新机制

现象：一个只改性能的 PR（分片布局、缓存键、批处理边界）通常只补"结果不变"的用例；这类用例在机制被整体撤掉后
依然全绿，因此无法证明机制存在。本次实例：把"每个 Scope 一个 hashed rowid 区间"退化为"所有 Scope 共用一个区间"
（保留全部身份过滤），`pytest -k sqlite_fts` 仍然 7 passed（oceanbase/powercontext #2532）。

判据与做法：对纯性能改动先做一次"机制退化变异"——在 `probes/` 里把新机制等价替换成它要替代的旧形态
（共享区间、全局序号、无缓存、批大小=1），保持其它语义不变，只改一处，然后跑该 PR 新增的用例。

- 全绿 ⇒ 机制没有断言，属测试强度缺口（`R06A` 的"能否检出原缺陷"同样适用于性能机制），可提 P2 并建议补
  直接约束机制的断言（如两实体区间不相交、写入后回读的键落在自己区间内、缓存命中计数）。
- 变红 ⇒ 机制已被覆盖，只需复核该用例是否走生产入口。

替代证据的边界：PR 正文里的 EXPLAIN QUERY PLAN（`SCAN … INDEX 0:` → `INDEX 0:><`）能证明"游标确实被收窄"，
是复杂度/B 计划层面的有效证据，但不能替代回归保护——plan 不会被 CI 断言，退化后没有任何红灯。
两者要分开陈述，不要把 plan 证据当成"测试已覆盖"。

相关：`review.md` `R06A`（测试真实性）、§4 性能类必须给出量化。

关键词：`validated_at: 2026-11-08`、`validated_ref: oceanbase/powercontext #2532 head b7dcaffb（probes/mutant_shared_band.py，7 passed）`、
`applies_to: 只改性能/布局而不改外部行为的 PR`、`recheck_when: 该 PR 补了机制断言，或该变异在后续 head 上变红`。

<a id="exp-118"></a>

## trace 拓扑型的契约 e2e：先用「单用例 base/head 对照」归因，别当基线抖动放过

现象：一个性能重构把取锁（`async with lock` / `_locked()`）从 stage span 之外挪到之内，功能与断言都正常，唯一红的是一个
「span 形状」用例（`_only_child(parent, "scope.lock")` → `assert 0 == 1`）。这类失败在日志里只显示一个 assert，很容易被
当成本地环境差异或 flaky 跳过。

判据与做法：

- 找失败点所属的契约断言，而不是先看被测逻辑。`span` 的父节点取决于**进入上下文时**的当前 span，所以任何
  "把 A 的上下文挪进 B 的 with 块"的重构都会静默改父节点。
- 归因成本极低：只跑那一条用例。`head` 红 + `merge-base` 绿 ⇒ PR 引入；两边都红 ⇒ 基线或环境。本次
  oceanbase/powercontext #2567 为 `head 1 failed 42.63s` / `merge-base 2291237a 1 passed 28.82s`，与 CI 日志同签名。
- 定级不要按"只是 trace 形状"降级：它红的是强制 e2e 作业，且该作业红会让同 workflow 的 suite job 因
  `contains(["success","skipped"], needs.tests.result)` 整批 skip，等于该 head 的全部验收证据清零。
- 本条同样适用于 metrics label、审计事件字段顺序等"可观测面即契约"的断言。

相关：`review.md` `R06A`（测试真实性）、`R15`（CI 结果可判定性）、§4 P1 的"使强制门禁失败"。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2567 head d47f4279（tests/e2e/test_observability.py::test_memory_write_stage_spans_are_bounded_and_nested）`、
`applies_to: 任何把锁/事务/子调用包进另一个 span 或 stage 的重构`、`recheck_when: 该契约用例被重写，或 span 拓扑不再被断言`。

<a id="exp-120"></a>

## 回复线程复核：三类容易被漏掉的"假修复"

前三类都是本仓库 PR 上实测命中的形态，复核时逐条对照，不要只看 diff 有没有动。

1. **元信息层假修复**。对方回复"我会改标题和正文去掉 `Implements issue #N`"，但只核代码就会漏。必须回读
   `GET /repos/{o}/{r}/pulls/{n}` 的 `title` / `body`，并与回复的 `created_at`、PR 的 `updated_at` 比对：
   `updated_at` 晚于回复而 title/body 文本未变 ⇒ 不是"还没推"，是没改。本次 #2568 即如此（head 与回复时
   `commit_id` 完全一致，`f4b5455b`）。
2. **门禁红的下游连锁，不是独立缺陷**。`.github/workflows/master.yml::upgrade-release-gate` 的判定是
   `if quality==success && UPGRADE_SELECTED==false → 期望 skipped，否则期望 success`；而 `upgrade-acceptance`
   自身 `if` 还要求 `needs.tests.result ∈ {success, skipped}`。于是 **tests 红/取消 ⇒ upgrade-acceptance 被 skip
   ⇒ selected=true 时 gate 必然红**。看到 gate 红先去 `needs.tests.result` 找上游，不要把它当独立 P1 记账。
3. **预算类断言必须做变异验证**。只跑绿说明不了回归保护存在。做法：把 workflow 里被断言的 `timeout-minutes`
   改小（本次 125→100、40→30），重跑该用例；必须转红，否则断言是空壳。本次 #2515/#2526 均转红。
   `2515::test_all_oceanbase_migration_step_budgets_...` 内部会 `subprocess` 起 `pytest --collect-only`，
   在隔离镜像里必须同时设 `os.environ['PYTHONPATH']`（Git Bash 里 `PYTHONPATH=a;b` 会被吞掉，子进程报 exit 4），
   否则是"环境性红"，不是产品缺陷。

判据与做法：

- 每条回复先归类：**代码层**（改实现/加用例）、**元信息层**（标题/正文/标签）、**承诺延后**（"后续 PR 做"）。三类都要落到
  "当前 head 上可验证的事实"，承诺延后一律记"未解决"，因为 head 上没有可交付物。
- 归因 CI 红之前，先拉 master 同 commit 的 check-runs 做基线：本次 master 自身 30 个红（Acceptance oceanbase/sqlite、
  code-seekdb、opendal-package 等），PR 上同名红点因此不可归因于 PR；只有 master 绿的作业在 PR 上红才是 PR 引入。
- 分支落后也要单独记：`rev-list --count pr..master` 与失败文件在落后区间内是否被成对修改（#2532 落后 14 个提交，
  `jev_reranking.py` 与失败用例同批改动 ⇒ 期望不一致属基线陈旧，需 rebase 复跑，不能记成 PR 缺陷）。

相关：`review.md` `R02`（实时状态快照）、`R06A`（测试真实性）、`§9`（merge 口径：线程解决 ≠ 可合并）、`§11`。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2568 / #2532 / #2515 / #2526`、
`toolchain: Windows Git Bash + Python 3.14 venv（uv sync --no-install-project，无 wheel 遮蔽）`、
`applies_to: 所有"已回复 review comment 的复核"轮次`、`recheck_when: master.yml 的 gate 表达式或 upgrade-release.yml 的 if 变更`。

<a id="exp-121"></a>

## 判"行为保持不变的重写"：把 base 版本原样复刻成函数，跑同一批变异输入做差分（2026-11-10 实测 #2518）

PR 重写校验器/判定器并声称"语义不变"（#2518 把 `mysql_schema.compatible_inventory` 从 deepcopy+剪枝改成按需归一化）时，
逐行读 diff 只能得到"看起来等价"。可靠做法是把 base 实现搬进 `probes/` 的探针脚本（直接复制旧函数体，它依赖的
`_matches`/`digest` 通常仍在模块里），再用真实清单生成变异矩阵，对每个输入同时跑新旧两版比布尔结果：

- 变异矩阵取自真实期望清单，而不是手搓字典：多余可空列 / 多余 NOT NULL 无默认列 / 多余带默认非空列、多余非唯一索引 /
  多余唯一索引、多余表、多余 view、绑定受管表与不受管表的触发器、check 改名、删 check、删表、删列、删索引、
  backend 默认 charset/collation、缺顶层键、多顶层键，再叠 N 条随机结构变更。
- 同时单独断言 **新实现不改写入参**（调用前 `before = deepcopy(x)`，调用后 `x != before` 即报），否则"输入被就地改掉"
  会让后续 case 全部失真，而布尔比较仍可能全绿。
- 实测产出：#2518 78 个 case 只有 1 处分歧，且是畸形输入（缺 `views` 键时旧版抛 `KeyError`、新版返回 `False`）⇒ 属改进，
  可判"重写等价、无需 Finding"。这类结论比"代码看起来一致"强得多，也能直接写进 review 结论。

踩坑：辅助函数常不在原模块（`server_bundle` 在 `migrations.deployment`，`digest` 在 `migrations.models`），按测试文件的
import 抄；生成器里 `del`/`next(iter(...))` 打到不存在的键会把 `StopIteration` 变成 `RuntimeError`，先判存在再删；
旧实现抛异常的分支要 `try/except` 记成"异常类型"而不是让探针崩掉。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2518 head 716ff071`、
`toolchain: WSL + _shared/venv-wsl（3.13.11），PYTHONPATH=<mirror>/src`、
`applies_to: 校验器/兼容性判定/去重逻辑的重写与"纯性能优化"PR`、`recheck_when: 探针依赖的私有 helper 被改名或签名变更`。

<a id="exp-123"></a>

## 基线归属要落到 step / 用例粒度：同名 job 在 master 红，不等于同一处失败

**现象**（2026-11-11，oceanbase/powercontext）：`dsh-package` 在 master（`d64381bf`）上是红的，看起来可以整体归为
基线问题；但逐个 job 读日志后，三个 head 红在不同 step：
- master：`make js-test` → `tests/status-http.spec.ts` 断言 `expected 'skipped' to be 'appended'`；
- #2539 `f7bdb2e5`：已越过 js-test，红在 `make dsh-runtime-test` 的
  `tests/runtime/setup.test.mjs`「setup validates native include trees…」（`powercontext setup dsh` 退出 1）；
- #2306 `e9dfcbd9`：红在 `tests/test_dsh_transport.py::test_explicit_web_doctor_does_not_read_desktop_environment_profile`
  （doctor 报 `plugin_memory_protocol: unverified`，`SystemExit(1)`）。

**判据与处理**
1. 取 `repos/{repo}/commits/master/check-runs?per_page=100`（必要时 page=2）拿 master 的 job 结论，而不是只看 PR 的 rollup。
2. 对每个红色 job 再取 `actions/jobs/{id}/logs`，用 `grep -nE "not ok|FAIL |make: \*\*\*|FAILED "` 定位**具体 step 与用例**。
3. 只有「同 step + 同用例」同时命中才算基线；仅 job 同名时写「该门禁在当前 master 与各 head 上均不稳定，本次不归因于 PR」，
   并把它记成验证缺口，不要写成「基线问题、不影响本 PR」。
4. 反过来也成立：PR 越过了 master 红的那个 step，说明它红在别处，不能借 master 的红给 PR 免责。

**为什么值得记**：`if-no-files-found`、`needs` 级联、聚合 job 都会让「整体红」停在 job 名上；一条错误的基线归属会同时
放掉真问题和误伤无关 PR。

关键词：`validated_at: 2026-11-11`、`validated_ref: oceanbase/powercontext master d64381bf / #2539 f7bdb2e5 / #2306 e9dfcbd9`、
`applies_to: 任何用 GitHub Actions 结论做基线归属的场景`、
`recheck_when: 仓库把 dsh 门禁拆成独立 workflow，或 master 常态绿之后`。

<a id="exp-126"></a>

## 复核「生成物是否重生成」：把生成器依赖装到被检 package.json 的同级独立目录（2026-11-12 实测 #2270）

- 现象：在被检目录内直接 `npm install <tool>` 失败，`verbose stack TypeError: Cannot read properties of null
  (reading 'edgesOut')`（npm 10.9.7 / node 22.22.2；该 `package.json` 的 devDependencies peer 树过大时触发，
  与待装工具无关）。
- 处理：把被检子目录复制到探针根，在**探针根**放一个最小 `package.json`（`{"type":"module"}`），在那里装工具；
  node 的 ESM 解析会向上找到 `node_modules`，脚本里基于 `import.meta.url` 的相对路径不受影响。
- 若脚本同时生成与本次风险无关的重型产物（需要 jar、编译器或外部 CLI），先剔除该 output 再跑 `--check`，
  并在报告里写明未覆盖项；剔除前后都要记录脚本哈希。
- 判据：`--check` 类门禁必须 exit 0 且打印其成功行（本次 `Desktop contract matches OpenAPI.`）。
  「相关常量已改」「单测只比对常量」都不能替代该门禁——手工改摘要恰好会让只比常量的测试通过。
- **给门禁脚本打桩时，补丁本身也会被门禁检到（2026-11-13 实测 #2270）**：若脚本把自身源码的一部分
  （license 头、banner、生成器版本号）写进产物，任何"用宿主默认换行改写脚本"的补丁都会让产物变形，
  `--check` 报 drift 且 diff 只落在产物头部。判据：drift 的区域若正好是脚本自引用的那段文本，
  先比对补丁后脚本的 `\r\n` 计数（Windows 上 `Path.write_text()` 默认 CRLF），再谈被测产物。
- 仓库专属执行细节（命令、版本、覆盖范围）见 `review-oceanbase-powercontext.md` 的 `R-PC114`。

<a id="exp-127"></a>

## 「完整性守卫」要读记录侧的 loss 声明，而不是只重新遍历一次输入（2026-11-12 源码级判断 #2435）

**现象**：PR 新增一个守卫 `represents_turn(request, transcript, list_key)`，语义是「这份结构化记录是否完整呈现了
模型看到的那一回合」，只有为真才允许复用会话前缀抽取记忆。守卫逐个 item 检查 `content.first()` 是否为文本，
看似对齐记录侧的渲染规则，实际漏两类：

1. **渲染侧丢内容但不记 loss**：记录投影对 `ItemKind::Message` 只取 `role == "assistant"` 的文本
   （`assistant_text`），其余 role 返回 `None` 后走 `unwrap_or_default()`，既不产生 step 也不置任何损失标志；
   守卫端只校验「content 是文本」，于是这段被丢弃的文本仍被判为已呈现。
2. **守卫不读已经算好的 coverage**：同一文件里另有 5 处只置 `unmeasured_projection` 的分支（多部件 message、
   未测量的调用载荷、未知 output 等）。守卫只查 `omitted_steps` 与文本里的截断/省略标记，不读
   `losses.declaration()`，这些形态目前只是被类型分支偶然挡住，任何新增的 lossy 分支都会漏过。

**判据与处理**
- 审查「完整性 / 资格 / 可复用」类守卫时，先找出记录侧已经产出的损失声明（`CaptureLosses`、coverage、warnings、
  `omitted_*` 计数），确认守卫读的是它；只重新遍历输入结构的守卫一律按「与实际投影不同源」处理。
- 两侧规则必须同源：守卫里的 role/类型过滤要与渲染函数用的是同一个谓词，不能各写一份。
- 提 finding 时给出「哪条输入形状会被判为完整但记录缺内容」的具体 item，并要求补一条反证用例
  （构造该 item，断言守卫为 false 且不产生下游句柄/资格记录）。

**关键词**：`validated_at: 2026-11-12`、`validated_ref: oceanbase/powercontext #2435 head fed3a4d9`、
`applies_to: 证据捕获 / 审计记录 / 缓存复用类「完整性守卫」，不限语言`、
`recheck_when: 该仓库的 transcript 投影或 represents_turn 的判据变更`。

<a id="exp-129"></a>

## head 是 `Merge upstream/master` 时：先用「四 blob 比对」判定能否复用旧审结论，再谈增量（2026-11-13 实测 #2527）

**现象**：PR `fix/python-adapters-trust-notice` 的 head 从 `59205a11`（已审）变成 `5b9532ff`，提交信息是
`Merge remote-tracking branch 'upstream/master'`。`git diff <旧head> <新head>` 有 131 个文件、+6256/−251，
看起来像大规模改动；实际 `git diff <当前master> <新head>` 只有 18 个文件，与 PR 自身的 changedFiles 一致。

**判据（三个数 + 一次四 blob 比对）**
1. 先算 `merge-base(master, head)`。若它 **等于** master tip，说明分支已合入上游，PR 的 diff 就是增量本身。
2. 再跑 `git diff <旧审 head> <新 head> -- <PR 自己的文件清单>`。**输出为空** ⇒ 这 18 个文件的字节与旧审时
   完全相同，旧审的源码级结论（含已跑过的测试结论）在 `R02` 意义上可复用；131 个文件全是 master 带进来的。
3. 只剩一个回退风险：合并在冲突文件上可能**用 PR 侧覆盖 master 的新改动**。对 18 个文件逐个取四个 blob
   （`head` / PR 侧父提交 / 当前 master / 旧 merge-base）比对：只要没有「master 相对旧 merge-base 变过」的
   文件，就不存在静默回退；若存在，必须逐行确认 PR 侧版本是否包含 master 的改动。

**反面样本**：只看到 `git diff 旧head 新head` 的 131 个文件就判「改动很大、需要重审」会白跑一轮；
反过来只看到 `merge-base == master` 就判「等于增量」会漏掉「两边都改同一文件、合并时整文件取一侧」的回退。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2527 head 5b9532ff / 旧 head 59205a11 / master 1cb0e75d`、
`applies_to: 以合并上游分支方式更新的 PR head，不限语言`、
`recheck_when: 仓库改用 rebase 代替 merge，或 GitHub 的 PR diff 基准语义变化`。

<a id="exp-131"></a>

## 镜像里跑全量单测出现「成片 F」时，先归因再计入（2026-11-13 实测 #2244）

**现象**：9188 个用例跑到 68% 冒出 180 个 F/E，集中在 `tests/test_cli_*`、`tests/test_config_wizard*`、
`tests/test_agent_lifecycle_cli.py`。看上去像大规模回归，实际全部与环境有关，四类原因都命中：

1. **安装元数据陈旧（本例约 155 例，最大一类）**。错误形如
   `RuntimeError: Cannot load CLI command provider 'code': missing module 'powercontext.builtin.code.cli'`。
   它不取决于被审代码，而取决于共享 venv 里 `*.dist-info/entry_points.txt`：PR 把 `builtin/code/cli.py`
   迁到 `cli/code.py` 并同步改了 `pyproject.toml` 的 `[project.entry-points."powercontext.cli"]`，
   但共享 venv 仍是迁移前的 editable 安装 ⇒ `importlib.metadata.entry_points()` 返回旧目标。
   **判据**：把 `.venv/Lib/site-packages/powercontext-*.dist-info/entry_points.txt` 与 head 的 `pyproject.toml`
   逐行对比，不一致即环境问题；CI 安装的是 PR 自身，不会出现。
   **反模式**：不要为此在镜像里再塞一份同名 `dist-info`——同名发行版会让入口点重复注册，红法只是变了个样。
2. **平台常量**：`OSError: [WinError 1314]`（无符号链接权限）、`ModuleNotFoundError: fcntl`（POSIX 专用
   `code` 缓存）、`PermissionError` on startup lock probe。
3. **镜像无 `.git`**：`CalledProcessError: ['git','rev-parse','HEAD'] exit 128`，波及所有要推导版本
   （`hatch-vcs`）或 `PC_UPGRADE_SOURCE_VERSION` 的用例。
4. **需要外网/构建**：`uv run --from hatchling --with hatch-vcs` 失败（拉不到包）。

**做法**：先抽 1–2 例 `--tb=line` 看错误类型分类；对可疑单例，直接在**工作区 master 检出**跑同一条测试做
基线（本轮 `test_upgrade_gate_distinguishes_not_required_from_missing_acceptance` 两条在 master 上同样红
⇒ 预先存在的 Windows/bash 差异，与本 PR 无关）。报告里必须按「真实回归 / 基线既有 / 环境不可用」三分列，
既不能把成片 F 都算成 PR 责任，也不能因为量大就跳过归因。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2244 head 1b26eb3b`、
`applies_to: 在隔离镜像里跑全量单测的复审（Python 生态尤甚）`、
`recheck_when: 镜像改用 `pip install <mirror>` 的真实安装态，或共享 venv 被重建`。

<a id="exp-132"></a>

## 「新事件未登记到运维文档」要先证明那份文档是注册表（2026-11-13 实测 #2619）

**现象**：PR 新增 `artifact.operation.failed` 日志事件，只在 `docs/{en,zh}/development/processing-failures.md`
描述，没进 `docs/*/docs/operate/observability.md`。第一反应是「运维文档漏登记新事件」。

**核验**：`observability.md` 只做两件事——① 日志字段白名单表（`stage` / `processing_stage` /
`failure_reason` / `input_item_count` / `failure_location` / `cause_exception_type`…逐字段语义，`scope` 在
line 168 单列）；② 对少数有专属语义的事件（`atomic_memory.evidence.neutral`、`artifact_processing.worker.blocked`、
`artifact.read.completed`）单开段落解释字段。它**没有**事件名清单，开头就写明事件示例与字段扩展去看
`development/observability.md`，而后者只有「怎么新增一个事件」的方法论。因此「没登记到 observability.md」不成立。

**结论（定级前的三步）**：新事件用到的每个字段是否都在白名单表里；仓库里是否存在事件注册表（拿一个已知事件名
grep，看命中处是不是表格/清单）；同族事件（`artifact_processing.*`）当初是怎么登记的。三步任一不满足，
就该判为假阳性，不要发评论。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2619 head 0c079d6a`、
`applies_to: 观测性/文档一致性类 finding，不限仓库`、
`recheck_when: 仓库给 `docs/*/docs/operate/observability.md` 加了事件清单表`。

<a id="exp-133"></a>

## 复核他人 finding 时，先确认他引用的那一行就是 head 的行（2026-11-14 实测 #2635）

**现象**：`scripts/check_public_content.py:50` 的评论把字符类写成 `[A-Za-z0-9._:@//-/]`，而 PR 四个提交里
从来没有这一版（`918d40fc` 是 `[^\s/<>"'()\[\]{},;]+`，`7f8afa0a` 起是 `[A-Za-z0-9._:@-]+`）。
评论者对着一份过期渲染/记忆手打了代码，`diff_hunk` 里其实是另一份。**结论仍然成立**（`+`/`%`/`$`/`~`/`!`
都不在类里），但如果照着被引用的那一行去改，会改错地方。

**做法**：复核时同时取三样——评论的 `original_commit_id` 与 `commit_id`、`diff_hunk` 末行、以及
`git show <head>:<path>` 的同一行；三者不一致时，先在自己的回复里点明「head 实际是哪一行」，再论证缺陷是否仍然成立。

**顺带**：这类「守卫自身漏检」的 finding，用**同一语料同时跑 head 与候选修复**最有力（本例 18 例：
head 误判 6、候选 0，且 PR 自带 7 个测试不改仍全绿）。同时列出「候选修复仍未覆盖」的形式（本例无 scheme 的
裸域名与 protocol-relative），并说明为什么不能顺手补（裸域名匹配会把 `someone@antfin.com` 判红）。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2635 head c18f3476 / 线程 4570421228`、
`applies_to: 复核他人（含并行身份）已有 finding，尤其是引用代码行的行内评论`、
`recheck_when: 无（流程性结论）`。

<a id="exp-134"></a>

## 契约删除类改动：验收顺序是「计数归零 → generated 产物 → e2e 分类清单 → 已提交 bundle」（2026-11-13 实测 #2616）

**现象**：PR 从 `openapi/powercontext.yaml` 删掉 7 个 `/v1/admin/artifact-plugins*` 操作，同时重生成
`integrations/*/src/operations.generated.ts`。`contractSha256` 在 `compatibility.json` 里有匹配记录，
看起来「契约一侧已经完整」。实际 CI 红了 13 个 job。

**核验（按这个顺序走，每步都能独立判红）**：
1. `git show <ref>:openapi/powercontext.yaml | grep -c '<被删路径>'` 必须为 0——先确认删除真的落地；
2. 每个 `*.generated.ts` / `*.generated.py` 也 `grep -c` 同一个路径，必须为 0；
3. e2e 侧的**分类清单**：`e2e/bub/tests/test_access_audit.py` 的 `_SERVER_WIDE_WITHOUT_CONTENT`
   是手写 operationId 列表，不会随代码生成更新。断言点在 `server_wide == SERVER_WIDE_CONTENT_OPERATIONS
   | _SERVER_WIDE_WITHOUT_CONTENT`，所以漏删的 id 会表现为「集合不等」而不是「缺某个操作」；
4. **已提交的 bundle**：`lib/index.js` / `dist/*.js` 是打包产物，`grep -n 'artifact-plugins'` 有命中即
   说明 bundle 与自己的 `src/` 不同步。这类失败报在 `*-package` job 的 diff 输出里，形如
   `-		path: "/v1/admin/..."`，容易被误读成「生成器坏了」。

**结论**：判「契约已同步」不能只看 OpenAPI 与 `contractSha256`。手写分类清单（第 3 步）和提交的
bundle（第 4 步）是两条独立失配面，且分别对应不同的 CI job，缺一步就会把红 CI 说成绿。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2616 head c408880f`、
`applies_to: 任何「删/改 API 操作 + 代码生成」的仓库`、
`recheck_when: 仓库把手写 operationId 清单改成从 OpenAPI 派生`。

<a id="exp-135"></a>

## 「设置项未登记到配置文档」先统计同族登记率（2026-11-13 实测 #2449）

**现象**：PR 新增 runtime 配置 `atomic_memory_related_page_size`（默认 250，1..1000 校验），
`docs/*/docs/workflows/atomic-memory.md` 与 `docs/*/docs/operate/configuration.md` 都没提它。
第一反应是「新增配置项漏登记文档」。

**核验**：`configuration.md` 里 `POWERCONTEXT_SERVER_RUNTIME_` 前缀只有 72 行，而 `runtime/config.py`
的字段有 80 多个；同族的 `atomic_memory_related_mode`、`atomic_memory_related_max_distance`、
`atomic_memory_comparison_batch_size` 同样一个都没登记。也就是说这份表登记的是「运维会调的那部分」，
不是全部字段的注册表。

**结论**：这类 finding 在发之前必须算同族登记率——同族项普遍未登记 ⇒ 是惯例而不是遗漏，判假阳性。
只有当同族其它项都在表里、唯独新增项不在时，才构成真正的文档缺口。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2449 head 5ac36aec`、
`applies_to: 配置项/文档一致性类 finding`、
`recheck_when: 仓库引入「配置字段 → 文档表」的生成或校验脚本`。

<a id="exp-136"></a>

## 「减法型」修复必须做变异反证，光跑绿用例不足以判有效（2026-11-14 实测 #2632）

**现象**：PR 的作用是删掉一个全局 `remaining` 上限（原来是 `MAX_TOPIC_MEMORY_STAGE_ITEMS - len(bound_candidates)`
这类「总配额减去已用」的算术），改为逐组件独立排名后再截断。改完新老用例全绿，很容易直接给 LGTM。

**核验**：在隔离镜像里把切片改回 `)[: 0]`（等价于旧行为的极端形式），重跑新增用例
`test_full_initial_history_does_not_block_a_distinct_second_pass_match`，如期报
`Extra items in the left set: 'created'`；再把 `min(required, floor.lexical_min_matched_terms)`
改回 `required`（#2628 的双侧阈值），3 例新用例同时失败。反向证明新用例真的锁住了修复点。

**结论**：删除配额、放宽阈值、把 `min(...)`/`intersection` 降级成单侧——这类「减法」修复的用例
在**没修**的代码上也常常是绿的（因为触发条件窄）。必须做一次变异反证：把修复点回退成旧行为，
确认新增用例转红。变异后仍绿的用例只能算「覆盖了路径」，不能算「锁住了缺陷」。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2632 head 1bd97f6c`、
`applies_to: 删除配额/上限、放宽阈值、双侧判定降级为单侧 的修复类 PR`、
`recheck_when: 仓库引入基于属性测试或差分测试的自动变异检查`。

<a id="exp-137"></a>

## 生成器 `--check` 在无 `.git` 的隔离镜像里会假失败（2026-11-14 实测 #2647 / #2645）

**现象**：`scripts/generate_integration_lifecycle.py --check` 在 `git archive` 出来的镜像里 exit 128，
报 `git ls-files` 失败，看起来像「生成副本与源不同步」。同理 TS 侧 `flush-progress.ts` 的
`Generated from ...` 头注释比对、`tests/pydantic_ai_adapter/test_packaging.py` 的 `uv build`
也会因 hatch-vcs 取不到版本而 ERROR。

**核验**：在 probes 目录 `git init && git add -A && git commit -m mirror` 后 `--check` exit 0；
`test_recall_query_bound.py` 41 passed 也证实生成内容本身一致。这类 exit 128 / build ERROR 全部是
环境性失败，必须在证据里标注为镜像缺陷，不能计入 Finding。

**结论**：凡判「代码生成不同步」，先确认运行目录是 git 仓库（`git ls-files` 可用），
再对比**文件内容逐字节**而不是只信退出码。生成副本的差异要精确到「仅多 N 行头注释」这种粒度。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2647 head fe8677a2 / #2645 head d411ab48`、
`applies_to: 代码生成器 --check、hatch-vcs 版本推导、git archive 镜像`、
`recheck_when: 生成器改为不依赖 git 索引（例如读显式清单）`。

<a id="exp-140"></a>

## 无法 checkout 时用「本地 base blob 复用 + 按需取 blob」核对 `managed_digest`（2026-11-14 实测 #2621）

**现象**：`release/upgrade-support.json` 的 `persistence_sha256` 是 `scripts/upgrade_release_gate.py::managed_digest(root)`
的结果（对 `MANAGED_INPUTS` 下全部 `.py/.sql/.json` 的 `{相对路径: sha256(bytes 归一化 CRLF)}` 再取 sha256）。
本机 git 传输不可用时无法 checkout 整个 head，全量走 API 取 244 个 blob 太慢。

**做法（可直接复用）**：
1. 先取 **head 版本**的门禁脚本读 `MANAGED_INPUTS`。用本地 master 版本会得到错误的文件集：本轮 master 仍写
   `src/powercontext/server/authz`，head 已改为 `src/powercontext/builtin/authz`，按旧集算出的 digest 是
   `5cadda41…`，与声明值不符；换成 head 的文件集后精确命中 `e5f3f2db…`。
2. 拉 `git/trees/<head>?recursive=1`，按 `MANAGED_INPUTS` 前缀 + 扩展名过滤出目标集。
3. 对每个路径取本地已有 base 提交的 blob sha（`git rev-parse <base>:<path>`）与目标 sha 比对：**相等即字节相同**，
   直接用 `git cat-file blob` 的字节算 sha256（`
`→`
` 归一化照做）；只有不等/缺失的路径走
   `gh api git/blobs/<sha>`。本轮 244 个文件里 225 个可复用、仅 19 次 API 调用。
4. 结论要写出「复用 N / 下载 M」与命中值，否则无法判断是校验通过还是没有覆盖。

**判据**：digest 命中说明声明与文件集一致（门禁不会因 persistence 变更而红）；**不**说明 schema 兼容性成立。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2621 head 673851d6`、
`applies_to: 需要核对 `managed_digest` 类「全目录内容指纹」且无法完整 checkout 的审查`、
`recheck_when: 门禁脚本改为不含目录遍历的哈希算法、或 MANAGED_INPUTS 结构变化`。

<a id="exp-141"></a>

## 本机 `git fetch` 可能整体不可用而 `gh api` 正常（2026-11-14 实测）

**现象**：`~/.gitconfig` 的 `http.proxy/https.proxy = http://127.0.0.1:7891` 指向已停止的本地代理，
`git fetch` 报 `Failed to connect to github.com:443 over proxy`；`git -c http.proxy= -c https.proxy= fetch`
仍 `curl 28` 超时。同一时刻 `gh api`（Go 实现、不读 git config）完全正常。

**处理**：不要反复重试 `git fetch`，也不要把「git 不可用」写成仓库或 PR 问题。改走纯 API 取证：
`pulls/<N>/files`（分页）、`compare/<old>...<new>` 取增量 diff（`Accept: application/vnd.github.v3.diff`）、
`git/trees/<sha>?recursive=1` + `git/blobs/<sha>` 取单文件。需要完整树时 `gh api repos/.../tarball/<sha>`
在本仓可达 140 MB 且可能十几分钟，先看镜像里有没有前一轮留下的 `.tar` 再决定是否重下。
**归档副本没有 `.git`**，依赖 `git rev-parse`/hatch-vcs 的用例仍属环境性失败，需在报告中单列。

**2026-11-15 更正**：本条「绕过代理仍超时」只对当日的代理存活状态成立。当日实测
`git -c http.proxy= -c https.proxy= ls-remote https://github.com/oceanbase/powercontext.git` **即时返回**，
`refs/pull/<N>/head` 的 fetch 也可用 ⇒ 先试一次把 `http.proxy`/`https.proxy` 显式置空，失败再退回纯 API。
`--filter=blob:none` 的裸克隆要额外 `git config http.proxy ""`（写进仓库 config）：`git archive` 会为缺 blob
触发**惰性 fetch**，`-c` 只在当前进程生效，惰性 fetch 仍读仓库 config ⇒ 报同一句
`failed to connect ... over proxy` 并给出 0 字节 tar。archive 的 `-o` 用绝对路径：
`git -C <bare>` 会把相对 `-o` 解析到该裸仓库目录下。

**2026-11-21 追加（promisor 惰性 fetch 不是可用路径）**：`clone --bare --filter=blob:none` 之后，
`git archive <sha> <subdir>` / `git cat-file -p <sha>:<path>` 会对每个缺 blob 单独发起一次带过滤的
fetch-pack。实测取一个 `migrations/` 子树（约 60 个文件）跑满 10 分钟后以
`fatal: fetch-pack: invalid index-pack output` 结束、产物 0 字节；同一时刻 `gh api .../tarball/<sha>`
单流 ~85 MB 约 10 分钟可完成，**两路并行**（`gh api ... > a.tgz & gh api ... > b.tgz & wait`）把 4 个 head
压到约 20 分钟。判据：`tarfile.open(name,'r:gz').getnames()` 能完整列出成员才算下载完成；解压用
`extractall(dest, filter='data')`，顶层目录名形如 `oceanbase-powercontext-<短sha>`。
`git merge-tree` / `git ls-tree` / `git cat-file` 对**已有** blob 仍正常，只有触发惰性 fetch 的路径不可用。

**关键词**：`validated_at: 2026-11-21`、`validated_ref: oceanbase/powercontext #2583/#2664/#2674 的 head 归档`、
`applies_to: 本机 Windows + 本地代理形态的审查环境`、
`recheck_when: 代理恢复正常、换用不含 promisor 的完整克隆、或改走 WSL 取证`。

<a id="exp-142"></a>

## 测试注释里「另一种实现会怎样」的断言必须实测（2026-11-14 实测 #2632）

**现象**：#2632 的增量提交只改测试，注释声明「首见分数排序会丢 `history-0021`、按候选 id 排序也会丢
`history-0021`」。做法是把实现变异为 `related_scores.setdefault(candidate_id, score)`（首见分数）后复跑：
用例确实失败（可证伪成立），但**被丢的是 `history-0020`，不是注释写的 0021**。

**收益**：一次变异同时给出两个结论——① 新增断言确实能检出原缺陷（不是恒真断言）；
② 注释对备选实现的预测已失真，后续读者会把「0021」当成事实。写结论时把两者分开写：
缺陷证明成立，注释不精确（不影响行为，只在报告里点出，不单独发评论）。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2632 head 51de6912`、
`applies_to: 「只改测试」的增量提交（声称让旧断言可证伪）`、
`recheck_when: 该用例数据或排序实现再改`。

<a id="exp-146"></a>

## `url` crate 的 `host_str()` 对 IPv6 带方括号：用它 `parse::<IpAddr>()` 判环回会漏掉 `[::1]`（2026-11-15 实测 #2630）

`url::Url::host_str()` 返回的是序列化后的 host，IPv6 带 `[` `]`；本地 cargo registry 的
`url-2.5.8/tests/unit.rs` 有断言 `assert_eq!(url.host_str(), Some("[::1]"))`（`~/.cargo/registry/src/*/url-*`）。
因此 `host_str().and_then(|h| h.parse::<IpAddr>().ok()).is_some_and(|ip| ip.is_loopback())` 对 IPv6 恒为 false，
`localhost` 同样为 false（主机名不是 `IpAddr`）。后果：把「本机 Core」判成「远端明文 HTTP」而整条发送路径暂停。

核验法（无 Rust 工具链也可）：在本地 cargo 缓存里 grep 该 crate 的 tests 断言，再对照 PR 里 `host_str()` 的用法。
正确写法是 `match url.host() { Some(Host::Ipv4(a)) => a.is_loopback(), Some(Host::Ipv6(a)) => a.is_loopback(), _ => false }`。
凡「环回/私网地址判定」类改动，回归至少要覆盖 `127.0.0.1`、`[::1]` 与一个非环回地址三种取值。

**关键词**：`validated_at: 2026-11-15`、`validated_ref: oceanbase/powercontext #2630 head bd057c3f（gateway/crates/pc-gateway-core/src/http_gate_client.rs:136）`、
`toolchain: url 2.5.x`、`applies_to: Rust 侧用 host_str 做地址分类的代码`、
`recheck_when: url crate 改为返回无括号 host，或判定改用 Url::host()`。

<a id="exp-147"></a>

## 提交进仓库的 pinned 报告若对工作树字节取摘要，在 CRLF 检出上必然与 blob 不符（2026-11-15 实测 #2630）

`evaluation/memory/prepared_context_budget/report.py::run_manifest()` 用
`hashlib.sha256((repo_root / source).read_bytes())` 直接算工作树字节。`core.autocrlf=true` 的检出上工作树是 CRLF、
blob 是 LF，于是同一份源码在报告里记录的摘要与 `git hash-object`／`git cat-file` 永远不同；换到 LF 检出（CI/macOS）
重跑同一命令又会得到第三组值。本轮 #2630 的 7 项 `source_sha256` 全部等于 `sha256(blob 转 CRLF)`（7/7），
没有一项等于 `sha256(blob)`（0/7）；同一文件在上一版报告（macOS 生成）里记的正是 LF 摘要，可作对照。

**取证顺序**：拿到「记录摘要 ≠ blob 摘要」时，先试 `sha256(blob.replace(b"\n", b"\r\n"))`，能命中就说明是行尾而非代码不同，
不要直接判「报告与提交不符／数字来自别的代码」。同时看同目录 `run-manifest.json` 的 `git_worktree_dirty`：
若为 true，先确认该标志是否自指——当 `--output` 指向仓库内（如 `evaluation/.../reports/x`）时，
上一次运行留下的未提交报告就在 `git status` 的观察路径里，标志会恒为 true、失去判别力。
报告还要能对上提交时，正确做法是按 blob 语义取摘要（`git cat-file`，或先归一化 CRLF→LF 再哈希），并在干净工作树上重生成。

**关键词**：`validated_at: 2026-11-15`、`validated_ref: oceanbase/powercontext #2630 head dc85dd61`、
`applies_to: 任何把 source_sha256/inputs 摘要写进仓库的 pinned 报告与评测产物`、
`recheck_when: report.py::run_manifest 的摘要实现变化，或仓库改用 core.autocrlf=false`。

<a id="exp-151"></a>

## 「记录到日志/追踪里的脱敏」必须发生在截断之前，否则前缀被切走就不再有可识别的凭据形态

现象（2026-11-17 实测 `oceanbase/powercontext` #2647 head `3dabdb17`）：`hermes` 的 `provider.py:879` 记
`query=_redact_secrets(recall_query)`，而本 PR 把 `recall_query` 从「头部截断 `query[:8192]`」改成「保留尾部
`bounded_recall_query`」。切点落在 `api_key=` 与值之间时，赋值前缀被丢掉，`SECRET_PATTERNS` 的赋值规则不再命中，
于是 base 会脱敏、head 把凭据原样写进 trace。

- 复现构造：让值下标恰好等于 `len(prompt) - 8192`（本例 `prompt=(f"api_key=synthetic-value-2084 " + "filler "*3000)[:8200]`，
  值下标 8）。
- 判据：凡是「先变形（截断/切片/摘要/重排）再脱敏」的路径，都要问「变形是否可能切掉凭据的判定前缀」。
  泛化一下：`bearer <token>`、`sk-…`、`ghp_…` 这类**自带形态**的 token 变形后仍能被识别，
  只有**依赖上下文**（`key=value`、`Header: value`）的凭据会漏 ⇒ 定级按这个子集算，不要因为「还认得 sk-」就判无风险。
- 修复序固定为「先脱敏完整的原文，再变形」：脱敏只会缩短文本，缩短后再套长度/字节上界必然仍满足；
  若坚持让日志与发送内容逐字一致，就必须把被切掉的前缀补回来再判定，代价更高，通常不该选。
- 验证方式：直接导入镜像里的两个纯函数（`bounded_recall_query` + `redact_secrets`）对拍 base 与 head 两种顺序，
  不需要跑宿主运行时。

`validated_at: 2026-11-17`、`validated_ref: oceanbase/powercontext #2647 head 3dabdb17（base 195be9b7）`、
`applies_to: 任何把用户输入写入日志/追踪/审计并同时施加长度上界的路径`、
`recheck_when: 脱敏规则从「上下文形态」改为「按字段白名单」，或 trace 改为记录原始 post 载荷`。

<a id="exp-153"></a>

## 「集合成员已同步」不能靠「对该集合做了参数化」来证明：用例总带同一个可选键时会掩盖缺项

- 现象（2026-11-23 #2725）：新公开操作的 scope-mode 契约标为 `current`，但下游宿主插件里维护的
  `_CURRENT_OPERATIONS` 手写集合没有登记它；CI 全绿。原因是针对该集合的参数化用例给每个成员都塞了
  `{"scope_id": "agent-selected"}`，而缺项的成员走的正是「已给 scope ⇒ 覆盖为绑定值」这条分支，断言照样成立。
- 判据：看到「用例参数化遍历一个业务集合」时，先问「集合缺项会不会仍然通过」。只有当用例存在**省略该可选键**
  （这里是省略 `scope_id`）的变体，参数化才等于覆盖；否则它只覆盖了「键已存在」的一半语义。
- 处理：把这类契约拆成两条断言——集合相等（`frozenset(生成物) == 手写集合`）与行为分支（省略键时仍注入）。
  前者成本极低，能直接拦住漂移；后者保证语义。
- 同源检查：新操作要在**所有按 scope-mode / 分组维护的手写集合**上扫一遍（插件钩子、宿主适配器、生成物），
  不要只看 openapi 与生成物是否 `--check` 通过——生成物是机器同步的，手写集合不会。

`validated_at: 2026-11-23`、`validated_ref: #2725 head f2b960a2（Codex 插件 bind_tools.py blob 7c82e0ea）`、
`applies_to: 有「生成物 + 手写分组集合」双份契约的仓库`、
`recheck_when: 该仓库改为从生成物派生分组集合`。

<a id="exp-159"></a>

## 「merge-only」复审：只合 upstream 也要审，判据与手法（2026-11-25 实测 #2815 / #2810 / #2771）

- **先判是不是 merge-only**：`git log --no-merges <prev>..<head> ^master` 为空、且 `git log -1 --format=%p <head>`
  有第二个父提交 ⇒ 作者只合了 master。此时 PR 独占提交集未变，但**冲突解析仍是作者工作**，不能直接放过。
- **三版符号比对区分「迁移」与「丢失」**：对每个改动的 `.rs` 取 `master:<f>` / `<prev>:<f>` / `<head>:<f>`，
  用 `^\s*(pub(\(crate\))?\s+)?(async\s+)?fn\s+(\w+)` 抽函数名做集合差。本轮两例都是假警报：
  #2771 的 `is_text_part`/`last_user_index` 被移入新模块 `turn_message.rs`；#2815 的
  `default_steering_and_overrides_reach_only_responses` 改名为 `..._reach_both_routes`（行为变更）。
  判「丢失」前必须先在 head 里按语义搜一遍重命名候选，否则会把正常重构写成删代码。
- **最强低成本证据是 merge 结果上的 CI**：`gateway-validation / check` = `cargo fmt --check` + `clippy --all-targets
  -D warnings` + `cargo test --locked --workspace`，pull_request 事件跑的是 merge ref ⇒ 绿即「合并组合可编译 + workspace 用例通过」。
  另可只用 `cargo test -p pc-gateway-protocol` 在本机跑协议层（exact head 镜像 + 共享 `CARGO_TARGET_DIR` 十几秒完成）。
- **跨 PR 的「致命环境变量」检查**：某 PR 把旧变量改成启动即退出时，用
  `git diff master <other_head> | grep '^+'` 扫其它在飞 PR 的新增行，能提前捞出合并顺序冲突。
