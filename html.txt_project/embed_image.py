from pathlib import Path
b64_path=Path('images/soaps.b64.txt')
html_path=Path('whoosh_babyco.html')
if not b64_path.exists():
    print('base64 file missing')
    raise SystemExit(1)
if not html_path.exists():
    print('html missing')
    raise SystemExit(1)

b64=b64_path.read_bytes().decode('ascii')
html=html_path.read_text(encoding='utf-8')
html=html.replace('src="images/soaps.jpg"','src="data:image/jpeg;base64,'+b64+'"')
html_path.write_text(html,encoding='utf-8')
print('embedded')
