# File bị thay thế ở GĐ2 (07/09/2026)

KHÔNG xoá — dự án chưa có git nên đây là bản sao lưu duy nhất.
Kiến trúc mới: 1 lượt = 1 lời gọi LLM (app/llm/turn.py + app/evidence/matcher.py).

| File cũ | Thay bằng |
|---|---|
| llm/extract.py | evidence/matcher.py (cue, 0 token) + turn.parse_turn_output() |
| llm/speak.py | turn.build_turn_prompt() |
| llm/quickreply.py | turn.parse_turn_output() — luật lọc chip giữ nguyên ở _chip_an_toan() |
| skills/01_EXTRACT_EVIDENCE.md | skills/10_OUTPUT_CONTRACT.md (mục evidence) |
| skills/13_QUICKREPLY.md | skills/10_OUTPUT_CONTRACT.md (mục chips) |
| skills/00_CORE_PERSONA.md | bản gọn 2.141 byte (từ 3.919) |
| tests/test_extract.py | tests/test_matcher.py + tests/test_turn.py |
| tests/test_quickreply.py | tests/test_turn.py |
