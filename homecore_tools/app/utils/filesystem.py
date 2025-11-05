from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.models import LogType, StatusEntry, StatusResponse

DATA_ROOT = Path(os.environ.get("DATA_DIR", "/data"))
LOG_DIR = DATA_ROOT / "logs"
BACKUP_DIR = DATA_ROOT / "backups"
STATE_DIR = DATA_ROOT / "state"
STATUS_FILE = DATA_ROOT / "status.json"
OPTIONS_FILE = DATA_ROOT / "options.json"
DEFAULT_CLIENT_TOKEN_PATH = Path("/config/homecore/client_token")

DEFAULT_OPTIONS = {
    "api_base_url": "https://homecore.com.br/api/sync/beacon.php",
    "core_base_url": "https://homecore.com.br/api/update/core",
    "hcc_base_url": "https://homecore.com.br/api/hcc",
    "auth_token": "change-me",
    "log_retention_days": 7,
}

_COMPONENTS: tuple[LogType, ...] = ("api", "core", "hcc")


def ensure_runtime_directories() -> None:
    for path in [LOG_DIR, BACKUP_DIR, STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    for component in _COMPONENTS:
        (BACKUP_DIR / component).mkdir(parents=True, exist_ok=True)


def prune_logs(retention_days: int) -> None:
    if retention_days <= 0:
        return

    threshold = datetime.now(timezone.utc) - timedelta(days=retention_days)
    for log_file in LOG_DIR.glob("*.log"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
        if mtime < threshold:
            log_file.unlink(missing_ok=True)


def build_log_path(component: LogType, started_at: datetime) -> Path:
    timestamp = started_at.strftime("%Y%m%dT%H%M%S")
    return LOG_DIR / f"{timestamp}_{component}_update.log"


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip("\n") + "\n")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=True, indent=2)


def load_options() -> Dict[str, Any]:
    options = DEFAULT_OPTIONS.copy()
    options_path = OPTIONS_FILE
    if options_path.exists():
        user_options = read_json(options_path)
        options.update({k: v for k, v in user_options.items() if v is not None})
    return options


def get_client_token(payload_token: Optional[str]) -> Optional[str]:
    if payload_token:
        return payload_token

    if DEFAULT_CLIENT_TOKEN_PATH.exists():
        return DEFAULT_CLIENT_TOKEN_PATH.read_text(encoding="utf-8").strip() or None

    return None


def load_manifest(component: LogType) -> Dict[str, Any]:
    manifest_path = STATE_DIR / f"{component}.json"
    return read_json(manifest_path)


def save_manifest(component: LogType, manifest: Dict[str, Any]) -> None:
    manifest_path = STATE_DIR / f"{component}.json"
    write_json(manifest_path, manifest)


def record_status(component: LogType, status: StatusEntry) -> None:
    data = read_json(STATUS_FILE)
    data[component] = status.model_dump(mode="json")
    write_json(STATUS_FILE, data)


def load_status() -> StatusResponse:
    data = read_json(STATUS_FILE)

    def to_entry(component: LogType) -> Optional[StatusEntry]:
        raw = data.get(component)
        if not raw:
            return None
        try:
            return StatusEntry.model_validate(raw)
        except Exception:
            return None

    return StatusResponse(
        api=to_entry("api"),
        core=to_entry("core"),
        hcc=to_entry("hcc"),
    )


def build_backup_path(component: LogType, started_at: datetime, filename: str) -> Path:
    timestamp = started_at.strftime("%Y%m%dT%H%M%S")
    sanitized = filename.replace("/", "_")
    return BACKUP_DIR / component / f"{timestamp}_{sanitized}"
