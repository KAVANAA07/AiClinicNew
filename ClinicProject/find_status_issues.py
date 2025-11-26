import re

# Read views.py
with open('api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print("=== ALL STATUS CHECKS IN views.py ===\n")

# Find all status-related patterns
patterns = [
    r"status__in=\[([^\]]+)\]",
    r"status=['\"]([^'\"]+)['\"]",
    r"\.exclude\(status",
    r"\.filter\(.*status",
]

for i, line in enumerate(lines, 1):
    for pattern in patterns:
        if re.search(pattern, line):
            print(f"Line {i}: {line.strip()}")
            break
