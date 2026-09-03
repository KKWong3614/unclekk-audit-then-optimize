---
name: unclekk-audit-then-optimize
slug: unclekk-audit-then-optimize
displayName: UncleKK 审计长闭环优化审计
version: 1.2.3
summary: 独立审计→优化→独立复审闭环，防自评分虚高、抓漏改残留。
description: UncleKK 的审计方法论：fresh 子代理独立审计+复审，以 C 为权威分纠正自评分虚高；附 audit_guard.py 硬代码保障。
license: MIT
author: Hermes Agent
metadata:
  agent_created: true
  hermes:
    tags:
    - audit
    - optimization
    - independent-audit
    - self-score-inflation
    category: skill审计
    related_skills:
    - skill-audit
    - unclekk-darwin-evolver
    - software-development/skill-audit
---

# unclekk-audit-then-optimize

unclekk 的三步模式：**独立审计 → 优化 → 独立复审**。

unclekk's three-step pattern: **independent audit → optimize → independent re-audit**.

本技能将 unclekk 技能生态中的「独立第三方审计」方法论固化下来——防止自评分虚高，并抓住优化器自以为已修复的残留缺陷。

This skill codifies the independent-third-party-auditor methodology for unclekk's skill ecosystem — preventing self-score inflation and catching residual bugs that the optimizer assumes fixed.

本技能记录了我们在 unclekk-darwin-evolver（2026-07-23）上的经验：优化器自评分 86/100，独立审计员评分 82/100，并发现了 4 个优化器遗漏的问题。自评分持续偏高。

This skill encodes what we learned on unclekk-darwin-evolver (2026-07-23): the optimizer self-scored 86/100, the independent auditor scored 82/100 and found 4 things the optimizer missed. Self-scores are consistently inflated.

## 语言说明 (Language)

**中文为第一使用语言**：本技能所有关键指令、示例、触发词、错误提示均有完整中文，仅凭中文即可完整使用；英文为技术术语对照（unclekk 生态双语惯例，保留 skill / audit / Agent 等术语原文），读者无需英文。若中文表述与英文对照有出入，**以中文为准**。

- 口语化中文输入直接可用：「帮我审计这个技能」「优化完给我独立复审一遍」「B 和 C 差多少」「按测评结果提升优化」
- 示例与案例均基于国内真实场景（unclekk 技能生态 / WorkBuddy / Hermes 中文环境）
- 仅 `cross-ecosystem-porting-audit.md` 的案例正文保留英文为主（历史移植记录），其余文档均为中英对照

## 为何存在此模式 (Why This Pattern Exists)

刚完成文件编辑的优化器（无论是子代理还是主代理）：

An optimizer (whether a subagent or the main agent) that just finished editing a file:

- 知道自己修了什么 → 假设自己修对了
- Knows what it fixed → assumes it fixed it correctly
- 继承了原始审计的上下文 → 看到的是「修复前」的状态
- Has context inheritance from the original audit → sees the "before" state
- 对自己产出的工作有偏向 → 对其产出过于乐观
- Is biased toward its own work → optimistic about what it produced

独立审计员（叶节点子代理，全新上下文，toolsets=['file','terminal']）：

An independent auditor (leaf subagent, fresh context, toolsets=['file','terminal']):

- 不继承优化器的历史
- Does not inherit the optimizer's history
- 像陌生人一样阅读文件
- Reads the file as a stranger would
- 抓住优化器自以为已修复的残留缺陷
- Catches residual bugs the optimizer assumed fixed

独立审计员耗时约 8 次 API 调用和 5 分钟。优化器则需 50+ 次调用，并可能触及迭代上限。

The independent auditor costs ~8 API calls and 5 minutes. The optimizer costs 50+ calls and can hit the iteration limit.

## 闭环 (The Loop)

```
1. Independent audit (leaf subagent) → score A, findings list
2. Optimize (main agent or subagent) → self-score B
3. Independent re-audit (leaf subagent) → score C
4. Compare A, B, C. If B − C > +3 points, suspect self-score inflation (optimizer over-claims); if C − B > +3 points, re-verify C (auditor may use different baseline or scoring scale — see Scoring Convention). In either direction, delta warrants lead-agent re-check.
5. Fix any P1/P2 the re-audit found that the optimizer missed.
```

> **[硬代码 · 闭环上限]** 闭环设硬性上限 **MAX_ROUNDS = 3**（可用 `python scripts/audit_guard.py loop --round N --max 3` 机械判定）。达到上限强制 STOP，未闭合项交主代理人工收口——防止无界递归（本技能样例曾把同类缺陷判为他人的 P0）。`B−C` 有向差值也可由 `audit_guard.py loop --delta B C` 消除人工查表误读。

### 闭环流程图 / Loop Diagram

```
        ┌──────────────────────────────────────────────┐
        │  用户要求「优化 skill」并产生自评分             │
        │  User asks "optimize skill" (self-score)       │
        └──────────────────────────────────────────────┘
                          │
                          ▼
   ┌───────────────────────────────────┐   score A
   │ ① 独立审计 (leaf subagent)         │──────────────► A
   │   Independent audit                │
   └───────────────────────────────────┘
                          │
                          ▼
   ┌───────────────────────────────────┐   self-score B
   │ ② 优化 (main / optimizer)          │──────────────► B
   │   Optimize                         │
   └───────────────────────────────────┘
                          │
                          ▼
   ┌───────────────────────────────────┐   score C
   │ ③ 独立复审 (fresh leaf subagent)   │──────────────► C
   │   Independent re-audit             │
   └───────────────────────────────────┘
                          │
                          ▼
   ┌───────────────────────────────────────────────────┐
   │ ④ 比较 A / B / C                                   │
   │   B−C > +3  →  自评分虚高，以 C 为准                │
   │   C−B > +3  →  重核实 C（基线/量规不同，勿自动否定）│
   │   其余      →  主代理交叉核对                       │
   └───────────────────────────────────────────────────┘
                          │
                          ▼
   ┌───────────────────────────────────┐
   │ ⑤ 修复复审发现的 P1/P2（优化器漏改）│
   └───────────────────────────────────┘
```

### 调用模板 / Invocation Template

可直接复制的最小闭环（① 与 ③ 必须用**不同** fresh 上下文的子代理；本环境用 `Agent` 工具，`delegate_task` 仅当宿主支持时作别名）：

```python
# ① 独立审计（fresh 子代理，全新上下文；只评不改，仅 file + terminal 工具集）
#    本环境用 Agent 工具（subagent_type="general-purpose"），切勿写死为本环境不存在的 delegate_task。
Agent(
  description="独立审计 <SKILL_NAME>",
  subagent_type="general-purpose",
  prompt=f"""你是独立第三方审计员（fresh 上下文，只评不改）。
审计目标：<SKILL_DIR_绝对路径>
文件清单：<find <SKILL_DIR> -type f | sort 的输出>
先前发现（供跳过，非重发现）：<prior findings>
首要问题：'这个设计是对的吗？' 而非 '代码写得漂亮吗？'
量规：skill-audit 8 阶段 /100，并产出 P0/P1/P2 清单。""",
)
# ② 优化（主代理 / 优化器）→ 自评分 B
# ③ 独立复审（另一个 fresh 子代理）→ 评分 C
# ④ 比较 B vs C（见「评分约定」定向差值规则；可用 scripts/audit_guard.py loop --delta B C 机械判定）
```

→ `references/cross-ecosystem-porting-audit.md`
→ `references/independent-auditor-multiround-loop.md` — 多轮独立审计长模式：主 Agent 派发，审计长（leaf subagent）独立执行达尔文+SkillEvolution直到触顶，主 Agent 独立验证结果。适用于用户要求"优化 skill 直到触顶"的场景。
→ `references/independent-auditor-multiround-loop.md` — Multi-round independent-auditor-long pattern: the lead Agent dispatches; the auditor (leaf subagent) independently runs Darwin + SkillEvolution until it tops out; the lead Agent independently verifies the results. Applies to user requests to "optimize the skill until it tops out".
→ `references/faq.md` — 高频问答（何时用 vs 直接优化 / B·C 差值解读 / 审计员工具缺失兜底 / 元技能死锁 / 纯文档 skill / 工具集）
→ `references/diagnostic-checklist.md` — 诊断清单法（P0/P1/P2 grep 可检缺陷清单，本技能 `scripts/audit_guard.py` 的算法蓝本）
→ `references/audit-verification-report.md` — 审计验证报告（含 P0-2 CRLF 修复记录）
→ `references/ceiling-confirmed-deadcode-fix.md` — 触顶确认死代码修复记录
→ `examples/quickstart-worked-example.md` — **全填好的调用示例**（真实路径 + 真实文件清单 + 占位符全填的 `Agent` 调用），复制即可跑
→ `references/audit-unclekk-audit-then-optimize-2026-08-28.md` — 本轮「审计→优化→复审」闭环审计报告（A/B/C + 差值决策，可作 `closure` 校验样本）
→ `references/deep-audit-unclekk-audit-then-optimize-2026-08-29.md` — 第三方 agent 深度审计报告（P0×1/P1×8/P2×12，变异测试证明 selfcheck 覆盖面缺口；v1.2.0 已据此修复并新增 `selftest` 变异测试自证"能检出"）
→ `references/optimize-unclekk-audit-then-optimize-2026-08-29.md` — v1.2.0 优化闭环报告（B 自评 84 / C 复审 75 / 差值决策 / C 残留修复终验）
→ `references/anti-patterns.md` — 反模式清单：错误用法 vs 改进示例对比 + 禁忌清单（TRACE C-反模式）
→ `references/faq-deep.md` — 深度 FAQ：边缘场景 / 工具兼容 / 安全合规 / 脚本故障排查（TRACE C-FAQ 深度）

## 硬代码保障 (audit_guard.py — Hard-code Enforcement)

> **[警告]** 本技能历史上反复出现「文档说强制、执行靠自觉」的漏洞：版本号漂移、链接断裂、CRLF 静默复发。v1.1.0 起所有约束改为**代码强制**；v1.2.0 起覆盖面全面化（链接扫全部 md、无扩展名文件 CRLF、@/中文路径、孤儿可达性 BFS、跨量规百分比、closure 数值重算）+ `selftest` 变异测试自证「能检出」而非仅「能运行」。

`scripts/audit_guard.py`（零依赖，仅标准库，Windows/Unix 通用；输出已强制 UTF-8，非 UTF-8 代码页不崩）把方法论里的规则变成可机械判定的退出码：

| 子命令 | 作用 | 拦截的缺陷 |
|---|---|---|
| `selfcheck [--target DIR]` | 结构自检：行尾(含无扩展名文件) / 版本一致(5 处含 CHANGELOG 标题) / 链接完整(扫全部 md) / 孤儿文件(可达性 BFS，示例文本不洗白) / README 结构 / 跨文件计数(含中文数字) / frontmatter / 软化措辞 / 陈旧路径(含 @ 与中文) / 尾换行 / 禁用工具名 | P0-2 回归、P1-3 断链、P1-4 孤儿、P1-5 计数漂移、P0-1 残留、P2-1/P2-2/P2-11/P2-12 |
| `preflight [--target DIR]` | 进入闭环前的预检闸（路径存在 + selfcheck 通过；闸 3 为人工确认项） | 预检闸形同虚设（P1-1/P1-8） |
| `loop --round N --max 3` | 闭环状态机：MAX_ROUNDS 硬上限（状态自增防忘递增、--max 硬钳制、拒绝负轮次） | 无界递归（P1-2/P1-7） |
| `loop --delta B C [--rubric-max 100\|90]` | 计算 B−C 有向差值规则（**跨量规转百分比**，防除零校验） | 人工查表误读、跨量规误判（P1-1） |
| `closure --report FILE [--rubric-max N]` | 校验报告含具名「审计分 A/自评分 B/复审分 C」字段，**重算差值并与结论比对** | 闭环不完整、结论倒置（P1-5） |
| `selftest [--target DIR]` | 变异测试：注入 5 组缺陷（README 断链/LICENSE CRLF/@ 幽灵路径/互引孤儿/纯孤儿），断言 selfcheck 必须检出 | 脚本「能运行但不能检出」（P1-2） |

**发布前必跑**（退出码非 0 不允许发布）：

```bash
python scripts/audit_guard.py selfcheck --target "$SKILL_DIR"
python scripts/audit_guard.py selftest --target "$SKILL_DIR"
python scripts/audit_guard.py preflight --target "$SKILL_DIR"
```

→ `scripts/audit_guard.py` — 硬代码保障脚本源码（自带完整 `--help`）

## 受众说明 (Audience)

**适用对象：所有 Agent 用户。** 只要你在用 AI Agent 做「优化」类工作、且该优化会产生自评分（"我觉得改好了"），本闭环方法论就适用——优化对象不限于 skill：prompt、工作流、代码、方案均可套用「独立审计 → 优化 → 独立复审」与 B−C 差值规则。

- **所有 Agent 用户**（总受众）：无需编程基础。把"自评 vs 独立复审"的差值规则套用到你的任何优化决策上——例如 prompt 改了几版觉得"更好了"，很可能只是自评乐观；请一个 fresh 上下文的独立视角复核，比自我感觉可靠。工具层面 `audit_guard.py` 的审计对象为 skill 文件；**方法论层面对所有 Agent 优化场景通用**。
- **个人 Skill 开发者**：优化自己的技能后走闭环（工具主场景）。
- **团队 / 组织用户**：把 `selfcheck` / `selftest` 退出码作为 CI 门禁，多人在合并技能/工作流改动前统一质量基线。
- **审核员 / 评测者**：以 A/B/C 差值规则 + 诊断清单作为统一评审框架，保证不同人评审口径一致。
- **非主要用户**（只想快速改一个简单技能）：跳过闭环直接改更高效——见「不适用场景」。

## 使用时机 (When to Use)

> **[提示]** 一句话判断：只要这次优化**会产生自评分**，就该走闭环（自评分几乎必然偏高）。

- 用户要求「优化 skill」，且该技能是元技能或方法论技能
- User asks for "优化 skill" and the skill is a meta-skill or methodology skill
- 在任何会产生自评分的优化之后
- After any optimization that produces a self-score
- 当先前的审计发现了 P0，且你想验证它们是否真的被修复
- When a prior audit found P0s and you want to verify they're truly fixed
- 当你怀疑优化器的分数偏高时（优化后总是如此）
- When you suspect the optimizer's score is inflated (always, post-optimization)
- **跨生态移植**：从另一个平台（Claude Code、Cursor 等）克隆而来的技能——移植代理对工具名不兼容视而不见。务必使用独立审计员，绝不要自我审计。→ `references/cross-ecosystem-porting-audit.md`
- **Cross-ecosystem ports**: skill cloned from another platform (Claude Code, Cursor, etc.) — the porting agent is blind to tool-name incompatibility. Always use an independent auditor, never self-audit. → `references/cross-ecosystem-porting-audit.md`

> **[注意]** 本技能只负责「审计闭环」本身，不替你改 skill；具体优化交给 unclekk-darwin-evolver 或主代理。

## 不适用场景（显式声明）(When NOT to Use — Explicit)

> **[警告]** 以下场景走本闭环是浪费或无效，请勿使用；直接用优化器，或走正式评审流程。

- **目标 skill 极简单、优化不产生自评分、或你本就打算直接改**：独立审计是额外开销，直接改更高效。
- **时间 / 成本极度受限**：连一次约 8 次 API 调用的独立审计都负担不起时，至少保留「主代理清空上下文后自审」的降级方案（见「异常处理 / Error Handling」兜底）。
- **改动属安全 / 合规关键且你无权独立处置**：走正式评审或审批流程，而非本闭环。
- **纯方法论 skill 的「真实测试」维度退化为 dry_run（自指性死锁）**：见「评分约定」——用「主代理人工核对 C」代替机器 C，不要误以为 C 是客观分。
- **你已 100% 确信优化正确，且优化器与审计员同一人 / 同一上下文**：独立审计失去意义，强行跑只会自欺。

### 能力边界总览 / Capability Boundary（三分类）

| 分类 | 具体能力 / 场景 |
|---|---|
| ✅ **擅长** | ① 独立审计任意 skill（fresh 子代理，产出 P0/P1/P2 清单）② 复审优化结果、抓优化器漏改残留 ③ B−C 差值决策（含跨量规转百分比）④ 硬代码结构自检（`audit_guard.py` 5 子命令）⑤ 跨生态移植技能审计（工具名兼容） |
| ⚠️ **需素材** | ① 目标 skill 的绝对路径（必须真实存在）② 文件清单 / 审计上下文包 ③ 上一轮审计发现（供跳过，非重发现）④ 量规选择（skill-audit /100 或 Darwin /90）⑤ 报告格式（具名「审计分 A / 自评分 B / 复审分 C」字段） |
| ❌ **超范围** | ① 替你改 skill（交给 unclekk-darwin-evolver 或主代理）② 简单技能的直接修改（走优化器更高效）③ 安全/合规关键改动的正式评审 ④ 评测非 skill 类文档或代码 ⑤ 方法论技能「真实测试」维度（第 8 维退化为 dry_run，用主代理人工核对 C 代替） |

## 陷阱（来自 unclekk-darwin-evolver 案例研究）(Pitfalls (from unclekk-darwin-evolver case study))

> **[警告]** 以下陷阱均来自真实案例，跳过会重蹈覆辙。

**P0-3 残留：修复算法本身，而非仅修改措辞。**
**P0-3 residual: fix the algorithm, not just the wording.**

如果一个技能定义了自身的终止/触顶规则（例如"连续2轮Δ<2"），并且该技能附带了一个声称遵循该规则的进化示例——请核实该示例确实满足该规则。技能自身示例中出现的反例是一个 P1 缺陷，而不是「需要进一步说明」。

If a skill defines its own termination/ceiling rule (e.g. "连续2轮Δ<2"), and the skill ships an evolution example claiming to follow that rule — verify the example actually satisfies the rule. A counterexample in the skill's own example is a P1 defect, not "needs clarification."

**跨文件计数必须一致。**
**Cross-file counts must match.**

当技能正文写"N类失败模式"时，每个重复该计数的 references/ 文件都必须一致。正文是摘要；references/ 文件才是事实来源。它们经常会漂移。

When a skill body says "N类失败模式", every references/ file that repeats that count must match. The body is the summary; the references/ file is the source of truth. They often drift.

**检查可复制的示例文件。**
**Check copyable example files.**

results.tsv、模板、tsv 示例——这些是用户真正会复制的内容。SKILL.md 是他们阅读的内容。两者都需要被验证。

results.tsv, templates, tsv samples — these are what users actually copy. SKILL.md is what they read. Both need to be verified.

**元技能存在自指性的第8维问题。**
**Meta-skills have a self-referential dimension-8 problem.**

一个定义了自身质量指标的技能，必须拥有一种非循环的方式来自我评估。如果权重最高的维度要求"真实测试"，但该技能本身就是方法论，那么该维度会退化为 dry_run。这是一个结构性死锁，而非文档缺口。

A skill that defines its own quality metric must have a non-circular way to evaluate itself. If the highest-weighted dimension requires "real testing" but the skill IS the methodology, that dimension degrades to dry_run. This is a structural deadlock, not a documentation gap.

## 异常处理 / Error Handling

> **[注意]** 本技能是方法论文档，无代码级重试 / 超时；以下「X → 做 Y」映射表覆盖最常见的误操作与边界情形。进入闭环前先完成参数校验。

### 强制预检闸 / Mandatory Pre-flight Gate

> **[警告]** 以下三项**必须全部通过（GO）才能进入闭环**。任意一项为 STOP，本次闭环**无效**——跳过校验直接跑，等于让优化器自己审自己，整个闭环失去意义。这不是建议，是硬性前置条件。

| # | 检查项 | GO 条件（机械判定） | STOP 处理 |
|---|:---:|---|---|
| 1 | 目标 skill 绝对路径存在 | `test -f "$SKILL_DIR/SKILL.md"` 退出 0（对**单一绝对路径**做存在性断言，替掉返回 61 条的 `find`） | 先定位，把**精确绝对路径**交给审计员 |
| 2 | 结构自检无 FAIL（含跨文件计数/链接/版本一致/行尾） | `python scripts/audit_guard.py selfcheck --target "$SKILL_DIR"` 退出 0 | 按脚本输出的 FAIL 项逐条回改正文/源文件 |
| 3 | 审计员工具可用（本环境用 `Agent` / `Task`） | 能派发 fresh 上下文子代理（`Agent` 本环境可用；`delegate_task` 仅当支持时） | 走「异常处理」兜底（主代理清上下文自审 / Agent 派发 / 另开会话），**绝不让优化器兼审计员** |

✅ 三项全 GO（脚本退出 0）→ 进入 ① 独立审计。
⛔ 任一 STOP → 先解决再进；强行跑 = 自欺。

> **[硬代码]** 预检闸的第 2 项不再靠人自觉——它由 `scripts/audit_guard.py selfcheck` 以退出码强制。发布前必跑，退出码非 0 即不允许进入闭环。

### 异常 → 应对映射表 / Exception → Action map

| 异常情形 | 应对（X → 做 Y） |
|---|---|
| 目标 skill 路径不存在 / 拼错 | 先 `find ~/.workbuddy/skills -name SKILL.md` 定位；把**精确绝对路径**交给审计员 |
| `Agent` / `Task` 或 leaf 子代理工具不可用 | **兜底**：用主代理在「清空相关上下文后」做一次独立审计（把目标 skill 当陌生文件读）；或改由 Agent / Task 工具派发同等 fresh 上下文子代理。**绝不让同一个人既是优化器又是审计员** |
| 复审分数 C 比预期低很多 | 不要自动否定 C；先按「评分约定 · C−B > +3 → 重核实 C」重读 C 的基线 / 量规是否与 B 一致 |
| B−C > +3（自评分虚高） | 以 C 为准，丢弃 B；把 C 的发现作为权威修复清单 |
| 跨文件计数漂移（如 10 类 vs 11 类） <!-- audit-guard:ignore --> | 以 references/ 源文件为事实来源，回改正文摘要使其一致 |
| 子代理超时 / 部分落地 | 见 `references/subagent-timeout-partial-landing.md`：保留已落地的 diff，重跑未完成的审计项 |
| 多轮闭环内审计员自审分 ≠ C | 多轮内自审只是自检；真正独立 C 由主代理轮后验证提供（见「评分约定」） |

### 失败恢复决策树 / Failure-recovery decision tree
```
审计中断？
├─ 路径错误        → 重定位绝对路径，重跑 ①
├─ 审计员工具缺失   → 主代理清上下文自审 / Agent 派发 fresh 子代理（本环境用 Agent）
├─ 子代理超时      → 保留 diff，分段重跑剩余审计项（见 subagent-timeout 文档）
└─ 分数异常(B/C)   → 走「评分约定」定向差值规则，主代理交叉核对
```

## 审计上下文包（供独立子代理使用）(Audit Context Package (for the independent subagent))

提供给审计员：

Give the auditor:

1. 技能目录的精确绝对路径
1. Exact absolute path to skill directory
2. 文件清单（运行 `find + wc -l`，粘贴结果）
2. File inventory (run `find + wc -l`, paste)
3. SKILL.md 前 100 行
3. SKILL.md first 100 lines
4. 先前的审计发现（让审计员知道该「跳过看什么」，而不是「重新发现什么」）
4. Prior audit findings (so auditor knows what to look past, not what to rediscover)
5. 明确指令："首要任务是问'这个设计是对的吗？'，而不是'这段代码写得漂亮吗？'"
5. Explicit instruction: "The primary task is to ask 'Is this design correct?', not 'Is this code written beautifully?'"

叶节点代理没有技能目录感知——始终提供绝对路径。

The leaf agent has no skill directory awareness — always provide absolute paths.

## 数据与隐私 (Data & Privacy)

本技能**不读取、不存储、不外传任何用户数据或凭据**：审计对象仅为技能目录内的文件（SKILL.md / references/ / scripts/），全程只读——审计员 toolsets=['file','terminal']，只评不改。`audit_guard.py` 的轮次状态文件仅记录技能路径 + 轮次号 + 时间戳（`~/.workbuddy/.audit_loop_state.json`），不含任何内容数据。若被审计的 skill 自身含敏感信息，请先脱敏再提供审计上下文包——上下文包只要求文件清单与 SKILL.md 前 100 行，不要求粘贴完整正文。

## 评分约定 (Scoring Convention)

> **[注意]** 优化后（同一量规）**分数 C（复审）是权威分，不是 B（自评）**。任何纠结都先回到这条。

→ `references/score-reading-guide.md` — B/C/A 分数**速读指南**（一句话卡片 + 决策表 + 3 个数值场景），看不懂评分约定时先读它

- 独立审计员对独立三步闭环使用 skill-audit 8 阶段量规（100 分）。当闭环被直接调用时，分数 B 和分数 C 都在此量规上衡量。
- Independent auditor uses skill-audit 8 Phase rubric (100 points) for the standalone three-step loop. Score B and score C are both measured on this scale when the loop is invoked directly.
- 代码质量 /15 → 纯文档技能为 N/A；从总分中剔除，归一化到 85 分制
- Code Quality /15 → N/A for pure-docs skills; omit from total, normalize to 85-point scale
- 对于多轮独立审计员闭环（`references/independent-auditor-multiround-loop.md`），审计员在达尔文 9 维量规下工作（每维 0-10，加权和 /90）。B 与 C 的差值规则不适用于跨量规：当混合 /100 与 /90 时，比较前先转换为相对百分比（例如 >3% 的量规满分）。
- For the multi-round independent-auditor loop (`references/independent-auditor-multiround-loop.md`), the auditor operates under Darwin 9-dimension rubric (each 0-10, weighted sum /90). The B-vs-C delta rule does not apply cross-rubric: when mixing /100 and /90, convert to relative percentage before comparing (e.g. >3% of rubric max).
- 在多轮闭环内，审计员自身的复审分数只是一次自检，而非独立的「C」——真正的独立 C 由主代理的轮后验证提供。
- Within the multi-round loop, the auditor's own re-audit score is a self-check, not an independent "C" — the true independent C is provided by the lead agent's post-round verification.
- 优化后（同一量规）：分数 C（复审）是权威分数，而非 B（自评分）。经主代理交叉核对后，C 成立。
- Post-optimization (same rubric): score C (re-audit) is the authoritative score, not B (self-score). After lead-agent cross-check, C stands.
- B 与 C 的差值：若 B − C > +3 分，则自评分虚高；以 C 为准。若 C − B > +3 分，则重新核实 C（基线或审计量规不同）——不要自动否定。
- Delta between B and C: if B − C > +3 points, self-score was inflated; treat C as truth. If C − B > +3 points, re-verify C (different baseline or auditor scale variation) — do not automatically dismiss.

## 案例研究：unclekk-darwin-evolver（2026-07-23）(Case Study: unclekk-darwin-evolver (2026-07-23))

→ `references/unclekk-darwin-evolver-case.md`（完整案例记录）
→ `references/unclekk-darwin-evolver-case.md` (full case record)
→ `references/audit-report-sample.md` — **完整 A/B/C 报告样例**（审计上下文包 → A 报告 → 优化 B → 复审 C → 差值决策），可复制模板

第 1 轮：独立审计，68/100，3×P0 + 5×P1 + 8×P2
Round 1: independent audit, 68/100, 3×P0 + 5×P1 + 8×P2

达尔文优化：自评分 86/100，50+ 次 API 调用，触及迭代上限
Darwin optimization: self-scored 86/100, 50+ API calls, hit iteration limit

第 2 轮：独立审计，82/100，8 次 API 调用，304 秒——发现 4 个优化器遗漏的问题：
Round 2: independent audit, 82/100, 8 API calls, 304s — found 4 things optimizer missed:

- P1-新1: 触顶判定算法与进化实例矛盾（P0-3深层残余）
- P1-new1: ceiling-determination algorithm contradicts the evolution example (P0-3 deep residual)
- P2-新1: references/"failure-modes.md" 计数残留（10类 vs 11类） <!-- audit-guard:ignore -->
- P2-new1: references/"failure-modes.md" count residual (10 categories vs 11 categories) <!-- audit-guard:ignore -->
- P2-新3: results.tsv dimension字段=-
- P2-new3: results.tsv dimension field = -
- P2-新4: results-tsv-template.md SHA示例含非法字符
- P2-new4: results-tsv-template.md SHA example contains illegal characters

## 互补技能 (Complementary Skills)

- `skill-audit` / `software-development/skill-audit` — 8 阶段方法论（审计部分）
- `skill-audit` / `software-development/skill-audit` — 8 Phase methodology (the audit half)
- `unclekk-darwin-evolver` — unclekk 的达尔文优化工作流（优化部分）
- `unclekk-darwin-evolver` — unclekk's Darwin optimization workflow (the optimize half)
