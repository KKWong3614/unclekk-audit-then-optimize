#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_guard.py — unclekk-audit-then-optimize 的「硬代码保障」(v1.2.0)

把方法论里靠人自觉执行的规则，变成可机械判定的退出码。
零依赖（仅标准库），Windows / Unix 通用（输出已强制 UTF-8，非 UTF-8 代码页不崩）。

子命令
======
  selfcheck   结构完整性自检（行尾 / 版本一致 5 处 / 链接完整 / 孤儿文件(可达性 BFS) /
              README 结构 diff / 跨文件计数 / frontmatter 体检 / 软化措辞 /
              陈旧路径 / 尾换行）。有 FAIL 则退出码 1。
  preflight   进入审计闭环前的预检闸（路径存在 + selfcheck 通过；闸 3 为人工确认项）。
  loop        闭环状态机：强制 MAX_ROUNDS 上限（状态自增防忘记递增、--max 硬钳制）
              + B−C 有向差值规则（跨量规转百分比）。
  closure     校验审计报告含具名「审计分 A / 自评分 B / 复审分 C」字段，
              重算差值并与报告结论比对。
  selftest    变异测试：在临时副本注入缺陷（断链 / LICENSE CRLF / @ 幽灵路径 /
              互引孤儿 / 纯孤儿），断言 selfcheck 必须检出。任一漏检退出码 1。

典型用法
========
  # 审计本技能自身（脚本在 <skill>/scripts/ 下，自动定位上级为技能目录）
  python scripts/audit_guard.py selfcheck
  python scripts/audit_guard.py selftest

  # 审计任意目标技能
  python scripts/audit_guard.py selfcheck --target /path/to/target-skill

  # 预检闸（闭环第 0 步）
  python scripts/audit_guard.py preflight --target /path/to/target-skill

  # 闭环轮次与差值（--delta 支持跨量规自动转百分比）
  python scripts/audit_guard.py loop --round 2 --max 3
  python scripts/audit_guard.py loop --delta 87 82 --rubric-max 100
  python scripts/audit_guard.py loop --delta 80 77 --rubric-max 90

  # 报告完整性校验
  python scripts/audit_guard.py closure --report references/audit-x-2026.md
"""

import argparse
import contextlib
import datetime
import difflib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ── 文本文件类型（用于行尾 / 扫描）─────────────────────────────
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini"}
# 无扩展名 / 常见脚本数据文件也纳入行尾扫描（内容嗅探判定文本，P1-2 修复 M2）
SNIFF_SUFFIXES = {"", ".sh", ".tsv", ".csv", ".gitattributes", ".gitignore", ".license"}

# 软化措辞（diagnostic-checklist.md P2 项）
SOFT_PHRASES = ["建议", "可以考虑", "根据情况", "灵活把握", "视情况而定", "酌情", "必要时"]

# 陈旧绝对路径前缀（命中后逐个 exists 校验）
STALE_PATH_PREFIXES = (r"D:/", r"C:/Users/", r"C:\\Users\\", r"/home/", r"/Users/")

# 行内豁免标记：命中该标记的行跳过「跨文件计数 / 陈旧路径 / 软化措辞」检查（P2-1 修复）
IGNORE_MARK = "<!-- audit-guard:ignore -->"

# 中文数字 → 整数（P1-3 修复：版本号 N 处常用中文数字书写）
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

# loop 状态持久化文件（用户级，跨会话自增轮次，P1-7 修复）
DEFAULT_STATE = Path.home() / ".workbuddy" / ".audit_loop_state.json"


# ── 结果模型 ──────────────────────────────────────────────────
class Check:
    def __init__(self, name, status, detail=""):
        self.name = name
        self.status = status  # PASS / WARN / FAIL
        self.detail = detail

    def __str__(self):
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(self.status, "?")
        return f"  {icon} [{self.status}] {self.name}" + (f" — {self.detail}" if self.detail else "")


def find_skill_dir(explicit=None):
    """定位技能目录；显式路径必须真实存在，否则退出码 2（P2-6 修复）。"""
    if explicit:
        p = Path(explicit).resolve()
        if not p.is_dir():
            print(f"❌ 目标不存在或不是目录: {explicit}")
            print("   提示：Windows 下请用原生路径（C:/...）或先 cygpath -m 转换。")
            sys.exit(2)
        return p
    # 脚本位于 <skill>/scripts/audit_guard.py → 上级目录即技能目录
    here = Path(__file__).resolve().parent
    return here.parent


def iter_text_files(skill_dir):
    """遍历文本文件：后缀白名单直接纳入；无扩展名/脚本数据文件做内容嗅探（前 8KB 无 NUL 即文本）。"""
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        if p.suffix.lower() in TEXT_SUFFIXES:
            yield p
        elif p.suffix.lower() in SNIFF_SUFFIXES:
            try:
                head = p.read_bytes()[:8192]
            except Exception:
                continue
            if b"\x00" not in head:
                yield p


# ── 各检查项 ──────────────────────────────────────────────────
def chk_line_endings(skill_dir):
    """P0-2 回归拦截：任何文本文件含 CR 即 FAIL（含无扩展名文件如 LICENSE，P1-2 修复 M2）。"""
    bad = []
    for p in iter_text_files(skill_dir):
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if b"\r" in data:
            bad.append(str(p.relative_to(skill_dir)))
    if bad:
        return Check("行尾一致性 (CRLF)", "FAIL", "含 CR 的文件: " + ", ".join(bad))
    return Check("行尾一致性 (CRLF)", "PASS", "全目录 LF")


def extract_version(path, regex):
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = re.search(regex, text, re.MULTILINE)
    return m.group(1) if m else None


def chk_version_consistency(skill_dir):
    """版本号五处（SKILL.md frontmatter / package.json / _meta.json / README / CHANGELOG 标题）一致。"""
    versions = {
        "SKILL.md frontmatter": extract_version(skill_dir / "SKILL.md", r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)"),
        "package.json": extract_version(skill_dir / "package.json", r'"version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"'),
        "_meta.json": extract_version(skill_dir / "_meta.json", r'"version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"'),
        "README.md": extract_version(skill_dir / "README.md", r"当前版本[：:]\s*`?([0-9]+\.[0-9]+\.[0-9]+)"),
        "CHANGELOG.md": extract_version(skill_dir / "CHANGELOG.md", r"^##\s*v([0-9]+\.[0-9]+\.[0-9]+)"),
    }
    found = {k: v for k, v in versions.items() if v}
    distinct = set(found.values())
    if len(distinct) <= 1 and found:
        return Check("版本号一致性 (5 处)", "PASS", "全部 = " + next(iter(distinct)))
    missing = [k for k, v in versions.items() if not v]
    detail = "不一致: " + ", ".join(f"{k}={v}" for k, v in found.items())
    if missing:
        detail += " | 未检出: " + ", ".join(missing)
    return Check("版本号一致性 (5 处)", "FAIL", detail)


def chk_link_integrity(skill_dir):
    """内部链接完整性：遍历全部 *.md（含 README/references/examples）。
    剥离代码块（示例/伪代码不算引用）；markdown 链接 ](path) 全部校验；
    裸路径 references//examples//scripts/ 仅从导航文档（SKILL.md/README.md）提取，
    避免把案例/审计报告里的他技能路径误判为断链。支持无扩展名目标（LICENSE）。"""
    md_files = list(skill_dir.rglob("*.md"))
    refs = set()
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        text = re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.DOTALL)  # 剥离代码块（示例不算引用）
        refs |= set(re.findall(r"\]\(([A-Za-z0-9_\-./]+\.(?:md|py))\)", text))
        refs |= set(re.findall(r"\]\((LICEN[SC]E)\)", text))
        if md.name in ("SKILL.md", "README.md"):
            refs |= set(re.findall(r"(references/[A-Za-z0-9_\-\.]+\.md|examples/[A-Za-z0-9_\-\.]+\.md|scripts/[A-Za-z0-9_\-\.]+\.py)", text))
    missing = []
    for r in sorted(refs):
        if not (skill_dir / r).exists():
            missing.append(r)
    if missing:
        return Check("链接完整性", "FAIL", "缺失目标: " + ", ".join(missing))
    return Check("链接完整性", "PASS", f"{len(refs)} 个内部引用全部存在（扫 {len(md_files)} 个 md）")


def chk_orphans(skill_dir):
    """孤儿文件检测（可达性 BFS，P1-2 修复 M4）：从 SKILL.md 出发，沿
    「文件名出现在文本中」的引用图遍历；references/examples 下 .md 若不在
    可达集合中 → FAIL。互引但未被 SKILL.md 可达的也算孤儿。"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return Check("孤儿文件检测", "WARN", "SKILL.md 缺失，无法计算可达性")
    all_md = [p for p in skill_dir.rglob("*.md")]
    by_name = {}
    for p in all_md:
        by_name.setdefault(p.name, []).append(p)
    texts = {}
    for p in all_md:
        try:
            texts[p.resolve()] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            texts[p.resolve()] = ""

    def refs_of(p):
        """引用信号只认两种：路径形式（references/x.md、examples/x.md）与 markdown 链接 ](x.md)。
        裸文件名（如审计报告里描述变异测试的 orphan-a.md）不算引用——避免示例文本把孤儿"洗白"（C 复审 P0）。"""
        out = set()
        t = texts.get(p.resolve(), "")
        for m in re.finditer(r"(?:references|examples)/[A-Za-z0-9_\-\.]+\.md", t):
            for q in by_name.get(m.group(0).split("/")[-1], []):
                if q.resolve() != p.resolve():
                    out.add(q.resolve())
        for m in re.finditer(r"\]\(([A-Za-z0-9_\-./]+\.md)\)", t):
            for q in by_name.get(m.group(1).split("/")[-1], []):
                if q.resolve() != p.resolve():
                    out.add(q.resolve())
        return out

    start = skill_md.resolve()
    visited, stack = {start}, [start]
    while stack:
        cur = stack.pop()
        for nxt in refs_of(cur):
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    orphans = []
    for sub in ("references", "examples"):
        d = skill_dir / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.resolve() not in visited:
                orphans.append(f"{sub}/{f.name}")
    if orphans:
        return Check("孤儿文件检测", "FAIL", "SKILL.md 不可达: " + ", ".join(orphans))
    return Check("孤儿文件检测", "PASS", f"无孤儿文件（{len(visited)} 个 md 可达）")


def _readme_structure_block(text):
    """只抓「目录结构 / Directory Structure」专节的代码块；没有则退回首个代码块。"""
    m = re.search(r"目录结构\s*Directory Structure\s*\n+```[^\n]*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    return blocks[0] if blocks else ""


def chk_readme_structure(skill_dir):
    """README 结构图 ↔ 真实目录 双向 diff。"""
    readme = skill_dir / "README.md"
    if not readme.exists():
        return Check("README 结构 ↔ 目录", "WARN", "README 缺失")
    text = readme.read_text(encoding="utf-8", errors="ignore")
    block = _readme_structure_block(text)
    listed = set()
    for line in block.splitlines():
        s = re.sub(r"^[├└│─\s]+", "", line.strip())  # 去树形字符
        if not s:
            continue
        tok = (s.split()[0] if s.split() else "").rstrip("/#").strip()
        if tok and (("." in tok) or tok.endswith("/") or tok in ("references", "examples", "scripts", "templates", "LICENSE", "LICENCE", "Makefile", "Dockerfile", "CHANGELOG")):
            listed.add(tok.split("/")[0])
    real_top = {p.name for p in skill_dir.iterdir()}
    only_in_readme = sorted(listed - real_top)   # 图中有但磁盘无 → 断链 FAIL
    only_in_dir = sorted(real_top - listed)       # 磁盘有但图无 → 信息缺失 WARN
    msgs = []
    if only_in_readme:
        msgs.append("图中有但磁盘无: " + ", ".join(only_in_readme))
    if only_in_dir:
        msgs.append("磁盘有但图无: " + ", ".join(only_in_dir))
    if msgs:
        status = "FAIL" if only_in_readme else "WARN"
        return Check("README 结构 ↔ 目录", status, " | ".join(msgs))
    return Check("README 结构 ↔ 目录", "PASS", "结构图与目录一致")


def cn_to_int(s):
    """阿拉伯或中文数字 → 整数；无法解析返回 None。"""
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if len(s) == 2 and s[0] in CN_NUM and s[1] == "十":
        return CN_NUM[s[0]] * 10
    if len(s) == 2 and s[0] == "十" and s[1] in CN_NUM:
        return 10 + CN_NUM[s[1]]
    if len(s) == 3 and s[0] in CN_NUM and s[1] == "十" and s[2] in CN_NUM:
        return CN_NUM[s[0]] * 10 + CN_NUM[s[2]]
    return None


def _rule_text(p, name):
    """读取规则文件文本；CHANGELOG 只取最新版本段（历史条目是演进记录，不参与当前一致性检查）。"""
    text = p.read_text(encoding="utf-8", errors="ignore")
    if name == "CHANGELOG.md":
        m = re.search(r"##\s*v[0-9]+\.[0-9]+\.[0-9]+.*?(?=\n##\s*v[0-9]+\.[0-9]+\.[0-9]+|\Z)", text, re.DOTALL)
        if m:
            text = m.group(0)
    return text


def chk_cross_count(skill_dir):
    """跨文件计数一致性：只扫「规则文件」（P1-3 修复：faq/diagnostic-checklist 路径改到 references/），
    专查版本号 N 处（支持中文数字）+ 强信号计数名词同键多值 → WARN；
    规则文件缺失时显式告警而非静默跳过。支持行内豁免标记。"""
    rule_files = ["SKILL.md", "README.md", "CHANGELOG.md", "references/faq.md", "references/diagnostic-checklist.md"]
    missing_rules = [name for name in rule_files if not (skill_dir / name).exists()]
    # 专查：版本号 N 处
    ver_count = {}
    pat_ver = re.compile(r"版本号\s*([0-9]+|[一二三四五六七八九十]+)\s*处")
    for name in rule_files:
        p = skill_dir / name
        if not p.exists():
            continue
        for line in _rule_text(p, name).splitlines():
            if IGNORE_MARK in line:
                continue
            for m in pat_ver.finditer(line):
                n = cn_to_int(m.group(1))
                if n is not None:
                    ver_count.setdefault(n, []).append(name)
    issues = []
    if len(ver_count) > 1:
        desc = ", ".join(f"{k}处({', '.join(fs)})" for k, fs in ver_count.items())
        issues.append(f"版本号处数冲突: {desc}")
    # 通用：强信号计数名词
    pat = re.compile(r"(\d+)\s*(类|种|categories|types)")
    groups = {}
    for name in rule_files:
        p = skill_dir / name
        if not p.exists():
            continue
        for line in _rule_text(p, name).splitlines():
            if IGNORE_MARK in line:
                continue
            for m in pat.finditer(line):
                groups.setdefault(m.group(2), {}).setdefault(m.group(1), []).append(name)
    for key, vals in groups.items():
        if len(vals) > 1:
            desc = ", ".join(f"{v}({', '.join(fs)})" for v, fs in vals.items())
            issues.append(f"「{key}」多值: {desc}")
    if missing_rules:
        issues.append("规则文件缺失: " + ", ".join(missing_rules))
    if issues:
        return Check("跨文件计数一致性", "WARN", " | ".join(issues[:5]))
    return Check("跨文件计数一致性", "PASS", "无冲突")


def chk_frontmatter(skill_dir):
    """frontmatter 体检：description/summary 长度 + 相似度。"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return Check("frontmatter 体检", "WARN", "SKILL.md 缺失")
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return Check("frontmatter 体检", "WARN", "无 frontmatter")
    fm = m.group(1)
    summary = extract_version_field(fm, r"summary:\s*(.+)$")
    description = extract_version_field(fm, r"description:\s*(.+)$")
    warns = []
    if summary and len(summary) > 120:
        warns.append(f"summary {len(summary)} 字符(>120)")
    if description and len(description) > 120:
        warns.append(f"description {len(description)} 字符(>120)")
    if summary and description:
        sim = _similarity(summary, description)
        if sim > 0.8:
            warns.append(f"summary/description 相似度 {sim:.2f}(>0.8)")
    if warns:
        return Check("frontmatter 体检", "WARN", " | ".join(warns))
    return Check("frontmatter 体检", "PASS", "字段长度/相似度正常")


def extract_version_field(fm, regex):
    m = re.search(regex, fm, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else None


def _similarity(a, b):
    """P2-9 修复：difflib.SequenceMatcher 对中文近义改写有判别力。"""
    return difflib.SequenceMatcher(None, a, b).ratio()


def chk_soft_phrases(skill_dir):
    """软化措辞计数（diagnostic-checklist P2 项）。句级豁免否定句（P2-10 修复），
    支持行内豁免标记。排除清单自身的定义文件。"""
    NEG = ["不是", "并非", "避免", "不要", "切勿", "拒绝", "不推荐", "不应", "不是建议"]
    count = 0
    hits = {}
    # 只扫方法论主文档（SKILL.md/README.md）；references 叙事案例中"建议"是正常表达，不计数
    for name in ("SKILL.md", "README.md"):
        p = skill_dir / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if IGNORE_MARK in line:
                continue
            # 按句读切分，逐句判断 NEG，避免整行豁免过粗
            for clause in re.split(r"[。！？；;]", line):
                if any(n in clause for n in NEG):
                    continue
                for ph in SOFT_PHRASES:
                    c = clause.count(ph)
                    if c:
                        hits[ph] = hits.get(ph, 0) + c
                        count += c
    if count >= 3:
        return Check("软化措辞计数", "WARN", f"共 {count} 处: " + ", ".join(f"{k}×{v}" for k, v in hits.items()))
    return Check("软化措辞计数", "PASS", f"{count} 处（<3）")


def chk_stale_paths(skill_dir):
    """陈旧绝对路径探测（P2-2）。P1-2 修复 M3：字符类含 @ 与中文（本生态路径含 @user_xxx）；
    排除 references/ 案例与 CHANGELOG 历史记录；支持行内豁免标记。"""
    bad = []
    for p in iter_text_files(skill_dir):
        if p.suffix != ".md":
            continue
        if "references" in p.parts or p.name == "CHANGELOG.md":
            continue  # 案例研究/历史记录里的路径不计为失效指令
        text = p.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if IGNORE_MARK in line:
                continue
            for pre in STALE_PATH_PREFIXES:
                for m in re.finditer(pre + r"[A-Za-z0-9_@./\\\-\u4e00-\u9fff]+", line):
                    path = m.group(0).rstrip(".,;:，。；：\"'()")
                    if not os.path.exists(path):
                        bad.append(path)
    bad = sorted(set(bad))
    if bad:
        return Check("陈旧路径探测", "WARN", "不存在的绝对路径: " + ", ".join(bad[:5]))
    return Check("陈旧路径探测", "PASS", "无失效绝对路径")


def chk_trailing_newline(skill_dir):
    """P2-11 修复：文本文件应以换行结尾（POSIX 规范）。"""
    bad = []
    for p in iter_text_files(skill_dir):
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if data and not data.endswith(b"\n"):
            bad.append(str(p.relative_to(skill_dir)))
    if bad:
        return Check("尾换行检查", "WARN", "缺尾换行: " + ", ".join(bad[:8]))
    return Check("尾换行检查", "PASS", "全部以换行结尾")


def chk_disallowed_tools(skill_dir):
    """禁用工具名检查（P0-1 硬代码化，C 复审 P1 修复）：`delegate_task` 作为操作指令
    出现且上下文无「别名/仅当支持」限定、亦非否定告诫 → FAIL。
    排除脚本自身（其 docstring 含别名说明）；支持行内豁免标记。"""
    bad = []
    for p in skill_dir.rglob("*"):
        if not p.is_file() or p.suffix not in (".md", ".py") or p.name == "audit_guard.py":
            continue
        if p.name == "CHANGELOG.md" or p.name.startswith(("audit-", "deep-audit-", "optimize-")):
            continue  # 历史记录/审计报告/闭环报告：引用 delegate_task 是事实叙述（缺陷原文/修复动作），非当前操作指令
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # 剥离代码块（反模式文档里的"错误用法"示例是教学文本，不是操作指令）
        lines = re.sub(r"```[^\n]*\n.*?```", "", raw, flags=re.DOTALL).splitlines()
        for i, line in enumerate(lines):
            if "delegate_task" not in line or IGNORE_MARK in line:
                continue
            ctx = " ".join(lines[max(0, i - 1): i + 2])
            if not (re.search(r"别名|alias|仅当|仅作|作别名|当.*支持", ctx)
                    or re.search(r"勿|不要|别用|切勿|不写|不可|不存在", ctx)):
                bad.append(f"{p.relative_to(skill_dir)}:{i + 1}")
    if bad:
        return Check("禁用工具名检查", "FAIL", "delegate_task 作操作指令: " + ", ".join(bad[:8]))
    return Check("禁用工具名检查", "PASS", "无禁用工具名操作指令")


# ── selfcheck 主流程 ──────────────────────────────────────────
def run_selfcheck(skill_dir, strict=False):
    checks = [
        chk_line_endings(skill_dir),
        chk_version_consistency(skill_dir),
        chk_link_integrity(skill_dir),
        chk_orphans(skill_dir),
        chk_readme_structure(skill_dir),
        chk_cross_count(skill_dir),
        chk_frontmatter(skill_dir),
        chk_soft_phrases(skill_dir),
        chk_stale_paths(skill_dir),
        chk_trailing_newline(skill_dir),
        chk_disallowed_tools(skill_dir),
    ]
    print(f"\n═══ selfcheck: {skill_dir} ═══")
    fails = warns = 0
    for c in checks:
        print(c)
        if c.status == "FAIL":
            fails += 1
        elif c.status == "WARN":
            warns += 1
    print(f"───────────────────────────────")
    print(f"结果: {fails} FAIL / {warns} WARN / {len(checks)-fails-warns} PASS")
    if fails:
        print("退出码 1：存在 FAIL，STOP。")
        return 1
    if warns and strict:
        print("退出码 1：--strict 下 WARN 也算失败。")
        return 1
    print("退出码 0：通过（WARN 不阻断）。")
    return 0


# ── preflight 预检闸 ─────────────────────────────────────────
def run_preflight(skill_dir):
    print(f"\n═══ preflight 预检闸: {skill_dir} ═══")
    # 闸 1：目标 SKILL.md 存在
    gate1 = (skill_dir / "SKILL.md").exists()
    print(f"  [{'✅' if gate1 else '❌'}] 闸1 目标 SKILL.md 存在 → {'GO' if gate1 else 'STOP'}")
    # 闸 2：selfcheck 通过（无 FAIL）
    code = run_selfcheck(skill_dir)
    gate2 = code == 0
    print(f"  [{'✅' if gate2 else '❌'}] 闸2 结构自检无 FAIL → {'GO' if gate2 else 'STOP'}")
    # 闸 3：审计员工具可用 —— 人工确认项（P1-8 修复：不再伪装成机械闸）
    print("  [ℹ️] 闸3（人工确认项，不参与机械判定）：审计员工具可用（本环境用 Agent/Task）；")
    print("        delegate_task 仅在环境支持时作为别名。绝不让优化器兼审计员。")
    if gate1 and gate2:
        print("═══ 预检全部 GO，可进入闭环 ① ═══")
        return 0
    print("═══ 预检存在 STOP，先解决再进；强行跑 = 自欺 ═══")
    return 1


# ── loop 状态机 ──────────────────────────────────────────────
def load_loop_state():
    try:
        if DEFAULT_STATE.exists():
            return json.loads(DEFAULT_STATE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_loop_state(state):
    try:
        DEFAULT_STATE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def run_loop(round_no, max_rounds, b=None, c=None, rubric_max=100, target=None, no_state=False, override_max=False, pure_query=False, reset_state=False):
    """闭环状态机（P1-7 修复）：参数校验 + --max 硬钳制 + 状态持久化自增。
    pure_query（--delta 纯差值查询）不读写轮次状态（C 复审 P1 修复）；reset_state 复位指定目标的轮次。"""
    print(f"\n═══ loop 状态机 ═══")
    if reset_state:
        state = load_loop_state()
        key = str(Path(target).resolve()) if target else "default"
        state.pop(key, None)
        save_loop_state(state)
        print(f"✅ 已复位轮次状态（{key}）。")
    if rubric_max <= 0:
        print(f"❌ rubric_max 必须 > 0（收到 {rubric_max}）——防除零。")
        return 2
    if round_no < 1:
        print(f"❌ round 必须 ≥ 1（收到 {round_no}）。")
        return 2
    if max_rounds < 1:
        print(f"❌ --max 必须 ≥ 1（收到 {max_rounds}）。")
        return 2
    hard_max = 3
    if not override_max and max_rounds > hard_max:
        print(f"⚠️  --max {max_rounds} 超过硬上限 {hard_max}，已钳制为 {hard_max}（--override-max 可显式解锁）。")
        max_rounds = hard_max
    # 状态自增（防"忘记递增永不触发"）；纯差值查询不落状态
    if not no_state and not pure_query:
        state = load_loop_state()
        key = str(Path(target).resolve()) if target else "default"
        entry = state.get(key, {})
        last = int(entry.get("round", 0) or 0)
        if round_no <= last:
            print(f"⚠️  轮次未递增（上次 {last}），已自动 +1 → {last + 1}")
            round_no = last + 1
        entry["round"] = round_no
        entry["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
        state[key] = entry
        save_loop_state(state)
    if round_no > max_rounds:
        print(f"❌ 超出最大轮次 MAX_ROUNDS={max_rounds}（当前 round={round_no}）→ 强制 STOP")
        print("   未闭合项请主代理人工收口，勿再自动循环。")
        return 1
    print(f"✅ round={round_no} ≤ MAX_ROUNDS={max_rounds}，允许继续。")
    if b is not None and c is not None:
        print(delta_decision(b, c, rubric_max))
    return 0


def delta_decision(b, c, rubric_max=100):
    """有向差值规则（P1-1 修复：跨量规转百分比）。
    (B−C)/rubric_max*100 > +3 百分点 → 自评分虚高以 C 为准；
    < −3 → 重核实 C；其余小幅波动主代理核对。"""
    if rubric_max <= 0:
        return f"   rubric_max 必须 > 0（收到 {rubric_max}）。"
    b_pct = b / rubric_max * 100
    c_pct = c / rubric_max * 100
    diff_pct = (b - c) / rubric_max * 100
    if diff_pct > 3:
        return (f"   B−C = {diff_pct:+.2f} 百分点（B={b_pct:.1f}% C={c_pct:.1f}%）> +3 → 自评分虚高，丢弃 B，以 C={c} 为准。\n"
                f"   行动：用 C 的发现做权威修复清单。")
    if diff_pct < -3:
        return (f"   C−B = {-diff_pct:+.2f} 百分点（B={b_pct:.1f}% C={c_pct:.1f}%）> +3 → 不要自动否定 C，先重核实 C 的基线/量规是否与 B 一致。")
    return (f"   |B−C| = {abs(diff_pct):.2f} 百分点 ≤ 3（B={b_pct:.1f}% C={c_pct:.1f}%）→ 小幅波动（正常方差），主代理交叉核对即可。\n"
            f"   权威分 = C = {c}。")


# ── closure 报告校验 ──────────────────────────────────────────
def run_closure(report_path, rubric_max=100):
    """P1-5 修复：解析具名「审计分 A / 自评分 B / 复审分 C」字段（消除与 SkillHub
    维度名 A/C 的冲突），重算 B−C 差值并与报告结论比对，不一致则 FAIL。"""
    p = Path(report_path)
    if not p.is_file():
        print(f"❌ 报告不是文件: {report_path}")
        return 1
    text = p.read_text(encoding="utf-8", errors="ignore")
    m_a = re.search(r"审计分\s*A[^0-9]{0,12}=\s*([0-9]+(?:\.[0-9]+)?)", text)
    m_b = re.search(r"自评分\s*B[^0-9]{0,12}=\s*([0-9]+(?:\.[0-9]+)?)", text)
    m_c = re.search(r"复审分\s*C[^0-9]{0,12}=\s*([0-9]+(?:\.[0-9]+)?)", text)
    a = float(m_a.group(1)) if m_a else None
    b = float(m_b.group(1)) if m_b else None
    c = float(m_c.group(1)) if m_c else None
    has_delta = bool(re.search(r"B\s*−\s*C|B−C|差值|delta", text, re.IGNORECASE))
    print(f"\n═══ closure 报告校验: {report_path} ═══")
    print(f"  [{'✅' if a is not None else '❌'}] 含 A 评分（审计分 A = {a}）")
    print(f"  [{'✅' if b is not None else '❌'}] 含 B 自评分（自评分 B = {b}）")
    print(f"  [{'✅' if c is not None else '❌'}] 含 C 复审分（复审分 C = {c}）")
    print(f"  [{'✅' if has_delta else '⚠️ '}] 含差值决策")
    if a is None or b is None or c is None:
        print("❌ 闭环不完整：报告必须含具名字段「审计分 A = N」「自评分 B = N」「复审分 C = N」。")
        print("   （提示：SkillHub 五维里的 A/C 维度名不算审计分，请用具名标识消除歧义。）")
        return 1
    if not has_delta:
        print("⚠️ 报告含 A/B/C 但未见差值决策，建议补 B−C 有向判定。")
        return 0
    # 重算差值并与报告结论比对
    diff_pct = (b - c) / rubric_max * 100
    if diff_pct > 3:
        concl_ok = bool(re.search(r"以\s*C\s*为准|丢弃\s*B|虚高", text))
        verdict = "虚高（以 C 为准）"
    elif diff_pct < -3:
        concl_ok = bool(re.search(r"重核实\s*C|重核\s*C|勿.*否定\s*C", text))
        verdict = "重核实 C"
    else:
        concl_ok = True
        verdict = "小幅波动"
    print(f"  [{'✅' if concl_ok else '❌'}] 差值结论与 B−C 规则一致（应判: {verdict}，B−C={diff_pct:+.2f} 百分点）")
    if not concl_ok:
        print("❌ 报告差值结论与 B−C 规则矛盾，请更正后重跑。")
        return 1
    print("✅ 闭环报告结构完整，且差值结论与规则一致。")
    return 0


# ── selftest 变异测试 ─────────────────────────────────────────
def run_selftest(target=None):
    """P1-2 修复：变异测试。在临时副本注入缺陷，断言 selfcheck 必须检出。
    全部检出 → 0；任一漏检 → 1。把「脚本能跑」升级为「脚本能检出」。"""
    src = find_skill_dir(target)
    print(f"\n═══ selftest 变异测试: {src} ═══")
    tmp = Path(tempfile.mkdtemp(prefix="audit_guard_selftest_"))
    results = []
    try:
        dst = tmp / "skill"
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        readme = dst / "README.md"
        lic = dst / "LICENSE"

        def run_capture(strict=False):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = run_selfcheck(dst, strict=strict)
            return code, buf.getvalue()

        def wl(path, text):
            """以 LF 字节写入文本（避免 Windows 文本模式把 \\n 转 CRLF 污染变异测试——C 复审 P0 修复）。"""
            path.write_bytes(text.encode("utf-8"))

        def rb_append(path, suffix_bytes):
            path.write_bytes(path.read_bytes() + suffix_bytes)

        def rb_remove(path, needle_bytes):
            path.write_bytes(path.read_bytes().replace(needle_bytes, b""))

        # M4b：纯孤儿（基线，必须检出）
        wl(dst / "references" / "lonely.md", "# lonely\n")
        code, _ = run_capture()
        results.append(("M4b 纯孤儿必须 FAIL", code == 1))
        (dst / "references" / "lonely.md").unlink()

        # M1：README 断链（P1-2 修复：原来只扫 SKILL.md 漏检）
        if readme.exists():
            rb_append(readme, "\n[断链测试](./no-such-file.md)\n".encode("utf-8"))
            code, _ = run_capture()
            results.append(("M1 README 断链必须 FAIL", code == 1))
            rb_remove(readme, "\n[断链测试](./no-such-file.md)\n".encode("utf-8"))

        # M2：LICENSE 无扩展名文件 CRLF（P1-2 修复：原来按后缀白名单跳过）
        if lic.exists():
            lic.write_bytes(lic.read_bytes().replace(b"\n", b"\r\n"))
            code, _ = run_capture()
            results.append(("M2 LICENSE CRLF 必须 FAIL", code == 1))
            lic.write_bytes(lic.read_bytes().replace(b"\r\n", b"\n"))

        # M3：含 @ 的幽灵路径（WARN 级；P1-2 修复：字符类必须含 @ 完整捕获）
        ghost = "C:/Users/user/.workbuddy/skills/@user_48f048de/TOTALLY-GHOST-SKILL"
        if readme.exists():
            rb_append(readme, f"\n幽灵路径 {ghost}\n".encode("utf-8"))
            _, out = run_capture()
            results.append(("M3 @ 幽灵路径必须检出", ghost in out))
            rb_remove(readme, f"\n幽灵路径 {ghost}\n".encode("utf-8"))

        # M4：互引孤儿（P1-2 修复：BFS 从 SKILL.md 可达性，互引即脱敏的旧判据已废）
        wl(dst / "references" / "orphan-a.md", "见 orphan-b.md\n")
        wl(dst / "references" / "orphan-b.md", "见 orphan-a.md\n")
        code, _ = run_capture()
        results.append(("M4 互引孤儿必须 FAIL", code == 1))
        (dst / "references" / "orphan-a.md").unlink()
        (dst / "references" / "orphan-b.md").unlink()

        all_ok = True
        for name, ok in results:
            print(f"  [{'✅' if ok else '❌'}] {name}")
            if not ok:
                all_ok = False
        if all_ok:
            print("全部变异均被检出：硬代码保障覆盖面成立。")
            return 0
        print("存在漏检：脚本 PASS 但缺陷在场——selftest 未通过。")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── CLI ──────────────────────────────────────────────────────
def main():
    # P1-4 修复：强制 UTF-8 输出，非 UTF-8 代码页（如中文 Windows cp936）不崩。
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="unclekk-audit-then-optimize 硬代码保障 (v1.2.0)")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("selfcheck", help="结构完整性自检")
    s.add_argument("--target", default=None, help="技能目录（默认自动定位为脚本上级）")
    s.add_argument("--strict", action="store_true", help="WARN 也视为失败")

    p = sub.add_parser("preflight", help="进入闭环前的预检闸")
    p.add_argument("--target", default=None)

    l = sub.add_parser("loop", help="闭环状态机 / 差值规则")
    l.add_argument("--round", type=int, default=1)
    l.add_argument("--max", type=int, default=3, dest="max_rounds")
    l.add_argument("--b", type=float, default=None)
    l.add_argument("--c", type=float, default=None)
    l.add_argument("--delta", nargs=2, type=float, metavar=("B", "C"), default=None,
                   help="B C 差值（等价于 --b/--c，跨量规自动转百分比）")
    l.add_argument("--rubric-max", type=float, default=100)
    l.add_argument("--target", default=None, dest="loop_target", help="状态持久化键（技能目录）")
    l.add_argument("--no-state", action="store_true", help="关闭轮次状态持久化（退化为显式传入）")
    l.add_argument("--override-max", action="store_true", help="允许 --max 超过硬上限 3")
    l.add_argument("--reset-state", action="store_true", help="复位指定目标的轮次状态")

    c = sub.add_parser("closure", help="审计报告完整性校验")
    c.add_argument("--report", required=True)
    c.add_argument("--rubric-max", type=float, default=100)

    t = sub.add_parser("selftest", help="变异测试（自证覆盖能力）")
    t.add_argument("--target", default=None)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0

    if args.cmd == "selfcheck":
        return run_selfcheck(find_skill_dir(args.target), args.strict)
    if args.cmd == "preflight":
        return run_preflight(find_skill_dir(args.target))
    if args.cmd == "loop":
        b, c = args.b, args.c
        pure_query = False
        if args.delta is not None:
            b, c = args.delta[0], args.delta[1]
            pure_query = True  # 纯差值查询不写轮次状态
        return run_loop(args.round, args.max_rounds, b, c, args.rubric_max,
                        target=args.loop_target, no_state=args.no_state, override_max=args.override_max,
                        pure_query=pure_query, reset_state=args.reset_state)
    if args.cmd == "closure":
        return run_closure(args.report, args.rubric_max)
    if args.cmd == "selftest":
        return run_selftest(args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
