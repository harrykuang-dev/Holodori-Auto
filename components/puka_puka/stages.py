"""Recognize the solo level menu, tutorial, and victory flow from visual landmarks."""

from functools import cache

import cv2
import numpy as np

from vision import bgr, is_ready, win_screen, yellow


# Sparse occupancy masks of the text regions on the Traditional Chinese UI.
ANCHORS = {
    "challenge": ((767, 722, 889, 753), "light", (
        0x000000, 0x00b524, 0x3c0784, 0x3cf5bc, 0x2da7b4, 0x2ca3b4, 0x3ca6be, 0x000000)),
    "level_title": ((127, 42, 268, 79), "light", (
        0x000000, 0x7dff8c, 0x7fef8c, 0x79edbe, 0x7bef9c, 0x79eb8e, 0x7def88, 0x000000)),
    "tutorial_title": ((730, 144, 896, 179), "ink", (
        0x000000, 0x5b919c, 0x39999e, 0x7dfd96, 0x399b92, 0x7bdbd2, 0x79a7d2, 0x000000)),
    "play": ((1391, 813, 1457, 846), "light", (
        0x000000, 0x036778, 0x1e6200, 0x1ba7f8, 0x0fa250, 0x0d46d0, 0x13e098, 0x000000)),
    "team_title": ((125, 31, 268, 67), "light", (
        0x000000, 0x086400, 0x7d7fac, 0x7d7fac, 0x7dfdae, 0x7dfdaa, 0x1c711e, 0x000000)),
    "team_auto": ((1257, 42, 1456, 75), "blue", (
        0x000000, 0x724440, 0x737fc0, 0x237fc0, 0x737fc0, 0x537fc0, 0x000000, 0x000000)),
}

CLICK = {
    "hub": (1412, 830),
    "challenge": (812, 737),
    "challenge_left": (298, 737),
    "challenge_right": (1326, 737),
    "level_next": (1569, 457),
    "team_auto": (1345, 56),
    "team_start": (1405, 824),
    "tutorial": (1324, 132),
    "win": (1368, 828),
    "win_details": (1368, 828),
    "reward": (812, 807),
}
CHALLENGES = ("challenge_left", "challenge", "challenge_right")


@cache
def bits(rows):
    return np.array([[(row >> i) & 1 == 1 for i in range(23, -1, -1)] for row in rows])


def anchor(frame, name, dx=0):
    (left, top, right, bottom), style, signature = ANCHORS[name]
    expected = bits(signature)
    for dy in (0, -2, 2):
        b, g, r = bgr(frame[top+dy:bottom+dy, left+dx:right+dx])
        if style == 'light':
            mask = (r > 215) & (g > 222) & (b > 222)
        elif style == 'blue':
            mask = (b > 140) & (g > 114) & (r < 150) & (b-r > 50)
        else:
            mask = (r < 152) & (g < 150) & (b < 185)
        sampled = cv2.resize(mask.astype(np.float32), (24, 8), interpolation=cv2.INTER_AREA) > .36
        if (sampled & expected).sum() / (sampled | expected).sum() >= .61:
            return True
    return False


def blue_button(area, fraction=.42):
    b, g, r = bgr(area)
    return ((b > 179) & (g > 122) & (r < 113) & (g - r > 68)).mean() > fraction


def white(area, fraction=.85):
    return (area.min(axis=2) > 211).mean() > fraction


def tutorial(frame):
    return (white(frame[113:199, 359:716]) and white(frame[664:718, 1072:1246])
            and blue_button(frame[115:148, 1305:1342], .23) and anchor(frame, "tutorial_title"))


def open_stage(frame):
    available = []
    for index, action in enumerate(CHALLENGES):
        x, _ = CLICK[action]
        if (blue_button(frame[721:755, x-105:x+104]) and anchor(frame, 'challenge', x-812)
                and yellow(frame[137:172, x-82:x+84]).mean() <= .15):
            b, g, r = bgr(frame[182:211, x-80:x+80])
            normal = ((g > 145) & (g-r > 45) & (g-b > 25)).mean() > .32
            available.append((not normal, index, action))
    return min(available)[2] if available else None


def has_next_page(frame):
    # The arrow is painted white at the edge. Only use it from a cleared card.
    badge = yellow(frame[137:172, 730:896]).mean() > .15
    arrow = white(frame[441:473, 1562:1576], .51)
    return badge and arrow


def classify_screen(frame):
    if is_ready(frame):
        return "board"
    if tutorial(frame):
        return "tutorial"
    if (anchor(frame, 'team_title') and anchor(frame, 'team_auto')
            and all(white(frame[y:y+23, 1270:1480], .76) for y in (260, 402, 550))):
        b, g, r = bgr(frame[807:837, 1320:1490])
        enabled = ((b > 190) & (g > 168) & (r < 115) & (g - r > 74)).mean() > .40
        return 'team_start' if enabled else 'team_auto'
    details = white(frame[275:650, 788:1497])
    result_button = blue_button(frame[801:861, 1234:1512])
    if result_button and win_screen(frame):
        return "win_details" if details else "win"
    if details and result_button:
        return "non_win"
    b, g, r = bgr(frame[320:371, 120:1488])
    reward_band = ((b > 186) & (g > 174) & (r < 162) & (g - r > 61)).mean() > .9
    if reward_band and white(frame[92:133, 732:895], .30) and white(frame[793:826, 749:874], .15):
        return "reward"
    if anchor(frame, "level_title"):
        stage = open_stage(frame)
        return stage or ('level_next' if has_next_page(frame) else 'level_menu')
    if (blue_button(frame[803:860, 1270:1540]) and anchor(frame, "play")
            and yellow(frame[170:234, 107:349]).mean() > .055):
        return "hub"
    return None
