"""Guard a polishing pass: compare each chapter in each_chapter/ with a baseline git revision.

Usage (repo root):
  python -I tools/polish_guard.py [--base main] [--chapter 09] [--verbose]

Errors (must fix):
  - body paragraph count or heading lines changed
  - note references inside a body paragraph changed (〔n〕 and [n] are treated alike)
  - number of endnotes changed, or endnotes not numbered 1..N
  - a quotation restored from a Chinese original (ledger status "restored") that was present
    in the baseline is no longer present verbatim
Warnings (review each one):
  - Arabic-digit numbers in a body paragraph differ from the baseline
  - 【原文待核】 count in a paragraph changed
"""
import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "each_chapter"
LEDGER = ROOT / "reference check" / "2026-10-16-round45.json"
NOTES_HEAD = re.compile(r"^## 注释与引用\s*$", re.M)


def git_show(rev, rel):
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def split(text):
    text = text.replace("\r\n", "\n")
    parts = NOTES_HEAD.split(text, maxsplit=1)
    body = [p.strip() for p in re.split(r"\n\s*\n", parts[0]) if p.strip()]
    notes = []
    if len(parts) > 1:
        for line in parts[1].split("\n"):
            m = re.match(r"^(\d+)\.\s", line)
            if m:
                notes.append((int(m.group(1)), line))
    return body, notes


def refs(p):
    return re.findall(r"\[(\d+)\](?!\()|〔(\d+)〕", p)


def refseq(p):
    return [a or b for a, b in refs(p)]


CN_DIGIT = dict(zip("零一二两三四五六七八九", [0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))
CN_UNIT = {"十": 10, "百": 100, "千": 1000}


def cn_section(s):
    total, cur = 0, 0
    for ch in s:
        if ch in CN_DIGIT:
            cur = CN_DIGIT[ch]
        elif ch in CN_UNIT:
            total += (cur or 1) * CN_UNIT[ch]
            cur = 0
    return total + cur


def cn2num(s):
    frac = ""
    if "点" in s:
        s, f = s.split("点", 1)
        frac = "".join(str(CN_DIGIT.get(c, "")) for c in f)
    total = 0
    for unit, mult in (("亿", 10**8), ("万", 10**4)):
        if unit in s:
            head, s = s.split(unit, 1)
            total += cn_section(head) * mult
    total += cn_section(s)
    return f"{total}.{frac}" if frac else str(total)


def numbers(p):
    """Values of numbers, so 二百四十万 == 240万 == 2400000; 1965—1966 counts both years."""
    p = re.sub(r"\[\d+\](?!\()|〔\d+〕", "", p)
    out = Counter()
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)(万|亿)?|([零一二两三四五六七八九十百千万亿点]{2,})", p):
        if m.group(1):
            v = float(m.group(1).replace(",", ""))
            v *= {"万": 10**4, "亿": 10**8}.get(m.group(2), 1)
            out[f"{v:g}"] += 1
        else:
            word = m.group(3)
            if not re.search(r"[十百千万亿点]", word):
                continue
            try:
                out[f"{float(cn2num(word)):g}"] += 1
            except ValueError:
                pass
    return out


def restored_quotes():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    out = {}
    for r in data["records"]:
        if r.get("status") == "restored" and r.get("replacement"):
            for q in re.findall(r"“([^”]{4,})”", r["replacement"]):
                out.setdefault(r["file"], []).append((r["id"], q))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="main")
    ap.add_argument("--chapter")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--renumbered", action="append", default=[],
                    help="chapter prefix whose notes were deliberately renumbered: compare ref counts only")
    ap.add_argument("--allow-quote", action="append", default=[],
                    help="ledger id whose restored text was deliberately moved or edited (see logs/decisions.md)")
    ap.add_argument("--drop-base", action="append", default=[],
                    help="prefix:N — baseline body paragraph N (1-based) was a standalone 校注 moved into the notes")
    a = ap.parse_args()
    a.drop_base += ["04:17"]  # 04: standalone 校注 paragraph moved to note 11
    allow = set(a.allow_quote) | {"09-23"}  # 09-23: inline 校注 moved to endnote, quote itself unchanged
    rq = restored_quotes()
    total_err = 0
    for path in sorted(CH.glob("*.md")):
        if a.chapter and not path.name.startswith(a.chapter):
            continue
        base = git_show(a.base, f"each_chapter/{path.name}")
        if base is None:
            print(f"{path.name}: no baseline")
            continue
        cur = path.read_text(encoding="utf-8")
        errs, warns = [], []
        renum_ch = any(path.name.startswith(r) for r in a.renumbered)
        bb, bn = split(base)
        drops = {int(d.split(":")[1]) for d in a.drop_base if path.name.startswith(d.split(":")[0])}
        bb = [p for i, p in enumerate(bb, 1) if i not in drops]
        cb, cn = split(cur)
        if len(bb) != len(cb):
            errs.append(f"body paragraphs {len(bb)} -> {len(cb)}")
        for i, (o, n) in enumerate(zip(bb, cb), 1):
            if o.startswith("#") or n.startswith("#"):
                if o.startswith("#") != n.startswith("#"):
                    errs.append(f"para {i}: heading/body mismatch")
            renum = any(path.name.startswith(r) for r in a.renumbered)
            if renum and len(refseq(n)) < len(refseq(o)):
                errs.append(f"para {i}: lost note refs {refseq(o)} -> {refseq(n)}")
            elif renum and len(refseq(n)) > len(refseq(o)):
                warns.append(f"para {i}: added note refs {refseq(o)} -> {refseq(n)}")
            elif not renum and refseq(o) != refseq(n):
                errs.append(f"para {i}: note refs {refseq(o)} -> {refseq(n)}")
            if numbers(o) != numbers(n):
                lost = numbers(o) - numbers(n)
                added = numbers(n) - numbers(o)
                warns.append(f"para {i}: numbers -{dict(lost)} +{dict(added)}")
            po, pn = o.count("【原文待核】"), n.count("【原文待核】")
            if po != pn:
                warns.append(f"para {i}: 原文待核 {po} -> {pn}")
        if len(bn) != len(cn):
            (warns if renum_ch else errs).append(f"endnotes {len(bn)} -> {len(cn)}")
        body_refs = [int(x) for p in cb for x in refseq(p)]
        if body_refs != list(range(1, len(body_refs) + 1)) or len(body_refs) != len(cn):
            (errs if renum_ch else warns).append(f"body refs not 1..{len(cn)} in order: {body_refs[:5]}...")
        if [k for k, _ in cn] != list(range(1, len(cn) + 1)):
            errs.append("endnotes not numbered 1..N")
        flat_base, flat_cur = base.replace("\n", ""), cur.replace("\n", "")
        for rid, q in rq.get(path.name, []):
            if rid not in allow and q in flat_base and q not in flat_cur:
                errs.append(f"restored quote {rid} changed: “{q[:30]}”")
        total_err += len(errs)
        status = "OK" if not errs else "ERROR"
        print(f"{path.name}: {status}  errors={len(errs)} warnings={len(warns)}  "
              f"待核 {base.count('【原文待核】')}->{cur.count('【原文待核】')}")
        for e in errs:
            print("  E", e)
        if a.verbose or errs:
            for w in warns:
                print("  W", w)
    raise SystemExit(1 if total_err else 0)


if __name__ == "__main__":
    main()
