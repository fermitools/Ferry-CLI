import sys
import re
import semver

bump_type = sys.argv[1]

# Read current version
with open('ferry_cli/version.py', 'r') as f:
    content = f.read()

match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
if match:
    current_version = match.group(1)
else:
    print("Could not find the current version.")
    sys.exit(1)

# Increment version
version_info = semver.VersionInfo.parse(current_version)
if bump_type == 'major':
    new_version = version_info.bump_major()
elif bump_type == 'minor':
    new_version = version_info.bump_minor()
elif bump_type == 'patch':
    new_version = version_info.bump_patch()
else:
    print(f"Invalid bump type: {bump_type}")
    sys.exit(1)

# Output the new version
print(f"::set-output name=new_version::{new_version}")
