import random
from pathlib import Path
import fitz  # PyMuPDF: turns PDF pages into images
from PIL import Image, ImageFilter, ImageEnhance

def scan_effect(img, rng):
    """Make a clean image look like a low-quality office scan."""
    img = img.convert("L")  # grayscale, like most scanners
    img = img.rotate(rng.uniform(-3, 3), expand=True, fillcolor=255)  # slightly crooked
    img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.6, 1.2)))  # blurry
    img = ImageEnhance.Contrast(img).enhance(rng.uniform(0.6, 0.85))  # faded

    # Speckle noise: random black and white dots
    pixels = img.load()
    width, height = img.size
    for _ in range(int(width * height * 0.002)):
        x, y = rng.randrange(width), rng.randrange(height)
        pixels[x, y] = rng.choice([0, 255])
    return img

def main():
    rng = random.Random(7)  # fixed seed so the scans are repeatable
    out_dir = Path("invoices_scanned")
    out_dir.mkdir(exist_ok=True)

    for pdf_path in sorted(Path("invoices").glob("*.pdf")):
        page = fitz.open(pdf_path)[0]
        pix = page.get_pixmap(dpi=120)  # lower resolution, like a cheap scanner
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img = scan_effect(img, rng)

        out_path = out_dir / f"{pdf_path.stem}.jpg"
        img.save(out_path, "JPEG", quality=40)  # heavy compression
        print(f"Created {out_path}")

if __name__ == "__main__":
    main()
