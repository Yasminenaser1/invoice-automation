from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_invoice(path):
    c = canvas.Canvas(path, pagesize=letter)

    # Vendor info (who sent the bill)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 740, "Northwind Office Supply")
    c.setFont("Helvetica", 11)
    c.drawString(50, 722, "1200 Commerce St, Dallas, TX 75201")

    # Invoice details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(400, 740, "INVOICE")
    c.setFont("Helvetica", 11)
    c.drawString(400, 722, "Invoice #: INV-1001")
    c.drawString(400, 707, "Date: 2026-09-15")

    # Customer
    c.drawString(50, 680, "Bill To: Lakeside Dental Group")

    # Line items table
    items = [
        ("Printer Paper (box)", 10, 42.50),
        ("Toner Cartridge", 3, 89.99),
        ("Office Chair", 2, 175.00),
    ]
    y = 640
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Description")
    c.drawString(300, y, "Qty")
    c.drawString(370, y, "Unit Price")
    c.drawString(470, y, "Amount")
    c.setFont("Helvetica", 11)

    subtotal = 0
    for desc, qty, price in items:
        y -= 20
        amount = qty * price
        subtotal += amount
        c.drawString(50, y, desc)
        c.drawString(300, y, str(qty))
        c.drawString(370, y, f"${price:.2f}")
        c.drawString(470, y, f"${amount:.2f}")

    # Totals
    tax = round(subtotal * 0.0825, 2)
    total = subtotal + tax
    y -= 40
    c.drawString(370, y, "Subtotal:")
    c.drawString(470, y, f"${subtotal:.2f}")
    c.drawString(370, y - 18, "Tax (8.25%):")
    c.drawString(470, y - 18, f"${tax:.2f}")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(370, y - 36, "Total:")
    c.drawString(470, y - 36, f"${total:.2f}")

    c.save()
    print(f"Created {path} — total ${total:.2f}")

if __name__ == "__main__":
    make_invoice("invoices/INV-1001.pdf")
