# Tool Contract

## Purpose

This document defines the initial public contract for `daum-video-mcp`.

## Transport

Primary transport:

- MCP over `streamable-http`

Example endpoints:

- MCP: `http://127.0.0.1:8200/mcp`
- health: `http://127.0.0.1:8200/healthz`

## Primary API Source

This repository should use the Daum video search endpoint:

- `GET https://dapi.kakao.com/v2/search/vclip`

Official reference:

- [Daum Search REST API](https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide)

## Common Response Shape

```json
{
  "query": "poker check raise lesson",
  "source": "daum_video",
  "items": [],
  "meta": {
    "pageable_count": 123,
    "total_count": 456,
    "is_end": false,
    "page": 1,
    "size": 10,
    "cached": false
  }
}
```

## Common Item Shape

```json
{
  "title": "normalized title",
  "link": "https://...",
  "snippet": "normalized summary",
  "source": "daum_video",
  "thumbnail_url": "https://...",
  "published_at": "2026-03-19T12:00:00+09:00",
  "play_time": 620,
  "author": "publisher or channel",
  "score": 0.0
}
```

Optional raw fields may be appended if useful.

## Tools

### `search_video`

Input:

```json
{
  "query": "poker check raise lesson",
  "sort": "accuracy",
  "page": 1,
  "size": 10
}
```

Supported input rules:

- `query` is required
- `sort` is `accuracy` or `recency`
- `page` must be between `1` and `15`
- `size` must be between `1` and `30`

Expected output:

```json
{
  "query": "poker check raise lesson",
  "source": "daum_video",
  "items": [
    {
      "title": "체크레이즈 강의",
      "link": "https://...",
      "snippet": "체크레이즈 개념 설명",
      "source": "daum_video",
      "thumbnail_url": "https://...",
      "published_at": "2026-03-18T10:00:00+09:00",
      "play_time": 620,
      "author": "YouTube"
    }
  ],
  "meta": {
    "pageable_count": 100,
    "total_count": 240,
    "is_end": false,
    "page": 1,
    "size": 10,
    "cached": false
  }
}
```

### `search_video_auto`

This tool is optional.

If added, it should accept:

```json
{
  "query": "check raise tutorial",
  "size": 5
}
```

And may internally call `search_video` with defaults.

Current convenience behavior:

- defaults to `page=1`
- defaults to `size=5`
- may switch to `recency` when the query clearly asks for fresh results

The output should still follow the same response shape.

## Normalization Rules

- strip HTML tags from titles and contents
- normalize datetime fields to `published_at`
- expose original URL as `link`
- expose thumbnail as `thumbnail_url`
- expose running time as `play_time`
- expose publisher or source as `author` when available

## Validation Rules

- reject empty `query`
- reject unsupported `sort`
- clamp or reject invalid `page` and `size`

## Error Shape

Errors should be structured:

```json
{
  "error": {
    "code": "DAUM_VIDEO_API_ERROR",
    "message": "Daum video search request failed",
    "retryable": true
  }
}
```

Recommended codes:

- `KAKAO_AUTH_ERROR`
- `KAKAO_RATE_LIMIT`
- `DAUM_VIDEO_TIMEOUT`
- `DAUM_VIDEO_API_ERROR`
- `VALIDATION_ERROR`

## Timeout Guidance

Suggested defaults:

- 6 to 8 seconds per request

## Cache Guidance

Suggested defaults:

- 5 to 10 minutes for identical queries

## Backward Compatibility

- additive fields are allowed
- tool names should remain stable once published
- breaking schema changes should be documented before implementation
