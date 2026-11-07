import os, pytest
from fastapi.testclient import TestClient
@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    for k in ("IBM_API_KEY", "IBM_PROJECT_ID"): monkeypatch.delenv(k, raising=False)
    from app.main import app; return TestClient(app)
V = {"shop_name": "Raju Chai", "business_type": "Tea stall", "opening_hours": "7 AM - 9 PM", "language": "mr"}
def shop(c):
    assert c.put("/api/vendor", json=V).status_code == 200
    return c.post("/api/products", json={"name": "Chai", "price": 10, "unit": "cup"}).json()

def test_profile_create_edit(c):
    assert c.get("/api/vendor").json() is None
    c.put("/api/vendor", json=V); r = c.put("/api/vendor", json={**V, "shop_name": "Raju Tea"})
    assert r.json()["shop_name"] == "Raju Tea"
def test_product_crud_and_persistence(c, tmp_path):
    p = shop(c); assert c.put(f"/api/products/{p['id']}", json={"name": "Kadak", "price": 12, "unit": "cup"}).json()["price"] == 12
    from app.main import app; assert TestClient(app).get("/api/products").json()[0]["name"] == "Kadak"   # new client, same DB file
    assert c.delete(f"/api/products/{p['id']}").status_code == 204 and c.delete(f"/api/products/{p['id']}").status_code == 404
@pytest.mark.parametrize("lang,word", [("en", "Raju Chai"), ("hi", "नमस्ते"), ("mr", "नमस्कार")])
def test_demo_generation_languages(c, lang, word):
    p = shop(c); r = c.post("/api/generate", json={"task": "whatsapp_promo", "language": lang, "product_id": p["id"]}).json()
    assert word in r["text"] and r["source"] == "demo-template" and r["status"] == "draft" and "suggestion" in r["disclaimer"]
def test_bad_language_and_missing_product(c):
    shop(c); assert c.post("/api/generate", json={"task": "whatsapp_promo", "language": "fr", "product_id": 1}).status_code == 422
    assert c.post("/api/generate", json={"task": "whatsapp_promo"}).status_code == 422
def test_ibm_mode_success_is_separate_from_demo(c, monkeypatch):
    p = shop(c); monkeypatch.setenv("IBM_API_KEY", "k"); monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite; monkeypatch.setattr(granite, "chat", lambda s, u: "Garam chai ₹10 per cup at Raju Chai!")
    r = c.post("/api/generate", json={"task": "social_caption", "product_id": p["id"]}).json()
    assert r["source"] == "ibm-granite" and c.get("/api/status").json()["mode"] == "ibm-granite"
def test_ibm_failure_does_not_fall_back_to_demo(c, monkeypatch):
    p = shop(c); monkeypatch.setenv("IBM_API_KEY", "k"); monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite
    def boom(*a, **k): raise granite.httpx.ConnectError("x")
    monkeypatch.setattr(granite, "_token", lambda: "t"); monkeypatch.setattr(granite.httpx, "post", boom)
    r = c.post("/api/generate", json={"task": "whatsapp_promo", "product_id": p["id"]})
    assert r.status_code == 502 and c.get("/api/campaigns").json() == []
def test_validation_rejects_risky_output(c, monkeypatch):
    p = shop(c); monkeypatch.setenv("IBM_API_KEY", "k"); monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite; monkeypatch.setattr(granite, "chat", lambda s, u: "Guaranteed 100% profit, send your OTP now!")
    assert c.post("/api/generate", json={"task": "whatsapp_promo", "product_id": p["id"]}).status_code == 422
def test_input_validation_and_xss(c):
    assert c.put("/api/vendor", json={**V, "shop_name": "<script>alert(1)</script>"}).status_code == 422
    c.put("/api/vendor", json=V)
    for bad in ({"name": "x", "price": -1}, {"name": "x", "price": 1e9}, {"name": "", "price": 5}, {"name": "x" * 500, "price": 5}):
        assert c.post("/api/products", json=bad).status_code == 422
    assert c.post("/api/products", json={"name": "a'; DROP TABLE products;--", "price": 5}).status_code == 201
    assert len(c.get("/api/products").json()) == 1
def test_requires_shop_first(c): assert c.post("/api/products", json={"name": "x", "price": 5}).status_code == 404
def test_schemes_have_official_links_and_upi_safety(c):
    s = c.get("/api/schemes").json(); assert all(i["link"].startswith("https://") and ".gov.in" in i["link"] for i in s["items"]) and not s["ai_generated"]
    assert "PIN" in c.get("/api/upi-guide").json()["safety"]
def test_demo_seed_and_download(c):
    c.post("/api/demo/seed"); assert c.get("/api/vendor").json()["is_demo"] == 1
    d = c.get("/api/profile/download"); assert "attachment" in d.headers["content-disposition"] and "Masala Chai" in d.text
def test_campaign_edit_approve(c):
    p = shop(c); g = c.post("/api/generate", json={"task": "marketing_tips", "language": "hi"}).json()
    r = c.patch(f"/api/campaigns/{g['id']}", json={"text": "Mera naya sandesh yahan hai", "status": "approved"}).json()
    assert r["status"] == "approved" and c.patch(f"/api/campaigns/{g['id']}", json={"text": "<b>x</b> hello there"}).status_code == 422
