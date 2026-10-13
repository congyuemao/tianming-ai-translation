"""Create portable WOFF2 subsets; never rewrite the installed source fonts."""
import argparse
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--font-dir', type=Path, default=Path('C:/Windows/Fonts'))
args = parser.parse_args()
text = ''.join(p.read_text(encoding='utf-8') for p in (root / 'each_chapter').glob('*.md'))
text += ''.join(p.read_text(encoding='utf-8') for p in (root / 'tools').glob('*') if p.suffix in {'.mjs', '.css', '.html'})
text += ''.join(chr(i) for i in range(32, 127)) + '↑—×‘’“”'
out = root / 'tools/fonts'
out.mkdir(parents=True, exist_ok=True)
for source, name in [('NotoSerifSC-VF.ttf','TianmingSerif'),('NotoSansSC-VF.ttf','TianmingSans')]:
    font = TTFont(args.font_dir / source)
    options = subset.Options()
    options.flavor = 'woff2'
    options.name_IDs = ['*']
    options.name_legacy = True
    options.name_languages = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(text=text)
    sub.subset(font)
    # Give the derivative a distinct primary family name.
    for record in font['name'].names:
        if record.nameID in (1, 4, 6, 16):
            record.string = name.encode(record.getEncoding())
    font.flavor = 'woff2'
    font.save(out / f'{name}.woff2')
    print(name, (out / f'{name}.woff2').stat().st_size)
