# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import importlib
import os
import sys
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from contextlib import suppress

from pyrogram import idle  # Add if not imported in anony

# File descriptor limit (Linux)
if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass

from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt)
from anony.plugins import all_modules

# HTTP Health Check Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_http_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"🌐 Health check server on port {port}")
    server.serve_forever()

async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()

async def main():
    # HTTP server thread start (Render के लिए)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info("🌐 HTTP health server started")

    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())
    logger.info(f"Loaded {len(app.sudoers)} sudo users.")

    logger.info("🎉 Bot started successfully!")
    await idle()
    await stop()

if __name__ == "__main__":
    asyncio.run(main())
