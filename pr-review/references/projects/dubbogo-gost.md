<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# dubbogo/gost Review 补充规则

## ZK 事件 State 语义：`StateConnected` 与 `StateSyncConnected` 不是同一层的东西

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155 Head `5adf2cef17306f8df54719b2709b518447f290cd`，base/merge-base `f6a75896b1832b994f59c59b8f5b447d8a8f7384`；依赖 `github.com/go-zookeeper/zk v1.0.4`
- `applies_to`: `database/kv/zk/client.go` 的 `DefaultHandler.HandleZkEvent`、`ZookeeperClient.RegisterEvent`/`UnregisterEvent`，以及任何在 `zk.Event.State` 上做分支的下游
- `recheck_when`: `go-zookeeper` 版本变化、`setState` 的产生点变化、`RegisterEvent` 是否仍拒绝空 path 变化

评审「handler 漏了某个 State」类改动时，必须先定位该 State 的**产生点**，不能只看常量表。go-zookeeper v1.0.4 里：

- `constants.go:74` `StateConnected = State(100)` 是**客户端合成**的会话状态，唯一产生点是 `conn.go:351` 的 `setState()`，发出的 `Event{Type: EventSession, State: state, Server: ...}` **没有 Path**（`conn.go:390` 在 TCP 拨通后触发）。
- `constants.go:68` `StateSyncConnected = State(3)` 是**服务端报文**里的 `KeeperState`，节点事件在 `conn.go:835-841` 直接取 `res.State` 透传。

后果：`HandleZkEvent` 里 `case zk.StateConnected:` 的 `strings.HasPrefix(event.Path, path)` 中 `event.Path` 恒为 `""`，而 `RegisterEvent` 拒绝空 path（registry 不可能有 `""`），所以该前缀派发分支**从未投递过任何事件**——`RegisterEvent` 在 master 上是完全空操作，从 `01d5bc0` 起一直如此。判断「这个分支是不是死的」时，用 `git log -L <start>,<end>:<file>` 追一次引入点，比推断可靠。

## 「本来该生效却死掉」的分支，修复等价于上线新功能

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155；下游 `apache/dubbo-go` `config_center/zookeeper/impl.go:100`、`metadata/report/zookeeper/report.go:242`、`remoting/zookeeper/listener.go:84`
- `applies_to`: gost 中所有对外暴露订阅/回调注册 API 的包
- `recheck_when`: 新增 `RegisterEvent` 类调用方，或既有调用方开始依赖回调

当 PR 修的是一个**从未生效**的注册路径时，release note 与灰度要求应等同「新增功能」而非「补一个边角状态」。审查时必须枚举修复后立刻变成活代码的下游调用点，并检查这些调用方的 handler 生产上是否被执行过——#155 合并后 dubbo-go 的配置中心与元数据上报两条链路的 `ExistsW` + `Get` + `DataChange` 逻辑会首次上线。

## go-zookeeper 的会话事件通道会静默丢弃，同步派发会把局部慢消费者放大成全局丢事件

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155；`github.com/go-zookeeper/zk v1.0.4` `conn.go:39` `eventChanSize = 6`、`conn.go:359-363` `sendEvent` 非阻塞丢弃
- `applies_to`: `database/kv/zk/client.go:278-286` 的派发循环（持 `RLock` 同步写订阅者通道）
- `recheck_when`: `HandleZkEvent` 的派发改为异步/分离锁，或 go-zookeeper 的 `eventChan` 容量与丢弃策略变化

`sendEvent` 是 `select { case c.eventChan <- evt: default: }`，`z.Session` 只有 6 个槽位，通道满即丢弃，不重试不告警。而 `HandleZkEvent` 是 `z.Session` 的唯一消费者，且派发时持 `eventRegistryLock.RLock()` 同步 `e <- event`。因此任一订阅者不排空会导致连锁：

1. `HandleZkEvent` 阻塞 → `z.Session` 6 槽填满 → 会话事件被库静默丢弃；
2. `StateDisconnected` 丢 → `valid` 不归零，`ZkConnValid()` 仍返回 true；`StateHasSession` 丢 → `reconnectCh` 不关闭，`HandleClientRestart` 不触发，重连后订阅不重挂；
3. `RegisterEvent`/`UnregisterEvent` 要写锁，被卡住的读者长期阻塞。

可复现探针：注册无缓冲且无人读的通道 + 一个应命中的通道，喂一条 `{EventNodeDataChanged, StateSyncConnected, Path}`，`HandleZkEvent` 不返回且另一订阅者收到 0 条。最小改法是 RLock 内只收集目标通道、解锁后再发送；彻底方案是每订阅者独立 goroutine + 有界队列。可达性取决于下游通道容量与消费耗时：dubbo-go 是 `make(chan zk.Event, 16)` 且每事件两次同步 RTT（`ExistsW` + `Get`），批量配置变更时容易打满。

## 手造 `zk.Event` 的单测只能证明 switch 分支存在

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155 `database/kv/zk/client_event_test.go:47`；可复用脚手架 `client_test.go:67` `testZkAddr`、`client_test.go:113` `verifyEventStateOrder`、`client_test.go:264` 被注释的 `verifyEventOrder`
- `applies_to`: `database/kv/zk` 包内所有基于事件状态/类型的回归测试
- `recheck_when`: 新增或修改 zk 事件相关断言

测试矩阵若同时遍历「不可能的 State/Path 组合」，会产出没有区分力的用例：`client_event_test.go` 的 `StateConnected` 三个子用例在修复前后**都通过**（回退 `client.go:277` 后只有 `StateSyncConnected` 三个失败），因为它们手造了库不会发出的 `StateConnected` + 非空 `Path`。审查时对每个子用例问一句「这个输入组合在线上可能出现吗」。

本仓库已有真实 ZK 集成脚手架（`testZkAddr` 在无 `ZK_ADDR` 时自动 skip），补一条「注册前缀 → `z.Create` → 断言收到 `State == StateSyncConnected`」的成本很低，能锁住线上契约；这正是 `client_test.go:264` 被注释掉时缺的那一环。

## 描述中的依赖 PR 状态必须现查

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155 描述引用 #156；#156 `state=closed, merged=false`（closed 2026-10-25T18:37Z），而 `./hash/consistent/` 在本 PR head 上连跑 5 次均 `ok`
- `applies_to`: 所有 PR 的「Special notes for your reviewer」段
- `recheck_when`: 每次审查

PR 描述里「CI 红是因为 master 既有问题 / 修正在另一个 PR」的说法会随时间失效。审查时必须查该依赖 PR 的 `merged` 字段，并在当前 head 上重跑被指为失败的包，而不是照抄描述——否则会把一个已关闭未合并的 PR 当作前提继续沿用。

## 不要把「被注释掉的断言」当成「能跑但被人为关掉的断言」

- `validated_at`: 2026-10-26
- `validated_ref`: PR #155 我在 review 中建议恢复 `client_test.go:264` 的 `// verifyEventOrder(...)`，PR #158 作者反驳成立；`git grep "func verifyEventOrder"` 在 `database/kv/zk/` 返回空，且 `Create`/`Delete` 不注册 watch
- `applies_to`: 所有「发现一行被注释的测试/断言」的场景
- `recheck_when`: 每次想建议恢复被注释代码前

看到被注释掉的断言时，先做两件事再下结论：① `git grep` 确认它引用的符号是否存在；② 确认它断言的行为在当前调用路径上是否真的会发生。`client_test.go:264` 那行是死引用（`verifyEventOrder` 根本不在包里）+ 不可能成立（`Create`/`Delete` 不装 watch，服务端不会下发 `EventNodeCreated`）。把「注释掉」反推成「曾经能跑、后来被人为关掉」是推测而非取证，会把错误建议写进 review。

## 锁内发送改为锁外发送，是死锁换 panic，契约必须写在导出 API 上

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 Head `fb18cc50255ba99befb510a31d6fecd5bdae8921`（`client.go:305-333` 新增 `snapshotPrefixEventChans`/`snapshotExactEventChans`），base `a236273a`
- `applies_to`: `database/kv/zk/client.go` 的 `HandleZkEvent`、`RegisterEvent`、`UnregisterEvent`
- `recheck_when`: 派发改成每订阅者 goroutine + 有界队列，或 `UnregisterEvent` 开始自己关闭通道

`RLock` 内发送改成「锁内快照、锁外发送」能消掉锁放大，但会打开一个新窗口：`UnregisterEvent` 只从 registry 删除、从不关闭通道，调用方若在其后 `close(ch)`，正在进行的发送会 panic。同一探针（同一通道注册到两个命中前缀 → snapshot 出现两次 → 收到第一条后反注册并 close）在两边的结果是：

- master `a236273a`：`unregister_completed=false (blocked on write lock)` —— 死锁；
- PR head：`unregister_completed=true` → `panic=send on closed channel`。

关键区别是这个 panic 发生在库自己的 handler goroutine 里，**调用方 `recover()` 不到**，整进程会挂；死锁只影响一个 goroutine。审查此类改动时必须确认契约写在哪：PR #158 把它写在未导出的 `snapshotPrefixEventChans` 注释里，而 `godoc` 上读者看到的是导出的 `UnregisterEvent`（注释只有一句 `unregisters zookeeper events`），等于没写。要求把「client 不关闭注册通道 / 调用方也不得 close」写进 `RegisterEvent`/`UnregisterEvent` 的 godoc，是这类 PR 最低限度的验收条件。

## `UnregisterEvent` 按下标前向删除，重复注册同一通道会越界 panic

- `validated_at`: 2026-10-26
- `validated_ref`: `client.go:360-364`（`for i, e := range infoList { if e == event { infoList = append(infoList[:i], infoList[i+1:]...) } }`），master `a236273a` 与 PR #158 head 相同，非本 PR 引入
- `applies_to`: `UnregisterEvent` 及所有按下标就地截断的删除循环
- `recheck_when`: 该循环被改写，或 `RegisterEvent` 开始做去重

同一通道在同一路径注册两次后反注册：`range` 仍按原始 2 元素头迭代，第一轮删除后长度变 1，第二轮 `infoList[2:]` 越界。实测 `PROBE before=2` → `panic: slice bounds out of range [2:1]`。凡是「锁内发送改为锁外发送、快照可能包含重复通道」的改动，都要顺带检查这个删除循环，因为重复项正是这类改动的常见副作用。

## 契约测试在 CI 里恒 skip，就不构成证据

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 `client_test.go:315` `TestNodeEventCarriesSyncConnected`；`.github/workflows/github-actions.yml` 无 `services:`、无 `ZK_ADDR`
- `applies_to`: 所有依赖外部服务、用 env + `t.Skip` 做可选执行的测试
- `recheck_when`: CI workflow 增加 service 容器，或测试的 skip 条件变化

「本机跑过、CI 绿」不等于「CI 有覆盖」。本仓库的 ZK 集成测试用 `ZK_ADDR` + `t.Skipf`，而 CI 没有 ZK service，所以新加的契约测试在 CI 里永远 `--- SKIP`，`go test ./...` 全绿对它零证明力。审查任何 `t.Skip` 型测试时，必须去 workflow 里确认对应的 service 是否存在；若不存在，要求 PR 明确写出「该测试在 CI 中恒 skip，仅本机有效」，否则后来者会误以为这条契约有 CI 保护。

## 文档类 commit 要像审代码一样把每句话跑一遍

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 第二版 head `520b80ebb4e3930488c2dba7176067c7efdb96c6`（`docs(zk): document the subscriber channel contract`，仅 `client.go` +19/-2，零行为变更）
- `applies_to`: 所有「只加注释/只改 godoc」的 commit
- `recheck_when`: 复审此类 commit 时

`RegisterEvent` 的新 godoc 写「When the channel is no longer needed, unregister it and drop the reference」，而这条建议本身会 panic：`RegisterEvent` 不去重，同一 path 注册同一通道两次后调用一次 `UnregisterEvent`，删除循环 `client.go:377-381` 在第二轮算 `infoList[2:]`、此时 len 已是 1，实测 `slice bounds out of range [2:1]`。文档 commit 的审查标准不能低于代码 commit——把文档里的每条陈述都当断言跑一遍（这里要跑的是「client 从不关闭注册通道」「panic 在调用方 recover 不到」「推荐姿势安全」三条），否则会把一个带坑的契约盖上「已文档化」的章。核对要点：`Close()` 是否真的不碰 `eventRegistry`、handler goroutine 是否由库自己启动（本例 `client.go:163`，故调用方确实无 recover 点）。

## 「这个分支是死代码」必须限定到具体语句，不能覆盖整个 case

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 head `520b80eb`，`client.go:285-287` 注释写「this exact-path send never runs. It is kept only for compatibility」，同 case 的 `:292-299` 却在维护 `valid` 与 `reconnectCh`
- `applies_to`: 任何给 `switch case` 加「kept for compatibility / dead code」注释的场景
- `recheck_when`: 后续有人清理兼容分支时

`StateConnecting, StateHasSession` 这个 case 里只有末尾的 `snapshotExactEventChans` 发送是死的（会话事件 Path 恒空 + `RegisterEvent` 拒绝空 path），前面的 `valid=1` 与 `close(z.reconnectCh)` 是重连机制的活逻辑。写成「kept only for compatibility」会让维护者把整块删掉，导致 `ZkConnValid()` 恒为 0。同文件 `StateConnected` 那个 case 整块确实只有发送循环，同样的措辞在那里才成立——**同一个文件里措辞相同不等于语义相同**，审查时要按 case 逐个确认体内是否还有非发送逻辑。

## Go 里「range 迭代头固定 + 就地截断」必然在二次匹配时越界

- `validated_at`: 2026-10-26
- `validated_ref`: `client.go:377-381`（master `a236273a` 与 PR #158 两版相同，非本 PR 引入）
- `applies_to`: 所有 `for i, e := range s { if match { s = append(s[:i], s[i+1:]...) } }` 形态的删除循环
- `recheck_when`: 该循环被改写，或注册路径开始允许重复项

`range` 在进入时固定 len/cap，就地截断后 len 变小但迭代仍按旧头继续；只要发生第二次匹配且 `i+1 > len`，`s[i+1:]` 就越界 panic。正确写法是匹配到即 `break`（只需删第一个），或重建切片。这类循环在「注册不去重、反注册删所有匹配」的容器里尤其危险，因为重复项正是最常见的输入。发现它的时机通常是审查「文档给出一条新的调用建议」——先问这条建议在重复输入下会怎样。

## 修掉一处 panic 之后，必须问「这个非法状态在其余路径上的语义是什么」

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 第三个 head `03b2c4bcdbd15b94996f710e924c01724e73c3b8`（`client.go:380-392` 改为重建切片），base `a236273a`
- `applies_to`: 所有「让某个原本会 panic 的非法输入变成可接受」的修复
- `recheck_when`: 同类容错型修复提交后

`UnregisterEvent` 改成重建切片后，重复注册不再 panic，API 从此「接受」重复注册这个状态。但同一条非法输入在另一条路径上仍然是未定义的：`RegisterEvent` 不去重，`snapshotPrefixEventChans`（`client.go:312-322`）会把 `subs...` 原样拼进快照，于是同一通道注册两次就收到两次事件（实测 `PROBE snapshot=2 dup_occurrences=2`）。对 dubbo-go `listener.go:121` 那种同步 `DataChange` 是有副作用的重复调用，同时也把阻塞风险翻倍。

审查容错型修复时的固定动作：列出该状态的**全部**消费点（本例是注册、反注册、派发三条），逐个确认语义是否已被定义。只修调用方报出来的那一条，等于把不确定从「会 panic」换成「静默不一致」，后者更难被发现。判断标准是「进一个、出一个」是否对称——注册允许重复、反注册删全部，这种不对称必须在文档里写死或在入口去重。

## 扫同类反模式时，必须逐处确认有没有早退保护

- `validated_at`: 2026-10-26
- `validated_ref`: `git grep "\[i+1:\]\.\.\." 03b2c4bc` 全库仅 `container/queue/queue.go:64-69` 一例，删除后紧跟 `return`
- `applies_to`: 用 grep 批量定位同一缺陷形态后的结论环节
- `recheck_when`: 每次准备把扫描结果写进 review 时

`for i := range s { if s[i]==x { s = append(s[:i], s[i+1:]...); return } }` 与出问题的写法形似，但 `return` 让它在首轮就退出，永远不会进入第二轮匹配，因此安全。把 grep 命中直接当成 bug 列表是常见错误——报之前必须读那一处的控制流。反过来，如果确实有早退保护，反而可以在 review 里写明「扫过，其余一例因 `return` 安全」，这比只报一处更有说服力。

## 导出 API 的 godoc 里，示例代码必须用外部包实测能否编译

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 第四个 head `055b31943466e47d71088ad8be2f2c7bc6b1113b`，`client.go:216-220` 写了 `go z.zkEventHandler.HandleZkEvent(z)`；第五个 head `14a88f57c39413c9463490e61a91d2bfbf5d81b1` 改为 `go z.GetEventHandler().HandleZkEvent(z)`
- `applies_to`: 所有面向包外调用方的 godoc 示例，尤其是「告诉调用方要做什么」的那类
- `recheck_when`: 每次在导出函数/构造器的注释里写代码片段；复审此类修复时

`NewZookeeperClientFromEnv` 是导出构造器，新加的注释告诉调用方「要自己启动 handler」，但示例用的是未导出字段 `zkEventHandler`。用同目录下 `package gxzookeeper_test` 的文件照抄这一行，`go vet` 直接报 `cannot refer to unexported field zkEventHandler`；换成已导出的 `z.GetEventHandler().HandleZkEvent(z)`（`client.go:616-618`）才能编过。验证方法很轻：在同包目录建一个 `_test.go`、声明 `package <pkg>_test`、把注释里的片段抄进去跑一次 `go vet`。审查「给调用方的操作指引」时，这一步应该和「核对事实是否成立」并列——语义对但编译不过的示例，比没有示例更误导。

复审这类「示例写法修正」时要**双向跑一次**：新写法 `go vet` 通过（rc=0），把同一行换回旧写法必须复现原来的报错。只跑新写法只能证明「现在能编」，证明不了「当初确实编不过」，也就无法确认修复针对的是真问题而非凑巧。本例两边结果相反（新：rc=0；旧：`z.zkEventHandler undefined`），才构成闭环证据。同理，作者把 `client_test.go:331` 的同一行一起改掉，是让「读者照抄测试」和「读者照抄 godoc」看到同一个 API——修正一处模式时要顺带 grep 全库的同模式出现点。

## 用 close(chan) 让 range 终止，把异步派发测成确定性断言

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 `client_event_test.go:138-158`（`TestRegisterEventIgnoresDuplicateRegistration`）
- `applies_to`: 所有 `for event := range someChan` 形态的消费循环的测试
- `recheck_when`: 测试里出现 `time.Sleep` 等派发完成时

被测算的是「同一通道重复注册后，一条事件只投递一次」。测试往缓冲为 1 的 `z.Session` 灌一条事件后立刻 `close(session)`，于是 `HandleZkEvent` 的 `for range` 自然终止、函数同步返回，再断言 `require.Len(t, dup, 1)` 读通道里的待消费条数。全程没有 `Sleep`、没有轮询、没有超时，结果是确定的，`-race` 也干净。对比之前那版只看 `len(client.eventRegistry[path])` 的写法：注册表长度只能证明「存了几份」，证明不了「投递了几次」，而去重这个改动的实际语义恰恰在投递侧。衡量测试够不够，看它断言的是不是改动的语义位置，而不是它有没有通过。

## 构造器把 opts 应用到临时结构体后不再读取，编译器和 vet 都不会报

- `validated_at`: 2026-10-26
- `validated_ref`: PR #158 第五个 head `14a88f57c39413c9463490e61a91d2bfbf5d81b1`，`NewZookeeperClientFromEnv` 的 `opts ...Option` 在 `client.go:235-238` 应用后到 `:274` 返回再无读取；master `a236273a` 同样如此（非本 PR 引入）
- `applies_to`: 所有 `opts ...XOption` 形态的构造器，尤其是同名族里存在两种 option 类型时
- `recheck_when`: 构造器签名或 option 应用顺序被改动时

`option := &options{} / for _, opt := range opts { opt(option) }` 里 `opt(option)` 已构成对局部变量的「使用」，因此 `go build`/`go vet` 全绿，静态检查也不会提示「声明未使用」。但函数随后直接读参数、返回在 `:224` 就构造好的 `z`，那份 `options` 从未被消费——调用方传进来的所有配置被静默丢弃。审查要点是**核对 option 的落地对象是否就是最终返回的对象**，而不是「有没有应用 option」。同族还存在类型分裂时更隐蔽：`WithZkEventHandler`（`options.go:43`）返回 `zkClientOption`，而 `FromEnv` 声明 `...Option`，二者不兼容，调用方想注入自定义 handler 连编译都过不了——文档里「两个构造器平行」的叙述因此不成立。顺带一提，`ZookeeperClient` 的 handler 由 `NewZookeeperClient` → `newClient:131` → `createZookeeperConn:154` → `:163` 的 `go z.zkEventHandler.HandleZkEvent(z)` 启动，`FromEnv` 走 `zk.Connect` 绕开了这条链，所以「不启动 handler」的注释是准确的——注释对、实现漏，两件事要分开核。
