import sys
import re

new_version = sys.argv[1]

# Update ferry_cli/version.py
with open('ferry_cli/version.py', 'r') as f:
    content = f.read()

def replace_version(match):
    return f'{match.group(1)}{new_version}{match.group(2)}'

pattern = r'(__version__\s*=\s*")[^"]+(")'
new_content = re.sub(pattern, replace_version, content)

with open('ferry_cli/version.py', 'w') as f:
    f.write(new_content)
