<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 宿主、并发与生命周期

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-007"></a>

## 递归解析器的资源边界

- 单次 `with_capacity`、单节点 payload 或单层工作量有上限，不代表一次递归解析的总资源有界。必须沿递归调用链计算同时存活的容器容量、调用栈和累计预算，并在分配或继续递归前设置深度或总预算门禁；回归测试同时覆盖最大合法深度、首个非法深度和所有递归容器分支。

<a id="exp-009"></a>

## 多阶段异步请求的统一超时预算

- 将 bounded queue admission 纳入既有请求超时时，必须让入队和后续执行/响应共享同一个 deadline；若两个阶段各自使用完整时长的 `timeout`，最坏总等待时间会变成各阶段预算之和。回归测试应先填满队列、延迟释放 admission，再断言整个请求仍在原总预算到期时失败，而不是只验证 channel 确实有界。

<a id="exp-032"></a>

## 并发审查身份下先拉线程表再决定发布

- `validated_at: 2026-10-16`、`validated_ref: oceanbase/powercontext PR #2004`（我的回复 4292580623 与另一身份的 4292583551 相隔 20 秒）。
- 现象：同一轮审查可能有多个身份（本机 `AlexStocks` 与另一账号 `hidb4ai`）在并行跑同一批 PR，同一 PR 上会出现相邻分钟内新增的同根因线程。
- 处理：发布前与收尾前各拉一次 `reviewThreads(first:50)`，按 `path` + 评论 id 判重；已有同根因线程时只在既有线程内补充证据，或用自己的线程做「范围边界 + 交叉引用」，不再新开同内容评论。同时把并发身份的线程计入 PR 的未解决清单，避免把「已覆盖」误判为「无人提出」。

<a id="exp-043"></a>

## 用「事件同步」替换定时等待后，兜底仍由被测进程自身的请求超时决定

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2051`（head `d8ec3149`，base `f2808fb4`）、`applies_to: 修复时间敏感测试抖动、用事件/回调替换 sleep 一类改动`、`recheck_when: 被测代码的请求级超时或 hook 预算变更`。
- 判定顺序：① 找出被挂起的那个请求在**被测进程**里的超时（本例 `transport.mjs` 的 `REQUEST_TIMEOUT_MS = 1000`，逐请求 `AbortSignal.timeout`），而不是夹具自己写的兜底定时器（本例 10s 定时器在失败用例里根本没机会触发，用例 1.5s 就结束了）；② 确认超时后被测代码是否继续推进（本例 prepare 失败只写 stage，capture 照常执行）——如果继续，顺序断言仍会退化成"谁先到谁拿 position"；③ 把结论写成"窗口从 A 收窄到 B"，不要写成"已消除抖动"。
- 复现手法：让**两个并发进程里的一个**慢下来（按"首个创建 marker 文件的进程"识别先启动者），而不是等量延迟两者。等量延迟会保持相对顺序从而假通过，只有非对称停顿才暴露残留窗口。探针 `oceanbase-powercontext-pr-2051/probes/slow-newer-hook.mjs`（0 ms pass / 1200 ms fail，签名与原始抖动同为 `2 !== 1`）。
- 定级口径：事件驱动改造对等量变慢是严格改善（base 900 ms 等量延迟必红、head 2/2 绿），残留仅在非对称停顿超过被测超时时出现 ⇒ 按 P2 提"兜底说明不成立 + 失败不可诊断"，不按"抖动未修复"提。

<a id="exp-045"></a>

## 进程组 kill ≠ 覆盖 reader join：POSIX 子进程监督的 deadline 会被 `setsid` 后代绕过

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2056`（head `d46de401`，文件 `desktop/src-tauri/src/diagnostic_process_macos.rs`）、`toolchain: WSL Ubuntu / Python 3.14（语义模型探针，非 Rust 执行）`、`applies_to: 以 `process_group(0)` + `kill(-pgid)` + 读线程 join 实现"超时/取消必须清理后代"的 POSIX 子进程监督`、`recheck_when: 改为 cgroup/Job 类不可逃逸的归属、或 join 侧引入截止时间`。
- 现象：`try_wait` 拿到超时后 `kill(-pgid, SIGKILL)` 只杀同组成员。后代若自己 `setsid`（或 `daemon(3)`）就脱离该组，却仍持有继承来的 stdout/stderr 写端，于是 `read()` 永远等不到 EOF，`JoinHandle::join()` 无限阻塞。`Timeout` 已算出但函数不返回：唯一的 semaphore permit 与 `spawn_blocking` 线程被永久占用，后续调用只能拿到 `Busy`。
- 判据（三问）：① 清理手段的归属粒度是"进程组/会话"还是"不可逃逸的容器"（Windows Job 对象子进程无法自行逃离，所以同一份逻辑在 Windows 侧没有该窗口）；② 管道读端是否由被清理对象继承并可能被脱离者持有；③ 读线程的等待是否有自己的截止时间——`join()` 语义上是无界的，deadline 只覆盖主循环。
- 复现手法：探针按被测函数的**精确顺序**建模（`process_group=0` → 线程 read 到 EOF → 短 deadline → `killpg(SIGKILL)` → 无超时 join），再跑对照组（launcher 不 `setsid`）。对照组必须 finish，实验组必须不 finish，两者合起来才排除"本来就永远等不到 EOF"。实例 `oceanbase-powercontext-pr-2056/probes/probe_group_escape.py` + `probe_group_control.py`。
- 定级口径：launcher 是用户显式注册的本地可执行文件（已声明"必须信任"），因此触发需要该 launcher 后台化并保留 stdout ⇒ 按 P2 提"deadline 覆盖不完整 + permit 泄漏"，不按"任意命令可挂死应用"提。
- 修复方向：group kill 之后按剩余预算轮询 `JoinHandle::is_finished()`，未结束就 detach 并返回超时；或对读端设非阻塞/读超时。

<a id="exp-049"></a>

## job 级 conclusion 会掩盖 step 级超时，且超时会让同 job 后续 step 被 skip

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2031`（head `b0e379f6`）、`applies_to: 需要判断「本 PR 是否让某个 CI job 变红」的审查，尤其是新增较重的 e2e/集成用例`、`recheck_when: workflow 调整 step 拆分或 `timeout-minutes``。
- 只看 `check-runs.conclusion=failure` 与 job 日志尾部常常没有信息量：日志可能只写 `The action 'X' has timed out after 5 minutes`，真正的信号是**每个 step 的起止时间**。取法：`gh api repos/<o>/<r>/actions/jobs/<job_id> --jq '.steps[] | "\(.number) \(.name) \(.conclusion) \(.started_at) -> \(.completed_at)"'`。
- 归因三步：① 同一 head 的其他版本/平台是否同 step 绿（本例 3.11 同 step 88 s success，3.14 超时）；② 上一 head 与 base 的同 step 耗时（本例上一 head 41 s）；③ 该 step 在本次提交里的 diff 面是否只有被测新增用例（本例 `2fef5fab...b0e379f6` 落在该 step 的只有新增的那个 e2e）。三条合起来才把「超时」钉到具体用例上。
- 附带后果要写进 Finding：超时步骤之后的 step 是 `skipped` 而不是 `failure`，也就是说该 job 里后续的验收（本例 unified migrations）**在本 head 上从未执行**，不能用「另一个 job 绿」替代。
- 定级口径：让一个验收 job 从绿变超时、并把后续验收整段跳过，按 P1；若只是耗时上升但仍在预算内，按 P2 并给出实测数字。

<a id="exp-053"></a>

## 复核第三方 open 线程是否已修：同进程 A/B 跑两版实现，别读 head 源码推断

- `validated_at: 2026-10-20`、`validated_ref: oceanbase/powercontext PR #2089`（head `cd12b639`，对照 `39585c6f`，文件 `src/powercontext/builtin/artifacts/topic_memory/admission.py`）、`applies_to: 判断 hireview001 / hidb4ai / Copilot 等第三方未解决线程在后续 head 上是否已闭合，尤其是新增的启发式校验模块`、`recheck_when: 方法类，长期有效`。
- 取旧版不用 checkout：共享裸克隆 `git --git-dir=<repo.git> cat-file -p <ref>:<path> > evidence/<name>-<ref>.py`，再用 `importlib.util.spec_from_file_location` 与 head 版本同进程加载，对同一组输入跑对照。输出写成 `pre → X / head → Y` 两列，直接就是回复线程时最有力的证据形态。
- 本轮实际拦下一次误判：`_coordination_only()` 里 `if text and not _CHINESE_COORDINATION_WORD.sub("", text):` 被我读成"英文文本命中早退"，推断英文模板检测整体失效；实际条件是"剥离后为空才进分支"，英文恰好跳过该分支走词表路径。**只靠读条件表达式判断覆盖范围，在否定/空值双重嵌套时必错**，跑一次最小输入（一条英文模板 + 一条中文模板）即可证伪。
- 对照必须带反向用例：确认"该拒绝的仍拒绝"。本例同进程同时跑"仅单一引用的分源引用仍拒绝"与"编号占位仍 `invalid_topic_placeholder`"，否则无法排除"把守卫整体放宽"这种伪修复。
- 平台细节：`core.autocrlf=true` 下旧版文件是 CRLF、head 解压产物可能是 LF，直接 `diff -u` 会整文件全红；用 `diff -u --strip-trailing-cr`，或先统一行尾再看真实 hunk。

<a id="exp-065"></a>

## 夹具的父进程超时大于子进程内部超时：失败只剩阶段名，拿不到根因

- `validated_at: 2026-10-22`、`validated_ref: oceanbase/powercontext PR #2031`（head `d8da2bca`，`tests/e2e/test_database_bootstrap.py::run_seekdb_scenario` 的 `subprocess.run(timeout=90)` 对 `tests/fixtures/seekdb_legacy_choice.py` 的 `asyncio.timeout(60)`）、`applies_to: 任何"父测试 spawn 子进程 + 子进程自带 deadline"的夹具`、`recheck_when: 方法类，长期有效`。
- 现象：父进程给的预算（90 s）大于子进程自己的预算（60 s），于是子进程永远先超时；父进程只会读到子进程的 `AssertionError: <阶段名>` 与前缀 stderr，报错里没有"哪一步超预算"的结论，审阅者需要自己去读子进程的 faulthandler 栈与引擎侧 `SHOW FULL PROCESSLIST` 才能定位。
- 判据：读夹具时先对齐三层预算——CI 步骤 `timeout-minutes`、父测试 `subprocess.run(timeout=)`、子进程 `asyncio.timeout()`。三层必须单调递减（步骤 > 父 > 子），否则外层超时永不触发，失败信息退化。本例还叠加了 `-o faulthandler_timeout=60`，日志里出现两个不同来源的 `Timeout (0:01:00)` / `Timeout (0:00:45)`，容易误读成同一件事。
- 定位手法：失败时让子进程把当前阶段名打 stderr（本例 `stage()`），再加上引擎侧快照（`SHOW FULL PROCESSLIST`、`__all_virtual_lock_wait_stat`）。本例据此判定"`CREATE TABLE` 已 `Time=22` 且 `ACTIVE`、无锁等待" ⇒ 是重复全量建表的真实耗时，而不是死锁。
- 结论写法：不要只写"超时/抖动"，要给出"哪个阶段 + 该阶段在引擎侧做什么 + 同一 head 另一解释器的耗时"，否则作者只能提高超时。

<a id="exp-066"></a>

## 对端进程被终止时 socket 读可能抛 `ConnectionResetError`，"空字节 = 正常关闭"只在 POSIX 成立

- `validated_at: 2026-10-22`、`validated_ref: oceanbase/powercontext PR #2196`（head `717c8e5c`，`src/powercontext/server/_log_transport.py::_read`）、`applies_to: socketpair / unix socket 多路复用代码把"recv 返回空"当作唯一正常关闭形态的地方`、`recheck_when: 方法类，长期有效`。
- 现象：Windows 上对端进程被 `terminate()`（`TerminateProcess`）后，接收侧 `recv()` 抛 `ConnectionResetError [WinError 10054]`，而 Linux 上返回 `b""`。如果 `except Exception` 分支统一调用失败回调，就会把**正常终止**记成"投递失败"：本例里 `_LOG_FAILURES` 递增、`telemetry_log_records_dropped` 增长、并写出 `observability.log_failed`。
- 判据：管道/套接字的关闭分支必须同时处理 ① `data == b""`（EOF）② `ConnectionResetError` / `ConnectionAbortedError`（对端强制关闭）。只有 `_decode` 失败与通道注册失败才算真正的投递失败。
- 探针写法：把 `_read` 整体替换成"打印异常类型与 payload"的版本再跑同一个场景（本例 `probes/probe_terminated_channel.py`），输出形如 `[('recv-raised','ConnectionResetError','[WinError 10054] …'), ('clean-eof',)]`，比读源码推断可靠。子进程用 `multiprocessing` spawn 时，探针脚本必须带 `if __name__ == "__main__"` 守卫，否则子进程会重跑整个探针、输出两遍互相污染。
- 覆盖陷阱：同一 PR 的用例跑在 `tests (x, e2e)`（ubuntu）上时全绿，`windows-unit-portability` 又不跑该文件 ⇒ 平台差异只能靠本地 Windows 复现。报告里要写"CI 在当前 head 不暴露"，而不是"CI 全绿所以没问题"。

<a id="exp-079"></a>

## 「共享截止时间」替换「逐次超时」后，回退日志的词表还在报对方的错

**现象**：把 N 次调用的独立超时改成「一次总预算、每次只等剩余时间」后，剩余时间为 0 的调用会立刻抛 `TimeoutError`，
而被测代码的回退分类器只按异常类型选词（`TimeoutError → inference_timeout`）⇒ 第 2..N 次调用一次都没等，却全部记成
「provider 超时」。行为是对的（预算不超），但 `error_code` / `reason` 把「自己没等」说成「对方慢」。

**判据**（改超时语义的 PR 必查三处）：

1. 读回退/降级分支的取词依据：是按异常类型、按剩余时间，还是按「本次是否真的进入等待」。
2. 用探针把每次实际等待记下来，与事件流对齐：让桩每次 `sleep(远超预算)` 并记录 `finally` 里的真实等待，同时挂 logging handler 收
   `error_code`。实测形态：`waits=[0.2012, 0.0001, 0.0]` 对应三条 `error_code=inference_timeout`。
3. 看上游用例能不能区分两种成因：`sum(waits) <= budget * 1.5` 这类断言在「预算被前一次吃掉」和「provider 真慢」下都成立，
   必须补「后几次不进入等待」的断言，否则新语义没有回归保护。

**易误判的反面**：`asyncio.timeout(0)` 不是「无超时」（`None` 才是），确实是下一次 await 即刻取消；所以「0 被当无超时」的假设要先用
探针否掉，再决定问题落在行为还是词表。

关键词：`validated_at: 2026-10-25`、`validated_ref: PR #2231 head ddc14b0bad7a3dae70618ae72c4ac6e8de45420e`
（`src/powercontext/builtin/runtime/application.py:1783` `_remaining_seconds`）、`applies_to: 把 per-call timeout 改成共享 deadline 的改动`、
`recheck_when: 回退词表引入「预算耗尽」等独立取值后`。

<a id="exp-108"></a>

## 读取 `/proc/<pid>/stat` 判活性：进程在 open 与 read 之间退出抛的是 `ProcessLookupError`（ESRCH），不是 `FileNotFoundError`

**现象**：以 `Path(f"/proc/{pid}/stat").read_text()` 探测进程存活，只捕获 `FileNotFoundError` 时，偶发抛
`ProcessLookupError`（`OSError` errno 3 / ESRCH），在并行测试里表现为「同一用例偶发红」。

**实测（2026-11-06，WSL/Linux）**：先 `open('/proc/<pid>/stat')` 拿到 fd，再 `SIGKILL` 该子进程并 `wait()`，之后连续三次
`os.read(fd)` 全部抛 `ProcessLookupError`；用 `Path.read_text()` 复现同样结果。也就是说 open 成功、read 时任务已消失
就会得到 ESRCH，而不是 EOF 或 ENOENT。

**判据与写法**：
- 只判「进程在不在」：捕获 `(FileNotFoundError, ProcessLookupError)` 两个，别用裸 `OSError`——后者会把 EACCES/EMFILE/EIO
  一起当成「进程已消失」，让「没有残留进程」这类断言静默通过。
- 想去重一份现成写法，可参考 powercontext 的 `src/powercontext/source_management/{background,durable}.py`。
- 复现脚本很短（`open` → `kill` → `wait` → `read`），比读内核文档快，也比在 CI 里等偶发可靠。

**归类**：这类失败是环境/内核接口语义，不是被测代码缺陷；但若被测实现捕获范围过窄，就属于真实缺陷（测试或产品皆然）。

<a id="exp-115"></a>

## 把 helper 换成手写查询时，要逐条清点 helper 的副作用（锁、排序、上限）

现象：为解除对某张新表的依赖，把 `await artifacts.latest(conn, ..., for_update=for_update)` 换成直接
`select(...).select_from(heads.outerjoin(bodies, ...))`。读路径确实不再碰新表了，但 `for_update=True` 原本走的是
`_find_head(..., for_update=True)` → `SELECT ... FOR UPDATE` 锁 head 行；手写查询没有 `with_for_update()`，
参数只剩对 governance/state 行的锁，head 行静默失去互斥。

判据：替换 helper 时列出它除返回值之外的全部副作用（加锁、排序、limit、错误类型、缓存），逐条对照新实现。
若同一文件里另一条路径仍在显式加锁（本次 `rebuild_atomic_memory_projection` 仍 `artifacts.lock_heads(...)`），
说明该锁仍被视为必要手段，缺失即是回归而非"读路径简化"。同时看调用方是否已有并发保护：
本次 `rebuild_atomic_memory_current` 不要求 `maintenance_confirmed`，`publisher.publish` 也没有 revision 守卫，
"读到 R 后 head 前进到 R+1"的窗口会以旧 revision 覆盖投影，只能靠事后的 `verify_atomic_memory_current` 暴露。

相关：`review.md` `R06A`（测试真实性：需要一个并发交错的用例才能证明锁有效）。

关键词：`validated_at: 2026-11-07`、`validated_ref: oceanbase/powercontext #2296 head fe761522（atomic_memory_rebuild.py:286）`、`applies_to: 任何"为绕开依赖/兼容问题而内联手写 SQL 或查询构造"的改动`、`recheck_when: 该路径重新引入 helper，或投影写入方增加 revision 守卫`。

<a id="exp-130"></a>

## 「尝试次数减免」类改动（`attempts - 1` 这种）要按四点核验，否则减免可能从未生效（2026-11-13 实测 #2597）

**现象**：`fix(topic-memory): stop head conflicts from spending window budget` 把
`attempts=row["attempts"]+1` 改成 `attempts=_spent_attempts(row)+1`，而
`_spent_attempts = attempts - (last_error_code == "head_conflict")`。这类「减免计数」看起来只是表达式改写，
但任何一环接错都会静默退化成「什么都没变」，且现有测试很可能仍然全绿。

**四点核验（缺一即可能无效）**
1. **标记列真的存在**：`last_error_code` 必须在 `TOPIC_MEMORY_WORK_BUDGETS_TABLE` 的定义里；同名列在别的表
   （`pc_skill_publications` 等）出现会让人误判。`row.get()` 取不到列时返回 `None`，表达式恒为假、不报错。
2. **写入值与比较值同源**：写入侧是 `completion.outcome.value`，比较侧是常量 `"head_conflict"`；必须回到枚举
   定义确认 `HEAD_CONFLICT = "head_conflict"`，不能按枚举名或 `observed_outcome`（本例被映射成 `"conflict"`）推断。
3. **减免只发生一次**：`begin()` 在同一事务里把 `last_error_code` 置 `None`，否则同一次冲突会被反复减免，
   计数器永久停住。
4. **终止边界转移到了谁身上**：减免让 `MAX_..._ATTEMPTS` 不再约束该路径，必须能指出另一组真实 ceiling
   （本例 request / token 预算 512 / 64M，每次尝试至少记 1 个 request）并在测试里跑到它。

**证据强度**：本例用「5 个单测 + 1 个 e2e 实测通过」+「`managed_digest` 复算等于声明的 `persistence_sha256`」支撑；
单测断言 `row["attempts"] == 1` 在重复冲突后仍成立、以及「永不稳定的 head 最终以
`window_provider_budget_exceeded` 停下」，这两条才是能检出原缺陷的反证（`R06A`），只断言「最终发布成功」不够。

**关键词**：`validated_at: 2026-11-13`、`validated_ref: oceanbase/powercontext #2597 head 3b2dd045`、
`applies_to: 重试/预算/配额计数器上的「某种失败不计入」类改动`、
`recheck_when: 该表列定义、`MAX_TOPIC_MEMORY_WORK_*` 常量或 `ArtifactProcessingWorkerOutcome` 取值变更`。

<a id="exp-158"></a>

## `gh api -f body=@file` 发的是字面量 `@file`，回复与 PATCH 必须用 `--input` 或 `-F`（2026-11-25 实测 oceanbase/powercontext #2816）

- 现象：`gh api repos/{o}/{r}/pulls/{n}/comments/{id}/replies -f body=@reply.json` 返回 200，评论也确实落库了，
  但正文是字符串 `@reply.json`。`-f`（raw field）不做文件展开，只有 `-F`（typed field）才支持 `@file`。
- 判据：任何带 `body` 的写调用，落库后必须回读 `body` 长度与首行；只看 HTTP 200 或 `html_url` 会把空壳评论当成发布成功。
- 处理：正文错误但已落库时按 R11 原地 `PATCH .../pulls/comments/{id}`（本轮 4690060889 → 正文 1266 字符），
  不新建第二条；草稿 JSON 只用 `{"body": "..."}` 走 `--input`，避免 `-f/-F` 的展开差异。

`validated_at: 2026-11-25`、`validated_ref: #2816 thread reply 4690060889`、
`applies_to: gh CLI 2.x 的任意 review 评论写入`、`recheck_when: gh CLI 改变 -f 对 @file 的展开语义`。
