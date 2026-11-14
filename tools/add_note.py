"""Insert a new endnote into a chapter and renumber the following notes.

Usage (repo root):
  python -I tools/add_note.py <chapter-prefix> <anchor-text> <note-text-file>

<anchor-text> must occur exactly once in the chapter body; the new reference [n] is placed
right after it. Body refs may be [n] or 〔n〕; all refs are rewritten as [n]. Notes after the
insertion point are shifted by one.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = re.compile(r"\[(\d+)\](?!\()|〔(\d+)〕")


def main():
    prefix, anchor, note_file = sys.argv[1:4]
    path = next((ROOT / "each_chapter").glob(f"{prefix}*.md"))
    note_text = Path(note_file).read_text(encoding="utf-8").strip()
    text = path.read_text(encoding="utf-8")
    body, sep, notes = text.partition("\n## 注释与引用\n")
    if body.count(anchor) != 1:
        raise SystemExit(f"anchor occurs {body.count(anchor)} times in body")
    pos = body.index(anchor) + len(anchor)
    new_no = len(REF.findall(body[:pos])) + 1
    shift = lambda m: f"[{int(m.group(1) or m.group(2)) + (1 if int(m.group(1) or m.group(2)) >= new_no else 0)}]"
    body = REF.sub(shift, body[:pos]) + f"[{new_no}]" + REF.sub(shift, body[pos:])
    lines = notes.split("\n")
    out, inserted = [], False
    for line in lines:
        m = re.match(r"^(\d+)\.(\s.*)$", line)
        if m and int(m.group(1)) >= new_no:
            if not inserted:
                out.append(f"{new_no}. {note_text}")
                inserted = True
            line = f"{int(m.group(1)) + 1}.{m.group(2)}"
        out.append(line)
    if not inserted:
        while out and not out[-1].strip():
            out.pop()
        out += [f"{new_no}. {note_text}", ""]
    path.write_text(body + sep + "\n".join(out), encoding="utf-8", newline="\n")
    print(f"{path.name}: inserted note {new_no}")


if __name__ == "__main__":
    main()
