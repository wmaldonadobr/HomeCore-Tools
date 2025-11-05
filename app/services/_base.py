from __future__ import annotations

import shutil
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from app.models import LogType, StatusEntry, UpdateRequest, UpdateResponse
from app.utils import filesystem
from app.utils.download import DownloadError, NotFoundError, download_file

ApplyFn = Callable[[Path, Dict[str, Any], Callable[[str], None]], Awaitable[None]]

REMOTE_VERSION_KEYS = (
    "version",
    "client_version",
    "api_version",
    "core_version",
    "hcc_version",
)


async def perform_update(
    *,
    component: LogType,
    request: UpdateRequest,
    base_url: str | None,
    apply_artifact: ApplyFn,
    build_request_payload: Optional[Callable[[UpdateRequest, str], Dict[str, Any]]] = None,
) -> UpdateResponse:
    filesystem.ensure_runtime_directories()
    options = filesystem.load_options()
    filesystem.prune_logs(int(options.get("log_retention_days", 7)))

    started_at = datetime.now(timezone.utc)
    log_path = filesystem.build_log_path(component, started_at)

    def log(message: str) -> None:
        filesystem.append_log(log_path, f"[{datetime.now(timezone.utc).isoformat()}] {message}")

    log(f"Starting {component} update")

    if not base_url:
        message = "Base URL não configurada"
        log(message)
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=None,
            exit_code=1,
        )

    token = filesystem.get_client_token(request.token)
    if not token:
        message = "Token não informado (payload ou arquivo)"
        log(message)
        response = _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=None,
            exit_code=1,
        )
        return response

    manifest = filesystem.load_manifest(component)
    local_version = manifest.get("version")

    try:
        remote_manifest = await _fetch_remote_manifest(
            base_url=base_url,
            token=token,
            request=request,
            build_request_payload=build_request_payload,
        )
    except NotFoundError:
        message = "Endpoint remoto retornou 404 (sem update)"
        log(message)
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="no_update",
            message=message,
            version=local_version,
            exit_code=0,
        )
    except Exception as exc:  # pragma: no cover - network failures
        message = f"Falha consultando manifest remoto: {exc}"
        log(message)
        log(traceback.format_exc())
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=local_version,
            exit_code=1,
        )

    remote_version = _extract_remote_version(remote_manifest)
    if not remote_version:
        message = "Manifest remoto não possui informação de versão"
        log(message)
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=local_version,
            exit_code=1,
        )

    if not request.force and local_version == remote_version:
        message = f"Versão {remote_version} já aplicada"
        log(message)
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="no_update",
            message=message,
            version=remote_version,
            exit_code=0,
        )

    download_url = _extract_download_url(remote_manifest)
    if not download_url:
        message = "Manifest remoto não possui URL de download"
        log(message)
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=local_version,
            exit_code=1,
        )

    checksum = remote_manifest.get("checksum")
    filename = remote_manifest.get("filename") or Path(download_url).name or f"{component}_{remote_version}.pkg"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / filename
            log(f"Baixando artefato de {download_url}")
            try:
                await download_file(
                    download_url,
                    artifact_path,
                    checksum=checksum,
                )
            except NotFoundError:
                message = "Artefato remoto não encontrado (sem update)"
                log(message)
                return _finalize(
                    component=component,
                    log_path=log_path,
                    started_at=started_at,
                    status="no_update",
                    message=message,
                    version=local_version,
                    exit_code=0,
                )
            except DownloadError as exc:
                message = f"Falha durante download: {exc}"
                log(message)
                log(traceback.format_exc())
                return _finalize(
                    component=component,
                    log_path=log_path,
                    started_at=started_at,
                    status="error",
                    message=message,
                    version=local_version,
                    exit_code=1,
                )

            backup_path = filesystem.build_backup_path(component, started_at, filename)
            log(f"Criando backup em {backup_path}")
            shutil.copy2(artifact_path, backup_path)

            await apply_artifact(artifact_path, remote_manifest, log)

    except Exception as exc:  # pragma: no cover - defensive logging
        message = f"Erro aplicando update: {exc}"
        log(message)
        log(traceback.format_exc())
        return _finalize(
            component=component,
            log_path=log_path,
            started_at=started_at,
            status="error",
            message=message,
            version=local_version,
            exit_code=1,
        )

    manifest.update(
        {
            "version": remote_version,
            "download_url": download_url,
            "updated_at": started_at.isoformat(),
            "checksum": checksum,
        }
    )
    filesystem.save_manifest(component, manifest)

    message = f"Update {component} aplicado (versão {remote_version})"
    log(message)
    return _finalize(
        component=component,
        log_path=log_path,
        started_at=started_at,
        status="ok",
        message=message,
        version=remote_version,
        exit_code=0,
    )


def _extract_remote_version(manifest: Dict[str, Any]) -> Optional[str]:
    for key in REMOTE_VERSION_KEYS:
        value = manifest.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _extract_download_url(manifest: Dict[str, Any]) -> Optional[str]:
    for key in ("download_url", "url", "artifact", "link"):
        value = manifest.get(key)
        if isinstance(value, str) and value:
            return value
    return None


async def _fetch_remote_manifest(
    *,
    base_url: str,
    token: str,
    request: UpdateRequest,
    build_request_payload: Optional[Callable[[UpdateRequest, str], Dict[str, Any]]],
) -> Dict[str, Any]:
    params = {"token": token}
    if request.client_id:
        params["client_id"] = request.client_id
    if build_request_payload:
        params.update(build_request_payload(request, token))

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(base_url, params=params)
        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundError("manifest not found")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Resposta inesperada do manifest")
        return payload


def _finalize(
    *,
    component: LogType,
    log_path: Path,
    started_at: datetime,
    status: str,
    message: str,
    version: Optional[str],
    exit_code: int,
) -> UpdateResponse:
    finished_at = datetime.now(timezone.utc)

    status_entry = StatusEntry(
        component=component,
        status=status,  # type: ignore[arg-type]
        message=message,
        version=version,
        log_path=str(log_path),
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
    )
    filesystem.record_status(component, status_entry)

    return UpdateResponse(
        status=status,  # type: ignore[arg-type]
        message=message,
        version=version,
        log_path=str(log_path),
        started_at=started_at,
        finished_at=finished_at,
        exit_code=exit_code,
    )
