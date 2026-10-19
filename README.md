# Tashkent Pharmacy Search & Smart Multi-Branch Delivery System

A lightweight **FastAPI + Aiogram 3 (Telegram Bot) + SQLite** backend built for local pharmacy chains in Tashkent, Uzbekistan.

## Key Features
- **Bilingual Search (RU / UZ):** Instant search across pharmacy branches by medicine name or SKU.
- **Smart Cart Optimizer (`single_branch` vs `multi_branch_split`):**
  - Automatically checks if a single nearest pharmacy branch (e.g., *Branch #1 — Tuzel-2*) has 100% of the customer's cart in stock to minimize courier fees.
  - Falls back to a multi-branch split fulfillment plan when rare items are spread across different branches (*Tuzel-2 + Kadysheva*).
- **F-Apteka / 1C Stock Sync:** Compatible with standard Excel/CSV inventory exports used by Tashkent pharmacies.
- **Web Dispatch Dashboard & OpenAPI (`/docs`):** Live view of incoming orders and real-time branch stock.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run automated test suite
pytest -v

# Start FastAPI web dashboard & REST API on http://127.0.0.1:8010
uvicorn app:app --host 127.0.0.1 --port 8010
```
