"""Truy cập bộ nhớ dài hạn trên Supabase qua PostgREST. docx/12 §4.

Cố tình KHÔNG dùng driver Postgres: DDL đã chạy sẵn bằng file trong
db/migrations, còn CRUD lúc chạy thì PostgREST làm đủ — thêm psycopg chỉ để
insert vài dòng là gánh thêm một phụ thuộc nhị phân cho mỗi máy cài dự án.
`httpx` thì đã có sẵn vì client LLM đang dùng.

Nuốt lỗi theo đúng cách của telemetry và Redis: bộ nhớ hỏng KHÔNG được làm
hỏng lượt chat. Mất trí nhớ còn hơn mất phiên tư vấn.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(4.0, connect=2.0)


@dataclass(frozen=True)
class MemoryNode:
    node_id: str
    confidence: float
    observations: int
    last_seen: datetime
    verbatim: str = ""      # nguyên văn học sinh nói, "" nếu chưa có/đã xoá


def _parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


class MemoryStore:
    """Một instance cho cả tiến trình. An toàn khi bộ nhớ đang tắt."""

    def __init__(self, url: str, service_key: str):
        self._base = url.rstrip("/")
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }
        self._degraded = False

    def _disable(self, reason: str) -> None:
        if not self._degraded:
            logger.warning("Bộ nhớ dài hạn không khả dụng (%s) — chạy không có bộ nhớ", reason)
        self._degraded = True

    @property
    def available(self) -> bool:
        return settings.memory_ready and not self._degraded

    async def memory_enabled_for(self, user_id: str) -> bool:
        """Người dùng đã BẬT ghi nhớ chưa. Chưa bật => coi như không có bộ nhớ."""
        if not self.available:
            return False
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                r = await c.get(
                    f"{self._base}/rest/v1/app_users",
                    headers=self._headers,
                    params={"id": f"eq.{user_id}", "select": "memory_enabled", "limit": 1},
                )
                r.raise_for_status()
                rows = r.json()
                return bool(rows and rows[0].get("memory_enabled"))
        except Exception as exc:
            self._disable(f"app_users {exc}")
            return False

    async def load(self, user_id: str, limit: int) -> list[MemoryNode]:
        """Node mạnh nhất, mới nhất trước. Phân rã áp ở tầng service."""
        if not self.available:
            return []
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                r = await c.get(
                    f"{self._base}/rest/v1/user_memory",
                    headers=self._headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "select": "node_id,confidence,observations,last_seen,verbatim",
                        "order": "confidence.desc,last_seen.desc",
                        "limit": limit,
                    },
                )
                r.raise_for_status()
                return [
                    MemoryNode(
                        node_id=row["node_id"],
                        confidence=float(row["confidence"]),
                        observations=int(row["observations"]),
                        last_seen=_parse_ts(row["last_seen"]),
                        verbatim=row.get("verbatim") or "",
                    )
                    for row in r.json()
                ]
        except Exception as exc:
            self._disable(f"user_memory {exc}")
            return []

    async def record(
        self, user_id: str, session_hash: str, turn_id: int, nodes: list[dict]
    ) -> None:
        """Gọi RPC ghi_nho_luot — node + cạnh + nhật ký trong một giao dịch."""
        if not self.available or not nodes:
            return
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
                r = await c.post(
                    f"{self._base}/rest/v1/rpc/ghi_nho_luot",
                    headers=self._headers,
                    json={
                        "p_user_id": user_id,
                        "p_session_hash": session_hash,
                        "p_turn_id": turn_id,
                        "p_nodes": nodes,
                    },
                )
                r.raise_for_status()
        except Exception as exc:
            self._disable(f"ghi_nho_luot {exc}")


_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore(settings.supabase_url, settings.supabase_service_role_key)
    return _store
