from pathlib import Path
import re

html_path = Path('whoosh_babyco.html')
out_path = Path('images/clothes_test.webp')

if not html_path.exists():
    print('html missing')
    raise SystemExit(1)

html = html_path.read_text(encoding='utf-8')
# find img tag with alt="Clothes"
m = re.search(r'<img\s+src="([^"]+)"\s+alt="Clothes"', html)
if not m:
    print('Clothes img tag not found')
    raise SystemExit(1)
src = m.group(1)
if src.startswith('data:'):
    # data:[mime];base64,DATA
    parts = src.split(',',1)
    if len(parts) != 2:
        print('invalid data uri')
        raise SystemExit(1)
    b64 = parts[1]
    out_path.write_bytes(b64.encode('ascii'))
    # write binary decode to verify
    import base64
    try:
        out_path.write_bytes(base64.b64decode(b64))
        print('wrote', out_path, 'size', out_path.stat().st_size)
    except Exception as e:
        print('decode failed', e)
        raise
else:
    print('Clothes src is not data URI:', src)
