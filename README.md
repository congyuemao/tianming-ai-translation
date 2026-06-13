# Tianming AI Translation Project / 《天命》AI 自动翻译项目

> Chinese translation workflow archive for Nigel Harris, *The Mandate of Heaven: Marx and Mao in Modern China*.
>
> Nigel Harris《天命：马克思与毛泽东在现代中国》中文翻译流程归档。

This repository keeps the source PDF, chapter-level Markdown drafts, Codex polishing skill, build scripts, and generated PDF/HTML outputs used in the translation project.

本仓库保存该翻译项目使用的原始 PDF、逐章 Markdown 草稿、Codex 润色校对 skill、排版脚本，以及生成后的 PDF/HTML 成品。

## Workflow / 工作流

1. **PDF to Markdown / PDF 转 Markdown**
   - Start from the source PDF.
   - Extract or convert the book text into Markdown.
   - Clean obvious extraction errors before chapter work begins.
   - 以原始 PDF 为底本，将全文抽取或转换为 Markdown，并先清理明显的识别、换行和编码问题。

2. **Chapter Split / 章节拆分**
   - Split the full Markdown into one file per preface, chapter, or afterword under `each_chapter/`.
   - Use ASCII filenames for cross-platform stability, while keeping Chinese headings inside the files.
   - 将全文按序言、章节和回顾拆分到 `each_chapter/`，文件名使用 ASCII，正文内部保留中文标题。

3. **Codex Translation Polish / Codex 润色校对**
   - Use the local skill `skills/book-translation-polish/SKILL.md`.
   - Compare each Chinese draft against the English source.
   - Preserve every substantive claim, date, quotation, note, and citation.
   - Naturalize the Chinese prose so it reads as fluent academic Chinese rather than literal English-shaped Chinese.
   - 使用本地 `book-translation-polish` skill 逐章处理：对照英文原文，补足遗漏，统一注释编号，核查人名和引文，并把中文改写为更自然的学术表达。

4. **Citation, Notes, and Quote Check / 注释与引文复核**
   - Renumber notes from 1 in every standalone chapter file.
   - Translate explanatory note prose into Chinese while preserving bibliographic metadata.
   - For Mao Zedong, party documents, newspapers, and other Chinese-language originals, restore the original Chinese wording when reliably found.
   - 每章注释从 1 重新编号；说明性注释译为中文，书目元数据保留英文；能找到中文原文的毛泽东、党史文件和报刊引文，尽量恢复原文。

5. **Human Review / 人工校对**
   - Human proofreaders review difficult passages, terminology, quotation uncertainty, and stylistic consistency.
   - Items marked as needing original-source verification are revisited manually.
   - 人工校对负责复核疑难段落、术语、引文不确定处和整体风格一致性。

6. **Integration and PDF Build / 整合与 PDF 输出**
   - `tools/build_book_pdf.mjs` collects the chapter Markdown files, renders HTML, creates pagination metadata, and generates a PDF draft.
   - `tools/pdf_finalize.py` finalizes the PDF metadata, background, outlines, and page map.
   - Generated outputs live in `dist/`.
   - 通过 `tools/build_book_pdf.mjs` 汇总章节、生成 HTML、建立页码映射并输出 PDF 草稿；再由 `tools/pdf_finalize.py` 完成 PDF 元数据、背景、目录和页码映射处理；成品位于 `dist/`。

## Repository Layout / 仓库结构

- `each_chapter/` - chapter-level Markdown translation drafts / 逐章中文 Markdown 草稿
- `skills/book-translation-polish/` - local Codex skill for translation polishing / 本项目使用的 Codex 翻译润色 skill
- `tools/` - build and PDF finalization scripts / 构建与 PDF 收尾脚本
- `dist/` - generated HTML, page-map data, table of contents data, and final PDF / 生成的 HTML、页码映射、目录数据和最终 PDF
- `README.md` - bilingual project notes and workflow / 中英双语项目说明

## Build / 构建

The build script expects the bundled Codex runtime dependencies for Node.js and Python packages such as `marked`, `pypdf`, and `reportlab`.

构建脚本依赖 Codex 运行时中提供的 Node.js 与 Python 包，例如 `marked`、`pypdf` 和 `reportlab`。

```powershell
node tools/build_book_pdf.mjs
```

## Notes / 说明

This repository is a translation workflow archive. The original work remains the intellectual property of its author and rights holders.

本仓库是翻译工作流归档。原书版权归原作者及权利方所有。
