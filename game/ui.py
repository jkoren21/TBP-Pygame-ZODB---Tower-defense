# game/ui.py
import pygame
from dataclasses import dataclass


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    enabled: bool = True

    def draw(self, screen: pygame.Surface, font, colors):
        bg = colors["btn"] if self.enabled else colors["btn_disabled"]
        border = colors["btn_border"]
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, border, self.rect, width=2, border_radius=10)
        label = font.render(self.text, True, colors["text"] if self.enabled else colors["muted"])
        screen.blit(label, (self.rect.centerx - label.get_width() // 2, self.rect.centery - label.get_height() // 2))

    def hit(self, pos) -> bool:
        return self.enabled and self.rect.collidepoint(pos)
