# UncleKK 审计长闭环优化 · Audit-then-Optimize Loop

> UncleKK 的独立审计→优化→独立复审闭环工作流，防止自评分虚高、抓住优化器漏改的残留缺陷。
>
> UncleKK's independent-audit → optimize → independent re-audit loop: prevents self-score inflation and catches residual bugs the optimizer misses.

UncleKK 的独立审计→优化→独立复审闭环工作流。防止自评分虚高，抓住优化器漏改的残留缺陷。

UncleKK's independent-audit → optimize → independent re-audit loop. It prevents self-score inflation and catches residual defects that the optimizer failed to fix.

## 安装 Installation

将此技能克隆到你的 WorkBuddy 技能目录：
Clone this skill into your WorkBuddy skills directory:

```bash
git clone https://github.com/KKWong3614/unclekk-audit-then-optimize.git "$HOME/.workbuddy/skills/unclekk-audit-then-optimize"
```

或下载 Release 中的 zip，解压到技能目录即可。
Or download the zip from the Release and extract it into your skills directory.

## 目录结构 Directory Structure

```
unclekk-audit-then-optimize/
├── SKILL.md      # 技能主文件（含 frontmatter）
├── README.md     # 本文件
├── LICENSE       # MIT 许可证
├── references/   # 参考文档（如有）
├── scripts/      # 可执行脚本（如有）
└── templates/    # 模板（如有）
```

## 版本 Version

当前版本：`1.0.3`
Current version: `1.0.3`

## 许可证 License

[MIT](LICENSE) © 2026 KK大叔 (UncleKK)
