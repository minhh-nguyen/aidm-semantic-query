"""the ONLY path to the proxy: cache, retry, thread pool ≤20"""

from dataclasses import dataclass
from typing import Any

Message = dict[str, object]

@dataclass
class LLMResult:
    text: str
    cost: float
    latency_s: float
    cached: bool


# Default completion-token budgets. Reasoning models (gpt-5, o-series, ...) spend
# hidden reasoning tokens from the same max_completion_tokens budget as the visible
# answer, so they need a much larger default: with the standard 512-token budget a
# reasoning model can exhaust the entire budget before emitting any visible text,
# returning an empty completion that operators silently coerce to their default
# output (see issue #255).
DEFAULT_MAX_TOKENS = 512
DEFAULT_REASONING_MAX_TOKENS = 8192

class LLMClient:
    def __init__(
        self,
        model: str = "gpt-6.1-luna",
        temperature: float = 0.0,
        max_ctx_len: int = 6400,
        max_tokens: int | None = None,
        cache_enable: bool = False,
        **kwargs: Any,
    ):
        self.model = model
        self.temperature = temperature
        self.max_ctx_len = max_ctx_len
        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        self.cache_enable = cache_enable
        self.max_tokens = max_tokens


    def send_request(self):
        print("LLClient starts sending a promp !")
