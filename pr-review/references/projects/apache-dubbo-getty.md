<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-getty Review 补充规则

## 仓库身份与 checkout

- `gh repo clone apache/dubbo-getty` 会保留 `origin=https://github.com/apache/dubbo-getty.git`，并添加 `upstream=https://github.com/AlexStocks/getty.git`。在该镜像中执行 PR checkout 时必须使用 `gh pr checkout <PR_NO> -R apache/dubbo-getty`；不带 `-R` 时 `gh` 可能解析到 upstream，并错误报告 PR 不存在。checkout 后仍需核对 `origin`、实时 Head SHA 和干净工作区。

## 测试与平台边界

- 仓库最低 Go 版本为 1.23；当前 Ubuntu CI 的代码门禁依次执行 `make fmt`、`make test` 和 `make lint`。Read-Only 审计不能在主证据副本运行会改写源码的 `make fmt`，应使用 exact Head CI 或独立副本验证。
- `client_test.go` 中的 WSS 测试使用绝对路径 `/tmp/server.crt` 和 `/tmp/server.key`。在 Windows 执行全仓测试前必须确认这些路径被隔离在审查镜像内；无法保证时，优先使用 WSL/Linux 或核对 exact Head 的 Ubuntu CI，避免向当前盘根目录写测试文件。

## Session 触发的并发重连与连接池上限

- `validated_at`: 2026-08-16
- `validated_ref`: `master@5e9c87f4ba5f324b1d9e8b7562fd00226303d5e4`, PR #142 Head `1994e7cf2f5dd40d24da00e3d7a9b587f45dc18f`
- `applies_to`: `client.go` 的 `runReconnect`、`reConnect`、`connect`、`ssMap`，以及 `session.go` 的关闭回调重连路径
- `toolchain`: WSL `go1.25.1 linux/amd64`
- `recheck_when`: reconnect single-flight、连接池计数/插入临界区或 Session 关闭触发方式发生变化

Session 关闭改为异步触发 reconnect 后，必须保证同一 client 最多运行一个补池 loop，或把“检查池大小 + 建连 + 插入”置于能够严格守住 `ClientOptions.number` 的协调机制下。两个 reconnect loop 可在 `sessionNum()` 均为 0 时同时进入 `newSession`，随后分别插入 `ssMap`；固定 `WithConnectionNumber(1)` 并在 `newSession` 设置双 worker barrier 的探针会得到 `len(ssMap)==2`。仅验证 Close 不死锁、backoff 可取消和 close 后 no-op，不能证明并发补池仍遵守上限。
