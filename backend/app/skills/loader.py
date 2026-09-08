"""
SkillLoader — load file .md một lần lúc startup, điền placeholder khi dùng.
Tham chiếu SystemPromptBuilder.java. docx/05 §10.

Luật: placeholder không được điền → BÁO LỖI ngay lúc build, không để chuỗi
`{XXX}` lọt vào prompt.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.config import settings

_PLACEHOLDER = re.compile(r"\{([A-Z_][A-Z0-9_]*)\}")

# placeholder trong 00_CORE_PERSONA được điền ở vòng build của skill gọi nó
_CORE_PLACEHOLDERS = {"TURN_COUNT", "HAS_TAKEN_ASSESSMENT", "MEMORY_QUOTES"}


class SkillError(RuntimeError):
    pass


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self._templates: dict[str, str] = {}
        for p in sorted(skills_dir.glob("*.md")):
            self._templates[p.stem] = p.read_text(encoding="utf-8")
        if "00_CORE_PERSONA" not in self._templates:
            raise SkillError("Thiếu 00_CORE_PERSONA.md")
        self._core = self._templates["00_CORE_PERSONA"]
        # Hợp đồng JSON dùng chung cho MỌI gate — kiến trúc 1-lời-gọi ở GĐ2.
        # Nằm riêng một file để luật định dạng chỉ có ĐÚNG MỘT bản: sáu skill
        # mỗi cái chép một phiên bản hơi khác nhau là cách chắc chắn nhất để
        # chúng lệch nhau sau vài lần sửa.
        self._contract = self._templates.get("10_OUTPUT_CONTRACT", "")
        required = {
            "00_CORE_PERSONA", "10_OUTPUT_CONTRACT", "11_CLARIFY",
            "12_REFLECT", "13_ORIENT", "14_SUPPORT", "15_BRIDGE", "99_REFUSAL",
        }
        missing = required - set(self._templates)
        if missing:
            raise SkillError(f"Thiếu skill file: {sorted(missing)}")

    def names(self) -> list[str]:
        return sorted(self._templates)

    def build(self, skill_name: str, **placeholders: object) -> str:
        if skill_name not in self._templates:
            raise SkillError(f"Không có skill '{skill_name}'")
        tpl = self._templates[skill_name]
        # Thứ tự có ý nghĩa: nhét khối trước, điền placeholder sau — placeholder
        # nằm BÊN TRONG khối được nhét (vd {NODE_CATALOG} trong OUTPUT_CONTRACT)
        # phải còn cơ hội được điền ở vòng dưới.
        tpl = tpl.replace("{CORE_PERSONA}", self._core)
        tpl = tpl.replace("{OUTPUT_CONTRACT}", self._contract)
        for key, value in placeholders.items():
            tpl = tpl.replace("{" + key + "}", str(value))
        leftover = {
            m.group(1)
            for m in _PLACEHOLDER.finditer(tpl)
        }
        # CORE placeholder được phép còn lại NẾU chưa truyền (skill 01 tự chứa CORE)
        leftover -= {k for k in _CORE_PLACEHOLDERS if k not in placeholders}
        if leftover:
            raise SkillError(
                f"skill '{skill_name}' còn placeholder chưa điền: {sorted(leftover)}"
            )
        return tpl


_loader: SkillLoader | None = None


def load_skills() -> SkillLoader:
    global _loader
    if _loader is None:
        _loader = SkillLoader(settings.skills_dir)
    return _loader


def get_skills() -> SkillLoader:
    if _loader is None:
        raise RuntimeError("Skills chưa load — gọi load_skills() lúc startup")
    return _loader
