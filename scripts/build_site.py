"""Builds site/: the same app running in the browser with stlite (https://github.com/whitphx/stlite).

Run with `uv run python scripts/build_site.py`, then preview with
`uv run python -m http.server -d site` and open http://localhost:8000.
CI runs this and deploys site/ to Firebase Hosting.
"""

import json
import re
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"
STLITE = "1.12.0"  # https://www.npmjs.com/package/@stlite/browser

# The app's own dependencies (from pyproject.toml); stlite installs them in the browser.
# Version pins are dropped: the browser (Pyodide) ships its own builds of packages like pandas.
# Streamlit itself comes with stlite.
dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
    "dependencies"
]
names = [re.split(r"[<>=!~\[ ]", d, maxsplit=1)[0] for d in dependencies]
requirements = [n for n in names if n != "streamlit"]

shutil.rmtree(SITE, ignore_errors=True)
shutil.copytree(ROOT / "data", SITE / "data")
shutil.copy(ROOT / "app.py", SITE / "app.py")
if (ROOT / ".streamlit" / "config.toml").exists():
    shutil.copytree(
        ROOT / ".streamlit",
        SITE / ".streamlit",
        ignore=shutil.ignore_patterns("secrets*"),
    )

files = {"app.py": {"url": "./app.py"}}
for path in sorted(SITE.rglob("*")):
    name = path.relative_to(SITE).as_posix()
    if path.is_file() and name != "app.py":
        files[name] = {"url": f"./{name}"}

(SITE / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Communication-needs Map</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE}/build/stlite.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
      import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE}/build/stlite.js";
      mount(
        {{
          entrypoint: "app.py",
          requirements: {json.dumps(requirements)},
          files: {json.dumps(files, indent=2)},
        }},
        document.getElementById("root"),
      );
    </script>
  </body>
</html>
""")
print(f"Built {SITE} with {len(files)} files")
