import json
import re
import sys
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


def normalize(text):
    if text is None:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", "", text)


def build_page_map(pdf_path, titles_json):
    reader = PdfReader(pdf_path)
    titles = json.loads(titles_json)
    page_text = []

    for page in reader.pages:
        page_text.append(normalize(page.extract_text() or ""))

    result = {}
    for item in titles:
        marker = normalize(f"[[SECTION:{item['id']}]]")
        candidates = [
            normalize(item.get("title", "")),
            normalize(f"{item.get('number', '')}{item.get('shortTitle', '')}"),
            normalize(item.get("shortTitle", "")),
        ]
        candidates = [candidate for candidate in candidates if candidate]

        found_page = None
        for index, text in enumerate(page_text):
            if marker in text:
                found_page = index + 1
                break

        if found_page is None:
            for index, text in enumerate(page_text):
                if index < 5:
                    continue
                if any(candidate in text for candidate in candidates):
                    found_page = index + 1
                    break

        if found_page is None:
            found_page = 1
        result[item["id"]] = found_page

    print(json.dumps(result, ensure_ascii=False))


def finalize_pdf(source_pdf, target_pdf, outline_json):
    source = Path(source_pdf)
    target = Path(target_pdf)
    reader = PdfReader(str(source))
    writer = PdfWriter()

    for page in reader.pages:
        background = make_background_page(float(page.mediabox.width), float(page.mediabox.height))
        background.merge_page(page)
        writer.add_page(background)

    writer.add_metadata(
        {
            "/Title": "天命：马克思与毛泽东在现代中国",
            "/Author": "Nigel Harris",
            "/Subject": "中文译文电子排印版",
            "/Creator": "Codex book PDF builder",
        }
    )

    for item in json.loads(outline_json):
        page_number = max(int(item.get("page") or 1) - 1, 0)
        if page_number < len(writer.pages):
            writer.add_outline_item(item["title"], page_number)

    with target.open("wb") as handle:
        writer.write(handle)

    print(str(target))


def make_background_page(width, height):
    mm = 72 / 25.4
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setFillColorRGB(0.9686, 0.9451, 0.9059)
    c.rect(10 * mm, 20 * mm, width - 20 * mm, height - 38 * mm, stroke=0, fill=1)
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: pdf_finalize.py page-map|finalize ...")

    command = sys.argv[1]
    if command == "page-map":
        build_page_map(sys.argv[2], sys.argv[3])
    elif command == "finalize":
        finalize_pdf(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
