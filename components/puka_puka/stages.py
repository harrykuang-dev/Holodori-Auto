"""Recognize solo game screens from controls, artwork geometry, and color."""

from functools import cache

import numpy as np

from vision import bgr, is_ready


CLICK = {
    "hub": (1412, 830),
    "challenge": (812, 737),
    "challenge_left": (298, 737),
    "challenge_right": (1326, 737),
    "level_next": (1569, 457),
    "team_auto": (1345, 56),
    "team_start": (1405, 824),
    "tutorial": (1324, 132),
    "result": (1368, 828),
    "result_details": (1368, 828),
    "win_details": (1368, 828),
    "reward": (812, 807),
    "refill": (1362, 838),
}
CHALLENGES = ("challenge_left", "challenge", "challenge_right")
MENU_STATES = {"level_menu", "level_next", "hub", *CHALLENGES}
RESULT_STATES = {"result", "result_details", "win_details"}
REFILL_STATES = {"refill", "refill_panel"}


def blue_button(area, fraction=.42):
    b, g, r = bgr(area)
    return ((b > 179) & (g > 122) & (r < 113) & (g - r > 68)).mean() > fraction


def white(area, fraction=.85):
    return (area.min(axis=2) > 211).mean() > fraction


def hammer(frame):
    return white(frame[29:72, 46:106], .58)


def tutorial(frame):
    return (white(frame[120:190, 359:716]) and white(frame[675:710, 1072:1246])
            and white(frame[107:152, 1290:1358], .37)
            and blue_button(frame[115:148, 1305:1342], .27))


@cache
def reward_ring():
    y, x = np.ogrid[-35:36, -35:36]
    radius_squared = x*x + y*y
    return (radius_squared > 24*24) & (radius_squared < 31*31), radius_squared < 15*15


def cleared_card(frame, x):
    rim, middle = reward_ring()
    checks = 0
    for offset in (-126, 0, 126):
        center = x + offset
        light = frame[513:584, center-35:center+36].min(axis=2) > 225
        if light[rim].mean() > .46 and light[middle].mean() > .29:
            checks += 1
    return checks >= 2


def active_card(frame, x):
    # The bright card remains visible beside its reward icons, even with a different label.
    b, g, r = bgr(frame[247:334, x-160:x-112])
    face = ((r > 194) & (g > 226) & (b > 232)).mean() > .70
    return face and blue_button(frame[721:755, x-105:x+104])


def normal_card(frame, x):
    b, g, r = bgr(frame[189:204, x-72:x-55])
    return ((g > 145) & (g-r > 45) & (g-b > 25)).mean() > .32


def level_menu(frame):
    if not (hammer(frame) and white(frame[47:95, 1517:1597], .43)):
        return False
    cards = 0
    for action in CHALLENGES:
        x, _ = CLICK[action]
        b, g, r = bgr(frame[247:334, x-160:x-112])
        face = (b > 177) & (g > 146) & (r > 129) & (r < 240) & (b-g < 48) & (g-r < 48)
        cards += face.mean() > .72
    return cards >= 2


def open_stage(frame):
    available = []
    for index, action in enumerate(CHALLENGES):
        x, _ = CLICK[action]
        if active_card(frame, x) and not cleared_card(frame, x):
            available.append((not normal_card(frame, x), index, action))
    return min(available)[2] if available else None


def has_next_page(frame):
    arrow = white(frame[441:473, 1562:1576], .46)
    # A cleared card on the right can hide the next available stage.
    return arrow and cleared_card(frame, CLICK["challenge_right"][0])


def team_screen(frame):
    if not (white(frame[38:69, 1220:1254], .66) and white(frame[38:69, 1456:1472], .66)
            and all(white(frame[y:y+23, 1270:1480], .76) for y in (260, 402, 550))):
        return None
    b, g, r = bgr(frame[807:837, 1320:1490])
    enabled = ((b > 190) & (g > 168) & (r < 115) & (g - r > 74)).mean() > .40
    return 'team_start' if enabled else 'team_auto'


def reward_popup(frame):
    b, g, r = bgr(frame[328:380, 100:1510])
    cyan = (b > 181) & (g > 172) & (r < 156) & (g-r > 60)
    return cyan.mean() > .94


def refill_screen(frame):
    if not white(frame[143:193, 931:1045]):
        return None
    b, g, r = bgr(frame[700:757, 930:1085])
    summary = ((b > 208) & (g > 111) & (g < 173) & (r < 99)).mean() > .90
    b, g, r = bgr(frame[304:389, 1337:1400])
    flame = ((g > 138) & (g-r > 25) & (g-b > 8)).mean() > .32
    if not (summary and flame and blue_button(frame[304:379, 1028:1119], .17)):
        return None
    # At the default quantity the slider knob is at the left end of the track.
    one_item = white(frame[575:598, 1100:1124], .80)
    ready = white(frame[816:856, 992:1170], .68) and blue_button(frame[816:856, 1258:1475], .70)
    return "refill" if one_item and ready else "refill_panel"


def result_screen(frame):
    if not hammer(frame) or not blue_button(frame[805:854, 1280:1525], .60):
        return None
    if not white(frame[297:639, 793:1502], .83):
        # Both victory and defeat can initially land on the stadium splash.
        return 'result'
    b, g, r = bgr(frame[520:592, 834:1168])
    colorful = (np.maximum(np.maximum(b, g), r)-np.minimum(np.minimum(b, g), r) > 65)
    return 'win_details' if colorful.mean() > .18 else 'result_details'


def hub(frame):
    # The globe and stamina icon distinguish this control from the result button.
    b, g, r = bgr(frame[748:779, 1347:1401])
    stamina_icon = ((g > 140) & (g-r > 22) & (g-b > 12)).sum() > 100
    return (white(frame[798:829, 72:130], .19)
            and blue_button(frame[789:838, 73:126], .19)
            and stamina_icon
            and blue_button(frame[805:854, 1280:1525], .60))


def classify_screen(frame):
    refill = refill_screen(frame)
    if refill:
        return refill
    if is_ready(frame):
        return "board"
    if tutorial(frame):
        return "tutorial"
    if reward_popup(frame):
        return "reward"
    if level_menu(frame):
        stage = open_stage(frame)
        return stage or ('level_next' if has_next_page(frame) else 'level_menu')
    if hub(frame):
        return "hub"
    return team_screen(frame) or result_screen(frame)
