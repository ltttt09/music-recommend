import os
BASE = r"D:\codexProject\music-recommender\frontend\src"

# Helper - write content ensuring no shell mangling
def w(rel, content):
    path = os.path.join(BASE, rel)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {rel}")

# All files defined right here using Python raw strings
# No PowerShell involved in content definition
