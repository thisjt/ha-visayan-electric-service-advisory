"""Data update coordinator for Visayan Electric Service Advisory."""
from __future__ import annotations

import html
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

def _parse_post_html(html_content: str, post_data: dict) -> list[dict]:
    """Parse the full post HTML into a list of advisory dicts."""
    # Find the post content container
    post_match = re.search(r'<section[^>]*data-hook="post-description"[^>]*>(.*?)</section>', html_content, re.DOTALL)
    if post_match:
        content = post_match.group(1)
    else:
        content = html_content

    content = content.replace('&nbsp;', ' ').replace('\xa0', ' ')

    advisories = []
    current_date = post_data.get("title", "Unknown Date")
    date_regex = re.compile(r'([A-Za-z]+ \d{1,2}, \d{4})')
    
    items = []
    
    # Find dates (underlined spans are the common marker for dates in these posts)
    for match in re.finditer(r'<u[^>]*>.*?<span>([^<]+, \d{4}[^<]*)</span>.*?</u>', content, re.DOTALL):
        items.append({
            'pos': match.start(),
            'type': 'date',
            'value': match.group(1).strip()
        })
    
    # If no structured dates found, look for plain text dates
    if not items:
         for match in re.finditer(r'([A-Za-z]+ \d{1,2}, \d{4} \([A-Za-z]+\))', content):
             items.append({
                'pos': match.start(),
                'type': 'date',
                'value': match.group(1).strip()
            })

    # Find tables (each advisory is in a table)
    for match in re.finditer(r'<table.*?>.*?</table>', content, re.DOTALL):
        items.append({
            'pos': match.start(),
            'type': 'table',
            'value': match.group(0)
        })
        
    # Sort by position to maintain the date -> table relationship
    items.sort(key=lambda x: x['pos'])
    
    for item in items:
        if item['type'] == 'date':
            d_match = date_regex.search(item['value'])
            if d_match:
                current_date = d_match.group(1)
        elif item['type'] == 'table':
            table_content = item['value']
            advisory = {
                "date": current_date,
                "time": "",
                "duration": "",
                "cancelled": False,
                "purpose": "",
                "areas_affected": "",
                "map": "",
                "post_url": post_data.get("link", ""),
                "post_title": post_data.get("title", ""),
            }
            
            # Extract fields from table rows
            rows = re.findall(r'<tr.*?>(.*?)</tr>', table_content, re.DOTALL)
            for row in rows:
                cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 2:
                    label = re.sub(r'<[^>]+>', '', cells[0]).strip()
                    # Wix sometimes puts complex HTML in the value cell
                    value_html = cells[1]
                    value = re.sub(r'<[^>]+>', '', value_html).strip()
                    value = html.unescape(value)
                    
                    if "Time" in label:
                        advisory["time"] = value
                        # Extract duration if present: (4hrs)
                        duration_match = re.search(r'\((\d+(\.\d+)?hrs)\)', value)
                        if duration_match:
                            advisory["duration"] = duration_match.group(1)
                            advisory["time"] = value.split('(')[0].strip()
                        
                        if "CANCELLED" in value.upper() or CANCELLED_UNICODE in value:
                            advisory["cancelled"] = True
                    elif "Purpose" in label:
                        advisory["purpose"] = value
                    elif "Areas Affected" in label:
                        advisory["areas_affected"] = value
                    elif "Map" in label:
                        # Extract image URI from Wix image component
                        image_match = re.search(r'data-image-info=[\'\"]({.*?})[\'\"]', value_html)
                        if image_match:
                            try:
                                json_str = html.unescape(image_match.group(1))
                                img_info = json.loads(json_str)
                                uri = img_info.get("uri") or img_info.get("imageData", {}).get("uri")
                                if uri:
                                    advisory["map"] = f"https://static.wixstatic.com/media/{uri}"
                            except:
                                pass
            
            if advisory["time"] or advisory["purpose"] or advisory["areas_affected"]:
                advisories.append(advisory)
                
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
                # Step 1: Fetch the blog feed page to find the latest post
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
                    feed_html = await resp.text()

                posts = _extract_posts_from_html(feed_html)
                if not posts:
                    _LOGGER.debug("No posts found in feed page.")
                    return []

                # Determine the latest post based on firstPublishedDate
                latest_post = max(
                    posts,
                    key=lambda p: p.get("firstPublishedDate", "")
                )
                
                post_url = latest_post.get("link")
                if not post_url:
                    _LOGGER.error("Latest post missing link.")
                    return []

                # Step 2: Fetch the full HTML of the latest post
                _LOGGER.debug("Fetching latest advisory post: %s", post_url)
                async with session.get(
                    post_url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; HomeAssistant/VECO-SA)"
                        )
                    },
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(
                            f"HTTP {resp.status} fetching {post_url}"
                        )
                    post_html = await resp.text()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching VECO page: {err}") from err

        # Step 3: Parse the full post HTML
        advisories: list[dict] = _parse_post_html(post_html, latest_post)

        _LOGGER.debug(
            "Fetched %d advisories from latest post (title: %s)",
            len(advisories),
            latest_post.get("title", "")
        )
        return advisories
