"""Pillow-based card profile image compositing.

Produces a 1920×1080 RGBA image that approximates the card_profile.html layout.
Call ``build_card_image(profile, teammates)`` to get a PIL.Image ready for saving.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, ImageDraw, ImageFont

from django.conf import settings
from django.contrib.staticfiles import finders as static_finders

# ---------------------------------------------------------------------------
# Canvas geometry
# ---------------------------------------------------------------------------
CARD_W, CARD_H = 1920, 1080

# CSS grid: 1fr | 25vw (480px at 1920, capped at 350px diameter PFP) | 1fr
CENTER_COL_W = 480                              # 25vw of 1920
LEFT_END     = (CARD_W - CENTER_COL_W) // 2    # 720  — right edge of left column
RIGHT_START  = LEFT_END + CENTER_COL_W          # 1200 — left edge of right column
PANEL_PAD    = int(0.04 * CARD_W)              # 4vw ≈ 76px

PFP_DIAMETER = 350
PFP_RADIUS   = PFP_DIAMETER // 2
PFP_CX, PFP_CY = CARD_W // 2, CARD_H // 2

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
C_NAVY     = (23,  29,  59)     # #171d3b  — gradient start (top-left)
C_TAN      = (166, 121, 99)     # #a67963  — gradient end   (bottom-right)
C_DARK     = (15,  25,  35)     # #0f1923  — panel fill
C_RED      = (255, 70,  85)     # #ff4655  — accent
C_WHITE    = (236, 232, 225)    # #ece8e1  — primary text
C_GREY     = (143, 161, 193)    # #8fa1c1  — secondary text
C_BORDER   = (60,  65,  80)     # subtle panel border

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_DIR = Path(settings.BASE_DIR) / 'profiles' / 'static' / 'profiles' / 'fonts'


def _load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / filename
    try:
        return ImageFont.truetype(str(path), size)
    except (IOError, OSError):
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _load_image_from_url_or_path(url: str) -> Optional[Image.Image]:
    """Resolve *url* to a PIL Image, handling relative /static/, /media/, and
    absolute http(s) URLs.

    Resolution order:
    1. Relative ``/static/...``  → locate via Django's staticfiles finders
    2. Relative ``/media/...``   → resolve against MEDIA_ROOT
    3. Absolute ``http(s)://``   → fetch with requests
    4. Bare filesystem path      → open directly
    """
    if not url:
        return None
    try:
        if url.startswith('/static/'):
            # Strip the leading /static/ prefix and ask the staticfiles finder
            relative = url[len('/static/'):]
            local_path = static_finders.find(relative)
            if local_path:
                return Image.open(local_path).convert('RGBA')
            return None

        if url.startswith('/media/'):
            relative = url[len('/media/'):]
            local_path = Path(settings.MEDIA_ROOT) / relative
            if local_path.exists():
                return Image.open(str(local_path)).convert('RGBA')
            return None

        if url.startswith('http://') or url.startswith('https://'):
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert('RGBA')

        # Last resort: treat as a bare filesystem path
        p = Path(url)
        if p.exists():
            return Image.open(str(p)).convert('RGBA')

    except Exception:
        pass
    return None


def _fetch_url(url: str) -> Optional[Image.Image]:
    """Thin wrapper kept for backward compatibility."""
    return _load_image_from_url_or_path(url)


def _open_field_image(field) -> Optional[Image.Image]:
    """Open a Django ImageField — local path first, then URL fallback."""
    if not field:
        return None
    try:
        return Image.open(field.path).convert('RGBA')
    except (ValueError, AttributeError, FileNotFoundError, NotImplementedError):
        try:
            return _load_image_from_url_or_path(field.url)
        except Exception:
            return None


def _get_icon(obj) -> Optional[Image.Image]:
    """Return icon image for a Role / Agent / Map / Team model instance.

    Uses the model's own ``get_icon_url()`` method so the resolution logic
    (uploaded file first, then icon_url fallback) stays in one place.
    """
    url = obj.get_icon_url()
    if url:
        img = _load_image_from_url_or_path(url)
        if img:
            return img
    # Secondary fallback: try the raw ImageField path if icon_url resolved to nothing
    if obj.icon:
        return _open_field_image(obj.icon)
    return None


def _circle_crop(img: Image.Image, diameter: int) -> Image.Image:
    """Resize and circle-crop img to the given diameter. Returns RGBA."""
    img = img.resize((diameter, diameter), Image.LANCZOS)
    mask = Image.new('L', (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    result = Image.new('RGBA', (diameter, diameter), (0, 0, 0, 0))
    result.paste(img.convert('RGBA'), mask=mask)
    return result


def _composite_over(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    """Alpha-composite overlay onto base at position (x, y)."""
    tmp = Image.new('RGBA', base.size, (0, 0, 0, 0))
    tmp.paste(overlay.convert('RGBA'), (x, y))
    base.alpha_composite(tmp)


def _paste_centered(base: Image.Image, overlay: Image.Image, cx: int, cy: int) -> None:
    x = cx - overlay.width // 2
    y = cy - overlay.height // 2
    _composite_over(base, overlay, x, y)


# ---------------------------------------------------------------------------
# Background gradient
# ---------------------------------------------------------------------------

def _draw_gradient(img: Image.Image) -> None:
    """Fill img with a #171d3b→#a67963 diagonal (top-left→bottom-right) gradient."""
    draw = ImageDraw.Draw(img)
    total = CARD_W + CARD_H
    for i in range(total + 2):
        t = i / total
        color = (
            round(C_NAVY[0] + (C_TAN[0] - C_NAVY[0]) * t),
            round(C_NAVY[1] + (C_TAN[1] - C_NAVY[1]) * t),
            round(C_NAVY[2] + (C_TAN[2] - C_NAVY[2]) * t),
            255,
        )
        # Anti-diagonal line strip that produces the true diagonal gradient
        x1 = min(i, CARD_W - 1)
        y1 = i - x1
        x2 = i - min(i, CARD_H - 1)
        y2 = min(i, CARD_H - 1)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=2)


# ---------------------------------------------------------------------------
# Watermark text
# ---------------------------------------------------------------------------

def _draw_watermark(img: Image.Image, text: str) -> None:
    """Draw large ghost watermark of the player name at ~5% opacity."""
    font = _load_font('Oswald-Bold.ttf', 400)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (CARD_W - tw) // 2
    ty = (CARD_H - th) // 2
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 13))  # 13/255 ≈ 5%
    img.alpha_composite(layer)


# ---------------------------------------------------------------------------
# Helper: section title row (returns height consumed)
# ---------------------------------------------------------------------------

def _draw_section_title(draw: ImageDraw.Draw, x: int, y: int, text: str,
                        font: ImageFont, right_align: bool = False) -> int:
    """Draw a red uppercase section title + underline. Returns total height used.

    Uses bbox[3] (full extent from anchor to bottom) so callers advance y
    past the real bottom of the glyphs, never clipping into them.
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    text_bottom = bbox[3]       # full distance from anchor to bottom of glyphs
    tx = (x - tw) if right_align else x
    draw.text((tx, y), text, font=font, fill=C_RED)
    underline_y = y + text_bottom + 6
    ux = (x - tw) if right_align else x
    draw.line([(ux, underline_y), (ux + tw, underline_y)], fill=(*C_RED, 140), width=2)
    return text_bottom + 6 + 2 + 10  # text + gap-to-underline + underline + bottom margin


# ---------------------------------------------------------------------------
# Left panel: Agents & Favourite Maps
# ---------------------------------------------------------------------------

def _section_title_height(draw: ImageDraw.Draw, text: str, font: ImageFont) -> int:
    """Pre-measure the height that _draw_section_title will consume."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] + 6 + 2 + 10


def _draw_left_panel(base: Image.Image, profile) -> None:
    draw = ImageDraw.Draw(base)
    font_title = _load_font('Oswald-Regular.ttf', 24)
    font_map   = _load_font('Oswald-Regular.ttf', 24)

    ICON_SIZE  = 65
    ICON_GAP   = 14
    ROW_GAP    = 16          # extra vertical gap between icon rows
    RIGHT_EDGE = LEFT_END - PANEL_PAD   # content right-aligns to here
    MAX_W      = RIGHT_EDGE             # maximum content width

    agents_list = list(profile.agents.all())
    maps_list   = list(profile.maps.all())

    MAP_IMG_W, MAP_IMG_H = 108, 58
    MAP_CARD_PAD = 10       # vertical padding inside each map card
    MAP_CARD_H   = MAP_IMG_H + MAP_CARD_PAD * 2
    MAP_ROW_GAP  = 12       # gap between consecutive map rows
    GAP = int(0.05 * CARD_H)   # gap between sections (~54px)

    # ---- Pre-calculate total height of all sections ----
    icons_per_row = max(1, (MAX_W + ICON_GAP) // (ICON_SIZE + ICON_GAP))
    agent_rows = math.ceil(len(agents_list) / icons_per_row) if agents_list else 0

    total_h = 0
    if agents_list:
        title_h = _section_title_height(draw, 'AGENTS', font_title)
        total_h += title_h + agent_rows * ICON_SIZE + (agent_rows - 1) * (ICON_GAP + ROW_GAP)

    if maps_list:
        if total_h > 0:
            total_h += GAP
        title_h = _section_title_height(draw, 'FAVORITE MAPS', font_title)
        total_h += title_h + len(maps_list) * MAP_CARD_H + (len(maps_list) - 1) * MAP_ROW_GAP

    y = (CARD_H - total_h) // 2

    # ---- Draw Agents ----
    if agents_list:
        consumed = _draw_section_title(draw, RIGHT_EDGE, y, 'AGENTS', font_title, right_align=True)
        y += consumed

        for idx in range(0, len(agents_list), icons_per_row):
            row = agents_list[idx: idx + icons_per_row]
            row_w = len(row) * ICON_SIZE + (len(row) - 1) * ICON_GAP
            rx = RIGHT_EDGE - row_w
            for agent in row:
                draw.rectangle([rx, y, rx + ICON_SIZE - 1, y + ICON_SIZE - 1],
                                fill=C_DARK, outline=C_BORDER)
                icon_img = _get_icon(agent)
                if icon_img:
                    sz = int(ICON_SIZE * 0.8)
                    icon_img = icon_img.resize((sz, sz), Image.LANCZOS)
                    px = rx + (ICON_SIZE - sz) // 2
                    py = y  + (ICON_SIZE - sz) // 2
                    _composite_over(base, icon_img, px, py)
                rx += ICON_SIZE + ICON_GAP
            y += ICON_SIZE + ICON_GAP + ROW_GAP

        y -= (ICON_GAP + ROW_GAP)   # remove trailing gap after last icon row
        if maps_list:
            y += GAP

    # ---- Draw Maps ----
    if maps_list:
        consumed = _draw_section_title(draw, RIGHT_EDGE, y, 'FAVORITE MAPS', font_title, right_align=True)
        y += consumed

        card_w = MAP_IMG_W + 150   # image + text area
        for map_obj in maps_list:
            card_x  = RIGHT_EDGE - card_w - 5
            card_y1 = y
            card_y2 = y + MAP_CARD_H
            draw.rectangle([card_x, card_y1, RIGHT_EDGE, card_y2],
                            fill=C_DARK, outline=C_BORDER)
            map_img = _get_icon(map_obj)
            if map_img:
                map_img = map_img.resize((MAP_IMG_W, MAP_IMG_H), Image.LANCZOS).convert('RGBA')
                _composite_over(base, map_img, card_x + 5, y + MAP_CARD_PAD)
            name_text = map_obj.name.upper()
            nbbox = draw.textbbox((0, 0), name_text, font=font_map)
            name_h = nbbox[3] - nbbox[1]
            name_y = y + MAP_CARD_PAD + (MAP_IMG_H - name_h) // 2
            draw.text((card_x + MAP_IMG_W + 15, name_y), name_text, font=font_map, fill=C_WHITE)
            y += MAP_CARD_H + MAP_ROW_GAP


# ---------------------------------------------------------------------------
# Centre: Profile picture
# ---------------------------------------------------------------------------

def _draw_pfp(base: Image.Image, profile) -> None:
    draw = ImageDraw.Draw(base)

    # Outer glow ring
    glow = PFP_RADIUS + 12
    draw.ellipse([PFP_CX - glow, PFP_CY - glow, PFP_CX + glow, PFP_CY + glow],
                 outline=(255, 255, 255, 50), width=3)

    pfp_img = None
    if profile.profile_picture:
        pfp_img = _open_field_image(profile.profile_picture)
    if pfp_img is None and profile.profile_picture_url:
        pfp_img = _fetch_url(profile.profile_picture_url)

    if pfp_img:
        cropped = _circle_crop(pfp_img, PFP_DIAMETER)

        # Glitch layer B: red-shifted, nudged right, 30% opacity
        r, g, b_ch, a = cropped.split()
        b_layer = Image.merge('RGBA', (r, g, b_ch, a.point(lambda v: int(v * 0.30))))
        _paste_centered(base, b_layer, PFP_CX + 3, PFP_CY)

        # Glitch layer S: cyan-shifted, nudged left, 40% opacity
        s_layer = Image.merge('RGBA', (b_ch, g, r, a.point(lambda v: int(v * 0.40))))
        _paste_centered(base, s_layer, PFP_CX - 3, PFP_CY)

        # Main layer
        _paste_centered(base, cropped, PFP_CX, PFP_CY)
    else:
        # Placeholder circle with "?"
        draw.ellipse([PFP_CX - PFP_RADIUS, PFP_CY - PFP_RADIUS,
                      PFP_CX + PFP_RADIUS, PFP_CY + PFP_RADIUS],
                     fill=C_DARK, outline=(180, 180, 180, 120), width=4)
        q_font = _load_font('Oswald-Bold.ttf', 160)
        bbox = draw.textbbox((0, 0), '?', font=q_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((PFP_CX - tw // 2, PFP_CY - th // 2), '?', font=q_font, fill=C_WHITE)


# ---------------------------------------------------------------------------
# Right panel: Player identity, roles, teammates
# ---------------------------------------------------------------------------

def _draw_right_panel(base: Image.Image, profile, teammates) -> None:
    draw = ImageDraw.Draw(base)

    font_team     = _load_font('Arimo-Bold.ttf',    26)
    font_name     = _load_font('Oswald-Bold.ttf',   90)
    font_tag      = _load_font('Oswald-Regular.ttf', 26)
    font_section  = _load_font('Oswald-Regular.ttf', 24)
    font_teammate = _load_font('Oswald-Regular.ttf', 22)

    ICON_SIZE  = 65
    ICON_GAP   = 14
    THUMB_D    = 60
    THUMB_PAD  = 10          # vertical padding inside each teammate row
    TM_ROW_H   = THUMB_D + THUMB_PAD * 2
    TM_ROW_GAP = 10          # gap between consecutive teammate rows
    LEFT_EDGE  = RIGHT_START + PANEL_PAD
    GAP        = int(0.05 * CARD_H)   # gap between sections (~54px)

    roles_list = list(profile.roles.all())
    tm_list    = list(teammates) if teammates else []

    # ---- Pre-measure heights using bbox[3] for accurate full-extent ----
    team_text = profile.team.name.upper() if profile.team else 'FREE AGENT'
    b_team = draw.textbbox((0, 0), team_text,                    font=font_team)
    b_name = draw.textbbox((0, 0), profile.in_game_name.upper(), font=font_name)
    b_tag  = draw.textbbox((0, 0), profile.riot_tag or '',        font=font_tag)

    # Use bbox[3] (full anchor→bottom extent) as the y-advancement amount so
    # the next element always starts below the actual bottom pixel of glyphs.
    identity_h = b_team[3] + 14 + b_name[3] + 14
    if profile.riot_tag:
        identity_h += b_tag[3] + 10

    total_h = identity_h
    if roles_list:
        total_h += GAP + _section_title_height(draw, 'ROLES', font_section) + ICON_SIZE + 4
    if tm_list:
        total_h += (GAP
                    + _section_title_height(draw, 'TEAMMATES', font_section)
                    + len(tm_list) * TM_ROW_H
                    + (len(tm_list) - 1) * TM_ROW_GAP)

    y = (CARD_H - total_h) // 2

    # ---- Team / player identity ----
    draw.text((LEFT_EDGE, y), team_text, font=font_team, fill=C_RED)
    y += b_team[3] + 14

    draw.text((LEFT_EDGE, y), profile.in_game_name.upper(), font=font_name, fill=C_WHITE)
    y += b_name[3] + 14

    if profile.riot_tag:
        draw.text((LEFT_EDGE, y), profile.riot_tag, font=font_tag, fill=C_GREY)
        y += b_tag[3] + 10

    # ---- Roles ----
    if roles_list:
        y += GAP
        consumed = _draw_section_title(draw, LEFT_EDGE, y, 'ROLES', font_section)
        y += consumed
        rx = LEFT_EDGE
        for role in roles_list:
            draw.rectangle([rx, y, rx + ICON_SIZE - 1, y + ICON_SIZE - 1],
                            fill=C_DARK, outline=C_BORDER)
            icon_img = _get_icon(role)
            if icon_img:
                sz = int(ICON_SIZE * 0.8)
                icon_img = icon_img.resize((sz, sz), Image.LANCZOS)
                px = rx + (ICON_SIZE - sz) // 2
                py = y  + (ICON_SIZE - sz) // 2
                _composite_over(base, icon_img, px, py)
            rx += ICON_SIZE + ICON_GAP
        y += ICON_SIZE + 4

    # ---- Teammates ----
    if tm_list:
        y += GAP
        consumed = _draw_section_title(draw, LEFT_EDGE, y, 'TEAMMATES', font_section)
        y += consumed
        for tm in tm_list:
            card_right = LEFT_EDGE + THUMB_D + 20 + 240
            draw.rectangle([LEFT_EDGE - 5, y, card_right, y + TM_ROW_H],
                            fill=C_DARK, outline=C_BORDER)

            tm_img = _open_field_image(tm.profile_picture) if tm.profile_picture else None
            if tm_img is None and getattr(tm, 'profile_picture_url', None):
                tm_img = _load_image_from_url_or_path(tm.profile_picture_url)

            circle_y = y + THUMB_PAD
            if tm_img:
                circ = _circle_crop(tm_img, THUMB_D)
                _composite_over(base, circ, LEFT_EDGE, circle_y)
            else:
                draw.ellipse([LEFT_EDGE, circle_y, LEFT_EDGE + THUMB_D, circle_y + THUMB_D],
                              fill=(45, 45, 55), outline=C_BORDER)

            name_bbox = draw.textbbox((0, 0), tm.in_game_name.upper(), font=font_teammate)
            name_h = name_bbox[3] - name_bbox[1]
            name_y = circle_y + (THUMB_D - name_h) // 2
            draw.text((LEFT_EDGE + THUMB_D + 20, name_y),
                      tm.in_game_name.upper(), font=font_teammate, fill=C_WHITE)
            y += TM_ROW_H + TM_ROW_GAP


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_card_image(profile, teammates) -> Image.Image:
    """Composite a 1920×1080 card image for the given profile.

    Args:
        profile:    profiles.models.Profile instance.
        teammates:  QuerySet or list of teammate Profile instances, or None.

    Returns:
        PIL.Image.Image in RGBA mode.
    """
    img = Image.new('RGBA', (CARD_W, CARD_H), (*C_DARK, 255))
    _draw_gradient(img)
    _draw_watermark(img, profile.in_game_name)
    _draw_pfp(img, profile)
    _draw_left_panel(img, profile)
    _draw_right_panel(img, profile, teammates)
    return img
