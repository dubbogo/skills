<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dubbogo Skills

中文 | [English](README.md)

面向需求分析、任务交接、PowerContext Rust 迁移与工程化 PR 审查的 agent 技能。第一版将 `alexstocks/arch-practice/alg/openclaw` 中的流程转为简短入口，按角色、阶段和风险加载参考资料。

这是 Dubbogo GitHub 组织下的社区仓库，不宣称属于 ASF 项目或获得 ASF 背书。Apache-2.0 表示许可证，不表示项目归属。

## 技能目录

| 技能 | 使用场景 | 交付物 |
|---|---|---|
| [task-issue-harness](task-issue-harness/SKILL.md) | 核实需求、拆 Task Issue、执行已批准契约 | 可审阅的契约与带证据的编码交接 |
| [powercontext-rust-migration](powercontext-rust-migration/SKILL.md) | 分析或实施 PowerContext 的 Python → Rust 单元 | 行为差分、原生路径、wheel 安装及性能证据 |
| [engineering-pr-review](engineering-pr-review/SKILL.md) | PR 初审、更新复审、合并条件判断 | 当前快照的问题及获授权的行内评论 |

Review 包含 10 个仓库的项目规则和历史诊断索引，分别匹配 fork 身份。诊断经验不自动增加检查门禁。

## 安装

克隆仓库后，将需要的技能**整个目录**复制到宿主支持的发现目录。例如，在克隆根目录执行：

```powershell
$skillName = 'task-issue-harness'
$skillRoot = Join-Path $env:USERPROFILE '.agents\skills'
$destination = Join-Path $skillRoot $skillName
if (Test-Path -LiteralPath $destination) { throw "Already installed: $destination" }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath (Join-Path (Get-Location) $skillName) -Destination $destination -Recurse
```

```sh
skill_name=task-issue-harness
skill_root="$HOME/.agents/skills"
mkdir -p "$skill_root"
if [ -e "$skill_root/$skill_name" ]; then
  echo "Already installed: $skill_root/$skill_name" >&2
  exit 1
fi
cp -R "./$skill_name" "$skill_root/$skill_name"
```

目标已存在时示例会停止，避免覆盖旧安装。宿主使用其他路径时采用其实际配置；按宿主要求刷新或重开会话，先确认技能已列出。每个包自带 `LICENSE`、`NOTICE`，不依赖相邻技能、原工作目录或必需 MCP 服务。安装由用户选择执行，不自动改全局 agent 配置。

## 调用

```text
使用 $task-issue-harness 核实需求，仅给出 Task Issue 草稿。
使用 $task-issue-harness 执行已批准 Issue，沿用有效的权限与执行模式。
使用 $powercontext-rust-migration 分析首个候选单元，先不实施。
使用 $engineering-pr-review 审查这个 PR，仅本地报告，不发评论。
```

自动发现技能不增加发布、推送、合并或部署权限。遵循当前用户指令，复用有效的既有授权；审查只选一份通用协议，不叠加冲突旧技能。Harness 保留契约批准与执行模式开工条件。

## 结构与维护

每个技能包含 `SKILL.md`、`agents/openai.yaml` 和参考资料；Task Issue 模板放在 `assets/`。仓库另含 `scripts/validate.py`、校验器回归测试、`.github/` 协作模板与 CI，以及 `docs/` 转换依据。

详见[架构](docs/architecture.md)、[来源](docs/provenance.md)、[导入清单](docs/source-manifest.json)及[行为验证](docs/validation.md)。本仓库是这些技能包的维护源，运行时不访问原工作台，也不自动同步上游。导入摘要区分工作区修订与已提交基线，导入日期不代替历史验证日期。社区文档中英文对照，技能正文与参考资料当前以中文提供。

## 校验

仓库校验需要 Python 3.11 及以上，使用技能本身不要求 Python。在克隆根目录执行：

```sh
python -m venv .venv
# 按当前 shell 激活 .venv 后：
python -m pip install -r requirements-dev.txt
python -m pip check
python -m ruff check scripts tests
python -m ruff format --check scripts tests
python scripts/validate.py
python -m unittest discover -s tests -v
python -m scripts.package --output-dir dist
git diff --check
```

Windows 不激活环境时，后续 Python 命令改用 `.venv\Scripts\python.exe`。校验覆盖元数据、分发文件、围栏、Markdown 链接、机器路径拒绝及显式规则/经验索引锚点。打包命令为每个技能生成并独立复验 zip，同时写入 `SHA256SUMS`。它不执行技能流程、不验证远端 URL，也不证明 agent 行为。CI 在 Linux、Windows 及 Python 3.11、3.14 组合上运行相同门禁，上传已验证的包，并检查准确的 PR 或推送差异中的空白错误。行为变化应复测[离线场景](docs/validation.md)。

## 协作与许可证

请阅读[贡献指南](CONTRIBUTING_CN.md)、[行为准则](CODE_OF_CONDUCT_CN.md)、[安全政策](SECURITY_CN.md)、[支持渠道](SUPPORT_CN.md)、[变更记录](CHANGELOG_CN.md)，各文档均有英文入口。

采用 [Apache-2.0 英文原文](LICENSE)。[中文许可证](LICENSE_CN.md) 是便于阅读的非官方译文，不替代英文原文。分发时保留 [NOTICE](NOTICE) 与[来源归属](docs/provenance.md)。名称与商标归各自权利人所有。
