"""Read exact HTML destinations; preserve links and fonts during finalization."""
import json
import re
import sys
import unicodedata
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

def normalize(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or ""))

def build_page_map(pdf_path, sections_path):
    reader = PdfReader(pdf_path)
    sections = json.loads(Path(sections_path).read_text(encoding="utf-8"))
    destinations = reader.named_destinations
    outlines = {}
    def walk(items):
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                outlines.setdefault(normalize(item.title), []).append(reader.get_destination_page_number(item) + 1)
    walk(reader.outline)
    result = {}
    for section in sections:
        dest = destinations.get(section["id"]) or destinations.get('/' + section["id"])
        if dest is not None:
            page = reader.get_destination_page_number(dest) + 1
        else:
            matches = outlines.get(normalize(section["title"]), [])
            if len(matches) != 1:
                raise ValueError(f"No unique destination for {section['id']}: {matches}")
            page = matches[0]
        if not 1 <= page <= len(reader.pages):
            raise ValueError(f"Invalid destination: {section['id']}")
        text = normalize(reader.pages[page - 1].extract_text())
        if normalize(section["shortTitle"]) not in text:
            raise ValueError(f"Title absent on destination page: {section['id']} ({page})")
        result[section["id"]] = page
    if list(result.values()) != sorted(set(result.values())):
        raise ValueError("Chapter pages are not strictly increasing")
    print(json.dumps(result, ensure_ascii=False))

def finalize_pdf(source, target, outline_path):
    reader = PdfReader(source)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.root_object.pop(NameObject("/Outlines"), None)
    outline = json.loads(Path(outline_path).read_text(encoding="utf-8"))
    for entry in outline:
        page = entry["page"] - 1
        if not 0 <= page < len(reader.pages):
            raise ValueError(f"Invalid bookmark: {entry}")
        writer.add_outline_item(entry["title"], page)
    writer.add_metadata({"/Title":"天命：马克思与毛泽东在现代中国","/Author":"Nigel Harris","/Subject":"中文译文 · 现代排印版","/Creator":"Tianming HTML book builder"})
    writer.root_object[NameObject("/PageMode")] = NameObject("/UseOutlines")
    with open(target, "wb") as stream:
        writer.write(stream)
    final = PdfReader(target)
    if len(final.pages) != len(reader.pages) or len(final.outline) != len(outline):
        raise ValueError("Page or bookmark count mismatch")
    links = sum(len(p.get("/Annots", [])) for p in final.pages)
    if links != sum(len(p.get("/Annots", [])) for p in reader.pages):
        raise ValueError("Finalization lost annotations")
    print(json.dumps({"pageCount":len(final.pages),"bookmarks":len(final.outline),"annotations":links,"bytes":Path(target).stat().st_size}))

if __name__ == "__main__":
    if sys.argv[1] == "page-map":
        build_page_map(*sys.argv[2:])
    elif sys.argv[1] == "finalize":
        finalize_pdf(*sys.argv[2:])
    else:
        raise SystemExit("Expected page-map or finalize")
