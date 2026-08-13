# unclekk-darwin-evolver 独立审计案例（2026-07-23）

## 背景

unclekk-darwin-evolver 是 unclekk 的达尔文进化优化 skill。在一次优化迭代中，优化器自评 86/100，
但独立第三方审计只给 82/100，还发现了 4 个优化器漏掉的缺陷。

这是"自评分虚高"（self-score inflation）的经典案例：优化器知道自己改了啥 → 认为改对了；
独立审计长用全新上下文读文件 → 发现残留问题。

## Round 1: 独立审计

- 评分：68/100
- 缺陷：3×P0 + 5×P1 + 8×P2
- 审计方式：独立 leaf subagent，fresh context

## 优化阶段

- 优化器：Darwin 进化策略
- 自评：86/100
- API 调用：50+ 次，触达 iteration limit
- 核心问题：优化器基于"知道自己改了啥"的乐观偏差，漏改多处

## Round 2: 独立复审计

- 评分：82/100
- 耗时：8 API 调用，304 秒
- 发现 4 个优化器漏掉的缺陷：
  - P1-新1: 触顶判定算法与进化实例矛盾（P0-3 深层残余）
  - P2-新1: references/"failure-modes.md" 计数残留（10 类 vs 11 类）
  - P2-新3: results.tsv dimension 字段 = -
  - P2-新4: results-tsv-template.md SHA 示例含非法字符

## 关键洞见

1. **自评分普遍虚高**：优化器 86 vs 独立审计 82，delta = 4（>3 阈值），确认为膨胀。
2. **独立审计成本远低于优化器**：8 次 API 调用 vs 50+ 次，效率约 6 倍。
3. **P0-3 深层残余**：触顶判定算法与进化实例矛盾——算法层面未修，只改了表述。
4. **Cross-file 计数漂移**：SKILL.md 说 10 类失败模式，references 文件实际 11 类。

## 与本 Skill 的关系

此案例直接催生了 `unclekk-audit-then-optimize` 的三步法：
- 独立审计（score A）
- 优化（self-score B）
- 独立复审计（score C）
- B 与 C 比较，delta > 3 即怀疑自评分虚高

详见 SKILL.md "The Loop" 和 `references/independent-auditor-multiround-loop.md`。

## 数据出处

- 原始审计日志：unclekk-darwin-evolver skill 的 results.tsv 与 evolution-log.md
- 独立审计长报告：delegated leaf subagent 产出
- 主 Agent 独立验证：diff + AST 函数签名比对 + 回归测试