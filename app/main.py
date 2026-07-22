"""
TN Compliance Copilot — app entrypoint.

Feature-modular by design: each feature lives under app/features/<name>/
with its own router, and registers itself here with app.include_router().
Adding CMDA/GCC jurisdictions, sketch upload, or accounts later means
adding a new feature folder and one line here — the compliance feature
should not need to change.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.features.compliance.router import router as compliance_router

app = FastAPI(title="TN Compliance Copilot")

app.include_router(compliance_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve the frontend last so /api/* routes above take precedence.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
