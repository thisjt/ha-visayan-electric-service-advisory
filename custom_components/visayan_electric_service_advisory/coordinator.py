"""Data update coordinator for Visayan Electric Service Advisory."""
from __future__ import annotations

import json
import logging
import re
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, SERVICE_ADVISORY_URL

_LOGGER = logging.getLogger(__name__)

# Unicode "CANCELLED" in mathematical bold capitals (𝗖𝗔𝗡𝗖𝗘𝗟𝗟𝗘𝗗)
# The text uses Unicode Mathematical Bold Capital letters
CANCELLED_UNICODE = "\U0001d402\U0001d400\U0001d40d\U0001d402\U0001d404\U0001d40b\U0001d40b\U0001d404\U0001d403"

# Pattern to parse each interruption block from the excerpt
# Matches: Time: ... (duration) Purpose: ... Areas Affected: ... [up to next Time:, Map:, or end]
_ADVISORY_PATTERN = re.compile(
    r"Time:\s*"
    r"(?P<cancelled_pre>(?:CANCELLED|" + re.escape(CANCELLED_UNICODE) + r")\s*)?"
    r"(?P<time>[^\(\n]+?)"
    r"(?:\s*\((?P<duration>[^\)]+)\))?"
    r"\s*(?:CANCELLED|" + re.escape(CANCELLED_UNICODE) + r")?\s*"
    r"Purpose:\s*(?P<purpose>.+?)\s*"
    r"Areas Affected:\s*(?P<areas>.+?)"
    r"(?=\s*Map:|\s*Time:|\.\.\.$|$)",
    re.DOTALL | re.IGNORECASE,
)

# Pattern to get the leading date from an excerpt
_DATE_PATTERN = re.compile(
    r"^([A-Z][a-z]+ \d{1,2},\s*\d{4})",
)


def _parse_excerpt(excerpt: str, post: dict) -> list[dict]:
    """Parse a post excerpt into a list of advisory dicts."""
    advisories = []

    map_url = (
        post.get("media", {})
        .get("wixMedia", {})
        .get("image", {})
        .get("url", "")
    )

    date_match = _DATE_PATTERN.match(excerpt.strip())
    date_str = date_match.group(1).strip() if date_match else post.get("title", "")

    for m in _ADVISORY_PATTERN.finditer(excerpt):
        time_raw = (m.group("time") or "").strip()
        duration_raw = (m.group("duration") or "").strip()
        purpose_raw = (m.group("purpose") or "").strip()
        areas_raw = (m.group("areas") or "").strip().rstrip(".")

        # Detect cancellation: either a prefix group matched, or the time string
        # contains a cancelled marker
        cancelled = bool(m.group("cancelled_pre")) or (
            "CANCELLED" in time_raw.upper()
            or CANCELLED_UNICODE in time_raw
        )

        # Clean unicode CANCELLED out of time string
        time_clean = time_raw.replace(CANCELLED_UNICODE, "").replace("CANCELLED", "").strip()

        advisories.append(
            {
                "date": date_str,
                "time": time_clean,
                "duration": duration_raw,
                "cancelled": cancelled,
                "purpose": purpose_raw,
                "areas_affected": areas_raw,
                "map": map_url,
                "post_url": post.get("link", ""),
                "post_title": post.get("title", ""),
            }
        )

    return advisories


def _extract_posts_from_html(html: str) -> list[dict]:
    """Extract blog post data from the wix-warmup-data script block."""
    script_match = re.search(
        r'<script[^>]+id="wix-warmup-data"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not script_match:
        raise UpdateFailed("Could not find wix-warmup-data script block in page HTML")

    try:
        outer = json.loads(script_match.group(1))
    except json.JSONDecodeError as err:
        raise UpdateFailed(f"Failed to parse wix-warmup-data JSON: {err}") from err

    apps_data = outer.get("appsWarmupData", {})
    for _app_id, app_entries in apps_data.items():
        for _entry_key, entry_value in app_entries.items():
            if not isinstance(entry_value, str) or not entry_value.startswith("{"):
                continue
            try:
                inner = json.loads(entry_value)
                posts = (
                    inner.get("response", {})
                    .get("data", {})
                    .get("postFeedPage", {})
                    .get("posts", {})
                    .get("posts", [])
                )
                if posts:
                    return posts
            except (json.JSONDecodeError, AttributeError):
                continue

    raise UpdateFailed("Could not locate posts list in wix-warmup-data")


class VECOServiceAdvisoryCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches and parses Visayan Electric service advisories."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> list[dict]:
        """Fetch data from VECO website."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    SERVICE_ADVISORY_URL,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; HomeAssistant/VECO-SA)"
                        )
                    },
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(
                            f"HTTP {resp.status} fetching {SERVICE_ADVISORY_URL}"
                        )
                    html = await resp.text()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching VECO page: {err}") from err

        posts = _extract_posts_from_html(html)

        advisories: list[dict] = []
        for post in posts:
            excerpt = post.get("excerpt", "")
            advisories.extend(_parse_excerpt(excerpt, post))

        _LOGGER.debug(
            "Fetched %d advisories from %d posts", len(advisories), len(posts)
        )
        return advisories
