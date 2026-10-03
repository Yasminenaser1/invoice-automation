import json
import random
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

VENDORS = [
    ("Northwind Office Supply", "1200 Commerce St, Dallas, TX 75201"),
    ("Summit Cleaning Services", "455 Elm St, Plano, TX 75074"),
    ("Brightline IT Solutions", "88 Main St, Richardson, TX 75080"),
]
CUSTOMERS = ["Lakeside Dental Group", "Maple Grove Pediatrics", "Riverstone Law Office"]
PRODUCTS = {
    "Northwind Office Supply": [("Printer Paper (box)", 42.50), ("Toner Cartridge", 89.99),
                                ("Office Chair", 175.00), ("Desk Organizer", 24.99)],
    "Summit Cleaning Services": [("Office Cleaning (weekly)", 320.00), ("Carpet Shampoo", 185.00),
                                 ("Window Cleaning", 140.00)],
    "Brightline IT Solutions": [("Laptop Setup", 95.00), ("Network Support (hour)", 120.00),
                                ("Wireless Mouse", 29.99), ("Monitor 27in", 249.00)],
}
TAX_RATE = 0.0825
ERROR_INVOICES = {1004}  # these get a wrong printed total on purpose

def build_invoice(number, rng, vendor_error=False):
    vendor, address = rng.choice(VENDORS)
    chosen = rng.sample(PRODUCTS[vendor], k=rng.randint(2, 3))
    items = []
    for desc, price in chosen:
        qty = rng.randint(1, 10)
        items.append({"description": desc, "quantity": qty,
                      "unit_price": price, "amount": round(qty * price, 2)})
    subtotal = round(sum(i["amount"] for i in items), 2)
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax, 2)
    if vendor_error:
        total = round(total + 50, 2)  # vendor printed the wrong total
    return {
        "vendor_name": vendor,
        "vendor_address": address,
        "invoice_number": f"INV-{number}",
        "invoice_date": f"2026-09-{rng.randint(1, 28):02d}",
        "customer_name": rng.choice(CUSTOMERS),
        "line_items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }

def draw_invoice(path, inv):
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 740, inv["vendor_name"])
    c.setFont("Helvetica", 11)
    c.drawString(50, 722, inv["vendor_address"])

    c.setFont("Helvetica-Bold", 14)
    c.drawString(400, 740, "INVOICE")
    c.setFont("Helvetica", 11)
    c.drawString(400, 722, f"Invoice #: {inv['invoice_number']}")
    c.drawString(400, 707, f"Date: {inv['invoice_date']}")
    c.drawString(50, 680, f"Bill To: {inv['customer_name']}")

    y = 640
    c.setFont("Helvetica-Bold", 11)
    for x, label in [(50, "Description"), (300, "Qty"), (370, "Unit Price"), (470, "Amount")]:
        c.drawString(x, y, label)
    c.setFont("Helvetica", 11)
    for item in inv["line_items"]:
        y -= 20
        c.drawString(50, y, item["description"])
        c.drawString(300, y, str(item["quantity"]))
        c.drawString(370, y, f"${item['unit_price']:.2f}")
        c.drawString(470, y, f"${item['amount']:.2f}")

    y -= 40
    c.drawString(370, y, "Subtotal:")
    c.drawString(470, y, f"${inv['subtotal']:.2f}")
    c.drawString(370, y - 18, "Tax (8.25%):")
    c.drawString(470, y - 18, f"${inv['tax']:.2f}")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(370, y - 36, "Total:")
    c.drawString(470, y - 36, f"${inv['total']:.2f}")
    c.save()

def main():
    rng = random.Random(42)  # fixed seed = same invoices every run
    out_dir = Path("invoices")
    out_dir.mkdir(exist_ok=True)
    truth = {}

    for number in range(1001, 1007):
        has_error = number in ERROR_INVOICES
        inv = build_invoice(number, rng, vendor_error=has_error)
        draw_invoice(out_dir / f"{inv['invoice_number']}.pdf", inv)
        inv["expected_status"] = "needs_review" if has_error else "approved"
        truth[inv["invoice_number"]] = inv
        flag = "  <- has vendor error" if has_error else ""
        print(f"Created {inv['invoice_number']}: {inv['vendor_name']}, total ${inv['total']:.2f}{flag}")

    Path("ground_truth.json").write_text(json.dumps(truth, indent=2))
    print("\nSaved correct answers to ground_truth.json")

if __name__ == "__main__":
    main()
