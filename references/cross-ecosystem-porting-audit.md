# 跨生态移植审计案例（grill-me，2026-07-24）
# Cross-Ecosystem Skill Porting Case Study (grill-me, 2026-07-24)

技能最初为 Claude Code/Cowork 编写，移植到 Hermes。
Skill originally written for Claude Code/Cowork, ported to Hermes.

## 初次审计：36/100
## Initial Audit: 36/100

- P0：Hermes 中不存在 AskUserQuestion 工具，Hermes 用的是 clarify。
- P0: AskUserQuestion tool does not exist in Hermes. Hermes uses clarify.
- P0：缺少 7 个标准 Hermes 章节。
- P0: 7 standard Hermes sections all missing.
- P0：description 达 247 字符（上限 60）。
- P0: description = 247 chars (limit 60).
- P0：README 声称它是 Claude Code 技能。
- P0: README claims it is a Claude Code skill.
- P0：路径引用 `~/.claude/skills/`。
- P0: Paths reference ~/.claude/skills/.

## 根因
## Root Cause

移植代理没有检测到生态不匹配，因为它对源生态太熟悉。对移植品做自审不可靠。
Ported agent did not detect ecosystem mismatch because it knew the source ecosystem too well. Self-audit of a port is unreliable.

## 修复（v2.0.0）：+49 分到 85/100
## Fix (v2.0.0): +49 points to 85/100

- AskUserQuestion → Hermes clarify
- AskUserQuestion -> Hermes clarify
- 补齐全部 7 个标准 Hermes 章节
- All 7 Hermes standard sections added
- description 压缩 247→47 字符
- Description compressed 247->47 chars
- 移除 `~/.claude/` 路径
- Removed ~/.claude/ paths
- README 按 Hermes 身份重写
- README rewritten for Hermes identity
- 新增 `references/grill-templates.md`（5 个领域模板）
- Added references/grill-templates.md with 5 domain templates
- Phase 0/1/2/3 结构化流程
- Phase 0/1/2/3 structured procedure

## v2.1.0：+4 分到 89/100
## v2.1.0: +4 points to 89/100

- Phase 0：结构化的 GRILL 开场横幅模板
- Phase 0: structured GRILL start banner template
- Phase 1：决策树预览格式
- Phase 1: decision tree preview format
- 陷阱：消息平台兜底 + API 直连路径
- Pitfalls: message-platform fallback + API-direct-call path
- README：加 v2.1.0 版本标签
- README: added version 2.1.0 tag
- SKILL.md Phase 2：`clarify(question, choices=[...])` 签名
- SKILL.md Phase 2: clarify(question, choices=[...]) signature

## 最终独立审计：84-89/100
## Final Independent Audits: 84-89/100

差值约 0，仅为审计员方差。按 Darwin HL-4 确认触顶。
Delta ~0. Auditor variance only. Touch-top confirmed per Darwin HL-4.

## 检测模式
## Detection Pattern

当技能来自 Hermes 之外时，grep 以下内容：
When a skill comes from outside Hermes, grep for:

```
AskUserQuestion, promptForChoice, ~/.claude, Claude Code skill
```

任一命中 → 立即判 P0。Hermes 中不存在的工具名会阻断所有执行。
Any match -> immediate P0. Tool names that do not exist in Hermes block all execution.

## 关键教训
## Key Lesson

移植代理是自己移植品最差的审计员。跨生态移植务必使用**独立 Agent/Task（role=leaf）审计员**。自审差距 89 vs 84（5 分），但初次移植的 P0 被移植代理**零检出**——只有独立审计员抓到。
The porting agent is the worst auditor for its own port. Use an independent Agent/Task (role=leaf) auditor for cross-ecosystem ports. The self-audit gap was 89 vs 84 (5 points), but the initial port had zero P0 detection by the porting agent — only the independent auditor caught them.
