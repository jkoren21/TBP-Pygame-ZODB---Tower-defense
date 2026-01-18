# objects/enemies.py
import pygame
from dataclasses import dataclass

Vec2 = pygame.Vector2


@dataclass
class Enemy:
    kind: str  
    pos: Vec2
    speed: float
    hp: int
    max_hp: int
    path_index: int = 0
    alive: bool = True

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.pos.x - 10), int(self.pos.y - 10), 20, 20)
