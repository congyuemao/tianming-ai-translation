"""Merge per-chapter JSONL tables into numbered review documents.

Usage (repo root): python -I tools/build_tables.py
Reads  logs/tables/idioms/*.jsonl, logs/tables/irony/*.jsonl
Writes logs/成语俗语对照表.md, logs/讽刺反话对照表.md (numbered, with a 决定 line per entry)
       build/成语俗语对照表.html, build/讽刺反话对照表.html (for reading)
Numbers are stable per run order (chapter file order, then line order). Existing 决定 lines in
the .md files are carried over by number+English text, so re-running does not wipe decisions.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
BUILD = ROOT / "build"

CHAPTER_TITLES = {}
for p in sorted((ROOT / "each_chapter").glob("*.md")):
    first = p.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ").strip()
    CHAPTER_TITLES[p.name] = first


def load(kind):
    rows = []
    for f in sorted((LOGS / "tables" / kind).glob("*.jsonl")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                r = json.loads(line)
                r.setdefault("file", f.stem)
                rows.append(r)
    rows.sort(key=lambda r: (r.get("file", ""),))
    return rows


def old_decisions(md_path):
    if not md_path.exists():
        return {}
    out = {}
    for block in re.split(r"\n(?=### )", md_path.read_text(encoding="utf-8")):
        m = re.match(r"### (\S+)", block)
        d = re.search(r"^- \*\*决定\*\*：(.*)$", block, re.M)
        en = re.search(r"^- 英文：(.*)$", block, re.M)
        if m and d and d.group(1).strip():
            out[(en.group(1).strip() if en else m.group(1))] = d.group(1).strip()
    return out


def lst(x):
    if isinstance(x, list):
        return "；".join(str(i) for i in x if i)
    return str(x or "")


def build_idioms():
    rows = load("idioms")
    md_path = LOGS / "成语俗语对照表.md"
    keep = old_decisions(md_path)
    md = ["# 成语俗语歇后语对照表", "",
          "润色前建立。每条列出原文说法、语境义、现译和拟用的中文说法。润色按此表执行，表外不随意加成语。",
          "请在每条的“决定”后填写：同意 / 改用某说法 / 不用成语（平实译） / 其他意见。留空表示同意建议。", ""]
    h = []
    cur = None
    for n, r in enumerate(rows, 1):
        no = f"C{n:03d}"
        if r["file"] != cur:
            cur = r["file"]
            title = CHAPTER_TITLES.get(cur, cur)
            md += [f"## {title}", ""]
            h.append(f"<h2>{html.escape(title)}</h2>")
        dec = keep.get(r.get("en", "").strip(), "")
        md += [f"### {no}　{r.get('en','')}", "",
               f"- 类型：{r.get('type','')}；原书第{r.get('page','')}页",
               f"- 英文：{r.get('en','')}",
               f"- 语境：{r.get('context','')}",
               f"- 语境义：{r.get('meaning','')}",
               f"- 现译：{r.get('current_zh','')}",
               f"- 建议：**{r.get('suggest','')}**" + (f"（备选：{lst(r.get('alt'))}）" if lst(r.get('alt')) else ""),
               f"- 说明：{r.get('note','')}",
               f"- **决定**：{dec}", ""]
        h.append(f"""<div class="e"><div class="no">{no}<span>{html.escape(r.get('type',''))} · p.{html.escape(str(r.get('page','')))}</span></div>
<p class="en"><b>{html.escape(r.get('en',''))}</b> — {html.escape(r.get('context',''))}</p>
<p>语境义：{html.escape(r.get('meaning',''))}</p><p>现译：{html.escape(r.get('current_zh',''))}</p>
<p class="s">建议：<b>{html.escape(r.get('suggest',''))}</b>{('　备选：'+html.escape(lst(r.get('alt')))) if lst(r.get('alt')) else ''}</p>
<p class="n">{html.escape(r.get('note',''))}</p></div>""")
    md_path.write_text("\n".join(md), encoding="utf-8", newline="\n")
    page("成语俗语对照表", f"共 {len(rows)} 条。按编号回复决定即可，也可以直接在 logs/成语俗语对照表.md 的“决定”行里填写。", h,
         BUILD / "成语俗语对照表.html")
    return len(rows)


def build_irony():
    rows = load("irony")
    md_path = LOGS / "讽刺反话对照表.md"
    keep = old_decisions(md_path)
    md = ["# 讽刺反话对照表", "",
          "润色时正文先用“直译”一栏。请逐条决定：用直译 / 用建议一或建议二 / 自己改写（直接写出）。",
          "改用意译的条目，完整版会加译注列出直译，阅读版正文同样改。留空表示暂用直译。", ""]
    h = []
    cur = None
    for n, r in enumerate(rows, 1):
        no = f"F{n:03d}"
        if r["file"] != cur:
            cur = r["file"]
            title = CHAPTER_TITLES.get(cur, cur)
            md += [f"## {title}", ""]
            h.append(f"<h2>{html.escape(title)}</h2>")
        sugg = r.get("suggest") or []
        if isinstance(sugg, str):
            sugg = [sugg]
        dec = keep.get(r.get("en", "").strip(), "")
        md += [f"### {no}", "",
               f"- 原书第{r.get('page','')}页",
               f"- 英文：{r.get('en','')}",
               f"- 讽刺对象与手法：{r.get('target','')}；{r.get('how','')}",
               f"- 现译：{r.get('current_zh','')}",
               f"- 直译（正文暂用）：{r.get('literal_zh','')}"]
        md += [f"- 意译建议{'一二三'[i]}：{s}" for i, s in enumerate(sugg[:3])]
        md += [f"- 风险：{r.get('risk','')}", f"- **决定**：{dec}", ""]
        sug_html = "".join(f"<p class='s'>意译{'一二三'[i]}：{html.escape(s)}</p>" for i, s in enumerate(sugg[:3]))
        h.append(f"""<div class="e"><div class="no">{no}<span>p.{html.escape(str(r.get('page','')))}</span></div>
<p class="en">{html.escape(r.get('en',''))}</p>
<p class="n">对象：{html.escape(r.get('target',''))}；手法：{html.escape(r.get('how',''))}</p>
<p>现译：{html.escape(r.get('current_zh',''))}</p><p class="l">直译：{html.escape(r.get('literal_zh',''))}</p>
{sug_html}<p class="n">风险：{html.escape(r.get('risk',''))}</p></div>""")
    md_path.write_text("\n".join(md), encoding="utf-8", newline="\n")
    page("讽刺反话对照表", f"共 {len(rows)} 条。正文暂用直译；按编号回复“用意译一／二”“保持直译”或你的改法。", h,
         BUILD / "讽刺反话对照表.html")
    return len(rows)


def page(title, lead, blocks, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
:root{{--bg:#fbfaf7;--fg:#222;--mut:#777;--card:#fff;--line:#e3e0d8;--acc:#9b2d20;--ok:#17652a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1b1b1b;--fg:#ddd;--mut:#999;--card:#242424;--line:#3a3a3a;--acc:#e38b7d;--ok:#9fe0ad}}}}
body{{background:var(--bg);color:var(--fg);font:16px/1.75 "Noto Serif SC","Songti SC",serif;margin:0 auto;max-width:860px;padding:0 16px 48px}}
h1{{margin-top:28px}} h2{{margin-top:36px;border-bottom:2px solid var(--acc);padding-bottom:4px}}
.e{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 16px;margin:12px 0}}
.no{{font:600 15px sans-serif;color:var(--acc)}} .no span{{font-weight:400;color:var(--mut);margin-left:10px;font-size:13px}}
.e p{{margin:4px 0}} .en{{font-family:Georgia,serif;color:var(--mut)}} .s{{color:var(--ok)}} .l{{font-weight:600}} .n{{color:var(--mut);font-size:14px}}
</style></head><body><h1>{title}</h1><p>{lead}</p>{''.join(blocks)}</body></html>""", encoding="utf-8")


if __name__ == "__main__":
    print("idioms", build_idioms(), "irony", build_irony())
