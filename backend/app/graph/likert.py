"""
Tra phát biểu Likert theo node — để prompt biết người dùng đã TRẢ LỜI GÌ.

Vì sao cần (bug 09/09/2026): `00_CORE_PERSONA.md` chỉ nhận
`{HAS_TAKEN_ASSESSMENT}` = "có" / "chưa" — một cờ boolean. Mô hình biết CÓ một
bài test, nhưng không biết bài đó ra cái gì, nên lượt đầu sau bài test nó hỏi
ngược lại người dùng "bạn đã đánh giá những gì vậy?". Người vừa trả lời xong 10
câu bị bắt kể lại chính 10 câu đó.

Overlay có sẵn 10 node LIKERT nhưng `verbatim` rỗng (họ tick ô, không gõ chữ).
Cái thiếu là NHỊP CẦU node_id -> phát biểu gốc. File này bắc đúng cây cầu đó.

Phát biểu trả về là NGUYÊN VĂN `data/assessment.yaml`, tức nguyên văn
NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx — nội dung đã duyệt, không phải mô hình
tự nghĩ ra.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import settings


@lru_cache(maxsize=1)
def likert_text_by_node() -> dict[str, str]:
    """{node_id: "Tôi thường tự trách bản thân khi mắc lỗi."}"""
    raw = yaml.safe_load(Path(settings.assessment_path).read_text(encoding="utf-8"))
    return {
        item["node_id"]: item["text"]
        for item in raw.get("items", [])
        if item.get("node_id") and item.get("text")
    }
