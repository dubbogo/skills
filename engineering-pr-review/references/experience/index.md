<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 诊断经验索引

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

先用风险、错误、符号或条目标题检索，再读取目标条目与必要上下文。分组只是检索导航，不表示其他分类不适用；不要整库加载或将一次历史故障变为强制门禁。`EXP` 顺序仅标记本次导入，后续新增用新 ID，不重排既有 ID。

| 条目 | 关键词 / 标题 | 位置 |
|---|---|---|
| exp-001 | 跨平台原生编译缓存 | [审查、契约与公共行为](review-contracts.md#exp-001) |
| exp-002 | GitHub 行内评论写入 | [审查、契约与公共行为](review-contracts.md#exp-002) |
| exp-003 | Diff 完整性计数与非 ASCII 路径 | [CI、构建与依赖](ci-build.md#exp-003) |
| exp-004 | 评论窗口内的 same-tree Head 变更 | [审查、契约与公共行为](review-contracts.md#exp-004) |
| exp-005 | 发布前远端分支租约 | [审查、契约与公共行为](review-contracts.md#exp-005) |
| exp-006 | 公开类型与指标状态演进 | [审查、契约与公共行为](review-contracts.md#exp-006) |
| exp-007 | 递归解析器的资源边界 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-007) |
| exp-008 | Rust exact 测试命令 | [审查、契约与公共行为](review-contracts.md#exp-008) |
| exp-009 | 多阶段异步请求的统一超时预算 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-009) |
| exp-010 | 审查报告的证据边界 | [审查、契约与公共行为](review-contracts.md#exp-010) |
| exp-011 | 审查收敛与噪声度量（外部来源，未在本仓复现） | [审查、契约与公共行为](review-contracts.md#exp-011) |
| exp-012 | 检出能力依赖模型版本与上下文完整性（外部来源，未在本仓复现） | [网关、召回与上下文](gateway-recall.md#exp-012) |
| exp-013 | Shutdown 与资源发布的同锁门禁 | [CI、构建与依赖](ci-build.md#exp-013) |
| exp-014 | 配置互换测试的夹具可区分性 | [审查、契约与公共行为](review-contracts.md#exp-014) |
| exp-015 | 组合 Writer 的字节计数语义 | [审查、契约与公共行为](review-contracts.md#exp-015) |
| exp-016 | GitHub Actions 中 Go 工具的锁文件门禁 | [CI、构建与依赖](ci-build.md#exp-016) |
| exp-017 | GitHub Actions OIDC 凭据隔离 | [审查、契约与公共行为](review-contracts.md#exp-017) |
| exp-018 | 无 check 模式格式化器的只读门禁 | [CI、构建与依赖](ci-build.md#exp-018) |
| exp-019 | PowerShell 到 WSL 的多行脚本传输 | [平台、工具与环境](environment.md#exp-019) |
| exp-020 | Markdown 控制面合同的可执行验证 | [审查、契约与公共行为](review-contracts.md#exp-020) |
| exp-021 | 离线 Git 证据与状态迁移门禁 | [CI、构建与依赖](ci-build.md#exp-021) |
| exp-022 | 潜在合并树的本地精确预检 | [审查、契约与公共行为](review-contracts.md#exp-022) |
| exp-023 | WSL Cargo 继承宿主 target-dir | [平台、工具与环境](environment.md#exp-023) |
| exp-024 | 仓库级 Agent Skills 的跨工具路径与校验 | [平台、工具与环境](environment.md#exp-024) |
| exp-025 | Agent 工具的工作目录漂移与镜像污染 | [审查、契约与公共行为](review-contracts.md#exp-025) |
| exp-026 | Force push 后的审批与 CI 证据失效（ruleset 门禁） | [CI、构建与依赖](ci-build.md#exp-026) |
| exp-027 | 评论正文含反引号时禁用 bash 内嵌字符串提交（正文会被命令替换截损） | [审查、契约与公共行为](review-contracts.md#exp-027) |
| exp-028 | 共享裸克隆的 master ref 会陈旧，「master 现在」类结论必须先强刷 | [审查、契约与公共行为](review-contracts.md#exp-028) |
| exp-029 | 矩阵 job 单版本失败不得直接归因 PR | [审查、契约与公共行为](review-contracts.md#exp-029) |
| exp-030 | 对称修复必须逐消费者核验（序列化面不止两个） | [审查、契约与公共行为](review-contracts.md#exp-030) |
| exp-031 | 库行为假设类 Finding 先读实现再定级 | [审查、契约与公共行为](review-contracts.md#exp-031) |
| exp-032 | 并发审查身份下先拉线程表再决定发布 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-032) |
| exp-033 | 平台专属失败必须先分辨「产品缺陷」与「测试夹具平台差异」 | [审查、契约与公共行为](review-contracts.md#exp-033) |
| exp-034 | 文档里的全局不变量要按「记录族」逐族核验消费者的覆盖面 | [审查、契约与公共行为](review-contracts.md#exp-034) |
| exp-035 | 已 resolved 线程的「残留形式」应新开评论并交叉引用，不复活原线程 | [审查、契约与公共行为](review-contracts.md#exp-035) |
| exp-036 | 「已接入 CI、不再跳过」的声明要同时核三步，且以 CI 运行结果为准 | [CI、构建与依赖](ci-build.md#exp-036) |
| exp-037 | 通知驱动增量审查的「自我噪声」（updated_at 变化 ≠ 有新外部活动） | [审查、契约与公共行为](review-contracts.md#exp-037) |
| exp-038 | gh CLI 凭据失效时用 git credential 取回同一账号 token（不改动任何凭据状态） | [网关、召回与上下文](gateway-recall.md#exp-038) |
| exp-039 | `pr view --json baseRefOid` 不是目标分支当前 tip | [审查、契约与公共行为](review-contracts.md#exp-039) |
| exp-040 | 无 git 传输时复算三方合并：`base.sha` 不是 merge-base，`merge_commit_sha` 会陈旧 | [平台、工具与环境](environment.md#exp-040) |
| exp-041 | 分平台失败先用同镜像 Base 树比对失败集合 | [审查、契约与公共行为](review-contracts.md#exp-041) |
| exp-042 | 「布局校验器不再认识该库」类结论先核 bundle 覆盖面与可达版本 | [审查、契约与公共行为](review-contracts.md#exp-042) |
| exp-043 | 用「事件同步」替换定时等待后，兜底仍由被测进程自身的请求超时决定 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-043) |
| exp-044 | 符号链接后接 `..` 的 realpath 差异只在 POSIX 成立 | [审查、契约与公共行为](review-contracts.md#exp-044) |
| exp-045 | 进程组 kill ≠ 覆盖 reader join：POSIX 子进程监督的 deadline 会被 `setsid` 后代绕过 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-045) |
| exp-046 | base 上已红的 job：「同一 job 红」不等于「同一原因红」，必须比对失败签名 | [审查、契约与公共行为](review-contracts.md#exp-046) |
| exp-047 | 产品测试对「工作树字节」做哈希时，先核 `.gitattributes` 与检出配置 | [存储、身份与迁移](storage-identity.md#exp-047) |
| exp-048 | `pull_request` 的 CI 跑在 merge 树上：head 树自检通过不等于 CI 通过 | [CI、构建与依赖](ci-build.md#exp-048) |
| exp-049 | job 级 conclusion 会掩盖 step 级超时，且超时会让同 job 后续 step 被 skip | [宿主、并发与生命周期](hosts-lifecycle.md#exp-049) |
| exp-050 | 同名 CI job 分属不同 workflow，`validate` 这类通用名必须按 `workflow_name` 取值 | [CI、构建与依赖](ci-build.md#exp-050) |
| exp-051 | 「生成物与契约一致」不等于「生成物可编译」：漂移检查绿了还要看消费者编译 | [审查、契约与公共行为](review-contracts.md#exp-051) |
| exp-052 | `mergeable_state=dirty` 要给出冲突文件，别只写"有冲突" | [CI、构建与依赖](ci-build.md#exp-052) |
| exp-053 | 复核第三方 open 线程是否已修：同进程 A/B 跑两版实现，别读 head 源码推断 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-053) |
| exp-054 | 判"过度检测"之前，先确认测试是否显式主张该行为 | [审查、契约与公共行为](review-contracts.md#exp-054) |
| exp-055 | 回复里的修复 commit 可能不存在于任何远端 ref，只能按内容核对 | [审查、契约与公共行为](review-contracts.md#exp-055) |
| exp-056 | 同名用例在不同环境失败在不同断言行，"同名失败"不等于"同一抖动" | [平台、工具与环境](environment.md#exp-056) |
| exp-057 | "先把记录写进去再改名"的修复，会让新记录成为窗口裁剪的首选受害者 | [审查、契约与公共行为](review-contracts.md#exp-057) |
| exp-058 | 变异测试用来定位"哪条路径没有回归保护"，而不是用来证明"有保护" | [平台、工具与环境](environment.md#exp-058) |
| exp-059 | 改用户可见文案前，先找按"整句 innerText"等待的 UI 验收 harness | [审查、契约与公共行为](review-contracts.md#exp-059) |
| exp-060 | 只有 lockfile 变更的依赖 PR：红 job 先按"同 workflow 相邻样本"归因，再谈因果 | [CI、构建与依赖](ci-build.md#exp-060) |
| exp-061 | 跨后端 e2e 用「整条记录相等」断言持久化契约，必然在某个后端变红 | [存储、身份与迁移](storage-identity.md#exp-061) |
| exp-062 | 超长 parametrize 实参会在 Windows 上经 `PYTEST_CURRENT_TEST` 溢出，用例根本没执行 | [平台、工具与环境](environment.md#exp-062) |
| exp-063 | 文档宣称「与某 RFC 的词表一致」时，必须逐值对回 RFC 原文 | [审查、契约与公共行为](review-contracts.md#exp-063) |
| exp-064 | 冗余实现会让单行变异失效：验证回归保护应回退整文件而非改一行 | [审查、契约与公共行为](review-contracts.md#exp-064) |
| exp-065 | 夹具的父进程超时大于子进程内部超时：失败只剩阶段名，拿不到根因 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-065) |
| exp-066 | 对端进程被终止时 socket 读可能抛 `ConnectionResetError`，"空字节 = 正常关闭"只在 POSIX 成立 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-066) |
| exp-067 | Windows 的 `.cmd` shim：CreateProcess 不做 PATHEXT 搜索，而 shim 的 stderr 来自 cmd.exe 的 OEM 代码页 | [平台、工具与环境](environment.md#exp-067) |
| exp-068 | 镜像内 `PYTHONPATH` 注入不会自动进入测试自己 spawn 的子进程 | [网关、召回与上下文](gateway-recall.md#exp-068) |
| exp-069 | 镜像根路径与证据边界（补充：`source/<sha8>` 分目录） | [平台、工具与环境](environment.md#exp-069) |
| exp-070 | 度量产物带 `code_sha` 只解决可追溯，不解决"是否仍描述当前代码" | [审查、契约与公共行为](review-contracts.md#exp-070) |
| exp-071 | 流式请求的 idle 看门狗看到的是「模型事件流」，不是「字节流」 | [网关、召回与上下文](gateway-recall.md#exp-071) |
| exp-072 | 复核「已回复线程」时 head 只是 merge 上游：先逐文件比对 PR 侧 blob，再决定重跑范围 | [审查、契约与公共行为](review-contracts.md#exp-072) |
| exp-073 | 在 Windows 上审查仅 POSIX 的缓存/锁模块：用 WSL + 只桩跨包依赖装载单文件 | [平台、工具与环境](environment.md#exp-073) |
| exp-074 | 把 `shutil.which` 换成自建 PATH 枚举：`PATHEXT` 只属于 Windows | [平台、工具与环境](environment.md#exp-074) |
| exp-075 | 结合性/优先级类断言先跑一行探针，别用"看起来属于哪个分支"定级 | [审查、契约与公共行为](review-contracts.md#exp-075) |
| exp-076 | 子包测试的 `PYTHONPATH` 顺序：editable 安装会把"被测包"悄悄换成工作区 master | [平台、工具与环境](environment.md#exp-076) |
| exp-077 | 归档副本缺少 `.git` 时，用「哑 gitdir + alternates」满足被测试代码的 `git rev-parse` | [审查、契约与公共行为](review-contracts.md#exp-077) |
| exp-078 | PR head 是 merge commit 时，`gh pr diff` 展示的是「冲突解析结果」，其中的删除往往是合并丢代码 | [审查、契约与公共行为](review-contracts.md#exp-078) |
| exp-079 | 「共享截止时间」替换「逐次超时」后，回退日志的词表还在报对方的错 | [宿主、并发与生命周期](hosts-lifecycle.md#exp-079) |
| exp-080 | socket 背压式用例在 Windows 上不可复现（`SO_SNDBUF` 只限发送端） | [平台、工具与环境](environment.md#exp-080) |
| exp-081 | 依赖 bump PR 要同时扫复合 action：dependabot 只覆盖 workflow | [CI、构建与依赖](ci-build.md#exp-081) |
| exp-082 | 归因 job 超时：用相邻 `PASSED` 时间戳算单条成本，并找同日对照 PR | [网关、召回与上下文](gateway-recall.md#exp-082) |
| exp-083 | 一处修复改到多条等价分支时，对**每条分支**分别做变异，并跑该模块的整个相关选择集 | [审查、契约与公共行为](review-contracts.md#exp-083) |
| exp-084 | 枚举 merge commit 的"人工冲突解决改动"：把自动合并树复算出来逐文件比对 | [审查、契约与公共行为](review-contracts.md#exp-084) |
| exp-085 | 跨 PR 撞号：`managed_digest` 一致、两边 CI 全绿、迁移测试全绿都不构成反驳 | [CI、构建与依赖](ci-build.md#exp-085) |
| exp-086 | 汇总门禁类 PR：先确认它在 ruleset 里是不是 required check | [CI、构建与依赖](ci-build.md#exp-086) |
| exp-087 | 并行 PR 各自 `mergeable: true` 不代表合并后能编译：必须比对被改函数的签名与调用点 | [审查、契约与公共行为](review-contracts.md#exp-087) |
| exp-088 | 生成物里的「契约摘要」不等于生成物：摘要校验通过 ≠ 产物已同步 | [审查、契约与公共行为](review-contracts.md#exp-088) |
| exp-089 | 测试把 Windows 原生路径写进 `.env` 文件时，dotenv 会吃掉反斜杠 | [平台、工具与环境](environment.md#exp-089) |
| exp-090 | 伪造成 dist-info 会让 Typer 的 entry-point 命令全部不注册（2026-10-30 实测） | [审查、契约与公共行为](review-contracts.md#exp-090) |
| exp-091 | `git merge-tree --write-tree` 的自动合并树里带着冲突标记，不能直接拿来判「删测试」 | [审查、契约与公共行为](review-contracts.md#exp-091) |
| exp-092 | 一个大 PR 里出现两个同构目录时，先判「陈旧副本」再判「设计」 | [审查、契约与公共行为](review-contracts.md#exp-092) |
| exp-093 | 判「PR 的红 job 属于 base」：用 base commit 的 push run 做 job 名集合差分，再抽一条签名 | [审查、契约与公共行为](review-contracts.md#exp-093) |
| exp-094 | `gh api` 的 POST 会出现 EOF，而 GET 正常：按请求重试，不要据此判断写操作失败 | [审查、契约与公共行为](review-contracts.md#exp-094) |
| exp-095 | 生成器产物的复核可以完全不落地：用 blob 级复算代替 checkout | [审查、契约与公共行为](review-contracts.md#exp-095) |
| exp-096 | 覆盖类清单要按"元素"对账，不能按"摘要"对账；夹具从被测清单同源生成时 CI 绿是自证的 | [CI、构建与依赖](ci-build.md#exp-096) |
| exp-097 | workflow 里 suite job 的 `skipped` 可能是「被别的 job 级联跳过」，不等于路径未命中 | [CI、构建与依赖](ci-build.md#exp-097) |
| exp-098 | 校验型守卫把「低危冗余」升级成「该 Scope 处理永久停摆」 | [审查、契约与公共行为](review-contracts.md#exp-098) |
| exp-099 | fork PR 的 workflow run = `action_required` 时，「0 个 check run」不是 CI 通过，是等维护者批准 | [CI、构建与依赖](ci-build.md#exp-099) |
| exp-100 | 新增「密钥/凭据文件安全校验」模块时，先查平台 API 存在性：`os.O_NOFOLLOW` / `os.getuid` 在 Windows 直接抛 `AttributeError` | [平台、工具与环境](environment.md#exp-100) |
| exp-101 | 「缺陷所在文件不在 diff」不等于 Fallback：先找同根因的可评论行 | [审查、契约与公共行为](review-contracts.md#exp-101) |
| exp-102 | 「按结构判定同一布局」必须先确认比较是双向的：单向 `differences()` 看不见多出来的对象 | [审查、契约与公共行为](review-contracts.md#exp-102) |
| exp-103 | 回复线程的请求体只能是 `{"body": ...}` | [审查、契约与公共行为](review-contracts.md#exp-103) |
| exp-104 | 重试循环里的「恢复动作」自身会失败：`check=True` 把可恢复失败变成整轮中止 | [审查、契约与公共行为](review-contracts.md#exp-104) |
| exp-105 | 某行「看起来没改」但 base 已改：用 `git log -S` + merge-base 判差异来源 | [审查、契约与公共行为](review-contracts.md#exp-105) |
| exp-106 | 反证不必回退文件：在同栈的另一个 PR head 上跑当前 head 的测试（2026-11-05 实测） | [审查、契约与公共行为](review-contracts.md#exp-106) |
| exp-107 | 在 blobless 克隆上取某个 PR 的源码树：`git archive` 会逐个拉 blob 并可能被 RPC 打断，改用稀疏克隆 | [平台、工具与环境](environment.md#exp-107) |
| exp-108 | 读取 `/proc/<pid>/stat` 判活性：进程在 open 与 read 之间退出抛的是 `ProcessLookupError`（ESRCH），不是 `FileNotFoundError` | [宿主、并发与生命周期](hosts-lifecycle.md#exp-108) |
| exp-109 | 本机 `.venv312` 的 `asyncio.run` 整体挂死：asyncio 探针改在 WSL 侧跑（2026-11-06 实测） | [CI、构建与依赖](ci-build.md#exp-109) |
| exp-110 | head 上的「已解决」不覆盖合并结果：摘要类门禁要按 merge-tree 结果树复算（2026-11-07 实测） | [CI、构建与依赖](ci-build.md#exp-110) |
| exp-111 | OOM/资源类缓解措施必须在同一 head 的构建日志里验证「配置生效 + 仍然失败」两段 | [CI、构建与依赖](ci-build.md#exp-111) |
| exp-112 | CI 分步预算与作业上限是两个数：改 workflow 必须把两者对账 | [CI、构建与依赖](ci-build.md#exp-112) |
| exp-113 | 宿主机上的 loopback 集成测试超时：先做 base 对照，别急着归因 PR | [平台、工具与环境](environment.md#exp-113) |
| exp-114 | 新用的序列化关键字要对照依赖下限：CI 锁的版本不等于声明支持的版本 | [CI、构建与依赖](ci-build.md#exp-114) |
| exp-115 | 把 helper 换成手写查询时，要逐条清点 helper 的副作用（锁、排序、上限） | [宿主、并发与生命周期](hosts-lifecycle.md#exp-115) |
| exp-116 | Windows 上 `git archive` 会按 `core.autocrlf` 导出 CRLF，逐 blob 校验必须显式关闭 | [平台、工具与环境](environment.md#exp-116) |
| exp-117 | 纯性能 PR 的"机制无断言"缺口：用退化变异判定测试是否真的覆盖了新机制 | [审查、契约与公共行为](review-contracts.md#exp-117) |
| exp-118 | trace 拓扑型的契约 e2e：先用「单用例 base/head 对照」归因，别当基线抖动放过 | [审查、契约与公共行为](review-contracts.md#exp-118) |
| exp-119 | "镜像 + 共享 venv" 跑测试前必须打印 `powercontext.__file__`：site-packages 里的正式版会静默顶掉镜像源码 | [平台、工具与环境](environment.md#exp-119) |
| exp-120 | 回复线程复核：三类容易被漏掉的"假修复" | [审查、契约与公共行为](review-contracts.md#exp-120) |
| exp-121 | 判"行为保持不变的重写"：把 base 版本原样复刻成函数，跑同一批变异输入做差分（2026-11-10 实测 #2518） | [审查、契约与公共行为](review-contracts.md#exp-121) |
| exp-122 | 判定"该 head 的 CI 到底跑没跑"：先查同 head 的 run 数，再谈 cancelled 的成因 | [CI、构建与依赖](ci-build.md#exp-122) |
| exp-123 | 基线归属要落到 step / 用例粒度：同名 job 在 master 红，不等于同一处失败 | [审查、契约与公共行为](review-contracts.md#exp-123) |
| exp-124 | 复用工作区 `.venv` 跑镜像代码时，`PYTHONPATH` 必须是绝对 Windows 路径 | [平台、工具与环境](environment.md#exp-124) |
| exp-125 | license-eye 的豁免是按后缀列举的：新增图源后缀会让 CI preflight 整轮红 | [CI、构建与依赖](ci-build.md#exp-125) |
| exp-126 | 复核「生成物是否重生成」：把生成器依赖装到被检 package.json 的同级独立目录（2026-11-12 实测 #2270） | [审查、契约与公共行为](review-contracts.md#exp-126) |
| exp-127 | 「完整性守卫」要读记录侧的 loss 声明，而不是只重新遍历一次输入（2026-11-12 源码级判断 #2435） | [审查、契约与公共行为](review-contracts.md#exp-127) |
| exp-128 | 「逐字节重放」类门禁要检查写入侧换行策略；适配器测试要先确认 `integrations/<host>` 的 import 源（2026-11-12 实测 #2529 / #2527） | [CI、构建与依赖](ci-build.md#exp-128) |
| exp-129 | head 是 `Merge upstream/master` 时：先用「四 blob 比对」判定能否复用旧审结论，再谈增量（2026-11-13 实测 #2527） | [审查、契约与公共行为](review-contracts.md#exp-129) |
| exp-130 | 「尝试次数减免」类改动（`attempts - 1` 这种）要按四点核验，否则减免可能从未生效（2026-11-13 实测 #2597） | [宿主、并发与生命周期](hosts-lifecycle.md#exp-130) |
| exp-131 | 镜像里跑全量单测出现「成片 F」时，先归因再计入（2026-11-13 实测 #2244） | [审查、契约与公共行为](review-contracts.md#exp-131) |
| exp-132 | 「新事件未登记到运维文档」要先证明那份文档是注册表（2026-11-13 实测 #2619） | [审查、契约与公共行为](review-contracts.md#exp-132) |
| exp-133 | 复核他人 finding 时，先确认他引用的那一行就是 head 的行（2026-11-14 实测 #2635） | [审查、契约与公共行为](review-contracts.md#exp-133) |
| exp-134 | 契约删除类改动：验收顺序是「计数归零 → generated 产物 → e2e 分类清单 → 已提交 bundle」（2026-11-13 实测 #2616） | [审查、契约与公共行为](review-contracts.md#exp-134) |
| exp-135 | 「设置项未登记到配置文档」先统计同族登记率（2026-11-13 实测 #2449） | [审查、契约与公共行为](review-contracts.md#exp-135) |
| exp-136 | 「减法型」修复必须做变异反证，光跑绿用例不足以判有效（2026-11-14 实测 #2632） | [审查、契约与公共行为](review-contracts.md#exp-136) |
| exp-137 | 生成器 `--check` 在无 `.git` 的隔离镜像里会假失败（2026-11-14 实测 #2647 / #2645） | [审查、契约与公共行为](review-contracts.md#exp-137) |
| exp-138 | 判「CI 红是否与本 PR 相关」用另一 head 本地复跑同用例（2026-11-14 实测 #2550） | [CI、构建与依赖](ci-build.md#exp-138) |
| exp-139 | 工作区 `.venv` 的 editable 目标可能指向另一个 PR 的 `probes/` 目录（2026-11-14 实测） | [平台、工具与环境](environment.md#exp-139) |
| exp-140 | 无法 checkout 时用「本地 base blob 复用 + 按需取 blob」核对 `managed_digest`（2026-11-14 实测 #2621） | [审查、契约与公共行为](review-contracts.md#exp-140) |
| exp-141 | 本机 `git fetch` 可能整体不可用而 `gh api` 正常（2026-11-14 实测） | [审查、契约与公共行为](review-contracts.md#exp-141) |
| exp-142 | 测试注释里「另一种实现会怎样」的断言必须实测（2026-11-14 实测 #2632） | [审查、契约与公共行为](review-contracts.md#exp-142) |
| exp-143 | 新 CI 作业「时长异常短」不等于空跑，取 job 日志的 `collected/passed` 行（2026-11-14 实测 #2649） | [CI、构建与依赖](ci-build.md#exp-143) |
| exp-144 | 从 Windows 调用 WSL 跑 e2e 时的三个环境陷阱（2026-11-15 实测 #2616） | [平台、工具与环境](environment.md#exp-144) |
| exp-145 | `commits/<sha>/check-runs` 默认只给 30 条：漏作业会直接导致「该作业不存在」的错误结论（2026-11-15 实测 #2630） | [CI、构建与依赖](ci-build.md#exp-145) |
| exp-146 | `url` crate 的 `host_str()` 对 IPv6 带方括号：用它 `parse::<IpAddr>()` 判环回会漏掉 `[::1]`（2026-11-15 实测 #2630） | [审查、契约与公共行为](review-contracts.md#exp-146) |
| exp-147 | 提交进仓库的 pinned 报告若对工作树字节取摘要，在 CRLF 检出上必然与 blob 不符（2026-11-15 实测 #2630） | [审查、契约与公共行为](review-contracts.md#exp-147) |
| exp-148 | 新增用例若要证明平台行为，Windows 侧的两条硬前提：`TimeoutExpired.stdout` 是 `str`、`str(Path("/proc/..."))` 带反斜杠（2026-11-16 实测 #2518 head 611c2498） | [平台、工具与环境](environment.md#exp-148) |
| exp-149 | 共享 venv 的 editable `.pth` 会把某个历史 probe 树插到 `sys.path` 首位，压过 `PYTHONPATH`（2026-11-16 实测 #2615） | [平台、工具与环境](environment.md#exp-149) |
| exp-150 | 作者把 master 合进 PR 分支后：派生的摘要/指纹必须按「三方各算一次」判，两个父提交自洽不代表合并树自洽 | [存储、身份与迁移](storage-identity.md#exp-150) |
| exp-151 | 「记录到日志/追踪里的脱敏」必须发生在截断之前，否则前缀被切走就不再有可识别的凭据形态 | [审查、契约与公共行为](review-contracts.md#exp-151) |
| exp-152 | Windows 上 `bash` 解析到 WSL 时，`subprocess` 的 Windows 环境变量不会跨 interop 传递（2026-11-17 实测 #2518） | [平台、工具与环境](environment.md#exp-152) |
| exp-153 | 「集合成员已同步」不能靠「对该集合做了参数化」来证明：用例总带同一个可选键时会掩盖缺项 | [审查、契约与公共行为](review-contracts.md#exp-153) |
| exp-154 | 同一 SHA 的 check-runs 可能含同一次 run 的多次重试：判读前先按 `check_suite` 取最新 attempt（2026-11-24 实测 oceanbase/powercontext #2749） | [CI、构建与依赖](ci-build.md#exp-154) |
| exp-155 | 把一条错误路径从 A 类改成 B 类时，用「同类损坏状态」用例证明 A 类仍在真正的判定点触发（2026-11-24 实测 oceanbase/powercontext #2751） | [平台、工具与环境](environment.md#exp-155) |
| exp-156 | 判「零 CI 覆盖」和「CI 红是否与本改动相关」的两步取证（2026-11-24 实测 oceanbase/powercontext #2615 / #2602） | [CI、构建与依赖](ci-build.md#exp-156) |
| exp-157 | PR 的 base 不是默认分支时，整层可能零 CI：先看 workflow 的 `pull_request.branches` 过滤（2026-11-25 实测 oceanbase/powercontext #2653） | [CI、构建与依赖](ci-build.md#exp-157) |
| exp-158 | `gh api -f body=@file` 发的是字面量 `@file`，回复与 PATCH 必须用 `--input` 或 `-F`（2026-11-25 实测 oceanbase/powercontext #2816） | [宿主、并发与生命周期](hosts-lifecycle.md#exp-158) |
| exp-159 | 「merge-only」复审：只合 upstream 也要审，判据与手法（2026-11-25 实测 #2815 / #2810 / #2771） | [审查、契约与公共行为](review-contracts.md#exp-159) |
