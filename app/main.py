from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from app.models import LogListResponse, LogType, StatusResponse, UpdateRequest, UpdateResponse
from app.services import api_update, core_update, hcc_update
from app.utils import filesystem

app = FastAPI(title="HomeCore Tools", version="0.1.0")


async def validate_auth(authorization: Annotated[str | None, Header(default=None)]) -> None:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Header Authorization ausente")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Formato de Authorization inválido")

    expected = filesystem.load_options().get("auth_token")
    if not expected:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token de autenticação não configurado")

    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


@app.on_event("startup")
async def on_startup() -> None:
    filesystem.ensure_runtime_directories()
    filesystem.prune_logs(int(filesystem.load_options().get("log_retention_days", 7)))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/update/api", response_model=UpdateResponse)
async def update_api(payload: UpdateRequest, _: None = Depends(validate_auth)) -> UpdateResponse:
    return await api_update.run(payload)


@app.post("/update/core", response_model=UpdateResponse)
async def update_core(payload: UpdateRequest, _: None = Depends(validate_auth)) -> UpdateResponse:
    return await core_update.run(payload)


@app.post("/update/hcc", response_model=UpdateResponse)
async def update_hcc(payload: UpdateRequest, _: None = Depends(validate_auth)) -> UpdateResponse:
    return await hcc_update.run(payload)


@app.get("/logs", response_model=LogListResponse)
async def list_logs(
    type: Annotated[LogType, Query(description="Tipo de log (api|core|hcc)")],
    _: None = Depends(validate_auth),
) -> LogListResponse:
    logs: list[str] = []
    if filesystem.LOG_DIR.exists():
        for file in sorted(filesystem.LOG_DIR.iterdir(), reverse=True):
            if file.is_file() and file.name.endswith(".log") and f"_{type}_" in file.name:
                logs.append(str(file))
    return LogListResponse(type=type, files=logs)


@app.get("/status", response_model=StatusResponse)
async def status_endpoint(_: None = Depends(validate_auth)) -> StatusResponse:
    return filesystem.load_status()
