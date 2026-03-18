"""
Tracker.gg API service for Valorant profile auto-fill.

Reads TRACKER_CF_CLEARANCE and TRACKER_EXTRA_COOKIES from Django settings.
Set those via environment variables — never hard-code credentials in settings.py.
cf_clearance expires roughly every 30 minutes; refresh it from browser DevTools.
"""

import re
from urllib.parse import parse_qs, unquote, urlparse

IMPERSONATE_OPTIONS = ["firefox135", "firefox133", "firefox144", "chrome124", "chrome131"]

_HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://tracker.gg",
    "Referer": "https://tracker.gg/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


def _build_cookie():
    from django.conf import settings

    clearance = getattr(settings, "TRACKER_CF_CLEARANCE", "")
    extra = getattr(settings, "TRACKER_EXTRA_COOKIES", "")
    parts = []
    if clearance:
        parts.append(f"cf_clearance={clearance}")
    if extra:
        parts.append(extra)
    return "; ".join(parts)


def parse_tracker_url(url):
    """
    Parse a tracker.gg profile URL and return profile lookup/filter fields.
    riot_tag always includes the leading '#', e.g. '#wells'.

    Example input:
        https://tracker.gg/valorant/profile/riot/welly%23wells/overview
    Example output:
        {
            'riot_id': 'welly',
            'riot_tag': '#wells',
            'playlist': 'competitive',
            'season_id': '3ea2b318-423b-cf86-25da-7cbb0eefbe2d',
        }
    """
    parsed = urlparse(url)
    m = re.match(r"^/valorant/profile/riot/([^/?#]+)", parsed.path, re.IGNORECASE)
    if not m:
        return None

    if parsed.netloc.lower() not in {"tracker.gg", "www.tracker.gg"}:
        return None

    decoded = unquote(m.group(1))
    if "#" not in decoded:
        return None
    riot_id, tag = decoded.split("#", 1)
    if not riot_id or not tag:
        return None
    query = parse_qs(parsed.query)
    playlist = (query.get("playlist", [""])[0] or "").strip().lower()
    season_id = (query.get("season", [""])[0] or "").strip()

    return {
        "riot_id": riot_id,
        "riot_tag": "#" + tag,
        "playlist": playlist,
        "season_id": season_id,
    }


def fetch_tracker_profile(riot_id, riot_tag, playlist="competitive", season_id=""):
    """
    Fetch and parse a Valorant profile from the tracker.gg API.

    Tries each value in IMPERSONATE_OPTIONS until one returns HTTP 200.
    Raises ValueError with a user-friendly message on expected failures.
    """
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError as exc:
        raise ValueError(
            "curl_cffi is not installed. Run: pip install curl_cffi"
        ) from exc

    combined = f"{riot_id}{riot_tag}"       # e.g. "welly#wells"
    encoded = combined.replace("#", "%23")  # e.g. "welly%23wells"
    url = f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{encoded}"

    headers = {**_HEADERS_BASE, "Cookie": _build_cookie()}

    last_status = None
    for impersonate in IMPERSONATE_OPTIONS:
        try:
            resp = cffi_requests.get(url, headers=headers, impersonate=impersonate)
        except Exception:
            continue

        last_status = resp.status_code

        if resp.status_code == 200:
            return _parse_profile(resp.json(), playlist=playlist, season_id=season_id)
        if resp.status_code == 404:
            raise ValueError(
                f"Player '{riot_id}{riot_tag}' was not found on tracker.gg."
            )
        if resp.status_code == 429:
            raise ValueError(
                "Rate limited by tracker.gg. Please wait a moment and try again."
            )
        if resp.status_code == 401:
            raise ValueError(
                "Tracker.gg authentication failed. "
                "The CF clearance cookie may have expired — refresh it from browser DevTools."
            )

    raise ValueError(
        f"Could not retrieve tracker.gg data (last HTTP status: {last_status}). "
        "The cf_clearance cookie may need refreshing."
    )


def _parse_profile(data, playlist="competitive", season_id=""):
    """Parse the raw tracker.gg API JSON into a flat dict."""
    platform = data["data"]["platformInfo"]
    metadata = data["data"].get("metadata", {})
    handle = platform["platformUserHandle"]
    if "#" in handle:
        riot_id, tag = handle.split("#", 1)
        riot_tag = "#" + tag
    else:
        riot_id = handle
        riot_tag = ""

    avatar_url = platform.get("avatarUrl", "")
    region = metadata.get("activeShard", "").upper()
    segments = data["data"]["segments"]

    def _get_seg(seg_type, attributes=None):
        for seg in segments:
            if seg["type"] != seg_type:
                continue
            if attributes and not all(
                seg["attributes"].get(k) == v for k, v in attributes.items()
            ):
                continue
            return seg
        return None

    # ── Current-season stats ────────────────────────────────────────────
    target_playlist = (playlist or metadata.get("defaultPlaylist") or "competitive").lower()
    default_season_id = season_id or metadata.get("defaultSeason", "")
    season = None
    if default_season_id:
        season = _get_seg(
            "season",
            {"playlist": target_playlist, "seasonId": default_season_id},
        )
    if not season:
        season = _get_seg("season", {"playlist": target_playlist})
    if not season:
        season = _get_seg("season")
    season_stats = season["stats"] if season else {}

    rank_meta = season_stats.get("rank", {}).get("metadata", {})
    current_rank = rank_meta.get("tierName", "")
    current_rank_icon = rank_meta.get("iconUrl", "")

    # ── Peak rank — PRIMARY: dedicated peak-rating segment ──────────────
    peak_seg = _get_seg("peak-rating", {"playlist": target_playlist})
    if peak_seg:
        pr = peak_seg["stats"].get("peakRating", {})
        peak_meta = pr.get("metadata", {})
        peak_rank = pr.get("displayValue", "")
        peak_rank_icon = peak_meta.get("iconUrl", "")
        peak_act = peak_meta.get("actName", "")
    else:
        # FALLBACK: season segment's peakRank (act-scoped only)
        pr = season_stats.get("peakRank", {})
        peak_meta = pr.get("metadata", {})
        peak_rank = pr.get("displayValue", "")
        peak_rank_icon = peak_meta.get("iconUrl", "")
        peak_act = peak_meta.get("actName", "")

    # Some tracker responses omit peak icon metadata; use current rank icon as fallback.
    if not peak_rank_icon:
        peak_rank_icon = current_rank_icon

    # ── Other season stats ───────────────────────────────────────────────
    kd_ratio = ""
    for kd_key in ("kDRatio", "kdRatio", "kd", "killDeathRatio"):
        kd_stat = season_stats.get(kd_key)
        if kd_stat:
            kd_ratio = kd_stat.get("displayValue", "")
            break

    wins = season_stats.get("matchesWon", {}).get("displayValue", "")
    matches_played = season_stats.get("matchesPlayed", {}).get("displayValue", "")
    damage_per_round = season_stats.get("damagePerRound", {}).get("displayValue", "")
    headshot_pct = season_stats.get("headshotsPercentage", {}).get("displayValue", "")

    # ── Top agents ───────────────────────────────────────────────────────
    agent_segs = []
    for seg in segments:
        if seg.get("type") != "agent":
            continue
        attrs = seg.get("attributes", {})
        if attrs.get("playlist") != target_playlist:
            continue
        if default_season_id and attrs.get("seasonId") != default_season_id:
            continue
        agent_segs.append(seg)

    # API order is not guaranteed to be "top"; sort by matches played and then time played.
    agent_segs.sort(
        key=lambda s: (
            s.get("stats", {}).get("matchesPlayed", {}).get("value", 0),
            s.get("stats", {}).get("timePlayed", {}).get("value", 0),
        ),
        reverse=True,
    )

    if not agent_segs:
        agent_segs = [s for s in segments if s.get("type") == "agent"]
        agent_segs.sort(
            key=lambda s: (
                s.get("stats", {}).get("matchesPlayed", {}).get("value", 0),
                s.get("stats", {}).get("timePlayed", {}).get("value", 0),
            ),
            reverse=True,
        )

    top_agents = []
    primary_agent_key = ""
    primary_agent_name = ""
    for agent in agent_segs[:5]:
        meta = agent.get("metadata", {})
        attrs = agent.get("attributes", {})
        agent_key = attrs.get("key") or attrs.get("agentId") or ""
        name = (
            meta.get("agentName")
            or meta.get("name")
            or attrs.get("agentName")
            or attrs.get("agentId")
            or "Unknown"
        )
        if not primary_agent_key:
            primary_agent_key = str(agent_key)
            primary_agent_name = str(name).strip().lower()
        a_stats = agent.get("stats", {})
        a_kd = ""
        for kd_key in ("kDRatio", "kdRatio", "kd", "killDeathRatio"):
            if kd_key in a_stats:
                a_kd = a_stats[kd_key].get("displayValue", "")
                break
        top_agents.append({
            "name": name,
            "wins": a_stats.get("matchesWon", {}).get("displayValue", ""),
            "played": a_stats.get("matchesPlayed", {}).get("displayValue", ""),
            "kd": a_kd,
        })


    return {
        "riot_id": riot_id,
        "riot_tag": riot_tag,
        "in_game_name": riot_id,
        "avatar_url": avatar_url,
        "region": region,
        "current_rank": current_rank,
        "current_rank_icon": current_rank_icon,
        "peak_rank": peak_rank,
        "peak_rank_icon": peak_rank_icon,
        "peak_act": peak_act,
        "kd_ratio": kd_ratio,
        "wins": wins,
        "matches_played": matches_played,
        "damage_per_round": damage_per_round,
        "headshot_pct": headshot_pct,
        "top_agents": top_agents,
    }
