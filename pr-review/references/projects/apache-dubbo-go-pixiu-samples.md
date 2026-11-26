<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-go-pixiu-samples Review 补充规则

## Traffic 路由样例

- 路由同时包含 path/prefix 与多个 header 条件时，正例必须发送所有必需 header，负例至少移除一个必需 header 并断言不得命中目标 cluster。只断言正例响应会放过“路径命中但 header 条件被忽略”的实现。
- 修改 `header-conf.yaml` 时，必须确认对应测试不受 `manual` build tag 排除，并从 exact-Head CI 日志看到 `TestHeader*` 实际执行；只运行 `pixiu/conf.yaml` 下的 `TestCanary*` 不覆盖 header 路由。

## CI 基线

- `validated_at`: 2026-08-17
- `validated_ref`: samples `131308d88f843cd62680fbf3decd67f6ab548e21`; Pixiu `c3df76a0fc1652a1dc9da9e910bf83ec91369ed5` 与 `106afed39e3447d64b5f63f6c537e6dbbd4cabc6`
- `applies_to`: `main` 上当前 `.github/workflows/github-actions.yml`
- `toolchain`: Go 1.25.x / Linux amd64
- `recheck_when`: workflow、`igt/Makefile`、traffic 配置、build tag 或 Pixiu 路由实现变化

当前 CI 的 traffic integration 只复制 `pixiu/conf.yaml` 并以 `-tags integration` 运行默认测试；`pixiu_header_test.go` 的 `manual` 测试不会执行。Golang Lint job 显式传入 `--disable errcheck`，不得把本地默认启用的 errcheck 输出描述为当前 CI 门禁失败。
