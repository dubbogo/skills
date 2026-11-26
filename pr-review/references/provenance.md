<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 来源与导入边界

来源仓库：`alexstocks/arch-practice`；基线提交 `9442590dba504fd8d2dcc093377afd13488226ae`；导入日期 2026-11-26。本次转换采用维护者提供的当前工作区内容，并未修改源工作台。导入日期不是历史规则的实际验证日期。

| 源文件 | 原始字节 SHA-256 | 导入身份 |
|---|---|---|
| [review.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review.md) | `84be0c11190aef04da5996d32f7769d9717e30efec4ef06be982aa3d86e57d54` | 与已提交基线内容一致（忽略 CRLF） |
| [review-experience.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-experience.md) | `1a356172b2d2b882f39788a0db443c0edec059299abb92ab1702639f5d4b5f90` | 工作区包含未提交修订；上游链接仅表示其已提交基线 |
| [review-AlexStocks-getty.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-AlexStocks-getty.md) | `228332a800c984689d78d315feb0c7764eb1f6e75713cd86f200d54cf01ad781` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-admin.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-admin.md) | `6ea512579fb51763140c88b7503310332698e74e62796a82b96fca92aeb7ede0` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-getty.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-getty.md) | `234651cc9ae0219dff3fecdc762c08b85ad1b6fc9510a32d875792cff577bf66` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-go-pixiu-samples.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-go-pixiu-samples.md) | `2daaa4f057abb9b67d0211df609aa0ebdfef06aa4dc80cbda1de3d310f4f3ef7` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-go-pixiu.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-go-pixiu.md) | `ef06bdd50bc16a07c269dbdfe80670896cdd2afba136b5acbe33e7e2f443481e` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-go-samples.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-go-samples.md) | `0e0a86962a9e6fc669064f01e7265a7107ee414daef17d2c34d7e3f107500ea1` | 与已提交基线内容一致（忽略 CRLF） |
| [review-apache-dubbo-go.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-apache-dubbo-go.md) | `b36a99e7b126887741d9fc52e78827c7870f8b433715ca0b74216053e194fce6` | 与已提交基线内容一致（忽略 CRLF） |
| [review-arana-db-kiwi.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-arana-db-kiwi.md) | `c065c12ce404135ffe973da9950f17ea05e58e4a5e4dbc0b719457616d87c3ea` | 与已提交基线内容一致（忽略 CRLF） |
| [review-dubbogo-gost.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-dubbogo-gost.md) | `ca18b3e943618874c02f476bb6e097a85bbd514880905ebd19d4601d8ede7b24` | 与已提交基线内容一致（忽略 CRLF） |
| [review-oceanbase-powercontext.md](https://github.com/alexstocks/arch-practice/blob/9442590dba504fd8d2dcc093377afd13488226ae/alg/openclaw/review-oceanbase-powercontext.md) | `a1a9772913adbd66cff8c63d57eb2a10776fcf15361cadfb6c557b4b14fb3e37` | 工作区包含未提交修订；上游链接仅表示其已提交基线 |

转换：提炼技能入口，按原章节和风险索引拆分，保留原稳定规则 ID；将个人机器路径示例参数化，补足包内导航与许可证。原文外部链接仅保留作来源，不要求安装所提及的全部工具，也不将历史结论当作当前事实。新入口与本包参考资料构成本版本的维护源，不自动追随上游工作区。

完整导入通用协议、10 个仓库的补充规则和跨项目诊断条目。退役经验中“回复自动改变 resolved 状态”“同根因残留另开线程”和未经授权 Resolve 的冲突处理，以 R11/R12 与 §8 为准。经验索引 ID 在本次首次分配，后续不重排。未执行这些历史 PR 的动态复验，未验证外部链接或当前 GitHub 规则。

继承的 R-PC43、R-PC44、R-PC45 重号保留原身份；索引以标题和唯一后缀锚点消歧，未擅自重排编号。
