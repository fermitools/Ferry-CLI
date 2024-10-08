from ast import Tuple
import bisect
import sys
import re
from typing import List, Tuple
import typing
from packaging import version

sorted_versions = []
new_version = sys.argv[1]
file_path = sys.argv[2] if len(sys.argv) > 2 else '.spack/package.py'
# Prepare the new preferred line
# Compare new version with the current latest
new_ver_obj = version.parse(new_version)
new_version_line = f'\tversion("{new_version}", tag="{new_version}", preferred=True)'


version_pattern = re.compile(r'version\("(?P<ver>[0-9]+\.[0-9]+\.[0-9]+)", tag="(?P<tag>[0-9]+\.[0-9]+\.[0-9]+)"(, preferred=True)?\)')
version_lines = []
latest_version_line = None
latest_version = None
maintainers_line = -1
depends_on_line = -1

existing_versions = set()
def insert_version(version: version.Version, line: str):
    """
    Inserts the version and associated string into the sorted list.
    """
    # Find the correct position to insert the tuple
    if version in existing_versions:
        # Find and remove the old version from the sorted list
        for i, (v, l) in enumerate(sorted_versions):
            if v == version:
                del sorted_versions[i]
                break
    existing_versions.add(version)
    bisect.insort(sorted_versions, (version, line))
    
    
def get_sorted_versions() -> List[Tuple[version.Version, str]]:
    """
    Returns the sorted list of versions and corresponding strings.
    """
    return sorted_versions 
    
with open(file_path, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    match = version_pattern.match(line.strip())
    if line.strip().startswith('maintainers = '):
        maintainers_line = i
    if line.strip().startswith('depends_on("python@3.6.8:'):
        depends_on_line = i
    if match:
        ver_str = match.group('ver')
        ver_obj = version.parse(ver_str)
        if 'preferred=True' in line:
            latest_version_line = str(line)
            latest_version = ver_obj
        
        insert_version(ver_obj, f'\t{line.replace(", preferred=True", "").strip()}')

if latest_version and new_ver_obj == latest_version:
    print(f"No update needed. Current latest version is {latest_version}.")
    sys.exit(0)
elif maintainers_line + depends_on_line > -2:
    insert_version(new_ver_obj, new_version_line)
    new_content = f'\n\tversion("latest", branch="master")\n'
    for i, (v, line) in enumerate(get_sorted_versions()):
        new_content += f"{line}\n"
    # Replace lines between maintainers and depends_on
    new_lines = lines[:maintainers_line + 1]  # Keep everything up to and including the maintainers line
    new_lines.append(new_content + "\n")      # Add the new content
    new_lines.extend(lines[depends_on_line:]) # Keep everything from depends_on onward
        

    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

print(f"Updated file with new version {new_version}.")