"""Bộ retry dùng chung cho các tầng ghi Supabase (app/persistence/http_retry.py).

Phát sinh khi chuẩn bị deploy Render free tier: đĩa tạm thời làm data/turns.jsonl
không còn là lưới an toàn, nên lời gọi Supabase PHẢI tự chịu được lỗi thoáng qua.
`base_delay=0` trong mọi test — không test nào cần chờ thật.
"""
import httpx
import pytest

from app.persistence.http_retry import voi_retry

_URL = "https://x.test/rest/v1/turn_logs"


def _resp(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", _URL))


class _DemNoiGoi:
    """Giả lập một chuỗi hành vi qua các lần gọi: mỗi phần tử là kết quả của
    một lần `goi()` — hoặc một Exception để raise, hoặc một Response để trả."""

    def __init__(self, *hanh_vi):
        self._hanh_vi = list(hanh_vi)
        self.so_lan_goi = 0

    async def __call__(self) -> httpx.Response:
        self.so_lan_goi += 1
        buoc = self._hanh_vi.pop(0)
        if isinstance(buoc, Exception):
            raise buoc
        return buoc


# ── lỗi tầng mạng ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_thanh_cong_ngay_lan_dau_khong_can_retry():
    goi = _DemNoiGoi(_resp(200))
    r = await voi_retry(goi, base_delay=0)
    assert r.status_code == 200
    assert goi.so_lan_goi == 1


@pytest.mark.asyncio
async def test_loi_mang_thoang_qua_roi_thanh_cong():
    """Đúng tình huống thật: container Render vừa thức dậy, request đầu timeout."""
    goi = _DemNoiGoi(httpx.ConnectTimeout("chết tạm"), _resp(200))
    r = await voi_retry(goi, retries=2, base_delay=0)
    assert r.status_code == 200
    assert goi.so_lan_goi == 2


@pytest.mark.asyncio
async def test_loi_mang_lien_tuc_thi_het_luot_va_raise():
    goi = _DemNoiGoi(
        httpx.ConnectTimeout("1"), httpx.ConnectTimeout("2"), httpx.ConnectTimeout("3")
    )
    with pytest.raises(httpx.ConnectTimeout):
        await voi_retry(goi, retries=2, base_delay=0)
    assert goi.so_lan_goi == 3          # đúng 1 lần đầu + 2 lần thử lại


# ── PostgREST trả 5xx ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_5xx_duoc_retry_roi_thanh_cong():
    goi = _DemNoiGoi(_resp(503), _resp(200))
    r = await voi_retry(goi, retries=2, base_delay=0)
    assert r.status_code == 200
    assert goi.so_lan_goi == 2


@pytest.mark.asyncio
async def test_5xx_lien_tuc_thi_raise_httpstatuserror():
    goi = _DemNoiGoi(_resp(503), _resp(503), _resp(503))
    with pytest.raises(httpx.HTTPStatusError):
        await voi_retry(goi, retries=2, base_delay=0)
    assert goi.so_lan_goi == 3


# ── 4xx: KHÔNG retry, sai payload thì thử lại vẫn sai ────────────────────
@pytest.mark.asyncio
async def test_4xx_khong_retry_fail_ngay_lan_dau():
    """Hồi quy PGRST102 (GĐ6): 400 do sai schema thử lại vẫn 400 y hệt.

    Retry ở đây chỉ trì hoãn lúc _disable() cần kích hoạt, không giúp gì.
    """
    goi = _DemNoiGoi(_resp(400), _resp(200))
    with pytest.raises(httpx.HTTPStatusError):
        await voi_retry(goi, retries=2, base_delay=0)
    assert goi.so_lan_goi == 1


# ── retries=0: đúng 1 lần thử, không lùi lũy thừa ─────────────────────────
@pytest.mark.asyncio
async def test_retries_bang_khong_chi_thu_dung_mot_lan():
    goi = _DemNoiGoi(httpx.ConnectTimeout("x"))
    with pytest.raises(httpx.ConnectTimeout):
        await voi_retry(goi, retries=0, base_delay=0)
    assert goi.so_lan_goi == 1
