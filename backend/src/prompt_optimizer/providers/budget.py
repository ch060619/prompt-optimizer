from __future__ import annotations

from dataclasses import dataclass

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderBudgetExceededError,
)

# RC ID: RC-172. Estimate request budgets before a Provider call.


@dataclass(frozen=True)
class BudgetEstimate:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float


def estimate_request(request: ModelRequest, provider: object) -> BudgetEstimate:
    config = getattr(provider, "config", None)
    input_rate = float(getattr(config, "input_cost_per_1k_tokens", 0.0) or 0.0)
    output_rate = float(getattr(config, "output_cost_per_1k_tokens", 0.0) or 0.0)
    output_tokens = int(getattr(config, "output_token_reserve", 256) or 0)
    input_text = f"{request.system_prompt}\n{request.prompt}"
    input_tokens = max(1, (len(input_text) + 3) // 4)
    total_tokens = input_tokens + output_tokens
    cost = round(
        (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate),
        8,
    )
    return BudgetEstimate(input_tokens, output_tokens, total_tokens, cost)


def enforce_budget(
    estimate: BudgetEstimate,
    *,
    max_tokens: int | None,
    max_cost: float | None,
) -> None:
    if max_tokens is not None and estimate.total_tokens > max_tokens:
        raise ProviderBudgetExceededError(
            f"Estimated request uses {estimate.total_tokens} tokens, above the "
            f"{max_tokens} token limit.",
            estimated_tokens=estimate.total_tokens,
            estimated_cost=estimate.cost,
            limit="tokens",
        )
    if max_cost is not None and estimate.cost > max_cost:
        raise ProviderBudgetExceededError(
            f"Estimated request costs {estimate.cost:.8f}, above the {max_cost:.8f} cost limit.",
            estimated_tokens=estimate.total_tokens,
            estimated_cost=estimate.cost,
            limit="cost",
        )
