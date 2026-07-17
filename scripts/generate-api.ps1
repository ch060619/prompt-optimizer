$ErrorActionPreference = "Stop"

# RC ID: RC-062. Keep the documented Windows generation command deterministic.
python scripts/generate_api.py @args
