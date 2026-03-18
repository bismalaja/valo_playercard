"""
Valorant Tracker - Parse profile data from API response
"""

from curl_cffi import requests
import json

RIOT_ID = "welly#wells"
encoded = RIOT_ID.replace("#", "%23")
URL = f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{encoded}"

BROWSER_COOKIES = (
    "cf_clearance=O.vXJvYTwYWxL0uflGbOGjY_p4vJzMG_Ao_SBorNhYg-1773188285-1.2.1.1-kdsqr2PZVIpA5r6ETq5uqOeX93bRVQpGpGRTwEwD1GErIV6kwH9t255k59.4jq_3Gg2pWnfsiUN1XgXfKT4x.LVwMbZbwOEz2rQbdWLzCOB8Ayxxhgi6XbW92HBi7TfZXCfLrqr1Re_nrJrFzogZZ.BqIVj29gnumocOZSWIKfAZlPhfaKtKR9FzS7h7aBijyZPorVA4OliGnZI.zZyKvIrfakzU9qy3lL.8KlfuHNY; "
    "__cflb=02DiuFQAkRrzD1P1mdkJhqGg79NVrGL35F2WNgk4TYP6t; "
    "__cf_bm=fWEUWzyA334MV92K9XoCxGyfvjjEa433_1OSwPZkPaE-1773188284-1.0.1.1-pk5Ps8m3KKl11KyYUIy4D4APyw7aoB_NJ40I87XbOBSx9l8HSZod4ONgt4XgXz0XxrYKdrJnZCLJabCY6buiFfYe6354rXEvQkaMyZLgAop3dNNXz4kGi6YSrOfssMPA"
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://tracker.gg",
    "Referer": "https://tracker.gg/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Cookie": BROWSER_COOKIES,
}

# Only valid values from curl_cffi 0.14.0
IMPERSONATE_OPTIONS = ["firefox135", "firefox133", "firefox144", "chrome124", "chrome131"]

response = None
used_impersonate = None
for impersonate in IMPERSONATE_OPTIONS:
    try:
        print(f"Trying impersonate={impersonate}...")
        response = requests.get(URL, headers=headers, impersonate=impersonate)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            used_impersonate = impersonate
            print(f"  ✓ Success with {impersonate}!")
            break
        else:
            print(f"  ✗ Got {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

if not response or response.status_code != 200:
    print("\nAll options failed.")
    print(response.text[:300] if response else "No response")
    exit()

data = response.json()

with open("api_response.json", "w") as f:
    json.dump(data, f, indent=2)
print(f"\nSaved to api_response.json! (used {used_impersonate})\n")

segments = data["data"]["segments"]
platform = data["data"]["platformInfo"]

print(f"Player    : {platform['platformUserHandle']}")
print(f"Avatar    : {platform['avatarUrl']}")
print(f"Region    : {data['data']['metadata']['activeShard'].upper()}")
print()

def get_segment(seg_type, attributes=None):
    for seg in segments:
        if seg["type"] != seg_type:
            continue
        if attributes:
            if all(seg["attributes"].get(k) == v for k, v in attributes.items()):
                return seg
        else:
            return seg
    return None

season = get_segment("season", {"playlist": "competitive", "seasonId": ""})
if not season:
    season = get_segment("season")

if season:
    stats  = season["stats"]
    rank   = stats.get("rank", {})
    peak   = stats.get("peakRank", {})
    kd     = stats.get("kdRatio", {})
    wins   = stats.get("matchesWon", {})
    played = stats.get("matchesPlayed", {})
    damage = stats.get("damagePerRound", {})
    hs     = stats.get("headshotsPercentage", {})

    print("── Current Season ───────────────��──────────")
    print(f"  Rank         : {rank.get('metadata', {}).get('tierName', 'N/A')} ({rank.get('displayValue', 'N/A')})")
    print(f"  Peak (season): {peak.get('metadata', {}).get('tierName', 'N/A')}")
    print(f"  K/D Ratio    : {kd.get('displayValue', 'N/A')}")
    print(f"  Wins         : {wins.get('displayValue', 'N/A')}")
    print(f"  Played       : {played.get('displayValue', 'N/A')}")
    print(f"  DMG/Round    : {damage.get('displayValue', 'N/A')}")
    print(f"  Headshot %   : {hs.get('displayValue', 'N/A')}")
    print()

peak_seg = get_segment("peak-rating", {"playlist": "competitive"})
if peak_seg:
    pr = peak_seg["stats"].get("peakRating", {})
    print("── All-Time Peak ───────────────────────────")
    print(f"  Peak Rank    : {pr.get('displayValue', 'N/A')}")
    print(f"  Act          : {pr.get('metadata', {}).get('actName', 'N/A')}")
    print(f"  Icon URL     : {pr.get('metadata', {}).get('iconUrl', 'N/A')}")
    print()

agent_segs = [s for s in segments if s["type"] == "agent"]
print("── Top Agents ──────────────────────────────")
for agent in agent_segs[:5]:
    name   = agent["attributes"].get("agentName", "Unknown")
    stats  = agent["stats"]
    kd     = stats.get("kdRatio", {}).get("displayValue", "N/A")
    wins   = stats.get("matchesWon", {}).get("displayValue", "N/A")
    played = stats.get("matchesPlayed", {}).get("displayValue", "N/A")
    print(f"  {name:<15} KD: {kd:<6} Wins: {wins:<5} Played: {played}")