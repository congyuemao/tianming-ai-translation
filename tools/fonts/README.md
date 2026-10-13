# Embedded reading fonts

`TianmingSerif.woff2` and `TianmingSans.woff2` are character subsets of Noto Serif SC and Noto Sans SC. The primary family names are changed to TianmingSerif and TianmingSans. The original variable weights are retained.

These font derivatives are distributed under SIL Open Font License 1.1. The accompanying files preserve the respective copyright notices and licenses. Upstream license sources:

- https://github.com/google/fonts/blob/main/ofl/notoserifsc/OFL.txt
- https://github.com/google/fonts/blob/main/ofl/notosanssc/OFL.txt

The HTML embeds both fonts and their license notices, so it can be read offline without downloading font assets. The PDF embeds its used glyphs.

After introducing characters that are not present in the existing subsets, regenerate from the full fonts:

```powershell
python tools/subset_fonts.py --font-dir C:/Windows/Fonts
```

The font directory must contain `NotoSerifSC-VF.ttf` and `NotoSansSC-VF.ttf`; the script requires FontTools and Brotli from `requirements.txt`. It never modifies the source fonts.
