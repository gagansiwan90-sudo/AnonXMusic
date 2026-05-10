# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp

from pathlib import Path
from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
        self.warned = False

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    # =========================================================
    # COOKIES
    # =========================================================

    def get_cookies(self):
        if not self.checked:
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")

            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; YouTube may fail.")

            return None

        cookie = self.cookies[0]

        logger.info(f"Using cookies: {cookie}")

        return cookie

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")

        os.makedirs(self.cookie_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    name = url.split("/")[-1]
                    link = "https://batbin.me/raw/" + name

                    async with session.get(link) as resp:
                        resp.raise_for_status()

                        with open(
                            f"{self.cookie_dir}/{name}.txt",
                            "wb"
                        ) as fw:
                            fw.write(await resp.read())

                except Exception as ex:
                    logger.error(f"Cookie download failed: {ex}")

        logger.info(f"Cookies saved in {self.cookie_dir}.")

    # =========================================================
    # URL CHECKS
    # =========================================================

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    # =========================================================
    # SEARCH
    # =========================================================

    async def search(
        self,
        query: str,
        m_id: int,
        video: bool = False
    ) -> Track | None:

        try:
            _search = VideosSearch(
                query,
                limit=1,
                with_live=False
            )

            results = await _search.next()

        except Exception as ex:
            logger.error(f"Search error: {ex}")
            return None

        if results and results["result"]:
            data = results["result"][0]

            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(
                    data.get("duration")
                ),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1]
                .get("url")
                .split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )

        return None

    # =========================================================
    # PLAYLIST
    # =========================================================

    async def playlist(
        self,
        limit: int,
        user: str,
        url: str,
        video: bool
    ) -> list[Track | None]:

        tracks = []

        try:
            plist = await Playlist.get(url)

            for data in plist["videos"][:limit]:

                track = Track(
                    id=data.get("id"),
                    channel_name=data.get(
                        "channel",
                        {}
                    ).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(
                        data.get("duration")
                    ),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1]
                    .get("url")
                    .split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )

                tracks.append(track)

        except Exception as ex:
            logger.error(f"Playlist error: {ex}")

        return tracks

    # =========================================================
    # DIRECT STREAM
    # =========================================================

    async def stream(
        self,
        video_id: str
    ) -> str | None:

        url = self.base + video_id

        cookie = self.get_cookies()

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "cookiefile": cookie,
            "extract_flat": False,
            "default_search": "ytsearch",
            "source_address": "0.0.0.0",
            "cachedir": False,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "android",
                        "web"
                    ]
                }
            }
        }

        def _extract():
            try:
                logger.info(f"Streaming: {url}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                    info = ydl.extract_info(
                        url,
                        download=False
                    )

                    if not info:
                        return None

                    if "url" not in info:
                        return None

                    return info["url"]

            except Exception as ex:
                logger.error(f"Stream Error: {ex}")
                return None

        return await asyncio.to_thread(_extract)

    # =========================================================
    # FALLBACK DOWNLOAD
    # =========================================================

    async def download(
        self,
        video_id: str,
        video: bool = False
    ) -> str | None:

        url = self.base + video_id

        ext = "mp4" if video else "m4a"

        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        cookie = self.get_cookies()

        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": True,
            "nocheckcertificate": True,
            "cookiefile": cookie,
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": (
                    "bestvideo[height<=720][ext=mp4]+"
                    "bestaudio[ext=m4a]/best"
                ),
                "merge_output_format": "mp4",
            }

        else:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio[ext=m4a]/bestaudio/best",
            }

        def _download():
            try:
                logger.info(f"Downloading fallback: {url}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                    ydl.download([url])

                return filename

            except Exception as ex:
                logger.error(f"Download failed: {ex}")
                return None

        return await asyncio.to_thread(_download)
