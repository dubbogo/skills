<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-go Review 补充规则

## Generic mode 与 Triple 兼容

- 修改 generic mode 合法集合时，必须联查 `internal.ValidateGenericType`、`filter/generic.isGeneric`、`filter/generic.getGeneralizer`、`protocol/triple.isGenericCall` 及测试；`bean`、`protobuf`、`protobuf-json` 的兼容策略必须一致，并覆盖未设置 `NONIDL` 和 `ClientInfoKey` 的 Triple 引用，确认合法 mode 会选择支持 `$invoke` 的 Invoker。
- `protobuf` 与 `protobuf-json` 的 legacy/transport marker 不得因字面值相近而互换。必须分别核对 Invoker、外层 wire codec、内层 `$invoke` 参数编码和 provider generalizer，并用 Hessian string/map/POJO 参数做 Base/Head 对照，防止历史 `generic=protobuf` 调用被错误要求为 JSON string 或 `proto.Message`。
- 新增 `WithGenericIncludeClass` 等 `ReferenceOption` 时，除执行总协议的配置端到端门禁外，还必须确认参数最终进入 `MapGeneralizer` 并改变输出；只断言 `Reference.Params` 或 URL 不足。

## MapGeneralizer tag 往返

- `MapGeneralizer.Generalize` 通过 `setInMap` 读取 `m` tag，无 tag 时使用 `toUnexport` 生成字段名；`Realize` 必须使用 `mapstructure.NewDecoder(DecoderConfig{TagName: "m"})`，否则 `UserID` 与 `m:"user_id"` 等字段无法往返。
- mapstructure v1.5.0 默认大小写不敏感，`Name`/`name` 或 `BaBa`/`m:"baBa"` 会掩盖 tag 不一致。回归探针必须使用带下划线或与字段名明显不同的 tag 做 OLD/NEW 对照。启用 `TagName: "m"` 后，仅声明 `mapstructure` tag 的字段会改按字段名匹配；这是行为变化，应明确 `m` 是唯一 tag 源。

## GenericException 迁移兼容

- 旧包保留 `GenericException` 兼容入口时，注释声称 alias 不构成证据，必须核对声明确为 `type GenericException = hessian.GenericException`。独立 struct 会使旧类型断言与新类型 switch 失配；必须用外部包通过公开 `HessianCodec.Write/Read` 验证旧类型编码、解码动态类型和 `ToGenericException(decoded.Exception)`，不能只验证符号可构造或 string helper 字段。
- `validated_at`: 2026-07-31；`validated_ref`: Base `bcd6aa42be158b28f969e7669c43ae8f543ac7e5` / Head `09ca103191a704c6daad779b9141178c5b849820`；`applies_to`: GenericException 从 dubbo-go 向 dubbo-go-hessian2 迁移及兼容层；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: 两侧类型声明、Hessian response 编解码 switch 或 hessian2 版本变化。

## Context 传播闭环

- 新增 `WithContext` 入口后必须扫描非测试调用方；若生产调用仍只进入固定 `context.Background()` 的兼容 wrapper，测试直接调用新 API 不能证明修复生效。metadata v1 还必须沿 `DubboInvoker -> ExchangeClient -> Getty Client.Request` 验证等待逻辑实际监听 `ctx.Done()`，仅把 ctx 传给 `Invoker.Invoke` 不足。
- JSON-RPC 自行使用 `http.ReadRequest` 解析连接时，`r.Context()` 不具备 `net/http.Server` 提供的断连取消语义；断连回归测试必须按真实连接/read-loop 构造请求，不能用预注入 context 的 `httptest.NewRequestWithContext` 替代。
- `RPCInvocation.GetAttachmentAsContext` 以已有 request context 为基底时，必须先 clone `triple_protocol.ExtractFromOutgoingContext` 再叠加 invocation attachments；`NewOutgoingContext` 会替换已有 outgoing headers。测试必须覆盖不同 key 的保留和冲突 key 的优先级。
- `validated_at`: 2026-07-31；`validated_ref`: Base `53d81d17c0f658b7151fb8c44f0d80371ef047e7` / Head `4dc23b5e73fa7db7007638450aa5b358b8f6bc38`；`applies_to`: metadata、JSON-RPC、RPCInvocation 与 Triple attachment 的 context 传播；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: metadata 生产入口、Dubbo remoting request API、JSON-RPC server ownership 或 Triple context header API 变化。

## Triple 非 IDL 响应容器形状

- Triple server 的生产返回链不是把业务结果标量直接交给 codec：`wrapTripleResponse` 会构造 `[]any{result}`，handler 再通过 `conn.Send(response.Any())` 传给 marshaler。新增或重构非 IDL response wrapper/session 时，必须按该真实容器形状验证并显式定义零元素、单元素、多元素和 `nil`；只在单测中直接调用 `Codec.Marshal(result)` 会绕过生产协议形状。至少用公开 Invoker/handler 链或等价 overlay 覆盖 Hessian2、MsgPack、具体类型指针和 `*any`，同时断言标量结果不被编码成数组、客户端不 panic。
- `validated_at`: 2026-08-02；`validated_ref`: Base `53d81d17c0f658b7151fb8c44f0d80371ef047e7` / Head `0b0aa98b48ffb068dcba1a6b67b99c079f101ef6`；`applies_to`: Triple 非 IDL server response wrapper、codec session 和客户端 wrapper 解码；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: `wrapTripleResponse`、handler `conn.Send`、response container 或 Triple wrapper codec 形状变化。

## Tools、CI 与时效性基线

- `tools/` 下现有工具均为带独立 `go.mod` 的子模块。新增 `tools/*` 必须遵循该边界，并按需使用 `replace dubbo.apache.org/dubbo-go/v3 => ../../..`；同时核对 README，避免工具被意外并入根模块的 `go build ./...` 或 `go test ./...`。
- 以实时 workflow、Makefile 和 `go.mod` 为准。当前记录的主测试包含根模块 `go test ./... -coverprofile ...` 和 `$(CLI_DIR)` 子模块测试；RISC-V 门禁执行 `GOOS=linux GOARCH=riscv64 CGO_ENABLED=0 go build ./...`；fmt/lint 入口为 Makefile 的 `fmt`/`lint`。当前记录的工具链为 Go 1.25，且 Makefile 设置 `GOTOOLCHAIN=go1.25.0+auto`；使用前必须复核是否仍有效。
- Windows PowerShell 配合 Cmder/GNU make 执行 `make check-fmt` 时，Makefile 中的 `GOROOT=$(shell go env GOROOT)` 可能经 Bash 把 `D:\...` 解释成缺少反斜杠的路径，导致 `imports-formatter` 因找不到 `GOROOT/src` 而 panic。Windows 审查应在 `core.autocrlf=false` 的隔离副本中依次执行 `modernize -fix`、根模块 `go fmt ./...`、显式设置 PowerShell `$env:GOROOT` 后运行 `imports-formatter`、CLI 子模块 `go fmt ./...`，并核对没有额外 Diff；最终格式门禁仍以 exact Head 的 Linux `make check-fmt` CI 为准。
  - `validated_at`: 2026-08-01；`validated_ref`: Head `23e50e5152c58d197317351dc835865ce26242a1`；`applies_to`: 当前 `Makefile` 的 `fmt` / `check-fmt` 与 `tools/imports-formatter`；`toolchain`: Windows Go 1.26.2 + Cmder GNU make，本轮 GitHub Actions Go 1.25；`recheck_when`: Makefile 的 GOROOT 传递方式、imports-formatter 启动方式或 Windows shell/make 组合变化。
- 历史基线 `53d81d17` 删除 `protocol/base` 后，`remoting/exchange_client.go` 曾残留该 import，使 Base 与 PR Head 的根模块构建同时失败。后续审查先复核当前 Base；若问题仍在，按基线处理，使用 merge-ref CI 或不传递依赖 `remoting` 的定向包验证，不得归责于 PR。

## Metadata mapping 指标生产链与测试生命周期

- mapping 指标的有效回归必须从 `DelegateMetadataReport` 的 Register/Get/Listen/Remove 公开方法出发，经过附件生成、`metrics.Publish`、包级 event channel、`MetadataMetricCollector.start()` switch、handler 和 registry，并断言 interface/group/application 标签及成功、失败、RT。测试手工构造 `MetadataMetricEvent` 和附件只能证明下半链，删除 Delegate 附件连接后仍通过时不得算需求闭环。
- 异步 collector 测试不得通过 `Unsubscribe` 永久关闭生产包级 channel 后继续复用同一进程状态；应提供可重建或可注入的测试 channel/teardown seam。mock registry 的 map/slice 写入与 `Eventually` 等异步读取必须同步，且关键用例同时通过 `-race` 和 `-count=2`，避免测试自身竞态或重复关闭掩盖生产回归。
- `validated_at`: 2026-08-08；`validated_ref`: Base `62476d5109e41eb2fb47afc5868372dab35f6e9f` / Head `f25bd1a770335568452a8bb2d3a9e84711d5157d`；`applies_to`: metadata mapping metrics producer、event bus、collector 与测试；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: Delegate 附件、metrics channel、collector start/stop 或 registry mock 生命周期变化。

## ZooKeeper config cache 的有界状态

- `DynamicConfiguration` 的 key/group 是调用方可控空间；启用 read-through cache 后，`entries`、missing-node 负缓存、watch bookkeeping 和 `pathLocks` 都必须有容量或 TTL/LRU 淘汰。`expiresAt` 只触发 reload 不等于回收；restart/reset 也必须清理不再使用的每路径状态，同时避免删除仍有 in-flight loader 的锁。回归探针应覆盖大量唯一 key、missing key、TTL 过期、reset、并发 same-key load，并断言状态数量有界且 singleflight 语义保持。
- `validated_at`: 2026-08-08；`validated_ref`: Base `0a0ce09631ccb72264f86223fdbbf61021c5a01e` / Head `9ce4e2e23d1ee9de8fdcdbc549da3d74d4060535`；`applies_to`: `config_center/zookeeper` read-through cache、watch 与 restart；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: cache key contract、TTL/eviction、watch lifecycle 或 reset 实现变化。

## Triple 服务端消息大小配置兼容与生产链

- `ProtocolConfig.MaxServerSendMsgSize`、`ProtocolConfig.MaxServerRecvMsgSize` 等已经发布的 v3 导出字段，即使标记 Deprecated，也不得在 `dubbo.apache.org/dubbo-go/v3` 内提前删除；原注释约定 v4 删除时，应保留旧字段并把非空旧值迁移到 `TripleConfig`，明确 legacy 与 nested 配置同时存在时的优先级。验证必须使用独立外部 module 编译 Base/Head 的同一 struct literal，并覆盖旧 YAML/JSON 配置，而不能只用仓内引用清零证明兼容。
- Triple message-size 配置的有效回归必须从公开入口 `dubbo.NewInstance` 与 `protocol.WithTriple` 出发，经过 `ServiceOptions.Export` 的 URL attribute/legacy params、`TripleProtocol` 和 handler option，最终用真实请求同时断言小载荷成功、超限载荷被拒。只检查字段存在性、默认值、Clone、Instance 内部配置或导出 URL 不足；应通过隔离 mutation 断开 attribute 与 legacy params，确认测试稳定失败。
- `validated_at`: 2026-08-08；`validated_ref`: Base `48d6e696e755d46df2425bbf71c413bbd1887f3f` / Head `b7c68e9ebe6d4ee49a0be5d7556b29df297be841`；`applies_to`: `global.ProtocolConfig` / `TripleConfig`、服务 Export 和 Triple server message-size option；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: module major、公开配置字段、配置解码、Export URL/attribute 或 Triple handler option 消费链变化。

## 扩展 filter 名称合并的 client/server 消费端语义

- `common/extension.MergeFilterNames` 只做字符串级合并，「扩展声明的 filter 是否与框架默认链共存」由两侧消费点分别决定，两者语义不同：client 走 `client/action.go` 的 `commonCfg.MergeValue(ref.Filter, "", defaultReferenceFilter)`，会把扩展名并入默认值；server 走 `server/action.go` 的 `if svcConf.Filter == "" { constant.DefaultServiceFilters } else { svcConf.Filter }`，一旦 `global.ProviderConfig.Filter` 被写成非空就整体替换默认链（`ServiceOptions.init` 通过 `dubboutil.CopyFields` 仅在 `Service.Filter` 为零值时把 `Provider.Filter` 抄进去，因此「用户没配 provider.filter」会被改写成「用户显式配置」）。
- 任何把框架级或扩展级 filter 名写进 `Provider.Filter` 的改动都会静默丢弃 `echo,token,accesslog,tps,generic_service,execute,pshutdown`；其中 `token` 是 provider 侧鉴权（`filter/token` 在 `TokenKey` 非空时强制校验）、`tps`/`execute` 是限流与并发限制、`pshutdown` 是优雅停机。审查这类改动必须同时给出 client 与 server 的导出 filter 串。
- 有效回归必须从 `Server.genSvcOpts` / `Export` 链路断言导出 URL 的 `service.filter`（包内探针可用 `defaultServerOptions().init` → `defaultServiceOptions().init(srv, SetProvider(...))` → `getUrlMap()` 等价复现）；只断言 `ServerOptions.Provider.Filter`、`ClientOptions.overallReference.Filter` 这类内部字段不足，回归存在时这些断言仍会通过。
- `validated_at`: 2026-09-11；`validated_ref`: Base `832124aaacf0283445d379e935ff5d73695fa84d` / Head `1bc7adaf5e1437cb1ea9295bd4522de561ed66ef`；`applies_to`: dubbo-go v3 `common/extension` 扩展 filter 名称在 client/server 的合并；`toolchain`: 探针 Go 1.27.0 windows/amd64（CI 以 workflow 为准）；`recheck_when`: `MergeFilterNames` 实现、`server/options.go` 与 `client/options.go` 的合并位置、`server/action.go` 的 `svcConf.Filter` 判定、`client/action.go` 的 `MergeValue` 调用、`constant.DefaultServiceFilters` 或 `dubboutil.CopyFields` 语义变化。
- **更新（同日，Head 漂移至 `0d935f6d`）**：上述「回写 `Provider.Filter`」缺陷在 `0d935f6d` 已修复——改为把扩展 filter 名存入 `ServerOptions.extensionFilterNames`，并在 `server/action.go` 的**默认链解析之后**做 `filters = extension.MergeFilterNames(filters, srvOpts.srvOpts.extensionFilterNames)`。上面的机制描述仍作为「同类改动的失效模式」保留：任何在 `CopyFields` 之前改写 `Provider.Filter` 的写法都会重新触发它。断言口保持不变（导出 `service.filter`）。

## 扩展 filter 抑制语法（`-name`）的两端口径与断言要求

- 同一 `-name` 写法在两端语义不同，交叉核对是必需项：**consumer** 经 `client/action.go` 的 `commonCfg.MergeValue(ref.Filter, "", defaultReferenceFilter)`，其内部 `removeMinus`（`common/config/utils.go`）会在展开 `default` 关键字后剥除 `-name`，因此 `-x` 表现为「默认链去掉 x」；**provider** 不经过 `MergeValue`（全仓唯一调用点是 `client/action.go`），`server/action.go` 把合并且**不会**剥除 `-name`。
- `MergeFilterNames` 对未命中 additions 的 `-name` 记号会**原样保留**（`common/extension/config_loader_test.go` 用 `MergeFilterNames("-default,a", []string{"extension"}) == "-default,a,extension"` 固化该行为）。provider 侧该记号随后进入 URL 的 `service.filter`，而 `protocol/protocolwrapper/protocol_filter_wrapper.go` 的 `BuildInvokerChain` 使用 `flt, _ := extension.GetFilter(strings.TrimSpace(filterName))` **忽略 `ok`**，未注册名字会构造 `filter == nil` 的 `FilterInvoker`，`FilterInvoker.Invoke` 调用 `fi.filter.Invoke` 时 panic（实测 `GetFilter("-x") -> ok=false`、`filter==nil: true`、`Invoke panicked: runtime error: invalid memory address or nil pointer dereference`）。
- 抑制「命中」与「未命中」必须分别验证导出结果，二者都不是「默认链减去该 filter」：实测 `WithServerFilter("-<扩展贡献的 filter>")` 的导出 `service.filter` 为**空串**（整条默认链消失，因为 `svcConf.Filter` 非空使默认链分支不生效）；`WithServerFilter("-<未注册名>")` 的导出串为 `-<未注册名>,<扩展 filter>`。
- 有效回归必须断言导出 URL 的 `service.filter`。只断言 `ServerOptions.Provider.Filter` 的用例在两种情况下都会通过，无法证明抑制生效——`server/options_test.go` 的抑制用例即属此类弱断言，而 `client/options_test.go` 断言的是 `refOpts.getURLMap().Get(constant.ReferenceFilterKey)`，两侧强度不对称，审查时按此对照。
- `MergeFilterNames` 在「抑制命中」场景**非幂等**：`MergeFilterNames("-contrib,a", []string{"contrib"})` → `a`，再以 `a` 为 existing 应用同一 additions → `a,contrib`。当前不构成缺陷，因为 `ClientOptions` / `ServerOptions` 每次构造都新建（`defaultClientOptions` 里 `global.DefaultReferenceConfig()`），`init()` 不会对同一实例重复执行；一旦出现复用或重复 init，抑制会静默失效，需重新评估。
- 扩展 SPI 的破坏性变更必须先核对「是否已发布」再判严重度：本 PR 删除的 `extension.SetConfig` 存在于 tag `v3.3.0` / `v3.3.1` / `v3.3.2`（逐 tag 取 `common/extension/config.go` 核对），同时 `Config` 接口新增 `New` / `Init` / `FilterNames`。仓内无调用点不代表外部无调用点；reviewer 应要求 CHANGELOG 或迁移说明（`SetConfig(c)` → `MustRegisterConfig(c)` 并实现三个新方法），而不是只看 `go build ./...` 通过。关联 issue 允许 breaking 时，缺口仅在「无迁移说明」。
- `collectRawConfigs` 对 `dubbo.extensions.<未注册前缀>` 直接返回错误（`extension %q: config is not registered`），即 YAML 中残留的、本服务未编译进的扩展块会导致启动失败。审查此类 fail-fast 设计时确认其是否被文档声明；多服务共用同一 YAML、扩展灰度启用的场景下这是可用性问题。
- `validated_at`: 2026-09-11；`validated_ref`: Base `832124aaacf0283445d379e935ff5d73695fa84d` / Head `0d935f6dd8df2569302c8dca85608b5d018cbb37`；`applies_to`: dubbo-go v3 `common/extension` 的 `MergeFilterNames` / `Initialize` 与 `protocol/protocolwrapper.BuildInvokerChain`；`toolchain`: Go 1.27.0 windows/amd64（探针），CI 以 workflow 为准；`recheck_when`: `MergeFilterNames` / `mergeExistingFilterName` / `removeMinus` 实现、`server/action.go` 与 `client/action.go` 的消费点、`BuildInvokerChain` 对 `GetFilter` 返回值的处理、`Config` 接口或 `RegisterConfig` 签名变化。

## tools/* 子模块的 CI 执行面

- `tools/` 下每个工具都是独立 module（各自 `go.mod`）。根模块 `go list ./...` 不匹配这些目录，因此 Makefile 的 `test` / `test-race`（根模块 `go test ./...` + `cd tools/dubbogo-cli && go test ./...`）**不覆盖** `tools/protoc-gen-triple-openapi` 等子模块，`make lint` 同样只跑根模块。
- 唯一由 `tools/**` 触发的工作流是 `.github/workflows/tools.yml`，作业为 `Format`（`make fmt` + `git diff --exit-code`）、`Lint`、`Generated CLI Projects`（只构建 `tools/protoc-gen-go-triple` 与 `tools/dubbogo-cli`），**没有 test 作业**。给 `tools/*` 新增测试的 PR，必须先确认该测试是否真会被执行；「Unit Test / Lint / Format 全绿」不能作为该模块测试已运行的证据。
- 有效验证方式：进入子模块目录执行 `go build ./... && go vet ./... && go test ./... -count=1`；按 R06A 用变异体（仅移除修复行）确认新增用例确实失败；对 protoc 插件还应用真实 `protoc` 覆盖三类参数（默认 / 合法 opt / 非法 opt），检查 exit code、产物文件数与 stderr。
- `options.Generate` 出错时返回的是**部分解析的** Options（先 `defaultOptions()` 给 yaml，再逐项覆盖）。因此 `convert` 忽略 `err` 后仍能静默产出 YAML/JSON，且结果依赖参数顺序；审查同类「忽略 err」缺陷时需确认返回值可用性，否则容易误判为 nil panic 而非静默成功。
- `validated_at`: 2026-10-21；`validated_ref`: Base `94bc3a530cb5a75d5ddfe3b857bcad89f4142951` / Head `917f692f395ded8af0fb33b8961823bc801a1da7`；`applies_to`: `tools/*` 子模块（尤其 `protoc-gen-triple-openapi`）的 CI 覆盖与测试有效性判定；`toolchain`: Go 1.27.0 windows/amd64（探针），protoc 35.1；`recheck_when`: Makefile 的 `test`/`lint` 目标、`.github/workflows/tools.yml` 作业集合、或 `tools/*` 模块边界变化。
- 「CI 检查 success」不等于「新增测试被执行」：必须读 job 日志确认 `working-directory`、实际执行命令，以及被测包出现 `ok  <pkg>` 行；出现 `[no test files]` 或包列表缺失都是假绿。
- `runs-on: ubuntu-latest` 会随 GitHub 镜像滚动迁移。实测 2026-10-21 → 2026-10-22 之间同一 PR 的 Integration Test 由 `ubuntu-24.04`（24.04.5）切到 `ubuntu-26.04`（26.04.1），`java_interop/service_discovery/service` 随即出现 `NoClassDefFoundError: com/alibaba/fastjson/JSONException` 与 `BindException`，并在 `timeout-minutes` 处被 cancelled。归因必须比对前后两轮 job 日志的 `Operating System` / `Runner Image` 段，并核对 PR 差异是否属于该工作流的输入（`github-actions.yml`），不能只看结论状态。
- `validated_at`: 2026-10-22；`validated_ref`: Head `8ff7866cb86864ebfe6c0096feea2a7786b36aba`；`applies_to`: dubbo-go CI 中 `ubuntu-latest` 运行时漂移的归因与「新测试是否真正执行」的核验；`toolchain`: GitHub Actions（runner 2.338.0）；`recheck_when`: runner 镜像迁移完成、`runs-on` 改为固定版本、或 Integration Test 样例升级 JDK/依赖。

## 测试拿标准库输出的字节数当断言前提，换 Go 版本就红

- `validated_at`: 2026-10-27
- `validated_ref`: apache/dubbo-go PR #3782（head `92a48c6884f15503de3130ddb159b77fad2187eb`，base `97666ec8`），`protocol/triple/response_compression_safety_test.go:216`、`:319`
- `applies_to`: 断言压缩/编码后大小、报文长度、序列化后字节数的测试
- `recheck_when`: 测试里出现「压缩后应该能塞进上限」「编码后长度应为 N」这类前提

PR 新增的发送上限用例用 `bytes.Repeat([]byte("x"), n)` 造 payload，并断言 63/64/65 字节的响应压缩后仍能通过 64 字节上限。同一份代码、同一个探针，只换 toolchain：

| Go | 63 字节 'x' 的 gzip 输出 | 用例结论 |
|---|---|---|
| 1.25.0 | 27 B | 200 + gzip，符合断言 |
| 1.27.0 | 88 B | 429 `compressed message size 88 exceeds sendMaxBytes 64` |

根因是 `compress/flate` 对小输入退化成 stored block，27 → 88 不是 bug 而是实现策略。CI 用 `go-version-file: go.mod` 锁在 1.25，所以绿；一旦上调 `go` 指令或贡献者用新版工具链本地跑就红，且报错指向「压缩后超限」，极易被误判成生产代码回归。

审查要点：看到测试用真实压缩率做前提，就问「换成另一种压缩器/另一个 Go 版本还成立吗」。取证方式很轻——`GOTOOLCHAIN=go1.25.0 go test ...` 与本地版本各跑一次同一探针。修法是让断言与编码器无关：要么把 payload 提到帧开销不占主导的区间（≥256B），要么只断言框架决策（阈值、flag、cap）不断言产物大小。

## loopback 被拦截时，用 ServeHTTP + ResponseRecorder 替真实服务取证

- `validated_at`: 2026-10-27
- `validated_ref`: 本机 `net.DialTimeout("tcp","127.0.0.1:<port>")` → `connectex: ... failed to respond`；关沙箱后相同；既有的 `TestClientManagerCallUnaryCopiesResponseMetadata` 同样失败
- `applies_to`: 所有依赖 `httptest.NewServer/StartTLS` 的 handler 行为评审
- `recheck_when`: wire 级测试在本机跑不起来时

`httptest.NewUnstartedServer(...).StartTLS()` 需要真实 dial，本机被拦时整条 wire 测试只能超时（我曾等满 300s）。可用的替代：手工构造请求交给 `handler.ServeHTTP(httptest.NewRecorder(), req)`，记得 `req.ProtoMajor, req.ProtoMinor = 2, 0`、补齐 `Content-Type` / `Te: trailers` / `Accept-Encoding`。这条路会完整经过 `resolveHandlerOptions` → `tri.NewUnaryHandler` → `tripleUnaryMarshaler`，能拿到真实的状态码、`Content-Encoding`、压缩 flag 与 body 长度，足以验证默认值、回滚、服务级覆盖、上限拒绝。

两个限制要写清：① 流式用例不适合这条路（请求体为空会先 EOF，测不出压缩决策），只能标注为同源推断；② 一旦改用这条路，就要在评审里说明「哪些结论是实测、哪些是读代码」，不要混着说「经验证」。

先跑一次仓库里既有的同类端到端测试确认是环境限制而不是自己的探针写错——本次既有的 client 测试报同样的 `connectex` 错误，直接坐实了是环境。
