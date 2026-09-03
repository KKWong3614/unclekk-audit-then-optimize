# 完整调用示例 — 一步不漏的最小闭环

> 这是 `unclekk-audit-then-optimize` 的**全填好版本**。
> 把下面每一处的真实路径换成你自己的即可，无需再猜参数。
> This is the fully-filled version of the invocation template. Swap the real paths; nothing else to guess.

**示范目标**：对 `unclekk-safety-harness-evolution` 做一次「优化 → 独立复审」。
**环境**：Windows + Git Bash；审计员用 Agent 子代理（fresh 上下文）。

---

## 步骤 0：生成「文件清单」（粘贴进审计上下文包）

在 Bash / Git Bash 里跑（注意 Windows 路径用 POSIX 写法或 `cygpath -m`）：

```bash
# 目标 skill 目录（绝对路径）
SKILL_DIR="C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution"

# 1) 文件清单
find "$SKILL_DIR" -type f | sort

# 2) 行数统计（审计员要看体量）
find "$SKILL_DIR" -type f -exec wc -l {} +
```

真实输出示例（节选）：

```
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/SKILL.md
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/_meta.json
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/package.json
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/scripts/evolve_guard.py
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/scripts/sync_artifacts.py
...
```

---

## 步骤 1：独立审计（①，Agent 子代理，fresh 上下文）

调用（所有占位符已填真实值）：

```python
# 本环境用 Agent 工具（subagent_type="general-purpose"，全新上下文）；delegate_task 仅当宿主支持时作别名
Agent(
  description="独立审计 unclekk-safety-harness-evolution",
  subagent_type="general-purpose",
  prompt=f"""你是独立第三方审计员（fresh 上下文，只评不改）。
审计目标：C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution
文件清单：
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/SKILL.md
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/scripts/evolve_guard.py
C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution/scripts/sync_artifacts.py
（其余见 find 输出）
先前发现（供跳过，非重发现）：无（首轮）
首要问题：'这个设计是对的吗？' 而非 '代码写得漂亮吗？'
量规：skill-audit 8 阶段 /100，并产出 P0/P1/P2 清单。""",
)
```

> ✅ 产出：A 评分 + 发现清单（记到 `references/audit-<skill>-<日期>.md`）。

---

## 步骤 2：优化（②，主代理 / 优化器）→ 自评分 B

主代理读取 A 的发现，逐条修复，给出自评分 B。
**B 只是乐观分，不要当真。**

---

## 步骤 3：独立复审（③，另一个 fresh Agent 子代理）→ 评分 C

```python
Agent(
  description="独立复审 unclekk-safety-harness-evolution",
  subagent_type="general-purpose",
  prompt=f"""你是独立第三方复审员（fresh 上下文，只评不改）。
审计目标：C:/Users/user/.workbuddy/skills/@user_48f048de/unclekk-safety-harness-evolution
文件清单：（同上 find 输出）
先前发现（供跳过，非重发现）：
- A 轮发现 P0-1/P0-2/P0-3，本次重点核对其是否真被修复
- 关注优化器可能自认为已修但残留的缺陷
首要问题：'这个设计是对的吗？' 而非 '代码写得漂亮吗？'
量规：skill-audit 8 阶段 /100，重点核对 A 的发现是否真修复，并找优化器漏改的残留缺陷。""",
)
```

> ✅ 产出：C 评分 + 复审发现（尤其是优化器漏改的残留）。

---

## 步骤 4：比较 A / B / C（④）

```
A = （步骤1 分数）      B = （步骤2 自评分）     C = （步骤3 分数）
B − C > +3  →  自评分虚高，以 C 为准，用 C 的发现做权威修复清单
C − B > +3  →  不要自动否定 C，先重核实 C 的基线/量规是否和 B 一致
其余小幅  →  主代理交叉核对即可
```

详见 `references/score-reading-guide.md`（含 3 个数值场景）。

---

## 步骤 5：修复复审发现的 P1/P2（⑤）

主代理按 C 的发现（特别是优化器漏改的残留）逐条修复。修复后若又产生自评分，回到步骤 1。

---

## 兜底：审计员工具选择（本环境用 Agent）

三选一，**核心：优化器与审计员不能是同一上下文**：

1. 用 Agent / Task 工具派发一个 fresh 子代理（首选；本环境 Agent 可用）；
2. 主代理**清空相关上下文后**自审（把目标 skill 当陌生文件读）；
3. 直接开另一个 WorkBuddy 会话/账号做审计。

> `delegate_task` 仅在宿主环境支持时作为别名，切勿写死为本环境不存在的工具。

> 完整异常处理见 SKILL.md「异常处理 / Error Handling」与 `references/faq.md` Q2。
