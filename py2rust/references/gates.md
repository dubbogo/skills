<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

## 7. 门禁与完成标准

先从项目规则确定必须执行的检查，再为本单元列出“风险 → 命令 → 预期结果”。局部迭代先跑高信号检查，交付前补齐相关必需门禁；不相关 workspace 或组件的全量测试不因新增 Rust 单元而自动成为门禁。

Rust 命令指向**实际拥有该单元的 manifest**。以下是 workspace 位于 `rust/Cargo.toml` 时的模板；路径、crate 和工具链必须先落实：

```text
cargo fmt --manifest-path rust/Cargo.toml --all --check
cargo clippy --locked --manifest-path rust/Cargo.toml --all-targets -- -D warnings
cargo test --locked --manifest-path rust/Cargo.toml --workspace
rust-anything diff <crate>
rust-anything bench <crate>
rust-anything gate <crate>
```

新 workspace 首次生成或有意更新锁文件属于依赖变更；核查后提交。后续构建、测试和 lint 使用 `--locked`，不得靠解锁绕过漂移。

Python 命令按当前平台执行，先确认解释器、依赖及目标模块的导入路径。例如，相关测试集已经写入计划、Python 包名为 `sample_package` 时：

```powershell
# Windows PowerShell；仅修改当前进程环境
$env:PYTHONPATH = (Resolve-Path ./src).Path
.venv\Scripts\python.exe -c "import sample_package; print(sample_package.__file__)"
.venv\Scripts\python.exe -m pytest <相关测试路径> -q -rs
```

```bash
# POSIX shell
PYTHONPATH="$PWD/src" .venv/bin/python -c 'import sample_package; print(sample_package.__file__)'
PYTHONPATH="$PWD/src" .venv/bin/python -m pytest <相关测试路径> -q -rs
```

以上命令本身不证明 Rust 已启用；必须同时采用 §3 的后端选择与构建身份核验。按当前 `Makefile` 和 CI 补齐 `make check`、受影响的跨组件测试及支持矩阵，不把某条裸 pytest 命令当成全部项目门禁的替代。

引用 CI 代替本地检查时，核对实际 checkout 并测试的 SHA、命令、workspace member/package、target、feature、平台与目标用例数量。区分 check/workflow 的关联 SHA 与实际测试 SHA，按 run/job、checkout 配置及日志归属证据；不能仅因关联 SHA 不同就判失效，也不能用关联 SHA 代替受测源码身份。尤其是新增 crate、可选原生依赖、workflow 或 wheel 路径变更，必须确认它们实际进入构建和测试选择集。job 名称或总体绿色不足以证明覆盖；`cancelled`、`skipped`、等待审批、零用例以及关键 step 被跳过，都不能作为所需验证通过的证据。Head 测试与合并结果测试分别记录；相同快照和条件下已覆盖风险的可信 CI 无需无目的重复执行。

结果按验收项记 `PASS / FAIL / BLOCKED / NOT_RUN`；未触发的条件项写“不适用及依据”。测试自身有效完成且证明预期时才记 PASS。环境不支持导致的平台 skip，相关验收仍是 BLOCKED 或 NOT_RUN；无法判读的 CI 说明具体原因，不能归为产品缺陷或通过。

完成前逐项给出结果：

- 相关既有测试在强制 Rust 路径通过；新增测试保护行为、选择后端和实际已构建产物。
- 迁移改动的测试断言有变更清单与依据；删除或弱化的断言已逐条说明，契约依据已记入 `DECISIONS.md`（见 correctness.md §3.1），未以全绿掩盖覆盖下降。
- 差分全部符合已批准契约，错误路径有覆盖；录制来源、比较规则和源码指纹有效。采用 Hypothesis 时附实际策略、预算、回放和回归样本；采用转译器时附生成与人工修正的来源，不把成功编译当成差分通过。
- 获批主工具及替代验收方案的相关检查通过。若任务选定 rust-anything，则其既有 gate 要求仍须满足；其他工具没有同名命令时，在计划中明确对应检查及独立证据。工具不支持当前边界时列出缺口，不得伪称 gate 通过或自行取消已批准的完成条件，需先明确调整计划。
- 请求或扩展入口的错误均被处理，不能因合法/非法外部输入 panic。优先 `Result` 和 `?`；`expect` 的不变量说明不是运行时安全证明。
- 许可证、生成文件、依赖与锁文件、打包及相关项目检查符合当前仓库规则。
- 含桥接成本的性能结果符合预先约定目标，或明确记录该单元仅为兼容性试点、尚未批准默认接入。
- 支持矩阵中区分实测、CI、待验证与平台跳过。已有 skip 不算通过，也不因此取消其他平台验收。
- 未通过、未运行、受环境阻塞和已证明的 Base 问题分别记录。
- 验证结论对应最终源码、测试、配置和实际构建产物；独立验证按 §3.4 记录真实能力与反馈，不用执行者自述代替。

不采用“差分 case 数不少于测试数”作为完成条件；测试与录制单位不同，应按契约、风险和错误路径检查覆盖。
