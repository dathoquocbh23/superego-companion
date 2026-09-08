"""
Retry nhẹ cho lời gọi PostgREST — dùng chung cho các tầng ghi Supabase
(transcript.py, turnlog.py).

Phát sinh khi chuẩn bị deploy Render free tier. Trước đó, `turn_logs` coi file
`data/turns.jsonl` là lưới an toàn: Supabase lỗi tạm thời thì cứ để đó, sau
chạy `scripts/backfill_turnlogs.py` là bù lại được. Free tier của Render dùng
ĐĨA TẠM THỜI — container khởi động lại (deploy mới, hoặc rảnh rồi tự ngủ/thức)
là toàn bộ `data/` mất sạch CÙNG LÚC với bản ghi trong RAM. Lưới an toàn đó
không còn, nên một lỗi mạng thoáng qua lúc container vừa thức dậy — tình huống
rất hay gặp trên free tier — giờ là mất dữ liệu vĩnh viễn, im lặng.

`messages` / `conversations` (transcript.py) chưa từng có file dự phòng — vốn
đã ở mức phơi nhiễm tối đa ngay từ đầu, retry ở đây quan trọng ngang `turn_logs`.

CHỈ retry lỗi TẠM THỜI:
  - lỗi tầng mạng (timeout, connect refused, DNS…) — httpx.TransportError
  - PostgREST trả 5xx — chính DB/service đang có vấn đề, không phải payload sai

KHÔNG retry 4xx: payload/schema sai thì thử lại vẫn sai y hệt (đúng kiểu
PGRST102 "All object keys must match" đã gặp ở GĐ6) — retry chỉ trì hoãn lúc
`_disable()` cần kích hoạt để caller biết mà xử lý.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

_STATUS_TAM_THOI = {500, 502, 503, 504}


async def voi_retry(
    goi: Callable[[], Awaitable[httpx.Response]],
    *,
    retries: int = 2,
    base_delay: float = 0.6,
) -> httpx.Response:
    """Gọi `goi()` với tối đa `retries` lần thử lại thêm. Không raise ngoài dự kiến.

    `goi` phải TẠO COROUTINE MỚI mỗi lần gọi — truyền vào dạng
    `lambda: client.post(url, ...)`, không phải một coroutine đã await dở
    (coroutine chỉ dùng được một lần).
    """
    for attempt in range(retries + 1):
        try:
            r = await goi()
        except httpx.TransportError:
            if attempt == retries:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
            continue
        if getattr(r, "status_code", 200) in _STATUS_TAM_THOI and attempt < retries:
            await asyncio.sleep(base_delay * (2**attempt))
            continue
        r.raise_for_status()
        return r
    raise AssertionError("unreachable")  # vòng lặp luôn return hoặc raise ở trên
