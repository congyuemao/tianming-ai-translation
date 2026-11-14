"""Build per-chapter English source files from page texts extracted from the source PDF.

Usage: python -I tools/extract_en.py  (run from repo root; reads source/en_pages/pNNN.txt)
Writes source/en/<prefix>.md with <!--p.N--> page markers so reviewers can cite book pages.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "source" / "en_pages"
OUT = ROOT / "source" / "en"

# (output name, first PDF page, last PDF page); book page = PDF page - 19 for arabic pages.
CHAPTERS = [
    ("00_2015_preface", 8, 13), ("01_1978_preface", 14, 15), ("01a_notes_for_reader", 16, 19),
    ("02_ch01_workers_revolution", 22, 37), ("03_ch02_from_defeat_to_victory", 38, 59),
    ("04_ch03_first_phase", 60, 73), ("05_ch04_great_leap_forward_and_after", 74, 87),
    ("06_ch05_cultural_revolution", 88, 103), ("07_ch06_after_cultural_revolution", 104, 117),
    ("08_ch07_workers_in_1950s", 118, 137), ("09_ch08_temporary_contract_labour", 138, 147),
    ("10_ch09_working_class_after_cultural_revolution", 148, 165),
    ("11_ch10_peasants_in_prc", 166, 185), ("12_ch11_equality", 186, 205),
    ("13_ch12_democracy", 206, 221), ("14_ch13_national_independence", 222, 245),
    ("15_ch14_theory", 246, 257), ("16_ch15_foreign_policy", 258, 283),
    ("17_ch16_mao_zedong_thought_abroad", 284, 305),
    ("18_ch17_modern_capitalism_bourgeois_revolution", 306, 317),
    ("19_ch18_soviet_union_new_class", 318, 331), ("20_ch19_mao_zedong_thought", 332, 345),
    ("21_retrospect", 346, 349),
]
FOOTER = re.compile(r"Mandate of Heaven text.*?Page\s+([0-9ivxlc]+)\s*$")


def clean(text):
    label = None
    lines = []
    for line in text.splitlines():
        m = FOOTER.search(line)
        if m:
            label = m.group(1)
            line = line[: m.start()]
        lines.append(line.rstrip())
    # drop bare running page numbers / running heads at top
    while lines and (not lines[0].strip() or re.fullmatch(r"\d+|[ivxlc]+", lines[0].strip())):
        lines.pop(0)
    body = "\n".join(lines)
    body = re.sub(r"(\w)-\n(\w)", r"\1\2", body)  # rejoin hyphenated line breaks
    return label, body.strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, a, b in CHAPTERS:
        parts = []
        for n in range(a, b + 1):
            label, body = clean((PAGES / f"p{n:03d}.txt").read_text(encoding="utf-8"))
            parts.append(f"<!--p.{label or n}-->\n{body}")
        (OUT / f"{name}.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(CHAPTERS)} files to {OUT}")


if __name__ == "__main__":
    main()
