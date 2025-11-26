import re

# Read views.py
with open('api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all case-sensitive status checks with case-insensitive ones
replacements = [
    (r"\.exclude\(status__in=\['completed', 'cancelled', 'skipped'\]\)", 
     ".exclude(status__iexact='completed').exclude(status__iexact='cancelled').exclude(status__iexact='skipped')"),
    
    (r"\.exclude\(status__in=\['completed', 'cancelled'\]\)", 
     ".exclude(status__iexact='completed').exclude(status__iexact='cancelled')"),
    
    (r"\.exclude\(status__in=\['cancelled', 'skipped'\]\)", 
     ".exclude(status__iexact='cancelled').exclude(status__iexact='skipped')"),
    
    (r"status__in=\['waiting', 'confirmed'\]", 
     "status__iregex=r'^(waiting|confirmed)$'"),
    
    (r"status__in=\['waiting', 'confirmed', 'in_consultancy'\]", 
     "status__iregex=r'^(waiting|confirmed|in_consultancy)$'"),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write back
with open('api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all case-sensitive status checks")
