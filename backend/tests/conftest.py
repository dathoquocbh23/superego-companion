from __future__ import annotations

import os
import sys

os.environ.setdefault("LLM_OFFLINE", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("REDIS_URL", "")  # test không cần Redis — overlay sống trong RAM

# Bộ nhớ dài hạn TẮT trong test. Biến môi trường thắng .env trong pydantic-settings,
# nên dù .env thật có SUPABASE_* thì bộ test vẫn không chạm mạng. Test mà phụ thuộc
# Supabase sống hay chết thì nó không còn là test nữa.
os.environ["MEMORY_ENABLED"] = "false"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pytest

from app.graph.loader import load_graph
from app.skills.loader import load_skills


@pytest.fixture(scope="session", autouse=True)
def _bootstrap():
    load_graph()
    load_skills()


@pytest.fixture
def graph():
    return load_graph()


@pytest.fixture
def skills():
    return load_skills()
