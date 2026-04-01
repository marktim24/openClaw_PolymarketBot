import json
from pathlib import Path
from typing import Dict, Any

from config import STATE_FILE

DEFAULT_STATE = {
    'processed_event_keys': [],
    'wallet_last_seen': {},
    'balance': None,
    'started_with': None,
    'poll_iteration': 0,
}

class LiveStateStore:
    def __init__(self, path: str = STATE_FILE):
        self.path = Path(path)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_STATE)
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            return dict(DEFAULT_STATE)

    def save(self, state: Dict[str, Any]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, indent=2), encoding='utf-8')
