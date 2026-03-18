from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import ValidationError

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional import during packaging edge cases
    load_dotenv = None  # type: ignore[assignment]


def _read_str(env: Mapping[str, str], key: str, default: str = "") -> str:
    return env.get(key, default).strip()


def _read_int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be an integer") from exc


def _read_float(env: Mapping[str, str], key: str, default: float) -> float:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} must be a float") from exc


@dataclass(frozen=True)
class DaumVideoMCPConfig:
    api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8200
    path: str = "/mcp"
    transport: str = "streamable-http"
    http_timeout_sec: float = 8.0
    cache_ttl_sec: int = 300
    api_base_url: str = "https://dapi.kakao.com/v2/search"

    @classmethod
    def from_env(
        cls,
        env: Optional[Mapping[str, str]] = None,
        *,
        dotenv_path: Optional[str] = None,
    ) -> "DaumVideoMCPConfig":
        # 로컬 개발과 서버 배포 모두 같은 진입점으로 맞추기 위해 .env를 우선 로드한다.
        if load_dotenv is not None:
            load_dotenv(dotenv_path=dotenv_path)

        source = env or os.environ
        return cls(
            api_key=_read_str(source, "KAKAO_REST_API_KEY"),
            host=_read_str(source, "DAUM_VIDEO_MCP_HOST", "127.0.0.1"),
            port=_read_int(source, "DAUM_VIDEO_MCP_PORT", 8200),
            path=_read_str(source, "DAUM_VIDEO_MCP_PATH", "/mcp") or "/mcp",
            transport=_read_str(
                source,
                "DAUM_VIDEO_MCP_TRANSPORT",
                "streamable-http",
            ),
            http_timeout_sec=_read_float(source, "DAUM_VIDEO_HTTP_TIMEOUT_SEC", 8.0),
            cache_ttl_sec=_read_int(source, "DAUM_VIDEO_CACHE_TTL_SEC", 300),
            api_base_url=_read_str(
                source,
                "DAUM_VIDEO_API_BASE_URL",
                "https://dapi.kakao.com/v2/search",
            ),
        )

    def require_api_key(self) -> None:
        if self.api_key:
            return
        raise ValidationError("KAKAO_REST_API_KEY must be configured")
