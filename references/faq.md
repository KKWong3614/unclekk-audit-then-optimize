# 高频问答 FAQ — unclekk-audit-then-optimize

> 把用户最常问、却散落在长文档里的问题，集中成 Q&A。读完本文件即可判断「要不要走这个闭环、怎么走、分数怎么读」。
>
> High-frequency Q&A distilled from the long-form SKILL.md. Read this to decide whether / how to run the loop and how to read the scores.

---

## 速查对照表（先扫这两张，再往下读）

### 表 1：什么时候走闭环 vs 直接优化

| 场景 | 走闭环？ | 原因 |
|---|:---:|---|
| 优化会产生自评分（尤其元技能 / 方法论技能） | ✅ 走 | 自评分几乎必然偏高 |
| 先前的审计发现 P0，想验证是否真修复 | ✅ 走 | 独立视角才能确认 |
| 跨生态移植来的 skill（Claude Code/Cursor→Hermes） | ✅ 走 | 移植者看不见工具名不兼容 |
| skill 极简单、优化不产生自评分、本就打算直接改 | ❌ 不走 | 独立审计是浪费 |
| 时间/成本极度受限，连一次审计都负担不起 | ❌ 不走（降级：主代理清上下文自审） | 至少保留降级方案 |
| 改动属安全/合规关键且你无权独立处置 | ❌ 不走 | 走正式评审/审批 |
| 你已 100% 确信正确，且优化器=审计员同一上下文 | ❌ 不走 | 独立审计无意义 |

### 表 2：B·C 差值速查（详细见 `references/score-reading-guide.md`）

| 差值 | 含义 | 行动 |
|---|---|---|
| B − C > +3 | 自评分虚高 | 丢弃 B，以 C 为准，用 C 的发现做权威清单 |
| C − B > +3 | 别急着否定 C | 先重核实 C 的基线/量规是否和 B 一致 |
| \|差值\| ≤ +3 | 小幅波动（正常方差） | 主代理交叉核对即可 |

> 铁律：优化后同一量规下 **C 是权威分，不是 B**。

---

## Q1：什么时候该用这个模式，而不是自己直接优化？

**A：** 只要这次优化**会产生自评分**，就该走闭环——因为自评分几乎必然偏高（证据：unclekk-darwin-evolver 优化器自评 86，独立审计 82，差 4 分）。具体触发场景见 SKILL.md「使用时机」。

若 skill 极简单、你本就打算直接改、且优化不产生自评分，则独立审计是浪费，直接用优化器即可。详见「不适用场景」。

> **When to use:** any optimization that produces a self-score should go through the loop. Skip it only for trivial edits with no self-score involved.

---

## Q2：审计员工具怎么选（本环境用哪个）？

**A：** 本环境用 **`Agent` 工具**（`subagent_type="general-purpose"`，全新上下文）派发独立审计员；`Task` 工具同等可用。`delegate_task` 仅在宿主环境支持时作为别名。核心原则永远是**「优化器」与「审计员」不能是同一上下文**，三选一兜底：

1. 用 `Agent` / `Task` 工具派发一个 fresh 上下文的子代理（首选）；
2. 主代理在**清空相关上下文后**做一次独立审计（把目标 skill 当陌生文件读）；
3. 直接请另一个独立的 WorkBuddy 会话/账号做审计。

**绝不要让同一个人既当优化器又当审计员**——那会抵消整个闭环的意义。

> **Fallback if no leaf tool:** the optimizer and the auditor must never share context. Use a fresh-context agent or a separate session.

---

## Q3：B、C 两个分数哪个才是准的？

**A：** 优化后（同一量规），**C（独立复审）是权威分，不是 B（自评分）**。经主代理交叉核对后 C 成立。A 是优化前的基线，用于看「优化到底有没有进步」。

> **Which score is truth:** post-optimization, C (re-audit) is authoritative, not B.

---

## Q4：B 和 C 的差值怎么解读？

**A：** 规则是**有方向的**（不是简单的「差>3 就否定」），直接查表：

| 差值 | 判定 | 行动 |
|---|---|---|
| **B − C > +3** | 自评分虚高 | 以 C 为准，丢弃 B 的发现，把 C 的发现当权威修复清单 |
| **C − B > +3** | 别急着否定 C | 先重核实 C 的基线/量规是否与 B 一致（可能审计员用了不同基准或量规） |
| **其余小幅差异** | 正常方差 | 主代理交叉核对即可 |

> **Delta rule is directional:** inflation (B>C) vs re-verify (C>B) are handled differently. Never auto-dismiss a higher C.

---

## Q5：元技能「自指性第 8 维死锁」怎么破？

**A：** 一个定义了自身质量指标的技能，无法循环地评估自己。解法：当最高权重维度要求「真实测试」但该技能本身就是方法论时，该维度**退化为 dry_run**——改用「主代理人工核对 C」代替机器打分（见 SKILL.md 评分约定）。这是结构性现实，不是文档缺口，接受它即可。

> **Self-referential deadlock:** accept that the "real test" dimension degrades to dry_run for pure-methodology skills; substitute lead-agent human verification for C.

---

## Q6：纯文档 skill（无代码）也能用这个闭环吗？

**A：** 能，且更需要——纯文档 skill 没有测试可跑，优化后最容易「自以为改对了」。注意两点：

- 评分约定中「代码质量 /15」对纯文档 skill 为 N/A，归一化到 85 分制；
- 其「真实测试」维度退化为 dry_run（见 Q5）。

> **Pure-docs skills:** fully supported; code-quality dimension is N/A (normalize to /85). They need the loop *more*, not less.

---

## Q7：独立审计员该配什么工具集？

**A：** 推荐 `toolsets=['file','terminal']`（只读文件 + 跑只读命令），不要给写入/发布工具——审计员只评不改。始终通过**绝对路径**提供技能目录（leaf 代理没有技能目录感知）。

> **Auditor toolset:** read-only `['file','terminal']`; pass the skill dir as an absolute path.

---

## Q8：复审（C）没发现新问题，是不是就完美了？

**A：** 不是。C 没发现新 P0/P1，只说明在你给的审计上下文包下没找到——可能审计员漏看了你没提供的文件，或基线本身就有盲区。若你仍不放心，换一个 fresh 审计员再跑一轮，或扩大审计上下文包（见「审计上下文包」第 2 项文件清单）。

> **"C found nothing" ≠ perfect:** it means nothing surfaced under the context you supplied. Re-run with a fresh auditor or a broader context package if uneasy.

---

## Q9：怎么避免正文与 references 的计数漂移（如「N 类失败模式」对不上）？

**A：** 正文是摘要，references/ 文件才是事实来源。凡是重复计数的地方，**以 references/ 为准**，发现不一致就回改正文。本技能自身已把这条列为 P1 缺陷，发布前务必用 grep 核一遍所有计数。

> **Count drift:** references/ files are source of truth; reconcile the body to them before publishing.

---

## Q10：多轮闭环里，审计员的自审分算不算独立 C？

**A：** 不算。多轮闭环内，审计员自己的复审只是一次**自检**；真正的独立 C 由**主代理的轮后验证**提供。混淆二者会高估闭环的严谨度。

> **Multi-round self-audit ≠ C:** only the lead agent's post-round verification counts as the independent C.
