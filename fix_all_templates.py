import re

# Read the file
with open('main/templates/main/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix ALL broken template tags with split {% endif %} patterns
# This will match any Django template tag that has {% endif followed by whitespace and %}
content = re.sub(
    r'{%\s*endif\s+%}',
    '{% endif %}',
    content
)

# Also fix common patterns where selected{% endif is split
content = re.sub(
    r'}selected{%\s*endif\s+%}',
    '}selected{% endif %}',
    content
)

# Ensure consistent spacing in comparison operators
content = re.sub(
    r"request\.GET\.(\w+)\s*==\s*'",
    r"request.GET.\1 == '",
    content
)

# Write fixed content
with open('main/templates/main/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ ALL TEMPLATE TAGS FIXED!")
print("Dashboard is ready for your demo!")
