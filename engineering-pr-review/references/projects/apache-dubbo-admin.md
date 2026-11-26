<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Modified for the 2026-11-26 skill adaptation; see references/provenance.md (relative to the skill root) for source attribution and changes. -->

> **适用性要求**：以下为导入的历史调查材料。导入不等于重新验证。命令、版本、CI、审批数和环境现象必须核对当前快照；缺失元数据只作线索。处理要求冲突时使用选定协议，特别是 R11/R12 的根因去重与 §8 的 Resolve 授权，不采用历史条目的相反操作。

# apache/dubbo-admin Review 补充规则

## 堆叠 PR 的审查基准是增量而非累计

- `validated_at`: 2026-10-24
- `validated_ref`: `ai@97d2db47883c0d3bd61dbfa8f95f17e83631b987`；链 `#1592(4c6bbad3) → #1594(0f7c8a6e) → #1596(6ada4033) → #1608(6d2501bc) → #1609(8459ec48) → #1610(2a51ff9b) → #1611(04fe99de)`
- `applies_to`: 所有基于同一长期分支（本例 `ai`）逐层叠加的 PR 系列，以及任何 target 非默认分支的 PR
- `recheck_when`: PR 描述里出现「blocked by / merge after / 合并顺序」字样，或 `gh api compare/<prev>...<cur>` 的 `behind` 为 0

GitHub 的 Files changed 页对堆叠 PR 展示的是**相对 base 分支的累计 diff**，不是本层增量。实测 `#1608`：页面显示 `+7279/−872`、99 个文件；用 `git diff 6ada4033...6d2501bc` 得到的真实增量是 **`+86/−2`、4 个文件** —— 差 7193 行。到 `#1611` 累计已到 `+16913/−988`、139 文件，若 7 层攒到一起合，等于要求维护者一次审 1.7 万行。

审查流程：

1. 先用 `gh api repos/<owner>/<repo>/compare/<prevHead>...<curHead> --jq '{ahead:.ahead_by, behind:.behind_by}'` 确认是**严格 ancestor 链**（`behind == 0`）；`behind > 0` 说明该层已分叉，按普通 PR 审。
2. 逐层用 `git diff <prevHead>...<curHead>` 生成增量，行号引用一律以**本层 Head** 为准（增量 diff 的行号与累计 diff 的行号不同）。
3. 在 review 里同时给出两个数字（累计 / 增量）并说明差异，否则作者和维护者会误判工作量。
4. 增量 ≤ 200 行而累计 ≥ 5000 行的层（如 `#1608`）要特别标注，这类 PR 最容易被「Files changed 太大」误判为无法审。

## `commit_id` 必须是完整 40 位 SHA

- `validated_at`: 2026-10-24
- `validated_ref`: `gh api repos/apache/dubbo-admin/pulls/1408/reviews` 首次提交失败；改用 `git rev-parse pr/1408` 的完整 SHA `e9c24b2fb9a2e6327b2f6e43ed97dea58d0e99e9` 后成功（review id `5636872353`）
- `applies_to`: 所有通过 API 提交 review 的流程
- `recheck_when`: 每次提交前确认 `commit_id` 长度

`gh api .../pulls/<n>/reviews --input` 的 `commit_id` 用 12 位短 SHA 会返回 `422 Variable $commitOID of type GitObjectID was provided invalid value`。这个报错不提示「太短」，容易被误判成 PR 已关闭或无权限。批量审查时先把所有 Head 汇总成 `number<TAB>full_sha` 的清单（本例 `heads.txt`）再逐条提交。

若首次提交返回 `404 Not Found`，不要直接怀疑权限：先用最小 payload（`{"commit_id": "<sha>", "event": "COMMENT", "body": "test"}`）验证可写性，再逐步加长正文定位问题。注意这样会留下一条正文为 `test` 的 review，而 `DELETE /reviews/<id>` 对已提交的 review 返回 `422 Can not delete a non-pending pull request review` —— 只能用 `PUT /reviews/<id>` 把 `body` 覆盖为正式内容，无法清理。

## `mergeable_state` 会过期，冲突必须用 merge-tree 复核

- `validated_at`: 2026-10-24
- `validated_ref`: `develop@f1c3f3a7`、`ai@97d2db47`；26 个 PR 全量 `git merge-tree --write-tree` 复核
- `applies_to`: 所有「可合并 / 不可合并」结论的取证环节
- `recheck_when`: 每次给出合并结论前重跑，不要引用上一次的结果

GitHub 的 `mergeable` / `mergeable_state` 有缓存，且会随 base 分支推进而变。实测：`#1582` 上次读到 `mergeable=false / dirty`，本次为 `clean`（作者在 `#1598` 同步后更新了分支）；`#1409` 上次是 `clean`，本次新增 `ui-vue3/src/Login.vue` 冲突。

正确的复核方式是对每个 PR 跑真实三方合并：

```bash
git fetch origin <base>:refs/remotes/origin/<base> --force
git merge-tree --write-tree origin/<base> pr/<n>
```

返回码 0 = 无冲突；返回码 1 且输出 `CONFLICT (content): ...` = 真实冲突（`CONFLICT` 行数即冲突文件数）。本次 26 个 PR 中只有 `#1409`（1 处）和 `#1585`（2 处）真实冲突，其余全部 clean —— 包括那些 `behind != 0` 的。

冲突归因要落到具体提交，不能只说「有冲突」：`#1585` 的冲突来自 `ai` 在分支创建后合入了 `#1567`（context windows）与 `#1598`（sync develop），两边都往 `AgentSpec` 的 `Timeout` 之后插字段，`ai` 侧还顺带重排了整个字段块（导致 diff 变成「全行改动」）。给作者的修复建议必须是「保留两边的哪几个字段、按什么顺序、合并后重跑什么命令」，而不是「请 rebase」。

## 归属校验的自证循环

- `validated_at`: 2026-10-24
- `validated_ref`: `#1611` Head `04fe99de`，`ai/store/summary.go:339` 与 `ai/component/memory/summary/service.go:192`
- `applies_to`: 所有「写入时断言 owner / tenant」+「提交时校验 owner / tenant」的成对逻辑
- `recheck_when`: 存储层校验里出现 `a.Subject.X` 与 `value.X` 的比较时

`#1611` 的 `ValidateSummaryCommit` 有一行看起来是权限校验的断言：

```go
if ... || v.TenantID != a.Subject.TenantID || v.OwnerID != a.Subject.UserID || ...
```

而服务层构造待写入对象时正是这么填的：

```go
v := store.Summary{TenantID: a.Subject.TenantID, OwnerID: a.Subject.UserID, ...}
```

赋值与校验用同一对字段，**判断永远成立**，无法发现「数据被登记到错误的 owner 名下」。实际后果：当调用方是持 `ai:sessions:admin` 的管理员或走 `SystemAccessContext()` 的维护路径时，记录会被写成**调用者**而不是资源真实 owner。读取侧通常不会因此越权（本例 `GetSummary` 走 Session 级授权），所以这不是越权漏洞，而是**审计归属错误 + 一条虚假的安全校验**。

识别方法：拿到「存储层校验」的代码后，回到**构造点**看被校验的字段是否由同一个 `AccessContext` 填充。若两边同源，校验只能防住「调用方主动篡改自己传入的字段」，防不住「调用方断言了错误的归属」。修法是让归属信息从资源本身（Session 行、快照、批次）取，校验与调用方断言解耦。

配套的判据：**不要把「有校验」当成「校验有效」**。凡是在 review 里准备写「已有防御」，先确认校验的两侧不是同一个信息源。

## 用语义无关的只读查询充当授权探针

- `validated_at`: 2026-10-24
- `validated_ref`: `#1608` Head `6d2501bc`，`ai/component/agent/react/steps.go:148`
- `applies_to`: 所有在循环体内「每个迭代重检一次权限」的实现
- `recheck_when`: 看到 `if _, err := store.SomeQuery(...)` 这种丢弃返回值的调用

`#1608` 的目的是「每次模型迭代前重检 Session 可达性」，实现方式是：

```go
if _, err := ra.messageStore.IsTurnEmpty(ctx, access, s.Session, turnID); err != nil {
    return false, err
}
```

借 `IsTurnEmpty` 触发一次带 `access` 的 Store 调用，意图正确、安全性也成立，但函数名与目的完全无关且布尔结果被丢弃。后果：① 每次迭代多一次纯检查性往返；② 读者会把它当成遗留 bug 去「修」，或者把它当成有意义的判断去依赖其返回值。

审查这类「探针」的判据：**授权检查应当有独立、名字自解释的入口**（`CheckTurnAccess`、`AuthorizeTurn`）。若 PR 需要靠一个业务查询来顺带完成权限复检，应在该行上方注释「本调用的唯一目的是复检授权，返回值被刻意忽略」；更好的做法是推动新增语义明确的方法。

同一个 PR 里还要检查**不可达分支**：`#1608` 在 `steps.go:149` 新增 `if state == nil { return err }`，但调用方 `run()`（`steps.go:87`）已在 `messageStore != nil` 时返回过同类错误，该分支永远走不到；同理 `steps.go:186` 的 `if state != nil` 变成恒真。同一个不变量在三个位置用三种表态，是「加防御时没回头读调用方」的典型痕迹。

## JSON 序列化吞错会让预算守卫 fail-open

- `validated_at`: 2026-10-24
- `validated_ref`: `#1610` Head `2a51ff9b`，`ai/component/context/types.go:148` 与 `ai/component/context/compiler.go:117`
- `applies_to`: 所有基于 `json.Marshal` 长度做体积 / token / 字节预算计算的代码
- `recheck_when`: 出现 `data, _ := json.Marshal(...)` 且返回值被用于计数

```go
func JSON(value any) json.RawMessage { data, _ := json.Marshal(value); return data }
func Estimate(value any) int { return len(JSON(value)) + 16 }
```

一旦候选内容无法被序列化（`NaN`/`Inf` 浮点、map 非字符串键，或未来新增 `func`/`chan` 字段），`JSON` 返回 `nil`，`Estimate` 返回 `16` —— 本该占几千 token 的内容被记成 16。这不是「少报一点」，而是**预算守卫在它最需要生效的场景下失效**，最终把超长输入发给 provider。

审查判据：

1. 尺寸 / 预算 / 配额计算链路上，任何 `_` 丢弃的 `json.Marshal` 错误都是 fail-open，必须上抛或在失败时取保守上界（而非 0）。
2. 区分「估算器不可用」与「估算结果为 0」：本例 `#1599` 用 `-1` 表示不可用（`ai/component/agent/react/context_size.go:38-42`），是正确做法；`#1610` 用 0 附近的值，不可区分。
3. 预算比较本身通常是 fail-closed 的（`used > available → ErrMandatoryBudget`），要确认的是**输入到比较的那一步**没有静默归零。
4. 顺带检查配置错误与容量不足是否共用同一个错误码：`#1610` 里 `OutputTokens >= ContextTokens` 会走到 `ErrMandatoryBudget`，运维看到「必选内容放不下」，实际是窗口配反了。

## 缓存未命中触发远程 I/O 且 miss key 来自未验证输入

- `validated_at`: 2026-10-24
- `validated_ref`: `#1600` Head `5229ae41`，`ai/component/server/engine/auth.go:105-125`、`:130-160`
- `applies_to`: 所有 JWKS / 公钥 / 元数据缓存 + 「未命中即刷新」的实现
- `recheck_when`: 认证中间件里出现 `refresh(...)` / `fetch(...)` 调用

```go
kid, ok := token.Header["kid"].(string)   // 来自未验签的 JWT header
key := v.keys[kid]
if key != nil { return key, nil }
if err := v.refresh(context.Background()); err != nil { return nil, err }  // 未命中就远程取
```

`kid` 此时**签名尚未校验**，任何人都能构造 `{"alg":"RS256","kid":"<随机串>"}` 打受保护端点，服务端就向 JWKS 端点发一次 GET。放大比 1:1，没有 singleflight、没有最小重取间隔，`context.Background()` 还让这次调用脱离请求的取消与截止时间。

后果有两层：① 免认证的请求放大（把流量全转打到无认证的 JWKS 端点）；② 自伤（JWKS 端点短暂不可达时，每个合法请求都卡满客户端超时，然后返回 500 而非 401）。

审查判据：

1. miss key 是否来自**未验证**的输入？是则应假定它是攻击者可控的。
2. 是否有冷却窗口 / 单飞合并 / 请求上下文？三者缺一即为可放大面。
3. 缓存条目是否有 TTL？本例已加载的 key **永不过期**，Admin 轮换或吊销后旧公钥仍能验签通过，直到进程重启或碰巧有一次未知 `kid` 触发重取 —— 这属于「撤销不生效」，比放大更难被发现。
4. 顺便核对密钥强度下限：本例校验了 `kty/alg/use/kid` 与 `n`/`e` 的合法性，但没校验模数位数，1024 bit RSA 会一路通过。

## 同一 concern 的两套实现要横向比对配置 schema

- `validated_at`: 2026-10-24
- `validated_ref`: `#1600` Head `5229ae41`（`auth: {jwks_url, issuer, audience}`）vs `#1609` Head `8459ec48`（`authentication: {jwt_secret, jwt_issuer, jwt_audience, allow_insecure_static_auth}`）
- `applies_to`: 同一模块下同时 open、解决同一问题的多个 PR
- `recheck_when`: 批量审查中发现两个 PR 都在改同一个配置文件或 schema 时

`#1600`（RS256 + JWKS，Admin 自签发 token）与 `#1609`（HS256，静态共享密钥）都实现了 AI 服务的 HTTP 认证，算法、实现位置、影响面全都不同。**`git merge-tree` 对两者都返回 0 冲突** —— 因为它们写的是不同的文件。只看 Git 冲突会得出「都能合」的错误结论。

真正的冲突在运维语义层：合并后 `ai/component/server/server.yaml` 与 `ai/schema/json/server.schema.json` 里会同时存在 `auth:` 和 `authentication:` 两个配置块，两条身份提取路径，运维无法判断以哪个为准。

审查方法：把两个 PR 的**配置结构**并排列出来（YAML 键名 / 环境变量 / 默认值），而不是比代码。若同一 concern 出现了互不兼容的配置形状，结论应当是「先决策、后合并」，并给出选型依据（本例：#1600 不引入外部 IdP、有密钥轮换路径；#1609 多副本需分发共享密钥、运维成本更高）。

## 默认值填充无法表达「显式关闭」

- `validated_at`: 2026-10-24
- `validated_ref`: `#1596` Head `6ada4033`，`ai/store/policy.go:59` 的 `QuotaPolicy.WithDefaults()`
- `applies_to`: 所有 `if value <= 0 { value = default }` 形式的配置默认值填充
- `recheck_when`: 配置项语义里存在「0 / 空 = 无限制 / 关闭」

```go
// fills omitted limits without replacing explicitly configured values
if p.MaxTurnsPerSession <= 0 { p.MaxTurnsPerSession = defaults.MaxTurnsPerSession }
```

注释承诺「不替换显式配置的值」，实现对每个字段都判 `<= 0`，因此运维想用 `max_turns_per_session: 0` 表示「不限」时会被**静默改成 100**。这类「想关掉限额结果没关掉」的误配在线上极难定位 —— 现象是「配置改了但行为没变」，日志里没有任何提示。

审查判据：注释与实现对不上时，以实现为准并指出分歧。修法只有两条 —— 改用指针字段（`*int`）区分「未配置」与「显式 0」，或在校验阶段直接拒绝 0 并报错，让语义只有一个出口。**不要把「加个布尔开关」当解**，那会让状态空间从 N 变 2N。

## 本地复现 CI 格式门禁必须带仓库自己的配置

- `validated_at`: 2026-10-24
- `validated_ref`: `#1409` Head `c362767a`，`ui-vue3/.prettierrc.json`（来自 `origin/develop`）
- `applies_to`: 所有以 `prettier --check` / `gofmt` / `eslint` 为门禁的 CI 结论
- `recheck_when`: 本地跑格式检查得到「无问题」但 CI 报错时

`#1409` 首次本地检查 `npx prettier@3.0.3 --check src/Login.vue` 报告无问题，实际 CI 必失败。原因是仓库 `.prettierrc.json` 没有拷到工作目录，prettier 退化为默认配置（双引号 + 分号），把真实的**尾随空格**改写掩盖掉了。把配置取过来再跑：

```bash
git show origin/develop:ui-vue3/.prettierrc.json > .prettierrc.json
npx prettier@3.0.3 --check src/Login.vue   # exit 1
```

才拿到 `exit 1` 与 3 行尾随空格的确切改写。

判据：**「本地跑过没问题」不是证据，跑的是同一套配置才是**。给作者的结论要带上具体命令与配置来源，让他能一次复现，而不是「CI 会挂」这种无法验证的断言。

## 纯文档 PR 的 `Fixes:` 会误关功能 issue

- `validated_at`: 2026-10-24
- `validated_ref`: `#1541` Body 的 `Fixes: #1491`；同仓库 `#1582` 用 `Closes #1575` + `Parent feature: #1491`
- `applies_to`: 设计提案 / RFC / 纯 `.md` 增删的 PR
- `recheck_when`: 文档类 PR 的 body 里出现 `Fixes` / `Closes` 关键字

`#1541` 只新增一个 1209 行的设计方案，不改任何代码，但 body 写了 `Fixes: #1491`。合并时 GitHub 会自动关闭跟踪整个 MCP Server 功能的总 issue，等于宣布功能完成。实际实现载体是 `#1582`（它用的是 `Closes #1575` + `Parent feature: #1491` 的正确写法）。

审这类 PR 时值得同时核对的还有两点，它们能反映作者是否真的对着代码写文档：

1. **设计文档里贴的基线 commit 是否真的在目标分支历史上**：`git merge-base --is-ancestor <doc_sha> origin/<base>`。本例 `2df3e07` 通过。
2. **文档对现有系统的能力断言今天是否仍成立**：本例 §4「ResourceStore 没有 CAS 接口」——在 `origin/ai` 上搜 `ConditionalResourceManager` 零命中，在 `#1582` 上命中，说明文档描述的是「引入前」的真实状态，与实现一致。
