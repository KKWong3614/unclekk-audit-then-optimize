---
name: unclekk-audit-then-optimize
slug: unclekk-audit-then-optimize
displayName: UncleKK 审计长闭环优化审计
version: 1.0.3
summary: UncleKK 的独立审计→优化→独立复审闭环工作流，防止自评分虚高、抓住优化器漏改的残留缺陷。Unclekk's independent-audit → optimize → independent re-audit loop — prevents self-score inflation and catches residual bugs the optimizer misses.
description: 'UncleKK 的独立审计→优化→独立复审闭环工作流。防止自评分虚高，抓住优化器漏改的残留缺陷。Unclekk''s independent-audit → optimize → independent re-audit loop: prevents self-score inflation and catches residual bugs the optimizer misses.'
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

unclekk's three-step pattern: **independent audit → optimize → independent re-audit**.

This skill codifies the independent-third-party-auditor methodology for unclekk's skill ecosystem — preventing self-score inflation and catching residual bugs that the optimizer assumes fixed.

This skill encodes what we learned on unclekk-darwin-evolver (2026-07-23): the optimizer self-scored 86/100, the independent auditor scored 82/100 and found 4 things the optimizer missed. Self-scores are consistently inflated.

## Why This Pattern Exists

An optimizer (whether a subagent or the main agent) that just finished editing a file:
- Knows what it fixed → assumes it fixed it correctly
- Has context inheritance from the original audit → sees the "before" state
- Is biased toward its own work → optimistic about what it produced

An independent auditor (leaf subagent, fresh context, toolsets=['file','terminal']):
- Does not inherit the optimizer's history
- Reads the file as a stranger would
- Catches residual bugs the optimizer assumed fixed

The independent auditor costs ~8 API calls and 5 minutes. The optimizer costs 50+ calls and can hit the iteration limit.

## The Loop

```
1. Independent audit (leaf subagent) → score A, findings list
2. Optimize (main agent or subagent) → self-score B
3. Independent re-audit (leaf subagent) → score C
4. Compare A, B, C. If B − C > +3 points, suspect self-score inflation (optimizer over-claims); if C − B > +3 points, re-verify C (auditor may use different baseline or scoring scale — see Scoring Convention). In either direction, delta warrants lead-agent re-check.
5. Fix any P1/P2 the re-audit found that the optimizer missed.
→ `references/cross-ecosystem-porting-audit.md`
→ `references/independent-auditor-multiround-loop.md` — 多轮独立审计长模式：主 Agent 派发，审计长（leaf subagent）独立执行达尔文+SkillEvolution直到触顶，主 Agent 独立验证结果。适用于用户要求"优化 skill 直到触顶"的场景。

## When to Use

- User asks for "优化 skill" and the skill is a meta-skill or methodology skill
- After any optimization that produces a self-score
- When a prior audit found P0s and you want to verify they're truly fixed
- When you suspect the optimizer's score is inflated (always, post-optimization)
- **Cross-ecosystem ports**: skill cloned from another platform (Claude Code, Cursor, etc.) — the porting agent is blind to tool-name incompatibility. Always use an independent auditor, never self-audit. → `references/cross-ecosystem-porting-audit.md`

## Pitfalls (from unclekk-darwin-evolver case study)

**P0-3 residual: fix the algorithm, not just the wording.**
If a skill defines its own termination/ceiling rule (e.g. "连续2轮Δ<2"), and the skill ships an evolution example claiming to follow that rule — verify the example actually satisfies the rule. A counterexample in the skill's own example is a P1 defect, not "needs clarification."

**Cross-file counts must match.**
When a skill body says "N类失败模式", every references/ file that repeats that count must match. The body is the summary; the references/ file is the source of truth. They often drift.

**Check copyable example files.**
results.tsv, templates, tsv samples — these are what users actually copy. SKILL.md is what they read. Both need to be verified.

**Meta-skills have a self-referential dimension-8 problem.**
A skill that defines its own quality metric must have a non-circular way to evaluate itself. If the highest-weighted dimension requires "real testing" but the skill IS the methodology, that dimension degrades to dry_run. This is a structural deadlock, not a documentation gap.

## Audit Context Package (for the independent subagent)

Give the auditor:
1. Exact absolute path to skill directory
2. File inventory (run `find + wc -l`, paste)
3. SKILL.md first 100 lines
4. Prior audit findings (so auditor knows what to look past, not what to rediscover)
5. Explicit instruction: "首要任务是问'这个设计是对的吗？'，而不是'这段代码写得漂亮吗？'"

The leaf agent has no skill directory awareness — always provide absolute paths.

## Scoring Convention

- Independent auditor uses skill-audit 8 Phase rubric (100 points) for the standalone three-step loop. Score B and score C are both measured on this scale when the loop is invoked directly.
- Code Quality /15 → N/A for pure-docs skills; omit from total, normalize to 85-point scale
- For the multi-round independent-auditor loop (`references/independent-auditor-multiround-loop.md`), the auditor operates under Darwin 9-dimension rubric (each 0-10, weighted sum /90). The B-vs-C delta rule does not apply cross-rubric: when mixing /100 and /90, convert to relative percentage before comparing (e.g. >3% of rubric max).
- Within the multi-round loop, the auditor's own re-audit score is a self-check, not an independent "C" — the true independent C is provided by the lead agent's post-round verification.
- Post-optimization (same rubric): score C (re-audit) is the authoritative score, not B (self-score). After lead-agent cross-check, C stands.
- Delta between B and C: if B − C > +3 points, self-score was inflated; treat C as truth. If C − B > +3 points, re-verify C (different baseline or auditor scale variation) — do not automatically dismiss.

## Case Study: unclekk-darwin-evolver (2026-07-23)

→ `references/unclekk-darwin-evolver-case.md` (full case record)

Round 1: independent audit, 68/100, 3×P0 + 5×P1 + 8×P2
Darwin optimization: self-scored 86/100, 50+ API calls, hit iteration limit
Round 2: independent audit, 82/100, 8 API calls, 304s — found 4 things optimizer missed:
- P1-新1: 触顶判定算法与进化实例矛盾（P0-3深层残余）
- P2-新1: references/"failure-modes.md" 计数残留（10类 vs 11类）
- P2-新3: results.tsv dimension字段=-
- P2-新4: results-tsv-template.md SHA示例含非法字符

## Complementary Skills

- `skill-audit` / `software-development/skill-audit` — 8 Phase methodology (the audit half)
- `unclekk-darwin-evolver` — unclekk's Darwin optimization workflow (the optimize half)
