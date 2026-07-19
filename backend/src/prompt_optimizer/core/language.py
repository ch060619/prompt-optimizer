from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

LanguageKind = Literal["zh", "en", "mixed", "other"]

_CHINESE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_LATIN = re.compile(r"[A-Za-z]")
_TRANSLATION_REQUEST = re.compile(
    r"(?:翻译(?:成|为)?|译成|翻成|(?:please\s+)?translate\b|translation\s+(?:to|into))",
    re.IGNORECASE,
)
_TRANSLATION_NEGATION = re.compile(
    r"(?:不要|无需|不需要|勿)\s*(?:翻译|译)|(?:do\s+not|don't|never|without)\s+translate",
    re.IGNORECASE,
)


class LanguagePreservationError(ValueError):
    """Raised when an optimization result changes the user's language."""


@dataclass(frozen=True)
class LanguageProfile:
    primary: LanguageKind
    chinese_letters: int
    latin_letters: int
    chinese_share: float
    latin_share: float
    translation_requested: bool

    @classmethod
    def detect(cls, text: str) -> LanguageProfile:
        chinese_letters = len(_CHINESE.findall(text))
        latin_letters = len(_LATIN.findall(text))
        total_letters = chinese_letters + latin_letters
        chinese_share = chinese_letters / total_letters if total_letters else 0.0
        latin_share = latin_letters / total_letters if total_letters else 0.0
        if not total_letters:
            primary: LanguageKind = "other"
        elif chinese_letters and latin_letters:
            primary = "zh" if chinese_share >= 0.75 else "en" if latin_share >= 0.75 else "mixed"
        elif chinese_letters:
            primary = "zh"
        else:
            primary = "en"
        translation_requested = bool(_TRANSLATION_REQUEST.search(text)) and not bool(
            _TRANSLATION_NEGATION.search(text)
        )
        return cls(
            primary=primary,
            chinese_letters=chinese_letters,
            latin_letters=latin_letters,
            chinese_share=chinese_share,
            latin_share=latin_share,
            translation_requested=translation_requested,
        )

    @property
    def instruction(self) -> str:
        if self.translation_requested:
            return "用户明确要求翻译，按用户指定的目标语言执行，不强制保持原语言。"
        if self.primary == "zh":
            return "请保持用户的中文表达，不要把整段内容改写成其他语言。"
        if self.primary == "en":
            return (
                "Preserve the user's English. "
                "Do not rewrite the whole result into another language."
            )
        if self.primary == "mixed":
            return (
                f"请保持用户的中英文混合表达；当前中文约 {self.chinese_share:.0%}、"
                f"English 约 {self.latin_share:.0%}，不要整体改成单一语言。"
            )
        return "请保持用户原有语言，不要在未被要求时整体翻译。"

    def validate(self, text: str) -> None:
        if self.translation_requested or self.primary == "other":
            return
        observed = self.detect(text)
        if self.primary == "zh":
            valid = observed.chinese_letters > 0 and observed.chinese_share >= 0.55
        elif self.primary == "en":
            valid = observed.latin_letters > 0 and observed.latin_share >= 0.55
        else:
            valid = (
                observed.chinese_letters > 0
                and observed.latin_letters > 0
                and abs(observed.chinese_share - self.chinese_share) <= 0.65
            )
        if not valid:
            raise LanguagePreservationError("优化结果整体改变了用户语言，结果未采用，请重试。")
