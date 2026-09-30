from pathlib import Path

b64_path = Path('images/clothes.b64.txt')
html_path = Path('whoosh_babyco.html')

if not b64_path.exists():
    print('clothes base64 file missing:', b64_path)
    raise SystemExit(1)
if not html_path.exists():
    print('html missing:', html_path)
    raise SystemExit(1)

b64 = b64_path.read_bytes().decode('ascii')
html = html_path.read_text(encoding='utf-8')

# Replace the clothes img src by locating the alt attribute
old_prefix = 'alt="Clothes"'
if 'alt="Clothes"' not in html:
    print('Clothes img not found in HTML')
    raise SystemExit(1)

import re

# Match src="..." for the img tag that has alt="Clothes"
pattern = re.compile(r'(\<img\s+src=")[^"]*("\s+alt=\"Clothes\")', re.IGNORECASE)
new_src = 'data:image/webp;base64,' + b64
new_html, n = pattern.subn(r'\1' + new_src + r'\2', html, count=1)
if n == 0:
    print('Failed to replace Clothes src')
    raise SystemExit(1)

html_path.write_text(new_html, encoding='utf-8')
print('embedded clothes b64')
