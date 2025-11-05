from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class DownloadError(Exception):
    """Raised when an artifact download fails."""


class NotFoundError(DownloadError):
    """Raised when the remote server responds with HTTP 404."""


async def _stream_to_file(response: httpx.Response, destination: Path, chunk_size: int = 65536) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        async for chunk in response.aiter_bytes(chunk_size):
            handle.write(chunk)


def _validate_checksum(path: Path, checksum: Optional[str]) -> None:
    if not checksum:
        return

    algo, _, expected = checksum.partition(":")
    algo = algo or "sha256"
    expected = expected or checksum

    try:
        digest = hashlib.new(algo)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise DownloadError(f"Unsupported checksum algorithm: {algo}") from exc

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)

    if digest.hexdigest() != expected:
        raise DownloadError("Checksum validation failed")


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TransportError, DownloadError)),
)
async def download_file(
    url: str,
    destination: Path,
    *,
    checksum: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, str]] = None,
    timeout: float = 60.0,
) -> Path:
    """Download an artifact with retries and optional checksum validation."""

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        response = await client.get(url, headers=headers, params=params)

        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundError(f"Artifact not found at {url}")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise DownloadError(f"Download failed: {exc}") from exc

        await _stream_to_file(response, destination)

    _validate_checksum(destination, checksum)

    return destination
