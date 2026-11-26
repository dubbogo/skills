<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

# 存储、身份与迁移

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

<a id="exp-047"></a>

## 产品测试对「工作树字节」做哈希时，先核 `.gitattributes` 与检出配置

- `validated_at: 2026-10-19`、`validated_ref: oceanbase/powercontext PR #2078`（head `3f6163cd`，文件 `evaluation/memory/atomic_extraction/manifest.py`）、`applies_to: 任何把夹具/生成的字节哈希写进仓库（golden hash、已 pin 报告、契约摘要）并由测试断言的改动`、`recheck_when: 仓库引入全局 `* text=auto` / `eol=lf`，或哈希改成归一化后计算`。
- 与「审查镜像比对」那一条不同：那里是审查者自己拿 `git archive` 产物和 API blob 比对，归一化即可；这里是**被测代码**拿工作树字节和仓库里固定下来的 blob 哈希比对，问题落在产品测试本身。
- 判定三步：① `git cat-file -p <ref>:<path> | sha256sum`（blob）；② 工作树同文件 `sha256sum`；③ 若二者不等、而 `\r\n`→`\n` 归一化后相等，就是纯行尾差异。Git for Windows 默认 `core.autocrlf=true`，除 `.gitattributes` 显式 `text eol=lf` 的路径外都会变成 CRLF；`git archive` 产物在本机表现相同，可直接当探针树。
- 最小反证：同一 head 复制两棵树，只把该夹具归一化为 LF，跑同一用例，得到 `1 failed → N passed`。这比读代码推断快，也不需要真实外部依赖。
- 报告口径：先确认该测试是否在默认收集范围（`testpaths`/`make test`），再看 CI 矩阵是否有对应平台的 job —— 两者都不覆盖时，正确结论是「本地开发被破坏且 CI 不可见」，不是「CI 全绿所以没问题」。定级按「不改变产品行为」给 P2。

<a id="exp-061"></a>

## 跨后端 e2e 用「整条记录相等」断言持久化契约，必然在某个后端变红

- `validated_at: 2026-10-21`、`validated_ref: oceanbase/powercontext PR #1717`（head `57a821f2`，`tests/e2e/test_source_declaration_contract.py:261`）、`applies_to: sqlite / mysql / oceanbase / seekdb 多后端参数化的 e2e 里比较 ORM 模型或 dataclass 全等的地方`、`recheck_when: 方法类，长期有效`。
- 现象：同一用例 `assert await records.get_artifact(...) == restored` 在 sqlite 全绿，在 OceanBase 与 SeekDB 同时红，而两侧 `revision` / `restored_from_revision` / `reason` / `created_by` / `sources` / `content_digest` 全等，只有 `created_at` 不同。
- 两种失效机制要分开写清：① 列由 `Column("created_at", DateTime(timezone=True))` 经 `CreateColumn` 生成 MySQL `DATETIME`（无小数秒）⇒ 写入 `00:50:09.931190` 落库被取整成 `00:50:10`，回读必然与写入值不等；② 嵌入式后端保留微秒，但读回值比写入值**早**（`.476426` vs `.478797`）⇒ 写路径返回的对象与它自己落库的行不同源，不是精度问题而是返回值语义问题。
- 判据：失败字段集合只剩时间戳 ⇒ 先判「断言过严」，不要顺着"元数据没保住"写 Finding（本例 `restored_from_revision`/`reason` 都正确）。只有当时间戳是作者本次要保证的不变量时，才升级为产品缺陷。
- 处理建议二选一：逐字段断言 + 时间戳按后端精度归一（秒级），或让写路径复用落库时间戳；同时指出该 PR 因此让两个后端 job 直接红，不能只报"用例红了"。

<a id="exp-150"></a>

## 作者把 master 合进 PR 分支后：派生的摘要/指纹必须按「三方各算一次」判，两个父提交自洽不代表合并树自洽

现象（2026-11-16 实测 `oceanbase/powercontext` #2674）：PR 自己把 `release/upgrade-support.json::persistence_sha256`
改对了（`fafd4c51` 摘要 == 声明），master 也自洽（`ad0d0206` 摘要 == 声明），作者随后推了一个
`Merge master into <branch>`，把声明值写成**合并前 PR 树**的值。合并同时带入了 master 侧对 `MANAGED_INPUTS`
（`migrations/mysql_schema.py`、`server_resources/plugin_artifact_readiness.py`）的改动，于是合并树摘要变成第三个值，
三个 commit 分别是 `6029d8ac` / `0fe382bd` / `a61fdf68`，声明的仍是 `6029d8ac`。

判据：

1. head 是 merge commit 时（`git log -1 --format='%P'` 两个父），对**父1、父2、head 三个树**分别跑同一算法
   （本例 `scripts/upgrade_release_gate.py::managed_digest`）。两个父各自相等、head 不等 ⇒ 只能归因于合并解析，
   不要回头质疑算法或基线。
2. 这类派生值（内容摘要、schema 指纹、契约 sha256、`managed_digest`）**不能沿用任一侧父提交的值**，必须在合并树上重算；
   合并提交里它会以「相对 master 的一次修改」出现在 diff 里，正好是最合适的评论锚点（`side=RIGHT` 的该字段行）。
3. 别只看「合并后 CI 还没跑完」就跳过：本例合并后 `CI preflight` 仍是 `queued`，而重算已能确定该门禁必红
   （`upgrade-policy-check` 是 `make check` 的前置），这属于源码级判断，不是猜测。
4. 反向的坑：`rationale`/说明文本被换成 PR 侧内容往往**是对的**（PR 新增了 revision，说明必须覆盖它），
   不要把它和摘要一起当成「合并丢内容」；先确认 master 侧那份文本描述的 revision 是否已被本 PR 取代。

`validated_at: 2026-11-16`、`validated_ref: #2674 head 2bdd5b77（父 fafd4c51 + ad0d0206）`、
`toolchain: Windows / CPython 3.14.3（工作区 .venv）、LF 归档树`、
`applies_to: 任何 head 为 merge commit 且仓库用内容摘要做门禁的 PR`、
`recheck_when: 门禁摘要算法或其输入集合变化`。
