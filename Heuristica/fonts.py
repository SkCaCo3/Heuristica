"""
fonts.py
The only module that touches pygame.font. Loads JetBrains Mono (headers /
code-style text) and IBM Plex Sans (body / UI text) from assets/fonts/ if
present, falling back to a system monospace/sans-serif font otherwise so
the app still runs cleanly without the bundled .ttf files.
"""

import os
import pygame
import config

_cache = {}


def _load(path, fallback_name, size, bold):
    key = (path, fallback_name, size, bold)
    if key in _cache:
        return _cache[key]
    font = None
    if os.path.isfile(path):
        try:
            font = pygame.font.Font(path, size)
        except Exception:
            font = None
    if font is None:
        font = pygame.font.SysFont(fallback_name, size, bold=bold)
    _cache[key] = font
    return font


def mono(size, bold=False):
    path = config.MONO_BOLD if bold else config.MONO_REGULAR
    return _load(path, "couriernew,monospace", size, bold)


def sans(size, bold=False):
    path = config.SANS_BOLD if bold else config.SANS_REGULAR
    return _load(path, "arial,sans-serif", size, bold)
