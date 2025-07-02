import json
import os
from pathlib import Path
from typing import Dict


REGISTRY_FILE = Path(os.getenv("MCP_REGISTRY_FILE", os.path.expanduser("~/.bytecrafter_mcp_servers.json")))


def _load() -> Dict[str, dict]:
    if REGISTRY_FILE.exists():
        try:
            with REGISTRY_FILE.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}
    return {}


def _save(data: Dict[str, dict]):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_server(name: str, command: str) -> None:
    data = _load()
    data[name] = {"command": command}
    _save(data)


def remove_server(name: str) -> bool:
    data = _load()
    if name in data:
        data.pop(name)
        _save(data)
        return True
    return False


def list_servers() -> Dict[str, dict]:
    return _load()


def get_server_command(name: str) -> str | None:
    return _load().get(name, {}).get("command") 