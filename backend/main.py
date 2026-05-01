from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.config import settings
from backend.database import Base, engine, SessionLocal
from backend.seed import run_seed
from backend.routers import chat, sessions, routines, exercises, profile, progress

Base.metadata.create_all(bind=engine)

# Seed on startup
with SessionLocal() as db:
    run_seed(db)

app = FastAPI(title="Workout Tracker Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(routines.router, prefix="/api/v1")
app.include_router(exercises.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "chat.html"))

    @app.get("/{page}.html", include_in_schema=False)
    async def serve_page(page: str):
        path = os.path.join(frontend_dir, f"{page}.html")
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse(os.path.join(frontend_dir, "chat.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}
