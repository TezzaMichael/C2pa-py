import subprocess
import json
import csv
import sys
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# --- CONFIGURAZIONE ---
DATASET_DIR = Path("C2PA_Dataset")
OUTPUT_CSV = "trust_comparison.csv"
OUTPUT_HTML = "trust_report.html"

# Argomenti per la validazione Trust
TRUST_ARGS = [
    "--trust_anchors", "https://contentcredentials.org/trust/anchors.pem",
    "--allowed_list", "https://contentcredentials.org/trust/allowed.sha256.txt",
    "--trust_config", "https://contentcredentials.org/trust/store.cfg",
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".mov", ".mp4", ".dng", ".avi", ".mp3", ".wav", ".pdf", ".heic", ".m4a", ".avif", ".gif", ".heif", ".TIF"}

def run_json(cmd):
    """Run a command and parse its JSON output."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        # not a valid manifest or tool error
        return {"validation_state": "ERROR_TOOL_FAILED"}
    except json.JSONDecodeError:
        return {"validation_state": "ERROR_JSON_PARSE"}
    except Exception:
        return {"validation_state": "ERROR_GENERIC"}

def get_validation_state(data):
    """Extract validation state from tool output."""
    return data.get("validation_state", "MISSING")

def generate_html_report(rows, stats, folder_stats):
    """Generate a HTML report."""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C2PA Validation Comparison Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f9; }}
            h1 {{ color: #333; }}
            .summary-box {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; text-align: center; }}
            .card h2 {{ margin: 0; font-size: 36px; color: #007bff; }}
            .card p {{ margin: 5px 0 0; color: #666; font-weight: bold; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #007bff; color: white; }}
            tr:hover {{ background-color: #f1f1f1; }}
            
            .status-Correct {{ color: green; font-weight: bold; }}
            .status-Mismatch {{ color: red; font-weight: bold; }}
            
            .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; color: white; font-weight: bold; }}
            .badge-Valid {{ background-color: #28a745; }}
            .badge-Invalid {{ background-color: #dc3545; }}
            .badge-Trusted {{ background-color: #17a2b8; }}
            .badge-ERROR_TOOL_FAILED {{ background-color: #6c757d; }}
            .badge-MISSING {{ background-color: #ffc107; color: black; }}

            .folder-header {{ background-color: #e9ecef; font-weight: bold; color: #495057; }}
        </style>
    </head>
    <body>
        <h1>C2PA Tool Comparison Report</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="summary-box">
            <div class="card">
                <h2>{stats['total']}</h2>
                <p>Total Files</p>
            </div>
            <div class="card">
                <h2 style="color: green;">{stats['correct']}</h2>
                <p>Matches (Correct)</p>
            </div>
            <div class="card">
                <h2 style="color: { 'red' if stats['mismatch'] > 0 else 'green' };">{stats['mismatch']}</h2>
                <p>Mismatches</p>
            </div>
            <div class="card">
                <h2>{stats['accuracy']:.2f}%</h2>
                <p>Accuracy</p>
            </div>
        </div>

        <h2>Folder Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Folder</th>
                    <th>Files</th>
                    <th>Matches</th>
                    <th>Mismatches</th>
                    <th>Accuracy</th>
                </tr>
            </thead>
            <tbody>
    """

    for folder, s in folder_stats.items():
        accuracy = (s['correct'] / s['total']) * 100 if s['total'] > 0 else 0
        html_content += f"""
                <tr>
                    <td><b>{folder}</b></td>
                    <td>{s['total']}</td>
                    <td>{s['correct']}</td>
                    <td style="color: {'red' if s['mismatch'] > 0 else 'inherit'}">{s['mismatch']}</td>
                    <td>{accuracy:.1f}%</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>

        <h2>Detailed Comparison</h2>
        <table>
            <thead>
                <tr>
                    <th>Image Path</th>
                    <th>Rust State</th>
                    <th>Python State</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
    """

    for row in rows:
        path, rust, py, res = row
        res_class = "status-Correct" if res == "Correct" else "status-Mismatch"
        
        # Helper per badge
        def badge(val):
            cls = f"badge-{val}" if val in ["Valid", "Invalid", "Trusted"] else "badge-ERROR_TOOL_FAILED"
            return f'<span class="badge {cls}">{val}</span>'

        html_content += f"""
                <tr>
                    <td>{path}</td>
                    <td>{badge(rust)}</td>
                    <td>{badge(py)}</td>
                    <td class="{res_class}">{res}</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n HTML Report written to: {os.path.abspath(OUTPUT_HTML)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_result.py <PATH> ")
        sys.exit(1)
    
    if not Path(sys.argv[1]).exists():
        print(f"Error: Dataset directory '{sys.argv[1]}' not found.")
        return

    print(f"Starting comparison on '{sys.argv[1]}'...\n")
    rows = []
    
    # Global result
    stats = {"total": 0, "correct": 0, "mismatch": 0}
    # Folder result
    folder_stats = defaultdict(lambda: {"total": 0, "correct": 0, "mismatch": 0})

    files = sorted([f for f in Path(sys.argv[1]).rglob("*") if f.suffix.lower() in IMAGE_EXTS])

    for i, image in enumerate(files):
        relative_path = image.relative_to(Path(sys.argv[1]))
        folder_name = relative_path.parts[0] if len(relative_path.parts) > 1 else "Root"
        
        # Progress bar
        print(f"[{i+1}/{len(files)}] Processing: {relative_path}", end="\r")

        # --- Rust / c2patool ---
        rust_cmd = ["c2patool", str(image), "trust"] + TRUST_ARGS
        rust_json = run_json(rust_cmd)
        rust_state = get_validation_state(rust_json)

        # --- Python implementation ---
        # py_cmd = ["python3", "c2pa-py.py", str(image), "trust"] + TRUST_ARGS
        py_cmd = [sys.executable, "commands/trust.py", str(image)]
        py_json = run_json(py_cmd)
        py_state = get_validation_state(py_json)

        is_correct = (rust_state == py_state)
        result_str = "Correct" if is_correct else "Not Correct"

        # update stats
        stats["total"] += 1
        folder_stats[folder_name]["total"] += 1
        
        if is_correct:
            stats["correct"] += 1
            folder_stats[folder_name]["correct"] += 1
        else:
            stats["mismatch"] += 1
            folder_stats[folder_name]["mismatch"] += 1

        rows.append([str(relative_path), rust_state, py_state, result_str])

    # Accuracy calculation
    stats["accuracy"] = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0

    print(f"\n\n{'='*60}")
    print(f"COMPARISON COMPLETED")
    print(f"{'='*60}")
    print(f"Total Files: {stats['total']}")
    print(f"Matches:     {stats['correct']}")
    print(f"Mismatches:  {stats['mismatch']}")
    print(f"Accuracy:    {stats['accuracy']:.2f}%")
    print(f"{'='*60}\n")

    # Print folder breakdown
    print(f"{'FOLDER':<30} | {'FILES':<6} | {'MATCH':<6} | {'ACCURACY':<8}")
    print("-" * 60)
    for folder, s in sorted(folder_stats.items()):
        acc = (s['correct'] / s['total']) * 100 if s['total'] > 0 else 0
        print(f"{folder:<30} | {s['total']:<6} | {s['correct']:<6} | {acc:.1f}%")
    print("-" * 60)

    # CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Image", "Rust_validation", "Python_validation", "Result"])
        writer.writerows(rows)
    print(f"\n CSV Data written to: {OUTPUT_CSV}")

    # HTML
    generate_html_report(rows, stats, folder_stats)

if __name__ == "__main__":
    main()