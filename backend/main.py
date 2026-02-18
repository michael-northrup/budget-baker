import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers import upload, categorize, export

app = FastAPI(title="Budget Baker API", version="2.0.0")

# CORS for local dev (Vite dev server on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(categorize.router, prefix="/api", tags=["categorize"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "budget-baker", "version": "2.0.0"}


# Serve the React build — must be last so it doesn't catch /api/* routes
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
