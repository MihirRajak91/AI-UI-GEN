from __future__ import annotations

import json
from pathlib import Path


class TraceStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        tools_dir = Path(__file__).resolve().parents[2]
        self.root_dir = root_dir or (tools_dir / "sessions")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, session_id: str) -> Path:
        safe_id = session_id.strip()
        return self.root_dir / f"{safe_id}.trace.jsonl"

    def append_many(self, session_id: str, events: list[dict[str, str]]) -> None:
        if not events:
            return
        target = self.path_for(session_id)
        with target.open("a", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=True) + "\n")
