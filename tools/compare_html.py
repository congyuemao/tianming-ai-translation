"""Make a side-by-side review page: baseline vs current chapter, paragraph by paragraph.

Usage (repo root):
  python -I tools/compare_html.py <chapter-prefix> [--base main] [--out build/对照_<prefix>.html]

Deleted text is red with strikethrough, new text green. The English source of the chapter
(source/en/<name>.md, from tools/extract_en.py) is appended at the end for reference.
"""
import argparse
import difflib
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polish_guard as g  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def diff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    old, new = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        x, y = html.escape(a[i1:i2]), html.escape(b[j1:j2])
        if op == "equal":
            old.append(x)
            new.append(y)
        else:
            if x:
                old.append(f"<del>{x}</del>")
            if y:
                new.append(f"<ins>{y}</ins>")
    return "".join(old), "".join(new), sm.ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("--base", default="main")
    ap.add_argument("--out")
    a = ap.parse_args()
    from add_note import chapter_path
    path = chapter_path(a.prefix.rstrip("_"))
    base = g.git_show(a.base, f"each_chapter/{path.name}")
    cur = path.read_text(encoding="utf-8")
    bb, bn = g.split(base)
    cb, cn = g.split(cur)
    rows = []
    for i, (o, n) in enumerate(zip(bb, cb), 1):
        x, y, r = diff(o, n)
        rows.append(f'<tr><td class="no">{i}</td><td>{x}</td><td>{y}</td></tr>')
    rows.append('<tr><th colspan="3">注释与引用</th></tr>')
    bmap = dict(bn)
    for k, line in cn:
        x, y, _ = diff(bmap.get(k, ""), line) if k in bmap else ("", html.escape(line), 0)
        rows.append(f'<tr><td class="no">注{k}</td><td>{x}</td><td>{y}</td></tr>')
    en_path = ROOT / "source" / "en" / path.name
    en = html.escape(en_path.read_text(encoding="utf-8")) if en_path.exists() else "（未生成英文底本）"
    en = re.sub(r"&lt;!--(p\.[^-]+)--&gt;", r"<b class='pg'>\1</b>", en)
    title = cb[0].lstrip("# ")
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>润色对照 {html.escape(title)}</title>
<style>
:root{{--bg:#fbfaf7;--fg:#222;--del:#fde2e2;--delfg:#a33;--ins:#dff3e1;--insfg:#17652a;--line:#ddd}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1b1b1b;--fg:#ddd;--del:#4a2222;--delfg:#f3a3a3;--ins:#1f3d25;--insfg:#9fe0ad;--line:#444}}}}
body{{background:var(--bg);color:var(--fg);font:16px/1.8 "Noto Serif SC","Songti SC",serif;margin:0 16px 40px}}
h1{{font-size:1.3em}} table{{border-collapse:collapse;width:100%;table-layout:fixed}}
td,th{{border-bottom:1px solid var(--line);padding:10px 8px;vertical-align:top;word-break:break-word}}
td.no{{width:3.2em;color:#888;font:13px sans-serif}} thead th{{position:sticky;top:0;background:var(--bg);text-align:left}}
del{{background:var(--del);color:var(--delfg)}} ins{{background:var(--ins);color:var(--insfg);text-decoration:none}}
pre{{white-space:pre-wrap;font:14px/1.6 Georgia,serif}} .pg{{display:block;margin-top:1em;color:#888}}
@media (max-width:700px){{table,tbody,tr,td{{display:block}} td.no{{width:auto}} thead{{display:none}}}}
</style></head><body><h1>{html.escape(title)}：润色前后对照</h1>
<p>左栏为原译稿（{html.escape(a.base)}），右栏为现稿。红色删除线是删去的文字，绿色是新写的文字。章末附英文底本。</p>
<table><thead><tr><th class="no">段</th><th>原译稿</th><th>润色稿</th></tr></thead><tbody>
{''.join(rows)}</tbody></table>
<details><summary><h2 style="display:inline">英文底本</h2></summary><pre>{en}</pre></details></body></html>"""
    out = Path(a.out) if a.out else ROOT / "build" / f"对照_{path.stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
