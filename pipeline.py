import json
import sys
from pathlib import Path
from google.genai import errors
from extract import extract_invoice, MIME_TYPES
from validate import validate_invoice

def output_dirs(input_dir):
    """Each input folder gets its own results, e.g. output/invoices_scanned/approved."""
    base = Path("output") / input_dir.name
    return base / "approved", base / "needs_review"

def already_processed(invoice_id, approved_dir, review_dir):
    filename = f"{invoice_id}.json"
    return (approved_dir / filename).exists() or (review_dir / filename).exists()

def process_invoice(file_path, approved_dir, review_dir):
    invoice_id = file_path.stem  # "INV-1001.jpg" -> "INV-1001"

    if already_processed(invoice_id, approved_dir, review_dir):
        print(f"SKIP     {invoice_id} (already processed)")
        return "skipped"

    data = extract_invoice(str(file_path))
    issues = validate_invoice(data)

    result = {
        "source_file": file_path.name,
        "extracted": data,
        "issues": issues,
    }

    if issues:
        folder, status = review_dir, "needs_review"
        print(f"REVIEW   {invoice_id}: {len(issues)} issue(s)")
        for issue in issues:
            print(f"           - {issue}")
    else:
        folder, status = approved_dir, "approved"
        print(f"APPROVED {invoice_id}: total ${data['total']:.2f}")

    (folder / f"{invoice_id}.json").write_text(json.dumps(result, indent=2))
    return status

def run(input_dir):
    if not input_dir.is_dir():
        print(f"Folder not found: {input_dir}")
        return

    approved_dir, review_dir = output_dirs(input_dir)
    approved_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in MIME_TYPES)
    print(f"Found {len(files)} invoice(s) in {input_dir}/\n")

    counts = {"approved": 0, "needs_review": 0, "skipped": 0, "failed": 0}
    for file_path in files:
        try:
            status = process_invoice(file_path, approved_dir, review_dir)
        except errors.ClientError as e:
            if e.code == 429:
                print(f"\nSTOPPED  Daily API limit reached at {file_path.stem}.")
                print("         Run again later. Finished invoices will be skipped.")
                break
            print(f"FAILED   {file_path.stem}: {e}")
            status = "failed"
        except Exception as e:
            print(f"FAILED   {file_path.stem}: {e}")
            status = "failed"
        counts[status] += 1

    print(f"\nDone. Approved: {counts['approved']}, "
          f"Needs review: {counts['needs_review']}, "
          f"Skipped: {counts['skipped']}, "
          f"Failed: {counts['failed']}")

if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("invoices")
    run(folder)
