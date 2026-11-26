<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 平台、工具与环境

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-019"></a>

## PowerShell 到 WSL 的多行脚本传输

- PowerShell 调用 WSL 执行包含 Bash 变量、引号、函数和多条命令的脚本时，不要把完整脚本直接嵌入 `bash -lc` 参数。应把 UTF-8 脚本 Base64 编码或写入审核目录内的临时文件，在 WSL 中解码后交给 `/bin/bash`；正式验证前先用无副作用 probe 同时核对变量值和预期非零退出码，避免宿主 shell 提前展开或吞掉 `$?`、`$var` 后制造假通过。
- **Git Bash（Windows 侧 bash）→ `wsl.exe -d <distro> -- bash -lc '<cmd>'` 也有同类陷阱，且表现更隐蔽（2026-11-03 实测）**：命令串里的 `$VAR`、`$PWD` 会取到 Windows 侧环境或空值，而不是 WSL 内的赋值。实测三种后果：`cd X && echo $PWD` 打印的是宿主工作区而非 `X`；`export PYTHONPATH=$PWD/src` 变成空值，于是被测代码从**开发者工作区**的 editable 路径导入（`sys.path` 里出现 `../../../../<repo>/src`），报错却像"被测 head 缺依赖"；`$PY -c ...` 直接把 `$PY` 吃成空串，只报 `bash: -c: command not found`。判据：一旦 WSL 侧报缺失模块，先打印 `pwd` 与 `sys.path[0:3]`，确认导入源是镜像而不是宿主目录。规避方式统一为"绝对路径字面量 + 独立 `.sh` 脚本"：脚本内用 `/mnt/d/...` 全路径，宿主侧只传 `wsl.exe ... bash /mnt/d/.../probe.sh`，不在 `-lc` 字符串里放任何变量或复合命令。
- 同一类会话里，宿主 `PYTHONPATH` 会**穿透进 WSL**（值为 Windows 侧的可编辑安装路径）。WSL 内显式 `PYTHONPATH=<镜像>/src` 必须在子进程里真正生效，否则镜像测试会静默跑成宿主工作区代码；判断方法同上一条的 `sys.path` 打印。

<a id="exp-023"></a>

## WSL Cargo 继承宿主 target-dir

- Cargo 会从工作目录向上查找 `.cargo/config.toml`。Windows 独立镜像若位于含 `target-dir = "D:/..."` 的上级目录，WSL Cargo 会把该值当作相对路径，形成 `/mnt/d/.../D:/...`，并可能因 `LD_LIBRARY_PATH` 路径段含冒号而在编译前失败。WSL Rust 门禁启动前应先用 `cargo metadata --no-deps --format-version 1` 核对 `target_directory`；发现 Windows 风格或错误拼接时，为本轮命令显式设置 WSL 可解析的 `CARGO_TARGET_DIR`，并把原失败归类为环境问题，不得修改仓库配置或误报为 PR 回归。

<a id="exp-024"></a>

## 仓库级 Agent Skills 的跨工具路径与校验

- 仓库内希望被多个 Agent Skills 实现发现的技能，应先核对目标工具的官方发现路径；同时支持时优先使用 `.agents/skills/<name>/SKILL.md`。`SKILL.md` 的 `name` 必须与父目录名一致，顶层 frontmatter 只能使用规范允许的字段；工具专属 UI 字段不得伪装成通用顶层字段。审查时用实际 validator 验证，不只检查 Markdown 可读性。
- Windows 上校验含中文的 `SKILL.md` 时，validator 若使用默认 `Path.read_text()`，可能先因 GBK 解码失败而掩盖真正的结构错误。应设置 `$env:PYTHONUTF8='1'` 后重跑，并在 WSL/Linux 再执行一次；编码失败归类为环境问题，只有 UTF-8 读取成功后的目录名、frontmatter 或引用错误才能归责于 PR。

<a id="exp-040"></a>

## 无 git 传输时复算三方合并：`base.sha` 不是 merge-base，`merge_commit_sha` 会陈旧

- `validated_at: 2026-11-02`、`validated_ref: oceanbase/powercontext #2343(head 3bbc8844, base.sha 0a98473a, 真实 merge-base bdf99789)、#2322(merge_commit_sha d6fcd6a5 的父是 4438ef86，当前 master 1c52626d)、master 1c52626d`、`applies_to: git over HTTPS 不可用、只能用 REST 取 blob 复算合并结果的场景`。
- 两个字段都**不能**当合并基准：`pulls/<n>` 的 `base.sha` 是 PR 快照里记录的 base，不等于 `merge-base(head, master)`（#2343 两者差 90 个提交）；`merge_commit_sha` 是懒计算产物，其父提交常落后当前 base tip（#2322 落后 10 个提交，而 `base.sha` 又落后 37 个）。用它们做三方合并会造出**假冲突**（本例 `desktop/README.md`、`README.zh.md` 用 `base.sha` 合并 exit 1，换成真实 merge-base 后 exit 0）。
- 处理：`gh api repos/{o}/{r}/compare/<head>...<master>` 的 `merge_base_commit.sha` 才是基准；再用 `gh api .../contents/<path>?ref=<sha>` 取三份 blob，落成三个文件后 `git merge-file -p ours base theirs`（**不要**加 `--name`，该参数需要 `-L`，会返回 exit 129）。合并结果与"应当重建出的产物"是否一致，用**键序**比对判定：把生成源里的条目名按出现顺序取出，与合并后 bundle 的条目名序列逐项相等即通过（本例 #2322 两个 `lib/*` 均为 149/149 且键序与 master 的 `src/operations.generated.ts` 全等）。
- 边界：`git merge-file` 只证明文本可合并与条目集合一致，不能替代真实重建（生成器的字节级格式、排序、模板改动都不在其中），收尾必须写明"未实跑重建门禁"。

<a id="exp-056"></a>

## 同名用例在不同环境失败在不同断言行，"同名失败"不等于"同一抖动"

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #1561`（head `9676264b`；CI `tests (3.14, e2e)` 红在 `test_zcode_service_chain.py:237`）、`applies_to: 用本地复跑判断 CI 失败是否 flaky 的所有场景`、`recheck_when: 方法类，长期有效`。
- 现象：本地跑同一用例连续 3 次失败于 `:147 Cannot find module …/integrations/zcode/…/scripts/scope.mjs`——原因是镜像只导出了 `src tests`，缺 `integrations/`；CI 的失败则是 `:237 'unknown' == 'cursor_reached'`。若不看行号，会把"镜像缺文件"当成"复现了 CI 失败"，进而错误升级为 PR 缺陷（或反向把它当抖动而漏掉环境缺口）。
- 处理：① 先统一失败签名（文件:行 + 断言文本），不一致就补齐镜像（`git archive <ref> integrations/<host>`）后重跑；② 补齐后本地 3/3 通过，才可把"CI 单版本红"归为时序/环境；③ 收尾必须写清"该红未被消除、合并前需重跑"，不能用本地通过替代 CI 结论。

<a id="exp-058"></a>

## 变异测试用来定位"哪条路径没有回归保护"，而不是用来证明"有保护"

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2096`（head `1072176e`，`tests/builtin/test_code_publication.py`）、`applies_to: 新守卫/新不变量只加了一处、而调用路径有多条时，判断测试覆盖的是哪一条`、`recheck_when: 方法类，长期有效`。
- 手法：把守卫删掉（保持其它逻辑不变）跑目标测试文件。`1 failed, 8 passed` 说明该守卫**这条路径**有回归保护；若全绿则说明新增用例只覆盖了别的入口。把变异结果写进评论，比"我担心另一条路径没覆盖"有力得多。
- 变异副本要独立：复制 `src` 到 `probes/mutant-src`，用 `PYTHONPATH=<mutant> <venv>/python -m pytest <head 测试>`，别改真实镜像树；改完立刻验证目标行唯一命中（`assert t.count(old) == 1`），否则静默改错位置。
- 定位 Finding 的落点也靠它：变异证明「A 路径有测试、B 路径没有」之后，评论直接指向 B 路径的具体行，不用泛泛说"建议补测试"。

<a id="exp-062"></a>

## 超长 parametrize 实参会在 Windows 上经 `PYTEST_CURRENT_TEST` 溢出，用例根本没执行

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #2033`（head `2166edc7`，`tests/test_dashboard.py` 的 33 KiB 参数）、`applies_to: 用 `parametrize` 传大字符串（>32 KiB 的查询串、正文、JSON）的测试`、`recheck_when: pytest 改为截断 `PYTEST_CURRENT_TEST`，或仓库 CI 增加 Windows 测试 job`。
- 现象：`pytest tests/test_dashboard.py -q` 在 Windows 上 `53 passed, 2 errors`，两个 error 都是同一条参数，栈落在 `_pytest/runner.py::_update_current_test_var → os.environ["PYTEST_CURRENT_TEST"] = ...`，报 `ValueError: the environment variable is longer than 32767 characters`；pytest 的 node id 把整个实参拼进去，Windows 单环境变量上限 32767 字符 ⇒ **setup 与 teardown 各失败一次，断言完全没有执行**。
- 判据：`ERROR`（不是 `FAILED`）、栈里没有被测代码、`key='PYTEST_CURRENT_TEST'` ⇒ 属参数化方式问题，不是产品缺陷；Linux 上同一用例正常，所以 ubuntu-only 的 CI 不会暴露。这类红不要报成"测试失败"，要报成"该边界在 Windows 无执行证据 + 本地整文件红"。
- 处理建议：长串在用例体内构造（`parametrize` 只传长度或 `padding`），或给该参数 `ids=` 一个短 id。同源风险还有 `tmp_path` 目录名过长、`caplog` 里塞大对象。
- 归因边界：先确认 Windows 侧确实有 job 覆盖该文件；本仓 `windows-unit-portability` 只跑一个文件，因此这条只能靠本地复现证明。

<a id="exp-067"></a>

## Windows 的 `.cmd` shim：CreateProcess 不做 PATHEXT 搜索，而 shim 的 stderr 来自 cmd.exe 的 OEM 代码页

- `validated_at: 2026-10-22`、`validated_ref: oceanbase/powercontext PR #2197`（head `6934d30c`，`src/powercontext/cli/system.py::_run_codex_json` / `_run_codex_mcp_list`）、`applies_to: CLI 以裸名调用 Node/npm 安装的宿主工具（codex、claude、pnpm、npx…）并解析其输出`、`recheck_when: 方法类，长期有效`。
- 事实一：`subprocess.run(["codex", ...])` 在 Windows 上直接 `FileNotFoundError [WinError 2]`——`CreateProcess` 不按 `PATHEXT` 展开 `.CMD`；必须先 `shutil.which("codex")` 拿到完整路径（会返回 `…\codex.CMD`）再传入。`shutil.which` 在 Windows 上还会把当前目录插到搜索路径最前，评估可执行文件劫持风险时要把这一点算进去。
- 事实二：`.cmd` 由 cmd.exe 解释执行，`stderr` 里会混入 cmd.exe 自己的消息（`'<name>' 不是内部或外部命令…`、AutoRun 失败等），编码是 ANSI/OEM 代码页（中文 Windows 为 cp936）。若父进程用 `text=True` 且处于 UTF-8 模式（`PYTHONUTF8=1`，或未来 Python 默认开启），reader 线程会 `UnicodeDecodeError`，`completed.stderr`/`stdout` 变成 `None`，随后 `.strip()` 抛 `AttributeError`，本该是 `SetupError` 的失败分支退化成 traceback。
- 核对手法：同一文件里比对同类读取点是否都写了 `encoding="utf-8", errors="replace"`；只有个别漏写即为缺口。复现脚本用一个 rc≠0 且 stderr 带本地化消息的 shim 即可（探针 `probes/probe_fail_path.py`），无需真实安装宿主工具。
- 定级口径：shim 成功路径的解析修复是 P1 级需求；"失败分支抛 AttributeError 而非可读错误"属错误路径健壮性 ⇒ P2，并明确写出触发条件（UTF-8 模式 + 非 UTF-8 stderr），不要写成"Windows 上必然失败"。
- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2197`（head `7b9ff4cb`，评论 4350992691）、`applies_to: 用"夹具把 PATH 收窄到只含 shim 目录"的方式断言 shim stderr 内容的 Windows 用例`、`recheck_when: 夹具改为保留 System32、或断言改成语义包含`。
  **cmd `AutoRun` 会污染 shim 的 stderr**：`PATH` 只剩夹具目录时，cmd.exe 执行 `HKCU\Software\Microsoft\Command Processor\AutoRun`（本机为 conda `conda_hook.bat`）找不到 `doskey`，于是先把 `'DOSKEY' 不是内部或外部命令…` 写进 stderr，shim 自己的输出退成第二行。断言写成 `"failed: <shim stderr>" in stdout` 这类**相邻子串**时，本机必红（实测 `2 failed, 4 passed`），而 GitHub 托管 runner 无 AutoRun ⇒ CI 全绿（同 head `6 passed`）。
  判据：本地红而 CI 绿时，先 `reg query "HKCU\Software\Microsoft\Command Processor" /v AutoRun`，再用「同一 shim + 同一收窄 PATH」的探针单跑，比较首行来源。处理建议：断言改语义包含、按行取最后一行，或探针用 `cmd /d` 关闭 AutoRun。定级 P2，理由与"本地开发被破坏且 CI 不可见"同类。

<a id="exp-069"></a>

## 镜像根路径与证据边界（补充：`source/<sha8>` 分目录）

- `validated_at: 2026-10-23`、`applies_to: 同一 PR 多次 head 漂移的复核`。同一个 PR 目录下按 `source/<sha8>/` 分别解压各 head，避免覆盖上一轮证据；`probes/mutant-*` 与 `evidence/*.out` 每轮新建，变异脚本里断言 `text.count(old) == 1` 后再写回，防止静默改错位置。

<a id="exp-073"></a>

## 在 Windows 上审查仅 POSIX 的缓存/锁模块：用 WSL + 只桩跨包依赖装载单文件

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2096`（`src/powercontext/builtin/code/cache.py`，`file_lock` 依赖 `fcntl`）、
  `applies_to: 目标模块在本机平台不可导入（fcntl/resource/信号），但缺陷需要实跑才能定性的审查`、`recheck_when: 该模块改为跨平台锁或 WSL 不可用`。
- 手法：不要把整个包装进 WSL。用 `importlib.util.spec_from_file_location` 逐个装载**被测文件及其同包子模块**，只为跨包依赖建 `types.ModuleType` 桩
  （本例 `powercontext.errors`、`powercontext._logging`、`powercontext._code_validation`）并预先塞进 `sys.modules`，包对象给 `__path__` 指向源码目录。
  这样被测逻辑（锁、目录、rename、SQLite）是真实的，桩只落在它与外部包的交界处。
- 关键细节：`os`/`shutil`/`rename` 等真实副作用要保留；只有「另一个进程/另一套存储」的边界才桩。若把 `fcntl` 也桩成 no-op，
  `collect()` 一类「非阻塞取锁失败即保留目录」的路径会失效，缺陷随之消失 —— 这正是本例必须用真实 flock 的原因。
- 成本：一次 `wsl.exe -d Ubuntu -- bash -lc 'cd /mnt/d/...; python3 probe.py'` 即可，不需要 `uv sync`；输出重定向到证据目录时用 `/mnt/d/...` 绝对路径，
  相对路径 `../evidence` 在 `bash -lc` 下会落到家目录而报 `No such file or directory`。

<a id="exp-074"></a>

## 把 `shutil.which` 换成自建 PATH 枚举：`PATHEXT` 只属于 Windows

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2197`（head `5cfb9d75`，`src/powercontext/cli/system.py::_codex_path_executable` 的 `:712`）、
  `applies_to: 任何为规避「`shutil.which` 在 Windows 上隐式前置当前目录」而手写 PATH 扫描的跨平台代码`、
  `recheck_when: 该函数改回调用 `shutil.which`、或按 `os.name` 分支处理 `PATHEXT``。
- 现象：作者手写候选枚举以求「不搜当前目录」，用 `os.environ.get("PATHEXT", "").split(os.pathsep)` 取扩展名集合。Windows 上 `PATHEXT` 形如
  `.COM;.EXE;.BAT;.CMD`（分隔符 `;`），而 `os.pathsep` 在 POSIX 上是 `:` ⇒ Linux/macOS 把整串当成**一个**扩展名，候选退化为
  `codex.COM;.EXE;.BAT;.CMD`，无扩展名的 `codex` 从未进入候选列表，函数恒返回 `None`。
- 后果：`setup codex` / `doctor codex` 在 Linux/macOS 全部失败（报未找到），Windows 绿 ⇒ 平台专属缺陷。判据不是「读代码觉得可疑」，而是
  「同一目录下 `shutil.which("codex")` 有值、该函数返回 `None`」这一单点对照。
- 验证手法（比读源码快且可复现）：在 WSL 下用 `git show <sha>:src/powercontext/cli/system.py` 抽出目标函数与其依赖常量，
  只注入标准库后 `exec` 运行；本例得 `resolver=None` 而 `shutil.which` 返回 `/tmp/codexbin/codex`。注意 WSL 侧 `typer`/`rfc8785` 常缺失 ⇒
  不要 import 整包，抽函数即可；驱动脚本要写成独立 `.sh` 再 `MSYS_NO_PATHCONV=1 wsl.exe … bash -lc <脚本>`，避免宿主机 bash 先吃 `$(…)` 与括号。
- 连带检查：换实现后 `grep` 既有测试是否仍在 patch 旧符号（本例约 20 处 `system_cli.which`）。patch 失效而测试仍绿，属「用例通过 ≠ 被测路径被执行」，
  应写入 Finding 的附注而不是当作已覆盖。
- 正确写法：Windows 用 `PATHEXT`（按 `;` 切）**并显式尝试空扩展名**；POSIX 只尝试空扩展名。

<a id="exp-076"></a>

## 子包测试的 `PYTHONPATH` 顺序：editable 安装会把"被测包"悄悄换成工作区 master

- `validated_at: 2026-10-23`、`validated_ref: oceanbase/powercontext PR #2122`（`evaluation/memory/capture_ownership/tests/test_replay.py`）、
  `applies_to: 仓库内含独立子包（evaluation/、integrations/）且宿主包为 editable 安装的验证`、
  `recheck_when: 工作区 `.venv` 不再是 editable、或子包以 workspace member 方式被 `uv sync` 安装`。
- 现象：只把子包 `src` 放进 `PYTHONPATH` 跑子包测试，出现与 PR 无关的断言失败（本例 `assert "content" not in evidence["source_metadata"]`）。
  原因是被测的 `powercontext` 从 `.venv` 的 editable 安装解析到**工作区主检出**（master），不是 PR 的 Head。
- 判据（先证明来源再判缺陷）：跑一行
  `PYTHONPATH="<PR>/src:<PR>/evaluation/<pkg>/src" python -c "import powercontext,<pkg>; print(powercontext.__file__, <pkg>.__file__)"`，
  两个路径都必须落在镜像的 Head 目录内。本例修正顺序后同一文件 `4 passed`（错误顺序下 `1 failed, 3 passed`）。
- 结论：**失败在前、定位来源在后**是必做顺序；同一命令先后得出两个结论时，先怀疑 import 来源，不要先怀疑 PR。

<a id="exp-080"></a>

## socket 背压式用例在 Windows 上不可复现（`SO_SNDBUF` 只限发送端）

**现象**：为了验证「记录被丢弃时计数/指标+1」，用例把生产者写成子进程、把消费者线程用一次 `select` 阻塞住，再给发送端
`setsockopt(SOL_SOCKET, SO_SNDBUF, 4096)`，指望 200 KB 记录在 `sendall` 时超时并留下残余缓冲。Linux 全绿，
Windows 稳定失败（`assert 0 == 0 + 1`），而且 stderr 里没有服务端自己的失败标记。

**判据**：不要先怀疑产品代码。按三步定位：① 找产物——若日志文件里能读到那条完整记录（本轮 400,608 字节、含
`Large observation`），说明发送端根本没有失败；② 数失败标记——`observability.log_failed` 一条都没有，说明
`sendall` 没超时；③ 再看 `LogReceiver._buffers` 在关闭前是否为空，为空就证明 `_close_channel` 走的是「干净 EOF」分支，
不计数是设计内的。Windows 的接收窗口会自动扩张，少量数据可直接整条吸收；`SO_SNDBUF` 只约束发送端，因此靠它制造背压
在 Windows 上不成立（同一写法在 Linux 上成立，于是只在这一个平台红）。

**处理**：
1. 结论写成「用例不可移植」，而不是「计数器坏了」；等级看平台矩阵——若该用例所在的 job 是本 PR 自己新增的 Windows
   step，按本 PR 引入的红门禁处理（P1），并给出 head 的 job/step 名与失败签名。
2. 给确定性替代：向 `socketpair` 写入「一条完整记录 + 一条截断记录」后正常关闭，残余缓冲必然触发一次丢弃；队列满路径
   让 `deliver` 抛 `Full`。两类都不依赖内核缓冲，两个平台同结果。
3. 在评论里同时给出「实现侧可用」的正向证据，避免作者误以为要改实现——本轮
   `probe_partial_close.py` 得到 `delivered=['delivered-record']`、`drop_counts=[1]`。

**易误判的反面**：传输层若要求 JSON **字符串**行，用 `b'{"ok":1}
'` 试探会走
`TypeError("Worker log record must contain formatted text")`，残余缓冲会被整段计入丢弃（本轮先得到 `drop_counts=[2]`），
看起来像「多算了一条」，其实是用例自身的负载不合契约。先核传输格式，再判计数是否多算。

关键词：`validated_at: 2026-10-25`、`validated_ref: PR #2196 head 921894c0c37e5f41c33729b197eeaf624f5e3500`
（job `121156274990`）、`applies_to: 用 socketpair + 小 SO_SNDBUF 制造丢包的跨平台用件`、
`recheck_when: 用例改为确定性驱动，或被测传输层去掉「JSON 字符串行」契约`。

<a id="exp-089"></a>

## 测试把 Windows 原生路径写进 `.env` 文件时，dotenv 会吃掉反斜杠

`.env`/`python-dotenv` 解析未加引号的值时把 `\` 当转义符：`POWERCONTEXT_SERVER_DATABASE_URL=sqlite+aiosqlite:///C:\Users\a\x.db`
在 settings 里变成 `sqlite+aiosqlite:///C:Usersax.db`，随后报 `sqlite3.OperationalError: unable to open database file`。
所以「同一个 URL 在代码里构造后直接传给 settings」能跑通，**同一串写进 env 文件再读回**却会失败 —— 这不是产品缺陷，
是测试写法问题，但表现为「CLI 子命令打不开库」，很容易被误判成业务 bug。

实测 `oceanbase/powercontext` #2304 head `a4dc0b11`：`tests/e2e/test_access_ownership_migration.py` 用
`f"...DATABASE_URL={database.url}"` 写 env（`database.url` 由 `tmp_path / "x.db"` 生成），本机
`1 failed, 11 passed`，唯一失败即此；探针 `probes/probe_env_url_fix.py` 同场景对照：原生路径 `exit=1`，
`Path.as_posix()` 生成 `sqlite+aiosqlite:///C:/...` 时 `exit=0`。CI 的 e2e 只在 ubuntu 跑，所以不会变红。

判据与做法：
- 判这类失败先看「失败的读取路径是否经过 `.env`」：同一 URL 两种传递方式的 A/B 是决定性证据，比读产品代码快。
- 用 settings 层直接打印解析后的值（本例 `server_settings_context` + `settings.database.url`）确认是转义而非权限/路径问题。
- 测试里应统一 `Path.as_posix()`（或写前 `replace("\\", "/")`）；仓库里同时存在两种写法时，不要把既有的坏写法当先例复制。
- 反过来：**产品**文档给出 `.env` 示例时也不要用 Windows 原生路径，否则用户照抄必然失败。

关键词：`validated_at: 2026-10-30`、`validated_ref: #2304 head a4dc0b11、探针 probes/probe_env_url_fix.py`、
`toolchain: Windows + 工作区 .venv（Python 3.14）+ typer CliRunner`、
`applies_to: 用 .env/环境文件加载数据库 URL 或路径的仓库`、
`recheck_when: dotenv 实现或 env 解析库变更、CI 增加 Windows e2e job`。

<a id="exp-100"></a>

## 新增「密钥/凭据文件安全校验」模块时，先查平台 API 存在性：`os.O_NOFOLLOW` / `os.getuid` 在 Windows 直接抛 `AttributeError`

现象：新加的评测/运行时 harness 在 Linux 上全绿，Windows 上 `pytest` 大批失败，失败信息只有一句业务化文案
（本例：`Configuration identity could not be verified`），看不出平台原因；同一套代码在 CI（ubuntu）上永远不红。

判据（`oceanbase/powercontext` #2315，2026-11-02，head `7c6939d9`，`evaluation/performance/input_encoding/identity.py`）：

```python
descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)   # win32: AttributeError
... or info.st_uid != os.getuid()                                          # win32: AttributeError
```

直接调内部函数即可定位，不必跑整套用例：

```
platform win32 / has getuid: False
ERR AttributeError module 'os' has no attribute 'O_NOFOLLOW'
```

`pytest tests/evaluation/input_encoding` 在同一 head 上是 46 failed / 52 passed，全部收敛到同一个根因；
包内 `grep -n "sys.platform\|os.name"` 零命中，说明不是环境问题而是缺少平台分支。

做法：

1. 看到"新增文件权限/属主/单链接校验"的代码，先 `grep -n "O_NOFOLLOW\|st_uid\|getuid\|0o600"`，再确认同文件有
   `sys.platform`/`os.name` 分支；没有就按平台缺口处理，不要等 CI。
2. 在目标平台直接调用最小内部函数（`from pkg.mod import _read_key`）拿异常类型；这一步比跑套件快，也不受
   fixture 影响。
3. 判断第二个缺陷：`except Exception: raise DomainError("...") from None` 会把 `AttributeError`/`OSError` 统一
   压成业务文案，属可报告问题（掩盖真实原因、让平台回归无法自查），可与主问题合并成一条评论。
4. 结论按 `R05` 分级：CI 只在 ubuntu 跑 ⇒ 不算"PR 把 CI 弄红"，但要写明"该平台无法执行"而不是"不适用"。

关键词：`validated_at: 2026-11-02`、`validated_ref: powercontext #2315 head 7c6939d9（win32 / CPython 3.14.3）`、
`applies_to: 新增本地密钥/凭据文件、评测 harness、CLI 缓存文件校验的任意仓库`、
`recheck_when: 模块改用 pathlib/tempfile 抽象、或测试矩阵纳入 Windows job 时`。

<a id="exp-107"></a>

## 在 blobless 克隆上取某个 PR 的源码树：`git archive` 会逐个拉 blob 并可能被 RPC 打断，改用稀疏克隆

`git clone --bare --filter=blob:none` 之后执行 `git archive <ref> | python tarfile`，blob 是逐个按需拉取的：
一个含 1000+ 文件的树会变成上千次懒取，几分钟到十几分钟，且实测在 `curl 56 schannel: server closed abruptly`
处直接失败（`fetch-pack: unexpected disconnect`），`git archive` 返回 **0 字节**，随后 `tarfile.open` 抛
`ReadError: empty file` —— 容易误判成仓库或工具问题。

可行的替代（实测 #2489/#2498，每个 PR 约 1.5 分钟）：

```bash
git init <dir>
git -C <dir> remote add origin <https-url>
git -C <dir> config extensions.partialClone origin
git -C <dir> config remote.origin.promisor true
git -C <dir> config remote.origin.partialclonefilter blob:none
git -C <dir> config core.sparseCheckout true
printf 'src/\ntests/\nscripts/\npyproject.toml\nuv.lock\n' > <dir>/.git/info/sparse-checkout
git -C <dir> fetch --filter=blob:none --depth 1 origin refs/pull/<N>/head
git -C <dir> checkout FETCH_HEAD   # 一次性批量取所需 blob
git -C <dir> rev-parse HEAD        # 必须等于 PR head SHA，按 R03 记录
```

要点：

- `checkout` 只对 sparse 模式命中的路径发一次批量 promisor 取，规模由路径数决定，不随仓库总文件数增长。
- 取完核对 `git rev-parse HEAD` 与 `pulls/<N>` 的 `headRefOid`；`git status --porcelain=v2 --untracked-files=all` 应干净。
- Windows 下 `git show refs/pr/<N>:<path>` 会被 MSYS 把 `:` 后的路径转成反斜杠，命令报
  `ambiguous argument 'refs\pr\2498;...'`；加 `MSYS_NO_PATHCONV=1` 前缀即可。单文件读取走这条路最快，不必整树取。

关键词：`validated_at: 2026-11-05`、`validated_ref: #2489 head 84b9011a / #2498 head c3f730ef`、
`toolchain: git for Windows（schannel）+ Python 3.13 tarfile`、`applies_to: 只读审查镜像的建立`、
`recheck_when: 远端支持 filter 协商的配置变化、或改用 hedd/其他归档通道`。

<a id="exp-113"></a>

## 宿主机上的 loopback 集成测试超时：先做 base 对照，别急着归因 PR

现象：Rust/Go 的本地 HTTP fixture 用例在 Windows 宿主机上稳定得到终态 `TimeoutAwaitingResponse`，
而同一 head 在 ubuntu CI 全绿；失败的用例名与用例数完全一致，总耗时恰好等于用例里写的超时值。

判据：把同一组用例在 **base 的 exact 副本** 上再跑一次（`git archive <base>` 到独立目录，独立
`CARGO_TARGET_DIR`）。两侧同样失败 ⇒ 环境/基线，只能写成"本机未取得该 crate 的行为证据"；
只有 base 绿、head 红才是 PR 引入。反之，head 红而 base 未测时不得给出 PR 归因。

补充：`cargo test -p <crate>` 的失败要区分 crate 内部的纯逻辑用例（宿主机通常可跑）与需要
loopback/子进程/UDS 的集成用例（宿主机可能不可跑）。不要因为一个 test target 红就否定整个 workspace 结论，
也不要因为 CI 绿就跳过宿主机证据这一步——两者回答的是不同问题。

相关：`review.md` `R05`（PR/基线/环境三分）与 `R06`（按平台选环境）。

关键词：`validated_at: 2026-11-07`、`validated_ref: oceanbase/powercontext #2506 head a1707cde / base b8b18909`、`applies_to: 任何在宿主机跑 loopback/子进程集成测试的判断`、`recheck_when: 宿主机操作系统、工具链版本或测试 fixture 的传输方式变化`。

<a id="exp-116"></a>

## Windows 上 `git archive` 会按 `core.autocrlf` 导出 CRLF，逐 blob 校验必须显式关闭

现象：在 `core.autocrlf=true` 的宿主机上 `git archive <ref> | tar -x` 得到的工作树是 CRLF，与仓库 blob（LF）逐字节比对
会出现成片"不一致"（本次 3647 个文件中 3101 个被判坏），很容易误判成"镜像被改动"或"仓库本身有问题"。

判据：导出时显式 `git -c core.autocrlf=false -c core.eol=lf archive <ref>`；校验时用 `git cat-file -p`/`hash-object`
比对 blob，而不是比对工作树文件。另需跳过 `mode == 120000` 的符号链接（Windows 上会抛 `PermissionError`）。
行尾/行长/尾随空白的一切结论都以 blob 为准，不以工作树为准。

同一根因的第二种表现：**仓库内的产物自校验测试**会因此假失败。若被测代码把"磁盘上夹具文件的 sha256"写进生成的
报告，再有一个用例断言"新生成的报告逐字节等于仓库里的 pinned 报告"，那么在 CRLF 工作树上生成的摘要必然不同，
用例红而代码没错（本次 `evaluation/memory/prepared_context_budget` 的 `test_the_pinned_report_replays_byte_for_byte`
即如此：CRLF 版 `budget-v1.json` 摘要 `f6b33a69…`，LF 版为 pinned 里声明的 `f66d20fd…`）。

判据：先按上一条用 `git -c core.autocrlf=false -c core.eol=lf archive <ref>` 建探针树重跑该用例；全绿即行尾导致，
不得写成 PR 缺陷。反过来，若 LF 副本仍不等，才把差异收敛到具体字段（本次只差 `manifest_sha256`/`definitions_sha256`
两行，其余用例结果完全相同），据此区分"报告过期"与"实现漂移"。

相关：`review.md` `R03`（独立镜像）与 `R04`（只读保护：镜像不得被本地转换污染）。

关键词：`validated_at: 2026-11-09`、`validated_ref: oceanbase/powercontext #2529 head 5411017c（LF 副本 29 passed / CRLF 副本 28 passed）与 #2296 head fe761522（3647 blob，bad 0/3101）`、`applies_to: 任何在 Windows 宿主机上做 blob 级镜像校验或重放仓库内 pinned 产物的仓库`、`recheck_when: 宿主机 git 配置、仓库 `.gitattributes`，或产物把文件摘要写入自身内容的机制变更`。

<a id="exp-119"></a>

## "镜像 + 共享 venv" 跑测试前必须打印 `powercontext.__file__`：site-packages 里的正式版会静默顶掉镜像源码

现象：用 `PYTHONPATH=<mirror>/src`（或 `run_mirror_pytest.py` 的 `sys.path.insert(0, ...)`）跑镜像里的用例，实际导入的仍是
`<venv>/lib/python3.x/site-packages/powercontext/...`。原因不是路径顺序，而是共享 venv 里装了一份**正式版** wheel（本次为
`powercontext 1.5.0`），且 `_virtualenv.pth` 注册的 `_Finder` 位于 `sys.meta_path`，优先于任何 `sys.path` 条目；只看
`run_mirror_pytest.py` 里按 `"editable" in type(finder).__module__` 过滤的逻辑会以为已经清理干净（该 finder 的模块名是
`_virtualenv`，不含 `editable`）。

判据与做法：

- 每次在镜像里跑 Python 测试前，先跑一行 `python -c "import powercontext; print(powercontext.__file__)"`（带上和正式运行完全相同的
  `PYTHONPATH`），确认路径落在镜像内。若落在 `site-packages`，本轮所有"实测"结论作废。
- 症状识别：镜像源码里明显存在的符号（本次是 `topic_memory_index._GLOBAL_ROWID_END`）在导入的模块上 `hasattr` 为 False，
  或新增的用例直接 AttributeError——这通常不是 PR 问题，而是导入到了别的版本。
- 干净做法优先用不带 `powercontext` 的 venv，或把 venv 里的 wheel 与 `*.dist-info` 移出后再跑；确实要复用共享 venv 时，
  在 pytest 插件里先 `sys.modules.pop("powercontext*", None)` 再显式 `sys.path.insert(0, mirror/src)`，仍要回读 `__file__`。

同类陷阱（同一轮踩到两次）：`wsl.exe -d Ubuntu -- bash -lc '... $VAR ...'` 里的 `$VAR` 会被**外层 Git Bash 先展开**，
`$PWD` 因此变成 Windows 路径，`cd`/`PYTHONPATH` 静默失真。要么用单引号 heredoc 把变量留给内层 shell（确认外层不展开），
要么把命令写进 `.sh` 文件后 `wsl.exe ... bash /mnt/.../x.sh`。

相关：`review.md` `R05`（工具选择与环境归类）、`R06A`（测试真实性：必须确认目标代码真的被执行）。

关键词：`validated_at: 2026-11-10`、`validated_ref: oceanbase/powercontext #2532（_shared/venv-wsl 内 powercontext 1.5.0 覆盖镜像 src）`、
`toolchain: Python 3.13.11 / WSL Ubuntu / venv-wsl`、`applies_to: 所有"隔离镜像 + 复用共享 venv"的本地验证`、
`recheck_when: 共享 venv 重建、改为 editable 安装、或 run_mirror_pytest.py 的 finder 过滤逻辑变更`。

<a id="exp-124"></a>

## 复用工作区 `.venv` 跑镜像代码时，`PYTHONPATH` 必须是绝对 Windows 路径

**现象**（2026-11-12，oceanbase/powercontext #2583 head `5325db8c`，Windows + Git Bash）：用工作区
`D:/test/github/powercontext/.venv/Scripts/python.exe` 跑镜像里的用例，命令写成
`PYTHONPATH=$PWD/src` 时 5 个用例失败，且失败形态完全不像环境问题：
`TypeError: ...create() got an unexpected keyword argument 'idempotency_key'`（11 个用例）与
`test_api_contract::test_server_publishes_the_canonical_openapi_schema`、
`test_migration_revision_names` 的 4 个参数化用例失败（`pending_migrations` 少一项新 revision）。

**根因**：Git Bash 的 `$PWD` 是 POSIX 形式 `/d/test/...`，Windows 版 CPython 无法把它当路径使用，
**静默丢弃**该 `PYTHONPATH` 项。于是 `powercontext` 落到 `.venv` 里的 editable 安装
（`_editable_impl_powercontext.pth` → 工作区 `src`），而 `tests/`、`conftest` 来自镜像 ⇒
被测源码与测试代码来自两个不同提交，产生「新测试打旧实现」「新清单打旧迁移链」这类假失败。

**判据与处理**
1. 执行前先自证导入来源：`python -c "import powercontext; print(powercontext.__file__)"` 必须指向镜像
   `<mirror>/src/powercontext/__init__.py`；指向工作区即说明 `PYTHONPATH` 未生效。
2. `PYTHONPATH` 写绝对盘符路径（`D:/.../<mirror>/src`）；需要 `tests` 包时再追加镜像根目录，
   Windows 用 `;` 分隔（`PYTHONPATH="D:/.../src;D:/..."`）。
3. 失败形态是「新 API 不存在」「清单少一项」这类**跨提交错配**时，先怀疑导入来源，不要先怀疑 PR：
   本次 5 个失败全部在修正路径后转绿（94 passed），若照旧记录会误报 2 条 P1。

**关键词**：`validated_at: 2026-11-12`、`validated_ref: oceanbase/powercontext #2583 head 5325db8c`、
`applies_to: Windows + Git Bash 下复用工作区 .venv 跑隔离镜像（editable 安装到另一个 src）`、
`recheck_when: 改用容器/WSL 执行、或 .venv 不再以 editable 指向工作区 src`。

<a id="exp-139"></a>

## 工作区 `.venv` 的 editable 目标可能指向另一个 PR 的 `probes/` 目录（2026-11-14 实测）

**现象**：在 `{REPO}\.venv` 上跑隔离镜像测试，不设 `PYTHONPATH` 时
`import powercontext` 解析到
`{WORKSPACE}\review\oceanbase-powercontext-pr-2635\probes\git-tree-8a0e2da4\src\powercontext\__init__.py`
——即**另一个 PR 的审查镜像**，不是工作区主检出。

**成因与判据**：该 venv 的 editable 形态是 `.pth`（`Lib/site-packages/_editable_impl_powercontext.pth`
逐行写绝对路径），不是 `__editable__*_finder` 模块。`.pth` 的路径排在 `PYTHONPATH` **之后**，
因此 `PYTHONPATH=<镜像>/src` 能正常覆盖；与之相反，meta_path finder 形态会抢先占住包名、
`PYTHONPATH` 压不过（见本文件「子包测试的 PYTHONPATH 顺序」一节）。
`ls Lib/site-packages | grep -i __editable__` 为空即可判为 `.pth` 形态。

**处理**：每轮跑镜像测试前固定先执行
`PYTHONPATH=<镜像>/src {venv}/python -c "import powercontext; print(powercontext.__file__)"`，
输出必须落在镜像内；再用同一 `PYTHONPATH` 起 pytest。变异副本同理（`PYTHONPATH=<probes>/src_mut`）。
不要因为看到 `.pth` 指向陌生目录就去改 venv 或重装——那是工作区状态，不属本轮授权范围。

**关键词**：`validated_at: 2026-11-14`、`validated_ref: oceanbase/powercontext #2429 head dfbce7e0 / #2435 head 67fcfdaa`、
`applies_to: 用工作区 venv + PYTHONPATH 跑隔离镜像的本仓审查`、
`recheck_when: venv 重装、editable 改为 meta_path finder、或 `.pth` 指向内容变化`。

<a id="exp-144"></a>

## 从 Windows 调用 WSL 跑 e2e 时的三个环境陷阱（2026-11-15 实测 #2616）

1. **`wsl.exe -d Ubuntu -- bash -lc '...'` 里 `$VAR` 可能整体失效**：`M=...; cd $M && PYTHONPATH=$M/src:$M ...`
   实测 `cd` 与 `PYTHONPATH` 都被按空值处理（pytest 报 `file or directory not found`、python 却 import 到
   `{REPO}/src` 的旧 editable）。把路径**全内联写死**（`cd /mnt/d/... && PYTHONPATH=/mnt/d/.../src:/mnt/d/...`）
   即恢复，不要为了复用字符串引变量。
2. **Git Bash 会把含 `;` 的 `PYTHONPATH` 当路径列表做 MSYS 转换**：`PYTHONPATH="$PWD/src;$PWD"` 变成
   `D:\d	est\...`（多一层 `\d`），于是 import 落到别的 editable 目标而 `powercontext.builtin.authz` 等
   子模块 `ModuleNotFoundError`——症状像「镜像树缺文件」。写 Windows 风格绝对路径并加 `MSYS_NO_PATHCONV=1`。
3. **`uv sync --locked` 在裁剪过的副本上连错三关**：缺 `[tool.uv.sources]` 指向的
   `integrations/{langchain,langgraph,opendal}`（`Distribution not found`）、缺 `README.md`/`LICENSE`
   （hatchling `Readme file does not exist`）、无 `.git` 时 setuptools-scm 失败（`SETUPTOOLS_SCM_PRETEND_VERSION=0.1.dev1`）。
   另外 `--default-index` 换源会让 `--locked` 报 `lockfile needs to be updated`——换源就别带 `--locked`，
   要锁版本就用原索引并加 `UV_HTTP_RETRIES`（本次 `files.pythonhosted.org` TLS `handshake eof` 一次，重试即过）。

**关键词**：`validated_at: 2026-11-15`、`validated_ref: oceanbase/powercontext #2616 head 6d847297`、
`applies_to: 本机 Windows + WSL Ubuntu 取证`、`recheck_when: wsl.exe 参数传递行为、uv 版本或 workspace 布局变化`。

<a id="exp-148"></a>

## 新增用例若要证明平台行为，Windows 侧的两条硬前提：`TimeoutExpired.stdout` 是 `str`、`str(Path("/proc/..."))` 带反斜杠（2026-11-16 实测 #2518 head 611c2498）

Windows 上给 Python subprocess 相关新用例判红/判绿前，先分清「用例写错」与「用例首次覆盖了旧代码的平台假设」：

- `subprocess.run(..., text=True, timeout=N)` 抛 `TimeoutExpired` 时，POSIX 的 `error.stdout` / `error.stderr`
  仍是 **bytes**（所以要 `.decode()`），Windows 走线程读管道给的是 **str** ⇒ 既有 `.decode()` 直接
  `AttributeError: 'str' object has no attribute 'decode'`。一批旧代码只在超时分支里这样写时，平时全绿，
  一旦新增用例真的把子进程拖到超时就会在两行内暴露。
- 用 `str(path).startswith("/proc/")` 做拦截/分支在 Windows 恒为假：`Path("/proc/1/stat")` 的字符串是
  `\proc\1\stat`。monkeypatch `Path.read_text` 并按该前缀抛 `ProcessLookupError` / `PermissionError` 的用例，
  在 Windows 上会落到真实读盘（FileNotFoundError），`pytest.raises(PermissionError)` 直接 DID NOT RAISE。
  同族 POSIX-only 用例在本仓的既有写法是 `@pytest.mark.skipif(sys.platform != "linux", ...)`。
- 判「CI 会不会发现」不能只看 job 名：本仓 `windows-unit-portability` 只跑显式文件清单
  （`tests/builtin/runtime/test_artifact_processing.py`、`tests/e2e/test_worker_logging.py` 等），
  `tests/e2e/test_database_bootstrap.py`、`tests/test_upgrade_release_gate.py` 都不在清单内 ⇒ 平台红只出现在
  本地与贡献者机器上。定级按「支持平台上的本地回归」处理（P2），不按 CI 阻断处理。

**关键词**：`validated_at: 2026-11-16`、`validated_ref: oceanbase/powercontext #2518 head 611c2498`、
`toolchain: Windows 11 / CPython 3.14 / pytest 8.x`、`applies_to: 任何在 Windows 上跑 e2e 或 subprocess 相关用例的仓库`、
`recheck_when: 仓库把这两个文件加进 windows 作业清单，或 Python 改为在 Windows 上也返回 bytes`。

<a id="exp-149"></a>

## 共享 venv 的 editable `.pth` 会把某个历史 probe 树插到 `sys.path` 首位，压过 `PYTHONPATH`（2026-11-16 实测 #2615）

现象：从 PR 镜像跑 `PYTHONPATH=<mirror>/src pytest <镜像用例>`，收集期报
`ModuleNotFoundError: No module named 'powercontext.builtin.persistence.migrations.profile_transitions'`，
而该文件明明在镜像里。`python -c "import powercontext; print(powercontext.__file__)"` 打出的是
`D:	est\github
eview\oceanbase-powercontext-pr-2635\probes\git-tree-...\src\powercontext\__init__.py`
—— 共享工作区 venv 的 `Lib/site-packages/_editable_impl_powercontext.pth` 里写的是**某一轮 probe 树的绝对路径**，
`.pth` 在 site 初始化时被处理，落点排在 `PYTHONPATH` 之前（或被插入到索引 0）。

判据与处理：

- 判据：先 `import powercontext; print(powercontext.__file__)`，别先怀疑镜像不完整；`grep` 该 `.pth` 的内容，
  比对是否指向别的 `review/...-pr-<N>/probes/` 目录。
- 两个独立的坑会同时出现：**`PYTHONPATH` 必须写盘符绝对路径**（`$PWD/src` 这类 POSIX 形式会被 Windows CPython
  静默丢弃，MSYS 还可能把 `/d/test/...` 变成 `D:\d	est\...`）。写错了 `sys.path` 里根本没有镜像项，
  editable 路径自然胜出。
- 兜底：在 `probes/prelude/sitecustomize.py` 里过滤掉 `review/*-pr-*/` 的陈旧条目，并把 `probes/prelude` 放在
  `PYTHONPATH` 最前（`sitecustomize` 在 `.pth` 处理之后导入）。注意路径写错时它也不会被导入——先验证 `import` 结果。
- 更彻底：给镜像单独 `uv venv`（R-PC119 的 `uv sync --locked`），不复用工作区 venv。

**关键词**：`validated_at: 2026-11-16`、`validated_ref: oceanbase/powercontext #2615 head 9275f2cc`、
`toolchain: Windows 11 / CPython 3.14 / 共享工作区 .venv（editable install）`、
`applies_to: 所有用共享 venv + 镜像 src 跑测试的仓库`、
`recheck_when: 共享 venv 重装、editable 安装方式改为 import hook、或镜像根目录结构变化`。

<a id="exp-152"></a>

## Windows 上 `bash` 解析到 WSL 时，`subprocess` 的 Windows 环境变量不会跨 interop 传递（2026-11-17 实测 #2518）

现象：`tests/test_upgrade_release_gate.py` 的 `test_upgrade_gate_distinguishes_not_required_from_missing_acceptance`
把 workflow 里的 gate 脚本取出来，用 `subprocess.run(["bash","-e","-c",script], env={**os.environ, "SCOPE_RESULT":…})`
执行并在本地比较退出码。本轮在 head 上跑，8 个参数组合里 2 个「应通过」的失败，看起来像 PR 把 gate 改坏了。

判据与处置：

- 先看 `bash --version`：本机输出 `GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu)` ⇒ 这是 WSL 的 bash，
  不是 Git Bash。用同一组 `env` 跑 `bash -c 'echo "$SCOPE_RESULT"'` 会得到空串，说明变量没有跨
  Windows→WSL 边界传过去；脚本里的 `[ "" = success ]` 落入 `else`，于是**任何**参数组合都返回 1。
- 因此这类用例在 Windows 上恒红且与 PR 无关，属环境问题（`R05`）；不要记为 Finding，也不要拿它支持
  「gate 逻辑被改坏」的结论。真正的证据用同 head 的 ubuntu CI（`Upgrade release gate` 作业）或 WSL 内原生跑。
- 同类陷阱：`subprocess` 传给 WSL bash 的字符串里若含 `(`、`)`、`!`，还会被当成语法错误
  （本轮 `bash -c 'echo $BASH_VERSION'` 报 `syntax error near unexpected token '('`），所以连「探针本身」都要用
  不含元字符的最小命令。
- 泛化：凡是「用 `bash -c` 重放 CI 里的 shell 片段」的本地验证，先确认 `bash` 是哪一个、env 是否真的到达，
  再解释退出码；在 Windows 上这两条都恒为否。

`validated_at: 2026-11-17`、`validated_ref: oceanbase/powercontext #2518 head b44d3e6b`、
`toolchain: Windows / Git Bash 工具链 + WSL bash 5.2.21`、
`applies_to: 在本机重放 workflow 内 shell 片段的任何 Python 测试`、
`recheck_when: 本机 PATH 里的 bash 改为 Git Bash，或测试改用 subprocess 之外的方式传参`。


### `git ls-files` 类门禁在 partial clone 上的取证做法：`git archive` + `git init && git add -A`（2026-11-18 实测 oceanbase/powercontext #2704 / #2703）

- 现象：共享裸克隆是 `--filter=blob:none`。`git clone --shared <bare>` 之后再 checkout 会成片
  `error: unable to read sha1 file of ...` / `invalid object ...`（promisor 元数据没有跟着 blob 一起过来），
  但 `git archive` 会经 origin 惰性补齐 blob，因此 archive 出来的树是完整的。
- 做法：`git --git-dir=<bare> -c core.autocrlf=false -c core.eol=lf archive refs/pr/<N> | tar -x -C <mirror>/source/head`
  → 在 `<mirror>/source/head` 里 `git init -q . && git add -A`（`.gitignore` 自动生效）→ 需要 `git ls-files`
  的门禁（`scripts/generate_integration_lifecycle.py --check`、`package_extras`、`uncommitted` 判据）即可直接跑。
  这一步只在镜像内造索引，不碰主证据副本的 refs，符合 `R04`。
- `git add -A` 打印的 `LF will be replaced by CRLF` 只是 `core.autocrlf=true` 的提示，工作树仍是 archive 的 LF，
  `render()/read_text()` 对比因此不会假红。
- `deploy/observability/*` 的 9 个符号链接在 Windows 上必然 `Operation not permitted`，archive 退出码可能是 2，
  文件数仍完整；判完整性看 `find <mirror> -type f | wc -l` 与 `git add -A` 后的索引条数，不看 tar 退出码。

`validated_at: 2026-11-18`、`validated_ref: oceanbase/powercontext #2704 head c05dfc72、#2703 head 578b1184`、
`toolchain: Git Bash / git 2.x / Windows`、
`applies_to: 需要 `git ls-files` 或工作树完整性的门禁脚本，在 partial clone 镜像里执行时`、
`recheck_when: 裸克隆改为完整克隆、或门禁脚本改用非 Git 的文件枚举`。

### `pulls/{n}/comments/{id}/replies` 只接受 `body`（2026-11-18 实测 oceanbase/powercontext #2562）

- `POST .../pulls/{n}/comments/{id}/replies --input payload.json` 若 payload 里带 `commit_id` 或 `path`，
  返回 422 `"commit_id", "path" are not permitted keys`。与 `in_reply_to` 同类，发送前统一剥成只剩 `body`。
- 新建行内评论（`/pulls/{n}/comments`）才需要 `commit_id + path + line + side`；两种 payload 不能复用同一份文件。

`validated_at: 2026-11-18`、`validated_ref: oceanbase/powercontext #2562 head bdc2b6b9`、
`applies_to: 通过 REST 发布行内评论或线程回复的全部场景`、
`recheck_when: GitHub REST 文档对 replies 端点字段的描述变化`。

### WSL 内 cargo 无法下载 crates 时的证据替代（2026-11-19 实测 oceanbase/powercontext #2435）

- 现象：`cargo test` 反复 `spurious network error … Could not connect to server (127.0.0.1 port 7890)`，但
  `env | grep -i proxy` 只有 `GOPROXY`、`~/.cargo/{config,config.toml}` 均不存在；同一 shell 里
  `curl -m 8 https://static.crates.io/...` 直连返回 200，`--offline` 报 `failed to download`。
  ⇒ 代理来自非环境变量通道，不要在 shell 里继续找变量、也不要把它记成仓库网络问题。
- 处置：不在宿主硬跑 Rust 门禁，改用可信 CI 的 job 日志作行为证据：
  `gh api repos/{owner}/{repo}/commits/<head>/check-runs` 取 job id →
  `gh api repos/{owner}/{repo}/actions/jobs/<job_id>/logs` → grep 目标用例名与 `test result:` 行，
  记录 job 名、conclusion、exact head。日志里的 `test prefix_store::tests::<name> ... ok` 即该用例在 CI 上真实执行过。
- 附：Rust 门禁若在 Windows 直接跑，先确认 crate 不含 unix-only 依赖（如 `tokio::net::UnixStream`），否则失败属平台不兼容，
  不能算 PR 缺陷。

`validated_at: 2026-11-19`、`validated_ref: oceanbase/powercontext #2435 head 26d6e928、job 135373602352`、
`applies_to: 需要在 WSL 或本机执行 Rust 门禁的审查`、
`recheck_when: WSL 的 cargo 代理配置变化、或 workspace 改用可离线构建的 vendor 目录`。

### 带 code 的完整性异常被并进 SQL 降级分支（2026-11-19 实测 #2674）

- 现象：`enumerate_aliased_related` 为 `alias-chain` / `stale-recall` 五种不一致各起了 code，调用方却写成
  `except Exception: _require_alias_snapshot(...); aliases = ()`，`_require_alias_snapshot` 只对「连接失效 / savepoint 不存在」重抛。
  ⇒ 数据一致性错误静默退化成「少召回」，且无 `log_safely`，与同一函数里直连通道的 `stale-recall → _conflict` 不对称。
- 判据：在降级 helper 里逐个列出会重抛的类型，与上游 `raise` 的 code 集合求差；差集里的 code 一旦属于完整性/版本一致性，
  就不是「可降级的 SQL 失败」，至少要有运营日志。
- 处置：按「SQL 层失败 vs 带 code 的完整性异常」两类分开写 except，并要求一条「一致性错误不会被吞」的用例。

`validated_at: 2026-11-19`、`validated_ref: oceanbase/powercontext #2674 head faccf373`、
`applies_to: 审查带 fail-open 降级路径的检索/索引代码`、
`recheck_when: 该降级 helper 的类型集合或日志约定变化`。

### 同一处无关改动出现在多个 open PR：按同名文件的 hunk 逐字比对（2026-11-19 实测 #2710 / #2713）

- 现象：两个不同作者、不同主题的 PR 都在 `src/powercontext/server/dashboard/content.py:281-286` 重排了同一段，
  一个把判断放在 `try` 前（#2713），一个放进 `try` 内（#2710），语义都与原实现等价。
- 判据：看到与 PR 主题无关的文件时，先在其他 open PR 的同名文件里搜同一段（`gh api .../contents/<path>?ref=<head>`），
  形态不同即构成合并冲突面；同时用「三个分支取值逐一展开」证明它是否真的等价，避免把它写成行为缺陷。
- 处置：按「无关改动 + 冲突面」报，建议移出或单独 PR；不要按「逻辑错误」定级。

`validated_at: 2026-11-19`、`validated_ref: oceanbase/powercontext #2710 head c66f8be0 / #2713 head fa34dc35`、
`applies_to: 改动面里出现与标题无关的模块文件时`、
`recheck_when: 两个 PR 的该 hunk 被移出或合并完成`。

### 同一修复被两个 open PR 重复实现：比 blob 而不是比 hunk（2026-11-20 实测 #2658 / #2710）

- 现象：两条不同提交信息（#2658 `307cfe28 fix(statistics): retry SQLite usage setup within batch budget`、
  #2710 `1dcd3e46 fix(stats): retry SQLite usage writes after setup expiry`）改的是同一处
  `src/powercontext/builtin/persistence/database.py`（`TimeoutError → ModelUsageAttemptExpired`）。
- 判据：`git rev-parse <ref>:<path>` 逐文件比对两棵 head 树的 blob；相同即"同一实现被复制"，与 hunk 形态无关
  （上一条针对的是形态不同的无关改动，本条针对完全相同的内容）。
- 追加证据：若两者都改同一份单值声明（`release/upgrade-support.json::schema_review.persistence_sha256`），
  且为它写的 rationale 句子**措辞不同**，则后合入者必然在该字段文本冲突。措辞差异要用 `difflib` 按句切分比对，
  不要只看 sha 是否相同——sha 相同反而更容易被误判为"不会冲突"。
- 处置：报"重复实现 + 合并顺序"，建议后合入方 rebase 掉整个改动；不要按"逻辑错误"定级。

`validated_at: 2026-11-20`、`validated_ref: oceanbase/powercontext #2658 head b75c0666 / #2710 head 16ab67ae`、
`applies_to: 改动面里出现与 PR 标题无关的持久层/统计文件时`、
`recheck_when: 任一 PR 被合入或 rebase`。

### `[tool.ty.src] exclude` 新增目录不等于类型门禁被绕过（2026-11-20 实测 #2658）

- 现象：新插件 PR 在 `pyproject.toml` 的 `[tool.ty.src] exclude` 里加了 `plugins/knowledge-base`，
  注释称"CI 会显式检查该目录"，表面上是把一个 2000+ 行的新包踢出强制类型检查。
- 判据：先查 CI workflow 里是否真有 `ty check --no-force-exclude <该目录>`（`--no-force-exclude` 让显式传入的路径
  跳过 `exclude`）。命中则排除项只是为了避免默认递归把插件当核心包处理，不构成门禁豁免。
- 反例边界：若 CI 只有 `ty check --python-platform win32` 之类不带目录参数的调用，则该目录确实逃过门禁，按 P2 报。
- 处置：结论写进报告或评论时必须同时给出 CI 的命令行原文，不能只引用 `pyproject.toml` 的 exclude 段。

`validated_at: 2026-11-20`、`validated_ref: oceanbase/powercontext #2658 head b75c0666（master.yml:1648）`、
`applies_to: PR 新增子包并在 lint/type 配置里加 exclude 时`、
`recheck_when: CI 的类型检查步骤或 ty 版本变化`。

### 模块级 fixture "被删除" 多数是上移到 conftest（2026-11-20 实测 #2658）

- 现象：Diff 里两个 e2e 文件各删掉十几行 `import shutil` / `_ROOT` / `def gateway_binary()`，看起来会让
  仍以该名作参数的用例名报 `NameError` 或静默 skip。
- 判据：同 PR 的 `tests/e2e/conftest.py` 若同时新增同名 `@pytest.fixture(scope="session")`，删除就是去重；
  session 作用域还顺带省掉每个模块各 build 一次的开销。只看被删文件不足以判定。
- 处置：先 `grep -rn "def <fixture>" tests/` 确认定义仍存在再决定是否报；确无定义才按 P1 报可运行性问题。

`validated_at: 2026-11-20`、`validated_ref: oceanbase/powercontext #2658 head b75c0666`、
`applies_to: Diff 中出现 fixture / helper 删除行且同 PR 改了 conftest 时`、
`recheck_when: conftest 的 fixture 作用域或命名变化`。

### 格式化门禁只认「字节等值」：`json.loads` 通过不代表 hook 通过（2026-11-20 实测 #2728）

- 现象：手工往 2000 行已格式化的大 JSON 数组里追加一个对象，`{` 落在第 0 列（其余项两空格缩进）。文件语法合法、
  业务测试全过，但 `pretty-format-json --autofix` 会改写该行并让 hook 以 1 退出，进而让整条 `make check` 链红、
  下游 job 全部 skipped。
- 判据：不要用 `json.loads` / `json.tool` 判断；直接比对 `json.dumps(obj, indent=2, sort_keys=False, ensure_ascii=False) + "\n"`
  与原字节。差 2 字节即说明只有一个缩进层级错。要拿"hook 真的会红"的证据，就在 `probes/` 建一个只含该 hook 的临时
  git 仓库（`git init` + 原 config 段 + 原文件），跑 `prek run <hook> --all-files`，输出必为 `files were modified by this hook`。
- 边界：命中后先确认 hook 的 `exclude` 是否覆盖该路径（本仓 exclude 只列 devcontainer、两个 evaluation 数据集与
  gateway 的 republic 夹具），以及该路径是否真的在版本控制内。
- 处置：定级按协议 §4——"使强制门禁失败"即 P1，但正文要写明修复是机械的（补两空格/跑一次 hook），别让作者误以为是设计问题。

`validated_at: 2026-11-20`、`validated_ref: oceanbase/powercontext #2728 head a79edde7`、
`toolchain: prek + pre-commit-hooks v6.0.0（Windows 工作区 .venv 自带 prek.exe）`、
`applies_to: PR 手工追加/重排 JSON、YAML 或生成物清单时`、
`recheck_when: .pre-commit-config.yaml 的 hook 集合或 exclude 列表变化`。

### 结构化日志的字段白名单会静默吞掉 `extra=`，`caplog` 断言是假绿（2026-11-20 实测 #2675）

- 现象：新失败路径写 `log_safely(..., extra={"event": ..., "outcome": ..., "unit": ..., "error_type": ...})`，
  作者还补了断言 `failures[0].error_type == "RuntimeError"`，看起来诊断完整。
- 判据：查日志模块的 `_OPERATIONAL_FIELDS` 白名单（本仓 `server/logging.py`）；`_operational_payload()` 只按白名单取属性，
  未登记的字段不会出现在 JSON/OTLP 输出里，但 `LogRecord` 上仍有该属性 ⇒ `caplog` 断言通过、实际输出没有。
  验证方式：构造 `LogRecord` 直接调 `_operational_payload(record)`，看返回字典里有没有该键。
- 处置：建议改用已登记且已文档化的词汇（`error_code`、有界 `error_category`），或补白名单 + 中英双语文档；
  并要求测试断言格式化后的 payload 而不是 record 属性。定 P2（可观测性缺陷，不影响写入正确性）。

`validated_at: 2026-11-20`、`validated_ref: oceanbase/powercontext #2675 head e53da046`、
`applies_to: 新增结构化事件或给既有事件补字段时`、
`recheck_when: 日志白名单、formatter 或 observability 文档的字段表变化`。


### 「CI 红」先分两级：preflight 级红与 tests 级红（2026-11-21 实测 oceanbase/powercontext #2546 / #2541 / #2630 / #2726）

同一个红色 check 名可能来自完全不同的层，归因前先确定是哪一级，再谈是否本 PR 引起：

1. **preflight 级**（`CI preflight` / `quality`）：读 job 日志第一条 `ERROR` / `##[error]` 行。本轮的两种形态是
   license header 缺失（清单直接给出）与 `schema_release.py check --base-ref` 的"已冻结 revision 被判成新增"。
   这一级红 ⇒ 后续 38 个 suite job 全部 `skipped` ⇒ 该 PR 的新增用例**零覆盖**，任何"CI 绿"的口径都不成立。
2. **tests 级**：到用例粒度。本轮两例都是 timing/资源型（`retry_wait == 1` 的 0.78s 窗口、子进程 10s 超时、
   e2e 的 `address already in use`），与本改动面无因果时记 `R15` 不可判定，不要写成缺陷。
3. **级联识别**：`Upgrade release gate` 在 `UPGRADE_SELECTED=true` + `UPGRADE_RESULT=skipped` 时必红，属下游级联；
   同一提交上它和其它红同时出现时，只在根因处开线程。

判据入口：`gh api repos/<o>/<r>/actions/jobs/<job>/logs`（job id 从 `details_url` 取），先用
`grep -n "FAILED\|##\[error\]\|don't have\|Schema release"` 定位层，再读上下文。


### GitHub 全站不可达但国内站点正常：先查本地 fake-IP 代理的选择器指向，再谈网络故障（2026-11-22 实测）

- 现象：`gh api` 与 `urllib` 对 `api.github.com` / `raw.githubusercontent.com` / `github.com` 一律
  `SSL: UNEXPECTED_EOF_WHILE_READING`，`gh auth status` 同时报 `The token in keyring is invalid`；但
  `baidu.com`、`pypi.tuna.tsinghua.edu.cn` 返回 200，Google / YouTube 同样 SSL EOF。
- 关键判据：DNS 解析结果是 **198.18.0.x**（Clash / Mihomo 的 fake-IP 段）⇒ 流量被 TUN 接管，既不是 DNS 污染，
  也不是 token 失效（EOF 是连接被关，401 才是鉴权）。TCP 握手成功、TLS 握手立刻 EOF = 本地代理接受连接、上游节点不可用。
- **不要直接下结论"网络挂了"**：Mihomo 自己的探测可能完全正常。它的控制器常常只监听命名管道（本机 `config.yaml`
  写 `external-controller: 127.0.0.1:9097`，实际只有 `\\.\pipe\verge-mihomo-production-<hash>` 可用；`-sidecar-`
  那条已失效），先用 `[System.IO.Directory]::GetFiles('\\.\pipe\')` 列名字再连。Python 直接
  `open(pipe, 'r+b', buffering=0)` 写 `GET /configs HTTP/1.1` 即可，**响应是 chunked**，需要自己去分块再 parse。
- 三步定位：①`GET /configs` 看 `mode` 与 `tun`；②`GET /proxies` 看各分组 `now`（Selector 组不会自动故障转移）；
  ③`GET /rules` grep 目标域名拿到它归属的分组（本机 GitHub 命中 `DomainKeyword github → 赔钱机场`），再对成员
  逐个 `GET /proxies/<name>/delay?url=https://api.github.com&timeout=4000` 测真实延迟。
- 本例结论：该 Selector 的 `now` 是一个已超时的美国节点，换成实测 202 ms 的节点后 `gh api` 立即恢复。**修复动作
  属于改动用户机器配置**：先记录原值、只改选择器成员、在报告里写明改了什么，不要动 profile 文件或工作模式。
- 备用只读通道：`WebFetch` 走平台侧网络，可匿名读公开仓库 REST（60 req/h）。但它返回模型摘要并会截断 JSON
  （本轮一次 40 项的数组只回 4 项）⇒ 只能用于"有没有新变化"的侦察，不能作为 Diff / digest 级证据，也不能替代需要
  鉴权的通知扫描与评论发布。

`validated_at: 2026-11-22`、`validated_ref: 本机 Clash Verge Rev + verge-mihomo v1.19.33（Windows 服务进程 3292）`、
`applies_to: 本机执行 review 时 GitHub 不可达而国内站点正常`、
`recheck_when: 代理客户端、TUN 配置、控制器管道名或订阅节点变化`。

### PR diff 里的 hunk 可能早已在 master：判「本 PR 新增 / 与谁冲突」前先比 blob（2026-11-22 实测 oceanbase/powercontext #2727 / #2721）

- 现象：`pulls/2727/files` 里 `server/dashboard/content.py` 有一段 12 行改动，看起来既是"与主题无关的重排"，又与在飞的
  #2721（重写同一函数）冲突；`git merge-tree refs/pr/2721 refs/pr/2727` 确实报该文件与 `profile.html` 冲突。
- 实测反证：`git ls-tree master -- <path>` 与 `git ls-tree refs/pr/2727 -- <path>` 的 blob **完全相同**
  （`a9dce2b0…`），`git diff master refs/pr/2727 -- <path>` 为空 ⇒ 该改动已由 master 的另一个提交（`3720f29b`）合入，
  PR 侧没有新增内容。原因是 merge-base（`b64ee80b`）早于那次合入，GitHub 的 Files changed 仍把它算进 PR 面。
- 判据顺序：①`git rev-parse master:<path>` vs `git rev-parse refs/pr/<N>:<path>` 比 blob；②两者相同即不是本 PR 新增，
  既不构成 Finding，也不能作为"与某 PR 冲突"的来源；③两个 PR 分支之间的 `merge-tree` **不是**合并结果——只要一侧内容
  已在 master，分支间冲突在合并时并不存在（本轮 2721 与 master 的 `merge-tree` 干净，与 2727 分支才冲突）。
- 反向适用：`git diff master refs/pr/<N>` 也不是"新增面"的干净视图（会把 master 后续他人的改动显示成 PR 的删除），
  只用于单文件 blob/内容比对。

`validated_at: 2026-11-22`、`validated_ref: #2727 head 5d25170b / master 1840db81 / content.py blob a9dce2b0`、
`applies_to: oceanbase/powercontext 及同类"长期不 rebase 的 PR"`、
`recheck_when: GitHub Files changed 基准改为 merge-base 之外的口径，或仓库改用 merge queue 强制 rebase`。


### 「lineage 由累积改为链式」不必然加深证据遍历：先跑一次遍历再判破坏（2026-11-22 实测 oceanbase/powercontext #2752）

- 背景：#2752 让 Topic Memory 的手动替换只链接上一条精确 Revision（原来把 `current.lineage.artifacts` 整体复制前进），
  直觉结论是"链式会让证据解析多 N 层，超过 `EvidenceLimits.max_depth = 8` 就报错"，看起来是 P1。
- 实测：同一探针（创建 topic + N 次 PUT 替换，再对 head 调 `EvidenceResolver.resolve`）在 base 与 head 上
  **阈值相同**——N=7 通过、N=8 均抛 `EvidenceResolutionError: evidence_limit_exceeded`。原因是旧的"扁平"列表
  每个元素本身也带自己的前序引用，遍历照样逐层递归；节点集合两版完全相同（16 个）。
- 结论：判"改 lineage / 依赖图会不会破坏可达性"必须**实际跑一次限制内的遍历**，不能按"扁平 vs 链式"推断；
  节点数相同、仅边数不同（旧版 O(n²) 边）才是最稳的观察量。
- 探针形态：`TestClient` 建 scope + topic → 循环 PUT（带 `If-Match`）→ 关 client → `open_builtin_contexts`
  对同一 sqlite 文件起 `EvidenceResolver(scope_id=…, sources=…, artifacts=…)`，用 `PYTHONPATH=<tree>/src` 切换实现。

`validated_at: 2026-11-22`、`validated_ref: #2752 head 6e4c7f26 / base master 1840db81`、
`applies_to: powercontext Topic Memory lineage 与 `builtin/evidence` 遍历`、
`recheck_when: EvidenceLimits 的默认值变化、或 `_artifact_children` 改为不递归`。


### 「可选环境变量」无守卫展开时命令会静默成功（不是报错）：`node "" npm ci` 实测 exit 0（2026-11-22 实测 oceanbase/powercontext #2777）

- 现象：workflow 用 `node "$PC_CI_NODE_INSTALLER" npm ci …` 调一个"由 composite action 条件导出"的变量。变量为空时，
  bash 展开成 `node "" npm ci --prefix …`（第一个参数是空串）。
- 实测（Git Bash / Node v22.22.2 / `bash -e`）：退出码 **0**、stdout/stderr 均无输出、`set -e` 不中断、后续命令照常执行
  ⇒ 这个安装步骤在 CI 里显示 **success 但什么也没装**，直到下游真正 `require`/执行该包时以"模块或可执行缺失"失败，
  错误信息不再指向安装步骤。
- 判据：①命令里出现"可能是空串"的变量且没有 `${VAR:-}` 判空 / `if [ -n ]` 守卫，就要按"静默 no-op"审；②修法优先让
  导出方**无条件**导出（无镜像/无代理时常量直通即可），把守卫负担从每个调用点移走；③同一 PR 里若有一处写了守卫、
  其他处没写，说明空值场景已被考虑但覆盖不全，这是最省力的取证入口。
- 反向核对：若下游有 `test -n "$x" || exit 1` 兜底，影响只是"错误位置后移"，不要夸大成"CI 会绿着放过"。

`validated_at: 2026-11-22`、`validated_ref: #2777 head 03763682 / gateway.yml:74 / master.yml:321,1133,1277,1338,1496,1524`、
`toolchain: Node v22.22.2（空脚本参数行为）`、`applies_to: GitHub Actions 与任何 bash 包装脚本`、
`recheck_when: Node 对空 script 参数的处理改变，或该仓库改为无条件导出安装器`。


### `pulls/<N>/files` 端点持续 TLS 超时时用裸克隆对账，不必等端点恢复（2026-11-22 实测 oceanbase/powercontext #2728）

- 现象：`gh api repos/<o>/<r>/pulls/<N>/files?per_page=100 --paginate` 连续多次 `net/http: TLS handshake timeout`
  （同一时刻 `pulls/<N>` 单对象请求也会偶发），而本地裸克隆的 `git fetch refs/pull/<N>/head` 正常。
- 替代路径：`git --git-dir=<bare> diff --name-status <merge-base> <head>` 得到文件清单，
  与 `pulls/<N>` 的 `changed_files` 三向对账（本层用 REST 的 changed_files 数 == 本地 diff 行数）；
  行级内容用 `git diff <base> <head> -- <path>`，单文件取 blob 用 `ls-tree` + `cat-file -p`。
- 注意：在 `--filter=blob:none` 的裸克隆上 `diff --stat` 会为每个 blob 触发 promisor 拉取，网络抖动时会以
  `could not fetch <oid> from promisor remote` 失败（部分文件数仍可拿到）；对账用 `--name-status` 更稳。
- 报告口径：端点超时属于取证通道问题，不是 PR 缺陷；但"文件数对账"必须换通道补齐后才能写"Diff 已对账"。

`validated_at: 2026-11-22`、`validated_ref: #2775/#2776/#2758/#2728（_state/r107）`、
`applies_to: 本机 gh/裸克隆取证流程`、`recheck_when: 网络或代理恢复、或改用 GitHub API 缓存`。

<a id="exp-155"></a>

## 把一条错误路径从 A 类改成 B 类时，用「同类损坏状态」用例证明 A 类仍在真正的判定点触发（2026-11-24 实测 oceanbase/powercontext #2751）

- 场景：PR 把 `undo_merge` 指向非合并结果时的 `invalid_memory_relation`（关系数据不一致）改成 `invalid_memory_state`
  （调用方用错目标）。这类改动最容易顺手把真正的数据损坏也一并降级成「调用方错误」，从而掩盖存储问题。
- 判据：要求 PR 同时给出反面用例——制造只有「内部关系不一致」才能解释的状态（结果记录的输入被删空、输入被改回 active
  而结果仍标记它为输入），断言它们仍抛原来的 A 类错误。三例覆盖 restore 路径与 undo 路径各一条。
- 核对顺序：先找 A 类错误的所有 `raise` 点，确认新增的 B 类判定只看「调用方可判断的前置条件」（记录是否有标记输入），
  再看 `A → B` 的分界是否可能在正常路径上误判（如把「输入数量不足」也归为调用方错误）。
- 对外可见面：错误码变化要同步对外文档的错误表，并在报告里写成「行为变更」而不是「修复」。

`validated_at: 2026-11-24`、`validated_ref: #2751 head c697d08c（merge_restoration.calculate_restoration）`、
`applies_to: 有分层错误码（调用方错误 vs 数据损坏）的服务端代码`、`recheck_when: 该仓库合并错误类型体系或重排 HTTP 状态映射`。
