from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


StatusValue = Literal["ok", "no_update", "error"]
LogType = Literal["api", "core", "hcc"]


class UpdateRequest(BaseModel):
    token: Optional[str] = Field(default=None, description="Client token override")
    client_id: Optional[str] = Field(default=None, description="Optional client identifier")
    force: bool = Field(default=False, description="Force update even if versions match")


class UpdateResponse(BaseModel):
    status: StatusValue
    message: str
    version: Optional[str]
    log_path: str
    started_at: datetime
    finished_at: datetime
    exit_code: Optional[int] = None


class StatusEntry(BaseModel):
    component: LogType
    status: StatusValue
    message: str
    version: Optional[str]
    log_path: Optional[str]
    exit_code: Optional[int]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class StatusResponse(BaseModel):
    api: Optional[StatusEntry]
    core: Optional[StatusEntry]
    hcc: Optional[StatusEntry]


class LogListResponse(BaseModel):
    type: LogType
    files: list[str]
