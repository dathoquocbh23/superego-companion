"""
GraphService — đọc YAML → networkx, validate lúc startup. docx/06 §6.

Luật: _validate() fail → KHÔNG cho app khởi động.
Graph sai âm thầm nguy hiểm hơn app không chạy.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from app.config import settings

from .schema import CONTENT_TYPES, EVIDENCE_TYPES, BridgeConfig, Cycle, Edge, Node


class GraphValidationError(RuntimeError):
    pass


class GraphService:
    def __init__(self, path: Path, content_dir: Path):
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.version: str = str(raw.get("version", "0"))
        self.reviewed_by = raw.get("reviewed_by")

        self.nodes: dict[str, Node] = {n["id"]: Node(**n) for n in raw["nodes"]}
        self.edges: list[Edge] = [Edge(**e) for e in raw["edges"]]
        self.cycles: list[Cycle] = [Cycle(**c) for c in raw.get("cycles", [])]
        self.bridge = BridgeConfig(**raw.get("bridge", {}))
        self.default_coping: str = raw.get("default_coping", "k-nhan-dien-tu-phe-phan")

        self.g = nx.MultiDiGraph()
        for node in self.nodes.values():
            self.g.add_node(node.id, **node.model_dump())
        for e in self.edges:
            self.g.add_edge(e.from_, e.to, key=e.type, **e.model_dump(by_alias=True))

        self._content_dir = content_dir
        self._validate()

    # ---- lookups ---------------------------------------------------------
    @property
    def evidence_node_ids(self) -> list[str]:
        return [n.id for n in self.nodes.values() if n.type in EVIDENCE_TYPES]

    @property
    def content_node_ids(self) -> list[str]:
        return [n.id for n in self.nodes.values() if n.type in CONTENT_TYPES]

    def node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def neighbors(self, node_id: str) -> set[str]:
        out: set[str] = set()
        if node_id in self.g:
            out.update(self.g.successors(node_id))
            out.update(self.g.predecessors(node_id))
        return out

    def policy_edges(self) -> list[Edge]:
        return [e for e in self.edges if e.type == "addressed_by"]

    def explained_by(self, node_id: str) -> list[str]:
        return [e.to for e in self.edges if e.type == "explained_by" and e.from_ == node_id]

    # ---- lý thuyết để ĐỊNH HƯỚNG prompt (không phải để đọc ra) -----------
    # Đối chiếu AGENT3_MENTOR_SKILL.md: {THEORY_CONTENT} được nhét vào system
    # prompt để mô hình biết nền lý thuyết, KHÔNG để nó chép lại cho người dùng.
    # Trước 07/09/2026 lý thuyết trong concepts.yaml chỉ tới được gate SUPPORT
    # — mà SUPPORT thì không bao giờ với tới vì gate kẹt ở CLARIFY. Lý thuyết
    # nằm đó chết. Hai hàm dưới đưa nó vào MỌI gate.
    THEORY_FALLBACK = "c-lanh-manh-vs-trung-phat"

    def theory_for(self, node_id: str | None) -> str | None:
        """Concept node giải thích node bằng chứng này. 3 nấc, luôn ra kết quả.

        1. cạnh explained_by trực tiếp
        2. hàng xóm 1 bước có explained_by (đa số trigger/affect/impact rơi vào đây)
        3. khái niệm mặc định — thà có nền chung còn hơn prompt trống
        """
        if node_id is None:
            return self.THEORY_FALLBACK
        direct = self.explained_by(node_id)
        if direct:
            return direct[0]
        for nb in sorted(self.neighbors(node_id)):
            hop = self.explained_by(nb)
            if hop:
                return hop[0]
        return self.THEORY_FALLBACK

    def theory_steer(self, node_id: str | None) -> str:
        """Đoạn lý thuyết cô đọng để nhét vào prompt. Rỗng => trả chuỗi rỗng."""
        concept = self.theory_for(node_id)
        body = self.content_body(concept) if concept else None
        return ((body or {}).get("steer") or "").strip()

    def escalates_to(self, node_id: str) -> list[str]:
        return [e.to for e in self.edges if e.type == "escalates_to" and e.from_ == node_id]

    def cycle_for(self, node_id: str) -> Cycle | None:
        for c in self.cycles:
            if node_id in c.nodes:
                return c
        return None

    def content_body(self, node_id: str) -> dict[str, Any] | None:
        """Đọc đoạn văn duyệt sẵn theo content_ref 'content/xxx.yaml#anchor'."""
        node = self.nodes.get(node_id)
        if not node or not node.content_ref:
            return None
        rel, _, anchor = node.content_ref.partition("#")
        fname = Path(rel).name
        data = _load_content_file(self._content_dir / fname)
        return data.get(anchor)

    # ---- validation ----------------------------------------------------
    def _validate(self) -> None:
        errors: list[str] = []
        ids = set(self.nodes)

        ev = self.evidence_node_ids
        ct = self.content_node_ids
        # 24 gốc + 7 tầng đời sống (07/09/2026: 4 trigger + 3 affect cơ bản).
        if len(ev) != 31:
            errors.append(f"cần 31 evidence node, đang có {len(ev)}")
        # 18 gốc + 8 mục lý thuyết trích 09/09/2026 (docx/13 §11): mục 3, 4, 6, 7
        # của docx siêu tôi · 2 mục của docx nhận diện · 2 mục của docx tìm hỗ trợ.
        if len(ct) != 26:
            errors.append(f"cần 26 content node, đang có {len(ct)}")

        for e in self.edges:
            if e.from_ not in ids:
                errors.append(f"cạnh {e.type}: 'from' không tồn tại: {e.from_}")
            if e.to not in ids:
                errors.append(f"cạnh {e.type}: 'to' không tồn tại: {e.to}")

        for n in self.nodes.values():
            if n.type in EVIDENCE_TYPES and len(n.cues) < 3:
                errors.append(f"evidence node {n.id} chỉ có {len(n.cues)} cues (cần ≥ 3)")
            if n.type in CONTENT_TYPES:
                if not n.content_ref:
                    errors.append(f"content node {n.id} thiếu content_ref")
                elif self.content_body(n.id) is None:
                    errors.append(f"content node {n.id}: content_ref không resolve được ({n.content_ref})")
                elif n.type == "concept" and not (self.content_body(n.id) or {}).get("steer"):
                    # Thiếu `steer` thì prompt mất nền lý thuyết mà KHÔNG BÁO GÌ —
                    # đúng kiểu hỏng âm thầm đã đẻ ra bot nói vòng vo. Chặn ở startup.
                    errors.append(f"concept node {n.id} thiếu `steer` trong content file")

        for c in self.cycles:
            missing = [x for x in c.nodes if x not in ids]
            if missing:
                errors.append(f"cycle {c.id} có node không tồn tại: {missing}")
            if c.min_nodes_to_activate > len(c.nodes):
                errors.append(f"cycle {c.id}: min_nodes_to_activate > số node")

        pe = self.policy_edges()
        # 13 = 8 cạnh gốc (docx/03 §5) + 3 nhánh xấu hổ / giá trị bản thân thấp
        #      + 2 nhánh đời sống (a-buon, a-tuc-gian) thêm 07/09/2026.
        # ⚠️ Con số này có trong docx/03 §5 — sửa graph thì phải sửa tài liệu theo.
        if len(pe) != 13:
            errors.append(f"cần 13 policy edge (addressed_by), đang có {len(pe)}")
        for e in pe:
            if e.priority is None:
                errors.append(f"policy edge {e.from_}->{e.to} thiếu priority")

        if errors:
            raise GraphValidationError(
                "Domain graph không hợp lệ:\n  - " + "\n  - ".join(errors)
            )


@lru_cache(maxsize=8)
def _load_content_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


_service: GraphService | None = None


def load_graph() -> GraphService:
    global _service
    if _service is None:
        _service = GraphService(settings.graph_path, settings.content_dir)
    return _service


def get_graph() -> GraphService:
    if _service is None:
        raise RuntimeError("Graph chưa được load — gọi load_graph() lúc startup")
    return _service
