
import os
import re

MOJIBAKE_MAP = {
    '鈿狅笍': '⚠️',
    '馃搳': '📂',
    '馃幆': '🎯',
    '馃攳': '🔍',
    '猸愨瓙': '⭐⭐⭐⭐⭐',
    '鈫?': '→',
    '漏': '©'
}

def clean_file(path, is_index=False):
    if not os.path.exists(path):
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Nav Replacement
        # Matches <nav class="navbar" ... > ... </nav>
        content = re.sub(r'(?s)<nav class="navbar".*?</nav>', '<div id="navbar-placeholder"></div>', content)

        # 2. Footer Replacement
        # Matches <footer class="footer" ... > ... </footer>
        content = re.sub(r'(?s)<footer class="footer".*?</footer>', '<div id="footer-placeholder"></div>', content)

        # 3. Add Script
        if "js/components.js" not in content:
            content = content.replace("</body>", "<script src='js/components.js'></script>\n</body>")

        # 4. Mojibake Fix (Index only)
        if is_index:
            for bad, good in MOJIBAKE_MAP.items():
                content = content.replace(bad, good)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {path}")

    except Exception as e:
        print(f"Error {path}: {e}")

base = "d:/project/amzaiagent.com"
files = [f for f in os.listdir(base) if f.endswith('.html')]

for f in files:
    clean_file(os.path.join(base, f), is_index=(f == "index.html"))
