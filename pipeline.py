import sys
from pathlib import Path
from google.genai import errors
from extract import extract_invoice, MIME_TYPES
from validate import validate_invoice
from db import get_connection, invoice_exists, save_invoice

def process_invoice(conn, test_set, file_path):
    invoice_id = file_path.stem  # "INV-1001.jpg" -> "INV-1001"

    if invoice_exists(conn, test_set, invoice_id):
        print(f"SKIP     {invoice_id} (already in database)")
        return "skipped"

    data = extract_invoice(str(file_path))
    issues = validate_invoice(data)
    status = "needs_review" if issues else "auto_approved"

    save_invoice(conn, test_set, invoice_id, file_path.name, status, data, issues)
    conn.commit()  # save each invoice right away, so a later failure can't undo it

    if issues:
        print(f"REVIEW   {invoice_id}: {len(issues)} issue(s)")
        for issue in issues:
            print(f"           - {issue}")
    else:
        print(f"APPROVED {invoice_id}: total ${data['total']:.2f}")
    return status

def run(input_dir):
    if not input_dir.is_dir():
        print(f"Folder not found: {input_dir}")
        return

    test_set = input_dir.name
    files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in MIME_TYPES)
    print(f"Found {len(files)} invoice(s) in {input_dir}/\n")

    counts = {"auto_approved": 0, "needs_review": 0, "skipped": 0, "failed": 0}
    with get_connection() as conn:
        for file_path in files:
            try:
                status = process_invoice(conn, test_set, file_path)
            except errors.ClientError as e:
                conn.rollback()
                if e.code == 429:
                    print(f"\nSTOPPED  Daily API limit reached at {file_path.stem}.")
                    print("         Run again later. Finished invoices will be skipped.")
                    break
                print(f"FAILED   {file_path.stem}: {e}")
                status = "failed"
            except Exception as e:
                conn.rollback()
                print(f"FAILED   {file_path.stem}: {e}")
                status = "failed"
            counts[status] += 1

    print(f"\nDone. Approved: {counts['auto_approved']}, "
          f"Needs review: {counts['needs_review']}, "
          f"Skipped: {counts['skipped']}, "
          f"Failed: {counts['failed']}")

if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("invoices")
    run(folder)
