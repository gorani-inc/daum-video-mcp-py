from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

KST = timezone(timedelta(hours=9))
SOURCE_NAME = "daum_video"
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    # Daum 검색 응답에는 강조용 HTML 태그가 섞일 수 있어 공통 전처리에서 제거한다.
    text = _HTML_TAG_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_datetime(value: Any) -> Optional[str]:
    text = strip_html(value)
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None

    if parsed is not None:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=KST)
        return parsed.isoformat()

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=KST).isoformat()
        except ValueError:
            continue

    return text


def _normalize_play_time(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_video_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "title": strip_html(item.get("title")),
        "link": str(item.get("url") or item.get("link") or ""),
        "snippet": strip_html(item.get("contents") or item.get("snippet")),
        "source": SOURCE_NAME,
        "thumbnail_url": str(item.get("thumbnail") or item.get("thumbnail_url") or ""),
        "published_at": normalize_datetime(item.get("datetime") or item.get("published_at")),
        "play_time": _normalize_play_time(item.get("play_time")),
        "author": strip_html(item.get("author") or item.get("publisher")),
        "score": 0.0,
    }


def normalize_search_video_response(
    query: str,
    payload: Mapping[str, Any],
    *,
    page: int,
    size: int,
    cached: bool = False,
) -> dict[str, Any]:
    raw_items = payload.get("documents", [])
    # 계약 문서 기준의 공통 응답 형태로 먼저 맞춰 두면 MCP 도구와 테스트가 단순해진다.
    items = [
        normalize_video_item(item)
        for item in raw_items
        if isinstance(item, Mapping)
    ]
    meta = payload.get("meta", {})
    pageable_count = _safe_int(meta.get("pageable_count"), default=len(items))
    total_count = _safe_int(meta.get("total_count"), default=len(items))
    is_end = bool(meta.get("is_end", True))
    return {
        "query": query,
        "source": SOURCE_NAME,
        "items": items,
        "meta": {
            "pageable_count": pageable_count,
            "total_count": total_count,
            "is_end": is_end,
            "page": page,
            "size": size,
            "cached": cached,
        },
    }


def _safe_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
