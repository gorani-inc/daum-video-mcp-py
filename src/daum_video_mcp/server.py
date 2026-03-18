from __future__ import annotations

import contextlib
from typing import Any, Optional

from .cache import TTLCache
from .client import DaumVideoClient
from .config import DaumVideoMCPConfig
from .tools_video import VideoTools

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional runtime dependency
    FastMCP = None  # type: ignore[assignment]

try:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
except ImportError:  # pragma: no cover - optional runtime dependency
    uvicorn = None  # type: ignore[assignment]
    Starlette = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    Mount = None  # type: ignore[assignment]
    Route = None  # type: ignore[assignment]


def create_server(config: Optional[DaumVideoMCPConfig] = None) -> Any:
    if FastMCP is None:
        raise RuntimeError(
            "fastmcp is not installed. Install the optional 'server' dependency first."
        )

    # 서버는 의존성 조립과 도구 등록만 맡고, 실제 검색 로직은 tools 계층에 위임한다.
    resolved_config = config or DaumVideoMCPConfig.from_env()
    client = DaumVideoClient(resolved_config)
    tools = VideoTools(
        client,
        cache=TTLCache(default_ttl_sec=resolved_config.cache_ttl_sec),
        config=resolved_config,
    )

    server = FastMCP("daum-video-mcp")

    @server.tool()
    def search_video(
        query: str,
        sort: str = "accuracy",
        page: int = 1,
        size: int = 10,
    ) -> dict[str, Any]:
        return tools.search_video(query=query, sort=sort, page=page, size=size)

    @server.tool()
    def search_video_auto(
        query: str,
        size: int = 5,
    ) -> dict[str, Any]:
        return tools.search_video_auto(query=query, size=size)

    @server.tool()
    def health() -> dict[str, Any]:
        return build_health_payload(resolved_config)

    return server


def build_health_payload(config: DaumVideoMCPConfig) -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "daum-video-mcp",
        "transport": config.transport,
        "host": config.host,
        "port": config.port,
        "path": config.path,
        "healthz": "/healthz",
    }


def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "daum-video-mcp"}


def main() -> None:
    config = DaumVideoMCPConfig.from_env()
    server = create_server(config)
    if _can_run_with_wrapper(server, config):
        _run_with_wrapper(server, config)
        return

    server.run(
        transport=config.transport,
        host=config.host,
        port=config.port,
        path=config.path,
    )


def _can_run_with_wrapper(server: Any, config: DaumVideoMCPConfig) -> bool:
    return bool(
        config.transport == "streamable-http"
        and uvicorn is not None
        and Starlette is not None
        and JSONResponse is not None
        and Mount is not None
        and Route is not None
        and hasattr(server, "streamable_http_app")
    )


def _run_with_wrapper(server: Any, config: DaumVideoMCPConfig) -> None:
    async def healthz_endpoint(_request: Any) -> Any:
        return JSONResponse(healthz())

    @contextlib.asynccontextmanager
    async def lifespan(_app: Any) -> Any:
        session_manager = getattr(server, "session_manager", None)
        if session_manager is not None and hasattr(session_manager, "run"):
            # streamable-http 경로를 Starlette에 마운트할 때 FastMCP 세션 수명을 함께 관리한다.
            async with contextlib.AsyncExitStack() as stack:
                await stack.enter_async_context(session_manager.run())
                yield
            return
        yield

    app = Starlette(
        lifespan=lifespan,
        routes=[
            Route("/healthz", endpoint=healthz_endpoint),
            Mount(config.path, app=server.streamable_http_app()),
        ],
    )
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
