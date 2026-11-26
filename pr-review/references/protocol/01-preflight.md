<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 1. 不可跳过的门禁

### R01. 前置文档

先读取当前环境明确指定且适用于任务的指令、仓库 `AGENTS.md`、`CLAUDE.md`、贡献指南和项目 Review 补充规则。未指定路径的工作台、踩坑日志或 SOP 不触发全盘搜索；参考材料仅按当前变更风险读取。同一任务内内容未变化的指令无需反复加载。

项目本地规范优先于通用语言规范，但不得降低安全性、正确性和可验证性的最低要求。

### R02. PR 实时状态与审查快照

任何 checkout、Diff、Lint、测试或评论之前，先固定仓库身份并检查 `state`、`isDraft`；通过状态门禁后才获取 required checks：

```bash
gh repo view {owner}/{repo} --json id,nameWithOwner,url
gh pr view [PR_NO] -R {owner}/{repo} --json number,url,state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid,isCrossRepository,headRepository,headRepositoryOwner,changedFiles,mergeable,mergeStateStatus,reviewDecision,potentialMergeCommit,statusCheckRollup
gh pr checks [PR_NO] -R {owner}/{repo} --required --json name,state,bucket,link,workflow,event
```

先执行前两条，**只有 `state == OPEN` 且 `isDraft == false` 才执行第三条及后续审查**。状态字段缺失或读取失败时，不推定 PR 可以审查；只报告预检阻塞。命令的 stdout、stderr 与退出码都属于证据。

**Draft 默认跳过**：`isDraft == true` 时，不获取 Diff、建立审查镜像、运行检查或测试、发布或回复评论。仅在当前用户聊天说明“PR 为 Draft，已跳过”。只有用户明确要求审查 Draft PR 时才可例外；普通“review 这个 PR”“再 review”或批量审查请求不构成例外。批量任务跳过该 PR 后继续处理其他符合条件的 PR。不得擅自将 Draft 转为 Ready for review。

记录：

- repository id、nameWithOwner、URL、PR number、PR URL、state、isDraft；跨仓 PR 另记录 isCrossRepository、headRepositoryOwner 和 headRepository（处置要求见 `R04`）
- headRefName、headRefOid、baseRefName、baseRefOid、changedFiles
- Diff 基准；本地 fallback 或结论依赖祖先关系时，取得 Base 与 Head 的 merge-base OID（取法见 §2.2）。纯远端 Diff 审查可记录固定快照下的三点比较语义，无需为取得 OID 单独 checkout；无法取得必需的 OID 时记录缺口
- potentialMergeCommit OID；仓库启用 merge queue 时，还要记录当前 merge-group SHA
- mergeable、mergeStateStatus、reviewDecision
- required checks 的名称、状态、链接和 workflow；`statusCheckRollup` 只作补充，不替代 required checks 清单。该清单只证明治理层面的 required-check 状态，不证明测试执行在 Head、merge commit 或其他 SHA 上；CI 的技术证据按 `R05`、`R15`、`R16` 单独取证。

**审查快照记录 `repository.id + nameWithOwner + PR number + baseRefName + baseRefOid + headRefOid`。** 各字段变化影响不同，不把所有变化都处理为全量重审：

| 变化 | 必须复核的内容 | 可复用的证据 |
|---|---|---|
| Head 变化 | 停止待发布批次；按 §8 核对新 Head 的完整 Diff、增量、关联影响与评论位置 | 仅复用已证明相关代码、依赖、配置及测试前提未变的证据 |
| 目标分支变化 | 暂停发布；重新核对 Diff 基准、适用规则、兼容性、merge result 与对应 checks | 仅复用与目标分支无关且前提未变的证据 |
| merge-base、文件数或 Diff 内容变化 | 重新获取并对账完整 Diff，复核受影响范围与评论位置 | 未受变化影响且已经核实的证据 |
| 仅 Base tip 变化 | 核对 merge-base、文件数及 Diff 是否变化；检查 Base 增量是否影响调用链、依赖、配置和支持场景；刷新 merge result、对应 checks 与适用规则 | Head 源码证据可按影响范围复用；旧 Base 对照和旧 merge result 的结果不得自动作为当前证据 |

`baseRefOid` 是目标分支当前 tip。它前进时 PR Diff 可能不变，因此不自动触发全量源码重审；但仍可能改变合并行为。Base 对照证据必须标明使用的是当前 Base tip 还是 merge-base 及其 OID，两者不能互相冒充。Base 或目标分支变化后，只有证明相关前提未变才能复用旧对照；无法证明时补充受影响验证或记录缺口。

哈希类字段无法读取时记录具体缺口，不阻止源码审查；未启用 merge queue 等不适用字段无需作为缺口。required checks 的空结果按 §9 解释。

**PR 文本元数据同样有时效性**：PR 描述、`special notes`、声明依赖的其它 PR 状态，以及行内 thread 里的澄清，都可能写给旧 Base，或早于/晚于当前 Head。把这些内容用作判断依据（"本来就有 / 本次新增 / 已在别处修复 / 作者已回应"）之前，必须现取并与当前 Head 逐条核对：把描述里每一句"现在 / 改为 / 新增"翻译成可检索的符号，用 `git show <base>:<file>` 或 `git log -S` 验证；thread 澄清结合 `reviewThreads` 的 `isResolved`、`isOutdated`、`createdAt` 与 PR 的 `updatedAt` 对齐。核对不上即按过期描述处理，记录为验证缺口，不照抄进结论，也不据此归责或免罪。

快照在首次取证、完整取证后、每个小批次评论发布前、最终收尾时复检，同时重新检查 `state`、`isDraft`；相邻阶段没有新增操作时可合并，不要求每次只读调用前后重复查询。PR 变为非 OPEN 或未经明确授权审查的 Draft 时，停止剩余审查与待发布批次，仅向当前用户说明原因，不向 PR 补发停止通知或总结。其他变化按上表处理；依赖已变化前提的 Finding 在复核完成前不得发布。旧证据保留其原 SHA，未经复核不得用于当前结论。checks 与治理状态独立刷新，不混用不同提交的结果。

若 PR 为 `MERGED` 或 `CLOSED`，立即停止：

```text
PR 状态为 MERGED/CLOSED，停止审查。
```

### R03. 独立镜像

不得在用户当前开发目录 checkout PR。每个 PR 使用独立镜像，根路径由调用环境通过 `{REVIEW_ROOT}` 指定（各平台取值见 §13）：

```text
{REVIEW_ROOT}/[owner]-[repo]-pr-[PR_NO]
```

镜像根目录按职责隔离：`source/` 保存主证据 checkout，`evidence/` 保存 API 响应、Diff、日志和报告，`probes/` 保存 Base/Head 或变异式的一次性副本。审查证据、显式脚本输出、临时数据和验证副本只能放在相应子目录内。不得写入用户开发目录、桌面、下载目录或其他项目目录。

建立或复用镜像时使用 `R02` 已取得的仓库身份，核验保存的 repository id/nameWithOwner、PR number、Base/Head，确认 Git 副本的 `HEAD` 等于审查 SHA、对象可读，且**工作区相对于该 SHA 没有内容差异**。判据说明：

- Git checkout 副本分别检查工作区与索引（`git diff`）、索引与审查 SHA（`git diff --cached <审查SHA>`），并用 `git status --porcelain=v2 --untracked-files=all` 检查额外文件。可能改变导入、测试发现或配置选择的未跟踪文件也属于污染。
- 正常的 CRLF checkout 不自动构成污染，但 `core.autocrlf=true` 也不构成忽略差异的理由。出现疑似行尾噪声时，核对 `.gitattributes`、`git ls-files --eol`、实际字节和归一化后的内容；只有证明差异完全来自预期的行尾转换、索引与 refs 未变且不影响待验证行为时，才可记录后继续复用。Git attribute 中的 filter 名称本身不执行命令；若本机 Git 配置为该名称配置了 `smudge` / `process` driver，checkout 可能执行它。`clean` driver 通常在 add/check-in 等调用 clean 转换的操作中执行。所有相关入口按 `R04` 隔离。
- 归档副本对照原始归档或文件哈希。

remote URL 只作辅助核对，SSH/HTTPS 或重定向的字符串差异不能单独证明身份不符。旧副本对应不同 SHA 时保留历史证据，可在同一 PR 目录下按 SHA 建立新副本；对象库异常或 checkout 不完整时另建干净副本，不用强制 reset 修补。Git 传输不可用但 API 正常时，可以按完整 Head SHA 下载归档，但不得声称完成依赖 `.git` 的验证。

归档必须通过保留原始字节的方式下载，检查下载退出状态、压缩流和归档成员的完整读取结果，再安全解压到隔离目录；拒绝绝对路径、越界路径和逃逸目标目录的链接。条目数量与关键路径存在只是辅助检查。遇到 `unexpected end of file` 等错误时先核对下载、重定向、shell 二进制输出及工具版本；可使用另一解析器交叉检查，但不能仅因它解出部分文件便宣称归档完整。记录确切错误和检查结果，必要时重新下载。具体平台的工具替代方案只在适用条件已验证时采用。

### R04. 只读保护与不可信代码边界

以下本地修改命令禁止作用于**主证据副本 `source/`**（含其受版本控制文件、索引和 Git refs）：

```text
git commit / merge / rebase / reset --hard
git checkout -- .
```

在 `probes/` 下的一次性副本中，为回滚变异而执行 `git checkout -- .` 或等价命令是允许的，但必须记录变异补丁与回滚前后的文件哈希。判据是**作用对象是否承载证据**，不是命令本身。

`git push`、`gh pr merge`、`gh repo sync` 等发布或同步操作受 §0.3 的授权边界约束，不因命令在 `probes/` 中执行而获得授权。

禁止运行会直接改写主证据副本源码的工具，例如 `cargo fmt`、`go fmt ./...`、`ruff --fix`、`eslint --fix`、`prettier --write`。`--check`、Lint、构建和测试也不得假定为天然只读；执行前必须检查命令、脚本和测试夹具的副作用，并遵守以下边界：

- 主证据 checkout 的受版本控制文件、索引和 Git refs 必须保持不变。显式日志、报告和临时数据写入 `evidence/`；缓存和构建产物应留在镜像内，并在工具支持时定向到任务专属目录。尽量使用任务专属的缓存、临时目录、端口和本地一次性服务。
- 在构建、测试或探针批次前后检查受版本控制文件、索引和 refs；Git 副本记录 `git status --porcelain=v2 --branch --untracked-files=all` 及固定引用，归档副本对照原始归档或文件哈希。纯读取命令不重复做此检查。若改变了主证据文件、索引或 refs，记录副作用并另建干净副本，不通过手工改回掩盖变化。已知会生成受版本控制文件的命令提前放入 `probes/` 执行。
- Base/Head 对照和变异式反证必须在固定到 exact OID 的独立一次性副本中执行。变异只能修改该副本，必须记录变异补丁、预期失败点和实际结果；不得 commit、push，也不得用变异后的结果替代未变异 Head 的正常验证。
- 使用共享或真实数据库、云资源、消息队列，或执行本协议授权范围外的外部写入、部署、发布、迁移、全局安装等操作，需要用户授权。§0.3 已授权的 GitHub 读取和问题行内评论不重复申请。缺少其他授权时采用源码推导、Dry Run 或隔离的本地验证，并记录未覆盖风险。
- **不可信 PR 代码只能在经过核验的受限环境中执行。** 是否可信依据来源、审读范围与执行入口判断；跨仓/fork 是加强检查信号，同仓 PR 也不能自动视为可信。安装脚本、依赖生命周期脚本、构建脚本、代码生成器、编译期代码（如 `build.rs`）、测试夹具、模块导入、测试和启动服务都可能执行 PR 代码。`npm ci`、`cargo build`、`go test` 等命令不能因名称看似常规就豁免本条。静态工具若加载项目配置、插件或扩展，也按实际执行入口判断。
- **checkout/fetch 前先关闭 Git 执行入口。** checkout PR 内容时，必须将 `core.hooksPath` 指向已核验的空目录，并显式关闭 `submodule.recurse` / `fetch.recurseSubmodules`；不得递归初始化 PR 指定的 submodule。Git 命令不得继承宿主的 system/global 配置：使用隔离的 Git 配置环境，检查并排除 local config 中的 `filter.<name>.smudge` / `filter.<name>.process` 等执行型 driver；不得为了让 PR 声明的 `.gitattributes` filter 生效而添加或启用 driver。checkout 期间重点防范 `smudge` / `process`；任何会调用 `clean` 转换的 add/check-in 操作同样受隔离约束。配置隔离应覆盖 hooks、filters、submodule、credential helper、protocol helper 等可能执行外部程序或访问宿主资源的入口。具体平台实现由调用环境提供，但必须记录实际生效配置并验证，而不是只记录命令行参数。
- 执行不可信代码前，必须确认使用一次性沙箱、受限用户、默认禁用网络、无宿主凭据或继承的敏感环境变量、无敏感目录及宿主控制接口挂载；输入仅包含必要源码与依赖，输入只读，写入仅限隔离的工作/临时目录，并限制资源与执行时间。独立目录、普通一次性副本或仅关闭网络都不等于此隔离；容器名称本身也不是隔离证据。依赖准备须与不可信代码执行分开，不向该执行环境注入网络访问或凭据。
- 同仓 PR 与 fork PR 都按不可信代码处理，但权限面必须区分：fork 的 `pull_request` 通常受到令牌权限和 Secrets 限制，具体仍需核对仓库设置；同仓 `pull_request` 可能获得仓库 Secrets 或更高权限的 `GITHUB_TOKEN`，不能仅凭事件名推定安全。`pull_request_target` 默认使用 Base 仓库默认分支上的 workflow，且可能拥有 Secrets/写权限；除非已证明流程只把 PR 内容当数据且不 checkout/执行 PR 代码，否则不得将其作为 PR 行为测试的可信证据。事件类型本身不能代替权限和执行路径审查。
- 无法核验上述隔离条件时，不在宿主直接执行不可信代码；使用源码推导或符合 `R05`、`R16` 的可信 CI，并记录仍缺少的行为证据。这一边界优先于行为验证要求；因隔离不可用而未完成的必要验证仍是缺口，不记作“不适用”。

---
