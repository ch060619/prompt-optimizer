from __future__ import annotations

from prompt_optimizer.core.analyzer import MAX_PROMPT_LENGTH
from prompt_optimizer.core.language import LanguagePreservationError, LanguageProfile
from prompt_optimizer.core.structure import StructuredInputError, StructuredPrompt

# RC ID: RC-156. Validate and minimally repair model output before it can be saved.


class OutputValidationError(ValueError):
    """Raised when an optimization result cannot be safely presented or saved."""


class OutputValidator:
    def validate(
        self,
        output: str,
        *,
        structure: StructuredPrompt,
        language_profile: LanguageProfile,
        preserve_language: bool,
    ) -> str:
        repaired = self.repair_once(output)
        if not repaired.strip():
            raise OutputValidationError("优化结果为空，结果未采用，请重试。")
        if len(repaired) > MAX_PROMPT_LENGTH:
            raise OutputValidationError(
                f"优化结果长度不能超过 {MAX_PROMPT_LENGTH} 个字符，结果未采用，请重试。"
            )
        try:
            validated = structure.validate(repaired)
            if preserve_language:
                language_profile.validate(StructuredPrompt.parse(validated).language_text())
            return validated
        except (LanguagePreservationError, StructuredInputError) as exc:
            raise OutputValidationError(str(exc)) from exc

    @staticmethod
    def repair_once(output: str) -> str:
        """Remove unsafe control characters without altering visible content."""
        if not isinstance(output, str):
            raise OutputValidationError("优化结果不是文本，结果未采用，请重试。")
        return "".join(
            character
            for character in output
            if character >= " " or character in {"\n", "\r", "\t"}
        )
