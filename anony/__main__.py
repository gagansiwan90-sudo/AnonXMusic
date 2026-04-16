# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import importlib
import os
import sys
import signal
from contextlib import suppress
import uvicorn
from fastapi import FastAPI
from pyrogram import idle

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

# FastAPI app for Render health checks
web_app = FastAPI()

@web_app.get("/")
async def health_check():
    return {"status": "Bot is running"}

async def run_web_server():
    """Run FastAPI server for Render health checks"""
    port = int(os.environ.get("PORT", 8000))
    config["PORT"] = port
    logger.info(f"🌐 Health check server starting on port {port}")
    await uvicorn.run(web_app, host="0.0.0.0", port=port, log_level="error")

async def main():
    try:
        # Validate config first
        await db.connect()
        
        # Start all bots
        await app.boot()
        await userbot.boot()
        await anon.boot()
        await thumb.start()

        # Load plugins
        for module in all_modules:
            try:
                importlib.import_module(f"anony.plugins.{module}")
            except Exception as e:
                logger.error(f"Failed to load {module}: {e}")
        logger.info(f"✅ Loaded {len(all_modules)} modules")

        # Load sudoers
        sudoers = await db.get_sudoers()
        app.sudoers.update(sudoers)
        app.bl_users.update(await db.get_blacklisted())
        logger.info(f"👑 Loaded {len(app.sudoers)} sudo users")

        if config.COOKIES_URL:
            await yt.save_cookies(config.COOKIES_URL)

        logger.info("🎉 Bot started successfully! Send /start to test.")

        # Run web server and bot idle TOGETHER
        await asyncio.gather(
            run_web_server(),
            idle()
        )
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}", exc_info=True)
    finally:
        await stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
