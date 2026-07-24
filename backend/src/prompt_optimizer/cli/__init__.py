__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from prompt_optimizer.cli.app import app

        return app
    raise AttributeError(name)
