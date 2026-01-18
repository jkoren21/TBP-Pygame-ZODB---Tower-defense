# objects/towers.py
import pygame
from dataclasses import dataclass
from typing import Tuple

Vec2 = pygame.Vector2


@dataclass
class Tower:
    kind: str  
    gx: int
    gy: int
    range_px: float
    fire_cd: float
    dmg: int
    cooldown_left: float = 0.0

    def center_px(self, cell: int, offset: Tuple[int, int]) -> Vec2:
        ox, oy = offset
        return Vec2(ox + self.gx * cell + cell / 2, oy + self.gy * cell + cell / 2)
