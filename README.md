# DukaanSaathi AI (IBM SkillsBuild AICTE-2026, Problem #29)
Digital shop profile, catalogue and marketing assistant for street vendors. English / Hindi / Marathi.

## Run
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # leave blank to run in labelled DEMO mode
uvicorn app.main:app --reload                          # open http://127.0.0.1:8000  (API docs: /docs)
python -m pytest -q
```
## IBM Granite (real mode)
Create a watsonx.ai project on IBM Cloud (Lite plan), then set `IBM_API_KEY`, `IBM_PROJECT_ID`, `IBM_REGION_URL` in `.env` and `DEMO_MODE=false`.
The app calls IAM (`iam.cloud.ibm.com/identity/token`) then `POST {region}/ml/v1/text/chat?version=2025-10-25` with model `ibm/granite-4-h-small` (per IBM's Granite docs).
If IBM fails the API returns 502; it never silently swaps in demo text. The banner and each draft show the true source.
**Not verified here:** no IBM credentials were available, so the live call is untested. Confirm model availability and Lite quotas in your account.

## Flow
vendor request -> context (shop + product from SQLite) -> task prompt -> Granite (or labelled demo) -> validator (length, markup, risky claims, PIN/OTP asks) -> saved as *draft* -> vendor edits and approves. Nothing is sent, bought or submitted.

## Limits (prototype)
Single vendor, no login, SQLite; add auth and per-vendor rows before real use. Scheme section lists names and official links only, no benefits or eligibility copied.
