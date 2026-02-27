from __future__ import annotations

import json
from pathlib import Path

from ir_pipeline.schemas import ConversationSession


class SessionStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        tools_dir = Path(__file__).resolve().parents[2]
        self.root_dir = root_dir or (tools_dir / "sessions")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, session_id: str) -> Path:
        safe_id = session_id.strip()
        return self.root_dir / f"{safe_id}.json"

    def exists(self, session_id: str) -> bool:
        return self.path_for(session_id).exists()

    def save(self, session: ConversationSession) -> None:
        target = self.path_for(session.session_id)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(session.model_dump_json(indent=2) + "\n", encoding="utf-8")
        tmp.replace(target)

    def load(self, session_id: str) -> ConversationSession:
        target = self.path_for(session_id)
        if not target.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        data = json.loads(target.read_text(encoding="utf-8"))
        return ConversationSession.model_validate(data)
