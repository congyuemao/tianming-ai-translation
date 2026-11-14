"""List italic text spans in the source PDF per chapter (to find the author's emphasis).

Usage (repo root): python -I tools/italics_en.py
Writes source/en_italic/<chapter>.txt: one line per italic run, "p.<book page>\t<text>".
Italics in the book mark titles, foreign words and the author's emphasis; only the last
needs bold in the Chinese text. Reviewers decide which is which.
"""
import logging
import re
import sys
from pathlib import Path

import pypdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_en import CHAPTERS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PDF = next(ROOT.glob("Mandate of Heaven*.pdf"))
OUT = ROOT / "source" / "en_italic"


def runs_for_page(page):
    runs, cur = [], []

    def visitor(text, cm, tm, font, size):
        name = (font or {}).get("/BaseFont", "") if font else ""
        italic = bool(re.search(r"Italic|Oblique|-It$", str(name)))
        if italic and text.strip():
            cur.append(text)
        elif text.strip():
            if cur:
                runs.append("".join(cur))
                cur.clear()
    page.extract_text(visitor_text=visitor)
    if cur:
        runs.append("".join(cur))
    return [re.sub(r"\s+", " ", r).strip() for r in runs if len(r.strip()) > 1]


def main():
    logging.disable(logging.WARNING)
    reader = pypdf.PdfReader(str(PDF))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, a, b in CHAPTERS:
        lines = []
        for n in range(a, b + 1):
            label = n - 19 if n > 19 else n
            for r in runs_for_page(reader.pages[n - 1]):
                lines.append(f"p.{label}\t{r}")
        (OUT / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(name, len(lines))


if __name__ == "__main__":
    main()
