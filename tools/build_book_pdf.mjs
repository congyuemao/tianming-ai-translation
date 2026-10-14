import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(toolDir, '..');
const dist = path.join(root, 'dist');
const temp = path.join(root, 'tmp', 'pdfs');
const runtime = process.env.CODEX_RUNTIME_DIR || path.join(process.env.USERPROFILE || process.env.HOME || '', '.cache/codex-runtimes/codex-primary-runtime/dependencies');
const require = createRequire(import.meta.url);
async function dependency(name) {
  try { return await import(name); }
  catch {
    const dirs = [...(process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean), path.join(runtime, 'node/node_modules')];
    return import(pathToFileURL(require.resolve(name, { paths: dirs })).href);
  }
}
const { marked } = await dependency('marked');
const playwrightModule = await dependency('playwright');
const { chromium } = playwrightModule.default || playwrightModule;
const python = process.env.PYTHON || (fs.existsSync(path.join(runtime, 'python/python.exe')) ? path.join(runtime, 'python/python.exe') : 'python3');
marked.setOptions({ gfm: true, breaks: false });
fs.mkdirSync(dist, { recursive: true });
fs.mkdirSync(temp, { recursive: true });
const htmlPath = path.join(dist, 'mandate_of_heaven_zh.html');
const pdfPath = path.join(dist, '天命_马克思与毛泽东在现代中国.pdf');
const draftPath = path.join(temp, 'book-layout.pdf');
const date = process.env.BUILD_DATE || new Intl.DateTimeFormat('en-CA', { timeZone: 'Australia/Sydney', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
const git = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' });
const sourceCommit = git.status === 0 ? git.stdout.trim() : null;
const removedTitles = [];
const chapters = fs.readdirSync(path.join(root, 'each_chapter')).filter(n => n.endsWith('.md')).sort().map((file, index) => {
  const bytes = fs.readFileSync(path.join(root, 'each_chapter', file));
  const raw = bytes.toString('utf8').replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');
  const heading = raw.match(/^\s*#\s+([^\n]+)\n?/);
  if (!heading) throw new Error(`Missing leading H1: ${file}`);
  const title = heading[1].trim();
  let body = raw.slice(heading[0].length).trimStart();
  // Remove only equivalent leading title lines, including "15. 外交政策".
  const titleKey = s => s.replace(/^#{1,6}\s*/, '').replace(/^第\s*\d+\s*章\s*/, '').replace(/^\d+\s*[.、．]\s*/, '').replace(/\s+/g, '').trim();
  while (body && titleKey(body.split('\n')[0]) === titleKey(title)) {
    removedTitles.push({ file, text: body.split('\n')[0] });
    body = body.slice(body.indexOf('\n') < 0 ? body.length : body.indexOf('\n') + 1).trimStart();
  }
  if (/^#\s+/m.test(body)) throw new Error(`Unexpected additional H1 in ${file}`);
  const cm = title.match(/^第(\d+)章\s*(.+)$/);
  const id = `sec-${index + 1}-${file.replace(/\.md$/, '').replaceAll('_', '-')}`;
  return { file, id, title, shortTitle: cm?.[2] || title, number: cm ? `第${cm[1]}章` : '', chapterNumber: cm ? +cm[1] : null, kind: cm || title === '回顾' ? 'chapter' : 'frontmatter', body, sha256: createHash('sha256').update(bytes).digest('hex') };
});
const pending = chapters.reduce((n, c) => n + (c.body.match(/【原文待核】/g) || []).length, 0);
const auditDir = path.join(root, 'reference check');
const auditFile = fs.readdirSync(auditDir)
  .filter(file => /^\d{4}-\d{2}-\d{2}-round\d+\.json$/.test(file))
  .sort((a, b) => Number(b.match(/round(\d+)/)[1]) - Number(a.match(/round(\d+)/)[1]))[0];
if (!auditFile) throw new Error('No citation audit ledger found.');
const audit = JSON.parse(fs.readFileSync(path.join(auditDir, auditFile), 'utf8'));
if (!Number.isInteger(audit.round) || audit.summary.remainingMarkers !== pending) {
  throw new Error(`Citation audit does not match chapter drafts: ${auditFile}`);
}
const citationAudit = { round: audit.round, date: audit.date, ledger: `reference check/${auditFile}`, sha256: createHash('sha256').update(fs.readFileSync(path.join(auditDir, auditFile))).digest('hex') };
fs.writeFileSync(path.join(temp, 'sections.json'), JSON.stringify(chapters.map(({id,title,shortTitle,number}) => ({id,title,shortTitle,number}))));
const expected = chapters.map(c => ({id:c.id,html:marked.parse(c.body)}));
const css = fs.readFileSync(path.join(toolDir, 'book.css'), 'utf8');
const fontCss = [['BookSerif','TianmingSerif.woff2','200 900'],['BookSans','TianmingSans.woff2','100 900']].map(([family,name,weight]) => `@font-face{font-family:${family};src:url(data:font/woff2;base64,${fs.readFileSync(path.join(toolDir,'fonts',name)).toString('base64')}) format('woff2');font-weight:${weight};font-display:block;}`).join('\n');
const licenses = ['OFL-NotoSerifSC.txt','OFL-NotoSansSC.txt'].map(n=>fs.readFileSync(path.join(toolDir,'fonts',n),'utf8').replace(/[ \t]+$/gm,'')).join('\n\n');
const cover = fs.readFileSync(path.join(toolDir,'cover.html'),'utf8');
const escape = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function renderChapter(c) {
  const parts = c.body.split(/^## 注释与引用\s*$/m);
  const prose = parts[0].replace(/\\?\[(\d+)\](?!\()|〔(\d+)〕/g,(match,a,b)=>`<a class="note-ref" id="ref-${c.id}-${a||b}" href="#note-${c.id}-${a||b}" aria-label="注${a||b}">${match.replace(/^\\/,'')}</a>`);
  let body = marked.parse(prose);
  if(parts.length>2) throw new Error(`Multiple endnote sections: ${c.file}`);
  if(parts.length===2) {
    let i=0;
    const notes=marked.parse(parts[1]).replace(/<li>/g,()=>`<li id="note-${c.id}-${++i}">`);
    body+=`<section class="endnotes" aria-label="注释与引用"><h2>注释与引用</h2>${notes}</section>`;
  }
  body=body.replaceAll('【原文待核】','<span class="editor-note">【原文待核】</span>').replaceAll('<p>✦</p>','<div class="section-break" aria-label="分节">✦</div>');
  // Archived sources must remain reachable when the HTML or PDF is downloaded alone.
  const sourceBase=`https://github.com/congyuemao/tianming-ai-translation/blob/${sourceCommit || 'main'}/each_chapter/`;
  body=body.replace(/href="(\.\.\/[^"\s]+)"/g,(_,href)=>`href="${new URL(href,sourceBase).href}"`);
  const label=c.chapterNumber?`CHAPTER ${String(c.chapterNumber).padStart(2,'0')}`:c.title==='回顾'?'RETROSPECT':c.title.includes('序言')?'PREFACE':'READER’S NOTE';
  return `<section id="${c.id}" class="book-section ${c.kind}" aria-labelledby="title-${c.id}"><header class="chapter-opener"><div class="section-label">${label}</div><h1 id="title-${c.id}">${c.number?`<span class="chapter-number">${c.number}</span>`:''}<span class="chapter-title">${escape(c.shortTitle)}</span></h1><div class="opener-rule"></div></header><div class="chapter-body">${body}</div></section>`;
}
function makeHtml(pageMap) {
  const toc=chapters.map(c=>`<li><a href="#${c.id}"><span class="toc-number">${c.chapterNumber?String(c.chapterNumber).padStart(2,'0'):'—'}</span><span class="toc-title">${escape(c.shortTitle)}</span><span class="toc-page">${pageMap?.[c.id]||''}</span></a></li>`).join('\n');
  const nav=chapters.map(c=>`<a href="#${c.id}">${escape(c.title)}</a>`).join('\n');
  return `<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="Nigel Harris《天命：马克思与毛泽东在现代中国》中文译文，现代排印修订版。"><title>天命：马克思与毛泽东在现代中国</title><style>${fontCss}\n${css}</style><!-- Embedded subset fonts: derived from Noto Serif SC and Noto Sans SC.\n${licenses.replaceAll('--','—')}\n--></head><body><a class="skip-link" href="#book-toc">跳到目录</a><nav class="reader-bar" aria-label="阅读导航"><a class="reader-brand" href="#cover">天命<span>THE MANDATE OF HEAVEN</span></a><details class="reader-menu"><summary>章节目录</summary><div class="reader-links">${nav}</div></details></nav><main id="book">${cover}<section class="edition-page" id="edition"><div class="section-label">ABOUT THIS EDITION</div><h1>阅读说明</h1><div class="edition-rule"></div><p class="edition-book">天命：马克思与毛泽东在现代中国</p><p class="edition-original">The Mandate of Heaven:<br>Marx and Mao in Modern China</p><p>Nigel Harris 著</p><div class="edition-text"><p>本版收录两篇序言、读者说明、十九章正文与回顾。各章注释按译稿编号保留，目录与正文注号均可点击跳转。</p><p>本修订版已同步至第 ${audit.round} 轮引文核查。正文仍保留 ${pending} 处“原文待核”标记；已找到对应措辞，不等于其中的历史判断或统计已获独立证实。</p><p>本书是中文翻译工作流的阶段性成果。原书版权归原作者及权利方所有。</p></div><div class="edition-meta"><span>现代排印修订版</span><span>${escape(date)}</span></div></section><nav class="toc-page" id="book-toc" aria-label="全书目录"><div class="section-label">CONTENTS</div><h1>目录</h1><p class="toc-caption"><span>前言与正文</span><span>页码</span></p><ol>${toc}</ol></nav>${chapters.map(renderChapter).join('\n')}</main><a class="back-to-toc" href="#book-toc" aria-label="返回全书目录">目录 ↑</a><script>document.querySelectorAll('.reader-links a').forEach(a=>a.addEventListener('click',()=>a.closest('details').removeAttribute('open')));</script></body></html>`;
}
const browser=await chromium.launch({headless:true,executablePath:findBrowser()});
try {
  const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  let pageMap=null,stable=false;
  for(let pass=1;pass<=4;pass++) {
    fs.writeFileSync(htmlPath,makeHtml(pageMap),'utf8');
    await page.goto(pathToFileURL(htmlPath).href,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    await page.emulateMedia({media:'print'});
    const dom=await inspectPage(page);
    if(dom.errors.length) throw new Error(`HTML validation: ${JSON.stringify(dom.errors)}`);
    fs.writeFileSync(path.join(temp,'dom-validation.json'),JSON.stringify(dom,null,2));
    await page.pdf({path:draftPath,printBackground:true,preferCSSPageSize:true,tagged:true,outline:true});
    const nextMap=runPython(['page-map',draftPath,path.join(temp,'sections.json')]);
    console.log(`Layout pass ${pass}: ${JSON.stringify(nextMap)}`);
    if(pageMap&&JSON.stringify(nextMap)===JSON.stringify(pageMap)){stable=true;break;}
    pageMap=nextMap;
  }
  if(!stable) throw new Error('Pagination did not converge in four passes.');
  const outline=[{id:'cover',title:'封面',page:1},{id:'edition',title:'阅读说明',page:2},{id:'book-toc',title:'目录',page:3},...chapters.map(c=>({id:c.id,title:c.title,page:pageMap[c.id]}))];
  fs.writeFileSync(path.join(temp,'outline.json'),JSON.stringify(outline));
  const pdfReport=runPython(['finalize',draftPath,pdfPath,path.join(temp,'outline.json')]);
  fs.writeFileSync(path.join(dist,'page-map.json'),JSON.stringify(pageMap,null,2)+'\n');
  fs.writeFileSync(path.join(dist,'toc.json'),JSON.stringify(chapters.map(c=>({id:c.id,title:c.title,shortTitle:c.shortTitle,number:c.number,kind:c.kind,page:pageMap[c.id]})),null,2)+'\n');
  fs.writeFileSync(path.join(dist,'build-info.json'),JSON.stringify({sourceCommit,buildDate:date,citationAudit,pendingMarkers:pending,chapters:chapters.map(({body,...c})=>c),removedLeadingTitleEchoes:removedTitles,pageCount:pdfReport.pageCount,format:'160 × 230 mm',paginationStable:true,validation:JSON.parse(fs.readFileSync(path.join(temp,'dom-validation.json'),'utf8'))},null,2)+'\n');
  await page.emulateMedia({media:'screen'});
  await page.screenshot({path:path.join(temp,'html-desktop.png')});
  await page.locator('.cover-page').screenshot({path:path.join(temp,'cover-screen.png')});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(temp,'html-mobile.png')});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('Mobile layout overflows horizontally.');
  console.log(JSON.stringify({html:htmlPath,pdf:pdfPath,...pdfReport,pendingMarkers:pending,removedLeadingTitleEchoes:removedTitles},null,2));
} finally {await browser.close();}
async function inspectPage(page) {
  return page.evaluate(({expected,totalPending})=>{
    const errors=[],normalize=s=>s.normalize('NFKC').replace(/\s+/g,'');
    let noteRefs=0,endnotes=0;
    for(const c of expected){
      const section=document.getElementById(c.id);
      if(section.querySelectorAll('h1').length!==1) errors.push(`${c.id}: title count`);
      const div=document.createElement('div');div.innerHTML=c.html;
      if(normalize(div.textContent)!==normalize(section.querySelector('.chapter-body').textContent)) errors.push(`${c.id}: text changed`);
      for(const a of section.querySelectorAll('.note-ref')){noteRefs++;if(!document.getElementById(a.hash.slice(1))) errors.push(`${c.id}: broken note ${a.hash}`);}
      endnotes+=section.querySelectorAll('.endnotes > ol > li').length;
    }
    const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
    if(new Set(ids).size!==ids.length) errors.push('Duplicate HTML id');
    if(document.querySelectorAll('.chapter-body .editor-note').length!==totalPending) errors.push('Pending marker mismatch');
    for(const a of document.querySelectorAll('a[href^="#"]'))if(!document.getElementById(a.hash.slice(1)))errors.push(`Broken anchor ${a.hash}`);
    return {errors,chapterCount:expected.length,noteRefs,endnotes,pendingMarkers:totalPending,textPreserved:true};
  },{expected,totalPending:pending});
}
function runPython(args){
  const r=spawnSync(python,[path.join(toolDir,'pdf_finalize.py'),...args],{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
  if(r.status!==0)throw new Error(`PDF processing failed: ${r.stdout}\n${r.stderr}`);
  return JSON.parse(r.stdout);
}
function findBrowser(){
  if(process.env.BROWSER_PATH)return process.env.BROWSER_PATH;
  return [path.join(process.env.ProgramFiles||'','Google/Chrome/Application/chrome.exe'),path.join(process.env['ProgramFiles(x86)']||'','Microsoft/Edge/Application/msedge.exe'),'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/google-chrome','/usr/bin/chromium'].find(p=>fs.existsSync(p));
}
