import json
from pathlib import Path
import pymupdf
import streamlit as st

OUTPUT_DIR = Path("output")
STATUSES = ["approved", "needs_review"]

st.set_page_config(page_title="Invoice Automation", layout="wide")

def list_test_sets():
    """Folders under output/, e.g. 'invoices' and 'invoices_scanned'."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(p.name for p in OUTPUT_DIR.iterdir() if p.is_dir())

def load_results(test_set):
    """Return a list of (invoice_id, status, result) for one test set."""
    results = []
    for status in STATUSES:
        for path in sorted((OUTPUT_DIR / test_set / status).glob("*.json")):
            results.append((path.stem, status, json.loads(path.read_text())))
    return sorted(results)

def show_document(file_path):
    """Display a PDF (first page) or an image file."""
    if not file_path.exists():
        st.error(f"Original file not found: {file_path}")
    elif file_path.suffix.lower() == ".pdf":
        page = pymupdf.open(file_path)[0]
        st.image(page.get_pixmap(dpi=100).tobytes("png"))
    else:
        st.image(str(file_path))

def money(value):
    return f"${value:,.2f}" if isinstance(value, (int, float)) else "Not found"

# ---------- Page ----------
st.title("Invoice Automation")

test_sets = list_test_sets()
if not test_sets:
    st.info("No results yet. Run pipeline.py first.")
    st.stop()

test_set = st.sidebar.selectbox("Test set", test_sets)
results = load_results(test_set)
if not results:
    st.info(f"No processed invoices in {test_set} yet.")
    st.stop()

labels = [
    f"{inv_id}  ({'Approved' if status == 'approved' else 'Needs review'})"
    for inv_id, status, _ in results
]
choice = st.sidebar.radio("Invoice", range(len(results)), format_func=lambda i: labels[i])
invoice_id, status, result = results[choice]
data = result["extracted"]

left, right = st.columns(2)

with left:
    st.subheader("Original document")
    show_document(Path(test_set) / result["source_file"])

with right:
    st.subheader(invoice_id)
    if status == "approved":
        st.success("Approved: passed all validation checks")
    else:
        st.warning("Needs review")
        for issue in result["issues"]:
            st.write(f"- {issue}")

    st.markdown("**Extracted data**")
    st.write(f"**Vendor:** {data.get('vendor_name') or 'Not found'}")
    st.write(f"**Invoice number:** {data.get('invoice_number') or 'Not found'}")
    st.write(f"**Date:** {data.get('invoice_date') or 'Not found'}")
    st.write(f"**Customer:** {data.get('customer_name') or 'Not found'}")

    st.markdown("**Line items**")
    st.dataframe(data.get("line_items") or [], hide_index=True)

    st.write(f"**Subtotal:** {money(data.get('subtotal'))}")
    st.write(f"**Tax:** {money(data.get('tax'))}")
    st.write(f"**Total:** {money(data.get('total'))}")
