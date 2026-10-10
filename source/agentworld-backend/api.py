"""Read-only JSON for the Agent World dashboard (optional).

Run:  uvicorn api:app --port 8000

GET /leads?status=new&max_fraud=59   leads table
GET /drafts?state=waiting            approval inbox
POST /leads/{id}/status?status=booked

Put this behind the same login/HTTPS as the dashboard; it has no auth of its own.
"""
from fastapi import FastAPI, HTTPException

import db

app = FastAPI(title="Agent World")
db.init()


@app.get("/leads")
def leads(status: str | None = None, max_fraud: int | None = None, limit: int = 100):
    return db.list_leads(status, max_fraud, limit)


@app.get("/drafts")
def drafts(state: str = "waiting"):
    return db.list_drafts(state)


@app.post("/leads/{lead_id}/status")
def set_status(lead_id: int, status: str):
    if not db.get_lead(lead_id):
        raise HTTPException(404, "lead not found")
    try:
        db.set_lead_status(lead_id, status)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}
