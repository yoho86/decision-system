#!/usr/bin/env python3
"""决策数据仓校验 + 统计（零依赖，python3 直接跑）。

三块输出：
  1. frontmatter 校验（必填/枚举/格式/一致性，E=错误 W=警告）
  2. 到期未回填清单（status: open 且 horizon <= 今天）
  3. 校准与切片统计（retrospective 自动排除出校准）

用法：
  python3 tools/validate.py                  # 从 ~/.config/decision-system/config.json 取 data_dir
  python3 tools/validate.py --data-dir PATH  # 显式指定数据仓

退出码：有校验错误 → 1，否则 0。schema 权威定义见仓库根 schema.md。
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "decision-system" / "config.json"

ENUMS = {
    "tier": {"micro", "full"},
    "stakes": {"low", "medium", "high"},
    "reversibility": {"reversible", "costly", "irreversible"},
    "mode": {"gut", "analysis", "rule", "external", "auto"},
    "status": {"open", "resolved"},
    "outcome": {"as-expected", "better", "worse", "mixed"},
}

# schema.md：micro 只强制这些；full 另需 mode
REQUIRED_MICRO = [
    "id", "title", "domain", "tier", "stakes", "reversibility",
    "chosen", "prediction", "confidence", "horizon", "status",
]
REQUIRED_FULL_EXTRA = ["mode"]

ANCHORS = [10, 30, 50, 70, 90]
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def strip_inline_comment(raw):
    """去掉行尾注释：空白后跟 #，且不在 [] 或引号内。"""
    in_quote = None
    depth = 0
    for i, ch in enumerate(raw):
        if in_quote:
            if ch == in_quote:
                in_quote = None
            continue
        if ch in "'\"":
            in_quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif ch == "#" and depth == 0 and i > 0 and raw[i - 1] in " \t":
            return raw[:i].rstrip()
    return raw.rstrip()


def parse_scalar(s):
    s = s.strip()
    if s == "":
        return None
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(x) for x in inner.split(",")]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def parse_frontmatter(text, errors):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append("E: 缺 frontmatter（文件须以 --- 开头）")
        return {}
    fm = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", line)
        if not m:
            continue  # 缩进的多行值等，机器字段用不到
        key, raw = m.group(1), strip_inline_comment(m.group(2))
        fm[key] = parse_scalar(raw)
    errors.append("E: frontmatter 未闭合（缺结尾 ---）")
    return fm


def validate_file(path, fm, seen_ids):
    errors, warns = [], []
    fname = path.name

    m = re.match(r"^(\d{4}-\d{2}-\d{2}-\d{3})-.+\.md$", fname)
    if not m:
        errors.append("E: 文件名不符合 YYYY-MM-DD-NNN-标题.md")
    fid = fm.get("id")
    if fid is None:
        pass  # 必填检查会报
    elif not ID_RE.match(str(fid)):
        errors.append(f"E: id 格式应为 YYYY-MM-DD-NNN，实际 {fid}")
    else:
        if m and m.group(1) != str(fid):
            errors.append(f"E: id({fid}) 与文件名前缀({m.group(1)})不一致")
        if fid in seen_ids:
            errors.append(f"E: id 重复（另见 {seen_ids[fid]}）")
        else:
            seen_ids[fid] = fname

    required = list(REQUIRED_MICRO)
    if fm.get("tier") == "full":
        required += REQUIRED_FULL_EXTRA
    for key in required:
        if fm.get(key) in (None, ""):
            errors.append(f"E: 必填字段缺失或为空：{key}")

    for key, allowed in ENUMS.items():
        val = fm.get(key)
        if val not in (None, "") and val not in allowed:
            errors.append(f"E: {key}={val} 不在枚举 {sorted(allowed)}")

    conf = fm.get("confidence")
    if conf is not None:
        if not isinstance(conf, int) or not (0 <= conf <= 100):
            errors.append(f"E: confidence 应为 0-100 整数，实际 {conf!r}")
        elif conf == 100:
            warns.append("W: confidence=100（schema 规定封顶 90，near-certain 手填 95+）")

    for key in ("horizon", "resolved_date"):
        val = fm.get(key)
        if val not in (None, "") and not DATE_RE.match(str(val)):
            errors.append(f"E: {key} 应为 YYYY-MM-DD，实际 {val!r}")

    status = fm.get("status")
    if status == "resolved":
        for key in ("outcome", "resolved_date", "process_score"):
            if fm.get(key) in (None, ""):
                errors.append(f"E: status=resolved 但 {key} 未回填")
        if fm.get("lesson") in (None, ""):
            warns.append("W: status=resolved 但 lesson 为空（建议一句话沉淀）")
    elif status == "open":
        for key in ("outcome", "resolved_date", "process_score"):
            if fm.get(key) not in (None, ""):
                warns.append(f"W: status=open 但 {key} 已有值（忘了改 status？）")

    ps = fm.get("process_score")
    if ps not in (None, "") and (not isinstance(ps, int) or not (1 <= ps <= 5)):
        errors.append(f"E: process_score 应为 1-5 整数，实际 {ps!r}")

    state = fm.get("state")
    if state not in (None, "") and not isinstance(state, list):
        warns.append(f"W: state 应为标签数组（如 [被催促, 怕错过]），实际是文本 {state!r}")

    for key in ("criteria", "models"):
        val = fm.get(key)
        if val not in (None, "") and not isinstance(val, list):
            warns.append(f"W: {key} 应为数组，实际 {val!r}")

    retro = fm.get("retrospective")
    if retro not in (None, True):
        errors.append(f"E: retrospective 只允许 true（或省略），实际 {retro!r}")

    return errors, warns


def nearest_anchor(conf):
    return min(ANCHORS, key=lambda a: abs(a - conf))


def fmt_slice(rows):
    """rows: [(label, mean, n)] 已按需过滤排序。"""
    return "\n".join(f"    {label:<14} 均分 {mean:.1f}（n={n}）" for label, mean, n in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", help="数据仓路径；缺省读 config.json")
    args = ap.parse_args()

    if args.data_dir:
        data_dir = Path(args.data_dir).expanduser()
    else:
        if not CONFIG_PATH.exists():
            sys.exit(f"找不到 {CONFIG_PATH}，请用 --data-dir 指定数据仓")
        data_dir = Path(json.loads(CONFIG_PATH.read_text())["data_dir"]).expanduser()
    log_dir = data_dir / "log"
    if not log_dir.is_dir():
        sys.exit(f"数据仓里没有 log/ 目录：{data_dir}")

    files = sorted(log_dir.glob("*/*.md"))
    decisions, seen_ids = [], {}
    total_errors = 0

    print(f"数据仓：{data_dir}（{len(files)} 个决策文件）\n")
    print("== 1. 校验 ==")
    clean = True
    for path in files:
        errs = []
        fm = parse_frontmatter(path.read_text(encoding="utf-8"), errs)
        e, w = validate_file(path, fm, seen_ids)
        errs += e
        if errs or w:
            clean = False
            print(f"  {path.relative_to(data_dir)}")
            for line in errs + w:
                print(f"    {line}")
        total_errors += len(errs)
        decisions.append(fm)
    if clean:
        print("  全部通过 ✓")

    today = date.today().isoformat()
    print("\n== 2. 到期未回填（status: open 且 horizon ≤ 今天）==")
    due = [d for d in decisions
           if d.get("status") == "open" and str(d.get("horizon", "9999")) <= today]
    if due:
        for d in due:
            print(f"  [{d.get('horizon')}] {d.get('title')}（{d.get('id')}）")
    else:
        print("  无")
    pending = [d for d in decisions
               if d.get("status") == "open" and str(d.get("horizon", "")) > today]
    if pending:
        print("  —— 未到期 open ——")
        for d in sorted(pending, key=lambda d: str(d.get("horizon"))):
            print(f"  [{d.get('horizon')}] {d.get('title')}（{d.get('id')}）")

    print("\n== 3. 统计 ==")
    resolved = [d for d in decisions if d.get("status") == "resolved"]
    n_open = sum(1 for d in decisions if d.get("status") == "open")
    domains = {}
    for d in decisions:
        domains[d.get("domain", "?")] = domains.get(d.get("domain", "?"), 0) + 1
    dom_str = "，".join(f"{k} {v}" for k, v in sorted(domains.items(), key=lambda x: -x[1]))
    print(f"  总量：{len(decisions)}（resolved {len(resolved)} / open {n_open}）；domain：{dom_str}")

    calib = [d for d in resolved
             if d.get("retrospective") is not True
             and isinstance(d.get("confidence"), int)
             and d.get("outcome") in ENUMS["outcome"]]
    n_retro = sum(1 for d in resolved if d.get("retrospective") is True)
    print(f"\n  校准（resolved 且非 retrospective，n={len(calib)}"
          + (f"；已排除 retrospective {n_retro} 条" if n_retro else "") + "）")
    if len(calib) < 20:
        print("  ⚠️ 样本 <20，统计不可靠，只做趋势提示，别急着定规则。")
    buckets = {a: [] for a in ANCHORS}
    for d in calib:
        buckets[nearest_anchor(d["confidence"])].append(d)
    for a in ANCHORS:
        ds = buckets[a]
        if not ds:
            continue
        hits = sum(1 for d in ds if d["outcome"] in ("as-expected", "better"))
        print(f"    档 {a:>2}%：n={len(ds)}，成真 {hits}/{len(ds)}"
              f"（实际 {100 * hits / len(ds):.0f}% vs 名义 {a}%）")

    scored = [d for d in resolved if isinstance(d.get("process_score"), int)]
    if scored:
        print(f"\n  process_score 切片（n={len(scored)}，均分 "
              f"{sum(d['process_score'] for d in scored) / len(scored):.1f}）")
        for field in ("mode", "stakes", "domain"):
            groups = {}
            for d in scored:
                groups.setdefault(str(d.get(field)), []).append(d["process_score"])
            rows = [(k, sum(v) / len(v), len(v)) for k, v in sorted(groups.items())]
            print(f"   按 {field}：")
            print(fmt_slice(rows))
        tag_groups = {}
        for d in scored:
            tags = d.get("state") if isinstance(d.get("state"), list) else []
            for t in tags:
                tag_groups.setdefault(str(t), []).append(d["process_score"])
        if tag_groups:
            rows = [(k, sum(v) / len(v), len(v)) for k, v in sorted(tag_groups.items())]
            print("   按 state 标签：")
            print(fmt_slice(rows))

    print(f"\n校验：{'有 %d 个错误 ✗' % total_errors if total_errors else '通过 ✓'}")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
