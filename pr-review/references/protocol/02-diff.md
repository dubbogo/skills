<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 2. 标准执行流程

审查范围包括 changed surface，即直接修改及其影响的调用方、配置、测试、文档和 CI 路径。先确定具体风险及所需证据，再选择验证方法；不因文件类型自动触发全仓检查。以下为工作清单，不强制静态检查与测试的执行顺序。任何可能执行 PR 控制内容的静态检查、依赖安装、生成、编译、测试或启动步骤，均须先通过 `R04`；R04 不满足时停止该执行路径，改用源码推导或按 `R05`、`R16` 核验的可信 CI，并记录缺口。必要证据不能省略；无 Finding 或用户要求仅本地报告时不发布评论。

1. **状态预检**：按 `R02` 检查 `state`、`isDraft` 和 Head SHA；未通过门禁即跳过，不执行以下步骤。
2. **分类定级**：判断 PR 类型、风险和需要的审查深度。
3. **获取证据**：保存完整文件列表和 Diff。
4. **关联扫描**：检查调用方、实现方、配置、测试和文档。
5. **必要时 checkout（条件步骤）**：关联扫描需要完整源码树，或需要执行静态检查、构建、测试和探针时，在独立镜像中建立 exact Head 副本。
6. **静态验证**：针对改动风险、适用的仓库门禁或需复核的工具结论，选择相关检查或复用 CI；执行前判断工具、项目配置、插件和脚本是否可能运行 PR 控制内容，可能时先通过 `R04`。
7. **行为验证**：行为变化、Bug 修复及协议、并发、安全、持久化等风险需有相应行为证据。优先最小相关测试，平台按 `R06` 选择，范围不足时再扩大；所有依赖安装、生成、编译、测试和启动步骤均先通过 `R04`，CI 替代证据按 `R05`、`R15`、`R16` 判定。
8. **形成 Finding**：只报告有证据、可定位、可执行的问题，格式见 §4。
9. **提交行内评论**：按 `R11` 锚定具体问题行；无法锚定相关可评论行时进入 **Fallback**，不改发 Conversation。
10. **实时复检**：重新确认 Head SHA、checks 和 merge 状态。
11. **收尾对账**：仅在当前用户聊天输出 Findings、验证结果与缺口、GitHub 状态、评论链接和证据目录，不向 PR 发布总结。

需要 checkout 时，在独立取证仓库或隔离目录固定到审查 SHA。不得直接沿用会执行 hooks、submodule 或宿主 filter 配置的默认 checkout；先按 `R04` 关闭 Git 执行入口，再核验仓库身份、HEAD SHA、工作区和 refs。可使用 `gh pr checkout` 或 Git fetch，但命令形式本身不构成安全证明。纯 Diff 审查不强制 checkout。未执行本地检查时如实说明原因：不适用、已复用符合 `R16` 的 CI 或环境阻塞，不把已触发但无法完成的检查写成"不需要"。

### 2.1 PR 分类与执行预算

| 类型 | 典型变更 | 默认深度 |
|---|---|---|
| 文档/注释 | `.md`、注释、docstring | 内容准确性、链接可达性、示例可执行性、术语 |
| 配置/CI | workflow、Dockerfile、Makefile、脚本 | 语法、权限、兼容性、执行路径和回滚 |
| 依赖更新 | lockfile、manifest、模块版本 | 安全公告、破坏性变更、间接依赖、许可证、适配 |
| 核心逻辑 | API、协议、数据路径、业务代码 | 相关调用链、行为证据及适用的静态门禁 |

分类只决定工具范围，不降低问题标准。小 Diff 也可能包含 P0。

当本 PR 修改了可复制命令、代码、安装入口、插件、配置示例、版本或路径，或者本 PR 的实现/配置变化可能使既有示例失真时，必须把相关文档按可执行接口审查。根据风险依次选择源码链路核对、语法检查、Dry Run 和安全的本地执行；实际安装、编译或运行必须符合 `R04` 的副作用边界。无法安全执行时，记录替代证据、未覆盖风险及其对 Merge 结论的影响。与 changed surface 无关且未被本 PR 影响的既有示例，不触发全量安装或运行验证。

**执行预算与覆盖记录**：以下规模阈值是分批与报告的默认约定，不是效率实测结果或缺陷判据。应结合 changed surface 的风险调整，说明实际覆盖范围；规模阈值不自动授权省略必要审查。

- `changedFiles` ≤ 50：默认全量审读。
- `changedFiles` > 50 或单一 Diff 超 1 MB：按模块分批，**每批完成后在 `evidence/` 记录已覆盖路径清单**；收尾对账的 Diff 字段必须列出未覆盖范围及理由。
- 单文件超过 500 行时按函数、类型或行区间读取，禁止整文件无差别灌入上下文。
- 无论规模，发现 P0/P1 后仍必须完成受影响范围的关联扫描，不得以"文件太多"为由跳过已定位问题的证据补全。

### 2.2 Diff、基准与上下文

必须保存完整证据。先记录 `R02` 快照，再获取文件列表和 Diff：

```bash
gh api "repos/{owner}/{repo}/pulls/[PR_NO]/files?per_page=100" --paginate --slurp > [mirror]/evidence/files.pages.json
gh pr diff [PR_NO] -R {owner}/{repo} > [mirror]/evidence/pr.diff
```

GitHub REST `List pull requests files` 即使分页也最多返回 3000 个文件。获取后必须展平分页结果，将 `R02` 的 `changedFiles` 与唯一 `filename` 数量对账，并再次读取 `R02` 快照。快照变化按 `R02` 复核；影响 Diff 基准或内容时重新取证。`changedFiles > 3000`、数量不一致、API/Diff 失败或疑似截断，且远端重取仍无法建立完整证据时，必须在**独立的临时 bare repository** 中获取对象并核验快照 OID；不得为了 Diff fallback 改写 `source/` 主证据副本的固定 refs。

先核对 Base 仓库身份与 repository id，再建立临时取证仓库。GitHub 通常可从 Base 仓库的只读 PR ref 获取当前 PR Head：

```bash
git init --bare [mirror]/evidence/diff.git
git -C [mirror]/evidence/diff.git remote add base https://github.com/{owner}/{repo}.git
git -C [mirror]/evidence/diff.git fetch --no-tags base \
  "+refs/pull/[PR_NO]/head:refs/review/pr/[PR_NO]/head" \
  "+refs/heads/[baseRefName]:refs/review/pr/[PR_NO]/base"
git -C [mirror]/evidence/diff.git rev-parse refs/review/pr/[PR_NO]/head^{commit}
git -C [mirror]/evidence/diff.git rev-parse refs/review/pr/[PR_NO]/base^{commit}
git -C [mirror]/evidence/diff.git cat-file -e "[headRefOid]^{commit}"
git -C [mirror]/evidence/diff.git cat-file -e "[baseRefOid]^{commit}"
git -C [mirror]/evidence/diff.git merge-base [baseRefOid] [headRefOid] > [mirror]/evidence/merge-base.txt
git -C [mirror]/evidence/diff.git diff --name-status --find-renames [mergeBase]...[headRefOid] > [mirror]/evidence/files.local.txt
git -C [mirror]/evidence/diff.git diff --binary --full-index --find-renames [mergeBase]...[headRefOid] > [mirror]/evidence/pr.local.diff
```

`rev-parse` 得到的 PR Head ref 与 Base branch ref 必须分别等于本轮快照的 `headRefOid` 和 `baseRefOid`。任一不等，说明 fetch 期间快照已变化：停止使用本次对象，按 `R02` 重新读取完整快照并重新取证；**禁止把新 Base tip 与旧 Head 快照拼在一起**。若快照 OID 对象不可取得、对象图不完整或 `merge-base` 失败，不得改用近似 SHA、当前分支 tip 或归档文件伪造三点 Diff；记录阻塞。验证仓库未处于 shallow 状态，且 `merge-base` 有唯一可核验结果。所有 fetch 和 refs 均留在该临时仓库。

三点 `A...B` 使用 merge-base 作为基准，与 `gh pr diff` 一致；**不得改用 `baseRefOid..headRefOid` 两点式**，否则会把 base 分支上的无关提交算进本 PR。

**堆叠 PR 的审查基准是本层增量而非累计**：优先检查 PR REST 资源中的 `stack` 对象，或 GraphQL `PullRequest.stack` / `stackEntry`；GitHub 当前将该能力作为公开预览，未提供或当前环境不支持时，不得假定存在。兼容回退时，完整分页读取 OPEN PR，只有在父 PR 的 `head.ref` 与当前 PR 的 `base.ref` 精确匹配、且仓库身份及 Head OID 能对齐时才认定父子关系；仅凭分支名相同不足以认定堆叠。存在多个候选或无法核对父层 OID 时，标记堆叠关系无法确认，不得把累计 Diff 当成本层增量。

确认父层后，记录父 PR 的 Head OID，并与当前 PR 的 Base 快照或 stack 元数据核对。以该固定 OID 与当前 `headRefOid` 确定本层增量。GitHub 原生堆叠 PR 的 Files changed 页面展示本层 Diff。已确认远端文件列表和 Diff 都按本层取值时，按本层对账即可。实际取得累计 Diff 时，另按上述固定 OID 计算本层增量，并报告两套文件数及差异原因。规模阈值和实际审读范围以本层增量为准，行内评论锚点须在 GitHub 当前可评论的 Diff 上按 `R11` 核验。`headRefOid` 未变而 Diff 变大时，先核前序 PR 或目标分支是否前进。被依赖 PR 的阻断问题仍按 §9 纳入合并判断。

GitHub 对大 Diff 会直接拒绝返回（`gh pr diff` 报 HTTP 406）。该阈值会随服务端策略变化，**不以记忆中的数字作为判据**：只要 `gh pr diff` 返回 406，就直接进入上面的本地 fallback，并把实际观察到的规模（文件数 / 行数）与错误原文记入 `evidence/`。

已建立本地镜像时，可在固定 Base/Head OID 上追加 `git -c core.autocrlf=false diff --check` 作为尾随空白、冲突标记等噪声的快速线索；高密度或语义敏感的改动可用 `git diff --word-diff=porcelain` 按词比对，比按行比对更容易暴露条件表达式和字面量的细微变化。两者只产生线索，不单独构成 Finding；CRLF 工作区、Markdown 两空格硬换行等场景产生的命中，先按 `R03` 的工作区污染判据和 §13.2 排除，再据 blob 内容判定。

文件计数时必须同时兼容引号路径：非 ASCII 路径可能在 Diff 头中写成 `diff --git "a/..." "b/..."`，用 `^diff --git a/` 计数会漏文件。按 `^diff --git ` 计数，并与 `changedFiles`、REST 唯一 `filename` 数量对账；需要本地 fallback 或出现无法解释的不一致时，再用固定 Base/Head 的 `git diff --name-only` 核对。纯远端 Diff 审查不为该交叉检查强制 checkout。

不得只看截图或零散片段。使用 `rg`、`fd`、`grep`、`ls` 检查：

- 调用方和接口实现
- 数据结构、协议、配置和序列化格式
- 单元测试、集成测试、Mock 和测试夹具
- 文档、示例、迁移与兼容层
- 删除或重命名后的残留引用

新增 Option、builder、环境变量、URL 参数或配置字段时，必须从公开入口设置非默认值，沿配置对象、URL/上下文和依赖传递追到真实运行时消费端，并断言最终可观察行为；只验证 Setter、配置对象或 URL 已写入不构成需求闭环。

修改兼容模式、协议标记、序列化或成对转换规则时，不得仅凭字面值相近认定语义等价。核对选择逻辑、传输编码、载荷、服务端解码和 schema/tag 的相关链路；验证证据应能排除默认值、宽松匹配或 fallback 掩盖错误，必要时执行 Base/Head 最小探针。

---
