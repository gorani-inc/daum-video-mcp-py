# daum-video-mcp

Small Python MCP server and reusable client for Daum video search only.

This repository is intentionally narrow:

- one upstream API: `GET https://dapi.kakao.com/v2/search/vclip`
- one primary MCP tool: `search_video`
- one optional convenience tool: `search_video_auto`

It is meant to be safe to publish as a public repository. Secrets stay in local environment variables, response fields are normalized into a stable schema, and tests rely on mocked payloads instead of live network calls.

## What This Repository Does

- calls the Daum video search API with a Kakao REST API key
- normalizes raw video documents into a predictable response shape
- exposes the search tools through FastMCP
- keeps timeout, retry, cache, and validation logic inside the repository

## What This Repository Does Not Do

- web, image, local, or map search
- chat-app-specific rendering
- orchestrator policy or tool routing
- unrelated Kakao APIs

## Requirements

- Python 3.10+
- Kakao Developers app with a valid `REST API 키`

Official reference:

- [Daum Search REST API](https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide)
- [FastMCP installation](https://gofastmcp.com/v2/getting-started/installation)

## Installation

### Runtime install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e ".[server]"
```

### Development install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e ".[server,dev]"
```

## Configuration

Copy the example file and set your API key:

```bash
cp .env.example .env
```

`python-dotenv` is loaded automatically, so `python -m daum_video_mcp.server` will read `.env` without an extra `source` step.

### Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `KAKAO_REST_API_KEY` | Yes | - | Kakao Developers REST API key |
| `DAUM_VIDEO_MCP_HOST` | No | `127.0.0.1` | MCP bind host |
| `DAUM_VIDEO_MCP_PORT` | No | `8200` | MCP bind port |
| `DAUM_VIDEO_MCP_PATH` | No | `/mcp` | MCP HTTP mount path |
| `DAUM_VIDEO_MCP_TRANSPORT` | No | `streamable-http` | FastMCP transport |
| `DAUM_VIDEO_HTTP_TIMEOUT_SEC` | No | `8.0` | Upstream HTTP timeout |
| `DAUM_VIDEO_CACHE_TTL_SEC` | No | `300` | In-memory cache TTL in seconds |
| `DAUM_VIDEO_API_BASE_URL` | No | `https://dapi.kakao.com/v2/search` | Override only for tests or custom proxies |

## Run

Start the MCP server:

```bash
python -m daum_video_mcp.server
```

Default endpoints:

- MCP: `http://127.0.0.1:8200/mcp`
- health: `http://127.0.0.1:8200/healthz`

If `fastmcp` is not installed, install the server extra first:

```bash
pip install -e ".[server]"
```

## Linux Server Example

Example deployment path:

```bash
/home/<deploy-user>/daum-video-mcp-py
```

Clone and install on Ubuntu or Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git

git clone <YOUR_PUBLIC_REPO_URL> /home/<deploy-user>/daum-video-mcp-py
cd /home/<deploy-user>/daum-video-mcp-py

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e ".[server]"
cp .env.example .env
```

Run manually:

```bash
cd /home/<deploy-user>/daum-video-mcp-py
source .venv/bin/activate
python -m daum_video_mcp.server
```

### systemd

Create `/etc/systemd/system/daum-video-mcp.service`:

```ini
[Unit]
Description=Daum Video MCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/<deploy-user>/daum-video-mcp-py
EnvironmentFile=/home/<deploy-user>/daum-video-mcp-py/.env
ExecStart=/home/<deploy-user>/daum-video-mcp-py/.venv/bin/python -m daum_video_mcp.server
Restart=always
RestartSec=3
User=<deploy-user>
Group=<deploy-user>

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now daum-video-mcp
sudo systemctl status daum-video-mcp
```

Check logs:

```bash
journalctl -u daum-video-mcp -f
```

If the server should accept external connections, set this in `.env`:

```env
DAUM_VIDEO_MCP_HOST=0.0.0.0
DAUM_VIDEO_MCP_PORT=8200
```

Replace `<deploy-user>` with your actual Linux account name when you deploy.

## Tools

### `search_video`

Maps closely to the Daum video search API.

Input:

```json
{
  "query": "poker check raise lesson",
  "sort": "accuracy",
  "page": 1,
  "size": 10
}
```

Validation:

- `query` must not be empty
- `sort` must be `accuracy` or `recency`
- `page` must be between `1` and `15`
- `size` must be between `1` and `30`

### `search_video_auto`

Small convenience wrapper around `search_video`.

- defaults to `page=1`
- defaults to `size=5`
- switches to `recency` when the query clearly asks for freshness such as `최신`, `recent`, `latest`, or `오늘`

## Response Shape

```json
{
  "query": "poker check raise lesson",
  "source": "daum_video",
  "items": [
    {
      "title": "체크레이즈 강의",
      "link": "https://example.com/video",
      "snippet": "체크레이즈 개념 설명",
      "source": "daum_video",
      "thumbnail_url": "https://example.com/thumb.jpg",
      "published_at": "2026-03-19T12:00:00+09:00",
      "play_time": 620,
      "author": "YouTube",
      "score": 0.0
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

Validation and upstream failures are returned as structured errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "query must not be empty",
    "retryable": false
  }
}
```

## Test

Run the test suite:

```bash
python -m unittest discover -s tests
```

Optional developer checks:

```bash
pytest
ruff check .
python -m py_compile src/daum_video_mcp/*.py tests/*.py
```

## Public Repository Notes

- `.env` is ignored and should never be committed.
- Choose and add a real open-source license before publishing if the repository will be shared publicly.
- Keep live API tests optional so contributors can work without Kakao credentials.

## Repository Layout

```text
daum-video-mcp/
  README.md
  AGENTS.md
  .env.example
  pyproject.toml
  src/daum_video_mcp/
    __init__.py
    cache.py
    client.py
    config.py
    errors.py
    models.py
    normalize.py
    server.py
    tools_video.py
  tests/
    test_normalize.py
    test_tools_video.py
  docs/
    architecture.md
    tool-contract.md
```

## Documentation

- [docs/architecture.md](docs/architecture.md)
- [docs/tool-contract.md](docs/tool-contract.md)
- [AGENTS.md](AGENTS.md)
