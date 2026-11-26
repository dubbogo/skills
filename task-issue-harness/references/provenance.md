<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 来源与导入边界

来源仓库：`alexstocks/arch-practice`；基线提交 `9442590dba504fd8d2dcc093377afd13488226ae`；导入日期 2026-11-26。本次转换采用维护者提供的当前工作区内容，并未修改源工作台。导入日期不是历史规则的实际验证日期。

| 源文件 | 原始字节 SHA-256 | 导入身份 |
|---|---|---|
| [issue-harness.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/issue-harness.md) | `e8f4291a4bfd0a7a4c7add7c0f35821a9a42cf9ea30eb57a49b231b23e3b9fd1` | 与已提交基线内容一致（忽略 CRLF） |

转换：提炼技能入口，按原章节和风险索引拆分，保留原稳定规则 ID；将个人机器路径示例参数化，补足包内导航与许可证。原文外部链接仅保留作来源，不要求安装所提及的全部工具，也不将历史结论当作当前事实。新入口与本包参考资料构成本版本的维护源，不自动追随上游工作区。

原文第三节的完整 Issue 模板单独放入 assets；规划、编码与验证分别加载。原文对 Tack 的描述保留固定提交来源，不表示本包依赖 Tack。
