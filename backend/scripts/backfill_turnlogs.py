"""
Nạp data/turns.jsonl đã thu được từ trước lên bảng turn_logs. GĐ6b.

Trước 07/09/2026 mọi lượt chỉ ghi ra file. Số liệu đó vẫn dùng được cho bài
báo — script này đưa nó lên Supabase để truy vấn bằng SQL thay vì phải grep.

CHẠY:
    python scripts/backfill_turnlogs.py --dry-run    # xem sẽ đẩy bao nhiêu
    python scripts/backfill_turnlogs.py              # đẩy thật

AN TOÀN KHI CHẠY LẠI: bảng turn_logs không có ràng buộc UNIQUE nào, nên chạy
hai lần là nhân đôi dữ liệu. Script tự đọc cặp (session_hash, turn_id) đã có
trên Supabase và bỏ qua chúng. Cặp này là khoá tự nhiên: một phiên không thể
có hai lượt cùng số.

⚠️ File có thể chứa bản ghi từ KIẾN TRÚC CŨ (trước GĐ2/GĐ4) — gate khác, flag
khác. Đó là dữ liệu thật, không phải rác, nhưng khi phân tích phải lọc theo
`ts` chứ đừng trộn hai giai đoạn vào một biểu đồ.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.config import settings  # noqa: E402
from app.persistence.turnlog import get_turnlog_store  # noqa: E402

BATCH = 200


def doc_file(path: Path) -> list[dict]:
    rows: list[dict] = []
    for so, dong in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        dong = dong.strip()
        if not dong:
            continue
        try:
            rows.append(json.loads(dong))
        except json.JSONDecodeError:
            print(f"  bỏ dòng {so}: không phải JSON hợp lệ")
    return rows


async def _get_voi_retry(c: httpx.AsyncClient, url: str, **kw) -> httpx.Response:
    """GET với 2 lần thử lại — mạng chập chờn không nên làm hỏng cả lần chạy.

    Gặp thật khi kiểm chứng GĐ6b: ConnectTimeout thoáng qua giữa hai lời gọi
    liên tiếp tới cùng một host, tự hết ngay lần thử sau.
    """
    last: Exception | None = None
    for lan in range(3):
        try:
            r = await c.get(url, **kw)
            r.raise_for_status()
            return r
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last = exc
            if lan < 2:
                await asyncio.sleep(1.5 * (lan + 1))
    raise last  # type: ignore[misc]


async def da_co_tren_supabase() -> set[tuple[str, int]]:
    """Cặp (session_hash, turn_id) đã nằm trên bảng."""
    h = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    ra: set[tuple[str, int]] = set()
    async with httpx.AsyncClient(timeout=20) as c:
        offset = 0
        while True:
            r = await _get_voi_retry(
                c, f"{settings.supabase_url}/rest/v1/turn_logs",
                headers={**h, "Range-Unit": "items", "Range": f"{offset}-{offset + 999}"},
                params={"select": "session_hash,turn_id"},
            )
            batch = r.json()
            if not batch:
                break
            ra.update((x["session_hash"], x["turn_id"]) for x in batch)
            if len(batch) < 1000:
                break
            offset += 1000
    return ra


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ đếm, không ghi")
    ap.add_argument("--file", default=None, help="mặc định: settings.log_path")
    args = ap.parse_args()

    if not settings.turnlog_ready:
        print("turnlog chưa sẵn sàng — thiếu SUPABASE_* hoặc TURNLOG_SUPABASE_ENABLED=false")
        return 1

    path = Path(args.file) if args.file else settings.log_path
    if not path.exists():
        print(f"không thấy file {path}")
        return 1

    rows = doc_file(path)
    print(f"đọc {len(rows)} bản ghi từ {path}")

    da_co = await da_co_tren_supabase()
    print(f"trên Supabase đã có {len(da_co)} cặp (session_hash, turn_id)")

    moi, trung = [], 0
    for r in rows:
        khoa = (r.get("session_hash"), r.get("turn_id"))
        if khoa in da_co:
            trung += 1
            continue
        da_co.add(khoa)          # chặn cả trùng NGAY TRONG file
        moi.append(r)
    print(f"bỏ qua {trung} bản ghi đã có · sẽ đẩy {len(moi)}")

    if args.dry_run or not moi:
        return 0

    store = get_turnlog_store()
    xong = 0
    for i in range(0, len(moi), BATCH):
        lo = moi[i: i + BATCH]
        if not await store.push(lo):
            print(f"  dừng ở lô {i // BATCH + 1} — xem log để biết lý do")
            break
        xong += len(lo)
        print(f"  đã đẩy {xong}/{len(moi)}")
    print(f"xong: {xong} bản ghi")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
