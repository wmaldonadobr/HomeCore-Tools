from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.models import UpdateRequest, UpdateResponse
from app.services._base import perform_update
from app.utils import filesystem

TARGET_DIR = Path("/config/homecore/core")


async def run(payload: UpdateRequest) -> UpdateResponse:
    options = filesystem.load_options()
    base_url = options.get("core_base_url")

    return await perform_update(
        component="core",
        request=payload,
        base_url=base_url,
        apply_artifact=_apply_artifact,
    )


async def _apply_artifact(artifact_path: Path, manifest: dict, log) -> None:
    await asyncio.to_thread(_apply_sync, artifact_path, log)


def _apply_sync(artifact_path: Path, log) -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if artifact_path.suffix.lower() == ".zip":
        shutil.unpack_archive(artifact_path, TARGET_DIR, "zip")
        log(f"Arquivo ZIP extraído para {TARGET_DIR}")
    else:
        destination = TARGET_DIR / artifact_path.name
        shutil.copy2(artifact_path, destination)
        log(f"Artefato copiado para {destination}")
