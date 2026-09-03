# 触顶确认后的死代码激活（Ceiling-Confirmed Dead-Code Remediation）

触顶（ceiling confirmed）之后，工作没有结束。独立审计长 L0-L5 扫描经常发现**死代码**——功能被文档声称、测试覆盖、但 CLI 到执行路径从未接通。

这类修复**不**属于新一轮 hill-climbing（不触发触顶规则重置），因为分数不变、无新测试增量（只是验证现有测试），但它是真 bug，必须修。

## 识别信号

- 审计长 L0-L5 扫描发现某个代码路径在 grep 中**有定义但无调用方**
- 文档/模板声称某功能可用，但 CLI 上无法激活
- 某个 recovery/safety 机制的函数签名带 `recover=True` 等参数，但所有调用方都传 False
- 测试结果说"覆盖到了"，但实际是通过 `_load(recover=True)` 等直接调用测试的，不是通过 CLI

## unclekk-harness 案例（2026-07-27，第 4 轮独立审计 · v1.0.4-remediation 阶段）

| 信号 | 事实 |
|------|------|
| 函数签名 | `_load(path, recover=False)`，L105/L113/L117/L121 四处分发 `recover=True` 路径 |
| 无调用方 | 所有 stage_* 函数（stage_ingest/plan/exec/complete/error/review/audit/settle/status）调用 `_load()` 时都传 `recover=False` 或根本不传参数 |
| CLI 无 flag | argparse 中没有 `--recover`，`main()` 没有 `args.recover` |
| 文档声称 | evolution-log.md 写"状态损坏可恢复"作为能力，失败模式表 #8 |
| 测试假阳性 | 直接调用 `_recover_state_from_log(path, raw)` 测了恢复路径，但 CLI 上完全没接通 |

**修复（14 个 patch，全部落盘）：**
1. `--recover` flag 注入所有 stage 命令的 argparse（L910）
2. 所有 `stage_*` 函数签名加 `recover=False, **_kw` 透传
3. `stage_exec` JSONDecodeError/ValueError handler 调 `_recover_state_from_log` 并设 `state["stage"]="exec"`（L513-517）
4. `main()` dispatch 层 `stage_exec(args.state, recover=args.recover)`（L958）
5. +4 测试（37/37 全绿）

**分数**：48.72 → 48.72（不变，不计入 hill-climbing）
**版本**：v1.0.4-remediation（remediation 后缀表示触顶后修复）

## 工作模式

```
独立审计长 L0-L5
  → 发现死代码（有定义无调用方）
  → 主 Agent 独立验证（grep 确认无调用方、测试通过）
  → 主 Agent 直接修复（不需要再派一轮审计长）
  → 修复后追加 results.tsv 条目（new_score = old_score，status=applied）
  → 追加 evolution-log.md remediation 章节
```

## 主 Agent 验证清单

1. **grep 确认**：`grep -n "recover" harness.py` 确认 `recover=True` 路径有定义
2. **调用方确认**：`grep -n "_load(" harness.py` 确认所有调用方都传 `False` 或不传
3. **CLI 确认**：`grep -n "recover" harness.py | grep -E "add_argument|args.recover"` 确认 flag 注册
4. **测试**：37/37 全绿

## 经验教训

- **测试假阳性**：直接调用内部函数测试 ≠ 该功能可被用户激活。CLI 路径必须测试。
- **审计长超时但 patch 已落盘**：600s 超时不等于没有产出——读 transcript 看最后 20 个 API call，确认 patch 状态。超时前的 patch 多数已经写入文件。
- **remediation 后缀**：version 用 `-remediation`（如 `v1.0.4-remediation`），表示"触顶后修复，分数不变"。
- **results.tsv new_score = old_score**：死代码修复不改变评分，新分等于旧分，这是棘轮规则允许的状态（不逆推）。
