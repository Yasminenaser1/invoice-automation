import json
from pathlib import Path

TRUTH = json.loads(Path("ground_truth.json").read_text())
OUTPUT_DIRS = {
    "approved": Path("output/approved"),
    "needs_review": Path("output/needs_review"),
}
TEXT_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "customer_name"]
NUMBER_FIELDS = ["subtotal", "tax", "total"]
ALL_FIELDS = TEXT_FIELDS + NUMBER_FIELDS + ["line_items"]

def same_text(a, b):
    return str(a).strip().lower() == str(b).strip().lower()

def same_number(a, b):
    try:
        return abs(float(a) - float(b)) <= 0.01
    except (TypeError, ValueError):
        return False

def line_items_match(got, want):
    if len(got) != len(want):
        return False
    for g, w in zip(got, want):
        if not (same_text(g.get("description"), w["description"])
                and same_number(g.get("quantity"), w["quantity"])
                and same_number(g.get("unit_price"), w["unit_price"])
                and same_number(g.get("amount"), w["amount"])):
            return False
    return True

def compare(extracted, truth):
    """Return {field: True/False} for every field we check."""
    results = {}
    for field in TEXT_FIELDS:
        results[field] = same_text(extracted.get(field), truth[field])
    for field in NUMBER_FIELDS:
        results[field] = same_number(extracted.get(field), truth[field])
    results["line_items"] = line_items_match(extracted.get("line_items") or [], truth["line_items"])
    return results

def load_processed():
    """Find every processed invoice and which folder it landed in."""
    found = {}
    for status, folder in OUTPUT_DIRS.items():
        for path in folder.glob("*.json"):
            found[path.stem] = (status, json.loads(path.read_text()))
    return found

def main():
    processed = load_processed()
    if not processed:
        print("No processed invoices yet. Run pipeline.py first.")
        return

    field_correct = {f: 0 for f in ALL_FIELDS}
    fully_correct = 0
    routing_correct = 0

    print(f"Evaluating {len(processed)} of {len(TRUTH)} invoices\n")

    for invoice_id in sorted(processed):
        status, result = processed[invoice_id]
        truth = TRUTH[invoice_id]
        checks = compare(result["extracted"], truth)

        for field, ok in checks.items():
            field_correct[field] += ok
        hits = sum(checks.values())
        if hits == len(ALL_FIELDS):
            fully_correct += 1

        route_ok = status == truth["expected_status"]
        routing_correct += route_ok

        print(f"{invoice_id}: fields {hits}/{len(ALL_FIELDS)} | "
              f"routed to {status} (expected {truth['expected_status']}) "
              f"{'OK' if route_ok else 'WRONG'}")
        for field, ok in checks.items():
            if not ok:
                got = result["extracted"].get(field)
                print(f"    MISS {field}: got {got!r}, expected {truth[field]!r}")

    n = len(processed)
    total_checks = n * len(ALL_FIELDS)
    total_hits = sum(field_correct.values())

    print("\n=== Summary ===")
    print(f"Field accuracy:     {total_hits}/{total_checks} ({total_hits / total_checks:.0%})")
    print(f"Invoices perfect:   {fully_correct}/{n} ({fully_correct / n:.0%})")
    print(f"Routing accuracy:   {routing_correct}/{n} ({routing_correct / n:.0%})")
    print("\nPer-field accuracy:")
    for field in ALL_FIELDS:
        print(f"  {field:<15} {field_correct[field]}/{n}")

if __name__ == "__main__":
    main()
