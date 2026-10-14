import re, html, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(".")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

# On remplace les img locaux par des data:uri inline pour éviter les problèmes de chemin/protocole.
def img_tag_to_datauri(m):
    s = m.group(0)
    src = (re.search(r'src="([^"]+)"', s) or re.search(r"""src='([^']+)'""", s))
    if not src:
        return s
    src_path = src.group(1)
    if src_path.startswith("http://") or src_path.startswith("https://"):
        return s
    p = ROOT / src_path
    if not p.is_file():
        return s
    try:
        data = p.read_bytes()
        import base64, mimetypes
        ct = mimetypes.guess_type(p.name)[0] or "image/svg+xml"
        b64 = base64.b64encode(data).decode("ascii")
        replacement = f'<img src="data:{ct};base64,{b64}"'
        s2 = re.sub(r'src="[^"]*"', replacement, s, count=1)
        s2 = re.sub(r"""src='[^']*'""", replacement, s2, count=1)
        return s2
    except Exception:
        return s

readme = re.sub(r'<img\s[^>]*>', img_tag_to_datauri, readme)

# Transforme une version grossière du Markdown en HTML.
# (Suffisant pour la prévisualisation du rendu GitHub-like.)
md = readme
md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2" style="max-width:100%;height:auto;display:block;margin:8px 0;"/>', md)
md = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#a78bfa;text-decoration:none;">\1</a>', md)
md = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', md)
md = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', md)
md = re.sub(r'^- ', r'<li>', md)
md = re.sub(r'^- ', r'<li>', md, flags=re.M)
md = re.sub(r'^\*\*Focus\*\*:', r'<li><strong>Focus:</strong>', md)
md = re.sub(r'^\*\*Approche\*\*:', r'<li><strong>Approche:</strong>', md)
md = re.sub(r'^\*\*Basé au\*\*:', r'<li><strong>Basé au:</strong>', md)
md = re.sub(r'^\*\*Langue\*\*:', r'<li><strong>Langue:</strong>', md)
md = re.sub(r'^## (.+)$', r'<h2 style="margin-top:24px;color:#c4b5fd;">\1</h2>', md, flags=re.M)
md = re.sub(r'^### (.+)$', r'<h3 style="margin-top:16px;color:#f5f3ff;">\1</h3>', md, flags=re.M)
md = re.sub(r'^> (.+)$', r'<blockquote style="border-left:3px solid #8B5CF6;color:#d8d4f7;margin:8px 0;padding-left:12px;font-style:italic;background:#0d0a1c;padding:6px 12px;border-radius:4px;">\1</blockquote>', md, flags=re.M)
md = re.sub(r'^<table>', '<table style="border-collapse:collapse;width:100%;margin:12px 0;">', md)
md = re.sub(r'^<tr>', '<tr>', md)
md = re.sub(r'^<td', '<td>', md)
md = re.sub(r'</td>', '</td>', md)
md = re.sub(r'</tr>', '</tr>', md)
md = re.sub(r'^</table>', '</table>', md)
md = re.sub(r'^\|', '', md, flags=re.M)
md = re.sub(r'<td[^>]*width="50%"', r'<td style="vertical-align:top;width:50%;padding:6px 8px;border:1px solid #2a1f4a;"', md)
md = re.sub(r'<td[^>]*valign="top"', r'<td style="vertical-align:top;"', md)
md = re.sub(r'<td[^>]*>\s*', r'<td style="padding:6px 8px;border:1px solid #2a1f4a;">', md)
md = re.sub(r'<h[23][^>]*>', r'\0', md)
md = re.sub(r'<div[^>]*>', r'\0', md)
md = re.sub(r'</div>', '', md)
md = re.sub(r'<!--.*?-->', '', md, flags=re.S)

lines = md.splitlines()
out = ['<!-- README_local_preview -->']
out.append('<meta charset="utf-8">')
out.append('<title>README preview — Vivien Agueounde</title>')
out.append('<style>')
out.append('body { background:#0a060f; color:#e5e7eb; font-family:system-ui,-apple-system,"Segoe UI",Roboto,Inter,sans-serif; line-height:1.6; padding:18px; }')
out.append('a { color:#a78bfa; }')
out.append('img { max-width:100%; }')
out.append('pre, code { font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace; }')
out.append('ul { list-style:none; padding-left:0; }')
out.append('li { margin:4px 0; padding-left:18px; position:relative; }')
out.append('li::before { content:"•"; color:#8B5CF6; position:absolute; left:4px; }')
out.append('</style>')
out.append('<div style="max-width:1100px;margin:0 auto;">')
out.append(md)
out.append('</div>')
page_html = "\n".join(out)

tmp_page = ROOT / "_readme_preview.html"
tmp_page.write_text(page_html, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width":1280,"height":900})
    page.goto(f"file://{tmp_page.resolve().as_posix()}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(600)
    snap = ROOT / "_readme_preview.png"
    page.screenshot(path=snap, full_page=False)
    page.close()
    browser.close()

print("HTML_PREVIEW:", tmp_page)
print("PNG_PREVIEW:", snap)
print("HTML_BYTES:", len(page_html.encode("utf-8")))
print("PNG_BYTES:", snap.stat().st_size)
