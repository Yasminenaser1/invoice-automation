import json
from pathlib import Path
from db import get_connection, save_invoice

# Folder names on disk -> status names in the database
STATUS_MAP = {"approved": "auto_approved", "needs_review": "needs_review"}

def main():
    saved = skipped = 0
    with get_connection() as conn:
        for test_dir in sorted(Path("output").iterdir()):
            if not test_dir.is_dir():
                continue
            for folder, status in STATUS_MAP.items():
                for path in sorted((test_dir / folder).glob("*.json")):
                    result = json.loads(path.read_text())
                    was_saved = save_invoice(
                        conn, test_dir.name, path.stem, result["source_file"],
                        status, result["extracted"], result["issues"],
                    )
                    if was_saved:
                        saved += 1
                        print(f"SAVED    {test_dir.name}/{path.stem} as {status}")
                    else:
                        skipped += 1
                        print(f"EXISTS   {test_dir.name}/{path.stem} (already in database)")
    print(f"\nDone. Saved: {saved}, Already in database: {skipped}")

if __name__ == "__main__":
    main()
