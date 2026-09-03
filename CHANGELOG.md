# CHANGELOG

## v1.2.3 (2026-08-29)

- TRACE「国内适配性」字面达标提升（此前按实质标准判 5.0，字面口径 4.5）：
  - SKILL.md 新增「语言说明」章节：中文为第一使用语言、仅凭中文即可完整使用、口语化中文触发词示例、中英出入以中文为准
  - `references/cross-ecosystem-porting-audit.md` 双语化：全仓唯一纯英文文档改为中英对照（与生态其他文件一致）
- 版本号五处统一升至 1.2.3

## v1.2.2 (2026-08-29)

- 「受众说明」扩展为**所有 Agent 用户**：方法论（防自评虚高）对 prompt / 工作流 / 代码 / 方案等一切会产生自评分的优化场景通用，不限于 Skill 开发者；工具层 `audit_guard.py` 审计对象仍为 skill 文件。
- 版本号五处统一升至 1.2.2

## v1.2.1 (2026-08-29)

- TRACE 五维评测（skill-trace-checker）改进，<5.0 子项实质补齐：
  - **T-数据隐私规范**：SKILL.md 新增「数据与隐私」章节（审计只读、不存不传用户数据、状态文件仅轮次+时间戳、敏感 skill 先脱敏再提供上下文包）
  - **A-能力边界定义**：SKILL.md 新增「能力边界总览」三分类表（✅擅长 5 项 / ⚠️需素材 5 项 / ❌超范围 5 项）
  - **A-受众广度**：SKILL.md 新增「受众说明」章节（个人开发者 / 团队维护者 / 审核员 / 非主要用户）
  - **C-反模式说明**：新增 `references/anti-patterns.md`（6 类错误用法 vs 改进示例对比 + 8 条禁忌清单）
  - **C-FAQ 深度**：新增 `references/faq-deep.md`（14 题深度 FAQ：边缘场景 / 工具兼容 / 安全合规 / 脚本故障排查）
  - **T-国内适配性**：双语设计属 unclekk 生态技术惯例（中文为主语言、示例/触发词/场景均国内），如实记录为设计取舍，不改动
- `chk_disallowed_tools` 增加代码块剥离（反模式文档的"错误用法"示例是教学文本，非操作指令）
- 版本号五处统一升至 1.2.1

## v1.2.0 (2026-08-29)

- 依据第三方 agent 深度审计（`references/deep-audit-unclekk-audit-then-optimize-2026-08-29.md`，P0×1/P1×8/P2×12）系统性修复，核心目标：**硬代码「能检出」而非仅「能运行」**。
- 修复 P0-1（残留）：`cross-ecosystem-porting-audit.md` / `unclekk-harness-audit-v105-case.md` 两处 `delegate_task` 操作指令改为 `Agent`；更正权威报告 :84 虚假 grep 断言
- 修复 P1-1：`loop --delta` 跨量规百分比换算真正实现（`diff=(b−c)/rubric_max*100`），`--rubric-max` 不再装饰性；防除零校验（P2-4）
- 修复 P1-2：selfcheck 覆盖面全面化——链接检查扫全部 md（剥离代码块、裸路径仅导航文档提取）；CRLF 内容嗅探覆盖无扩展名文件（LICENSE）；陈旧路径字符类含 `@` 与中文；孤儿判定改从 SKILL.md 做可达性 BFS（互引不再脱敏）
- 修复 P1-3：`chk_cross_count` 规则文件路径改对（references/faq.md、references/diagnostic-checklist.md）、缺失显式告警；`pat_ver` 支持中文数字；CHANGELOG 只取最新段避免历史演进误报
- 修复 P1-4：入口 `sys.stdout.reconfigure(utf-8)`，非 UTF-8 代码页不再崩溃（退出码 2 区分参数错误）
- 修复 P1-5：`closure` 改解析具名「审计分 A/自评分 B/复审分 C」字段（消除与 SkillHub 维度名冲突）、重算 B−C 并与报告结论比对、`is_file` 判据（P2-5）
- 修复 P1-6：权威报告标明量规归属（SkillHub 归一 vs skill-audit），注明 A/C 基数不同不可直接比
- 修复 P1-7：`loop` 轮次状态持久化（`~/.workbuddy/.audit_loop_state.json` 自增防忘递增）、`--max` 硬钳制 3（`--override-max` 解锁）、拒绝负轮次/负 max
- 修复 P1-8：preflight 闸 3 诚实化为「人工确认项」，不再伪装机械判定
- 新增 `selftest` 子命令：5 组变异测试（README 断链 / LICENSE CRLF / @ 幽灵路径 / 互引孤儿 / 纯孤儿），断言 selfcheck 必须检出
- 修复 P2-1：行内豁免标记 `<!-- audit-guard:ignore -->` + 软化措辞只扫主文档，清除永久误报 WARN
- 修复 P2-2：`import json` 从死导入变为实际使用（loop 状态持久化）
- 修复 P2-3：子命令计数统一为 5 个（selfcheck / preflight / loop / closure / selftest）
- 修复 P2-6：`find_skill_dir` 入口断言 is_dir，POSIX 路径误导输出消除
- 修复 P2-7：audit-report-sample 示范路径改占位符
- 修复 P2-9：frontmatter 相似度改 `difflib.SequenceMatcher`
- 修复 P2-10：软化措辞否定豁免从整行细化为句级
- 修复 P2-11：新增尾换行检查
- 修复 P2-12：版本号一致性扩为 5 处（含 CHANGELOG 标题）
- 独立复审 C（fresh 子代理，C=75/100）抓出并修复 3 项残留：
  - **孤儿 BFS 引用判定收紧**：只认路径形式（references/x.md）与 markdown 链接，裸文件名/示例文本不再把孤儿"洗白"（审计报告内变异示例文件名已改裸名）
  - **selftest 假自证修复**：变异注入改字节写入（LF helper），消除 Windows 文本模式把 README 转 CRLF 的副作用——M4/M4b 现在真自证
  - **禁用工具名检查落地**：selfcheck 新增 `chk_disallowed_tools`（delegate_task 作操作指令且无"别名/仅当/否定告诫"限定即 FAIL；CHANGELOG 与审计报告等历史记录豁免）
  - **loop 状态副作用修复**：`--delta` 纯查询不写轮次状态；新增 `--reset-state` 复位
- 版本号五处统一升至 1.2.0

## v1.1.0 (2026-08-28)

- 新增 `scripts/audit_guard.py` 硬代码保障：把预检闸 / 版本一致 / 链接完整 / 孤儿文件 / README 结构 / 跨文件计数 / frontmatter / 软化措辞 / 陈旧路径等规则变成可机械判定的退出码（零依赖，仅标准库，Windows/Unix 通用）。回应审计复测中 R(稳定性) 短板——所有约束由代码强制，而非荣誉制。
  - `selfcheck`：结构自检，有 FAIL 退出码 1
  - `preflight`：进入闭环前的预检闸（路径存在 + selfcheck 通过）
  - `loop --round N --max 3`：强制 MAX_ROUNDS 闭环上限，杜绝无界递归
  - `loop --delta B C`：B−C 有向差值规则机械判定（跨量规自动转百分比）
  - `closure --report FILE`：校验审计报告含 A/B/C 且应用差值决策（特征词已放宽，兼容「自评分 B」「优化 B」等表述，不再强求字面 `B = 数字`）
- 修复 P0-1：主调用模板与 quickstart 写死的 `delegate_task`（本环境不存在）改为 `Agent` 工具，`delegate_task` 仅作别名；faq Q2 改为「审计员工具怎么选」
- 修复 P0-2：SKILL.md 整文件 CRLF 复发，归一化为 LF（此前 v1.0.1 修过、写入 CHANGELOG，v1.0.6 静默复发）
- 修复 P1-1：预检闸「强制」名不副实 → 第 2 项改为 `audit_guard.py selfcheck` 退出码强制
- 修复 P1-2：闭环无最大轮次上限 → 新增 MAX_ROUNDS=3 硬上限
- 修复 P1-3：README 断链（LICENSE 缺失）+ 结构图失实（scripts/templates 不存在、漏 examples/等）→ 补 LICENSE、修正结构图
- 修复 P1-4：diagnostic-checklist.md 等孤儿文件 → 接入 SKILL.md 引用（selfcheck 的算法蓝本）
- 修复 P1-5：diagnostic-checklist 计数「三处」与 CHANGELOG「四处」矛盾 → 统一为四处（frontmatter/package.json/_meta.json/README）
- 修复 P2-1：frontmatter summary/description 过长且近重复 → 精简去重
- 修复 P2-2：audit-verification-report.md 陈旧双副本路径 → 加历史留痕说明
- 版本号四处（SKILL.md frontmatter / package.json / _meta.json / README）统一升至 1.1.0

## v1.0.6 (2026-08-28)

- 依据 SkillHub 新版测评报告（T 5.0 / R 4.3 / A 4.7 / C 4.7 / E 4.6）短板，实施 5 项优化（全文档改动，无代码、无安全面变化）：
  - 新增 `references/audit-report-sample.md` —— 完整可复制的 A/B/C 审计报告样例（输入上下文包→A 报告→优化 B→复审 C→差值决策）+ 自填清单，回应 C/文档质量 4.5「缺少输入输出示例」
  - 新增 `examples/quickstart-worked-example.md` —— 全填好的最小闭环（真实路径 + 真实 find 文件清单 + 占位符全填的 Agent 调用 + 兜底），回应 A/触发方式 4.5「无现成完整例子」
  - 新增 `references/score-reading-guide.md` —— B/C/A 速读指南（一句话卡片 + ASCII 决策表 + 3 个数值场景 + 常见误解表），回应 E/有效性 4.6 与 A/适用性「B·C 分数理解复杂」
  - SKILL.md「异常处理」升级为**强制预检闸**（GO/STOP 表 + 「跳过则闭环无效」硬约束），回应 R/异常处理 4.0 与运行稳定性 4.3「建议而非强制保护」
  - `references/faq.md` 顶部加**速查对照表**（何时用 vs 不用 / B·C 差值速查），Q4 改表格，回应 C/反模式与FAQ 4.7「对照表更直观」
  - SKILL.md 在调用模板 / 评分约定 / 案例研究三处接入上述新文件引用，避免文件孤立、提升结构清晰度
- 版本号四处（SKILL.md frontmatter / package.json / _meta.json / README）统一升至 1.0.6

## v1.0.5 (2026-08-27)

- 依据 SkillHub 测评报告（综合高分，子项短板：antiPatternFaq 4.0 / errorHandling 4.0 / docQuality 4.3 / stability 4.3 / boundary 4.5）优化：
  - 新增 `references/faq.md` 高频问答（何时用 vs 直接优化 / B·C 差值解读 / delegate_task 缺失兜底 / 元技能死锁 / 纯文档 skill / 工具集）—— 回应 antiPatternFaq 4.0
  - SKILL.md 新增闭环流程图（ASCII）+ 可直接复制的 `delegate_task` 调用模板 —— 回应 docQuality 4.3
  - 新增「不适用场景」显式声明章节 —— 回应 boundary 4.5
  - 新增「异常处理」段：进入前参数校验 + 「X→做Y」映射表 + 失败恢复决策树 —— 回应 errorHandling 4.0 与 stability 4.3
  - 关键章节加 `[提示]`/`[注意]`/`[警告]` 视觉层级标注 —— 回应 progressive 4.5
  - 修正版本号不一致：`package.json` 1.0.3 → 1.0.5，与 `SKILL.md`/`_meta.json` 对齐；补录缺失的 v1.0.4 条目 —— 回应 structure 4.5
- 全文件纯文档改动，无代码、无安全面变化；跨文件版本号三处统一为 1.0.5

## v1.0.4 (2026-08-26)

- 版本字段提升至 1.0.4（`SKILL.md` / `_meta.json` 对齐）
- 新增 `references/unclekk-harness-audit-v105-case.md`（unclekk-harness v1.0.5 独立审计案例）
- 注：本版 `package.json` 版本号未同步为 1.0.4（遗留瑕疵，已于 v1.0.5 修正）

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
