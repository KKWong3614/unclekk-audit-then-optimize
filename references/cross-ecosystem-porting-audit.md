# Cross-Ecosystem Skill Porting Case Study (grill-me, 2026-07-24)

Skill originally written for Claude Code/Cowork, ported to Hermes.

## Initial Audit: 36/100

P0: AskUserQuestion tool does not exist in Hermes. Hermes uses clarify.
P0: 7 standard Hermes sections all missing.
P0: description = 247 chars (limit 60).
P0: README claims it is a Claude Code skill.
P0: Paths reference ~/.claude/skills/.

## Root Cause

Ported agent did not detect ecosystem mismatch because it knew the source ecosystem too well. Self-audit of a port is unreliable.

## Fix (v2.0.0): +49 points to 85/100

- AskUserQuestion -> Hermes clarify
- All 7 Hermes standard sections added
- Description compressed 247->47 chars
- Removed ~/.claude/ paths
- README rewritten for Hermes identity
- Added references/grill-templates.md with 5 domain templates
- Phase 0/1/2/3 structured procedure

## v2.1.0: +4 points to 89/100

- Phase 0: structured GRILL start banner template
- Phase 1: decision tree preview format
- Pitfalls: message-platform fallback + API-direct-call path
- README: added version 2.1.0 tag
- SKILL.md Phase 2: clarify(question, choices=[...]) signature

## Final Independent Audits: 84-89/100

Delta ~0. Auditor variance only. Touch-top confirmed per Darwin HL-4.

## Detection Pattern

When a skill comes from outside Hermes, grep for:
AskUserQuestion, promptForChoice, ~/.claude, Claude Code skill
Any match -> immediate P0. Tool names that do not exist in Hermes block all execution.

## Key Lesson

The porting agent is the worst auditor for its own port. Use an independent delegate_task(role=leaf) auditor for cross-ecosystem ports. The self-audit gap was 89 vs 84 (5 points), but the initial port had zero P0 detection by the porting agent — only the independent auditor caught them.
