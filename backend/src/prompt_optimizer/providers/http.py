from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-049. Keep the legacy import path as a compatibility alias.

HttpChatProvider = OpenAICompatibleAdapter

__all__ = ["HttpChatProvider"]
