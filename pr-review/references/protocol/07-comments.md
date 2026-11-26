<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 7. 行内评论协议

### R11. 评论位置与 Fallback

按 §0.3 的默认授权发布有证据的 Findings，发布动作无需再次征询；仅在用户要求仅本地报告或不要发评论时停止发布。GitHub 写入仅限两类：在 `Files changed` 的具体问题代码行创建行内评论；在已有同根因的行内线程补充实质性证据。仅本地报告模式下不发布评论。没有问题时不发占位、表扬或"无问题"评论，完成 review 也不产生额外的 GitHub 总结发布步骤。

**禁止的发布通道**：不得使用 `gh pr comment`、`POST /repos/{owner}/{repo}/issues/{pull_number}/comments`、`gh pr review --comment`，或通过 `/pulls/{pull_number}/reviews`、网页、MCP/其他工具发布总评、完成通知、验证清单或无问题总结。不通过 Approve 或 Request Changes 改变正式审查状态。即使全部 Findings 已发布行内评论，也不得再向 PR Conversation 或 review body 重复汇总；§10 只输出到当前用户聊天。

**`LGTM` 一类表态本身不禁止**：在已有行内线程内回复具体问题时可使用，但必须同时给出问题位置与依据；不得单独发送无锚点表态，不得以它替代 Finding 的证据，也不得用它把未完成审查表述为通过。

**锚点必须对应问题**：`path` 指向实际存在缺陷的文件，`line` 指向触发或导致缺陷的具体代码行。确实无法直接评论该行时，只能选择同一根因直接相关、能够说明问题的 Diff 行，并在正文写明真正的缺陷位置；不得挂到无关新增行、文件首行或 PR 描述来凑锚点，也不得用 `subject_type=file` 的文件级评论代替具体行。没有相关可评论行时走 Fallback。

形成 Finding 时保存 `reviewedHeadOid` 及所依赖的 Base、目标分支和 Diff 基准。提交前按 `R02` 核对快照，确认当前 `headRefOid` 仍等于 `reviewedHeadOid`、Finding 的前提仍成立，并确认 `commit_id`、`path`、`line`、`side` 对应这个 Head 的当前 Diff。删除行使用 `side=LEFT`；新增或上下文行通常使用 `side=RIGHT`。

**Fallback（定义）**：当一条 Finding 无法锚定到任何**与该根因直接相关**的可评论 Diff 行时（典型情形：缺陷位于 PR 正文、提交信息或仓库外内容），只记入当前用户聊天的收尾报告（§10），标注"未发布 + 原因 + 实际位置或已核实的大致位置"。不编造行号，**禁止退化为 Conversation 评论或 review 总结**。已有同根因行内线程时先按 `R12` 复用该线程，只有确实无线程可用才进入 Fallback。

最小请求示例：

```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments --input comment.json
```

```json
{
  "body": "[P1] 问题说明",
  "commit_id": "当前 headRefOid",
  "path": "src/example.go",
  "line": 123,
  "side": "RIGHT"
}
```

API 成功后回读评论，核验 `body`、`html_url`、`commit_id`、`path`、`line`、`side`，确认实际锚定当前审查 Head 的问题行；仅有 HTTP 成功或 URL 不算发布完成。正文格式错误（服务端已落库）应原地 `PATCH .../pulls/comments/{comment_id}` 修正，**禁止重复创建评论**；锚点不符时记录发布缺口，不把它算作已正确发布，也不补发 Conversation 总结。请求被拒绝（未落库）时按 `R12` 处理。

### R12. 行号失败、批次与去重

**批次大小**：默认每批 ≤ 10 条评论，作为缩短发布窗口的操作约定，不表示已测得最优批次。每个小批次发布前按 `R02` 复检快照，并获取完整 review comments 和目标 Diff hunk，**按根因**而非行号或措辞去重。若 Head 不等于 `reviewedHeadOid`，立即停止整批并按 §8 复核新 Head；其他快照变化按 `R02` 复核后再发布。禁止只替换 `commit_id`、路径或行号后提交旧 Finding。

**行号失败的处理**：API 返回 409/422 或行号失败时，先按 `R02` 复检快照。仅当 Head 仍等于 `reviewedHeadOid` 且 Finding 的相关前提已复核，才重新获取目标 Diff hunk 和 comments、校正 `path`、`line`、`side` 后重试一次；Head 已变化时不得按旧快照重试。仍失败则按 `R11` 的 Fallback 记入当前用户聊天的收尾报告，不换用总评接口绕过行号要求。

**线程身份与去重判据**：判断"是否已有同根因线程"时，不得只看行号或评论摘要——同时核对 `path`、`original_commit_id`、当前 `commit_id`、`position`，以及 GraphQL review thread 的 `isResolved` / `isOutdated`。REST review comment 本身不提供 `isResolved`、`isOutdated`；`position == null` 不能替代线程状态。必须通过 GraphQL 查询 `reviewThreads`，并持续分页直到 `hasNextPage=false`；每个 thread 的 `comments` 连接也必须检查 `pageInfo`，若超过 100 条则对该 thread 单独继续分页，不能只读取第一页。

可使用以下查询获取 thread 状态及首批评论；`after` 为空时省略该变量或传入 null：

```bash
gh api graphql -f query='
query($owner:String!, $repo:String!, $number:Int!, $cursor:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100, after:$cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line originalLine
          comments(first:100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              fullDatabaseId id body createdAt
              commit { oid }
              originalCommit { oid }
            }
          }
        }
      }
    }
  }
}' -F owner='{owner}' -F repo='{repo}' -F number=[PR_NO]
```

外层 `reviewThreads` 翻页直到 `hasNextPage=false`；对 `comments.pageInfo.hasNextPage=true` 的每个 thread，使用该 thread 的 `id` 和 `comments` 的 `endCursor` 单独续页。使用 `fullDatabaseId` 作为 REST comment 数字 ID，不使用已废弃的 GraphQL `databaseId`；处理时须保留 64 位整数精度。查询失败、权限不足或分页未完成时，线程去重状态属于未确认，不得假定不存在同根因线程。

已有机器人或人工评论覆盖同根因时，**复用原线程**，不重复创建评论；只有新增实质性证据、修复状态或必要的定级修正时才补充回复。回复必须使用原线程的顶层 review comment ID：

```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments \
  -f body='补充的实质性证据' \
  -F in_reply_to=[TOP_LEVEL_REVIEW_COMMENT_ID]
```

使用 `in_reply_to` 时不得同时提交新的 `path`、`line`、`side` 或 `commit_id`；该回复接口以顶层评论为父节点，不得把另一条回复当作父节点。仓库内存在其他自动审查（CodeRabbit / Copilot 等）时同样适用，见 `R05`。

全部评论提交后再次拉取 Head 和 threads。提交窗口内出现同根因线程时，只记录竞态与时间顺序，不擅自删除、Resolve 或追加 Conversation 评论；若 Head 已漂移，标记本轮评论和结论基于旧 SHA、回到新 Head 复审，不把已成功提交到旧 SHA 的评论冒充当前证据。同一行多个小问题合并为一条。

---
