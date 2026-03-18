from __future__ import annotations

import unittest
from typing import Any, Mapping

from daum_video_mcp.cache import TTLCache
from daum_video_mcp.config import DaumVideoMCPConfig
from daum_video_mcp.models import VideoSearchRequest
from daum_video_mcp.tools_video import VideoTools


class FakeVideoClient:
    def __init__(self) -> None:
        self.calls = 0
        self.last_request: VideoSearchRequest | None = None

    def search_video(self, request: VideoSearchRequest) -> Mapping[str, Any]:
        self.calls += 1
        self.last_request = request
        return {
            "meta": {
                "total_count": 6033,
                "pageable_count": 800,
                "is_end": False,
            },
            "documents": [
                {
                    "title": "AOA 지민",
                    "contents": "무대 영상",
                    "url": "https://example.com/video",
                    "thumbnail": "https://example.com/thumb.jpg",
                    "datetime": "2017-05-06T00:36:45+09:00",
                    "play_time": 185,
                    "author": "_SBS",
                }
            ],
        }


class VideoToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeVideoClient()
        self.tools = VideoTools(
            self.client,
            cache=TTLCache(default_ttl_sec=300),
            config=DaumVideoMCPConfig(cache_ttl_sec=300),
        )

    def test_search_video_returns_normalized_contract(self) -> None:
        result = self.tools.search_video(
            query="aoa",
            sort="accuracy",
            page=1,
            size=10,
        )

        self.assertEqual(result["query"], "aoa")
        self.assertEqual(result["source"], "daum_video")
        self.assertEqual(result["meta"]["page"], 1)
        self.assertEqual(result["meta"]["size"], 10)
        self.assertFalse(result["meta"]["cached"])
        self.assertEqual(self.client.calls, 1)

    def test_search_video_uses_cache_for_identical_requests(self) -> None:
        first = self.tools.search_video(query="aoa", sort="accuracy", page=1, size=10)
        second = self.tools.search_video(query="aoa", sort="accuracy", page=1, size=10)

        self.assertFalse(first["meta"]["cached"])
        self.assertTrue(second["meta"]["cached"])
        self.assertEqual(self.client.calls, 1)

    def test_search_video_validation_errors_are_structured(self) -> None:
        result = self.tools.search_video(query="  ", sort="accuracy", page=1, size=10)

        self.assertEqual(result["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("query", result["error"]["message"])
        self.assertFalse(result["error"]["retryable"])

    def test_search_video_auto_switches_to_recency_when_query_hints_freshness(self) -> None:
        result = self.tools.search_video_auto(query="최신 aoa 영상", size=5)

        self.assertEqual(result["source"], "daum_video")
        self.assertIsNotNone(self.client.last_request)
        assert self.client.last_request is not None
        self.assertEqual(self.client.last_request.sort, "recency")
        self.assertEqual(self.client.last_request.page, 1)
        self.assertEqual(self.client.last_request.size, 5)


if __name__ == "__main__":
    unittest.main()
