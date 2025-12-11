import re

# Read the file
with open('main/templates/main/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all broken template tags
# Pattern 1: Split {% endif %} tags
content = re.sub(
    r'{%\s*if\s+request\.GET\.sort\s*==\s*[\'"]default[\'"]\s+or\s+not\s+request\.GET\.sort\s*%}selected{%\s*endif\s+%}',
    "{% if request.GET.sort == 'default' or not request.GET.sort %}selected{% endif %}",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'{%\s*if\s+request\.GET\.sort\s*==\s*[\'"]priority[\'"]\s*%}selected{%\s*endif\s+%}',
    "{% if request.GET.sort == 'priority' %}selected{% endif %}",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'{%\s*if\s+request\.GET\.category\s*==\s*[\'"]School[\'"]\s*%}selected{%\s*endif\s+%}',
    "{% if request.GET.category == 'School' %}selected{% endif %}",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'{%\s*if\s+request\.GET\.category\s*==\s*[\'"]Personal[\'"]\s*%}selected{%\s*endif\s+%}',
    "{% if request.GET.category == 'Personal' %}selected{% endif %}",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'{%\s*if\s+request\.GET\.category\s*==\s*[\'"]Work[\'"]\s*%}selected{%\s*endif\s+%}',
    "{% if request.GET.category == 'Work' %}selected{% endif %}",
    content,
    flags=re.DOTALL
)

# Write fixed content
with open('main/templates/main/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ DASHBOARD FIXED!")
