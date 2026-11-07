import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def c(monkeypatch):
    for k in ("IBM_API_KEY", "IBM_PROJECT_ID"):
        monkeypatch.delenv(k, raising=False)
    from app.main import app
    return TestClient(app)


V = {"shop_name": "Raju Chai", "business_type": "Tea stall", "opening_hours": "7 AM - 9 PM", "language": "mr"}
P = {"name": "Chai", "price": 10, "unit": "cup", "description": None}


def gen(c, **kw):
    body = {"task": "whatsapp_promo", "language": "en", "vendor": V, "product": P}
    body.update(kw)
    return c.post("/api/generate", json=body)


@pytest.mark.parametrize("lang,word", [("en", "Raju Chai"), ("hi", "नमस्ते"), ("mr", "नमस्कार")])
def test_demo_generation_languages(c, lang, word):
    r = gen(c, language=lang)
    assert r.status_code == 200
    r = r.json()
    assert word in r["text"] and r["source"] == "demo-template" and r["status"] == "draft" and "suggestion" in r["disclaimer"]


def test_bad_language_and_missing_product(c):
    assert gen(c, language="fr").status_code == 422
    assert gen(c, product=None).status_code == 422


def test_marketing_tips_needs_no_product(c):
    r = gen(c, task="marketing_tips", language="hi", product=None)
    assert r.status_code == 200 and "Google" in r.json()["text"]


def test_no_server_state_needed(c):
    # works on a fresh server with nothing stored: the browser supplies shop + product
    assert gen(c).status_code == 200
    assert c.get("/api/vendor").status_code == 404


def test_ibm_mode_success_is_separate_from_demo(c, monkeypatch):
    monkeypatch.setenv("IBM_API_KEY", "k")
    monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite
    monkeypatch.setattr(granite, "chat", lambda s, u: "Garam chai ₹10 per cup at Raju Chai!")
    r = gen(c, task="social_caption").json()
    assert r["source"] == "ibm-granite" and c.get("/api/status").json()["mode"] == "ibm-granite"


def test_ibm_failure_does_not_fall_back_to_demo(c, monkeypatch):
    monkeypatch.setenv("IBM_API_KEY", "k")
    monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite

    def boom(*a, **k):
        raise granite.httpx.ConnectError("x")

    monkeypatch.setattr(granite, "_token", lambda: "t")
    monkeypatch.setattr(granite.httpx, "post", boom)
    assert gen(c).status_code == 502


def test_validation_rejects_risky_output(c, monkeypatch):
    monkeypatch.setenv("IBM_API_KEY", "k")
    monkeypatch.setenv("IBM_PROJECT_ID", "p")
    from app import granite
    monkeypatch.setattr(granite, "chat", lambda s, u: "Guaranteed 100% profit, send your OTP now!")
    assert gen(c).status_code == 422


def test_input_validation_and_xss(c):
    assert gen(c, vendor={**V, "shop_name": "<script>alert(1)</script>"}).status_code == 422
    for bad in ({"name": "x", "price": -1}, {"name": "x", "price": 1e9}, {"name": "", "price": 5}, {"name": "x" * 500, "price": 5}):
        assert gen(c, product=bad).status_code == 422
    assert gen(c, product={"name": "a'; DROP TABLE products;--", "price": 5}).status_code == 200


def test_validate_endpoint(c):
    assert c.post("/api/validate", json={"text": "<b>x</b> hello there"}).json()["ok"] is False
    assert c.post("/api/validate", json={"text": "Fresh chai at Raju Chai"}).json()["ok"] is True


def test_schemes_have_official_links_and_upi_safety(c):
    s = c.get("/api/schemes").json()
    assert all(i["link"].startswith("https://") and ".gov.in" in i["link"] for i in s["items"]) and not s["ai_generated"]
    assert "PIN" in c.get("/api/upi-guide").json()["safety"]


def test_index_served(c):
    r = c.get("/")
    assert r.status_code == 200 and "DukaanSaathi" in r.text