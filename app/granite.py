"""IBM Granite via watsonx.ai REST. Endpoint/model id follow IBM Granite docs
(https://www.ibm.com/granite/docs/models/granite4-0); re-verify region/quota in your IBM Cloud account."""
import os, time, httpx
_tok = {"v": None, "exp": 0}
class GraniteError(Exception): pass

def configured(): return bool(os.getenv("IBM_API_KEY") and os.getenv("IBM_PROJECT_ID"))
def is_demo(): return os.getenv("DEMO_MODE", "").lower() == "true" or not configured()
def model(): return os.getenv("IBM_MODEL_ID", "ibm/granite-4-h-small")

def _token():
    if _tok["v"] and time.time() < _tok["exp"] - 60: return _tok["v"]
    try:
        r = httpx.post("https://iam.cloud.ibm.com/identity/token",
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": os.environ["IBM_API_KEY"]},
            headers={"Accept": "application/json"}, timeout=20)
        r.raise_for_status(); j = r.json()
    except Exception as e: raise GraniteError(f"IBM authentication failed ({type(e).__name__})")
    _tok.update(v=j["access_token"], exp=time.time() + int(j.get("expires_in", 3000)))
    return _tok["v"]

def chat(system: str, user: str) -> str:
    base = os.getenv("IBM_REGION_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    url = f"{base}/ml/v1/text/chat?version={os.getenv('IBM_API_VERSION','2025-10-25')}"
    body = {"model_id": model(), "project_id": os.environ["IBM_PROJECT_ID"], "max_tokens": 500, "temperature": 0.4,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    try:
        r = httpx.post(url, json=body, headers={"Authorization": f"Bearer {_token()}"}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except GraniteError: raise
    except Exception as e: raise GraniteError(f"IBM Granite request failed ({type(e).__name__})")
