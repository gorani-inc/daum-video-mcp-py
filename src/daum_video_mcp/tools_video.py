from __future__ import annotations

import json
from typing import Any, Mapping, Optional, Protocol

from .cache import TTLCache
from .config import DaumVideoMCPConfig
from .errors import DaumVideoMCPError
from .models import VideoSearchAutoRequest, VideoSearchRequest
from .normalize import normalize_search_video_response


class VideoClientProtocol(Protocol):
    def search_video(self, request: VideoSearchRequest) -> Mapping[str, Any]:
        ...


class VideoTools:
    _RECENCY_HINTS = ("latest", "recent", "today", "오늘", "최신", "업로드", "방금")

    def __init__(
        self,
        client: VideoClientProtocol,
        *,
        cache: Optional[TTLCache] = None,
        config: Optional[DaumVideoMCPConfig] = None,
    ) -> None:
        self.client = client
        self.config = config or DaumVideoMCPConfig()
        self.cache = cache or TTLCache(default_ttl_sec=self.config.cache_ttl_sec)

    def search_video(
        self,
        *,
        query: str,
        sort: str = "accuracy",
        page: int = 1,
        size: int = 10,
    ) -> dict[str, Any]:
        try:
            request = VideoSearchRequest(query=query, sort=sort, page=page, size=size)
            cache_key = self._build_cache_key("search_video", request.to_params())
            cached = self.cache.get(cache_key)
            if cached is not None:
                cached["meta"]["cached"] = True
                return cached

            payload = self.client.search_video(request)
            normalized = normalize_search_video_response(
                request.query,
                payload,
                page=request.page,
                size=request.size,
                cached=False,
            )
            self.cache.set(cache_key, normalized)
            return normalized
        except DaumVideoMCPError as exc:
            return exc.to_dict()

    def search_video_auto(
        self,
        *,
        query: str,
        size: int = 5,
    ) -> dict[str, Any]:
        try:
            request = VideoSearchAutoRequest(query=query, size=size)
        except DaumVideoMCPError as exc:
            return exc.to_dict()

        # 자동 도구는 과한 추론 대신 최신성 힌트만 반영하는 얇은 래퍼로 유지한다.
        sort = self._detect_sort(request.query)
        return self.search_video(
            query=request.query,
            sort=sort,
            page=1,
            size=request.size,
        )

    def _build_cache_key(self, tool_name: str, params: Mapping[str, object]) -> str:
        return json.dumps(
            {
                "tool": tool_name,
                "params": dict(params),
            },
            ensure_ascii=True,
            sort_keys=True,
        )

    def _detect_sort(self, query: str) -> str:
        lowered = query.lower()
        if any(hint in lowered for hint in self._RECENCY_HINTS):
            return "recency"
        return "accuracy"
