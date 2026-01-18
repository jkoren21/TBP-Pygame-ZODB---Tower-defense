# game/engine.py
import math
import pygame
from typing import Any, Dict, List, Optional, Tuple

from game.constants import GRID_W, GRID_H, CELL, GRID_OFFSET, COLORS
from game.ui import Button
from objects.enemies import Enemy
from objects.projectiles import Bullet
from objects.towers import Tower

Vec2 = pygame.Vector2


class CampusDefenseEngine:
    
    def __init__(self, screen: pygame.Surface, level_data: dict, mode: str = "campaign", load_state: Optional[dict] = None):
        self.screen = screen
        self.w, self.h = self.screen.get_size()

        
        self.grid_w = GRID_W
        self.grid_h = GRID_H
        self.cell = CELL
        self.grid_offset = GRID_OFFSET
        self.colors = COLORS

        self.level_id = int(level_data["id"])
        self.level_name = str(level_data.get("name", f"Level {self.level_id}"))
        self.path_grid = list(level_data["path_grid"])
        self.campaign_waves = int(level_data.get("campaign_waves", 6))

        self.mode = mode  # "campaign" or "endless"
        self.waves_cleared = 0  
        self.current_wave_number = 1  
        self.campaign_completed = False  

        
        self.grid_px_w = self.grid_w * self.cell
        self.grid_px_h = self.grid_h * self.cell

        self.panel_x = self.grid_offset[0] + self.grid_px_w + 24
        self.panel_rect = pygame.Rect(self.panel_x, 24, self.w - self.panel_x - 24, self.h - 48)

        self.font = pygame.font.Font(None, 26)
        self.font_big = pygame.font.Font(None, 40)

        
        self.path_px = [self._grid_to_px(gx, gy) for gx, gy in self.path_grid]
        self.path_cells = self._expand_path_cells(self.path_grid)

        
        self.lives = 15
        self.gold = 150
        self.score = 0
        self.kills = 0

        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []

        # Tornjevi
        self.tower_defs = {
            "basic": {
                "cost": 50, "range": 140, "cd": 0.55,
                "dmg": 20, "bullet_speed": 430
            },
            "sniper": {
                "cost": 90, "range": 300, "cd": 1.0,
                "dmg": 56, "bullet_speed": 560
            },
            "shotgun": {
                "cost": 100, "range": 120, "cd": 1.5,
                "dmg": 15, "bullet_speed": 380,
                "pellets": 12,
                "spread_deg": 30
            },
        }
        self.selected_tower = "basic"

        
        self.enemy_defs = {
            "fast": {"hp": 40, "speed": 80, "reward": 15, "score": 18},
            "tank": {"hp": 90, "speed": 70, "reward": 20, "score": 30},
        }

        # wave
        self.wave_in_progress = False
        self.spawn_timer = 0.0
        self.spawned_this_wave = 0
        self.enemies_this_wave = 0

        
        bx = self.panel_rect.x + 16
        bw = self.panel_rect.w - 32
        self.btn_start = Button(pygame.Rect(bx, 0, bw, 44), "Start Wave", True)
        self.btn_exit = Button(pygame.Rect(bx, 0, bw, 44), "Save & Exit", True)

        
        self.victory_choice_active = False
        self.btn_endless_yes = Button(pygame.Rect(0, 0, 0, 44), "Endless: YES", True)
        self.btn_endless_no = Button(pygame.Rect(0, 0, 0, 44), "Endless: NO", True)

        self.msg = "1=BASIC, 2=SNIPER, 3=SHOTGUN. Gradi između waveova."

        self.running = True
        self.lost = False

        
        self.exit_reason: str = "running"
        self.saved_checkpoint: Optional[Dict[str, Any]] = None
        
        self._wave_start_checkpoint: Optional[Dict[str, Any]] = None

        if load_state is not None:
            self._load_from_checkpoint(load_state)
        else:
            
            self._wave_start_checkpoint = self._make_checkpoint()

    def _make_checkpoint(self) -> Dict[str, Any]:
        """Return a serializable snapshot for continuing later (build phase)."""
        towers = []
        for t in self.towers:
            towers.append({
                "kind": str(t.kind),
                "gx": int(t.gx),
                "gy": int(t.gy),
                "cooldown_left": float(getattr(t, "cooldown_left", 0.0)),
            })

        return {
            "version": 1,
            "level_id": int(self.level_id),
            "mode": str(self.mode),
            "lives": int(self.lives),
            "gold": int(self.gold),
            "score": float(self.score),
            "kills": int(self.kills),
            "waves_cleared": int(self.waves_cleared),
            "current_wave_number": int(self.current_wave_number),
            "selected_tower": str(self.selected_tower),
            "towers": towers,
        }

    def _load_from_checkpoint(self, state: dict):
        """Restore a saved checkpoint. Always resumes in build phase."""
        self.mode = str(state.get("mode", self.mode))
        self.lives = int(state.get("lives", self.lives))
        self.gold = int(state.get("gold", self.gold))
        self.score = float(state.get("score", self.score))
        self.kills = int(state.get("kills", self.kills))
        self.waves_cleared = int(state.get("waves_cleared", self.waves_cleared))
        self.current_wave_number = int(state.get("current_wave_number", self.current_wave_number))
        self.selected_tower = str(state.get("selected_tower", self.selected_tower))

        
        self.wave_in_progress = False
        self.spawn_timer = 0.0
        self.spawned_this_wave = 0
        self.enemies_this_wave = 0
        self.enemies = []
        self.bullets = []
        self.lost = False
        self.campaign_completed = False
        self.victory_choice_active = False

        
        self.towers = []
        for td in list(state.get("towers", [])):
            kind = str(td.get("kind", "basic"))
            gx = int(td.get("gx", 0))
            gy = int(td.get("gy", 0))
            defs = self.tower_defs.get(kind, self.tower_defs["basic"])
            t = Tower(kind, gx, gy, defs["range"], defs["cd"], defs["dmg"])
            t.cooldown_left = float(td.get("cooldown_left", 0.0))
            self.towers.append(t)

        self.msg = f"Loaded save: Wave {self.current_wave_number}. Build and press Start Wave."
        self._wave_start_checkpoint = self._make_checkpoint()

    

    def _grid_to_px(self, gx: int, gy: int) -> Vec2:
        ox, oy = self.grid_offset
        return Vec2(ox + gx * self.cell + self.cell / 2, oy + gy * self.cell + self.cell / 2)

    def _mouse_to_grid(self, mx: int, my: int) -> Optional[Tuple[int, int]]:
        ox, oy = self.grid_offset
        if mx < ox or my < oy or mx >= ox + self.grid_px_w or my >= oy + self.grid_px_h:
            return None
        gx = int((mx - ox) // self.cell)
        gy = int((my - oy) // self.cell)
        if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
            return gx, gy
        return None

    def _cell_rect(self, gx: int, gy: int) -> pygame.Rect:
        ox, oy = self.grid_offset
        return pygame.Rect(ox + gx * self.cell, oy + gy * self.cell, self.cell, self.cell)

    def _expand_path_cells(self, pts: List[Tuple[int, int]]) -> set:
        cells = set()
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            if x1 == x2:
                step = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step, step):
                    cells.add((x1, y))
            elif y1 == y2:
                step = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step, step):
                    cells.add((x, y1))
            else:
                cells.add((x1, y1))
                cells.add((x2, y2))
        return cells

    

    def handle_event(self, e: pygame.event.Event):
        if e.type == pygame.QUIT:
            self.exit_reason = "quit"
            self.running = False
            return

        
        if self.victory_choice_active:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.btn_endless_yes.hit(e.pos):
                    self._switch_to_endless()
                    self.victory_choice_active = False
                    return
                if self.btn_endless_no.hit(e.pos):
                    self.exit_reason = "end"
                    self.running = False
                    return
            return

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_1:
                self.selected_tower = "basic"
                self.msg = "Selected: BASIC"
            elif e.key == pygame.K_2:
                self.selected_tower = "sniper"
                self.msg = "Selected: SNIPER"
            elif e.key == pygame.K_3:
                self.selected_tower = "shotgun"
                self.msg = "Selected: SHOTGUN"

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = e.pos

            if self.btn_start.hit((mx, my)):
                if (not self.wave_in_progress) and (not self.lost):
                    self._start_wave()
                return

            if self.btn_exit.hit((mx, my)):
                self._save_and_exit()
                return

            
            if self.wave_in_progress or self.lost:
                return

            g = self._mouse_to_grid(mx, my)
            if g:
                self._try_build(*g)

    

    def _switch_to_endless(self):
        self.mode = "endless"
        self.msg = "Endless mode! Good luck."

    def _save_and_exit(self):
        
        if self.lost:
            self.exit_reason = "end"
            self.saved_checkpoint = None
            self.running = False
            return

        self.exit_reason = "save"
        if self.wave_in_progress and self._wave_start_checkpoint is not None:
            self.saved_checkpoint = self._wave_start_checkpoint
        else:
            self.saved_checkpoint = self._make_checkpoint()
        self.running = False

    

    def _start_wave(self):
        
        self._wave_start_checkpoint = self._make_checkpoint()
        self.wave_in_progress = True
        self.spawn_timer = 0.0
        self.spawned_this_wave = 0

        
        self.enemies_this_wave = 6 + self.current_wave_number * 2

        self.msg = f"Wave {self.current_wave_number} started!"

    def _spawn_enemy(self):
        kind = "tank" if (self.spawned_this_wave % 5 == 2) else "fast"
        base = self.enemy_defs[kind]

        
        hp = int(base["hp"] * (1.0 + 0.18 * (self.current_wave_number - 1)))
        if kind == "tank":
            hp = int(hp * 1.15)

        speed = float(base["speed"] + (self.current_wave_number - 1) * (2 if kind == "fast" else 1))

        self.enemies.append(Enemy(kind, self.path_px[0].copy(), speed, hp, hp))

    

    def _try_build(self, gx: int, gy: int):
        if (gx, gy) in self.path_cells:
            self.msg = "Ne možeš graditi na putanji."
            return
        if any(t.gx == gx and t.gy == gy for t in self.towers):
            self.msg = "Tu već postoji kula."
            return

        td = self.tower_defs[self.selected_tower]
        if self.gold < td["cost"]:
            self.msg = "Nemaš dovoljno golda."
            return

        self.gold -= td["cost"]
        self.towers.append(Tower(self.selected_tower, gx, gy, td["range"], td["cd"], td["dmg"]))
        self.msg = f"Postavljena {self.selected_tower.upper()}."

    # ----- update -----

    def update(self, dt: float):
        if self.lost:
            return

        # spawn
        if self.wave_in_progress:
            self.spawn_timer -= dt
            spawn_interval = max(0.25, 0.85 - self.current_wave_number * 0.06)

            if self.spawned_this_wave < self.enemies_this_wave and self.spawn_timer <= 0:
                self.spawn_timer = spawn_interval
                self._spawn_enemy()
                self.spawned_this_wave += 1

            
            if self.spawned_this_wave >= self.enemies_this_wave and not any(e.alive for e in self.enemies):
                self.wave_in_progress = False

                
                bonus = 25 + self.current_wave_number * 8
                if self.mode == "endless":
                    bonus += self.waves_cleared * 1  # tiny ramp
                self.gold += bonus

                self.msg = f"Wave cleared! +{bonus} gold. Build now."

                self.waves_cleared += 1
                self.current_wave_number += 1

                
                self._wave_start_checkpoint = self._make_checkpoint()

                
                if (self.mode == "campaign") and (self.waves_cleared >= self.campaign_waves):
                    self.campaign_completed = True
                    self.victory_choice_active = True
                    return

        
        for en in self.enemies:
            if not en.alive:
                continue

            if en.path_index >= len(self.path_px) - 1:
                en.alive = False
                self.lives -= 1
                if self.lives <= 0:
                    self.lost = True
                continue

            target = self.path_px[en.path_index + 1]
            d = target - en.pos
            dist = d.length()
            if dist < 1e-6:
                en.path_index += 1
            else:
                step = en.speed * dt
                if step >= dist:
                    en.pos = target.copy()
                    en.path_index += 1
                else:
                    en.pos += d.normalize() * step

        
        for t in self.towers:
            t.cooldown_left = max(0.0, t.cooldown_left - dt)
            if t.cooldown_left > 0:
                continue

            tp = t.center_px(self.cell, self.grid_offset)

            
            if t.kind == "shotgun":
                target = self._find_target(tp, t.range_px)
                if target is None:
                    continue
                base_dir = (target.pos - tp)
                if base_dir.length_squared() == 0:
                    continue

                td = self.tower_defs["shotgun"]
                base_angle = math.atan2(base_dir.y, base_dir.x)
                pellets = int(td["pellets"])
                spread = math.radians(float(td["spread_deg"]))
                speed = float(td["bullet_speed"])

                if pellets <= 1:
                    offsets = [0.0]
                else:
                    offsets = [spread * (i / (pellets - 1) - 0.5) for i in range(pellets)]

                for off in offsets:
                    ang = base_angle + off
                    vel = Vec2(math.cos(ang), math.sin(ang)) * speed
                    self.bullets.append(Bullet(tp.copy(), vel, t.dmg))

                t.cooldown_left = t.fire_cd
                continue

            
            target = self._find_target(tp, t.range_px)
            if target is None:
                continue

            v = target.pos - tp
            if v.length_squared() == 0:
                continue

            speed = float(self.tower_defs[t.kind]["bullet_speed"])
            vel = v.normalize() * speed
            self.bullets.append(Bullet(tp.copy(), vel, t.dmg))
            t.cooldown_left = t.fire_cd

        
        for b in self.bullets:
            if not b.alive:
                continue

            b.pos += b.vel * dt
            if b.pos.x < 0 or b.pos.y < 0 or b.pos.x > self.w or b.pos.y > self.h:
                b.alive = False
                continue

            for en in self.enemies:
                if en.alive and en.rect().collidepoint(int(b.pos.x), int(b.pos.y)):
                    en.hp -= b.dmg
                    b.alive = False
                    if en.hp <= 0:
                        en.alive = False
                        self.kills += 1

                        base = self.enemy_defs[en.kind]
                        reward = int(base["reward"] + self.current_wave_number * 0.5)
                        self.gold += reward
                        self.score += int(base["score"] + self.current_wave_number * 3)
                    break

        
        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.alive]

        
        if self.wave_in_progress:
            self.score += dt * 2.0

    def _find_target(self, tower_pos: Vec2, range_px: float) -> Optional[Enemy]:
        best = None
        best_key = -1.0
        for en in self.enemies:
            if not en.alive:
                continue
            if (en.pos - tower_pos).length() <= range_px:
                key = en.path_index * 10000 + (en.pos - self.path_px[en.path_index]).length()
                if key > best_key:
                    best_key = key
                    best = en
        return best

    

    def draw(self):
        c = self.colors
        self.screen.fill(c["bg"])

        ox, oy = self.grid_offset
        pygame.draw.rect(self.screen, c["grid_bg"], (ox, oy, self.grid_px_w, self.grid_px_h), border_radius=12)

        for x in range(self.grid_w + 1):
            pygame.draw.line(self.screen, c["grid_line"], (ox + x * self.cell, oy),
                             (ox + x * self.cell, oy + self.grid_px_h))
        for y in range(self.grid_h + 1):
            pygame.draw.line(self.screen, c["grid_line"], (ox, oy + y * self.cell),
                             (ox + self.grid_px_w, oy + y * self.cell))

        for i in range(len(self.path_px) - 1):
            pygame.draw.line(self.screen, c["path"], self.path_px[i], self.path_px[i + 1], 16)
            pygame.draw.line(self.screen, c["path_edge"], self.path_px[i], self.path_px[i + 1], 2)

        
        for t in self.towers:
            center = t.center_px(self.cell, self.grid_offset)

            if t.kind == "shotgun":
                
                radius = 14
                pts = []
                for i in range(5):
                    ang = math.radians(90 + i * 72)
                    pts.append((
                        int(center.x + math.cos(ang) * radius),
                        int(center.y - math.sin(ang) * radius)
                    ))
                pygame.draw.polygon(self.screen, (160, 200, 120), pts)
                pygame.draw.polygon(self.screen, (90, 110, 80), pts, 2)

            else:
                r = self._cell_rect(t.gx, t.gy).inflate(-10, -10)
                base = (45, 55, 70) if t.kind == "basic" else (55, 50, 80)
                pygame.draw.rect(self.screen, base, r, border_radius=10)
                dot = c["accent"] if t.kind == "basic" else (200, 160, 255)
                pygame.draw.circle(self.screen, dot, (int(center.x), int(center.y)), 10)

        
        for en in self.enemies:
            col = (220, 90, 110) if en.kind == "fast" else (220, 170, 90)
            pygame.draw.rect(self.screen, col, en.rect(), border_radius=6)

            bar_w = 24
            bx = int(en.pos.x - bar_w / 2)
            by = int(en.pos.y - 18)
            pygame.draw.rect(self.screen, (60, 60, 60), (bx, by, bar_w, 4), border_radius=2)
            ratio = max(0.0, en.hp / en.max_hp)
            pygame.draw.rect(self.screen, c["good"], (bx, by, int(bar_w * ratio), 4), border_radius=2)

        
        for b in self.bullets:
            pygame.draw.circle(self.screen, (240, 240, 240), (int(b.pos.x), int(b.pos.y)), 3)

        
        pygame.draw.rect(self.screen, c["panel_bg"], self.panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, c["btn_border"], self.panel_rect, width=2, border_radius=12)
        self._draw_panel()

        
        if self.lost:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            text = "PORAZ!"
            s = self.font_big.render(text, True, c["bad"])
            self.screen.blit(s, (self.w // 2 - s.get_width() // 2, self.h // 2 - s.get_height() // 2))

        
        if self.victory_choice_active:
            self._draw_victory_choice_overlay()

    def _draw_victory_choice_overlay(self):
        c = self.colors
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(self.w // 2 - 260, self.h // 2 - 150, 520, 300)
        pygame.draw.rect(self.screen, c["panel_bg"], card, border_radius=16)
        pygame.draw.rect(self.screen, c["btn_border"], card, width=2, border_radius=16)

        title = self.font_big.render("Čestitamo!", True, c["good"])
        self.screen.blit(title, (card.centerx - title.get_width() // 2, card.y + 24))

        line1 = self.font.render("Campaign završen.", True, c["text"])
        self.screen.blit(line1, (card.centerx - line1.get_width() // 2, card.y + 82))

        line2 = self.font.render("Želiš li nastaviti u Endless modu?", True, c["text"])
        self.screen.blit(line2, (card.centerx - line2.get_width() // 2, card.y + 108))

        
        bw = card.w - 80
        self.btn_endless_yes.rect = pygame.Rect(card.x + 40, card.y + 155, bw, 44)
        self.btn_endless_no.rect = pygame.Rect(card.x + 40, card.y + 210, bw, 44)

        self.btn_endless_yes.draw(self.screen, self.font, c)
        self.btn_endless_no.draw(self.screen, self.font, c)

    def _draw_panel(self):
        c = self.colors
        x = self.panel_rect.x + 16
        y = self.panel_rect.y + 16

        title = self.font_big.render(self.level_name, True, c["text"])
        self.screen.blit(title, (x, y))
        y += 44

        if self.mode == "campaign":
            wave_line = f"Waves cleared: {self.waves_cleared}/{self.campaign_waves}" + (" (active)" if self.wave_in_progress else "")
        else:
            wave_line = f"Waves cleared: {self.waves_cleared}" + (" (active)" if self.wave_in_progress else "")

        lines = [
            f"Mode: {self.mode.upper()}",
            wave_line,
            f"Lives: {self.lives}",
            f"Gold: {self.gold}",
            f"Score: {int(self.score)}",
            f"Kills: {self.kills}",
            "",
            "Towers:",
            f"1) BASIC   cost {self.tower_defs['basic']['cost']}",
            f"2) SNIPER  cost {self.tower_defs['sniper']['cost']}",
            f"3) SHOTGUN cost {self.tower_defs['shotgun']['cost']}",
            f"Selected: {self.selected_tower.upper()}",
            "",
            "Build only between waves.",
        ]

        
        for line in lines:
            surf = self.font.render(line, True, c["muted"] if line else c["muted"])
            self.screen.blit(surf, (x, y))
            y += 22

        
        msg_area_h = 52
        msg_area_top = self.panel_rect.bottom - msg_area_h - 12

        
        btn_gap = 10
        btn_h = 44

        btn_y = y + 12
        max_btn_y = msg_area_top - (btn_h * 2 + btn_gap)
        btn_y = min(btn_y, max_btn_y)
        btn_y = max(self.panel_rect.y + 160, btn_y)

        self.btn_start.rect.y = btn_y
        self.btn_exit.rect.y = btn_y + btn_h + btn_gap

        
        self.btn_start.enabled = (not self.wave_in_progress) and (not self.lost) and (not self.victory_choice_active)
        self.btn_start.draw(self.screen, self.font, c)
        self.btn_exit.draw(self.screen, self.font, c)

        
        msg = self.msg.strip()
        max_w = self.panel_rect.w - 32

        words = msg.split()
        line1, line2 = "", ""
        for w in words:
            test = (line1 + " " + w).strip()
            if self.font.size(test)[0] <= max_w:
                line1 = test
            else:
                if not line2:
                    line2 = w
                else:
                    test2 = (line2 + " " + w).strip()
                    if self.font.size(test2)[0] <= max_w:
                        line2 = test2

        m1 = self.font.render(line1 if line1 else "", True, c["text"])
        self.screen.blit(m1, (x, msg_area_top))
        if line2:
            m2 = self.font.render(line2, True, c["text"])
            self.screen.blit(m2, (x, msg_area_top + 22))
