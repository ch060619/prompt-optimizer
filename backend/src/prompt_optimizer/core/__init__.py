__all__ = ["Analyzer", "Optimizer"]


def __getattr__(name: str):
    if name == "Analyzer":
        from prompt_optimizer.core.analyzer import Analyzer

        return Analyzer
    if name == "Optimizer":
        from prompt_optimizer.core.optimizer import Optimizer

        return Optimizer
    raise AttributeError(name)
