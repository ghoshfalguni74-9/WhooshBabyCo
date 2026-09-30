import re
from pathlib import Path

p = Path('whoosh_babyco.html')
if not p.exists():
    print('missing')
    raise SystemExit(1)
s = p.read_text(encoding='utf-8')
new, n = re.subn(r'(src=")data:image/webp;base64,[^\"]+("\s+alt=\"Clothes\")', r'\1images/clothes_test.webp\2', s)
if n:
    p.write_text(new, encoding='utf-8')
    print('replaced', n)
else:
    print('no match')
