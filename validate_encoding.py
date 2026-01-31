#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-commit hook to validate UTF-8 encoding and detect Mojibake
Usage: Copy this file to .git/hooks/pre-commit and make it executable
"""

import sys
import re
from pathlib import Path

# Common Mojibake patterns (Windows-1252 → UTF-8 double encoding)
MOJIBAKE_PATTERNS = [
    r'馃',  # Emoji corruption prefix
    r'鈥',  # En dash corruption
    r'鈿',  # Gear/Warning corruption
    r'鏃',  # Japanese corruption
    r'涓',  # Chinese corruption
    r'Fran莽ais',  # French accents
    r'Espa帽ol',  # Spanish ñ
]

def check_file_encoding(filepath):
    """Check if file is valid UTF-8 and detect Mojibake"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for Mojibake patterns
        for pattern in MOJIBAKE_PATTERNS:
            if re.search(pattern, content):
                return False, f"Mojibake detected: {pattern}"
        
        return True, "OK"
    except UnicodeDecodeError as e:
        return False, f"Not valid UTF-8: {e}"

def main():
    """Main validation function"""
    # Get staged files
    import subprocess
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True,
        text=True
    )
    
    staged_files = result.stdout.strip().split('\n')
    
    # Check only text files
    text_extensions = {'.html', '.css', '.js', '.py', '.md', '.txt', '.json'}
    errors = []
    
    for filepath in staged_files:
        if not filepath:
            continue
            
        path = Path(filepath)
        if path.suffix in text_extensions and path.exists():
            is_valid, message = check_file_encoding(filepath)
            if not is_valid:
                errors.append(f"{filepath}: {message}")
    
    if errors:
        print("❌ Encoding validation failed!")
        print("\n".join(errors))
        print("\n💡 Run 'python fix_all_mojibake.py' to fix these issues")
        return 1
    
    print("✅ All files passed UTF-8 validation")
    return 0

if __name__ == '__main__':
    sys.exit(main())
