from __future__ import annotations

import unittest

from daum_video_mcp.normalize import normalize_search_video_response, normalize_video_item


class NormalizeVideoTests(unittest.TestCase):
    def test_normalize_video_item_strips_html_and_keeps_core_fields(self) -> None:
        item = {
            "title": "AOA <b>라이브</b>",
            "contents": "AOA <b>무대</b> 하이라이트",
            "url": "https://example.com/video",
            "thumbnail": "https://example.com/thumb.jpg",
            "datetime": "2017-05-06T00:36:45+09:00",
            "play_time": 185,
            "author": "_SBS",
        }

        normalized = normalize_video_item(item)

        self.assertEqual(normalized["title"], "AOA 라이브")
        self.assertEqual(normalized["snippet"], "AOA 무대 하이라이트")
        self.assertEqual(normalized["link"], "https://example.com/video")
        self.assertEqual(normalized["thumbnail_url"], "https://example.com/thumb.jpg")
        self.assertEqual(normalized["published_at"], "2017-05-06T00:36:45+09:00")
        self.assertEqual(normalized["play_time"], 185)
        self.assertEqual(normalized["author"], "_SBS")
        self.assertEqual(normalized["source"], "daum_video")

    def test_normalize_search_video_response_matches_contract_shape(self) -> None:
        payload = {
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

        normalized = normalize_search_video_response(
            "aoa",
            payload,
            page=1,
            size=10,
            cached=False,
        )

        self.assertEqual(normalized["query"], "aoa")
        self.assertEqual(normalized["source"], "daum_video")
        self.assertEqual(len(normalized["items"]), 1)
        self.assertEqual(
            normalized["meta"],
            {
                "pageable_count": 800,
                "total_count": 6033,
                "is_end": False,
                "page": 1,
                "size": 10,
                "cached": False,
            },
        )


if __name__ == "__main__":
    unittest.main()

