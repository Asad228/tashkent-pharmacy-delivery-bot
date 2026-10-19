from typing import List
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import database

app = FastAPI(
    title="Tashkent Pharmacy Search & Smart Delivery API",
    version="1.0.0",
    description="Multi-branch pharmacy inventory search, F-Apteka stock importer, and smart single/multi-branch cart optimizer.",
)


class CartRequest(BaseModel):
    skus: List[str]
    user_lat: float = 41.2980
    user_lon: float = 69.3620


@app.on_event("startup")
def on_startup():
    database.init_db()


@app.get("/api/v1/search")
def api_search(q: str = Query("", description="Medicine name (RU / UZ) or SKU")):
    database.init_db()
    results = database.search_medicines(q)
    return {"count": len(results), "results": results}


@app.post("/api/v1/cart/optimize")
def api_optimize_cart(payload: CartRequest):
    database.init_db()
    return database.optimize_cart(payload.skus, payload.user_lat, payload.user_lon)


@app.get("/api/v1/branches")
def api_branches():
    database.init_db()
    conn = database.get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM branches").fetchall()]
    conn.close()
    return {"branches": rows}


@app.get("/", response_class=HTMLResponse)
def admin_dashboard():
    database.init_db()
    conn = database.get_conn()
    branches = [dict(r) for r in conn.execute("SELECT * FROM branches").fetchall()]
    orders = [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()]
    inventory = [
        dict(r)
        for r in conn.execute(
            """SELECT i.sku, i.title_ru, i.manufacturer, i.price_uzs, i.stock_qty, b.name as branch_name
               FROM inventory i JOIN branches b ON b.id = i.branch_id ORDER BY b.id, i.sku"""
        ).fetchall()
    ]
    conn.close()

    order_rows = "".join(
        f"<tr><td>#{o['id']}</td><td>{o['customer_name']}</td><td>{o['customer_phone']}</td>"
        f"<td><code>{o['delivery_mode']}</code></td><td>{o['branch_summary']}</td>"
        f"<td>{o['items_json']}</td><td>{o['total_uzs']:,} UZS</td><td><b>{o['status']}</b></td></tr>"
        for o in orders
    )
    inv_rows = "".join(
        f"<tr><td><code>{i['sku']}</code></td><td>{i['title_ru']}</td><td>{i['manufacturer']}</td>"
        f"<td>{i['branch_name']}</td><td>{i['price_uzs']:,} UZS</td><td>{i['stock_qty']} pcs</td></tr>"
        for i in inventory
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Pharmacy Dispatch & F-Apteka Inventory Admin</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px 36px; background: #f6f8fa; color: #1f2328; }}
    header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #d0d7de; padding-bottom: 14px; margin-bottom: 20px; }}
    h1 {{ font-size: 22px; margin: 0; }}
    h2 {{ font-size: 16px; margin: 22px 0 10px; color: #24292f; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d0d7de; font-size: 13.5px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; }}
    th {{ background: #f6f8fa; font-weight: 600; }}
    code {{ background: #eff1f3; padding: 2px 5px; border-radius: 4px; font-size: 12px; }}
    .meta {{ font-size: 13px; color: #57606a; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Pharmacy Chain Dispatch & Inventory Admin (Tashkent)</h1>
      <div class="meta">Connected Branches: {len(branches)} (Tuzel-2, Kadysheva, Buyuk Ipak Yuli, Chilanzar-9) • F-Apteka Sync: Active</div>
    </div>
    <div class="meta"><a href="/docs">OpenAPI / Swagger (/docs)</a></div>
  </header>

  <h2>Live Delivery & Split-Cart Orders</h2>
  <table>
    <thead>
      <tr><th>ID</th><th>Client</th><th>Phone</th><th>Mode</th><th>Fulfillment Branch(es)</th><th>Items</th><th>Total (w/ Delivery)</th><th>Status</th></tr>
    </thead>
    <tbody>{order_rows}</tbody>
  </table>

  <h2>Real-Time Branch Stock (Synced from F-Apteka / 1C Export)</h2>
  <table>
    <thead>
      <tr><th>SKU</th><th>Medicine</th><th>Manufacturer</th><th>Branch</th><th>Price</th><th>Stock</th></tr>
    </thead>
    <tbody>{inv_rows}</tbody>
  </table>
</body>
</html>"""
