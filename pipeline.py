import json
from pathlib import Path
from extract import extract_invoice
from validate import validate_invoice

INVOICE_DIR = Path("invoices")
APPROVED_DIR = Path("output/approved")
REVIEW_DIR = Path("output/needs_review")

def already_processed(invoice_id):
    """True if this invoice has a result in either folder."""
    filename = f"{invoice_id}.json"
    return (APPROVED_DIR / filename).exists() or (REVIEW_DIR / filename).exists()

def process_invoice(pdf_path):
    invoice_id = pdf_path.stem  # "INV-1001.pdf" -> "INV-1001"

    if already_processed(invoice_id):
        print(f"SKIP     {invoice_id} (already processed)")
        return "skipped"

    data = extract_invoice(str(pdf_path))
    issues = validate_invoice(data)

    result = {
        "source_file": pdf_path.name,
        "extracted": data,
        "issues": issues,
    }

    if issues:
        folder, status = REVIEW_DIR, "needs_review"
        print(f"REVIEW   {invoice_id}: {len(issues)} issue(s)")
        for issue in issues:
            print(f"           - {issue}")
    else:
        folder, status = APPROVED_DIR, "approved"
        print(f"APPROVED {invoice_id}: total ${data['total']:.2f}")

    (folder / f"{invoice_id}.json").write_text(json.dumps(result, indent=2))
    return status

def run():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(INVOICE_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} invoice(s)\n")

    counts = {"approved": 0, "needs_review": 0, "skipped": 0}
    for pdf in pdfs:
        status = process_invoice(pdf)
        counts[status] += 1

    print(f"\nDone. Approved: {counts['approved']}, "
          f"Needs review: {counts['needs_review']}, "
          f"Skipped: {counts['skipped']}")

if __name__ == "__main__":
    run()
