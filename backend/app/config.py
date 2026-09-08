"""Cấu hình tập trung. Xem docx/06 §8."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- LLM ---
    llm_provider: str = "gemini"                  # "gemini" | "anthropic"
    llm_offline: bool = False                     # true → không gọi API, trả câu tĩnh

    # Gemini (Google AI Studio)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Anthropic (giữ lại để đổi lại nếu cần)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    @property
    def active_model(self) -> str:
        return self.gemini_model if self.llm_provider == "gemini" else self.anthropic_model

    @property
    def has_api_key(self) -> bool:
        return bool(self.gemini_api_key if self.llm_provider == "gemini" else self.anthropic_api_key)

    # --- Hạ tầng ---
    redis_url: str = "redis://localhost:6379/0"
    overlay_ttl_seconds: int = 86_400
    # "redis" (mặc định, cần REDIS_URL trỏ dịch vụ thật) | "supabase" (dùng
    # luôn SUPABASE_* đã có, không cần đăng ký thêm dịch vụ ngoài — khuyến
    # nghị khi deploy Render free tier, nơi không có Redis cục bộ) | "memory"
    # (chỉ để test — mất khi tiến trình tắt).
    overlay_backend: str = "redis"
    log_path: Path = BACKEND_ROOT / "data" / "turns.jsonl"
    # NoDecode: tắt JSON-decode ở tầng source để field_validator xử lý chuỗi CSV
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # --- Dữ liệu ---
    graph_path: Path = BACKEND_ROOT / "data" / "domain_graph.yaml"
    content_dir: Path = BACKEND_ROOT / "data" / "content"
    crisis_card_path: Path = BACKEND_ROOT / "data" / "crisis_card.md"
    assessment_path: Path = BACKEND_ROOT / "data" / "assessment.yaml"
    skills_dir: Path = BACKEND_ROOT / "app" / "skills"

    # --- Ngưỡng (docx/03 §3, docx/11 phần D) ---
    confidence_threshold: float = 0.70
    extract_confidence_cap: float = 0.60          # INFERRED
    self_report_confidence_cap: float = 0.75      # SELF_REPORT (D2)
    min_nodes_for_reflect: int = 3                # D3 — REFLECT chế độ đơn
    # docx/11 §E5 — "Đúng một phần". Trên confidence_threshold (0.70) nên node
    # vẫn đủ mạnh để bot bám vào, nhưng dưới CONFIRMED (0.95) nên KHÔNG mở được
    # gate SUPPORT: đưa kỹ năng dựa trên một mẫu hình mới đúng một nửa là đúng
    # kiểu sai mà cả tài liệu đang tránh. Vượt trần SELF_REPORT (0.75) là CỐ Ý —
    # trần đó chặn bước TRÍCH, còn đây là hành động của chính người dùng.
    partial_confirm_confidence: float = 0.80
    # Số lượt REFLECT bị khoá sau khi người dùng bấm "Đúng một phần". Không có
    # nó thì cycle vẫn sáng ở 0.80 và lượt sau bot dựng lại y hệt cái thẻ họ
    # vừa nói là chưa đúng hẳn.
    reflect_cooldown_turns: int = 2
    cycle_activation_confidence: float = 0.60     # docx/03 §6
    max_response_sentences: int = 5
    crisis_tier3_max_chars: int = 600

    # --- Bộ nhớ dài hạn (docx/12) ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_audience: str = "authenticated"
    memory_enabled: bool = False                  # tắt => app chạy y như cũ
    # Trần confidence khi nạp từ bộ nhớ. Thấp hơn cả INFERRED (0.60) và dưới
    # confidence_threshold (0.70) => node nhớ lại KHÔNG BAO GIỜ tự đủ mạnh để
    # kích REFLECT; luôn phải có bằng chứng mới trong phiên này.
    memory_seed_confidence_cap: float = 0.50
    memory_half_life_days: float = 30.0           # phân rã theo thời gian
    memory_max_seed_nodes: int = 8
    # Loại node được phép NHẮC LẠI NGUYÊN VĂN từ phiên trước (docx/12 §5.1).
    # Mặc định chỉ trigger + impact = SỰ VIỆC ("thi được 6.5", "khó ngủ").
    # KHÔNG gồm manifestation/affect = LỜI TỰ PHÁN XÉT ("mình kém cỏi") —
    # nhắc lại mấy câu đó là đóng đinh người ta vào phiên bản cũ của chính họ.
    memory_recall_node_types: Annotated[list[str], NoDecode] = ["trigger", "impact"]

    # --- Lưu hội thoại nguyên văn (GĐ6, 07/09/2026) ---
    # ĐỔI LUẬT: trước đây dự án cố ý KHÔNG lưu transcript (docx/03 §8). Chủ đề
    # tài quyết định lưu để có dữ liệu cho phần nghiên cứu sau. Dùng chung
    # SUPABASE_* với bộ nhớ dài hạn, nhưng là công tắc RIÊNG: tắt bộ nhớ mà vẫn
    # lưu transcript (hoặc ngược lại) là hai chuyện khác nhau.
    transcript_enabled: bool = True

    # Đẩy turn_logs (số liệu nghiên cứu, KHÔNG PII) lên Supabase. Công tắc
    # RIÊNG với transcript_enabled: turn_logs không truy ngược được về cá nhân
    # nên có thể bật kể cả khi không lưu nguyên văn. Ghi file jsonl luôn chạy.
    turnlog_supabase_enabled: bool = True

    @property
    def turnlog_ready(self) -> bool:
        return bool(
            self.turnlog_supabase_enabled
            and self.supabase_url
            and self.supabase_service_role_key
        )

    @property
    def transcript_ready(self) -> bool:
        return bool(
            self.transcript_enabled and self.supabase_url and self.supabase_service_role_key
        )

    @property
    def memory_ready(self) -> bool:
        return bool(
            self.memory_enabled and self.supabase_url and self.supabase_service_role_key
        )

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()] or ["http://localhost:3000"]
        return v

    @field_validator("memory_recall_node_types", mode="before")
    @classmethod
    def _split_recall_types(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = Settings()
