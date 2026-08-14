"""HTTP API consumed by the kiosk frontend (and by admins over SSH)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api")


@router.get("/state")
async def get_state(request: Request) -> dict:
    return request.app.state.display.snapshot()


@router.get("/health")
async def get_health(request: Request) -> dict:
    display = request.app.state.display
    return {
        "status": "ok",
        "elastic_reachable": display.elastic_reachable,
        "sources": {
            name: source.status.value for name, source in display.sources.items()
        },
        "sse_clients": request.app.state.bus.subscriber_count,
    }


@router.get("/events")
async def get_events(request: Request) -> StreamingResponse:
    bus = request.app.state.bus
    display = request.app.state.display
    return StreamingResponse(
        bus.stream(initial=display.snapshot()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
