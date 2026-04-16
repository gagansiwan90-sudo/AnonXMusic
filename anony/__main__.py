# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import signal
import importlib
import os
import uvicorn
from contextlib import suppress
from fastapi import FastAPI, Request
from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt)
from anony.plugins import all_modules

app2 = FastAPI()

@app2.post("/")
async def webhook(request: Request):
    """Telegram webhook endpoint"""
    update = request.json()
    # Process with your bot's dispatcher (adjust if needed for pyrogram)
    await app.process_update(update)  # Assuming app has process_update; check anony/app.py
    return {"status": "ok"}

async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()

async def main():
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

    # Start webhook server
    port = int(os.environ.get("PORT", 8000))
    config["WEBHOOK_URL"] = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/"
    logger.info(f"Starting webhook on port {port}, URL: {config['WEBHOOK_URL']}")
    
    # Set Telegram webhook if BOT_TOKEN available
    if hasattr(app, 'bot') and app.bot:
        await app.bot.set_webhook(config["WEBHOOK_URL"])

    await idle()
    await stop()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    uvicorn.run("main:app2", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
