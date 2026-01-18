# objects/projectiles.py
import pygame
from dataclasses import dataclass

Vec2 = pygame.Vector2


@dataclass
class Bullet:
    pos: Vec2
    vel: Vec2
    dmg: int
    alive: bool = True
