"""
Kiểm tra nhanh data/turns.jsonl. docx/08 §5.

Chạy:  python scripts/analyze_log.py [đường_dẫn.jsonl]

Không phụ thuộc pandas — dùng stdlib để chạy được ở máy demo.
Giai đoạn 2: nạp bằng `pd.read_json(path, lines=True)` rồi phân tích sâu.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "data" / "turns.jsonl"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"Chưa có log: {path}")
        return

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        print("Log rỗng.")
        return

    n = len(rows)
    print(f"== {path.name} — {n} lượt ==\n")

    gates = Counter(r.get("gate") for r in rows)
    print("Phân bố gate:")
    for g, c in gates.most_common():
        print(f"  {g:10} {c:4}  {c / n:6.1%}")

    tiers = Counter(r.get("safety_tier") for r in rows if r.get("safety_tier"))
    print(f"\nAn toàn kích hoạt: {sum(tiers.values())} lượt  {dict(tiers)}")
    matched = Counter(m for r in rows for m in (r.get("safety_matched") or []))
    if matched:
        print("  Cụm tầng-3 hay khớp:", matched.most_common(5))

    pc = Counter(f for r in rows for f in (r.get("postcheck_flags") or []))
    print(f"\nPost-check chặn: {sum(pc.values())}  {dict(pc)}")

    hall = [r["turn_id"] for r in rows if r.get("extract_hallucinated")]
    print(f"Trích bịa node: {len(hall)} lượt {hall[:10]}")
    print(f"Trích parse lỗi: {sum(1 for r in rows if r.get('extract_failed'))}")

    totals = [r["latency_ms"]["total"] for r in rows if r.get("latency_ms", {}).get("total")]
    if totals:
        print(
            f"\nLatency total ms — trung vị {statistics.median(totals):.0f} · "
            f"p95 {sorted(totals)[int(len(totals) * 0.95) - 1]:.0f} · max {max(totals)}"
        )

    # số lượt tới CONFIRMED đầu tiên (chỉ số quan trọng — docx/08 §3)
    first_confirmed = None
    for r in rows:
        if r.get("overlay_by_source", {}).get("CONFIRMED", 0) > 0:
            first_confirmed = r["turn_id"]
            break
    print(f"\nLượt đạt CONFIRMED đầu tiên: {first_confirmed}")

    cyc = sum(1 for r in rows if r.get("active_cycles"))
    print(f"Lượt có cycle hoạt hoá: {cyc}  {cyc / n:.1%}")

    escapes = [p for r in rows for p in (r.get("chip_provenance") or []) if p.get("is_escape")]
    print(f"Chip thoát được sinh: {len(escapes)}")


if __name__ == "__main__":
    main()
