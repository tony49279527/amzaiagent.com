"""Keep the main identity pages readable when JavaScript is unavailable.

Reuse the existing footer template; do not maintain a second company identity.
Run after changing the shared footer in js/components.js.
"""

from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
PAGES = ('index.html', 'about.html', 'contact.html', 'privacy.html', 'terms.html')


def main():
    source = (ROOT / 'js/components.js').read_text(encoding='utf-8')
    match = re.search(r'const footerHTML = `(.*?)`;', source, re.S)
    if not match:
        raise SystemExit('Shared footer template not found; no pages changed.')
    footer = match.group(1).strip().replace(
        '${currentYear}', str(datetime.now(timezone.utc).year)
    )
    if '${' in footer:
        raise SystemExit('Unsupported footer expression; no pages changed.')
    pattern = re.compile(
        r'<div id="footer-placeholder">(?:\s*<footer\b.*?</footer>\s*)?</div>', re.S
    )
    updates = []
    for name in PAGES:
        path = ROOT / name
        original = path.read_text(encoding='utf-8')
        updated, count = pattern.subn(
            lambda _: '<div id="footer-placeholder">\n' + footer + '\n    </div>',
            original,
        )
        if count != 1:
            raise SystemExit(f'{name}: expected one footer placeholder; no pages changed.')
        updates.append((path, original, updated))
    for path, original, updated in updates:
        if updated != original:
            path.write_text(updated, encoding='utf-8')
        print(f'{path.name}: static footer ready')


if __name__ == '__main__':
    main()
