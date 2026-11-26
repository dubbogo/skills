<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-go-pixiu Review 补充规则

## HTTP FilterChain 热刷新资源所有权

- 为 FilterChain/FilterFactory 新增长连接、后台 goroutine、descriptor cache 或 `Close` 后，不能只验证 listener 终止路径。`HttpListenerService.Refresh` 替换旧 chain 时必须定义并发安全的 swap、drain 与最终 Close；回归测试应覆盖连续刷新、在途请求期间刷新和 Close 错误，并证明旧 connection manager、socket、goroutine 与 descriptor 状态最终释放。

## gRPC proxy connection 与 descriptor cache

- descriptor cache miss 不得在全局 map mutex 下执行 REMOTE/AUTO 网络 reflection。应在锁外 lookup，只在 double-check/store 时短暂持锁；需要合并同 key 并发 miss 时按 connection/service/method 使用 singleflight 或 per-key entry。测试必须证明慢后端 A 不阻塞无关后端 B，同时保留同 key 只查询一次。
- connection manager 按 cluster/endpoint 缓存长期 `grpc.ClientConn` 时，注册中心 endpoint 删除、cluster snapshot reconcile 和 listener refresh 都必须进入淘汰路径；只在再次访问同 key 且 transport 不健康时删除会永久保留已下线但健康的连接。删除连接时必须同步清理以 `*grpc.ClientConn` 为 key 的 descriptor cache，并用多轮 endpoint churn 验证连接、goroutine 与内存状态有界。
- `validated_at`: 2026-08-08；`validated_ref`: Base `57781a8831d69f030af14b11e8c88f6aae3186e0` / Head `3360561b8b14fbb8df8c76a23147abb1c576fa47`；`applies_to`: HTTP listener refresh、gRPC proxy connection manager、reflection descriptor cache 与动态 registry endpoint；`toolchain`: Go 1.25.1 linux/amd64；`recheck_when`: FilterChain ownership、cluster manager notifications、connection key/eviction 或 reflection lookup locking 变化。

## Admin 端点的域边界（审查跨模块删除时的必查项）

- `admin/controller/configInfo/` 与 `admin/logic/logic.go` 承载**多个配置域**：base、cluster、listener、resource/method、plugin_group、opa。审查"把某一域的代码移出"类重构时，必须逐一核对 `admin/initialize/router.go` 中**被删除的路由注册**是否属于本次 PR 的目标域，不能只看新增路由。
- 判据：`git show <base>:admin/initialize/router.go` 与 head 对比路由表；对每个被移除的 handler 再 `grep` 其函数名与关联 `logic.*` 符号在 head 是否仍有定义。若 head 中处理函数、关联 logic 符号与 swagger 路径**同时消失**，说明是整个域被删除，需在 PR 描述/release-note 中找到显式声明，否则按越界删除提出。
- 注意区分"空实现"与"有效实现"：本仓库存在 `BatchReleaseMethod` 这类 `// todo` 空 handler，删除它无行为影响；而 `BatchReleasePluginGroup` 有真实读写逻辑，删除会静默产生 404。
- `validated_at`: 2026-10-08；`validated_ref`: Base `ba018888affd631f5e7683813d78a88a54a2de32` / Head `12a9be583176e26c9ee29a7ebc82deaa4c6fda66`（PR 1046）；`applies_to`: `admin/` 目录的路由注册与 controller/logic 重构；`toolchain`: Windows amd64 Go 1.27.0；`recheck_when`: `admin/initialize/router.go` 路由表、`admin/controller/configInfo/` 分文件或 plugin_group/resource/method 域恢复。

## 构建与测试边界（Windows 沙箱）

- `go build ./...` 在本仓库 Windows 下失败于 `admin/core/zap.go: undefined: utils.GetWriteSyncer`（定义在 `admin/utils/rotatelogs_unix.go`，无 windows 变体）。该文件未被 PR 1046 改动，属 Base 既有平台缺口，不得归责 PR。替代做法：直接对目标包执行 `go test ./pkg/config/schema/...`、`go test ./admin/logic/...`。
- `admin/logic` 的 `opa_test.go` 全部依赖 loopback，在本沙箱必然失败（见 `review.md` 第 13.1 节）。核对本域改动时用 `-run` 过滤出目标用例（如 `-run 'RouteBinding|Publish|Draft'`）再判读结果。
- `validated_at`: 2026-10-08；`validated_ref`: Head `12a9be583176e26c9ee29a7ebc82deaa4c6fda66`（PR 1046）；`applies_to`: `admin/` 与 `pkg/config/` 的本地构建与测试；`toolchain`: Windows amd64 Go 1.27.0；`recheck_when`: 新增 `admin/utils/rotatelogs_windows.go`、zap 初始化重构，或 OPA 测试改为不依赖真实监听。
