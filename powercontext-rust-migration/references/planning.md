<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 4. 分析阶段：交付可评审的选型计划

先按单元选择主工具并核查实际版本、来源提交、可执行路径和帮助；MCP 不可用时可用对应 CLI。不要把迁移工具自身的构建要求、MCP 运行环境和 PC 交付 crate 的工具链混为一谈，生成器给出的 MSRV 也需按实际代码与依赖验证。

- `rust-anything`：迁移分析、桥接、录制、差分和工程检查，可作为既有迁移任务的主工具。
- `fast-anything`：热点分析、真实调用抽样和受控加速试验；比较器、编码、错误与导入回退规则必须按本单元契约核对。
- `rocq-of-rust`：对已稳定纯算法选择性建立规格与证明；转译成功、证明满足规格、与 Python 行为对应分别报告，不设为所有迁移的统一前置门槛。
- [Hypothesis](https://github.com/HypothesisWorks/hypothesis)：按批准输入域生成测试输入、缩减失败样本；补充固定 golden 与既有行为测试，不是 Python→Rust 转译器。
- [pyperf](https://github.com/psf/pyperf)：校准、重复测量和保存 Python 调用入口的原始性能结果；按 §4.1 作为主计时器，内置 bench 辅助诊断，不作为正确性或服务 p99 的证明。
- [py2many](https://github.com/py2many/py2many)：Python→Rust 的候选转译路线；只在选定的独立试验目录生成代码，逐项核对类型、依赖和语义。
- [Depyler](https://github.com/paiml/depyler)：另一条 Python→Rust 候选转译路线；官方支持表和 `--verify` 只作为待验证能力输入，不能据此宣布 PC 等价迁移完成。

一个单元只由一个主工具管理桥接、录制与入口替换；其他工具可提供辅助证据，不并行覆盖同一 shim、语料或后端选择。公共背景与完整示例见 [迁移实践 Discussion #2822](https://github.com/oceanbase/powercontext/discussions/2822)，执行仍以当前仓库规则和获批任务为准。

### 4.1 工具重叠、所有权与裁决

| 编号 | 重叠或冲突 | 必须由任务明确的选择 | 当前状态 |
| --- | --- | --- | --- |
| D1 | py2many、Depyler 与 coding agent 都可产出 Rust；接入后也会影响 anything 工具管理的生成文件 | 保留 coding agent 直接移植主线；py2many、Depyler 先在同一小单元、不同独占目录做对照试验 | 已确定采用此组合；转译器接入具体产品单元前，根据同一验收标准的试验结果再选定实现 |
| D2 | pyperf 与 rust-anything/fast-anything 的 bench 都能提供耗时比较 | pyperf 作为真实 Python 调用边界的性能验收主计时器，内置 bench 辅助诊断；比较必须覆盖相同输入、桥接和调用边界 | 已确定采用此组合；原合同要求的 bench/gate 继续执行，既有验收阈值和完成条件保持有效 |
| D3 | rust-anything 与 fast-anything 都可能管理桥接、录制和入口替换 | 一个单元选定一个主流程所有者；其他工具只提供明确的辅助证据 | 沿用任务既有选择；更换时裁决 |

Hypothesis 的生成与缩减可补充 anything 工具的固定录制和回放，无需二选一；应共享输入契约与无损比较规范，不重复维护互相冲突的 oracle。Depyler 的 `--verify`、Hypothesis 的有限输入差分和 rocq-of-rust 的规格证明有部分“验证”目标重叠，但证据范围不同，不能互相冒充；需要哪一种证据按具体风险和获批契约决定。

采用以下组合：沿用每个任务既有的 anything 主流程，coding agent 直接移植为主线，Hypothesis 补充固定语料差分，pyperf 负责真实 Python 调用边界的性能验收，内置 bench 辅助诊断；py2many、Depyler 先做隔离对照试验。沿用这一组合无需重复请求选型批准。既有任务的范围、验收阈值和明确要求的 bench/gate 继续有效；不得据此取消旧验收。工具尚未在 PC 实测的能力仍须验证，具体试验单元和转译器默认接入仍按任务范围确定。

### 4.2 候选与任务计划

先固定可重复工作负载与结果，再分析 CPU、I/O/锁等待、已有原生库、启动/IPC、对象转换和复制成本。函数累计耗时不是纯 CPU 占比；涉及异步、原生执行或子进程时补充相应证据。可以先用标准 profiler 或主工具画像定位，关闭 profiler 后再测最终性能。核查更直接的 Python、批量或查询改进，不以静态建议代替收益证据。

计划存为 `{{TASK_DIR}}/PORT-PLAN.md`，只需包含支持本轮决策的信息：

1. **目标与基线**：目标模式、Base/Head、平台、用户授权、成功标准。
2. **候选与负载**：函数/算法边界 → 实际调用方 → 工作负载 → CPU/等待/内存成本 → 拟验证收益。明确区分线上负载、现有基准、离线语料和合成输入；离线探针不能声称代表线上耗时占比。
3. **依赖与桥接**：相关直接依赖、算法实现位置、拟保留的 Python 边界、桥接粒度和数据转换成本。图只在有助于理解时使用，不机械划分 L0→L4。
4. **语义风险**：列出本单元适用的 §8 项，以及已有测试、待补录制和未覆盖行为。
5. **替代库与打包**：核实关键 Rust 库的版本、功能和语义差异；标明 `unknown`，不得据名称相似就认定可替换。定义 wheel、支持平台、安装与回滚办法。
6. **不迁/后置清单**：写明当前收益不足、生态绑定、兼容代价或缺少证据的原因；完整 Rust 模式下改写为未完成依赖，不能静默取消功能。
7. **首个单元与验收**：限定实现、接入、测试和性能范围，说明需要的外部环境。

每个进入实施的单元附一份简短任务契约，直接写在计划对应条目或已授权的任务 Issue 中，不另建重复表单：

| 契约项 | 必须明确的内容 |
| --- | --- |
| 人类概览与目标 | 谁在哪条路径遇到什么成本或限制；完成后的可观察变化；对总迁移目标的贡献 |
| 行为与不变量 | 具体输入、操作、输出、异常；边界两侧与含等关系、单位，以及 `None`、空值、零、未设置、默认值的适用差异；预期来自 RFC、公开契约或经核实的既有行为 |
| 允许与禁止范围 | 已核实的修改入口、文件/模块所有者、允许新增内容与依赖；保护的历史逻辑和典型跑偏示例，例如为分词试点改写数据库检索或升级 gateway 工具链 |
| 依赖与启动条件 | 区分硬依赖、建议顺序和共享文件冲突；硬依赖无环，上游待合并与获准 stacked Base 分别说明 |
| 验收与交付 | 风险 → 场景 → 预期 → 环境 → 命令/产物 → 结果；首个切片、独立验证方式、完成和停止条件 |

新增第三方依赖列明名称、版本范围/锁定版本、来源、用途与许可证依据；超出批准范围时先明确影响，不能借迁移升级无关依赖。多单元并行只在共享接口和所有权已落实时使用独立工作区；共享入口串行修改，不按 Issue 数量机械增加 agent。调查任务交付证据，实现任务交付行为，harness 任务交付设施及运行证据，不把三者的完成状态混用。

`analyze` 的目录、导入环和 `start_here` 是静态建议，不代表热点、真实运行依赖或必须一起迁移的范围。不得据此把整个 `builtin/` 或大目录一次搬走。

可作为分析起点的候选是文本分析核心 `src/powercontext/builtin/artifacts/search.py` 和代码事实提取 `src/powercontext/builtin/code/extract.py`，但它们不构成预先批准的迁移计划。若复用现有离线分析，先记录其提交、语料和证据路径，实施前仍需确认。对前者必须检查 Jieba 词典、`HMM=False`、Unicode 规范化、词项编码与检索投影兼容；不能假定可直接替换。

用户尚未批准具体实施单元时，提交计划供选择；用户已经批准时直接进入该范围，不重复审批同一事项。

### 4.3 四个工具的实施与验收要求

**Hypothesis**：由单元契约定义 strategies、正常和非法输入及相关独立性质。先固定 Python oracle，在同一输入上调用强制 Rust 后端，分别比较结果类型、值、顺序、异常及必要状态；生成数量不等于覆盖率。固定工具版本、策略、预算与回放信息，把合法可公开的最小失败样本或操作序列按 §8 的无损格式纳入回归。构建、安装和后端身份检查放在生成循环外；相关错误实现必须能被比较器检出。只对有状态边界建立状态机，不为简单函数增加通用测试框架。

**pyperf**：按 D2 作为主计时器，固定一个 `pyperf.Runner` 脚本、同名基准、输入身份、单位和计时区间；两端使用可比解释器和资源，Rust 用交付构建档位。确认每个 worker 实际加载参考或 Rust 产物；如选择后端依赖环境变量，仅按所用版本的 `--inherit-environ` 传递必要变量，不继承全部环境。脚本加载、语料解码和验证断言在微基准计时外，产品必需的桥接和转换计入。保存 baseline/candidate JSON、`check`、`compare_to --table`、`metadata` 输出及稳定性警告；验收依据预先批准的工程阈值，不能只凭统计显著或退出码。任务可将这些模板落实为真实路径：

```text
<baseline-python> <benchmark.py> -o baseline.json
<candidate-python> <benchmark.py> -o candidate.json
<analysis-python> -m pyperf check baseline.json candidate.json
<analysis-python> -m pyperf compare_to baseline.json candidate.json --table
<analysis-python> -m pyperf metadata candidate.json
```

**py2many / Depyler**：按 D1 在选定小单元上先做隔离对照，把同一固定 Python 参考分别复制到两个任务独占试验目录，核对当前 CLI，再分别使用 `py2many --rust <copied-unit.py>` 或 `depyler transpile <copied-unit.py>` 等已核实入口。不假设 anything 工具存在转译器插件开关；未经支持不得声称自动集成。记录输入/输出 hash、完整命令、工具提交、生成依赖与人工修正 diff，检查固定宽度整数、除法、Unicode、容器顺序、错误、动态特性与适用生命周期。不得为迎合转译器改写 oracle 或降低承诺；无法支持时报告边界。选中的生成代码仍须进入任务拥有的 crate、必要桥接、forced-native、Hypothesis/固定差分、项目检查和干净安装验收。`--verify`、编译成功和作者语料统计都不代替这些证据。对照两个转译器时使用不同目录，验收后只接入一份明确选定的实现。

四个工具默认作为开发/测试或隔离转译工具，不进入 PC 的运行时依赖；实际引入依赖组、锁文件或 CI 前，在任务契约中落实版本、来源、许可、平台和运行成本。只安装选定环节需要的工具，不因本文列出它们就批量安装。
