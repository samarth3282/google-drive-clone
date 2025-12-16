import re

# Read the file
with open('rag.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix: Remove lines that are just whitespace + closing paren + closing paren
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this line is just whitespace + )
    if re.match(r'^\s+\)\s*$', line) and i > 0:
        prev_line = lines[i-1]
        # Check if previous line also ends with )
        if re.search(r'\)\s*$', prev_line):
            # This is likely a duplicate ), skip it
            print(f"Removing duplicate ) at line {i+1}")
            i += 1
            continue
    fixed_lines.append(line)
    i += 1

# Write back
with open('rag.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f"Fixed {len(lines) - len(fixed_lines)} duplicate closing parentheses")
