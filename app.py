import json
from pathlib import Path
import pymupdf
import streamlit as st

OUTPUT_DIR = Path("output")
STATUSES = ["approved", "needs_review"]

# status -> (label, text color, background color)
STATUS_STYLE = {
    "approved": ("Approved", "#15803D", "#DCFCE7"),
    "needs_review": ("Needs review", "#B45309", "#FEF3C7"),
}

st.set_page_config(page_title="Invoice Automation", layout="wide")

st.markdown("""
<style>
.badge {
    display: inline-block; padding: 4px 12px; border-radius: 999px;
    font-size: 0.85rem; font-weight: 600; vertical-align: middle;
}
.totals {
    text-align: right; line-height: 2; font-variant-numeric: tabular-nums;
}
.totals .grand {
    font-size: 1.2rem; font-weight: 700;
    border-top: 1px solid #D1D5DB; margin-top: 4px; padding-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Data helpers ----------

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

def money(value):
    return f"${value:,.2f}" if isinstance(value, (int, float)) else "Not found"

# ---------- Display helpers ----------

def badge(status):
    label, color, background = STATUS_STYLE[status]
    return f'<span class="badge" style="color:{color}; background:{background};">{label}</span>'

def show_document(file_path):
    """Display a PDF (first page) or an image file."""
    if not file_path.exists():
        st.error(f"Original file not found: {file_path}")
    elif file_path.suffix.lower() == ".pdf":
        page = pymupdf.open(file_path)[0]
        st.image(page.get_pixmap(dpi=110).tobytes("png"))
    else:
        st.image(str(file_path))

def field(column, label, value):
    """A small gray label with the value underneath."""
    column.caption(label)
    column.markdown(f"**{value or 'Not found'}**")

# ---------- Sidebar ----------

test_sets = list_test_sets()
if not test_sets:
    st.title("Invoice Automation")
    st.info("No results yet. Run pipeline.py first.")
    st.stop()

with st.sidebar:
    st.header("Invoices")
    test_set = st.selectbox("Test set", test_sets)
    results = load_results(test_set)
    if not results:
        st.info(f"No processed invoices in {test_set} yet.")
        st.stop()

    labels = [
        f"{inv_id}  ·  {STATUS_STYLE[status][0]}"
        for inv_id, status, _ in results
    ]
    choice = st.radio("Select an invoice", range(len(results)),
                      format_func=lambda i: labels[i])

invoice_id, status, result = results[choice]
data = result["extracted"]

# ---------- Header and summary ----------

st.title("Invoice Automation")
st.caption("AI extraction, validation, and routing for accounts payable")

approved_count = sum(1 for _, s, _ in results if s == "approved")
m1, m2, m3 = st.columns(3)
m1.metric("Processed", len(results))
m2.metric("Auto-approved", approved_count)
m3.metric("Needs review", len(results) - approved_count)

st.divider()

st.markdown(f"### {invoice_id} &nbsp; {badge(status)}", unsafe_allow_html=True)
st.caption(data.get("vendor_name") or "Unknown vendor")

# ---------- Document and extracted data ----------

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.markdown("**Original document**")
        show_document(Path(test_set) / result["source_file"])

with right:
    if result["issues"]:
        with st.container(border=True):
            st.markdown("**Validation issues**")
            for issue in result["issues"]:
                st.warning(issue)

    with st.container(border=True):
        st.markdown("**Invoice details**")
        c1, c2 = st.columns(2)
        field(c1, "Vendor", data.get("vendor_name"))
        field(c2, "Invoice number", data.get("invoice_number"))
        field(c1, "Invoice date", data.get("invoice_date"))
        field(c2, "Bill to", data.get("customer_name"))

    with st.container(border=True):
        st.markdown("**Line items**")
        st.dataframe(
            data.get("line_items") or [],
            hide_index=True,
            column_config={
                "description": st.column_config.TextColumn("Description"),
                "quantity": st.column_config.NumberColumn("Qty"),
                "unit_price": st.column_config.NumberColumn("Unit price", format="$%.2f"),
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            },
        )
        st.markdown(
            f'<div class="totals">'
            f'Subtotal: {money(data.get("subtotal"))}<br>'
            f'Tax: {money(data.get("tax"))}'
            f'<div class="grand">Total: {money(data.get("total"))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
