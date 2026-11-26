<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# oceanbase/powercontext 项目索引

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

已确认仍适用的仓库专属规则与选定协议共同生效；稳定 ID 保留，按表检索相关模块。下表完整列出本次导入规则，分类不改变规则含义。

> **继承的编号冲突**：源文中 R-PC43、R-PC44、R-PC45 各有两个不同标题。保留原规则编号，不将其默认为同一规则；引用时同时写明标题，并使用本索引的唯一 `-01` / `-02` 锚点。原资料中只有编号而无法判明所指的引用，需要核对上下文，不能凭编号推定。

| ID | 规则 / 关键词 | 位置 |
|---|---|---|
| R-PC01 | R-PC01. 仓库与集成布局 | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc01) |
| R-PC02 | R-PC02. 分支门禁（master ruleset） | [CI、构建与依赖](powercontext/ci-build.md#r-pc02) |
| R-PC03 | R-PC03. CI 真实命令与覆盖范围 | [CI、构建与依赖](powercontext/ci-build.md#r-pc03) |
| R-PC04 | R-PC04. Pi 插件风险面 | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc04) |
| R-PC05 | R-PC05. 无网络时的本地验证方式（该仓库 TS 插件） | [平台、工具与环境](powercontext/environment.md#r-pc05) |
| R-PC06 | R-PC06. native code 模块（`src/powercontext/builtin/code/`） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc06) |
| R-PC07 | R-PC07. 宿主 hook 超时/预算：文档写的默认值不可信 | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc07) |
| R-PC08 | R-PC08. `builtin/code/process.py` 批次重试的前进不变式（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc08) |
| R-PC09 | R-PC09. Python 侧的可执行审查方式（裸克隆 + archive + 复用工作区 venv） | [平台、工具与环境](powercontext/environment.md#r-pc09) |
| R-PC10 | R-PC10. CI 作业全集（2026-10-09 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc10) |
| R-PC11 | R-PC11. 缺陷位于 PR 正文（非 Diff 行）时的发布路由 | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc11) |
| R-PC12 | R-PC12. `CHANGES_REQUESTED` 是独立阻塞项，且本仓无人可旁路（2026-10-09 实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc12) |
| R-PC13 | R-PC13. 迁移版本号必须跨 PR 核对（并行 PR 会撞号） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc13) |
| R-PC14 | R-PC14. 「启动期 ensure 加列」必须与离线迁移布局登记保持一致（已实证） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc14) |
| R-PC15 | R-PC15. 新增文档里的版本号必须登记到 `scripts/release_version.py`（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc15) |
| R-PC16 | R-PC16. `e2e/bub` 的跨 Scope 污染判定依赖 Access audit（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc16) |
| R-PC17 | R-PC17. 工作区绑定键的身份语义必须跨宿主核对（本仓已有两套实现） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc17) |
| R-PC18 | R-PC18. Source 持久化 payload 的版本化与历史读回（2026-10-18 实证） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc18) |
| R-PC19 | R-PC19. MySQL 兼容 DDL 里的用户可控标识符必须按 driver paramstyle 转义 `%`（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc19) |
| R-PC20 | R-PC20. zcode 宿主插件的时序预算与「观察顺序」用例（已实证） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc20) |
| R-PC21 | R-PC21. Desktop 的 qualification 记录必须与 bundled contract 对齐（文档引用同样受约束） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc21) |
| R-PC22 | R-PC22. `desktop/` 的文档中英必须同步（README 与 VALIDATION） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc22) |
| R-PC23 | R-PC23. Server metrics 的两个投影边界：readiness 白名单与 snapshot 异常（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc23) |
| R-PC24 | R-PC24. 删除/重命名 `src/powercontext/cli/` 的模块级入口必须扫两份 e2e 消费者（已实证） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc24) |
| R-PC25 | R-PC25. 固定字节哈希的夹具必须在 `.gitattributes` 登记 `text eol=lf`（已实证） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc25) |
| R-PC26 | R-PC26. `code-seekdb` 的 bootstrap 步骤有 300 s 步预算，新增 e2e 不得多进程抢同一嵌入式引擎（已实证） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc26) |
| R-PC27 | R-PC27. 新增的 typed refusal 必须在**全部** CLI 入口收敛，而不只是迁移命令（已实证） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc27) |
| R-PC28 | R-PC28. Desktop 的 OpenAPI→Rust 生成链：`generate:check` 通过 ≠ 生成物可编译 | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc28) |
| R-PC29 | R-PC29. `desktop/` 安装包验收按整句等待用户可见文案，改 `memory-messages.ts` 必须同扫三处 harness（已实证） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc29) |
| R-PC30 | R-PC30. SQLite 支持基线是 3.38，判"pre-3.35 兼容回归"前先核 `SQLiteProfile.open` 守卫（已实证） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc30) |
| R-PC31 | R-PC31. 原子记忆提取证据的去重判据必须按「规范化文本」比较，并区分「提示词载体」与「审计记录」 | [存储、身份与迁移](powercontext/storage-identity.md#r-pc31) |
| R-PC32 | R-PC32. 新增 `builtin`/`images` 模块后必须核 extra 的模块级导入闭包（已被 CI 抓到一次） | [CI、构建与依赖](powercontext/ci-build.md#r-pc32) |
| R-PC33 | R-PC33. Server 托管文件日志：开关来源、单写者锁与「投递失败」计数语义（2026-10-22 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc33) |
| R-PC34 | R-PC34. `cli/system.py` 的宿主可执行文件解析只在 `windows-unit-portability` 的专用 step 里被执行 | [CI、构建与依赖](powercontext/ci-build.md#r-pc34) |
| R-PC35 | R-PC35. 新增 Server 开关：`_BASE_ENVIRONMENT`、`.env.example`、两份 configuration.md 与 provider 前缀白名单必须四向对齐（2026-10-23 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc35) |
| R-PC36 | R-PC36. 评估 harness 提交的 report 绑定 `code_sha`：merge 上游运行时改动后必须重算或在报告内标注（2026-10-23 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc36) |
| R-PC37 | R-PC37. 生命周期边界的 flush 调用预算按 Scope 重置，不按边界累计（2026-10-23 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc37) |
| R-PC38 | R-PC38. `GenerationCache` 的 `PUBLICATION_WINDOW` 裁剪必须带 retained 差集（已实证） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc38) |
| R-PC39 | R-PC39. MiniMax 宿主适配：数据目录四级回落、`enabled` 在读侧与写侧语义不同、安装记录键 = `sha256(data_dir)`（2026-10-23 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc39) |
| R-PC40 | R-PC40. `desktop/` 验收 harness 走显式文件枚举，安装包验收步骤的结论可以直接引用（2026-10-23 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc40) |
| R-PC41 | R-PC41. macOS 诊断进程组的 reap/kill 顺序，与 Desktop macOS CI 的覆盖基线（2026-10-23 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc41) |
| R-PC42 | R-PC42. 用户显式要求时才提交 `APPROVE`，且必须自带范围与 AI 参与声明（2026-10-23 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc42) |
| R-PC43 | R-PC43. `quality` 的 `ty-check` 钩子覆盖 `tests/`：断言 `logging` 的动态 `extra` 字段必须走 `getattr` / `cast`（已实证） | [CI、构建与依赖](powercontext/ci-build.md#r-pc43-01) |
| R-PC44 | R-PC44. Desktop 只有 Windows（`nsis`）与 macOS 打包形态，平台分支判据是「macOS vs 其余」（已实证） | [平台、工具与环境](powercontext/environment.md#r-pc44-01) |
| R-PC45 | R-PC45. `compatibility.json` 的资格记录是「按 Server commit 追加」的数组，并行 PR 撞 `contractSha256` 时要按双记录冲突处理 | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc45-01) |
| R-PC46 | R-PC46. 两处易误判的归因：`locomo_plus` 不经过流式聚合；Desktop 三条红 job 的仓库基线签名（2026-10-24 实测） | [网关、召回与上下文](powercontext/gateway-recall.md#r-pc46) |
| R-PC47 | R-PC47. `pc_atomic_memory_current` 新增列只由启动期 `require_current_schema` 的 ALTER 补齐，不在迁移布局里 | [存储、身份与迁移](powercontext/storage-identity.md#r-pc47) |
| R-PC48 | R-PC48. 「靠 socket 背压制造丢包」的用例在 Windows 上不成立；`windows-unit-portability` 自 #2196 起也跑日志 e2e | [CI、构建与依赖](powercontext/ci-build.md#r-pc48) |
| R-PC49 | R-PC49. third-party action 的 pin 在 `.github/actions/**/action.yml` 里另有一套，dependabot 不管 | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc49) |
| R-PC50 | R-PC50. Atomic Memory 的 `description` 有三条互不相同的语义，动它就是动公开往返契约 | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc50) |
| R-PC43 | R-PC43. 发布类 PR（`chore(release): prepare vX.Y.Z`）的对账基线（2026-10-23/26 两次实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc43-02) |
| R-PC44 | R-PC44. 发布 PR 声称"另一 PR 的能力"时，必须跨 PR 对齐（2026-10-26 实测 #2245 ↔ #2168） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc44-02) |
| R-PC45 | R-PC45. "有改动"但 `headRefOid` 没变 = base 前进导致冲突（2026-10-26 实测 #2245 第三次复审） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc45-02) |
| R-PC51 | R-PC51. 动了 persistence 就必须同改 `release/upgrade-support.json`；判红先算 `managed_digest`（2026-10-27 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc51) |
| R-PC52 | R-PC52. 新增 revision 的 DDL 条数会乘进每个 e2e 用例的 bootstrap 预算（2026-10-27 实测） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc52) |
| R-PC53 | R-PC53. 仓库没有 `pytest-asyncio`：异步用例必须自带 `asyncio.run` 包装（2026-10-27 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc53) |
| R-PC54 | R-PC54. 复算 `managed_digest` 的取数方式；merge result 上的 upgrade-acceptance 红先比对修复提交时间（2026-10-28 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc54) |
| R-PC55 | R-PC55. head 是 merge commit 时必须复算自动合并树，逐文件核对人工解析改动（2026-10-28 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc55) |
| R-PC56 | R-PC56. 提高 prompt 契约版本必须同步重算 pinned evaluation report（2026-10-28 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc56) |
| R-PC57 | R-PC57. `sqlite-*.json` 与 `mysql-*.json` 的资源结构不同：判 DDL 预算只看 mysql，判 layout 漏项只看 sqlite（2026-10-29 实测） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc57) |
| R-PC58 | R-PC58. 收紧 seekdb 的「只读不建库」必须按消费者扫 `runner.plan()` 的可写性，不能只补 Server 启动一处（2026-10-30 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc58) |
| R-PC59 | R-PC59. 新增 OpenAPI operation 后，宿主生成物完备性必须按 **merge 结果** 判定（2026-10-30 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc59) |
| R-PC60 | R-PC60. `Acceptance (oceanbase)` 的 40 分钟步预算由 runner 波动主导，不能按新增 DDL 条数外推（2026-10-30 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc60) |
| R-PC61 | R-PC61. 改了 `openapi/powercontext.yaml` 后，Desktop 产物要按**生成器**判，不是按 `contractSha256`（2026-10-30 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc61) |
| R-PC62 | R-PC62. 契约摘要前移后，`compatibility.json` 必须同时出现同摘要的资格记录（2026-10-30 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc62) |
| R-PC63 | R-PC63. 写进 env 文件的 `POWERCONTEXT_SERVER_DATABASE_URL` 必须用 `Path.as_posix()`（2026-10-30 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc63) |
| R-PC64 | R-PC64. 回复里的「已加进 Windows 专用 job」要按 job 的步骤与事件类型核，而不是按 PR 的 check 名核（2026-10-30 实测） | [平台、工具与环境](powercontext/environment.md#r-pc64) |
| R-PC65 | R-PC65. `cli/app.py` 的命令注册由 dist-info 的 extras 元数据决定，不是源码（2026-10-30 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc65) |
| R-PC66 | R-PC66. 提交进仓库的生成 bundle 必须有「重建后逐字节比对」的门禁，否则会在无关 PR 里漂移（2026-10-31 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc66) |
| R-PC67 | R-PC67. Desktop 的 Unix 诊断链路是「一份共享实现 + 两条平台 job + 一个共用探针」 | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc67) |
| R-PC68 | R-PC68. 新增一个公开 OpenAPI 操作要同步 **五类** 消费方，其中两类不失败在 Python 侧 | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc68) |
| R-PC69 | R-PC69. 发布说明里的每条能力必须能用 `git ls-tree` 在本 head 上点到（2026-11-02 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc69) |
| R-PC70 | R-PC70. 迁移链只能往 head 之后追加；改已登记 revision 的 `down_revision` 会让已 stamp 的库跳过新 revision（2026-11-02 实测） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc70) |
| R-PC71 | R-PC71. JS 宿主 bundle 的「重建比对」可在 exact head 本地复现；判等必须做 LF 归一化（2026-11-03 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc71) |
| R-PC72 | R-PC72. 「release-aware」调用必须对**已发布版本的 CLI** 验证，分支 CI 永远看不到它（2026-11-03 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc72) |
| R-PC73 | R-PC73. extras 漏声明只能由「只装目标 extras」的安装用例发现（2026-11-03 实测 #2388） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc73) |
| R-PC74 | R-PC74. `code-seekdb` 分片 0 的 30 分钟取消是基线现象，归因前先查 base 提交的同名 job（2026-11-03 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc74) |
| R-PC75 | R-PC75. Desktop 资格记录要按 `serverCommit` 的 openapi 摘要反查，而不是只看摘要字符串出现（2026-11-03 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc75) |
| R-PC76 | R-PC76. Codex 与 Claude Code 的 hook 实现是逐行同源的，改一处文档必须扫另一处（2026-11-03 实测） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc76) |
| R-PC77 | R-PC77. 加密准入类修复要单独证明「测试能检出过滤器被删」（2026-11-03 实测 #2429） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc77) |
| R-PC78 | R-PC78. 三个宿主的凭据处理不同源：表格里「某行没写脱敏」不是省略，而是事实（2026-11-03 实测 #2446） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc78) |
| R-PC79 | R-PC79. macOS DMG 打包步骤是本仓最拥挤的争用点：三个 open PR 同改一段，且「恢复动作」必须自己可失败（2026-11-04 实测） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc79) |
| R-PC80 | R-PC80. `/openapi.json` 不在 `_PUBLIC_PATHS`：CLI 侧的「契约探测」在 enforced 部署上恒 401（2026-11-05 实测 #2495） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc80) |
| R-PC81 | R-PC81. 根级 opaque 豁免必须逐个 key 白名单：`before_release` 没有 `_REQUEST_FIELDS` 这层过滤（2026-11-05 实测 #2486） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc81) |
| R-PC82 | R-PC82. 核销「加密回执跨目标复用」：target 绑定是 `sha256([endpoint, protocol])`，对照必须改同一 profile 的 endpoint（2026-11-05 实测 #2429） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc82) |
| R-PC83 | R-PC83. 改 `desktop.yml` 的 macOS 打包步骤必须同步 `tests/test_ci_pipeline.py`（2026-11-05 实测 #2306） | [CI、构建与依赖](powercontext/ci-build.md#r-pc83) |
| R-PC84 | R-PC84. 新增 e2e 用例是否真在 OceanBase 上跑，要按「fixture skip 条件 + OB 作业显式清单」两处对账（2026-11-05 实测 #2498） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc84) |
| R-PC85 | R-PC85. 能力探针必须与生产语句同形：字面量 options 通过不代表绑定参数可用（2026-11-05 实测 #2498） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc85) |
| R-PC86 | R-PC86. 窗口兄弟项的相关性门槛要和投影输入同源：`atomic_memory_embedding_input(kind, text)` 不含 description（2026-11-05 实测 #2489） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc86) |
| R-PC87 | R-PC87. `compatibility.json` 记录的 `evidence` 锚点要单独校验；`desktop/VALIDATION.md` 最容易被整文件 ours 解冲突（2026-11-06 实测 #2457） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc87) |
| R-PC88 | R-PC88. master 的 `gateway/crates/pc-gateway-core/src/lifecycle.rs` 缺 license header ⇒ `CI preflight` 红 ⇒ **全部 suite job skip**（2026-11-06 实测） | [CI、构建与依赖](powercontext/ci-build.md#r-pc88) |
| R-PC89 | R-PC89. `api.d.ts` 是否真的重生成：可在无 pnpm 环境下逐字节重建（2026-11-06 实证 #2270） | [平台、工具与环境](powercontext/environment.md#r-pc89) |
| R-PC90 | R-PC90. `create_app(middleware=...)` 传入的中间件位于两层 `BaseHTTPMiddleware` **之内**：不发送响应就会变成 500（2026-11-06 实测 #2512） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc90) |
| R-PC91 | R-PC91. 新增的回归步骤要放在「能让它失败的路径所命中的 suite」里（2026-11-06 实测 #2517） | [平台、工具与环境](powercontext/environment.md#r-pc91) |
| R-PC92 | R-PC92. 改「已有」OpenAPI 参数的 schema 也会穿透到 Dify 的 `contract.json` 与工具入参（2026-11-07 实测 #2502） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc92) |
| R-PC93 | R-PC93. 网关的 listener 门禁 ≠ 端口收口：`PC_GATEWAY_API_KEY` 只覆盖 `/gateway/*`（2026-11-07 实测 #2523） | [CI、构建与依赖](powercontext/ci-build.md#r-pc93) |
| R-PC94 | R-PC94. 三个摘要/资格位置会在 dirty 时同时冲突，且两侧取值都不是合并结果树的值（2026-11-07 实测 #2270） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc94) |
| R-PC95 | R-PC95. `CI preflight` 红在 `Check License Header` 且日志含 `license-eye: command not found` ⇒ 工具安装问题，不是本 PR 引入（2026-11-07 实测 #2526） | [CI、构建与依赖](powercontext/ci-build.md#r-pc95) |
| R-PC96 | R-PC96. `e2e-harness.yml` 的 acceptance：分步 `timeout-minutes` 之和可能超过作业上限，`if: always()` 的门禁步骤因此永不执行（2026-11-07 实测 #2526） | [CI、构建与依赖](powercontext/ci-build.md#r-pc96) |
| R-PC97 | R-PC97. 网关 Rust 代码的行为证据归属：`gateway-validation / check` 跑 `cargo test --workspace`，Python e2e 作业自带 cargo，但本机 Windows 跑 loopback 用例会误报（2026-11-07 实测 #2506/#2523） | [平台、工具与环境](powercontext/environment.md#r-pc97) |
| R-PC98 | R-PC98. 判「迁移手册登记完整性」不能按 `schemas/sqlite.json` 反查；`managed_digest` 可在裸克隆上直接复算（2026-11-07 实测 #2296） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc98) |
| R-PC99 | R-PC99. 基于旧 merge-base 的 PR 会把「已合入 master 的修复」显示成本 PR 新增；两侧取值不同时会覆盖 master 更严格的版本（2026-11-07 实测 #2518） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc99) |
| R-PC100 | R-PC100. `migrations/pinned.py::_PinnedConnection` 不是完整 `AsyncConnection`：新代码取 `connection.sync_engine` 会打穿历史迁移路径（2026-11-08 实测 #2498） | [平台、工具与环境](powercontext/environment.md#r-pc100) |
| R-PC101 | R-PC101. OceanBase `SHOW PARAMETERS` 在 `--skip-column-names` 下的列位固定：`name`=5、`value`=7（awk 1-based）（2026-11-08 实测 #2526/#2498/#2518） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc101) |
| R-PC102 | R-PC102. CI 步骤上限必须 ≥ 每片用例数 × 逐用例超时：改分片数时要重算，不能只换实测均值（2026-11-08 实测 #2515） | [CI、构建与依赖](powercontext/ci-build.md#r-pc102) |
| R-PC103 | R-PC103. 本机无法为 `pc-gateway-core` 提供行为证据：Windows 缺 UDS、WSL 缺链接器（2026-11-09 实测 #2451） | [平台、工具与环境](powercontext/environment.md#r-pc103) |
| R-PC104 | R-PC104. 判「分步上限 ≥ 逐用例超时之和」时分母要用实际收集数，不能取 durations 文件的键集（2026-11-09 实测 #2515） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc104) |
| R-PC105 | R-PC105. `evaluation/memory/**/tests` 能否被执行由 `testpaths` + `Makefile::evaluation-unit-test` 两处枚举共同决定，缺一处等于从未跑过（2026-11-09 实测 #2529） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc105) |
| R-PC106 | R-PC106. Issue 前提核验：grep 断言须同大小写同范围重跑，Allowed 文件集必须覆盖 Observable behavior（2026-11-09 实测 #2559/#2560/#2561） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc106) |
| R-PC107 | R-PC107. `capture()` 的 `scope.lock` span 拓扑是 e2e 契约：把取锁移进 `memory.capture` 之内会静默打红（2026-11-10 实测 #2567） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc107) |
| R-PC108 | R-PC108. `TopicMemoryWorkBlock` 没有 `stage` 字段：`classify_block_code` 只有 `stage == "topic_memory"` 才出诊断（2026-11-10 实测 #2568） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc108) |
| R-PC109 | R-PC109. Source plugin 的 4xx 不会变成 `REJECTED`：服务端 409 会穿到 `business()` 把 collect 实例置 `failed`（2026-11-10 实测 #2546） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc109) |
| R-PC110 | R-PC110. 改 `openapi/powercontext.yaml` 等于改 Desktop 契约摘要，并连带作废真机资格记录（2026-11-10 实测 #2580 / #2553） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc110) |
| R-PC111 | R-PC111. OceanBase 迁移作业预算：判据是 `ceil(收集数/分片数) × (逐用例超时+10) + 190`，收集数要实跑（2026-11-10 实测 #2515 / #2526） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc111) |
| R-PC112 | R-PC112. `scope.lock` 必须是 capture application span 的兄弟节点，位置由 `_capturing()` 的两个上下文管理器顺序决定（2026-11-10 实测 #2567） | [网关、召回与上下文](powercontext/gateway-recall.md#r-pc112) |
| R-PC113 | R-PC113. Memory 契约门禁在 JS 与 Python 两侧各有一份 fixture，修一侧不会让 `dsh-package` 转绿（2026-11-12 实测 #2270 head 95e0a357） | [CI、构建与依赖](powercontext/ci-build.md#r-pc113) |
| R-PC114 | R-PC114. `desktop/scripts/generate.mjs --check` 可在本机全量复核 api.d.ts / operations.ts / operations.json（2026-11-12 实测 #2270 head 8faa8345） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc114) |
| R-PC115 | R-PC115. 三个宿主的 bundle 在 pnpm 10.18.3 下与 CI（pnpm 11.13.1）重建结果字节相同（2026-11-12 实测 #2270 head 8faa8345） | [CI、构建与依赖](powercontext/ci-build.md#r-pc115) |
| R-PC116 | R-PC116. 「head 自洽」与「合并结果自洽」是两个判据，且两者对摘要的影响方向相反（2026-11-13 实测 #2270 head eb6a9dc7） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc116) |
| R-PC117 | R-PC117. 归档镜像里复核生成物：`generate_api.py --check` / `generate_js_operations.py --check` 直接可跑；`ty check` 不能用于定级（2026-11-13 实测 #2516 / #2244） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc117) |
| R-PC118 | R-PC118. `git show "refs/pr/<N>:<path>"` 在 Git Bash 下会被 MSYS 把冒号翻成分号（2026-11-13 实测 #2471） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc118) |
| R-PC119 | R-PC119. `tests/e2e/plugin_server.py` 只按 POSIX 启动：本机跑插件 e2e 必须走 WSL，且 venv 元数据要与 head 同版本（2026-11-15 实测 #2616） | [平台、工具与环境](powercontext/environment.md#r-pc119) |
| R-PC120 | R-PC120. embedding profile 切换的「journal transition」机制：OceanBase 目前没有记录路径（2026-11-16 实测 #2615） | [平台、工具与环境](powercontext/environment.md#r-pc120) |
| R-PC121 | R-PC121. 两类「master 基线红」，归因前先在这两个位置对账（2026-11-16 实测 #2620） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc121) |
| R-PC122 | R-PC122. 两条本仓专属的判读手法：`generate_integration_lifecycle.py --check` 需要 `.git`；`managed_digest` 必须三处同时命中才算方法可信（2026-11-17 实测 #2628 / #2647） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc122) |
| R-PC123 | R-PC123. 迁移/门禁的「接受面」扩到新资源文件时，派生校验和必须同步扩容（2026-11-17 实测 #2674） | [CI、构建与依赖](powercontext/ci-build.md#r-pc123) |
| R-PC124 | R-PC124. 「新增 real-host e2e 作业」的验收判据：先核作业是否真跑，再核它与既有 suite 的覆盖分工（2026-11-17 实测 #2685 / #2686） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc124) |
| R-PC125 | R-PC125. 「自动 prompt 隐私」共享规则只认裸键名：带前缀的键（`DB_PASSWORD=`、`db-password=`、`X-Api-Key:`）不会被脱敏（2026-11-18 实测 #2703） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc125) |
| R-PC126 | R-PC126. 并发迁移 PR 的 revision ID 与合并图取证 | [存储、身份与迁移](powercontext/storage-identity.md#r-pc126) |
| R-PC127 | R-PC127. Topic 校验和定义变更会连「已完成」的 journal 一起拒绝；本仓 PR 整轮 run 被取消时 `Upgrade release gate` 必红（2026-11-19 实测 #2674 head 88f9a300） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc127) |
| R-PC128 | R-PC128. 迁移命名门禁上线前必须枚举在飞迁移 PR：`vX_Y_Z_prNNNN` 会被新的 `000` 政策判红（2026-11-19 实测 #2713 / #2674） | [CI、构建与依赖](powercontext/ci-build.md#r-pc128) |
| R-PC129 | R-PC129. `make check` 的 prek/ty 挂在 `workflow-actions-check` 下；`pretty-format-json` 覆盖 `desktop/**`（2026-11-20 实测 #2728） | [CI、构建与依赖](powercontext/ci-build.md#r-pc129) |
| R-PC130 | R-PC130. 新增 `__init__.py` 是 license 门禁最常见的漏点；`CI preflight` 红等于全 suite 零覆盖（2026-11-21 实测 #2546） | [CI、构建与依赖](powercontext/ci-build.md#r-pc130) |
| R-PC131 | R-PC131. `schema_release.py check --base-ref` 与"PR 实际执行树"不是同一棵树：旧 base 的 PR 会把已冻结 revision 判成新增（2026-11-21 实测 #2541） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc131) |
| R-PC132 | R-PC132. PR 面里出现的 hunk 可能已由 master 合入；判「本 PR 新增 / 与在飞 PR 冲突」前先比 blob（2026-11-22 实测 #2727） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc132) |
| R-PC133 | R-PC133. Rust 侧 `-D warnings` + 固定工具链：新增 `x % n == 0` 直接让 gateway-validation 红，且 Tests 被 skipped（2026-11-22 实测 #2775） | [CI、构建与依赖](powercontext/ci-build.md#r-pc133) |
| R-PC134 | R-PC134. 宿主包装标签有权威全集：`capture_ownership/host.py` 与 workbuddy hook 的四个标签，判"是否识别宿主提示块"以它们为准（2026-11-23 实测 #2771） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc134) |
| R-PC135 | R-PC135. 新增 `x-powercontext-scope-mode: current` 操作必须同步 Codex 插件 `_CURRENT_OPERATIONS`；参数化用例总带 `scope_id` 会掩盖缺项（2026-11-23 实测 #2725） | [宿主、并发与生命周期](powercontext/hosts-lifecycle.md#r-pc135) |
| R-PC136 | R-PC136. gateway 的 protocol/types crate 可在 Windows 跑单测与 clippy；只 archive `gateway/` 会让协议套件假红（2026-11-23 实测 #2792） | [CI、构建与依赖](powercontext/ci-build.md#r-pc136) |
| R-PC137 | R-PC137. `contents` raw 接口对大文件会返回空/EOF，取 blob 要走 `git/blobs`；作者回复里的摘要值只对当时的 head 成立（2026-11-24 实测 #2728 / #2765） | [审查、契约与公共行为](powercontext/review-contracts.md#r-pc137) |
| R-PC138 | R-PC138. 门禁级红的两类新形态：`ty` 对 dict 字面量 `**` 展开的推断、license-eye 判不了 `.txt`；install.sh 与 gateway 分发契约（2026-11-24 实测 #2816 / #2811） | [CI、构建与依赖](powercontext/ci-build.md#r-pc138) |
| R-PC139 | R-PC139. 所有权写入的两套幂等键：审批重试 409 的成因与判定（2026-11-24 实测 #2787） | [存储、身份与迁移](powercontext/storage-identity.md#r-pc139) |
| R-PC140 | R-PC140. 网关的"跳过召回"要分成 prepare / 注入 / 证据三步判；工具续写不注入会丢掉整回合的召回块（2026-11-24 实测 #2792） | [网关、召回与上下文](powercontext/gateway-recall.md#r-pc140) |
| R-PC141 | R-PC141. 旧上游 URL 变量转为「启动致命」后，`var_os` 语义让测试里的「置空串」变成启动失败（2026-11-25 实测 #2630 / #2815） | [网关、召回与上下文](powercontext/gateway-recall.md#r-pc141) |
| R-PC142 | R-PC142. `TurnKind::Empty` 与 `RecallPolicy::allows_prepare` 是两套语义：判「某尾部形态会不会丢召回」必须同时读两处（2026-11-26 实测 #2792 head ac477151） | [CI、构建与依赖](powercontext/ci-build.md#r-pc142) |
