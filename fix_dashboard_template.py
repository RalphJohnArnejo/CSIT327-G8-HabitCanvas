#!/usr/bin/env python3
"""
Quick script to fix the broken Django template tag in dashboard.html
"""

import os

file_path = r"c:\Users\Ryle Fritz\CSIT327-G8-HabitCanvas\main\templates\main\dashboard.html"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken template tag
old_text = """                    <option value="default" {% if request.GET.sort=='default' or not request.GET.sort %}selected{% endif
                        %}>Default</option>"""

new_text = """                    <option value="default" {% if request.GET.sort == 'default' or not request.GET.sort %}selected{% endif %}>Default</option>"""

if old_text in content:
    content = content.replace(old_text, new_text)
    print("Found and replaced broken template tag!")
else:
    print("Pattern not found - checking line-by-line...")
    print("File might already be fixed or pattern is different")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File has been written successfully!")
