"""
TOPIC PROFILE — 4 chủ đề cửa vào. docx/13 §5.1–§5.2.

Đọc `data/topics.yaml`. Mỗi chủ đề map 1:1 với một folder tài liệu nghiên cứu.

Vì sao validate ở startup chứ không lúc dùng (docx/03 §7 luật 11):
    Chip TÌM HIỂU là một LỜI HỨA — người dùng bấm thì phải có nguyên văn để
    phát. Chip trỏ tới node không tồn tại thì mô hình sẽ lấp bằng nội dung tâm
    lý tự chế, mà chưa có chuyên gia duyệt thì đó là thứ nguy hiểm nhất sản
    phẩm này có thể làm. Sai thì KHÔNG cho app lên — cùng triết lý với
    GraphService._validate().

`source_docs` là ƯU TIÊN, KHÔNG phải bộ lọc (docx/03 §4.1b luật 1): người dùng
kể chuyện ngoài chủ đề thì overlay và gate vẫn làm việc bình thường. Chủ đề là
cửa vào, không phải nhà tù.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.config import settings

# `opening` đặc biệt: chủ đề 2 mở bằng bài Likert 10 câu chứ không bằng thẻ.
# Cả 10 câu đều mang source_doc của NHẬN DIỆN TRONG ĐỜI SỐNG HỌC SINH.docx nên
# bài test CHÍNH LÀ nội dung của chủ đề đó — xem docx/13 §3.
OPENING_ASSESSMENT = "assessment"


class TopicValidationError(RuntimeError):
    pass


class LearnChip(BaseModel):
    text: str
    serves: str                      # id content node phát ra khi bấm


class Topic(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    folder: str = ""
    source_docs: list[str] = Field(default_factory=list)
    opening: str | None = None
    learn_chips: list[LearnChip] = Field(default_factory=list)
    bridge_chip: str = ""
    enabled: bool = True

    @property
    def mo_bang_bai_test(self) -> bool:
        return self.opening == OPENING_ASSESSMENT

    def serves_for(self, text: str) -> str | None:
        """Node mà chip TÌM HIỂU này phát ra. So khớp NGUYÊN VĂN đã bóc tiền tố."""
        muc_tieu = (text or "").strip()
        for c in self.learn_chips:
            if c.text.strip() == muc_tieu:
                return c.serves
        return None


class TopicService:
    def __init__(self, path: Path, graph) -> None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        self.version: str = str(raw.get("version", "0"))
        self.topics: dict[str, Topic] = {}
        for row in raw.get("topics", []):
            t = Topic(**row)
            if t.id in self.topics:
                raise TopicValidationError(f"chủ đề trùng id: {t.id}")
            self.topics[t.id] = t
        self._validate(graph)

    # ---- lookups --------------------------------------------------------
    def get(self, topic_id: str | None) -> Topic | None:
        return self.topics.get(topic_id) if topic_id else None

    def enabled(self) -> list[Topic]:
        return [t for t in self.topics.values() if t.enabled]

    def serves_for(self, topic_id: str | None, text: str) -> str | None:
        """Tra node cho một chip TÌM HIỂU.

        Tra trong chủ đề đang mở trước; không thấy thì quét mọi chủ đề. Lý do
        quét rộng: chip của lượt trước vẫn nằm trên màn hình sau khi người dùng
        đổi chủ đề, bấm lại thì vẫn phải trả đúng thẻ chứ không được rơi vào
        nhánh "không hiểu".
        """
        t = self.get(topic_id)
        if t and (nid := t.serves_for(text)):
            return nid
        for other in self.topics.values():
            if other is t:
                continue
            if nid := other.serves_for(text):
                return nid
        return None

    def uu_tien(self, topic_id: str | None, node) -> int:
        """0 = node thuộc tài liệu của chủ đề, 1 = ngoài. Dùng làm KHOÁ PHỤ.

        Khoá phụ, không phải bộ lọc: node ngoài chủ đề vẫn được chọn khi nó là
        thứ duy nhất còn lại. Xem docx/03 §4.1b.
        """
        t = self.get(topic_id)
        if not t or not t.source_docs:
            return 0
        doc = getattr(node, "source_doc", None)
        if not doc:
            return 0                 # content node không có source_doc → không phạt
        return 0 if doc in t.source_docs else 1

    # ---- validation -----------------------------------------------------
    def _validate(self, graph) -> None:
        errors: list[str] = []
        for t in self.topics.values():
            if t.opening and not t.mo_bang_bai_test and graph.node(t.opening) is None:
                errors.append(f"chủ đề {t.id}: opening '{t.opening}' không phải node có thật")
            for c in t.learn_chips:
                if graph.node(c.serves) is None:
                    errors.append(
                        f"chủ đề {t.id}: chip «{c.text}» trỏ tới node không tồn tại "
                        f"'{c.serves}' — xem docx/03 §7 luật 11"
                    )
            # Chủ đề bật mà không có gì để nói = bấm vào là mô hình tự chế.
            if t.enabled and not t.opening:
                errors.append(f"chủ đề {t.id}: enabled nhưng không có `opening`")
        if errors:
            raise TopicValidationError(
                "topics.yaml không hợp lệ:\n  - " + "\n  - ".join(errors)
            )


_service: TopicService | None = None


def load_topics(graph) -> TopicService:
    global _service
    if _service is None:
        _service = TopicService(Path(settings.topics_path), graph)
    return _service


def get_topics() -> TopicService:
    """Khác `get_graph()` ở chỗ CÓ tự nạp khi chưa nạp — cố ý.

    `get_graph()` được phép nổ vì graph là thứ đầu tiên startup dựng; chưa có
    nó thì không có gì chạy được cả. Còn topics bị gọi từ sâu trong `decide_gate`
    (khoá phụ khi chọn target), nên bất kỳ ai gọi decide_gate ngoài đường
    startup — unit test, script, notebook — đều sẽ vấp. Phát hiện 09/09/2026:
    `pytest tests/test_gate.py` chạy riêng thì đỏ, chạy cả bộ lại xanh vì
    test_api.py chạy trước và khởi động app hộ. Xanh vì thứ tự file là loại
    xanh tệ nhất.

    Vẫn validate đầy đủ ở lần nạp đầu, nên không có đường nào bỏ qua luật
    "chip phải trỏ tới node có thật".
    """
    if _service is None:
        from app.graph.loader import get_graph

        return load_topics(get_graph())
    return _service
