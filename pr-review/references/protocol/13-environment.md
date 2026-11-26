<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 13. 附录：环境诊断入口与路径约定（非门禁）

本节提供资料入口，不保存环境实测基线，也不增加独立门禁。环境故障按 `R05` 归类，验证平台按 `R06` 选择，实际诊断记录及其适用范围保存在 `review-experience.md` 或仓库补充文件。不能仅凭相同错误文本认定根因相同。

### 13.1 网络与 loopback 故障

网络超时的取证与替代验证见 `R05`、`R06A`；先查适用的经验与仓库规则，没有当前证据时不预设 loopback 被阻断。Base 同样失败只能说明该失败不是当前 Head 独有，环境问题与仓库基线缺陷仍需分别定位。

### 13.2 行尾与格式化差异

工作区污染判定见 `R03`，格式化异常的工具、配置与提交 blob 核对见 `R05`。具体格式化器及 clean filter 的诊断方法查 `review-experience.md` 的“无 check 模式格式化器的只读门禁”章节；不以 Windows、CRLF 或 Base/Head 同时报差异自动判定为行尾噪声。

### 13.3 平台专属构建问题

支持平台与验证范围见 `R06`，失败归类见 `R05`。符号所在文件未被直接修改，并不能单独证明问题属于 Base；构建选择、依赖或调用方变化也可能使错误首次出现。

### 13.4 各平台镜像根路径 `{REVIEW_ROOT}`

显式提供的非空 `{REVIEW_ROOT}` 优先使用。变量缺失或为空时，默认使用当前用户 home 下的 `pr-review/`；调用环境也可传入其他任务专属目录。根目录及本 PR 子目录不存在时按需创建；若目标不可写或创建失败，停止 checkout 并报告阻塞，不静默改用其他位置。按 `R03` 在根目录下划分职责。

| 平台 | 取值 |
|---|---|
| Windows | `%USERPROFILE%\pr-review` |
| WSL / Linux / macOS | `$HOME/pr-review` |

在默认根目录下，每个 PR 使用 `{REVIEW_ROOT}/[owner]-[repo]-pr-[PR_NO]`。WSL 使用运行该任务的 Linux 用户 home；Windows 使用当前 Windows 用户的 profile。

### 13.5 环境资料的时效性

环境资料的元数据要求见 `R13`。`validated_at` 对应实际验证日期，编辑日期不能替代；换用执行环境、工具链或支持平台后，按条目的 `recheck_when` 重新核对。缺少适用证据的环境条目只能作为调查线索，不支持 PR 定级或“可 Merge”结论。
