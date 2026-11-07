"""DukaanSaathi AI - stateless API.

Shop, products and saved messages now live in the BROWSER (localStorage).
Vercel serverless functions have no persistent disk and every request can hit a
different instance, so the old SQLite file kept disappearing (that is why the app
asked you to create the shop again). The server now only does the AI step:
the browser sends the shop + product it wants a message for, and gets text back.
"""
import os
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import granite, content as C

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastAPI(title="DukaanSaathi AI", version="0.2")
Lang = Literal["en", "hi", "mr"]


def _clean(v):
    if v is None:
        return v
    v = v.strip()
    if any(ch in v for ch in "<>") or any(ord(ch) < 32 for ch in v):
        raise ValueError("Remove special characters like < >")
    return v


class VendorCtx(BaseModel):
    shop_name: str = Field(min_length=2, max_length=80)
    business_type: str = Field(min_length=2, max_length=60)
    opening_hours: str = Field(min_length=2, max_length=60)
    language: Lang = "en"
    service_area: Optional[str] = Field(None, max_length=100)
    about: Optional[str] = Field(None, max_length=500)

    @field_validator("shop_name", "business_type", "opening_hours", "service_area", "about")
    @classmethod
    def _c(cls, v):
        return _clean(v)


class ProductCtx(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, le=100000)
    unit: str = Field("piece", min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=300)

    @field_validator("name", "unit", "description")
    @classmethod
    def _c(cls, v):
        return _clean(v)


class GenIn(BaseModel):
    task: Literal["product_description", "whatsapp_promo", "festival_offer", "social_caption", "marketing_tips"]
    language: Lang = "en"
    festival: Optional[str] = Field(None, max_length=40)
    vendor: VendorCtx
    product: Optional[ProductCtx] = None

    @field_validator("festival")
    @classmethod
    def _c(cls, v):
        return _clean(v)


@app.get("/api/status")
def status():
    d = granite.is_demo()
    return {"mode": "demo" if d else "ibm-granite", "model": None if d else granite.model(),
            "label": "DEMO MODE: sample text from templates, not IBM Granite" if d else f"IBM Granite ({granite.model()})"}


@app.post("/api/generate")
def generate(g: GenIn):
    """Workflow: intent -> context (sent by browser) -> prompt -> Granite (or labelled demo) -> validate -> draft."""
    v = g.vendor.model_dump()
    p = None
    if g.task in C.PRODUCT_TASKS:
        if not g.product:
            raise HTTPException(422, "Choose a product first.")
        p = g.product.model_dump()

    if granite.is_demo():
        text, src = C.demo_text(g.task, g.language, v, p, g.festival), "demo-template"
    else:
        sysm, usr = C.build_prompt(g.task, g.language, v, p, g.festival)
        try:
            text, src = granite.chat(sysm, usr), "ibm-granite"
        except granite.GraniteError as e:
            raise HTTPException(502, f"{e}. Nothing was substituted. Try again or check IBM settings.")

    ok, why = C.validate(text)
    if not ok:
        raise HTTPException(422, f"{why} Please try again.")
    return {"task": g.task, "language": g.language, "text": text, "source": src, "status": "draft",
            "disclaimer": "AI suggestion, not a guarantee. Review and edit before you use it. Nothing is sent automatically."}


@app.post("/api/validate")
def validate_text(b: dict):
    ok, why = C.validate(str(b.get("text", "")))
    return {"ok": ok, "reason": why}


@app.get("/api/schemes")
def schemes():
    return {"items": C.SCHEMES, "note": C.SCHEME_NOTE, "verified_facts": "Names and official links only", "ai_generated": False}


@app.get("/api/upi-guide")
def upi():
    return {"steps": C.UPI, "safety": C.UPI_SAFETY}


_S = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=_S), name="static")


@app.get("/")
@app.get("/api/index")
def index():
    return FileResponse(os.path.join(_S, "index.html"), headers={"Cache-Control": "no-cache"})