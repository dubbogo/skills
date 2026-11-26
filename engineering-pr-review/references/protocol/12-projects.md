<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 12. 项目补充规则

通用协议与项目补充规则同时生效：

```text
review.md                    # 协议与门禁（强制）
review-experience.md         # 跨项目诊断经验与环境基线（参考）
review-[owner]-[repo].md     # 仓库专属规则（该仓库内强制）
```

项目文件只保存该仓库特有的语言命令、模块风险、架构约束和测试要求。已确认仍适用于当前 Base/Head 的项目规则优先，但不得降低本协议的安全性、正确性和可验证性最低标准，也不得覆盖 §0.4 的底线；缺少或失效的时效性元数据不具有优先级。

**仓库文件的强制结构**：

1. 首行注明"与 `review.md` 同时生效，只记录该仓库专属内容"。
2. 规则用 `R-<短名><NN>` 编号（如 `R-PC01`），只追加、不重排。
3. 时效性条目按 `R13` 在条目或所属章节集中记录元数据；稳定不变量不机械添加。
4. 引用本协议时只用规则 ID（如 `R05`、`R11`/`R12`、§8、§9），禁止引用行号。

旧命名 `review-protocol-[repo].md` 或 `review-[repo].md` 在下次审查该仓库时迁移为 `review-[owner]-[repo].md`。迁移时先去重，并重新验证时效性条目的当前适用性；仍有效的稳定规则不改变语义，失效规则按当前证据修正或删除。

---
