import os
import pygame
from config import FONT_PATH

_loaded_fonts = {}

def get_font(size: int) -> pygame.font.Font:
    """Return Friz Quadrata font at size, falling back to pygame default if missing."""
    key = (FONT_PATH, size)
    cached = _loaded_fonts.get(key)
    if cached:
        return cached
    try:
        if os.path.exists(FONT_PATH):
            font = pygame.font.Font(FONT_PATH, size)
        else:
            font = pygame.font.Font(None, size)
    except Exception:
        font = pygame.font.Font(None, size)
    _loaded_fonts[key] = font
    return font

