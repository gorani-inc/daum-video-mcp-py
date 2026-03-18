from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping, Optional

from .config import DaumVideoMCPConfig
from .errors import (
    DaumVideoAPIError,
    DaumVideoTimeoutError,
    KakaoAuthError,
    KakaoRateLimitError,
)
from .models import VideoSearchRequest

Transport = Callable[
    [str, str, Mapping[str, str], Optional[bytes], float],
    Mapping[str, Any],
]


class DaumVideoClient:
    def __init__(
        self,
        config: DaumVideoMCPConfig,
        *,
        transport: Optional[Transport] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        max_retries: int = 2,
    ) -> None:
        self.config = config
        self._transport = transport or self._default_transport
        self._sleep_fn = sleep_fn or time.sleep
        self._max_retries = max(1, max_retries)

    def search_video(self, request: VideoSearchRequest) -> Mapping[str, Any]:
        return self._request_json("GET", "vclip", params=request.to_params())

    def _request_json(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, object]] = None,
    ) -> Mapping[str, Any]:
        url = self._build_url(endpoint, params=params)
        headers = self._build_headers()

        # 재시도는 timeout, rate limit, 일시적 서버 오류처럼 회복 가능성이 있는 경우에만 허용한다.
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._transport(
                    method,
                    url,
                    headers,
                    None,
                    self.config.http_timeout_sec,
                )
            except (DaumVideoTimeoutError, KakaoRateLimitError) as exc:
                if attempt >= self._max_retries:
                    raise
                self._sleep_fn(min(0.2 * attempt, 1.0))
                last_exc = exc
            except DaumVideoAPIError as exc:
                if not exc.is_retryable or attempt >= self._max_retries:
                    raise
                self._sleep_fn(min(0.2 * attempt, 1.0))
                last_exc = exc

        raise DaumVideoAPIError(str(last_exc))

    def _build_headers(self) -> dict[str, str]:
        # 인증 누락은 네트워크 호출 전에 즉시 드러내는 편이 운영 중 원인 파악이 쉽다.
        self.config.require_api_key()
        return {
            "Accept": "application/json",
            "Authorization": f"KakaoAK {self.config.api_key}",
        }

    def _build_url(
        self,
        endpoint: str,
        *,
        params: Optional[Mapping[str, object]] = None,
    ) -> str:
        base = self.config.api_base_url.rstrip("/")
        url = f"{base}/{endpoint.lstrip('/')}"
        if not params:
            return url
        query_string = urllib.parse.urlencode(params)
        return f"{url}?{query_string}"

    def _default_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: float,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(
            url=url,
            headers=dict(headers),
            data=body,
            method=method,
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            self._raise_for_http_error(exc.code, raw_body)
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, socket.timeout) or "timed out" in str(reason).lower():
                raise DaumVideoTimeoutError("Daum video search request timed out") from exc
            raise DaumVideoAPIError(
                "Daum video search request failed",
                retryable=True,
            ) from exc
        except TimeoutError as exc:
            raise DaumVideoTimeoutError("Daum video search request timed out") from exc

        try:
            parsed = json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise DaumVideoAPIError("Daum video search returned invalid JSON") from exc

        if not isinstance(parsed, Mapping):
            raise DaumVideoAPIError("Daum video search returned an unexpected payload")
        return parsed

    def _raise_for_http_error(self, status_code: int, body: str) -> None:
        # 상위 계층이 일관되게 처리할 수 있도록 HTTP 상태를 내부 에러 코드로 정규화한다.
        message = body.strip() or f"Daum video search request failed with status {status_code}"
        if status_code in {401, 403}:
            raise KakaoAuthError(message, status_code=status_code)
        if status_code == 429:
            raise KakaoRateLimitError(message, status_code=status_code)
        if status_code in {408, 504}:
            raise DaumVideoTimeoutError(message, status_code=status_code)
        if status_code >= 500:
            raise DaumVideoAPIError(
                message,
                status_code=status_code,
                retryable=True,
            )
        raise DaumVideoAPIError(message, status_code=status_code)
