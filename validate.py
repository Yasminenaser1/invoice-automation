from datetime import date, datetime

TOLERANCE = 0.01  # allow 1 cent of rounding difference
REQUIRED_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "line_items", "total"]

def close_enough(a, b):
    return abs(a - b) <= TOLERANCE

def validate_invoice(data):
    """Return a list of problems. An empty list means the invoice passed."""
    issues = []

    # 1. Required fields must be present
    for field in REQUIRED_FIELDS:
        if data.get(field) in (None, "", []):
            issues.append(f"Missing required field: {field}")
    if issues:
        return issues  # can't check the math without the basics

    # 2. Each line: quantity x unit price = amount
    for i, item in enumerate(data["line_items"], start=1):
        expected = item["quantity"] * item["unit_price"]
        if not close_enough(expected, item["amount"]):
            issues.append(f"Line {i} ({item['description']}): "
                          f"{item['quantity']} x {item['unit_price']} = {expected:.2f}, "
                          f"but invoice says {item['amount']:.2f}")

    # 3. Line items must add up to the subtotal
    line_sum = sum(item["amount"] for item in data["line_items"])
    subtotal = data.get("subtotal")
    if subtotal is not None and not close_enough(line_sum, subtotal):
        issues.append(f"Line items add up to {line_sum:.2f}, but subtotal is {subtotal:.2f}")

    # 4. Subtotal + tax must equal the total
    tax = data.get("tax") or 0
    if subtotal is not None and not close_enough(subtotal + tax, data["total"]):
        issues.append(f"Subtotal + tax = {subtotal + tax:.2f}, but total is {data['total']:.2f}")

    # 5. Date must be real and not in the future
    try:
        invoice_date = datetime.strptime(data["invoice_date"], "%Y-%m-%d").date()
        if invoice_date > date.today():
            issues.append(f"Invoice date {invoice_date} is in the future")
    except ValueError:
        issues.append(f"Invalid date format: {data['invoice_date']}")

    # 6. Total must be positive
    if data["total"] <= 0:
        issues.append(f"Total must be positive, got {data['total']}")

    return issues

if __name__ == "__main__":
    # A correct invoice (the AI's real output from Step 3)
    good = {
        "vendor_name": "Northwind Office Supply",
        "invoice_number": "INV-1001",
        "invoice_date": "2026-09-15",
        "line_items": [
            {"description": "Printer Paper (box)", "quantity": 10, "unit_price": 42.5, "amount": 425.0},
            {"description": "Toner Cartridge", "quantity": 3, "unit_price": 89.99, "amount": 269.97},
            {"description": "Office Chair", "quantity": 2, "unit_price": 175.0, "amount": 350.0},
        ],
        "subtotal": 1044.97,
        "tax": 86.21,
        "total": 1131.18,
    }

    # The same invoice, but as if the AI misread the total (1131.18 -> 1181.18)
    bad = dict(good, total=1181.18)

    for name, invoice in [("GOOD", good), ("BAD", bad)]:
        issues = validate_invoice(invoice)
        print(f"\n{name} invoice:")
        if issues:
            for issue in issues:
                print(f"  FAILED: {issue}")
        else:
            print("  PASSED all checks")
