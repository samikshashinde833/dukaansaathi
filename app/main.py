import os, sqlite3, html
from contextlib import contextmanager
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from . import granite, content as C

try:
    from dotenv import load_dotenv; load_dotenv()
except Exception: pass
app = FastAPI(title="DukaanSaathi AI", version="0.1")
Lang = Literal["en", "hi", "mr"]
SCHEMA = """CREATE TABLE IF NOT EXISTS vendor(id INTEGER PRIMARY KEY CHECK(id=1), shop_name TEXT, business_type TEXT, opening_hours TEXT, language TEXT, service_area TEXT, about TEXT, is_demo INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, unit TEXT NOT NULL, description TEXT);
CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, language TEXT, text TEXT, source TEXT, status TEXT DEFAULT 'draft', product_id INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP);"""

@contextmanager
def db():
    c = sqlite3.connect(os.getenv("DB_PATH", "dukaan.db")); c.row_factory = sqlite3.Row; c.executescript(SCHEMA)
    try: yield c; c.commit()
    finally: c.close()

def _clean(v):
    if v is None: return v
    v = v.strip()
    if any(ch in v for ch in "<>") or any(ord(ch) < 32 for ch in v): raise ValueError("Remove special characters like < >")
    return v
class VendorIn(BaseModel):
    shop_name: str = Field(min_length=2, max_length=80); business_type: str = Field(min_length=2, max_length=60)
    opening_hours: str = Field(min_length=2, max_length=60); language: Lang = "en"
    service_area: Optional[str] = Field(None, max_length=100); about: Optional[str] = Field(None, max_length=500)
    _c = field_validator("shop_name", "business_type", "opening_hours", "service_area", "about")(lambda cls, v: _clean(v))
class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=80); price: float = Field(gt=0, le=100000)
    unit: str = Field("piece", min_length=1, max_length=20); description: Optional[str] = Field(None, max_length=300)
    _c = field_validator("name", "unit", "description")(lambda cls, v: _clean(v))
class GenIn(BaseModel):
    task: Literal["product_description", "whatsapp_promo", "festival_offer", "social_caption", "marketing_tips"]
    language: Lang = "en"; product_id: Optional[int] = None; festival: Optional[str] = Field(None, max_length=40)
    _c = field_validator("festival")(lambda cls, v: _clean(v))
class CampaignPatch(BaseModel):
    text: Optional[str] = Field(None, min_length=5, max_length=2000); status: Optional[Literal["draft", "approved"]] = None
    _c = field_validator("text")(lambda cls, v: _clean(v))

def vendor_or_404(c):
    r = c.execute("SELECT * FROM vendor WHERE id=1").fetchone()
    if not r: raise HTTPException(404, "Set up your shop first.")
    return dict(r)

@app.get("/api/status")
def status():
    d = granite.is_demo()
    return {"mode": "demo" if d else "ibm-granite", "model": None if d else granite.model(),
            "label": "DEMO MODE: sample text from templates, not IBM Granite" if d else f"IBM Granite ({granite.model()})"}

@app.get("/api/vendor")
def get_vendor():
    with db() as c:
        r = c.execute("SELECT * FROM vendor WHERE id=1").fetchone(); return dict(r) if r else None
@app.put("/api/vendor")
def put_vendor(v: VendorIn):
    with db() as c:
        c.execute("INSERT INTO vendor(id,shop_name,business_type,opening_hours,language,service_area,about) VALUES(1,?,?,?,?,?,?) "
                  "ON CONFLICT(id) DO UPDATE SET shop_name=excluded.shop_name,business_type=excluded.business_type,opening_hours=excluded.opening_hours,"
                  "language=excluded.language,service_area=excluded.service_area,about=excluded.about,is_demo=0",
                  (v.shop_name, v.business_type, v.opening_hours, v.language, v.service_area, v.about))
        return vendor_or_404(c)

@app.get("/api/products")
def list_products():
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM products ORDER BY id")]
@app.post("/api/products", status_code=201)
def add_product(p: ProductIn):
    with db() as c:
        vendor_or_404(c)
        i = c.execute("INSERT INTO products(name,price,unit,description) VALUES(?,?,?,?)", (p.name, p.price, p.unit, p.description)).lastrowid
        return dict(c.execute("SELECT * FROM products WHERE id=?", (i,)).fetchone())
@app.put("/api/products/{pid}")
def edit_product(pid: int, p: ProductIn):
    with db() as c:
        if not c.execute("UPDATE products SET name=?,price=?,unit=?,description=? WHERE id=?", (p.name, p.price, p.unit, p.description, pid)).rowcount:
            raise HTTPException(404, "Product not found.")
        return dict(c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone())
@app.delete("/api/products/{pid}", status_code=204)
def del_product(pid: int):
    with db() as c:
        if not c.execute("DELETE FROM products WHERE id=?", (pid,)).rowcount: raise HTTPException(404, "Product not found.")
    return Response(status_code=204)

@app.post("/api/generate", status_code=201)
def generate(g: GenIn):
    """Workflow: intent -> context -> task -> prompt -> Granite (or labelled demo) -> validate -> draft for vendor review."""
    with db() as c:
        v = vendor_or_404(c); p = None
        if g.task in C.PRODUCT_TASKS:
            r = c.execute("SELECT * FROM products WHERE id=?", (g.product_id,)).fetchone() if g.product_id else None
            if not r: raise HTTPException(422, "Choose a product first.")
            p = dict(r)
        if granite.is_demo(): text, src = C.demo_text(g.task, g.language, v, p, g.festival), "demo-template"
        else:
            sysm, usr = C.build_prompt(g.task, g.language, v, p, g.festival)
            try: text, src = granite.chat(sysm, usr), "ibm-granite"
            except granite.GraniteError as e: raise HTTPException(502, f"{e}. Nothing was substituted. Try again or check IBM settings.")
        ok, why = C.validate(text)
        if not ok: raise HTTPException(422, f"{why} Please try again.")
        i = c.execute("INSERT INTO campaigns(task,language,text,source,product_id) VALUES(?,?,?,?,?)", (g.task, g.language, text, src, g.product_id)).lastrowid
        return {**dict(c.execute("SELECT * FROM campaigns WHERE id=?", (i,)).fetchone()),
                "disclaimer": "AI suggestion, not a guarantee. Review and edit before you use it. Nothing is sent automatically."}
@app.get("/api/campaigns")
def campaigns():
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM campaigns ORDER BY id DESC")]
@app.patch("/api/campaigns/{cid}")
def patch_campaign(cid: int, b: CampaignPatch):
    with db() as c:
        if not c.execute("SELECT 1 FROM campaigns WHERE id=?", (cid,)).fetchone(): raise HTTPException(404, "Campaign not found.")
        if b.text is not None:
            ok, why = C.validate(b.text)
            if not ok: raise HTTPException(422, why)
        c.execute("UPDATE campaigns SET text=COALESCE(?,text),status=COALESCE(?,status) WHERE id=?", (b.text, b.status, cid))
        return dict(c.execute("SELECT * FROM campaigns WHERE id=?", (cid,)).fetchone())
@app.delete("/api/campaigns/{cid}", status_code=204)
def del_campaign(cid: int):
    with db() as c: c.execute("DELETE FROM campaigns WHERE id=?", (cid,))
    return Response(status_code=204)

@app.get("/api/schemes")
def schemes(): return {"items": C.SCHEMES, "note": C.SCHEME_NOTE, "verified_facts": "Names and official links only", "ai_generated": False}
@app.get("/api/upi-guide")
def upi(): return {"steps": C.UPI, "safety": C.UPI_SAFETY}

@app.post("/api/demo/seed")
def seed():
    with db() as c:
        c.executescript("DELETE FROM products; DELETE FROM campaigns;")
        c.execute("INSERT OR REPLACE INTO vendor VALUES(1,'Sharma Chai & Vada Pav','Food stall','7 AM - 9 PM','hi','Andheri East, Mumbai','Demo shop for presentations',1)")
        for n, p, u, d in [("Masala Chai", 15, "cup", "Fresh ginger and elaichi"), ("Vada Pav", 20, "piece", "Hot and fresh"), ("Misal Pav", 60, "plate", "Medium spicy")]:
            c.execute("INSERT INTO products(name,price,unit,description) VALUES(?,?,?,?)", (n, p, u, d))
        return vendor_or_404(c)

@app.get("/api/profile/download")
def download_profile():
    with db() as c:
        v = vendor_or_404(c); ps = [dict(r) for r in c.execute("SELECT * FROM products")]
    e = html.escape
    rows = "".join(f"<li>{e(p['name'])} - ₹{p['price']:g}/{e(p['unit'])}</li>" for p in ps)
    page = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{e(v['shop_name'])}</title>"
            f"<body style='font-family:sans-serif;max-width:480px;margin:auto;padding:16px'><h1>{e(v['shop_name'])}</h1><p>{e(v['business_type'])} · {e(v['opening_hours'])}</p>"
            f"<p>{e(v.get('service_area') or '')}</p><p>{e(v.get('about') or '')}</p><h2>Products</h2><ul>{rows}</ul></body>")
    return Response(page, media_type="text/html", headers={"Content-Disposition": "attachment; filename=shop-profile.html"})

_S = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=_S), name="static")
@app.get("/")
def index(): return FileResponse(os.path.join(_S, "index.html"))
