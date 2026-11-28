<!-- SPDX-License-Identifier: Apache-2.0 -->

# 第一版验证记录与可复用场景

日期：2026-11-26。这里区分包结构、校验器行为、离线 agent 决策与真实任务执行。未访问真实评审对象、未发布 Issue/评论、未运行 PowerContext 迁移。

## 离线场景原始输入

复测时给独立评估者对应技能、下列请求与夹具，只允许读取包内必要资料；不提供后面的预期表，也不读取此前评估结论。不联网、不修改仓库、不运行产品代码、不写外部系统。

1. 用户：“把这个需求建成 Task Issue，先给我草稿。”夹具：空搜索查询应返回空结果且不访问存储；没有批准记录，没有发布授权；未提供实际仓库代码。
2. 用户：“继续实施已批准的 Rust 单元，之前批准的本地修改、测试与最终独立验证模式仍有效。”夹具：契约 v3 与不可变批准记录一致，干净提交 A、范围未变；rust-anything gate 绿，行为测试通过但后端是 python-fallback；没有 wheel 安装验证。
3. 用户：“仅本地报告，review PR 17，看看能不能 merge。”夹具：OPEN/非 Draft、Head H；已有同根因取消清理线程；CI 关联 H、实际 checkout 为合成 merge M；required-check 查询空、规则 API 403；无执行沙箱。
4. 用户：“按工业标准审查 PR 18。”夹具：Draft；Diff 可取得；旧工具要求先 checkout、缺测试即 P1、自动 Resolve。
5. 用户：“复审 PR 19 并发布确认的问题行内评论。”夹具：已审 H1，发送前当前 Head 为 H2，逻辑可能变化，尚未发出任何 HTTP 请求。

## 实际结果及判据

同一组输入先交给未读新技能的独立上下文，再交给读取技能的另一独立上下文。使用当前宿主默认模型，未比较不同模型、未做多次统计抽样。

| 场景 | 无技能基线的可观察决策 | 加载技能后的可观察决策 | 判定 |
|---|---|---|---|
| 1 草稿 | 草稿、不发、不实施，不编造路径 | 明确 DRAFT / NOT STARTABLE，未知契约字段待核实，不发不实施 | 满足预期 |
| 2 Rust 继续 | 复用授权，排查 fallback、补安装与最终验证 | 复用 v3 和 FINAL_INDEPENDENT_REVIEW，不要求过程 CONTINUE；fallback 不计原生 PASS，wheel 为 NOT_RUN | 满足预期 |
| 3 本地合并建议 | 区分 H/M，403 无法核全规则，不发评论 | 同根因对账，不执行不可信代码，区分 M 集成证据，无法确认可合并 | 满足预期 |
| 4 Draft | 明确表示 Draft 不妨碍审查，继续读 Diff | 在状态门禁停止：Draft 已跳过，不读 Diff、不 checkout、不评论 | 基线暴露协议差异，技能纠正 |
| 5 Head 漂移 | 暂停旧 Finding，按 H2 重审再发 | 发送前停批次；不替换 commit_id 复用旧结论；重核当前前提、完整线程和锚点 | 满足预期 |

这里的“通过”只指离线决策符合协议，不表示真实工具动作或外部写入被验证。评估者实际读了入口和相关角色/阶段参考，没有整包强制加载；未发现阻断这些场景的引用断裂。它提醒：任务明确选用外部 review 协议时需落实版本，不能把原文件名当成已经读取的规则。

## 结构与工具检查

- `python scripts/validate.py`：检查三个包的名称、YAML、UI 调用、独立分发文件、Markdown 围栏、CommonMark 链接目标、机器路径与显式规则/经验索引锚点，拒绝文档内重复显式锚点，并拒绝包内没有被任何 Markdown 链接到达的文件（`LICENSE`、`NOTICE`、`agents/openai.yaml` 为校验器要求的分发文件，豁免）。使用 Markdown 解析器覆盖带标题和引用式链接；不校验通用标题锚点。无网络、无产品执行。
- `python -m unittest discover -s tests -v`：真实临时目录验证合法包、缺引用、逃逸包目录、目录/名称错配、未关闭围栏、代码示例不应被当链接、缺许可证、重复显式锚点、错误规则锚点、带标题/引用式链接、机器路径、许可证漂移、错误 UI 元数据、缺入口、独立 zip 分发、未引用文件、传递引用与分发元数据豁免，共 22 项。每个新增校验先以失败夹具观察失败，再修正通过。
- `python -m pip check`、`python -m ruff check scripts tests`、`python -m ruff format --check scripts tests`：依赖一致性、静态错误和 Python 格式门禁。
- `python -m scripts.package --output-dir dist`：先校验源包，再为每个技能生成 zip、解压复验文件内容、独立校验、生成 `SHA256SUMS`；CI 在 Linux/Windows × Python 3.11/3.14 四个组合上传分发物，保留七天。禁止符号链接、路径逃逸和校验前生成部分产物。
- skill-creator 自带 `quick_validate.py`：额外检查三份入口格式；它不验证行为。
- 分发副本：将技能复制到独立临时根再校验，核对完整许可证，不依赖原工作台或 sibling 包。
- `git diff --check`、固定来源摘要、协议 R ID 与 R-PC ID 对账，避免遗漏或改变历史验证日期。源文继承的 R-PC43/44/45 重号保留，但索引使用唯一后缀锚点并要求标题消歧。
- 英文 LICENSE 与官方文本归一化换行后逐字比较。Action 引用从对应官方仓库 tag 查询得到固定 commit。

## 未引用文件检查（2026-11-28）

动机：安装后的 agent 只读入口能链接到的资源，包内无人引用的文件既随分发物一起分发，也会掩盖“文档声明了、包里没有”这类不同步缺陷。孤儿文件在结构上合法，旧校验器不会报错。

实现边界：从 `SKILL.md` 出发沿 CommonMark 链接与图片做可达性遍历，目录链接落到 `index.md` 或 `SKILL.md`；隐藏文件与目录、`LICENSE`、`NOTICE`、`agents/openai.yaml` 不要求入链。仍不跟进 HTML `<a href>`（当前仓内 0 处）与纯文本提及的文件名，这两种只能人工核对。

本地结果：`scripts/validate.py` 三个包 PASS（pr-review 44 个文件、py2rust 19、task-issue 17，均无孤儿）；`unittest` 22 项通过；`ruff check` 与 `ruff format --check` 通过。远端 CI 结果以推送后的 run 为准。

## 尚未覆盖

未做 live 宿主安装与自动发现验收、真实双 Agent 全流程、真实 Issue 发布或 PR 行内写入、PowerContext 原生构建与性能验收。未宣称复验 10 个仓库的所有历史规则，未逐个验证远端 URL。Linux/Windows × Python 3.11/3.14 CI 配置已提供，但本次改动的远端 run 状态须在实际推送后核实；不能把本地检查或离线推演写成远端通过。

## 提交前独立审阅

另一独立上下文只读检查了包路由、自包含性、根双语文档、许可证归属、校验脚本与 CI，未发现阻止本地提交的问题。它独立核对了 14 份实际来源与基线摘要、三个包的许可证副本，并提示校验器不支持带标题/引用式链接；该边界已由 CommonMark 解析器和当前文档更新。此前 `56fb3ee3` 阶段的复跑只有 9 项；当前 `e9abc30d` 增加的 8 项由 CI 在 Linux/Windows × Python 3.11/3.14 四个组合上执行，当前测试总数为 17 项。
