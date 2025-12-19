#!/usr/bin/env python3
"""Quick script to remove emoji characters from test file"""

import sys

replacements = {
    '📋': '[*]',
    '🎯': '[>]',
    '🔄': '[~]',
    '✅': '[OK]',
    '🛑': '[STOP]',
    '⚠️': '[WARN]',
    '⚠': '[WARN]',  # Alternative warning
    '📊': '[CHART]',
    '✓': '[+]',
    '✗': '[-]',
    '🎉': '[PASS]',
    '❌': '[FAIL]',
    '📤': '[OUT]',
    '⏳': '[WAIT]',
    '🔑': '[KEY]',
}

try:
    with open('test_integration.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        for emoji, ascii_char in replacements.items():
            line = line.replace(emoji, ascii_char)
        new_lines.append(line)
    
    with open('test_integration.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ Replaced emojis in {len(new_lines)} lines")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
