import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");
const chapterDir = path.join(root, "each_chapter");
const distDir = path.join(root, "dist");
const htmlPath = path.join(distDir, "mandate_of_heaven_zh.html");
const draftPdfPath = path.join(distDir, "mandate_of_heaven_zh_draft.pdf");
const pagedPdfPath = path.join(distDir, "mandate_of_heaven_zh_paged.pdf");
const finalPdfPath = path.join(distDir, "天命_马克思与毛泽东在现代中国.pdf");
const pageMapPath = path.join(distDir, "page-map.json");
const tocPath = path.join(distDir, "toc.json");

const nodeModules =
  process.env.NODE_PATH ||
  path.join(
    process.env.USERPROFILE || "C:\\Users\\21161",
    ".cache",
    "codex-runtimes",
    "codex-primary-runtime",
    "dependencies",
    "node",
    "node_modules",
  );
const markedModule = path.join(nodeModules, "marked", "lib", "marked.esm.js");
const { marked } = await import(pathToFileURL(markedModule).href);

marked.setOptions({
  gfm: true,
  breaks: false,
  mangle: false,
  headerIds: false,
});

const chromePath = findChrome();
const pythonPath =
  process.env.PYTHON ||
  path.join(
    process.env.USERPROFILE || "C:\\Users\\21161",
    ".cache",
    "codex-runtimes",
    "codex-primary-runtime",
    "dependencies",
    "python",
    "python.exe",
  );

fs.mkdirSync(distDir, { recursive: true });

const chapters = loadChapters();

await buildOnce(draftPdfPath, null);
const pageMap = readPageMap(draftPdfPath);
fs.writeFileSync(pageMapPath, `${JSON.stringify(pageMap, null, 2)}\n`, "utf8");
await buildOnce(pagedPdfPath, pageMap);
finalizePdf(pagedPdfPath, finalPdfPath, pageMap);

console.log(`HTML: ${htmlPath}`);
console.log(`PDF: ${finalPdfPath}`);

async function buildOnce(pdfPath, pageMap) {
  const html = makeHtml(pageMap);
  fs.writeFileSync(htmlPath, html, "utf8");
  printPdf(htmlPath, pdfPath);
}

function loadChapters() {
  if (!fs.existsSync(chapterDir)) {
    throw new Error(`Missing chapter directory: ${chapterDir}`);
  }

  return fs
    .readdirSync(chapterDir)
    .filter((name) => name.endsWith(".md"))
    .sort((a, b) => a.localeCompare(b, "en"))
    .map((filename, index) => {
      const fullPath = path.join(chapterDir, filename);
      const raw = fs.readFileSync(fullPath, "utf8").replace(/\r\n/g, "\n");
      const titleMatch = raw.match(/^#\s+(.+)$/m);
      if (!titleMatch) {
        throw new Error(`Missing H1 title in ${filename}`);
      }

      const title = titleMatch[1].trim();
      let body = raw.replace(/^#\s+.+\n?/, "").trimStart();
      const bodyLines = body.split("\n");
      if (bodyLines[0]?.trim() === title) {
        body = bodyLines.slice(1).join("\n").trimStart();
      }

      const chapterMatch = title.match(/^第(\d+)章\s+(.+)$/);
      const kind =
        chapterMatch || title === "回顾"
          ? "chapter"
          : filename === "01a_notes_for_reader.md"
            ? "reader-note"
            : "frontmatter";

      const id = `sec-${index + 1}-${slugify(filename.replace(/\.md$/, ""))}`;
      const shortTitle = chapterMatch ? chapterMatch[2] : title;
      const number = chapterMatch ? `第${chapterMatch[1]}章` : "";

      return {
        filename,
        id,
        kind,
        number,
        title,
        shortTitle,
        markdown: body,
      };
    });
}

function makeHtml(pageMap) {
  const tocEntries = chapters.map((chapter) => ({
    id: chapter.id,
    title: chapter.title,
    shortTitle: chapter.shortTitle,
    number: chapter.number,
    kind: chapter.kind,
    page: pageMap?.[chapter.id] || "",
  }));
  fs.writeFileSync(tocPath, `${JSON.stringify(tocEntries, null, 2)}\n`, "utf8");

  const chapterHtml = chapters.map(renderChapter).join("\n");

  return `<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <title>天命：马克思与毛泽东在现代中国</title>
  <style>
${makeCss()}
  </style>
</head>
<body>
${renderCover()}
${renderTitlePage()}
${renderColophon()}
${renderToc(tocEntries)}
${chapterHtml}
</body>
</html>`;
}

function renderCover() {
  return `<section class="cover-page" aria-label="封面">
  <div class="cover-inner">
    <div class="cover-edition">中文译文 · 电子排印版</div>
    <div class="cover-title-block">
      <div class="cover-title-cn">天命</div>
      <div class="cover-title-en">The Mandate of Heaven</div>
      <div class="cover-subtitle">马克思与毛泽东在现代中国</div>
    </div>
    <div class="cover-mark" aria-hidden="true">命</div>
    <div class="cover-author">Nigel Harris</div>
  </div>
</section>`;
}

function renderTitlePage() {
  return `<section class="title-page">
  <div class="title-page-inner">
    <p class="series-line">The Mandate of Heaven</p>
    <h1>天命</h1>
    <p class="subtitle">马克思与毛泽东在现代中国</p>
    <p class="author">Nigel Harris 著</p>
    <p class="edition-note">中文译文 · 专业排印版</p>
  </div>
</section>`;
}

function renderColophon() {
  const generated = new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date());

  return `<section class="colophon-page">
  <h2>排印说明</h2>
  <p>本电子版由 <span class="mono">each_chapter</span> 目录内的 Markdown 章节完整整合排印而成，正文、注释编号及译者校注标记均按源文件保留。</p>
  <p>版式采用 A5 书籍开本、宋体风格正文字体、章首页与目录页分层处理，并写入 PDF 目录书签以便电子阅读。</p>
  <p class="colophon-date">生成日期：${escapeHtml(generated)}</p>
</section>`;
}

function renderToc(entries) {
  const lines = entries
    .map((entry) => {
      const label = entry.number
        ? `<span class="toc-number">${escapeHtml(entry.number)}</span><span class="toc-title">${escapeHtml(entry.shortTitle)}</span>`
        : `<span class="toc-title">${escapeHtml(entry.title)}</span>`;
      return `<li class="toc-item toc-${entry.kind}">
        <a href="#${entry.id}">
          <span class="toc-label">${label}</span>
          <span class="toc-page-number">${entry.page ? escapeHtml(String(entry.page)) : "&nbsp;"}</span>
        </a>
      </li>`;
    })
    .join("\n");

  return `<section id="toc" class="toc-page">
  <h2>目录</h2>
  <ol class="toc-list">
${lines}
  </ol>
</section>`;
}

function renderChapter(chapter) {
  let html = marked.parse(chapter.markdown);
  html = postprocessChapterHtml(html);

  const opener = chapter.number
    ? `<p class="chapter-number">${escapeHtml(chapter.number)}</p><h1>${escapeHtml(chapter.shortTitle)}</h1>`
    : `<h1>${escapeHtml(chapter.title)}</h1>`;

  return `<section id="${chapter.id}" class="book-section ${chapter.kind}">
  <header class="chapter-opener">
    <span class="page-marker">[[SECTION:${chapter.id}]]</span>
    <div class="opener-rule" aria-hidden="true"></div>
    ${opener}
  </header>
  <div class="chapter-body">
${html}
  </div>
</section>`;
}

function postprocessChapterHtml(html) {
  return html
    .replaceAll("<h2>注释与引用</h2>", '<h2 class="notes-heading">注释与引用</h2>')
    .replaceAll("【原文待核】", '<span class="editor-note">【原文待核】</span>')
    .replaceAll("<p>✦</p>", '<div class="section-ornament">✦</div>');
}

function makeCss() {
  const font = (name) => pathToFileURL(path.join("C:\\Windows\\Fonts", name)).href;
  return `
@font-face {
  font-family: "BookSerifSC";
  src: url("${font("NotoSerifSC-VF.ttf")}") format("truetype");
  font-weight: 200 900;
}
@font-face {
  font-family: "BookSansSC";
  src: url("${font("NotoSansSC-VF.ttf")}") format("truetype");
  font-weight: 200 900;
}
@font-face {
  font-family: "LatinSerif";
  src: url("${font("NotoSerif-Regular.ttf")}") format("truetype");
  font-weight: 400;
}
@font-face {
  font-family: "LatinSerif";
  src: url("${font("NotoSerif-Italic.ttf")}") format("truetype");
  font-style: italic;
}

@page {
  size: A5;
  margin: 24mm 10mm 26mm 12mm;
  @top-left {
    content: "天命";
    color: #8b7760;
    font-family: "BookSansSC";
    font-size: 8pt;
    letter-spacing: 0;
  }
  @bottom-center {
    content: counter(page);
    color: #8b7760;
    font-family: "LatinSerif", "BookSerifSC";
    font-size: 8pt;
  }
}
@page :right {
  margin: 24mm 12mm 26mm 10mm;
  @top-left { content: ""; }
  @top-right {
    content: "马克思与毛泽东在现代中国";
    color: #8b7760;
    font-family: "BookSansSC";
    font-size: 8pt;
    letter-spacing: 0;
  }
}
@page cover {
  margin: 0;
  @top-left { content: ""; }
  @top-right { content: ""; }
  @bottom-center { content: ""; }
}
@page title {
  margin: 22mm 20mm;
  @top-left { content: ""; }
  @top-right { content: ""; }
  @bottom-center { content: ""; }
}
@page front {
  margin: 22mm 14mm 20mm;
  @top-left { content: ""; }
  @top-right { content: ""; }
}
@page toc {
  margin: 20mm 12mm 18mm;
  @top-left { content: ""; }
  @top-right { content: ""; }
}

* { box-sizing: border-box; }
html {
  color: #211b16;
  font-family: "BookSerifSC", "Noto Serif SC", SimSun, serif;
  font-size: 10.7pt;
  line-height: 1.86;
}
body {
  margin: 0;
  background: transparent;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
p {
  margin: 0 0 0.82em;
  text-align: justify;
  text-justify: inter-ideograph;
  widows: 2;
  orphans: 2;
}
em, i {
  font-family: "LatinSerif", "BookSerifSC", serif;
  font-style: italic;
}
a {
  color: inherit;
  text-decoration: none;
}

.cover-page {
  page: cover;
  width: 148mm;
  height: 210mm;
  break-after: page;
  background:
    linear-gradient(90deg, rgba(255,255,255,.06), transparent 22%, transparent 78%, rgba(255,255,255,.04)),
    linear-gradient(145deg, #16120f 0%, #2a1713 48%, #6c211d 100%);
  color: #f4ead8;
  overflow: hidden;
  position: relative;
}
.cover-page::before,
.cover-page::after {
  content: "";
  position: absolute;
  inset: 9mm;
  border: 0.35mm solid rgba(211, 171, 96, 0.72);
}
.cover-page::after {
  inset: 13mm;
  border-width: 0.15mm;
  border-color: rgba(244, 234, 216, 0.35);
}
.cover-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  padding: 23mm 18mm 20mm;
  display: flex;
  flex-direction: column;
}
.cover-edition {
  align-self: flex-start;
  border: 0.18mm solid rgba(244, 234, 216, .55);
  padding: 2mm 4mm;
  font-family: "BookSansSC";
  font-size: 8.5pt;
  color: #e8d7b8;
}
.cover-title-block {
  margin-top: 25mm;
}
.cover-title-cn {
  font-size: 44pt;
  font-weight: 800;
  line-height: 1;
}
.cover-title-en {
  margin-top: 5mm;
  font-family: "LatinSerif", serif;
  font-size: 12pt;
  color: #d7b36f;
  text-transform: uppercase;
}
.cover-subtitle {
  margin-top: 9mm;
  max-width: 86mm;
  font-size: 18pt;
  line-height: 1.45;
  font-weight: 600;
}
.cover-mark {
  position: absolute;
  right: -12mm;
  bottom: 18mm;
  color: rgba(244, 234, 216, 0.08);
  font-size: 118mm;
  font-weight: 900;
  line-height: 1;
}
.cover-author {
  margin-top: auto;
  font-family: "LatinSerif", "BookSerifSC", serif;
  font-size: 16pt;
  color: #f1dfbc;
}

.title-page {
  page: title;
  min-height: 166mm;
  break-after: page;
  background: #f7f1e7;
}
.title-page-inner {
  min-height: 166mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}
.series-line {
  margin: 0 0 18mm;
  font-family: "LatinSerif", serif;
  font-size: 9pt;
  color: #8a6d42;
  text-transform: uppercase;
  text-align: center;
}
.title-page h1 {
  margin: 0;
  color: #241711;
  font-size: 38pt;
  font-weight: 800;
  line-height: 1.1;
}
.title-page .subtitle {
  margin: 7mm auto 0;
  max-width: 92mm;
  color: #6b201c;
  font-size: 16pt;
  line-height: 1.45;
  text-align: center;
}
.title-page .author {
  margin: 24mm 0 0;
  font-size: 13pt;
  text-align: center;
}
.edition-note {
  margin: 8mm 0 0;
  color: #8b7760;
  font-family: "BookSansSC";
  font-size: 9pt;
  text-align: center;
}

.colophon-page {
  page: front;
  padding-left: 5mm;
  padding-right: 5mm;
  break-after: page;
}
.colophon-page h2,
.toc-page h2 {
  margin: 0 0 12mm;
  color: #6b201c;
  font-size: 21pt;
  font-weight: 750;
  line-height: 1.3;
}
.colophon-page h2::after,
.toc-page h2::after {
  content: "";
  display: block;
  width: 30mm;
  height: 0.5mm;
  margin-top: 4mm;
  background: #b28a50;
}
.colophon-page p {
  font-size: 10pt;
  line-height: 1.9;
}
.mono {
  font-family: Consolas, "BookSansSC", monospace;
  font-size: 92%;
}
.colophon-date {
  margin-top: 10mm;
  color: #806f5b;
  font-family: "BookSansSC";
}

section.toc-page {
  page: toc;
  padding-left: 5mm;
  padding-right: 5mm;
  break-after: page;
}
.toc-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.toc-item {
  break-inside: avoid;
  margin: 0;
  border-bottom: 0.12mm solid rgba(139, 119, 96, .25);
}
.toc-item a {
  min-height: 7.2mm;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 13mm;
  align-items: baseline;
  gap: 5mm;
  padding: 1.4mm 0;
}
.toc-label {
  min-width: 0;
  display: grid;
  grid-template-columns: 19mm minmax(0, 1fr);
  gap: 3mm;
  align-items: baseline;
}
.toc-frontmatter .toc-label,
.toc-reader-note .toc-label {
  display: block;
  padding-left: 22mm;
}
.toc-number {
  color: #8a6d42;
  font-family: "BookSansSC";
  font-size: 8.8pt;
}
.toc-title {
  overflow-wrap: anywhere;
}
.toc-page-number {
  color: #8a6d42;
  font-family: "LatinSerif", "BookSerifSC";
  text-align: right;
}

.book-section {
  break-before: page;
}
.chapter-opener {
  position: relative;
  min-height: 54mm;
  padding: 12mm 5mm 0;
  break-after: avoid;
}
.page-marker {
  position: absolute;
  left: 0;
  top: 0;
  color: rgba(0, 0, 0, 0);
  font-size: 1px;
  line-height: 1;
  white-space: nowrap;
}
.opener-rule {
  width: 28mm;
  height: 0.55mm;
  margin-bottom: 9mm;
  background: #b28a50;
}
.chapter-number {
  margin: 0 0 2mm;
  color: #8a6d42;
  font-family: "BookSansSC";
  font-size: 10pt;
  text-align: left;
}
.chapter-opener h1 {
  margin: 0;
  color: #241711;
  font-size: 25pt;
  font-weight: 780;
  line-height: 1.35;
  text-align: left;
}
.frontmatter .chapter-opener h1,
.reader-note .chapter-opener h1 {
  color: #6b201c;
  font-size: 23pt;
}
.chapter-body {
  padding-bottom: 4mm;
}
.chapter-body > p,
.chapter-body > h2,
.chapter-body > h3,
.chapter-body > h4,
.section-ornament {
  padding-left: 5mm;
  padding-right: 5mm;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.chapter-body > p:first-child::first-letter {
  color: #6b201c;
  float: left;
  font-size: 2.85em;
  line-height: 0.9;
  padding: 0.09em 0.12em 0 0;
  font-weight: 700;
}
.reader-note .chapter-body > p:first-child::first-letter,
.chapter-body > h2:first-child + p::first-letter,
.chapter-body > .section-ornament + p::first-letter {
  float: none;
  font-size: inherit;
  line-height: inherit;
  padding: 0;
  color: inherit;
  font-weight: inherit;
}
.chapter-body h2 {
  margin: 9mm 0 3.8mm;
  color: #6b201c;
  font-size: 15pt;
  font-weight: 760;
  line-height: 1.45;
  break-after: avoid;
}
.chapter-body h3 {
  margin: 6mm 0 2.8mm;
  color: #4b3a2a;
  font-size: 12.4pt;
  font-weight: 700;
  line-height: 1.45;
  break-after: avoid;
}
.chapter-body h4 {
  margin: 4.8mm 0 2.2mm;
  color: #4b3a2a;
  font-size: 10.8pt;
  font-weight: 700;
  break-after: avoid;
}
.chapter-body .notes-heading {
  margin-top: 11mm;
  padding-top: 5mm;
  border-top: 0.25mm solid rgba(139,119,96,.42);
  color: #6f5b43;
  font-family: "BookSansSC";
  font-size: 11.2pt;
}
.chapter-body ol {
  margin: 0 0 0.5em;
  padding-left: 12.5mm;
  padding-right: 5mm;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.chapter-body li {
  margin: 0 0 0.5em;
  padding-left: 1mm;
  text-align: justify;
}
.notes-heading + ol,
.notes-heading ~ ol {
  color: #45382b;
  font-size: 8.4pt;
  line-height: 1.58;
}
.notes-heading + ol li,
.notes-heading ~ ol li {
  margin-bottom: 0.42em;
}
.section-ornament {
  margin: 8mm 0;
  color: #b28a50;
  font-size: 12pt;
  text-align: center;
}
.editor-note {
  color: #7c4b2d;
  font-family: "BookSansSC";
  font-size: 0.86em;
}
`;
}

function readPageMap(pdfPath) {
  const titles = chapters.map((chapter) => ({
    id: chapter.id,
    title: chapter.title,
    shortTitle: chapter.shortTitle,
    number: chapter.number,
  }));
  const result = spawnSync(
    pythonPath,
    [
      path.join(__dirname, "pdf_finalize.py"),
      "page-map",
      pdfPath,
      JSON.stringify(titles),
    ],
    { encoding: "utf8", cwd: root },
  );

  if (result.status !== 0) {
    throw new Error(`Page map failed:\n${result.stdout}\n${result.stderr}`);
  }

  return JSON.parse(result.stdout);
}

function finalizePdf(sourcePdf, targetPdf, pageMap) {
  const outline = chapters.map((chapter) => ({
    id: chapter.id,
    title: chapter.title,
    page: pageMap[chapter.id],
  }));

  const result = spawnSync(
    pythonPath,
    [
      path.join(__dirname, "pdf_finalize.py"),
      "finalize",
      sourcePdf,
      targetPdf,
      JSON.stringify(outline),
    ],
    { encoding: "utf8", cwd: root },
  );

  if (result.status !== 0) {
    throw new Error(`PDF finalization failed:\n${result.stdout}\n${result.stderr}`);
  }
}

function printPdf(sourceHtml, targetPdf) {
  if (fs.existsSync(targetPdf)) {
    fs.unlinkSync(targetPdf);
  }

  const userDataDir = path.join(distDir, `.chrome-profile-${Date.now()}`);
  const args = [
    "--headless=new",
    "--disable-gpu",
    "--disable-extensions",
    "--allow-file-access-from-files",
    `--user-data-dir=${userDataDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--print-to-pdf-no-header",
    "--no-pdf-header-footer",
    `--print-to-pdf=${targetPdf}`,
    pathToFileURL(sourceHtml).href,
  ];

  const result = spawnSync(chromePath, args, {
    cwd: root,
    encoding: "utf8",
    timeout: 120000,
  });

  fs.rmSync(userDataDir, { recursive: true, force: true });

  if (result.status !== 0 || !fs.existsSync(targetPdf)) {
    throw new Error(`Chrome PDF generation failed:\n${result.stdout}\n${result.stderr}`);
  }
}

function findChrome() {
  const candidates = [
    path.join(process.env.ProgramFiles || "", "Google", "Chrome", "Application", "chrome.exe"),
    path.join(process.env["ProgramFiles(x86)"] || "", "Google", "Chrome", "Application", "chrome.exe"),
    path.join(process.env.LOCALAPPDATA || "", "Google", "Chrome", "Application", "chrome.exe"),
    path.join(process.env.ProgramFiles || "", "Microsoft", "Edge", "Application", "msedge.exe"),
    path.join(process.env["ProgramFiles(x86)"] || "", "Microsoft", "Edge", "Application", "msedge.exe"),
  ];
  const found = candidates.find((candidate) => candidate && fs.existsSync(candidate));
  if (!found) {
    throw new Error("Could not find Chrome or Edge for PDF printing.");
  }
  return found;
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
