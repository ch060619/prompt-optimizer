from __future__ import annotations

import json
from pathlib import Path

from prompt_optimizer.api.app import app


output = Path(__file__).parents[1] / "frontend" / ".openapi.json"
output.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
