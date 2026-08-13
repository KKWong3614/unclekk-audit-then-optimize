# unclekk-harness 第 4 轮独立审计案例（v1.0.5，2026-07-30）

## 背景

独立 leaf agent 审计 unclekk-harness（orchestrator，6 阶段管线，零依赖 stdlib），
主 Hermes 事后抽验关键断言并按 P0→P1 修复，再补跑全量回归 + 打包交付。

## 流程

1. 主 Hermes 加载 skill（SKILL.md / harness.py / test_harness.py / audit-layers.md）
2. 启动独立 leaf 审计 agent（delegate_task，role=leaf，toolsets=[file,terminal]），
   主 Hermes 不参与审计过程（零预读、零评分、零方向）
3. 审计长 6 层方法论（L0-L5）→ NEEDS_REVISION
4. 主 Hermes 抽验 P0-1 / P0-2 关键发现（实证）
5. P0 修复 + 补 2 项回归 + 39/39 全量通过 + ad-hoc 专项验证（5/5）
6. 打包到 `D:/已检skill/unclekk-harness/`（排除 __pycache__，目标目录复测 39/39）

## 审计长发现 vs 主 Hermes 抽验结果

| 审计长声称 | 主 Hermes 抽验 | 结论 |
|-----------|---------------|------|
| P0-1: skeleton plan 返回 ok:true，与文档"报错"承诺矛盾 | 实证确认 | 真实缺陷，已修 |
| P0-2: SKILL.md 多处写"33 项"，实际 37（现 39）项 | 实证确认 | 真实缺陷，已修 |
| P1-2: stage 枚举缺 init/recovered | 实证确认 | 真实缺陷，已修 |
| P2-2: results.tsv 无 v1.0.1 行，74→92 断言缺支撑 | 实证 **推翻**：tsv 第 3 行已有 v1.0.1 (old=74, new=92) | 审计长误判 |
| P1-1/P2-1: 维持观察 | — | 未修，已实测安全 |

## 关键教训（generalize 到 audit-then-optimize loop）

**审计长的数据声称必须用主 Hermes 抽验。**
"evolution-log 声称 X 闭合/分数 Y" 类断言，必须回查 results.tsv / 原始输出文件确认对应数据行存在。
本案例审计长声称"tsv 无 v1.0.1 行"，抽验发现该声称错误——如果主 Hermes 不抽验就直接采信，会错误地补一行重复数据。

这是 2026-07-22 审计铁律的另一个实例：
> evolution-log 每项"闭合/已评分"声称必须在 results.tsv 有对应数据行，否则是虚构断言。

本案例反向：审计长的声称（"无行"）也是虚构断言，抽验纠正了它。
→ 所有"计数/缺失/存在"类声称必须实测，不能采信审计长的 grep 结论。

## 修复内容（v1.0.5）

- P0-1: `validate_state()` 拦截 `[LLM:` 前缀，skeleton plan 现返回 ok:false
- P0-2: SKILL.md 文档 33→39 测试数系统性修正（自测/文件结构/变更记录三处）
- P1-2: SKILL.md stage 枚举补充 init/recovered
- +2 回归测试（39/39）
- 新增 CHANGELOG.md，results.tsv v1.0.5 行，evolution-log v1.0.5 章节

## 打包交付

`D:/已检skill/unclekk-harness/`，12 文件，__pycache__ 已排除，
SKILL.md frontmatter 含 name/version/description/license，目标目录回归 39/39。