import subprocess
import json
import csv
from pathlib import Path

DATASET_DIR = Path("C2PA_Dataset")
OUTPUT_CSV = "trust_comparison.csv"

TRUST_ARGS = [
    "--trust_anchors", "https://contentcredentials.org/trust/anchors.pem",
    "--allowed_list", "https://contentcredentials.org/trust/allowed.sha256.txt",
    "--trust_config", "https://contentcredentials.org/trust/store.cfg",
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".mov", ".mp4", ".dng", ".avi", ".mp3", ".wav", ".pdf", ".heic", ".m4a", ".avif", ".gif", ".heif", ".TIF"}

def run_json(cmd):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception:
        return {"validation_state": "ERROR"}

def get_validation_state(data):
    return data.get("validation_state", "MISSING")

rows = []

for image in DATASET_DIR.rglob("*"):
    if image.suffix.lower() not in IMAGE_EXTS:
        continue

    relative_path = image.relative_to(DATASET_DIR)
    print(f"Processing: {relative_path}")

    # --- Rust / c2patool ---
    rust_cmd = ["c2patool", str(image), "trust"] + TRUST_ARGS
    rust_json = run_json(rust_cmd)
    rust_state = get_validation_state(rust_json)

    # --- Python implementation ---
    #py_cmd = ["python3.12", "c2pa_py.py", str(image), "trust"] + TRUST_ARGS
    py_cmd = ["python3.12", "trust.py", str(image)]
    py_json = run_json(py_cmd)
    py_state = get_validation_state(py_json)

    result = "Correct" if rust_state == py_state else "Not Correct"

    rows.append([
        str(relative_path),
        rust_state,
        py_state,
        result
    ])

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Image",
        "Rust_validation",
        "Python_validation",
        "Result"
    ])
    writer.writerows(rows)

print(f"\n✅ CSV written to {OUTPUT_CSV}")