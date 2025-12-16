import re

# Read the file
with open('rag.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace async def with def
content = re.sub(r'\basync def\b', 'def', content)

# Remove await and loop.run_in_executor patterns
# Pattern 1: await loop.run_in_executor(None, lambda: EXPR)
content = re.sub(
    r'await loop\.run_in_executor\(\s*None,\s*lambda:\s*([^\)]+)\)',
    r'\1',
    content
)

# Pattern 2: await loop.run_in_executor(None, lambda x=y: EXPR)
content = re.sub(
    r'await loop\.run_in_executor\(\s*None,\s*lambda\s+[^:]+:\s*([^\)]+)\)',
    r'\1',
    content
)

# Remove loop = asyncio.get_event_loop() lines
content = re.sub(r'\s*loop = asyncio\.get_event_loop\(\)\s*\n', '\n', content)

# Write back
with open('rag.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed async patterns in rag.py")
