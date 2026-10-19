from fastapi.testclient import TestClient
import database
from app import app

client = TestClient(app)


def test_search_medicine_ru_and_uz():
    database.init_db()
    resp_ru = client.get("/api/v1/search", params={"q": "Нурофен"})
    assert resp_ru.status_code == 200
    assert resp_ru.json()["count"] >= 1

    resp_uz = client.get("/api/v1/search", params={"q": "Nurofen"})
    assert resp_uz.status_code == 200
    assert resp_uz.json()["count"] >= 1


def test_single_branch_cart_tuzel2():
    # DRG-101 (Nurofen) and DRG-104 (Otrivin) are both in stock at Branch #1 (Tuzel-2)
    resp = client.post(
        "/api/v1/cart/optimize",
        json={"skus": ["DRG-101", "DRG-104"], "user_lat": 41.2980, "user_lon": 69.3620},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["AllInOneBranch"] is True
    assert data["FulfillmentPlan"]["mode"] == "single_branch"
    assert "Tuzel-2" in data["FulfillmentPlan"]["branch"]


def test_multi_branch_split_cart():
    # DRG-104 (Otrivin, only at Tuzel-2) + DRG-107 (TheraFlu, at Kadysheva/Buyuk Ipak Yuli)
    resp = client.post(
        "/api/v1/cart/optimize",
        json={"skus": ["DRG-104", "DRG-107"], "user_lat": 41.2980, "user_lon": 69.3620},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["AllInOneBranch"] is False
    assert data["FulfillmentPlan"]["mode"] == "multi_branch_split"
    assert len(data["FulfillmentPlan"]["allocations"]) == 2
