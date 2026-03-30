"""FastAPI application entry point."""
from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Agent Harness backend...")
    settings.ensure_dirs()

    # Initialize default personality files if missing
    soul_path = settings.personality_dir / "soul.md"
    agent_path = settings.personality_dir / "agent.md"
    default_dir = Path(__file__).parent / "data" / "personality"
    if not soul_path.exists() and (default_dir / "soul.md").exists():
        import shutil
        shutil.copy(default_dir / "soul.md", soul_path)
    if not agent_path.exists() and (default_dir / "agent.md").exists():
        import shutil
        shutil.copy(default_dir / "agent.md", agent_path)

    logger.info("Agent Harness backend ready")
    yield

    logger.info("Agent Harness backend shutdown complete")


app = FastAPI(
    title="Agent Harness",
    description="A production-ready agentic AI framework with 5-tier memory, project isolation, and autonomous tasks.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    return {"message": "Agent Harness API", "docs": "/docs"}
