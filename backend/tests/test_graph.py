from app.graph.loader import GraphService, GraphValidationError
from app.config import settings


def test_counts(graph):
    assert len(graph.evidence_node_ids) == 31  # 24 gốc + 7 tầng đời sống
    # 18 gốc + 8 mục lý thuyết trích 09/09/2026 (docx/13 §11)
    assert len(graph.content_node_ids) == 26
    assert len(graph.policy_edges()) == 13  # 8 gốc + 3 nhánh xấu hổ + 2 nhánh đời sống


def test_every_content_node_resolves(graph):
    for nid in graph.content_node_ids:
        assert graph.content_body(nid) is not None, nid


def test_every_evidence_node_has_cues(graph):
    for nid in graph.evidence_node_ids:
        assert len(graph.node(nid).cues) >= 3, nid


def test_cycle_nodes_exist(graph):
    for c in graph.cycles:
        for nid in c.nodes:
            assert graph.node(nid) is not None


def test_policy_edges_have_priority(graph):
    for e in graph.policy_edges():
        assert e.priority is not None


def test_risk_adjacent_flag(graph):
    assert graph.node("a-vo-vong").risk_adjacent is True


def test_broken_graph_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "version: '1'\nnodes:\n  - {id: x, type: manifestation, label: X, cues: [a]}\n"
        "edges: []\ncycles: []\n",
        encoding="utf-8",
    )
    try:
        GraphService(bad, settings.content_dir)
        assert False, "phải raise"
    except GraphValidationError:
        pass
