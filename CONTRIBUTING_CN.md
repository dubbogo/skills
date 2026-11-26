<!-- SPDX-License-Identifier: Apache-2.0 -->

# 贡献指南

中文 | [English](CONTRIBUTING.md)

可为可复现问题或流程建议创建 Issue，也可提交聚焦 PR。使用问题见[支持渠道](SUPPORT_CN.md)，敏感报告见[安全政策](SECURITY_CN.md)。禁止公开凭据、私有代码、用户数据或完整 agent 会话。

欢迎有证据且适用范围明确的决策规则、附固定引用和真实验证日期的项目资料修正、保留授权边界的入口精简，以及带最小回归夹具的校验器修复。

`SKILL.md` 保留触发条件、核心约束和参考导航。包内相对链接不依赖相邻技能或作者机器路径。可独立分发的技能保留完整 `LICENSE`、`NOTICE`。协议和项目规则 ID 不重排；历史诊断放入参考资料，不变成通用门禁。

## 提交前

1. 按 [README](README_CN.md) 准备 Python 环境。
2. 运行 `python -m pip check`、`python -m ruff check scripts tests`、`python -m ruff format --check scripts tests`、`python scripts/validate.py`、`python -m unittest discover -s tests -v`、`python -m scripts.package --output-dir dist`、`git diff --check`。
3. 行为变化复测[离线场景](docs/validation.md)，有独立上下文时使用独立评估者，只提供原始请求与夹具，不提供预期答案。不为测试指令而操作真实远端资源。
4. PR 说明结果行为、证据、限制和来源；中英文社区文档同步，技能参考正文当前为中文。

结构校验不证明行为。搬移文本不等于复验旧 PR 或环境。阅读[来源说明](docs/provenance.md)，核实贡献权利并保留归属；新增第三方文本、资产、依赖需说明来源和许可证义务。

必需工作流会在 Linux、Windows 以及 Python 3.11、3.14 组合上运行这些门禁。PR 按准确的 head 和 base 提交检查，推送按前一个提交检查。CI 会保留分发包七天，便于审阅。

除明确另行说明外，贡献按 Apache-2.0 提交，且必须是有权贡献的内容。本仓库不建立 ASF CLA 流程，也不要求 ASF committer 身份。维护者审查行为与范围，CI 通过不自动授权合并。
