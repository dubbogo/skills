<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# AlexStocks/getty Review 补充规则

## Session 关闭、Reset 与 goroutine 完成语义

- `validated_at`: 2026-07-31
- `validated_ref`: `master@33d84ce338b4403e27073b79d9a54fcdc5c2337d`, PR #94 Head `f61e2cbd11b16a031984a8df571cf6716c7bdf35`, 历史提交 `89139c56a97760e1c90d169ccba6220198c52b8b`
- `applies_to`: `transport/session.go` 的 `run`、`handlePackage`、`stop`、`Close`、`Reset` 生命周期
- `recheck_when`: `Session.Close` 的阻塞契约、读 goroutine 数量、`Reset` 复用语义或 `grNum` 类型发生变化

审查新增的 session 完成同步时，先确认历史契约：提交 `89139c56` 明确删除 `Session.Close()` 中的 `WaitGroup.Wait()`，改为非阻塞关闭并仅用原子 `grNum` 观测 goroutine 数量；当前 `grNum` 为 `go.uber.org/atomic.Int32`。若要恢复等待语义，必须给出可复现需求，并覆盖尚未启动读 goroutine、正常退出、异常退出、并发或重复 `Close`、以及 `Reset` 后的状态重建。

私有完成 channel 必须同时具备明确消费者和完整生产者生命周期。只有初始化与 `close(channel)`、仓库内没有接收或 `select` 分支时，该 channel 不产生协调效果；不要把“计数归零时关闭”本身视为关闭等待已经实现。`Reset()` 使用结构体整体覆盖，新增长生命周期字段时还要核对 Reset 调用方和复用契约，不能只根据字段遗漏机械判断可达 panic。

当前公开测试 `TestUDPClient` 在 `Client.Close()` 返回后立即调用 `Session.Reset()`，但 `Session.Close()` 不等待读 goroutine，`stop()` 又异步执行 close callbacks。`go test -race ./transport -run '^TestUDPClient$' -count=1` 可稳定报告 `Reset()` 与 `handlePackage`、`invokeCloseCallbacks`、属性读取的竞态。审查 `Reset` 或关闭复用时，必须要求一个覆盖读 goroutine、回调和重连属性访问的完成屏障；普通 `go test` 通过不能替代 race 验证。

## Connection 原子字段与值接收者

- `validated_at`: 2026-07-31
- `validated_ref`: `master@33d84ce338b4403e27073b79d9a54fcdc5c2337d`
- `applies_to`: `transport/connection.go` 的 `gettyConn` 及其嵌入类型，`transport/session.go` 的关闭路径
- `toolchain`: WSL `go1.25.1 linux/amd64`
- `recheck_when`: `gettyConn` 字段、timeout accessor 接收者或 Session 关闭顺序发生变化

`gettyConn` 含多个 `go.uber.org/atomic` 字段。访问器不得使用值接收者复制整个结构；即使目标字段自身通过原子 Load 读取，复制结构时仍会并发读取其他正在更新的原子字段。当前 `ReadTimeout`、`WriteTimeout` 的值接收者会在 `Session.Close()` 与网络读 goroutine并发时触发 race，`go test -race ./transport -run '^TestNewWSClient$' -count=1` 可稳定复现。审查修复时应核对所有 `gettyConn` 方法接收者，并保留 TCP 与 WebSocket 关闭路径的 race 回归测试。

## 运行期 Codec 切换与活跃 I/O

- `validated_at`: 2026-08-16
- `validated_ref`: `master@cc9909dc9e0aab1307f553bc2a3d8400161be4e2`, PR #111 Head `604c153af9405b7888c35f1ff2b11d09a8c395c3`
- `applies_to`: `transport/connection.go` 的 `gettyTCPConn.SetCompressType`、`recv`、`Send` 及 codec reader/writer 状态
- `toolchain`: WSL `go1.25.1 linux/amd64`
- `recheck_when`: codec 安装时机、Session 启动契约或 reader/writer 同步方式发生变化

`SetCompressType` 是公开的 Connection/Session 操作，不能默认只在 I/O goroutine 启动前调用。并发执行 `SetCompressType(CompressSnappy)` 与 `Send([]byte)` 时，race detector 会报告 codec writer 的发布与读取竞态，并可能让发送进入尚未同步发布或已经被替换的 writer。审查 codec 状态变更时必须要求统一的同步/状态机，或在 Session 启动后明确拒绝切换；回归测试应通过公开调用并发驱动实际 `Send`/`recv`，不能只检查 `codecEnabled` 字段。

## PR head 落后 master 时的审查基准

- `validated_at`: 2026-09-24
- `validated_ref`: `baseRefOid 4207b65402db7688eccafb1cca1a0c52cc11f15c`，PR #144 Head `f31b13e25e60fa5f28ccf925911f5e2fab8bb911`，其 merge-base 为 `c216553ab185d6d89af8c8f72e4c8aa18e852b82`；复检时 master 已到 `344cd3baed9876a85edfaadf7e4f5f51837c7978`
- `applies_to`: 本仓库所有 PR 的取证阶段（Diff 基准、Base/Head 对照、测试归因）
- `recheck_when`: 每次审查前重算 `git merge-base <baseRefOid> <headRefOid>`；只要 merge-base ≠ baseRefOid 即适用本条

PR head 分支可能**落后**当前 base：`#144` 的分支基于 `c216553a`，而 `baseRefOid` 已推进到 `4207b654`（master 已合入 PR #141 的 `session.Send` packetLock 与 #112 锁修复）。此时 `git diff <base>..<head>` 会把 master 已合入的改动显示成本 PR 的**伪回退**（实测多出 `transport/session.go -81`、`transport/session_test.go -249`），与 GitHub `changedFiles` 对不上。审查基准必须用 `git diff <merge-base>..<head>` 或 `gh pr diff`。由此产生的测试失败（该分支上 `session.Conn()`/`gettyConn()` 是无锁旧版）属「Base 已修 + 分支未同步」，**不得归责该 PR**；做 base/head 对照时也须以 merge-base 为起点。

## ws 收发两侧尺寸约束不对称

- `validated_at`: 2026-10-22（初版 2026-09-24）
- `validated_ref`: PR #146 Head `e8ed0247b2b51651cb8eb697a957d6af7b0bbcbf`（初版为 `bde1f89b`），base `89da27f4`（初版为 `4207b654`）；gorilla `readLength > readLimit → CloseMessageTooBig + ErrReadLimit`
- `applies_to`: `transport/session.go` 的 `WriteBytes`/`WriteBytesArray`/`WritePkg`/`Send` ws 分支与 `websocketPayloadTooLarge`，`transport/server.go`、`transport/client.go` 的 `SetReadLimit` 调用点
- `recheck_when`: ws 写入分片策略、`maxMsgLen` 校验位置或 gorilla 版本发生变化

PR #146 之后 ws 上 `WriteBytes` 整包作为**单条**消息、`WriteBytesArray` 每包一条消息，**写入侧不再分片**；而接收侧 gorilla `SetReadLimit(maxMsgLen)` 是**按消息**生效的硬限制，超限主动回 `Close(MessageTooBig)` 并令连接失败。二者叠加使「`maxPacketLen`(16 KiB) ≤ 对端 `maxMsgLen` < 载荷」这类旧配置从可用变为**整条连接被断**。审查任何 ws 发送语义变更时必须同时核对：① 写入侧是否校验 `maxMsgLen`（`session.go` 的 `WriteBytes`/`WriteBytesArray`）；② read limit 的施加时机（`#144` 后 client 侧移到 `newSession` 之后、server 侧本就如此）；③ 测试用的 ws 对端是否**带 read limit**——PR 自带测试用裸 gorilla（无 read limit），会掩盖该约束。

**2026-10-22 补充（Head `e8ed0247`）**：写入侧不再是「无上限」。新增的 `websocketPayloadTooLarge` 直接复用 `s.maxMsgLen` 作写侧闸门，形成不对称的**反向**问题——见下条「接收侧上限被复用为写侧闸门」。核对本条时不要停在「写侧没校验」，要判断写侧校验的**阈值来源**是否与语义匹配。

## 接收侧上限被复用为写侧闸门

- `validated_at`: 2026-10-22
- `validated_ref`: PR #146 Head `e8ed0247b2b51651cb8eb697a957d6af7b0bbcbf`，base `89da27f4`；`maxReadBufLen = 4*1024`（`session.go:50`）是 `newSession` 的默认 `maxMsgLen`（`session.go:219`）
- `applies_to`: `transport/session.go` 的 `websocketPayloadTooLarge` 及所有 `WriteBytes`/`WriteBytesArray`/`WritePkg`/`Send` 的 `[]byte` 分支
- `toolchain`: WSL `go1.27.0 linux/amd64`
- `recheck_when`: 新增任何写侧尺寸检查、`SetMaxMsgLen` 语义变更，或 `maxMsgLen` 默认值调整

`maxMsgLen` 的文档语义是接收方向（`SetMaxMsgLen set maximum package length of every package in OnMessage(@pkgs)`），默认 4 KiB。把它当作写侧阈值会让「发送端 `maxMsgLen` < 载荷」的合法写入在本地直接报错，而 base 行为是成功发送（旧版按 16 KiB 分片）。探针 base/HEAD 对照（未调用 `SetMaxMsgLen`）：4096 两边成功；8192 base `n=8192` 对端收全 / HEAD `n=0` 报 `above maxMsgLen(4096)`；20480 base 对端收到首片 16384 / HEAD 同样 `n=0`。

审查此类闸门的三条硬性要求：

1. **阈值语义**必须是「对端能收多大」，不能是本端能收多大；若确要复用，必须新增「是否被显式设置过」的标记，默认不检查。
2. **必须做 base/HEAD 双向对照探针**。只跑 HEAD 会看到「超限被拒」这个看似合理的新行为，无法发现「原本成功」的回归。
3. **PR 自带测试若需要先 `SetMaxMsgLen(len(pkg))` 才能通过，这本身就是默认值冲突的信号**，不要把它当作测试写法问题一带而过。

## Go 1.25+ 的 TLS 默认下限使显式 MinVersion 成为 no-op

- `validated_at`: 2026-10-22
- `validated_ref`: PR #145 Head `f7fee17aa6124c6600901106a8814a6b5d48a291`，`transport/tls.go:68`；`$GOROOT/src/crypto/tls/common.go:1239`
- `applies_to`: `transport/tls.go` 的 `ServerTlsConfigBuilder`/`ClientTlsConfigBuilder` 及 `server.go` 自建的 `tls.Config`
- `toolchain`: WSL `go1.27.0 linux/amd64`（仓库 `go.mod` 要求 `go 1.25`）
- `recheck_when`: `go.mod` 的 go 指令降到 1.22 以下，或仓库开始支持更早工具链

`crypto/tls` 的 `Config.supportedVersions` 在 `MinVersion == 0` 时直接跳过 `v < VersionTLS12`，因此在 Go 1.25+ 上显式写 `MinVersion: tls.VersionTLS12` **不改变任何握手结果**。探针实测（`MinVersion=0` vs `MinVersion=TLS12`）：TLS 1.0/1.1 两种配置都 `protocol version not supported`，TLS 1.2 都成功协商 `0x0303`，完全一致。

审查此类「安全加固」改动的判据：

1. 不要接受「加了 MinVersion 所以更安全」的叙述，先查 `go.mod` 的 go 指令与 `crypto/tls` 的默认下限逻辑。
2. 若改动是 no-op，则 `change_log.md` 里对应的 Breaking 条目（「TLS 1.0/1.1 客户端不再能连接」）会给升级方制造不存在的迁移负担，属于**文档失真**，同样要提。
3. 「`every server`」这类全量表述必须逐个核对：WSS 服务端在 `runWSSEventLoop` 里自建 `tls.Config`（`server.go:541-546`），根本没设该字段。
4. 真正有效的加固是 `ClientAuth` 由 `RequireAnyClientCert` 改为 `RequireAndVerifyClientCert`——这一项才是真破坏性变更，验证要用握手级用例而非只断言配置字段。

## UDP 回调错误后的端点状态与 IsClosed 不一致

- `validated_at`: 2026-10-22
- `validated_ref`: PR #145 Head `f7fee17aa6124c6600901106a8814a6b5d48a291`，`transport/server.go:423-430`
- `applies_to`: `transport/server.go` 的 `runUDPEventLoop`、`callNewSession`，以及 `IsClosed()`/`stop()` 的状态维护
- `toolchain`: WSL `go1.27.0 linux/amd64`
- `recheck_when`: `runUDPEventLoop` 的错误处理路径、`s.done` 的关闭时机或 `IsClosed()` 的判据发生变化

把 `panic` 改成 `log.Errorf + conn.Close() + return` 消除了进程崩溃，但引入了一个**状态不一致**：`conn` 是 endpoint 共享的 UDP socket（`s.pktListener.(*net.UDPConn)`），关掉它等于让端点停止服务；而 `return` 只退出 goroutine，没有调用 `s.stop()`，`s.done` 未关闭，`IsClosed()` 仍返回 false，错误也没交给调用方（UDP 的 `RunEventLoop` 只起协程、本身立即返回）。探针实测：回调报错后 `IsClosed()=false`、端点写入报 `use of closed network connection`、peer 收到 `connection refused`，直到显式 `Close()` 才变 true。

审查「panic 改日志」类改动时，除确认不再崩溃，还必须追问三件事：① 关掉的资源是否是共享的（端点级 vs 连接级）；② 退出 goroutine 前有没有把关闭状态写回 `s.done`/`IsClosed()`；③ 注释里的「继续服务」与实际 `return` 是否一致——本例注释写 `keeps serving`、实现是停止服务，随附测试的注释同样写反了，且测试只断言 `IsClosed()`，恰好绕过了这个不一致。

## PR 描述里的「special notes」可能写给旧 base，逐条核对再采信

- `validated_at`: 2026-10-27
- `validated_ref`: AlexStocks/getty PR #161（head `21b8ecf8d1246bba11b1c1f3149bde73c51ab2b4`，base `a6d8e699` = `Merge pull request #159 ... fix/issue-153-session-reset-lifecycle`）
- `applies_to`: 任何 PR 描述里带「deliberately standalone / when X is rebased on top / this PR is before Y」的说明
- `recheck_when`: 引用 PR 描述做判断前

描述里写「本 PR 刻意基于 callbackDepth 改动之前，将来 rebase 时 `invokeEventCallback` 必须改成 `s.invokeCallback(f)`，而不是直接调 `f()`」——但 base 就是那次改动的合并提交，`callbackDepth`（`session.go:174`）、`invokeCallback`（`session.go:383`）都在，新函数第 948 行本来就是 `s.invokeCallback(f)`。同一份描述还写「`handlePackage` 现在改为 defer `s.gc()`」，而 base 的 `handlePackage` 第一行（`session.go:1106`）早就 `defer s.gc()`，本 PR 没碰。

做法：拿到描述后，把每一句「现在/改为/新增」翻译成一个可 grep 的符号，然后 `git show <base>:<file> | grep` 一次。对不上就是描述过期（作者写给旧 base 忘了更新），要么要求作者改，要么自己在评审里写清实际状态——按过期描述读 diff，会把「本来就有」误判成「本次新增」，也会把评审注意力引到不存在的问题上。

## 「行为未改变」是断言，新可达路径会推翻它

- `validated_at`: 2026-10-27
- `validated_ref`: PR #161 `transport/session.go:989`（`ss.Close()`）；`client.go:438-439`（`connect()` 写 `sessionClientKey`/`ignoreReconnectKey`）、`session.go:1481-1485`（`stop()` 据此调 `clt.runReconnect()`）、`client.go:583-586`（连接成功即把 `reconnectAttempts` 归零）
- `applies_to`: 新增 `Close()`/`Reset()` 调用的改动，以及描述里出现「X behavior is not changed by this PR」的场景
- `recheck_when`: 有新路径能到达 `stop()` 时

描述写「OnCron panic 后的 client 重连行为未改变」。实际上改动前 cron panic 根本到不了 `stop()`：无任务池时 panic 冲出 timer wheel goroutine（base 子进程 `exit status 2`），有任务池时被 gost `GoSafely` 吞掉且不关闭会话。PR 新增的 `ss.Close()` 让重连路径第一次可达，而 `reConnect()` 在 `connect()` 成功时重置尝试计数、退避只在失败时生效——于是「cron 恒 panic」的 client 会以 cron 周期为单位无限重连，每轮 64KB 栈日志，且不向用户升级。

判据：先问「这条语句在改动前能否被执行到」。判「未改变」时，把新调用点（`Close`/`Reset`/`stop`）当作入口，沿已有的回调链走一遍，看是否首次触达某个既有分支（重连、goroutine 池回收、共享资源清理）。

## 偶发失败的测试，用「放大回调耗时」做确定性复现

- `validated_at`: 2026-10-27
- `validated_ref`: PR #161 `transport/session_event_panic_test.go:346-358`（`pooled-cron` 的 `want` 只允许 2 或 3 条事件）
- `applies_to`: 依赖「任务在某个周期内完成」的并发测试断言
- `recheck_when`: 同一个测试在不同机器上结论不一致时

同一条 `go test -race ./transport -run '^TestEventCallbackPanicContained$/^pooled-cron$' -count=10`：前一次审查 10/10 失败，我在本机 20 次（无 race）+ 10 次（`-race`）全过，CI 的 `Race` 作业也是绿的。重复跑只会在「偶发」和「不复现」之间来回摇摆。

确定性做法是改**唯一变量为回调耗时**：`delay=0/5ms/25ms` + `SetCronPeriod(10)`，实测 `count=1/1/3`。因为 `AddTaskAlways` 在池忙时另起 goroutine，回调耗时超过 tick 周期就必然叠加。这条证据同时说明断言错在把不成立的假设写成了契约，而不是机器太慢。

## 沙箱禁 loopback 时，先跑仓库既有的同类测试判断是环境还是代码

- `validated_at`: 2026-10-27
- `validated_ref`: 本机 `net.DialTimeout("tcp", 127.0.0.1:<随机端口>)` → `connectex: connection attempt failed`；`TestTCPClientOnOpenCloseKeepsPoolAtConfiguredSize` 在这里同样是 `got 0 sessions (0 live)`
- `applies_to`: 需要 client/server 端到端探针的评审
- `recheck_when`: 探针里出现「连接数为 0」「opens=0」这类空结果时

新写的 client 探针拿到 `opens=0` 时，不要先改探针。先跑仓库里已有的同类端到端测试：如果它在这个环境里也拿不到连接，就是环境限制（沙箱禁出站），不是探针写错。确认之后，把无法实测的结论明确标注为「源码级判断」，并列出判断依据的调用链，而不是含糊地说「经验证」。本条适用于所有 `127.0.0.1` 依赖。

## 关闭语义（linger）类修复必须覆盖全部 Connection 实现

- `validated_at`: 2026-11-21
- `validated_ref`: PR #175 Head `8b375fe632b03b68ba1587e0cbf8eb24094c95fc`，base `f310191d7ecf0b32bbcc6815d62bcc67c7018bb6`（`transport/session.go:1564-1569`、`transport/connection.go:1262-1271`）
- `applies_to`: `transport/session.go` 的 `gc()` linger 计算，以及任何往 `CloseConn(int)` 传秒数的改动
- `toolchain`: WSL `go1.27.0 linux/amd64`
- `recheck_when`: `gc()` 的连接类型分支、`gettyWSConn.CloseConn` 的 `SetLinger` 调用或 `SetWaitTime` 语义发生变化

`gc()` 把秒数取整改成 `lingerSeconds(wait)` 只加在非 WS 分支，WS 保留 base 的 `int(wait/time.Second)`，而 `gettyWSConn.CloseConn` 把这个值原样交给 `*net.TCPConn.SetLinger`——和 TCP 分支是同一个系统调用。探针（`httptest` WS 对端 + `newGettyWSConn` 包服务端 conn + 直接调 `gc()`，对端读裸 TCP）实测：`SetWaitTime(500ms)` → 对端读完 14 字节关闭帧后 `connection reset by peer`（3/3 复现）；`SetWaitTime(3s)` → `EOF`。WSS 走 `*tls.Conn` 的 `CloseWrite` 分支，不受影响。

判据：审查「优雅关闭 / linger / 半关闭」类修复时，先枚举 `Connection` 的全部实现（TCP、WS、WSS、UDP）各自怎么消费这个秒数，再看 PR 声称覆盖了哪几条。PR 描述里「special notes: 本改动只适用于 TCP，WS/WSS 仍用旧写法」属于**声明未覆盖范围**，不是需求闭合——issue 的验收条件若写成无条件的「不再出现 `SetLinger(0)`」，就要按所有传输逐条核对，并用 ws 侧探针给出实测结果，不要只跑 PR 自带的 TCP 用例。
