---
name: py2rust
description: Use when profiling a Python project and considering Rust for a performance-sensitive unit, or when planning a complete Python-to-Rust application migration. 适用于 Python 项目的 Rust 性能优化或完整迁移，不用于一般 Rust 编码。
license: Apache-2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Python 项目的 Rust 优化与迁移

面向任意 Python 项目，按可观察行为划分迁移单元，固定 Python 参考，证明真实入口执行 Rust 且满足契约，再判断收益。性能驱动的增量迁移与完整 Rust 应用有不同的完成标准。PowerContext 是来源案例，不是目标仓库前提。

## 选当前阶段

- 分析选型：读[任务参数](references/setup.md)、[项目边界](references/baseline.md)、[选型与工具所有权](references/planning.md)，交付有负载依据的候选和计划。首次模糊请求停在分析，不擅自迁整库。
- 实施或恢复：核对批准单元与已有授权；读[正确性与验证组织](references/correctness.md)、[单元循环](references/implementation.md)、[桥接与安装](references/packaging.md)、[门禁](references/gates.md)、[相关语义](references/semantics.md)。只展开本单元适用项。
- 跨会话接手：读[状态与证据](references/state.md)，核对实际源码、录制语料和二进制身份。未改变的既定工具组合与授权无需重批。
- 报告：采用[统计纪律](references/reporting.md)与[交付格式](references/delivery.md)。完整节号导航在[索引](references/index.md)。

## 必须守住的迁移判据

1. 核实目标仓库规则、Python 支持范围、manifest、lockfile、toolchain 和 CI；本包中的历史路径或工具能力不是当前事实。按项目实际边界选择 Rust workspace，不因迁移改变无关服务、工具链或公共接口。
2. 默认按性能驱动模式逐单元推进。只有明确要求完整 Rust 应用时，才以完整产品入口脱离 Python 运行时作为目标；“非热点”不能取消完整应用的必需功能。
3. 分别固定主流程所有者、产码路线、行为验收工具和主计时器；按风险和仓库现状选用工具，不把本包的历史工具组合当成必选项。一个单元只允许一个主工具管理桥接、录制和入口替换，避免多工具覆盖同一 shim、语料或路由。不要求批量安装所有列出的工具。
4. **三类证据缺一不可**：保持断言强度的行为测试；固定 Python oracle 的无损差分；真实入口加载本次 Rust 构建的身份与后端证据。测试必须能强制 Rust 且禁止回退，Python fallback 全绿不算 Rust 验收。
5. 工具 gate 通过不代替真实调用、安装与产品验收。开发环境扩展可导入后，还要在干净环境安装 wheel，从公开入口验证后端、成功和相关失败路径。目标平台未运行、静默 skip、零用例如实记录。
6. 等价移植核对返回类型、异常、Unicode、数值、排序、状态、副作用和持久化身份。既有缺陷另行提出，不能悄悄混成行为修复；golden 编码与比较规则不得丢失语义或靠通配掩盖差异。
7. 同负载、构建档位和资源下测量，计入桥接、转换与分配；分清并行收益和语言收益。性能阈值提前确定，未达到时可建议保留 Python或调整批量边界。

## 权限与组合使用

用户已授权具体单元时继续本地实施和验证。新服务边界、持久化兼容性、默认路由或外部发布范围的实质变化才需要补充决策。录制与 shadow 可能重复副作用，先选择隔离夹具或已批准的重置机制。

本包已收录[任务契约与证据方法](references/task-contract.md)，单独安装可用。若任务明确采用 task-issue，核对原批准记录、固定契约和执行模式；所需独立反馈缺失时不能自降级。迁移过程中借用验证方法不自动开启 PR 评论或经验账本写入。

普通调试在当前范围内自主推进；正式纠偏轮次与失败命令次数分别统计。结论绑定最终源码、语料、配置与产物，区分代码正确性、证据完整性、默认入口接入和发布状态。

来源及导入基线见 [provenance.md](references/provenance.md)。
