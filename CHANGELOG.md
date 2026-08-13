# CHANGELOG

## v1.0.3 (2026-08-13)

- README restructured to section-by-section bilingual: every heading/paragraph now has the Chinese text immediately followed by its English translation (overview, loop, all six breakdown sections, file table) — instead of a CN block then a separate EN block. Overview is now CN-first / EN-second as required.

## v1.0.2 (2026-08-13)

- README bilingual completion: added the full English version of "The Audit-Lead's Two-Layer Audit System: Full Breakdown" (7-Phase process, two scoring rubrics, 8-layer design review, diagnostic checklist, execution constraints, defect tiering) to mirror the Chinese section
- Bumped to v1.0.2 (SKILL.md, package.json)
- Synced package copy to the `.workbuddy` install copy

## v1.0.1 (2026-08-13)

- Post-audit fixes (independent third-party audit, 2026-08-13):
  - P1-3: Fixed Case Study link mismatch — added `references/unclekk-darwin-evolver-case.md` (full case record matching the title)
  - P1-4: Clarified Scoring Convention — /100 (skill-audit rubric) vs /90 (Darwin 9-dim) applicable contexts; cross-rubric comparison uses relative percentage
  - P1-5: Multi-round loop now declares leaf self-audit ≠ independent "C"; true C requires lead-agent post-round verification
  - P2-4: B-vs-C delta rule now directional: B−C>+3 → inflation, C−B>+3 → re-verify C
  - P2-6: `failure-modes.md` reference quoted to mark as external file
- New: `references/unclekk-darwin-evolver-case.md` — full case record for the darwin-evolver audit example
- Fixed: duplicate CHANGELOG entry for broken link fix (was recorded in both v1.0.0 and v1.0.1)
- Dual-copy sync: `.workbuddy/skills/` copy synchronized with `D:/skill已检/` canonical copy

## v1.0.0 (2026-08-13)

- Initial release of unclekk-audit-then-optimize skill (SkillHub namespace: unclekk)
- Three-step loop: independent audit → optimize → independent re-audit
- Independent auditor multi-round meta-audit loop
- Subagent timeout handling playbook
- Cross-ecosystem porting audit case study
- Diagnostic checklist method (P0/P1/P2 defect inventory)
- Ceiling-confirmed dead-code remediation
- unclekk-harness v1.0.5 4th-round independent audit case study
- Fixed: broken reference link in SKILL.md (case study section)
- NTFS case-folding safe: ships SKILL.md + package.json (no skill.md)
- All line endings normalized to LF for GitHub compatibility