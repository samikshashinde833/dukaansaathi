# DukaanSaathi AI

Digital shop profile, product catalogue and marketing assistant for street vendors. Works in English, Hindi and Marathi.

Built for IBM SkillsBuild AICTE-2026, Problem #29 (Street Vendor Digitalization Agent).

**Live demo:** https://dukaansaathi-gamma.vercel.app/

## Features
- Create a shop profile and add products with price and unit
- Generate WhatsApp messages, product descriptions, festival messages, social captions and marketing tips
- Edit, approve, copy and download messages
- Download a shareable shop profile page
- UPI guide and official government scheme links
- Backup and restore your data as a file

## How it works
- Shop, products and saved messages are stored in your **browser (localStorage)**, so they stay after refresh and restart. They are not shared between devices; use Backup and Restore to move them.
- The server (FastAPI) only writes the message text. It stores no data.
- Without IBM keys the app runs in a clearly labelled **DEMO MODE** using templates. With keys it uses IBM Granite on watsonx.ai.
- Every message is a draft. The vendor reviews and approves it. Nothing is sent automatically.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # leave keys blank for DEMO mode
uvicorn app.main:app --reload                        # open http://127.0.0.1:8000
python -m pytest -q
```

## IBM Granite (optional)
Set these in `.env` (or in the Vercel project's Environment Variables):

| Variable | Value |
|---|---|
| `IBM_API_KEY` | your IBM Cloud API key |
| `IBM_PROJECT_ID` | your watsonx.ai project ID |
| `IBM_REGION_URL` | e.g. `https://us-south.ml.cloud.ibm.com` |
| `DEMO_MODE` | `false` |

Never commit real keys. If IBM fails, the app shows an error instead of silently using demo text.

## Deploy on Vercel
1. Push this repo to GitHub.
2. Import it in Vercel. No build settings are needed (`index.py` and `vercel.json` are included).
3. Add the IBM variables above if you want real AI mode.

## Tech
Python FastAPI, HTML/CSS/JavaScript (mobile-first), browser localStorage, IBM Granite (optional).

## Limits
Prototype for a single vendor per browser, with no login. Add authentication and a database before real use. Scheme section lists names and official links only.
