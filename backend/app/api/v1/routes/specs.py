"""Minimal API specification discovery endpoint."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, status

from app.schemas.api_specification import DiscoveryCatalog, DiscoveryRequest
from app.services.discovery.engine import APIDiscoveryService


router = APIRouter(tags=["discovery"])

_SUFFIX_BY_FORMAT = {
    "openapi_json": ".json",
    "openapi_yaml": ".yaml",
    "graphql_sdl": ".graphql",
    "graphql_introspection": ".json",
}
_MAX_SPECIFICATION_BYTES = 2_000_000


@router.post("/discovery", response_model=DiscoveryCatalog)
def discover_specification(request: DiscoveryRequest) -> DiscoveryCatalog:
    """Parse and enrich one submitted specification through the existing discovery service."""
    content, filename = _resolve_source(request)
    suffix = _resolve_suffix(filename, request.format_hint)

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=suffix,
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)

        return APIDiscoveryService().discover([temporary_path])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _resolve_source(request: DiscoveryRequest) -> tuple[str, str]:
    has_content = bool(request.content and request.content.strip())
    has_url = bool(request.source_url and request.source_url.strip())
    if has_content == has_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one API specification source: file/text content or a URL.",
        )

    if has_content:
        return request.content or "", request.filename or "specification"

    source_url = request.source_url or ""
    parsed_url = urlparse(source_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid HTTP or HTTPS URL for the API specification.",
        )

    try:
        with urlopen(
            Request(source_url, headers={"User-Agent": "AegisAPI-Discovery/1.0"}),
            timeout=10,
        ) as response:
            payload = response.read(_MAX_SPECIFICATION_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The specification URL is unavailable. Check the URL and try again.",
        ) from exc

    if len(payload) > _MAX_SPECIFICATION_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The specification exceeds the 2 MB discovery limit.",
        )

    try:
        content = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The specification must be UTF-8 encoded text.",
        ) from exc

    return content, Path(parsed_url.path).name or "specification"


def _resolve_suffix(filename: str, format_hint: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix or _SUFFIX_BY_FORMAT.get(format_hint or "", ".json")
