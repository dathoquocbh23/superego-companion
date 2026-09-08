import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # kích hoạt lifespan
        async with app.router.lifespan_context(app):
            yield c


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["evidence_nodes"] == 31
    assert body["content_nodes"] == 18


@pytest.mark.asyncio
async def test_session_then_assessment_seed(client):
    r = await client.post("/api/session")
    sid = r.json()["session_id"]

    spec = await client.get("/api/assessment")
    assert len(spec.json()["items"]) == 10

    # band CAO: tất cả 5
    answers = {str(i): 5 for i in range(1, 11)}
    r2 = await client.post("/api/assessment", json={"session_id": sid, "answers": answers})
    body = r2.json()
    assert body["average"] == 5.0
    assert body["band"] == "CAO"
    assert body["next_actions"][0]["href"].startswith("/chat")

    # overlay đã được seed 10 node LIKERT
    hist = await client.get(f"/api/chat/history/{sid}")
    assert hist.status_code == 200


@pytest.mark.asyncio
async def test_assessment_band_mapping(client):
    r = await client.post("/api/session")
    sid = r.json()["session_id"]
    # trung bình 3.4 → DANG_CHU_Y (ví dụ trong tài liệu: 34/50)
    answers = {str(i): (4 if i <= 4 else 3) for i in range(1, 11)}
    total = sum(answers.values())
    r2 = await client.post("/api/assessment", json={"session_id": sid, "answers": answers})
    body = r2.json()
    assert body["total"] == total
    assert body["band"] in {"NHE", "DANG_CHU_Y"}


@pytest.mark.asyncio
async def test_chat_stream_sse(client):
    r = await client.post("/api/session")
    sid = r.json()["session_id"]
    async with client.stream("POST", "/api/chat/stream", json={"session_id": sid, "message": "mình hay tự trách bản thân khi mắc lỗi"}) as resp:
        assert resp.status_code == 200
        text = ""
        async for chunk in resp.aiter_text():
            text += chunk
    assert "event: meta" in text
    assert "event: done" in text


@pytest.mark.asyncio
async def test_chat_stream_crisis_no_tokens(client):
    r = await client.post("/api/session")
    sid = r.json()["session_id"]
    async with client.stream("POST", "/api/chat/stream", json={"session_id": sid, "message": "mình muốn tự tử"}) as resp:
        text = ""
        async for chunk in resp.aiter_text():
            text += chunk
    assert "CRISIS_CARD" in text
    assert "event: token" not in text
