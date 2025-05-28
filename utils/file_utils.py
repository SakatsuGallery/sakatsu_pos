import csv
import json
from pathlib import Path

def ensure_dir(path):
    """Ensure the directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

def load_json(path_or_file):
    """Load JSON data from a file path or file-like object."""
    if hasattr(path_or_file, "read"):
        return json.load(path_or_file)
    with open(path_or_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    """Save a Python object as JSON to the given file path."""
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_csv(path):
    """Load CSV file and return a list of rows."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)

def save_csv(path_or_buffer, rows=None):
    """Save rows to a CSV file or return a CSV writer for a buffer."""
    if rows is None:
        # buffer mode: return writer
        return csv.writer(path_or_buffer)
    # file mode: write rows to disk
    output_path = Path(path_or_buffer)
    ensure_dir(output_path.parent)
    with open(path_or_buffer, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
