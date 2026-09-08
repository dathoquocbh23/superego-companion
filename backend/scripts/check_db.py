"""Kiểm schema Supabase đã chạy đủ db/migrations/*.sql chưa.

    python scripts/check_db.py                     # đọc backend/.env
    python scripts/check_db.py --env-file X.env    # đọc file khác

Lý do tồn tại: quên chạy một file SQL thì app lỗi ở tận lúc bấm nút, với thông
báo kiểu 'relation does not exist' chẳng nói lên điều gì. Script này chỉ đúng
file còn thiếu. (Cùng vai trò với scripts/check-db.mjs bên app-duong-sau.)

CHỈ ĐỌC — không tạo, không sửa, không xoá dữ liệu.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

# Console Windows mặc định cp1252 — không in được tiếng Việt có dấu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# [file sql, mô tả, bảng, cột cần có]
CAN_CO = [
    ("001_init", "phiên hội thoại", "conversations", "session_id"),
    ("001_init", "phiên gắn tài khoản", "conversations", "user_id"),
    ("001_init", "tin nhắn", "messages", "message_type"),
    ("001_init", "kết quả thang đo", "assessment_results", "band"),
    ("001_init", "telemetry không PII", "turn_logs", "session_hash"),
    ("002_memory", "hồ sơ + opt-in bộ nhớ", "app_users", "memory_enabled"),
    ("002_memory", "bộ nhớ: trọng số node", "user_memory", "confidence"),
    ("002_memory", "bộ nhớ: trọng số cạnh", "user_memory_edges", "weight"),
    ("002_memory", "nhật ký quan sát", "user_memory_events", "source"),
    ("003_consent", "ghi nhận đồng ý", "app_users", "consent_at"),
    ("003_consent", "cờ dưới 16 tuổi", "app_users", "duoi_16"),
    ("003_consent", "đồng ý người giám hộ", "app_users", "guardian_consent"),
    ("004_verbatim", "nguyên văn theo node", "user_memory", "verbatim"),
    ("004_verbatim", "nguyên văn trong nhật ký", "user_memory_events", "verbatim"),
]

# RPC chỉ cấp cho `authenticated`. Gọi bằng service_role thì auth.uid() là NULL
# nên hàm ném lỗi ("chua dang nhap") — 4xx là ĐÚNG, nghĩa là hàm CÓ tồn tại.
#
# ⚠️ PostgREST phân giải hàm theo TÊN THAM SỐ. Gọi thiếu tham số thì nó báo
# 404 PGRST202 y như hàm không tồn tại — nên phải truyền đủ, nếu không check
# này báo thiếu oan (đã dính 07/09/2026).
RPC_CAN_CO = [
    ("003_consent", "bat_bo_nho",
     {"p_duoi_16": False, "p_guardian_consent": False, "p_consent_version": "checkdb"}),
    ("003_consent", "tat_bo_nho", {}),
    ("004_verbatim", "xoa_nguyen_van", {}),
]


def doc_env(path: Path) -> dict[str, str]:
    if not path.exists():
        sys.exit(f"Không thấy file env: {path}")
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=str(BACKEND_ROOT / ".env"))
    args = ap.parse_args()

    env = doc_env(Path(args.env_file))
    url = env.get("SUPABASE_URL", "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        sys.exit(
            "Thiếu SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY trong "
            f"{args.env_file}. Xem docx/12 §8."
        )

    ref = re.sub(r"^https?://", "", url).split(".")[0]
    print(f"Project: {ref}\n")

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    thieu = 0

    with httpx.Client(timeout=10.0, headers=headers) as c:
        for ten, mo, bang, cot in CAN_CO:
            try:
                r = c.get(f"{url}/rest/v1/{bang}", params={"select": cot, "limit": 1})
                if r.status_code == 200:
                    print(f"PASS  {ten}.sql — {mo}")
                else:
                    thieu += 1
                    print(f"FAIL  {ten}.sql — {mo}")
                    print(f"      {bang}.{cot}: {r.status_code} {r.text[:120]}")
            except Exception as exc:
                thieu += 1
                print(f"FAIL  {ten}.sql — {mo}\n      {exc}")

        # RPC ghi_nho_luot: gọi với user không tồn tại → hàm thoát sớm, không ghi gì.
        print()
        try:
            r = c.post(
                f"{url}/rest/v1/rpc/ghi_nho_luot",
                json={
                    "p_user_id": "00000000-0000-0000-0000-000000000000",
                    "p_session_hash": "checkdb",
                    "p_turn_id": 0,
                    "p_nodes": [],
                },
            )
            if r.status_code in (200, 204):
                print("PASS  rpc ghi_nho_luot() — gọi được bằng service_role")
            else:
                thieu += 1
                print(f"FAIL  rpc ghi_nho_luot(): {r.status_code} {r.text[:160]}")
        except Exception as exc:
            thieu += 1
            print(f"FAIL  rpc ghi_nho_luot(): {exc}")

        # quen_toi_di: chỉ kiểm TỒN TẠI. Hàm trả void nên PostgREST đáp 204.
        #
        # Lưu ý: service_role VẪN gọi được hàm này dù đã `grant to authenticated`
        # — trong Supabase service_role có quyền rất rộng, revoke/grant không
        # chặn được nó. Điều đó KHÔNG sao: phạm vi xoá do `auth.uid()` BÊN TRONG
        # hàm quyết định, mà service_role thì auth.uid() là NULL nên
        # `where user_id = null` không khớp dòng nào. Bảo vệ nằm ở auth.uid(),
        # không nằm ở GRANT.
        try:
            r = c.post(f"{url}/rest/v1/rpc/quen_toi_di", json={})
            if r.status_code in (200, 204):
                print("PASS  rpc quen_toi_di() — tồn tại, gọi được")
            else:
                thieu += 1
                print(f"FAIL  rpc quen_toi_di(): {r.status_code} {r.text[:160]}")
        except Exception as exc:
            thieu += 1
            print(f"FAIL  rpc quen_toi_di(): {exc}")

        for ten, fn, args in RPC_CAN_CO:
            r = c.post(f"{url}/rest/v1/rpc/{fn}", json=args)
            missing = r.status_code == 404 and "PGRST202" in r.text
            if missing:
                thieu += 1
                print(f"FAIL  {ten}.sql — rpc {fn}() chưa tồn tại")
            else:
                print(f"PASS  {ten}.sql — rpc {fn}() tồn tại")

    print()
    if thieu:
        print(f"=> Còn {thieu} mục chưa đạt. Chạy lại file SQL tương ứng trong db/migrations/.")
        return 1
    print("=> Schema đầy đủ.")
    print("   Lưu ý: script này KHÔNG kiểm được RLS. Vào Dashboard → Authentication")
    print("   → Policies xác nhận 4 bảng bộ nhớ đều 'RLS enabled'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
