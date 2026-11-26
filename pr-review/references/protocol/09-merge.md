<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 9. Merge 结论

分别报告三种结论，不将证据不足写成确定的代码缺陷：

| 维度 | 可用结论 | 判据 |
|---|---|---|
| 代码审查 | 有阻断问题 / 未发现阻断问题 / 审查未完成 | 当前提交的 P0/P1、实际审读范围和未覆盖内容 |
| 验证证据 | 对本次风险充分 / 存在具体缺口 | 相关源码、测试、静态检查及可信 CI 能否支持结论 |
| GitHub 状态 | 满足当前合并条件 / 等待审批或检查 / 存在冲突或其他策略阻塞 / 无法确认 | 实时规则、checks、reviewDecision 和 merge 状态 |

"有阻断问题"说明必须修复的 Finding；"等待审批或检查"说明治理条件；"无法确认"说明缺少什么证据。已确认问题与未完成范围可同时报告。没有发现 P0/P1 不等于已完成审查，也不等于可合并。

`gh pr checks --required` 的 stdout、stderr 和退出码必须保存；pending 通常返回 8，空结果也可能返回非零。该命令只列出已产生且被标为 required 的检查，不能独自确定规则集合。准备给出合并肯定结论、PR 修改 CI/规则或出现缺失/异常检查时，核对目标分支适用的 branch protection、rulesets（包括继承规则）与 merge 状态。可使用以下只读 API 入口；对列表接口必须完整分页，对每个返回的 ruleset id 单独读取规则内容，并把目标分支名按 URL 路径要求正确编码：

```bash
gh api "repos/{owner}/{repo}/rulesets?includes_parents=true&per_page=100" --paginate
gh api "repos/{owner}/{repo}/rulesets/{ruleset_id}?includes_parents=true"
gh api "repos/{owner}/{repo}/rules/branches/{baseRefName}?per_page=100" --paginate
gh api "repos/{owner}/{repo}/branches/{baseRefName}/protection"
```

`rules/branches/{branch}` 用于核对该分支当前生效的 ruleset 规则。rulesets 列表与详情用于核对来源、继承、enforcement、conditions、bypass actors 和规则参数。经典分支保护单独查询 `branches/{branch}/protection`，仅核对经典必需状态检查时可查询 `branches/{branch}/protection/required_status_checks`。分别核对两类规则。空集合仅在请求成功、分页完整且权限覆盖目标范围时说明对应规则来源未发现适用规则。经典保护返回 `403`，或返回 `404` 且无法确认仓库、分支及读取权限时，记为无法确认。按以下情况解释：

- **已确认未配置必需状态检查**：适用规则已核全且没有此要求，空结果不构成缺口，不额外要求一个非空的 required checks 列表。其他审批、部署等规则仍须满足。
- **配置了必需检查但未完成**：逐项说明失败、等待、缺失或未触发，不把总体绿色替代规则对账。
- **规则无法核全**：说明权限、API 或继承规则等具体缺口，合并状态记为无法完整确认。单独的 branch protection 404 不能证明 rulesets 也不存在。

例如已确认仅要求一个 approval，且当前 `REVIEW_REQUIRED / BLOCKED`，应报告"等待审批"，而非"必需检查缺失"。可见 CI 即使非 required，仍可按 `R05` 用作技术验证证据。

只有代码审查完成、无未修复 P0/P1、相关验证充分、完整 Diff 已对账、当前适用规则满足，且最终仓库/PR/目标分支/Base/Head 及适用的 merge result 已按 `R02` 复核时，才能给出“可 Merge”的综合判断。引用旧 Base 对照或旧 merge result 的检查时，必须已证明它们仍适用于当前前提；否则存在验证缺口。该判断不是执行 merge 的授权。

启用 merge queue 时，入队前仅判断当前入队条件；最终合入验证使用当前 `merge_group` SHA 和其必需检查，PR Head 或 `potentialMergeCommit` 不能替代。没有入队时不将尚不存在的 merge-group SHA 记为代码缺陷。只有检查缺失/异常或 PR 修改相关 CI 时，才进一步扫描 `merge_group` 触发配置。

---
