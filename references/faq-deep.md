# 深度 FAQ — Edge Cases, Tooling & Troubleshooting

> 主 FAQ（`faq.md`）解决"要不要走闭环、怎么走、分数怎么读"；本文件处理**边缘场景 / 工具兼容 / 安全合规 / 脚本故障**——用户踩到具体问题时先查这里。
>
> Deep FAQ for edge cases, tool compatibility, security/compliance and script troubleshooting. Consult this file when you hit a concrete problem.

---

## QD1：多个 skill 要同时审计，能批量吗？

**A：** 可以顺序批量：对每个 skill 跑 `audit_guard.py selfcheck --target <DIR>`（逐个目录），但独立审计（fresh 子代理）**不要**并行派发到同一上下文——并行子代理会互相干扰"fresh"语义。推荐逐个闭环、逐个收口，避免审计员上下文串味。若追求吞吐，可让每个闭环用独立的子代理 ID。

---

## QD2：目标 skill 在远程 / 别的机器上，怎么审计？

**A：** 先同步到本地技能目录（git clone / rsync / 压缩传输），再走闭环。远程目录不能直接作为 `--target`。审计员只认本地绝对路径；远程审计先拉取，审计完按需回传。不要试图在审计器里做远程文件操作（leaf 代理只有 file + terminal 且无网络感知保证）。

---

## QD3：审计报告（A/B/C）丢了，能重新生成吗？

**A：** 不能原样重建——审计是 fresh 上下文的独立过程，报告是其一次性产出。但可以：
1. 用 `references/audit-report-sample.md` 模板 + 保留的「先前发现」重新派发一轮审计（相当于新一轮 A，不是找回旧 C）；
2. 若报告未丢但缺具名字段，`closure` 会明确报"需审计分 A / 自评分 B / 复审分 C 具名字段"，按提示补字段即可通过校验。
3. 养成习惯：闭环报告落盘为 `references/audit-<skill>-<日期>.md` 并接入 SKILL.md 引用（避免孤儿）。

---

## QD4：B 和 C 用的量规不同（/100 vs /90），差值怎么比？

**A：** 用 `loop --delta B C --rubric-max <量规>` 机械判定，脚本把差值**转成相对百分比**：`diff = (b−c)/rubric_max*100`，阈值 3（百分点）。例：/90 量规 B=80 C=77 → +3.33 百分点 > 3 → 判虚高。**不要**拿不同量规的原始分直接作差。

---

## QD5：审计员发现了 P0，但优化器不认同，听谁的？

**A：** 不自动采信任何一方——按「差值规则」+ 主代理核对：
1. 若这是复审 C 的发现，B−C 差值判定已经给出方向（虚高以 C 为准 / C−B 大则重核实 C）；
2. 主代理用**可复现证据**裁决：让 C 给出 文件:行号 + 命令输出，实测验证（本技能铁律：所有"计数/缺失/存在"类声称必须实测，不采信口头结论）；
3. 证据不足的 P0 降级为 P1/P2 观察项，不阻断。

---

## QD6：selftest 失败，怎么排查？

**A：** `selftest` 报告哪组变异漏检（M1 断链 / M2 LICENSE CRLF / M3 @ 幽灵路径 / M4 互引孤儿 / M4b 纯孤儿），按表对治：
- **M1**：`chk_link_integrity` 没扫到全部 md / 代码块剥离异常 → 检查扫描逻辑与正则
- **M2**：`iter_text_files` 没覆盖无扩展名文件（内容嗅探被 NUL 判定跳过）→ 检查文本探测
- **M3**：`chk_stale_paths` 字符类缺 `@` / 中文 → 检查路径正则
- **M4/M4b**：孤儿 BFS 引用判定过宽（裸文件名被算引用）→ 检查 `refs_of` 信号
- 若全 FAIL 但 expect 全 PASS，多半是临时副本污染（Windows 文本模式 CRLF）→ 用字节写入重测

---

## QD7：轮次状态文件（~/.workbuddy/.audit_loop_state.json）误删/损坏，闭环还能跑吗？

**A：** 能。状态文件只是"防忘记递增"的辅助：删掉后 `loop --round N --max 3` 退化为显式传入轮次（等价 `--no-state`）。想重置：`loop --round 1 --max 3 --target <DIR> --reset-state`。状态损坏时脚本会静默忽略（`load_loop_state` 异常兜底），不会阻断闭环。

---

## QD8：技能目录里混入二进制 / 大文件，selfcheck 会卡或误报吗？

**A：** 不会误报：`iter_text_files` 对无扩展名/未知后缀做**内容嗅探**（前 8KB 含 NUL 判为二进制跳过），二进制文件不进行尾/扫描。大文件会拖慢扫描（逐个 read_bytes），建议审计前排除 `__pycache__` / `.git` / node_modules 等（脚本已默认跳过 `__pycache__`；`.git` 请在复制审计副本时排除）。

---

## QD9：把技能分享给别人，需要带哪些文件？

**A：** 最小可分享集：
- `SKILL.md`（主文件）、`README.md`、`LICENSE`、`CHANGELOG.md`、`package.json`、`_meta.json`
- `scripts/audit_guard.py`（硬代码保障，无它则预检闸 2 无法机械判定）
- `references/` 全部 + `examples/` 全部（引用完整性：SKILL.md 引用了它们，缺失会触发断链 FAIL）
- 分享前必跑：`selfcheck` + `selftest` + `preflight`（退出码全 0 才允许发布）

---

## QD10：审计中发现目标 skill 含硬编码凭据/密钥，怎么处理？

**A：** 这是 P0 级发现，按安全流程处理：
1. 审计员**只报告不处置**（toolsets 只读，不得改文件）；
2. 主代理立即：删除/轮换凭据 → 检查是否已提交到版本库历史 → 更新技能文档；
3. 若凭据已外泄（公网仓库），按平台泄露流程处理（撤销密钥、联系平台）；
4. 后续审计用脱敏副本（凭据占位符替换），不要在审计上下文包里传真实密钥。
5. 本技能自身不存储任何数据（见 SKILL.md「数据与隐私」）。

---

## QD11：Windows 原生路径 / Git Bash POSIX 路径混用会怎样？

**A：** `audit_guard.py --target` 只认**可解析的本地路径**：
- Windows 原生：`C:/Users/...` 或 `C:\Users\...` → 正常
- Git Bash POSIX：`/c/Users/...` → `Path.resolve()` 会解析成 `C:\c\Users\...`（不存在）→ `find_skill_dir` 入口断言 is_dir 会报错退出（退出码 2）
- 正确做法：POSIX 路径先 `cygpath -m` 转成 `C:/...` 再传
- 文档/示例里的路径一律用 `C:/...` 原生形式（`examples/quickstart-worked-example.md` 已示范）

---

## QD12：审计员超时但产出已落盘，怎么恢复？

**A：** 见 `references/subagent-timeout-partial-landing.md` 完整流程。要点：
1. 读子代理 transcript 的最后 20 个 API 调用，确认哪些 patch/发现已落地；
2. 保留已落地的 diff/发现，只重跑未完成的审计项（不要整轮重来）；
3. 超时前的产出多数已写入文件——超时不等于零产出。

---

## QD13：闭环报告怎么写才能通过 closure 校验？

**A：** `closure` 要求**具名字段**（消除与 SkillHub 五维 A/C 维度名的歧义）：
- 必含：`审计分 A = <数字>`、`自评分 B = <数字>`、`复审分 C = <数字>`（行内任意位置均可）
- 必含差值结论文字（"虚高 / 以 C 为准" 或 "重核实 C" 等）
- 脚本会**重算 B−C** 并与结论比对，结论与规则矛盾会 FAIL
- 对照样例：`references/audit-unclekk-audit-then-optimize-2026-08-28.md`（closure 校验通过的真实样本）

---

## QD14：这套方法论能用于非 skill 对象（代码/文档/方案）吗？

**A：** 不能直接套用，但思想可迁移：
- **❌** 评测普通代码/产品文档/PPT → 用对应领域的评审工具（本技能只审 skill）
- **✅** 但"独立第三方审计 → 优化 → 独立复审"的**防自评偏差**模式，适用于任何会产生"自我评分"的优化流程（策略方案、代码重构等），只是量规要换
- 边界以 SKILL.md「能力边界总览」为准：❌ 超范围项不承接
