"""Read-only example plugin artifact."""


def handle(payload: dict[str, object]) -> dict[str, object]:
    return {"keys": sorted(str(key) for key in payload)}
