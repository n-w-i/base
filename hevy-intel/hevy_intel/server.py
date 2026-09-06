import asyncio

import uvicorn

from hevy_intel.client import sync_all, HevyNotConfigured


def _try_sync():
    try:
        sync_all()
    except HevyNotConfigured as e:
        print(f"[sync] {e}")
    except Exception as e:
        print(f"[sync] Error: {e}")


async def _sync_loop(interval_minutes: int):
    while True:
        await asyncio.sleep(interval_minutes * 60)
        _try_sync()


async def run_server(port: int, sync_interval: int):
    config = uvicorn.Config(
        "hevy_intel.api:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    if sync_interval > 0:
        _try_sync()
        sync_task = asyncio.create_task(_sync_loop(sync_interval))
        try:
            await server.serve()
        finally:
            sync_task.cancel()
    else:
        await server.serve()
