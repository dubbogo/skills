<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# arana-db/kiwi Review 补充规则

## OpenRaft snapshot

- OpenRaft 0.9 会把 `RaftStateMachine::get_snapshot_builder()` 返回的 builder 移入独立任务；审查时必须按它与后续 `apply()` 并发执行处理。
- 只允许在固化 collector state 和创建 RocksDB checkpoint 时阻塞 `apply()`；tar 打包、内存聚合和 snapshot 同步落盘不得继续持有同一 guard。
- 分别验证内容一致性与 current-snapshot publication/install 串行化：checkpoint 后阻塞慢阶段时，`apply()` 必须仍能前进，旧 builder 也不能覆盖稍后 install 或发布的 snapshot。

## Redis 8.8.1 二进制 glob

- Matcher 必须按字节工作，覆盖空 pattern/输入、单个或连续 `*`、`?`、字符类、转义和非 UTF-8；不得仅凭通用 glob 直觉推导空输入语义。
- Redis 8.8.1 `stringmatchlen_impl()` 的主循环要求 pattern 和 input 同时非空；命令层又可能只对精确单个 `*` 做旁路。因此 `MATCH *`、`MATCH **`、`MATCH ***` 对空 key/field/member 的结果必须分别用 exact Redis raw RESP 验证，不能假定连续星号等价。若 Kiwi 有意采用不同语义，必须登记为显式兼容差异。
- 以 Base 和 Redis 8.8.1 命令级行为为 oracle；除 matcher 单测外，分别用 KEYS、SCAN、HSCAN、SSCAN 的 RESP 测试覆盖空 key、field 和 member。

## RocksDB SCAN cursor

- 不得用“从 MetaCF 起点重新迭代并 `skip(ordinal)`”恢复 SCAN cursor：小 `COUNT` 下完整遍历会退化为 O(N²)，删除或 TTL 清理 cursor 之前的记录还会使全程存活的后续键被永久跳过。
- cursor 应恢复到下一条 encoded key 并使用 RocksDB seek；测试同时覆盖 iterator step 数、删除已返回键、实际 TTL 清理和跨 instance 边界。
- cursor 位布局必须与 `db-instance-num` 等配置上限形成同一合同。若高位只能表示固定数量的 instance，配置验证和 Storage 构造必须拒绝超限值，并测试最大合法值及首个非法值。

## Stacked PR

- stacked PR 必须分别给出“当前 PR 相对直接 base 的增量结论”和“整个 stack 的可合并结论”。增量无 P0/P1 不代表可绕过被依赖 PR 的阻断问题；base 更新后须在新 Head 上重新确认 Diff、checks 和组合接口。

## MetaCF 类型分派

- String 与集合 meta 共用 `BaseKey`，必须先按 value 首字节的 `DataType` 分派到唯一 parser，禁止依次试解析。`ParsedStringsValue::new` 只校验合法 tag，集合 meta 又共享 `ctime/etime`；`ParsedBaseMetaValue` 也可能接受更长的 List 布局。
- 集合解析后再检查 `!stale && count > 0`；回归测试至少覆盖 `count == 0` 的逻辑空集合和使用独立布局的 List。

## 新增 DataType / Column Family 的闭环

- 新增 `DataType` 或 Column Family 时，不能只更新 enum、CF 配置和主读写路径；固定扫描 binlog 的 user-key/slot 推导、`SCAN TYPE` 名称解析、`RANDOMKEY`/KEYS/TYPE 等 keyspace 枚举、统计、TTL、compaction filter、snapshot/manifest 和所有 CF 列表。每个消费者都要有只包含新类型的回归用例，避免旧类型混合数据掩盖漏分派。
- 集群路径若仍依赖节点本地持久化身份或无法在 Raft apply 时重编码，生产配置不得绕过门禁。non-strict `xfail` 只能记录未实现合同，不能作为开放已知 failover 数据不可见或可被 compaction 删除路径的验证证据。

## RocksDB 测试 hook 与 FFI callback

- 多个并行测试共享全局 compaction/snapshot gate 时，必须用统一串行 guard 或按实例隔离，禁止在持有 registry mutex 时用断言拒绝第二个安装；否则一次测试 panic 会毒化全局锁并污染其他测试。
- RocksDB comparator、compaction filter 等 FFI callback 中不得对测试 hook 的锁使用会 panic 的 `unwrap`/`expect`。测试状态损坏时应禁用 hook 或走无 panic 的保守路径，并在 ASAN/LSAN/TSAN 的默认并行测试模式下验证。

## 磁盘 schema 与 manifest 升级

- 新增 Column Family 或外置 manifest 时，必须用 Base 二进制创建非空普通数据，再由 Head 原地打开并读回；同时验证首次启动失败后的旧版本回滚。不能在创建新 CF、改变磁盘 schema 后才因缺 manifest 拒绝旧库。
- 对 Base 不可能产生的新类型，可设计显式、原子的首次 bootstrap；只有已经存在该新类型数据但身份文件丢失或损坏时才 fail closed。空库单测和人工传入 `db_has_entries=true` 不能替代真实升级测试。

## 仓库审查口径

- 测试模块局部使用 `#[allow(clippy::unwrap_used)]` 符合本仓库规则，不得按生产代码的 unwrap 禁令报告。
- lossy UTF-8 等兼容性缺口若仅保持 Base 行为，且当前 Diff 和 PR 描述未扩大承诺，不归责于当前 PR；保留证据并拆分后续任务。

## 可执行文档中的本地验证命令

- `validated_at`: 2026-07-31
- `validated_ref`: Base `cbc28958f261ae049d67a8b4a9d904d794b37726` / Head `c1f0f9da1aa50d833d1bc49d9dbb98ebea1b7a71`
- `applies_to`: `docs/development.md`、`CHANGELOG.md`、Python 集成测试和 sample-config 使用说明
- `recheck_when`: `tests/python/conftest.py`、`tests/run_python_integration.sh`、`tests/Makefile`、默认端口或 sample-config CLI 行为变化

- `make standalone` 默认启动 `127.0.0.1:7379`，而 `tests/python/conftest.py` 当前固定连接 `6379`，且未设置 `KIWI_TEST_REQUIRE_SERVER=1` 时连接失败会 skip。文档不得把 `make standalone` 与裸 `make -C tests test-python` 组合成有效集成测试；应使用 `tests/run_python_integration.sh`，或显式对齐端口并强制目标服务不存在时失败。
- `kiwi --sample-config` 和 `kiwi --full-sample-config` 只向 stdout 输出内容。文档若要求随后编辑配置文件，必须给出重定向到具体文件以及用 `--config` 启动的完整命令，不能声称 CLI 自行创建了文件。

## Runtime baseline CI 显式命令契约

- `validated_at`: 2026-07-31
- `validated_ref`: PR #403 Head `c67828b08ec26915209c71af5a4b89c93ec2778f`
- `applies_to`: `.github/workflows/ci.yml`、`Makefile`、`tools/runtime-baseline/tests/ci_contract_test.rs`
- `recheck_when`: 修改 `cargo-clippy` job、`make lint` 或 runtime-baseline 的 CI 命令

- `stable_platform_matrix_verifies_runtime_baseline_explicitly` 按 YAML step 精确查找 `cargo clippy -p runtime-baseline --all-targets -- -D warnings -D clippy::unwrap_used`。即使 `make lint` 已扩展为 workspace/all-features/all-targets，也不能删除该显式 step，除非同时有意修改并验证这份契约。
- CI 契约变更必须先运行 `cargo test -p runtime-baseline --test ci_contract_test stable_platform_matrix_verifies_runtime_baseline_explicitly -- --exact`，再执行 `cargo test -p runtime-baseline --all-targets`；只跑 Clippy 不能发现 workflow 结构回归。

## 生产进程关闭生命周期

- `validated_at`: 2026-07-31
- `validated_ref`: `main@3164d4a0fead580ac6701fb0595e50193c4edff9`
- `applies_to`: `src/server/src/main.rs`、`src/common/runtime/manager.rs`、`src/common/runtime/storage_server.rs`、`src/storage/src/storage.rs`、`src/raft/src/node.rs`、生产容器入口
- `recheck_when`: server startup/退出信号、RESP/Raft gRPC serve、append-log bridge、RuntimeManager stop、StorageServer/Storage shutdown 或 OpenRaft 生命周期发生变化

- 不能用 `Runtime::shutdown_timeout`、runtime drop 或进程退出本身证明优雅关闭。生产入口必须保留 RESP、Raft gRPC、append-log drain、StorageServer、Storage 后台任务和 OpenRaft 的 cancellation owner/`JoinHandle`，并逐项等待或记录有界 fallback。
- 审查关闭顺序时固定检查“停止 admission -> 在共享 deadline 内 drain 已接受请求 -> 停止 Raft/gRPC -> 停止 Storage/background task -> 最后关闭 runtime”。先关闭 storage runtime、同时让 network 继续接收请求会破坏 drain 合同。
- Linux/容器路径必须同时验证 SIGINT 和 SIGTERM。关闭失败、task panic 或 deadline 超时必须传播到进程退出状态，不能只记录 warning 后返回成功。
- graceful stop 与 crash recovery 分开验证：`kill -9`/abort 不会运行退出钩子，持久化正确性必须由 RocksDB/OpenRaft recovery 和 fault-injection 测试证明；不得通过每次退出强制 snapshot 掩盖恢复缺陷。

## INFO 与状态发现接口

- `validated_at`: 2026-08-01
- `validated_ref`: `main@3164d4a0fead580ac6701fb0595e50193c4edff9`
- `applies_to`: `src/cmd/src/admin.rs`、命令表注册、server/runtime/storage/Raft 状态 provider、Redis 8.8.1 compatibility tests
- `recheck_when`: `INFO`/`CONFIG`、build identity、监听地址、client/runtime/storage/Raft metrics 或 Redis compatibility profile 发生变化

- `INFO`、健康状态和其他发现接口中的版本、OS、PID、端口、uptime、mode、cluster role/leader、storage/Raft 指标必须追到真实生产来源；硬编码占位值即使格式正确，也属于客户端可见的错误行为。
- 审查 `INFO` 时必须在非默认端口、Linux 进程和启用/禁用 Raft 两种模式验证；至少检查 PID、port、OS/arch、uptime 单调性、standalone/cluster mode、leader/follower 和重启后的状态变化。
- section 参数、默认 section 集合、未知 section、字段格式及 RESP2/RESP3 返回类型以 exact Redis 8.8.1 raw Oracle 为准。Kiwi 暂无来源的字段不得用看似真实的常量补齐；应按兼容合同输出真实零/状态或省略，并为 `kiwi_*` 扩展字段建立文档。
- 状态 provider 必须生成一次有界 snapshot，不得因单次 `INFO` 触发全库扫描、无界 RocksDB property 查询、网络 RPC、敏感信息泄漏或攻击者可控的 metrics label 基数。
