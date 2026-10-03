# Invoice Automation

An AI-powered pipeline that reads invoices (PDFs and scanned images), extracts structured data, validates it, and routes each invoice to automatic approval or human review.

## The Problem

Many businesses still process invoices by hand: an employee opens each document, reads it, and types the details into a spreadsheet. This is slow and error-prone. This project automates that process while keeping a human involved for uncertain cases.

## How It Works

## Reliability Features

- **Retry with exponential backoff** - automatically retries when the API is overloaded (HTTP 5xx), waiting 2s, 4s, 8s, 16s
- **Idempotency** - already-processed invoices are skipped, so re-running never duplicates work
- **Graceful quota handling** - stops cleanly at API rate limits; the next run resumes where it left off
- **Per-invoice error isolation** - one failed invoice does not stop the batch
- **Input validation** - unsupported file types are rejected before any API call is made

## Evaluation

Test invoices are generated with known correct values (`ground_truth.json`), including one invoice with a deliberate vendor error that should be routed to review. Degraded "scanned" versions (rotated, blurred, low contrast, noisy, compressed) test robustness on realistic input.

| Test set | Field accuracy | Routing accuracy |
|---|---|---|
| Clean PDFs | Pending full run | Pending full run |
| Degraded scans | Pending full run | Pending full run |

## Project Structure

| File | Purpose |
|---|---|
| `make_invoice.py` | Generates sample invoices and ground truth |
| `make_scans.py` | Creates degraded scan versions for harder testing |
| `extract.py` | Sends a document to Gemini and returns structured data |
| `validate.py` | Checks extracted data for errors |
| `pipeline.py` | Runs extract, validate, and route on a folder |
| `evaluate.py` | Measures accuracy against ground truth |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo 'GEMINI_API_KEY=your-key-here' > .env
```

## Usage

```bash
python make_invoice.py              # generate sample invoices
python make_scans.py                # generate degraded scans
python pipeline.py invoices         # process clean PDFs
python pipeline.py invoices_scanned # process scans
python evaluate.py invoices         # accuracy report
```

## Note

All invoices in this repository are synthetic test data. Company names, addresses, and amounts are fictional.

## Tech Stack

Python, Google Gemini API, ReportLab, PyMuPDF, Pillow
