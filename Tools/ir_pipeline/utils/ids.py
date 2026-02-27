from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def create_session_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8]
    return f"sess_{ts}_{suffix}"
