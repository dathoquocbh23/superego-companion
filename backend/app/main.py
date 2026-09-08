"""FastAPI app — CORS, startup load graph + skills, health check. docx/06 §10."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assessment, chat, graph as graph_api, session
from app.config import settings
from app.graph.loader import load_graph
from app.overlay.store import get_store
from app.skills.loader import load_skills

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Graph validate fail → KHÔNG khởi động (chủ ý). docx/06 §6.
    graph = load_graph()
    skills = load_skills()
    logger.info(
        "Graph v%s: %d evidence + %d content node, %d cycle. Skills: %s",
        graph.version, len(graph.evidence_node_ids), len(graph.content_node_ids),
        len(graph.cycles), ", ".join(skills.names()),
    )
    llm_mode = (
        "OFFLINE (câu tĩnh)"
        if (settings.llm_offline or not settings.has_api_key)
        else f"{settings.llm_provider}:{settings.active_model}"
    )
    logger.info("LLM: %s", llm_mode)
    yield
    await get_store().close()


app = FastAPI(title="Chatbot đồng hành — Cái siêu tôi trừng phạt", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(assessment.router)
app.include_router(chat.router)
app.include_router(graph_api.router)


@app.get("/health")
async def health() -> dict:
    from app.graph.loader import get_graph

    g = get_graph()
    return {
        "status": "ok",
        "graph_version": g.version,
        "evidence_nodes": len(g.evidence_node_ids),
        "content_nodes": len(g.content_node_ids),
        "cycles": [c.id for c in g.cycles],
        "llm_provider": settings.llm_provider,
        "llm_model": settings.active_model,
        "llm_offline": settings.llm_offline or not settings.has_api_key,
    }
