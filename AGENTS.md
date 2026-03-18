# AGENTS.md

This repository is a Python MCP server for Daum video search.

## Mission

Build a small and reliable MCP server focused on one job:

- searching videos well

## Priority Order

1. Contract clarity
2. Stable normalization
3. Operational simplicity
4. Narrow scope
5. Optional convenience features

## What This Repository Owns

- Daum video search API client code
- normalized response schema
- MCP tool implementation
- timeout, retry, cache, and validation behavior
- tests for video tool contracts

## What This Repository Does Not Own

- image search
- local or map search
- general web search
- KakaoTalk reply rendering
- orchestrator policy

## Coding Guidelines

- Keep the client layer separate from tool functions.
- Normalize returned fields consistently.
- Preserve important source fields such as title, URL, thumbnail, play time, and datetime when available.
- Avoid chat-app-specific assumptions in tool output.
- Keep heuristics minimal and documented.

## Tool Design Rules

- `search_video` should map closely to the Daum video search API.
- `search_video_auto` should only be added if it adds real convenience.
- All tools should return a predictable `meta` block.
- Validation errors should be explicit and structured.

## Testing Rules

- Add tests for normalization.
- Add contract tests for each MCP tool.
- Prefer mocked HTTP responses.
- Keep live network tests optional.

## File Ownership Hints

- `client.py`: Daum HTTP client only
- `normalize.py`: response cleanup and normalized shaping
- `tools_video.py`: MCP tools
- `server.py`: FastMCP setup and health endpoints
- `models.py`: request and response models

## When Extending The Repository

- Update `docs/tool-contract.md` before or with implementation changes.
- Keep the scope narrow.
- Do not add unrelated Kakao APIs unless the repository purpose is intentionally broadened.

## First Steps For A New Codex Session

1. Read `README.md`.
2. Read `docs/architecture.md`.
3. Read `docs/tool-contract.md`.
4. Implement the smallest end-to-end slice first.
