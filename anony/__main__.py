# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import asyncio
import signal
import importlib

from aiohttp import web
from contextlib import suppress

from anony import (
    anon,
    app,
    config,
    db,
    logger,
    stop,
    thumb,
    userbot,
    yt
)

from anony.plugins import all_modules


# ==========================================
# Render Web Server
# ==========================================

async def home(request):
    return web.Response(text="AnonXMusic Bot Running!")

async def start_webserver():
    app_web = web.Application()
    app_web.router.add_get("/", home)

    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app_web)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Web server started on port {port}")


# ==========================================
# Idle
# ==========================================

async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    await stop_event.wait()


# ==========================================
# Main
# ==========================================

async def main():

    # Start Render HTTP server
    await start_webserver()

    # Bot startup
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    # Load plugins
    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")

    logger.info(f"Loaded {len(all_modules)} modules.")

    # Save cookies
    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    # Load sudo users
    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())

    logger.info(f"Loaded {len(app.sudoers)} sudo users.")

    # Keep alive
    await idle()

    # Stop bot
    asyncio.create_task(stop())


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
