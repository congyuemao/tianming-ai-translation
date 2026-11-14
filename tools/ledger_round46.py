"""Write the round-46 citation ledger after the full-book polish (2026-11).

Usage (repo root): python -I tools/ledger_round46.py
Reads  reference check/2026-10-16-round45.json and each_chapter/*.md
Writes reference check/2026-11-15-round46.json and reference check/2026-11-15-round46.md

Round 46 is a policy round, not a new search round: the user authorised translating
"partial" items (English intermediary source verified, Chinese original not found) from the
author's English with a note, and removing their 【原文待核】 markers.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUD = ROOT / "reference check"
SRC = AUD / "2026-10-16-round45.json"
OUT_JSON = AUD / "2026-11-15-round46.json"
OUT_MD = AUD / "2026-11-15-round46.md"


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    chapters = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "each_chapter").glob("*.md")}
    markers = sum(t.count("【原文待核】") for t in chapters.values())
    for r in d["records"]:
        prev = {k: r.get(k) for k in ("status", "statusLabel")}
        if r["status"] == "partial":
            r["status"] = "translated_from_english"
            r["statusLabel"] = "据英文转引译出（中文原话未见）"
            r["round46Note"] = ("英文转引来源已核；按用户2026-11-15授权，按作者所引英文忠实译出，"
                                "撤去【原文待核】，注中说明据英文转引译出及已知出入。")
            r["previousRound"] = {**prev, "round": 45}
        elif r["status"] == "restored" and "回译" in (r.get("statusLabel") or ""):
            # BBC/English-record items: verified against the English record, never a Chinese original.
            r["status"] = "translated_from_english"
            r["statusLabel"] = "据英文记录译出（BBC等英文记录已核，中文原话未见）"
            r["round46Note"] = "第45轮记为“已落实”，实为按已核英文记录回译；本轮归入据英文译出一类，引文和注释不变。"
            r["previousRound"] = {**prev, "round": 45}
        r.pop("currentLine", None)
        r.pop("currentParagraph", None)
    counts = Counter(r["status"] for r in d["records"])
    d.update({
        "date": "2026-11-15",
        "round": 46,
        "previousSnapshot": SRC.name,
        "scope": "全书重新润色后的政策轮：部分核实条目改为据英文转引译出并撤标；不新增检索。",
    })
    acc = d.get("userSourceAcceptance")
    note46 = "2026-11-15 用户授权：“找资料那个核查到英文来源的就按你的处理”，即英文转引来源已核的条目按英文译出、注明出处并撤标。"
    if isinstance(acc, dict):
        acc["2026-11-15"] = note46
    else:
        d["userSourceAcceptance"] = {"previous": acc, "2026-11-15": note46}
    d["summary"] = {
        "initialMarkers": len(d["records"]),
        "restored": counts.get("restored", 0),
        "translated_from_english": counts.get("translated_from_english", 0),
        "searched_unresolved": counts.get("searched_unresolved", 0),
        "partial": counts.get("partial", 0),
        "not_reviewed": counts.get("not_reviewed", 0),
        "remainingMarkers": markers,
        "note": "currentLine/currentParagraph 字段已删除：全书润色后段落和注号均有变化，定位请用 excerpt 检索。",
    }
    OUT_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    s = d["summary"]
    OUT_MD.write_text(f"""# 第四十六轮：全书润色后的引文状态（2026-11-15）

本轮不是新的检索轮。另把第45轮记为“已落实”、实为按BBC等英文记录回译的条目，归入“据英文译出”一类，引文本身不变。2026年11月全书对照英文重新润色，用户授权：英文转引来源已经核到、中文原话没有找到的引文（第45轮的“部分核实”），按作者所引英文忠实译出，在注中写明“据英文转引译出，中文原话未见”及已知出入，撤去【原文待核】。

固定225条现为：

| 状态 | 数量 |
| --- | ---: |
| 已恢复中文原文或按指定版本校引 | {s['restored']} |
| 据英文转引或英文记录译出（中文原话未见） | {s['translated_from_english']} |
| 已检索未落实，保留【原文待核】 | {s['searched_unresolved']} |

正文现有【原文待核】标记 {s['remainingMarkers']} 处。

润色和三道复核中，还对不在台账里的若干毛泽东、马克思、恩格斯、列宁引文做了核对：核到原文的按原文校正并注明出处，核不到的改为据英文译出。逐章记录见 `logs/polish/` 和 `logs/review/`。

台账的 currentLine、currentParagraph 字段已删除：润色后段落与注号都有变化，定位请用 excerpt 检索。
""", encoding="utf-8", newline="\n")
    print(json.dumps(s, ensure_ascii=False))


if __name__ == "__main__":
    main()
