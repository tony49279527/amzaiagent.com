
import os
import glob

# Paths
BASE_DIR = 'd:/project/amzaiagent.com'
HTML_FILES = glob.glob(os.path.join(BASE_DIR, '*.html'))

# Mojibake Map (Extracted from index.html patterns)
# These are sequences often resulting from Windows-1252 to UTF-8 confusion
MOJIBAKE_MAP = {
    '鈿狅笍': '⚠️',
    '馃搳': '📂',
    '馃幆': '🎯',
    '馃攳': '🔍',
    '猸愨瓙': '⭐⭐⭐⭐⭐',
    '鈫?': '→',
    '漏': '©',
    '鈥?': '—',
    '钛?': '—',
    '鈥?': '—',
    '猸?': '',
    '鈥?': '—',
    '鉁?': '✅',
    '馃洝锔?': '🛡️',
    '🛡️/div>': '🛡️</div>', # Fix broken tag from previous replace
    '鈿?': '⚙️',            # Gear icon
    '馃敀': '🔒',            # Lock icon
    '馃拵': '💎',             # Diamond icon
    '馃挕': '🛠️',            # Tool icon (Listing Optimization)
    
    # Flags
    '馃嚭馃嚫': '🇺🇸',
    '馃嚚馃嚘': '🇨🇦',
    '馃嚞馃嚙': '🇬🇧',
    '馃嚛馃嚜': '🇩🇪',
    '馃嚝馃嚪': '🇫🇷',
    '馃嚠馃嚬': '🇮🇹',
    '馃嚜馃嚫': '🇪🇸',
    '馃嚡馃嚨': '🇯🇵',

    # Languages
    'Fran莽ais': 'Français',
    'Espa帽ol': 'Español',
    '鏃ユ湰瑾': '日本語',
    '涓枃': '中文',

    # Icons
    '馃挵': '💰',             # Money bag (Pricing)
    '馃殌': '🚀',             # Rocket (Start)
    '馃槫': '😫',             # Pain points face
    '馃摟': '📧',             # Email
    '馃實': '🌐'              # Global/World
}

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        
        for bad, good in MOJIBAKE_MAP.items():
            content = content.replace(bad, good)
            
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {os.path.basename(filepath)}")
        else:
            print(f"Clean: {os.path.basename(filepath)}")
            
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    print("Starting Global Mojibake Remediation...")
    for html_file in HTML_FILES:
        fix_file(html_file)
    print("Completed.")
