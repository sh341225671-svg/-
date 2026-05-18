import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import projects, chapters, agents, writing, volumes, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="言灵创作引擎", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(agents.router)
app.include_router(writing.router)
app.include_router(volumes.router)
app.include_router(chat.router)


from fastapi.responses import RedirectResponse


@app.get("/api/info")
async def api_info():
    return {"name": "言灵创作引擎", "version": "0.1.0"}


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")


FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
