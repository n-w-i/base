import asyncio

import uvicorn

from whoop_core.client import sync_all


async def _sync_loop(interval_minutes: int):
    while True:
        await asyncio.sleep(interval_minutes * 60)
        try:
            sync_all(days=2)
        except Exception as e:
            print(f"[sync] Error: {e}")


async def run_server(port: int, sync_interval: int):
    config = uvicorn.Config(
        "whoop_core.api:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    if sync_interval > 0:
        sync_all(days=2)
        sync_task = asyncio.create_task(_sync_loop(sync_interval))
        try:
            await server.serve()
        finally:
            sync_task.cancel()
    else:
        await server.serve()
