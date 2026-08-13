# 独立审计长 subagent 超时与部分改动存活

**场景**：主 Hermes 派发独立第三方 audit/optimization subagent（`role=leaf`），subagent 在 600s 超时前未产出完整报告但已落地代码改动。

**来源**：unclekk-harness 2026-07-30 两轮独立第三方（deleg_34b30bbe 审计 / deleg_d42c48ec 优化），均超时（518s 与 600s，API 慢）。

## 关键事实

1. **超时 ≠ 无用**。subagent 可能已修改文件并跑过测试，超时只说明"没来得及输出最终报告"。
2. **主 Hermes 绝不能因为超时就回滚改动**。应先验证回归。
3. **主 Hermes 绝不能因为超时就再派一遍**。重复 dispatch 等于对已落地的改动做未知数量的叠加修改。

## 主 Hermes 收到超时通知后的标准处理

1. 跑回归：`PYTHONHOME="" python scripts/test_harness.py -v`
   → 测试全通过：改动是安全的（subagent 自己验证过）
   → 测试失败：用 diff 找新增/修改的函数，人工定位半截改动，补完或回滚

2. 用 diff 核查改动范围：
   `diff "/d/upstream/harness.py" "/d/skill待检/harness.py" | head`
   → 只有一两个 hunk：增量改动，安全
   → 整个文件重写（1,1011c1,1058 模式）：subagent 可能用 Python 重写了整个文件，需逐函数核查

3. 用 AST 提取函数签名比对：
   `re.findall(r'^(\s*)def (\w+)\(', text, re.M)`
   比较 upstream 函数集合 vs 待检函数集合
   → 只增不删：安全
   → 有删除：核查删除的函数是否被新 helper 覆盖

4. 若改动安全 + 测试通过：同步到上游 + 对上游再跑一遍回归 + 主 Hermes 补 subagent 因超时未完成的测试

5. 若改动不安全（测试失败 / 函数被删 / 语法错误）：回滚到上游版本 + 重新 dispatch（timeout 设更高如 900s，或 split 成多个小任务）

## 已知超时场景 & 对应策略

| 超时原因 | 现象 | 策略 |
|----------|------|------|
| API 慢 | api_calls 少（<25），600s 超时 | 增大 timeout 或 split 成多个 subagent |
| subagent 陷入死循环 | api_calls 多（>100），600s 超时 | 立即回滚，重新 dispatch 并加"每 5 次 call 检查进度" |
| subagent 重写大文件 | 一个 1000+ 行文件的 Python 重写，超时在写完后 | 核查 diff，通常改动已存活 |

## 与现有铁律的交互

- "主 Agent 收到报告后必须独立验证" — 超时场景是这条铁律的**边界 case**：没有报告，但改动存在。验证对象从"审计报告"转为"代码 + 回归"。
- "主 Agent 不预读" — 超时场景无报告可读，但 main 仍要**不预读改动细节**，用工具客观核查（diff + AST + test），与"不预读"精神一致。

## 案例

- deleg_34b30bbe（审计）：518s/11 calls，超时前产出完整报告，主 Hermes 抽验 3 项关键发现全部确认。
- deleg_d42c48ec（优化）：600s/21 calls，超时前落地 5 个 helper（`_atomic_write_path`、`_new_subtask`、`_resp_ok`、`_resp_error`、`_respond_and_exit`），43/43 回归通过，0 函数删除。主 Hermes 同步到上游并确认上游 43/43。

## 环境已知坑（PYTHONHOME 与 NTFS）

- 宿主机 uv 管理 Python 3.11 与系统 Python 3.12 存在 `SRE module mismatch`，导致 `import re` / `skillhub` CLI 崩溃。**必须用 `PYTHONHOME=""` 前缀**让 Python 解析到系统 3.12。
- NTFS 卷（如 `D:/`）大小写不敏感，`SKILL.md` 与 `skill.md` 被折叠成同一文件。这是文件系统特性，不是 bug——但 SkillHub 要求同时存在 skill.md（描述）和 SKILL.md/package.json（元数据），大小写折叠会破坏发布结构。变通：只满足其一（package.json 已覆盖元数据）。