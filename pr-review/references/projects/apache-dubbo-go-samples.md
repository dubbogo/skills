<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-go-samples Review 补充规则

## Sample 集成验证

- 新增到 `start_integrate_test.sh` 的 sample 必须让 client 精确断言关键返回字段，并在不匹配时非 0 退出。consumer/provider 共用路由或 REST mapping 时，还必须用不复用该配置的原生请求固定验证 HTTP method、path、query、header、body、状态码和完整响应。
- 远端 `Build And Integration` 不能只看 job 总状态；必须从日志确认目标 sample 实际出现 `start`、业务响应和 `Sample flow completed`。
- graceful-shutdown 回归必须在同一服务进程收到真实停机信号后发起独立新请求，并用删除停机阶段 `RejectRequest` 状态切换的变异证明测试会失败。另启进程并用 `WithRejectRequest` 预置拒绝状态只能验证静态配置，不能证明停机状态切换。

## CI 依赖基线

- CI 会在测试前执行 `go mod edit -replace=dubbo.apache.org/dubbo-go/v3=...@<base branch>` 和 `go mod tidy`。本地验证应复现该改写；若仓库原始 `go.mod` 的预发布依赖导致未改模块失败，必须对 Base 执行同一失败包，并结合完成替换的 CI 结果区分 PR、基线和依赖环境问题。

## 未列入集成矩阵的 sample 是否被 CI 覆盖

- 判定「某 sample 的编译/类型检查是否被 CI 覆盖」不能只看 workflow 中是否存在 `go build ./...`。本仓 `.github/workflows/golangci-lint.yml` 走 `golangci-lint-action`，而根 `.golangci.yml` 启用了 `staticcheck` / `unused` / `govet`，这三者都需要对模块内全部包做类型检查，因此**未**列入 `start_integrate_test.sh` 的 sample（如 `http3`）其编译仍被 `lint` 检查覆盖。先误判为「编译未验证」、再经静态核查纠正的做法不可复用；直接读 `.golangci.yml` 的 linter 集即可定论。
- 反向结论同样成立：来自 `lint` 的覆盖不能替代行为验证。集成行为仍只由 `start_integrate_test.sh` 的 `array` 决定，`integrate_test.sh` 以 sample 目录为入参，新增测试点即在 `array` 中追加条目。
- `validated_at`: 2026-09-11；`validated_ref`: Head `b9eb3468bddcae8643e029cc5871325018858073` / Base `0060392cb0d733ba63c95109db642d847ac28968`；`recheck_when`: `.golangci.yml` 的 linter 集或 `golangci-lint-action` 参数变化、`start_integrate_test.sh` 的 `array` 变化。

## 依赖 pin 的三步核验

- samples 仓把 dubbo-go 依赖 pin 到日期型 tag，核验必须三步齐全：① `git/ref/tags/<tag>` 确认 tag 是真实 ref；② 取该 ref 的 commit；③ 与 CI 的替换目标对照——`go mod edit -replace=...@<base_ref>` 用的是 PR 的 `base_ref`，故应 `compare/<base_ref>...<pin_sha>` 确认二者一致。
- 本轮实例：pin `v3.3.2-20260910` → `832124aaacf0283445d379e935ff5d73695fa84d`，`compare/main...832124aa` 为 `identical`，即 pin 与 `main` 同一 commit，CI 与本地一致；被替换的旧 pin `v3.3.2-20260419` 在 dubbo-go 中已不存在（404 `No commit found for the ref`），故本次升级有据。不要仅凭「一次依赖大范围抬升」就判定为范围失控。
- 新 pin 到位后，仍需确认 sample 调用的符号在该 ref 真实存在（逐个取源文件核对函数签名），并核对待替换 API 是否为薄封装别名（如 `triple.Http3Enable()` 即 `return WithHttp3Enable()`），避免把等价替换误报成语义变更。
- `validated_at`: 2026-09-11；`validated_ref`: Head `b9eb3468bddcae8643e029cc5871325018858073`；`recheck_when`: CI 的 `go mod edit -replace` 目标分支、pin 命名规则或 dubbo-go tag 策略变化。

## PR review thread 的未解决诉求

- samples 仓的 review 诉求常以行内 thread 提出，且**澄清可能晚于最新 commit**。审查前必须用 `graphql reviewThreads` 同时取 `isResolved`、`isOutdated`、`path`、每条评论的 `author` / `createdAt` / `body`，并与 PR 的 `updatedAt` 对齐：若某 thread 最新评论时间等于或晚于 head 提交，则诉求尚未被回应，即使 CI 全绿也不能视为已闭环。
- 本轮实例：`http3/go-client/cmd/main.go` 上未解决的 thread 明确要求「集成测试的测试点，以验证 server 和 client 是否符合预期行为，不是加单元测试」，而 head 只新增了 `http3/internal/quic/quic_test.go`（断言 `Options()` → `triple.Options.Triple.Http3` 的字段映射，不启动 server/client、无 RPC 往返），故诉求未被满足。判定测试性质时应明确区分「构造级字段映射」与「行为级验证」，后者需要启动双端并断言关键返回字段。
- `validated_at`: 2026-09-11；`validated_ref`: Head `b9eb3468bddcae8643e029cc5871325018858073`；`recheck_when`: thread 状态变化或 head 更新。
