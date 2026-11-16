"""Record installed Conda packages and copy their license notices."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

prefix, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=True)
packages = []
for record_path in sorted((prefix / "conda-meta").glob("*.json")):
    record = json.loads(record_path.read_text(encoding="utf-8"))
    packages.append({key: record.get(key) for key in ("name", "version", "build", "url", "sha256", "license")})
    source = record.get("link", {}).get("source")
    if source:
        licenses = Path(source) / "info" / "licenses"
        if licenses.is_dir():
            shutil.copytree(licenses, output / "licenses" / record["name"], dirs_exist_ok=True)
(output / "conda-packages.json").write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")
with (output / "python-packages.txt").open("w", encoding="utf-8") as file:
    subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=file, check=True)
