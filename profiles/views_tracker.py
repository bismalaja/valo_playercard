import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.tracker_api import fetch_tracker_profile, parse_tracker_url


@require_POST
def fetch_tracker_stats(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required."}, status=401)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    riot_id = None
    riot_tag = None
    playlist = "competitive"
    season_id = ""

    if "tracker_url" in body:
        result = parse_tracker_url(body["tracker_url"])
        if result is None:
            return JsonResponse(
                {"error": "Invalid or unrecognised tracker.gg profile URL."},
                status=400,
            )
        riot_id = result["riot_id"]
        riot_tag = result["riot_tag"]
        playlist = result.get("playlist") or "competitive"
        season_id = result.get("season_id") or ""
    elif "riot_id" in body and "riot_tag" in body:
        riot_id = body["riot_id"]
        riot_tag = body["riot_tag"]
    else:
        return JsonResponse(
            {"error": "Provide either 'tracker_url' or both 'riot_id' and 'riot_tag'."},
            status=400,
        )

    try:
        data = fetch_tracker_profile(
            riot_id,
            riot_tag,
            playlist=playlist,
            season_id=season_id,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=502)
    except Exception:
        return JsonResponse(
            {"error": "An internal error occurred while fetching tracker data."},
            status=500,
        )

    request.session['tracker_autofill_profile'] = {
        'peak_rank': data.get('peak_rank') or '',
        'peak_rank_icon': data.get('peak_rank_icon') or '',
    }

    return JsonResponse({"ok": True, "data": data})
