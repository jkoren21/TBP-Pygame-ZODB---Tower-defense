# main.py
import datetime
from typing import Optional
import pygame

from storage import open_storage, commit
from models import GameState
from game.constants import SCREEN_W, SCREEN_H, COLORS
from game.ui import Button
from game.engine import CampusDefenseEngine

from levels.level1 import get_level_1
from levels.level2 import get_level_2
from levels.level3 import get_level_3




def ensure_state(root) -> GameState:
    if "game_state" not in root:
        root["game_state"] = GameState()
        commit()
    return root["game_state"]


def draw_center_text(screen, font, text, y, color):
    s = font.render(text, True, color)
    screen.blit(s, (screen.get_width() // 2 - s.get_width() // 2, y))


def get_levels():
    return [
        get_level_1(),
        get_level_2(),
        get_level_3(),
    ]


def run_text_input(screen, title: str, initial: str = ""):
    font = pygame.font.Font(None, 30)
    font_big = pygame.font.Font(None, 48)

    w, h = screen.get_size()
    panel = pygame.Rect(w // 2 - 280, 170, 560, 260)
    box = pygame.Rect(panel.x + 30, panel.y + 130, panel.w - 60, 56)

    text = initial
    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_RETURN:
                    t = text.strip()
                    return t if t else None
                if e.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if e.unicode and len(e.unicode) == 1 and len(text) < 18:
                        text += e.unicode

        screen.fill(COLORS["bg"])
        pygame.draw.rect(screen, COLORS["panel_bg"], panel, border_radius=16)
        pygame.draw.rect(screen, COLORS["btn_border"], panel, width=2, border_radius=16)

        draw_center_text(screen, font_big, title, panel.y + 28, COLORS["text"])
        draw_center_text(screen, font, "ENTER = potvrdi, ESC = odustani", panel.y + 80, COLORS["muted"])

        pygame.draw.rect(screen, (18, 20, 26), box, border_radius=12)
        pygame.draw.rect(screen, COLORS["btn_border"], box, width=2, border_radius=12)

        t = font_big.render(text if text else " ", True, COLORS["text"])
        screen.blit(t, (box.x + 14, box.y + 10))

        pygame.display.flip()
        clock.tick(60)


def run_menu(screen, gs: GameState, username: str):
    font = pygame.font.Font(None, 30)
    font_big = pygame.font.Font(None, 52)

    profile = gs.get_or_create_profile(username)
    commit()

    w, h = screen.get_size()
    panel = pygame.Rect(w // 2 - 260, 100, 520, 460)

    bx = panel.x + 24
    bw = panel.w - 48
    btn_start = Button(pygame.Rect(bx, panel.y + 170, bw, 50), "Start Game", True)
    btn_continue = Button(pygame.Rect(bx, panel.y + 230, bw, 50), "Continue Saved Game", profile.has_saved_game())
    btn_history = Button(pygame.Rect(bx, panel.y + 290, bw, 50), "Game History (ZODB)", True)
    btn_change = Button(pygame.Rect(bx, panel.y + 350, bw, 50), "Change User", True)
    btn_quit = Button(pygame.Rect(bx, panel.y + 410, bw, 50), "Quit", True)

    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit", username
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_start.hit(e.pos):
                    return "level_select", username
                if btn_continue.enabled and btn_continue.hit(e.pos):
                    return "continue", username
                if btn_history.hit(e.pos):
                    return "history", username
                if btn_change.hit(e.pos):
                    newu = run_text_input(screen, "Enter username", initial=username)
                    if newu:
                        username = newu
                        profile = gs.get_or_create_profile(username)
                        commit()
                if btn_quit.hit(e.pos):
                    return "quit", username

        screen.fill(COLORS["bg"])
        pygame.draw.rect(screen, COLORS["panel_bg"], panel, border_radius=16)
        pygame.draw.rect(screen, COLORS["btn_border"], panel, width=2, border_radius=16)

        draw_center_text(screen, font_big, "Geometry defense", panel.y + 22, COLORS["text"])
        draw_center_text(screen, font, "Save yourself from boxes", panel.y + 72, COLORS["muted"])

        draw_center_text(screen, font, f"User: {profile.username}", panel.y + 115, COLORS["text"])
        stats_line = f"Games: {profile.stats['games_played']}   Wins: {profile.stats['wins']}   Total kills: {profile.stats['total_kills']}"
        draw_center_text(screen, font, stats_line, panel.y + 145, COLORS["muted"])

        btn_start.draw(screen, font, COLORS)
        btn_continue.enabled = profile.has_saved_game()
        btn_continue.draw(screen, font, COLORS)
        btn_history.draw(screen, font, COLORS)
        btn_change.draw(screen, font, COLORS)
        btn_quit.draw(screen, font, COLORS)

        pygame.display.flip()
        clock.tick(60)


def run_history(screen, profile):
    font = pygame.font.Font(None, 28)
    font_big = pygame.font.Font(None, 44)

    w, h = screen.get_size()
    panel = pygame.Rect(70, 70, w - 140, h - 140)
    btn_back = Button(pygame.Rect(panel.right - 180, panel.y + 16, 160, 44), "Back", True)

    scroll = 0
    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.hit(e.pos):
                    return "back"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "back"
                if e.key == pygame.K_DOWN:
                    scroll += 1
                if e.key == pygame.K_UP:
                    scroll = max(0, scroll - 1)

        screen.fill(COLORS["bg"])
        pygame.draw.rect(screen, COLORS["panel_bg"], panel, border_radius=16)
        pygame.draw.rect(screen, COLORS["btn_border"], panel, width=2, border_radius=16)

        title = font_big.render("Game History (ZODB)", True, COLORS["text"])
        screen.blit(title, (panel.x + 20, panel.y + 18))
        btn_back.draw(screen, font, COLORS)

        bs = profile.best_score_by_level
        best_line = "Best score by level: " + ", ".join([f"L{lvl}:{bs[lvl]}" for lvl in bs.keys()]) if len(bs) else "Best score by level: (nema još)"
        screen.blit(font.render(best_line, True, COLORS["muted"]), (panel.x + 20, panel.y + 72))

        hint = "UP/DOWN scroll, ESC back"
        screen.blit(font.render(hint, True, COLORS["muted"]), (panel.x + 20, panel.y + 98))

        runs = list(profile.runs)[::-1]
        start_y = panel.y + 130
        line_h = 28
        max_lines = (panel.height - 160) // line_h

        start_idx = scroll
        end_idx = min(len(runs), start_idx + max_lines)

        if len(runs) == 0:
            screen.blit(font.render("Nema još odigranih partija.", True, COLORS["muted"]), (panel.x + 20, start_y))
        else:
            for i in range(start_idx, end_idx):
                r = runs[i]
                won = r["won"]
                col = COLORS["good"] if won else COLORS["bad"]
                status = "WIN" if won else "LOSE"
                line = f"{r['ts']}  |  L{r['level']}  |  Score {r['score']}  |  Kills {r['kills']}  |  {status}"
                screen.blit(font.render(line, True, col if i == start_idx else COLORS["text"]), (panel.x + 20, start_y))
                start_y += line_h

            footer = f"Showing {start_idx+1}-{end_idx} of {len(runs)}"
            screen.blit(font.render(footer, True, COLORS["muted"]), (panel.x + 20, panel.bottom - 36))

        pygame.display.flip()
        clock.tick(60)


def draw_level_preview_map(screen, level_data: dict, rect: pygame.Rect):
   
    path = level_data["path_grid"]
    if not path:
        return

    
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    
    pad = 1
    minx -= pad
    maxx += pad
    miny -= pad
    maxy += pad

    bw = max(1, maxx - minx)
    bh = max(1, maxy - miny)

    def to_px(gx, gy):
        
        nx = (gx - minx) / bw
        ny = (gy - miny) / bh
        x = rect.x + 20 + nx * (rect.w - 40)
        y = rect.y + 20 + ny * (rect.h - 40)
        return (int(x), int(y))

    pts = [to_px(gx, gy) for gx, gy in path]

    pygame.draw.rect(screen, (18, 20, 26), rect, border_radius=14)
    pygame.draw.rect(screen, COLORS["btn_border"], rect, width=2, border_radius=14)

    
    for i in range(len(pts) - 1):
        pygame.draw.line(screen, COLORS["path"], pts[i], pts[i + 1], 10)
        pygame.draw.line(screen, COLORS["path_edge"], pts[i], pts[i + 1], 2)


def run_level_select(screen, levels: list):
    font = pygame.font.Font(None, 30)
    font_big = pygame.font.Font(None, 52)

    w, h = screen.get_size()
    panel = pygame.Rect(w // 2 - 320, 90, 640, 500)

    bx = panel.x + 24
    bw = panel.w - 48

    btn_back = Button(pygame.Rect(panel.right - 180, panel.y + 18, 160, 44), "Back", True)

    
    level_buttons = []
    start_y = panel.y + 120
    for i, lvl in enumerate(levels):
        r = pygame.Rect(bx, start_y + i * 64, bw, 52)
        level_buttons.append((lvl, Button(r, f"{lvl.get('name', 'Level')} (ID {lvl['id']})", True)))

    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.hit(e.pos):
                    return None
                for lvl, btn in level_buttons:
                    if btn.hit(e.pos):
                        return lvl

        screen.fill(COLORS["bg"])
        pygame.draw.rect(screen, COLORS["panel_bg"], panel, border_radius=16)
        pygame.draw.rect(screen, COLORS["btn_border"], panel, width=2, border_radius=16)

        title = font_big.render("Select Level", True, COLORS["text"])
        screen.blit(title, (panel.x + 24, panel.y + 22))
        btn_back.draw(screen, font, COLORS)

        hint = font.render("Klikni level za preview (Campaign/Endless).", True, COLORS["muted"])
        screen.blit(hint, (panel.x + 24, panel.y + 72))

        for lvl, btn in level_buttons:
            btn.draw(screen, font, COLORS)

        pygame.display.flip()
        clock.tick(60)

def draw_wrapped_text(screen, font, text, x, y, max_width, color, line_h=28):
    
    if not text:
        return y + line_h

    words = text.split(" ")
    line = ""

    for w in words:
        test = (line + " " + w).strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            if line:
                screen.blit(font.render(line, True, color), (x, y))
                y += line_h
                line = w
            else:
                
                cut = w
                while cut and font.size(cut + "…")[0] > max_width:
                    cut = cut[:-1]
                screen.blit(font.render(cut + "…", True, color), (x, y))
                y += line_h
                line = ""

    if line:
        screen.blit(font.render(line, True, color), (x, y))
        y += line_h

    return y


def run_level_preview(screen, level_data: dict):
    font = pygame.font.Font(None, 30)
    font_big = pygame.font.Font(None, 50)

    w, h = screen.get_size()
    panel = pygame.Rect(w // 2 - 360, 90, 720, 500)

    btn_back = Button(pygame.Rect(panel.right - 180, panel.y + 18, 160, 44), "Back", True)

    map_rect = pygame.Rect(panel.x + 24, panel.y + 110, 360, 300)

    right_x = panel.x + 420
    btn_w = panel.w - (right_x - panel.x) - 24
    btn_h = 45
    btn_campaign = Button(pygame.Rect(right_x, 0, btn_w, btn_h), "Play Campaign", True)
    btn_endless = Button(pygame.Rect(right_x, 0, btn_w, btn_h), "Play Endless", True)


    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.hit(e.pos):
                    return None
                if btn_campaign.hit(e.pos):
                    return "campaign"
                if btn_endless.hit(e.pos):
                    return "endless"

        screen.fill(COLORS["bg"])
        pygame.draw.rect(screen, COLORS["panel_bg"], panel, border_radius=16)
        pygame.draw.rect(screen, COLORS["btn_border"], panel, width=2, border_radius=16)

        title = font_big.render(level_data.get("name", f"Level {level_data['id']}"), True, COLORS["text"])
        screen.blit(title, (panel.x + 24, panel.y + 22))
        btn_back.draw(screen, font, COLORS)

        
        draw_level_preview_map(screen, level_data, map_rect)

        
        info_y = panel.y + 120
        max_w = panel.right - 24 - right_x  

        lines = [
            level_data.get("duration_text", f"Campaign: ~{level_data.get('campaign_waves', 6)} waves"),
            level_data.get("difficulty_text", "Difficulty: (not set)"),
            "",
            "Mode options:",
            "- Campaign: završava i pita za Endless",
            "- Endless: beskonačno, broji waves cleared",
        ]

        for line in lines:
            info_y = draw_wrapped_text(screen, font, line, right_x, info_y, max_w, COLORS["muted"], line_h=28)

        
        gap = 16
        y_btn1 = info_y + gap
        y_btn2 = y_btn1 + btn_h + 14

        max_btn2_top = panel.bottom - 24 - btn_h
        if y_btn2 > max_btn2_top:
            shift = y_btn2 - max_btn2_top
            y_btn1 -= shift
            y_btn2 -= shift

        btn_campaign.rect.y = y_btn1
        btn_endless.rect.y = y_btn2


        btn_campaign.draw(screen, font, COLORS)
        btn_endless.draw(screen, font, COLORS)

        pygame.display.flip()
        clock.tick(60)


def run_game(screen, level_data: dict, mode: str, load_state: Optional[dict] = None):
    clock = pygame.time.Clock()
    eng = CampusDefenseEngine(screen, level_data, mode=mode, load_state=load_state)

    while eng.running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            eng.handle_event(e)

        eng.update(dt)
        eng.draw()
        pygame.display.flip()

    if eng.exit_reason == "save" and eng.saved_checkpoint is not None:
        return {
            "action": "saved",
            "checkpoint": eng.saved_checkpoint,
        }

    
    won_campaign = bool(eng.campaign_completed) if mode == "campaign" else False
    return {
        "action": "ended",
        "won": won_campaign,
        "score": int(eng.score),
        "kills": int(eng.kills),
        "level_id": int(level_data["id"]),
        "campaign_completed": bool(eng.campaign_completed),
        "lost": bool(eng.lost),
        "exit_reason": str(eng.exit_reason),
    }


def _level_by_id(levels: list, level_id: int):
    for lvl in levels:
        if int(lvl.get("id")) == int(level_id):
            return lvl
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Geometry Defense - Josip Koren")

    db, conn, root = open_storage("game_data.fs")
    try:
        gs = ensure_state(root)
        
        for p in gs.profiles.values():
            if not hasattr(p, "saved_game"):
                p.saved_game = None
        commit()
        username = "student"

        levels = get_levels()

        while True:
            action, username = run_menu(screen, gs, username)
            if action == "quit":
                break

            profile = gs.get_or_create_profile(username)
            commit()

            if action == "history":
                res = run_history(screen, profile)
                if res == "quit":
                    break

            if action == "continue":
                if not profile.has_saved_game():
                    continue

                saved = profile.saved_game
                lvl = _level_by_id(levels, int(saved.get("level_id", 1)))
                if lvl is None:
                    
                    profile.clear_saved_game()
                    commit()
                    continue

                mode = str(saved.get("mode", "campaign"))
                result = run_game(screen, lvl, mode=mode, load_state=saved)

                if result["action"] == "saved":
                    profile.save_game(result["checkpoint"])
                    commit()
                else:
                    
                    if result.get("campaign_completed") or result.get("lost"):
                        profile.clear_saved_game()
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    profile.record_run(ts_iso=ts, level=result["level_id"], score=result["score"], kills=result["kills"], won=result["won"])
                    commit()

                continue

            if action == "level_select":
                while True:
                    lvl = run_level_select(screen, levels)
                    if lvl is None:
                        
                        break

                    mode = run_level_preview(screen, lvl)
                    if mode is None:
                        
                        continue

                    
                    profile.clear_saved_game()
                    commit()

                    result = run_game(screen, lvl, mode=mode)

                    if result["action"] == "saved":
                        profile.save_game(result["checkpoint"])
                        commit()
                        break

                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    profile.record_run(
                        ts_iso=ts,
                        level=result["level_id"],
                        score=result["score"],
                        kills=result["kills"],
                        won=result["won"],
                    )

                    if result.get("campaign_completed") or result.get("lost"):
                        profile.clear_saved_game()

                    commit()
                    break

    finally:
        conn.close()
        db.close()
        pygame.quit()


if __name__ == "__main__":
    main()
