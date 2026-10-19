import math
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path(__file__).parent / "pharmacy.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            address TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            phone TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            sku TEXT NOT NULL,
            title_ru TEXT NOT NULL,
            title_uz TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            price_uzs INTEGER NOT NULL,
            stock_qty INTEGER NOT NULL,
            rx_required INTEGER DEFAULT 0,
            FOREIGN KEY(branch_id) REFERENCES branches(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            branch_summary TEXT NOT NULL,
            items_json TEXT NOT NULL,
            subtotal_uzs INTEGER NOT NULL,
            delivery_fee_uzs INTEGER NOT NULL,
            total_uzs INTEGER NOT NULL,
            status TEXT DEFAULT 'pending_pharmacist',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        branches = [
            ("TUZEL2", "Branch #1 — Tuzel-2", "Yashnabad", "Tuzel-2 array, block 14, Tashkent", 41.2985, 69.3642, "+998 71 200-11-01"),
            ("KADYSH", "Branch #2 — Kadysheva (Aviasozlar)", "Yashnabad", "Aviasozlar-2, 19, Tashkent", 41.2874, 69.3481, "+998 71 200-11-02"),
            ("BUYUK", "Branch #3 — Buyuk Ipak Yuli", "Mirzo-Ulugbek", "Buyuk Ipak Yuli str, 60, Tashkent", 41.3265, 69.3288, "+998 71 200-11-03"),
            ("CHIL9", "Branch #4 — Chilanzar-9", "Chilanzar", "Chilanzar-9, Qatortol str, Tashkent", 41.2782, 69.2045, "+998 71 200-11-04"),
        ]
        cur.executemany(
            "INSERT INTO branches (code, name, district, address, lat, lon, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
            branches,
        )

        stock = [
            # Branch 1 (Tuzel-2)
            (1, "DRG-101", "Нурофен Экспресс капс. 200мг №24", "Nurofen Ekspress kaps. 200mg #24", "Reckitt Benckiser (UK)", 38500, 42, 0),
            (1, "DRG-102", "Парацетамол таб. 500мг №10", "Paratsetamol tab. 500mg #10", "Nika Pharm (UZ)", 4200, 180, 0),
            (1, "DRG-103", "Магне B6 таб. №60", "Magne B6 tab. #60", "Sanofi (France)", 94000, 15, 0),
            (1, "DRG-104", "Отривин спрей назальный 0.1% 10мл", "Otrivin burun spreyi 0.1% 10ml", "GSK (Switzerland)", 41000, 28, 0),
            (1, "DRG-105", "Линекс Форте капс. №14", "Lineks Forte kaps. #14", "Sandoz (Slovenia)", 79500, 19, 0),
            (1, "DRG-106", "Витамин D3 Аквадетрим 15000 МЕ/мл", "Vitamin D3 Akvadetrim 15000 ME/ml", "Polpharma", 52000, 31, 0),
            # Branch 2 (Kadysheva)
            (2, "DRG-101", "Нурофен Экспресс капс. 200мг №24", "Nurofen Ekspress kaps. 200mg #24", "Reckitt Benckiser (UK)", 39000, 20, 0),
            (2, "DRG-103", "Магне B6 таб. №60", "Magne B6 tab. #60", "Sanofi (France)", 92000, 24, 0),
            (2, "DRG-107", "ТераФлю Экстра порошок №10 (Лимон)", "TeraFlyu Ekstra kukun #10 (Limon)", "GSK (Switzerland)", 86000, 35, 0),
            (2, "DRG-108", "Смекта порошок 3г №10", "Smekta kukun 3g #10", "Ipsen (France)", 48000, 50, 0),
            # Branch 3 (Buyuk Ipak Yuli)
            (3, "DRG-101", "Нурофен Экспресс капс. 200мг №24", "Nurofen Ekspress kaps. 200mg #24", "Reckitt Benckiser (UK)", 38500, 14, 0),
            (3, "DRG-105", "Линекс Форте капс. №14", "Lineks Forte kaps. #14", "Sandoz (Slovenia)", 78000, 11, 0),
            (3, "DRG-107", "ТераФлю Экстра порошок №10 (Лимон)", "TeraFlyu Ekstra kukun #10 (Limon)", "GSK (Switzerland)", 85000, 18, 0),
        ]
        cur.executemany(
            """INSERT INTO inventory
               (branch_id, sku, title_ru, title_uz, manufacturer, price_uzs, stock_qty, rx_required)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            stock,
        )

        sample_orders = [
            ("Azizbek R.", "+998 90 912-44-18", "single_branch", "Branch #1 — Tuzel-2 (1.2 km)", "Nurofen Express x1, Otrivin 0.1% x1", 79500, 15000, 94500, "delivered"),
            ("Malika K.", "+998 93 541-09-22", "multi_branch_split", "Tuzel-2 + Kadysheva (Split Order)", "Magne B6 x1, TheraFlu Extra x1", 180000, 27000, 207000, "courier_assigned"),
            ("Sardor M.", "+998 97 701-88-30", "single_branch", "Branch #1 — Tuzel-2 (0.8 km)", "Linex Forte x1, Paracetamol x2", 87900, 15000, 102900, "pending_pharmacist"),
        ]
        cur.executemany(
            """INSERT INTO orders
               (customer_name, customer_phone, delivery_mode, branch_summary, items_json, subtotal_uzs, delivery_fee_uzs, total_uzs, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            sample_orders,
        )

    conn.commit()
    conn.close()


def search_medicines(query: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    q = f"%{query.strip()}%"
    cur.execute(
        """
        SELECT i.sku, i.title_ru, i.title_uz, i.manufacturer, i.price_uzs, i.stock_qty,
               b.id as branch_id, b.code as branch_code, b.name as branch_name, b.district, b.lat, b.lon
        FROM inventory i
        JOIN branches b ON b.id = i.branch_id
        WHERE i.stock_qty > 0
          AND (i.title_ru LIKE ? OR i.title_uz LIKE ? OR i.sku LIKE ?)
        ORDER BY i.price_uzs ASC
        """,
        (q, q, q),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def optimize_cart(skus: List[str], user_lat: float = 41.2950, user_lon: float = 69.3600) -> Dict[str, Any]:
    """
    Smart Cart Optimizer:
    1. Checks if a single nearest branch has 100% of requested SKUs.
    2. Otherwise calculates optimal multi-branch split fulfillment across branches.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM branches")
    branches = [dict(b) for b in cur.fetchall()]
    for b in branches:
        b["distance_km"] = haversine_km(user_lat, user_lon, b["lat"], b["lon"])
    branches.sort(key=lambda x: x["distance_km"])

    single_branch_candidates = []
    for b in branches:
        placeholders = ",".join("?" for _ in skus)
        cur.execute(
            f"SELECT sku, title_ru, price_uzs, stock_qty FROM inventory WHERE branch_id=? AND sku IN ({placeholders}) AND stock_qty > 0",
            [b["id"], *skus],
        )
        found = [dict(r) for r in cur.fetchall()]
        if len(found) == len(set(skus)):
            subtotal = sum(item["price_uzs"] for item in found)
            fee = 15000 if b["distance_km"] <= 3.0 else int(15000 + (b["distance_km"] - 3.0) * 3000)
            single_branch_candidates.append(
                {
                    "mode": "single_branch",
                    "branch": b["name"],
                    "distance_km": b["distance_km"],
                    "items": found,
                    "subtotal_uzs": subtotal,
                    "delivery_fee_uzs": fee,
                    "total_uzs": subtotal + fee,
                }
            )

    if single_branch_candidates:
        conn.close()
        return {"FulfillmentPlan": single_branch_candidates[0], "AllInOneBranch": True}

    # Multi-branch split fulfillment
    remaining = set(skus)
    allocations = []
    subtotal = 0
    for b in branches:
        if not remaining:
            break
        placeholders = ",".join("?" for _ in remaining)
        cur.execute(
            f"SELECT sku, title_ru, price_uzs FROM inventory WHERE branch_id=? AND sku IN ({placeholders}) AND stock_qty > 0",
            [b["id"], *remaining],
        )
        matched = [dict(r) for r in cur.fetchall()]
        if matched:
            allocations.append({"branch": b["name"], "distance_km": b["distance_km"], "items": matched})
            for m in matched:
                subtotal += m["price_uzs"]
                remaining.discard(m["sku"])

    conn.close()
    fee = 15000 + max(0, len(allocations) - 1) * 12000
    return {
        "AllInOneBranch": False,
        "FulfillmentPlan": {
            "mode": "multi_branch_split",
            "allocations": allocations,
            "missing_skus": list(remaining),
            "subtotal_uzs": subtotal,
            "delivery_fee_uzs": fee,
            "total_uzs": subtotal + fee,
        },
    }
