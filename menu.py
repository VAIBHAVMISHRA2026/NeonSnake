"""
menu.py - Implements state-driven menus (Main, Settings, Pause, Shop, Achievements, Highscores) with layout widgets.
"""
import pygame
import math
from typing import Tuple, List, Dict, Any, Callable
from settings import Settings
from save import SaveManager
from audio import AudioManager
from ui import UIButton, HUD
from utils import Utils

class Slider:
    def __init__(self, x: int, y: int, w: int, h: int, value: float, label: str) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.value = value
        self.label = label
        self.is_dragging = False
        self.handle_radius = 8

    def update(self, mouse_pos: Tuple[int, int], mouse_down: bool) -> float:
        """Handles slider value drag tracking. Returns updated float value (0.0 to 1.0)."""
        mx, my = mouse_pos
        
        # Check if user clicks/drags handle or slider line
        if mouse_down:
            handle_x = self.rect.x + int(self.rect.w * self.value)
            dist_to_handle = ((mx - handle_x)**2 + (my - self.rect.centery)**2)**0.5
            
            if dist_to_handle <= self.handle_radius * 2 or (self.rect.collidepoint(mx, my) and not self.is_dragging):
                self.is_dragging = True
                
            if self.is_dragging:
                # Calculate relative factor
                t = (mx - self.rect.x) / float(self.rect.w)
                self.value = max(0.0, min(1.0, t))
        else:
            self.is_dragging = False
            
        return self.value

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Renders slider bar, track handle, and value label."""
        # Label text
        label_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, Settings.COLOR_WHITE)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 22))
        
        # Base bar
        Utils.draw_rounded_rect(surface, self.rect, Settings.COLOR_DARK_GRAY, radius=4)
        
        # Filled active bar
        fill_w = int(self.rect.w * self.value)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            Utils.draw_rounded_rect(surface, fill_rect, Settings.COLOR_CYAN, radius=4)
            
        # Draw handle circle
        hx = self.rect.x + fill_w
        hy = self.rect.centery
        color = Settings.COLOR_PINK if self.is_dragging else Settings.COLOR_WHITE
        pygame.draw.circle(surface, color, (hx, hy), self.handle_radius)
        pygame.draw.circle(surface, Settings.COLOR_DARK_GRAY, (hx, hy), self.handle_radius, 1)


class MenuSystem:
    def __init__(self, save_manager: SaveManager, audio_manager: AudioManager, change_state_cb: Callable[[str], None]) -> None:
        self.save_manager = save_manager
        self.audio_manager = audio_manager
        self.change_state = change_state_cb
        
        self.width = Settings.SCREEN_WIDTH
        self.height = Settings.SCREEN_HEIGHT
        
        # Buttons cache grouped by menu states
        self.buttons: Dict[str, List[UIButton]] = {}
        # Active sliders
        self.sliders: List[Slider] = []
        
        # Shop pagination / selection indexes
        self.shop_scroll_index = 0
        self.logo_pulse: float = 0.0
        self.rebind_target = None
        
        self.init_menus()

    def init_menus(self) -> None:
        """Initializes buttons layout for each state: MAIN, SHOP, SETTINGS, HIGHSCORES, ACHIEVEMENTS."""
        cx = self.width // 2
        
        # 1. MAIN MENU
        self.buttons["MAIN"] = [
            UIButton(pygame.Rect(cx - 120, 220, 240, 45), "PLAY", lambda: self.change_state("PLAYING"), Settings.COLOR_CYAN, Settings.COLOR_GREEN),
            UIButton(pygame.Rect(cx - 120, 280, 240, 45), "SHOP", lambda: self.change_state("SHOP"), Settings.COLOR_CYAN, Settings.COLOR_PINK),
            UIButton(pygame.Rect(cx - 120, 340, 240, 45), "HIGHSCORES", lambda: self.change_state("HIGHSCORES")),
            UIButton(pygame.Rect(cx - 120, 400, 240, 45), "ACHIEVEMENTS", lambda: self.change_state("ACHIEVEMENTS")),
            UIButton(pygame.Rect(cx - 120, 460, 240, 45), "SETTINGS", lambda: self.change_state("SETTINGS")),
            UIButton(pygame.Rect(cx - 120, 520, 240, 45), "EXIT", lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)), Settings.COLOR_RED, Settings.COLOR_PINK)
        ]

        # 2. SHOP MENU BACK BUTTON
        self.buttons["SHOP"] = [
            UIButton(pygame.Rect(50, 50, 100, 35), "BACK", lambda: self.change_state("MAIN"), Settings.COLOR_GRAY, Settings.COLOR_WHITE)
        ]
        
        # 3. SETTINGS MENU BUTTONS & SLIDERS
        self.buttons["SETTINGS"] = [
            UIButton(pygame.Rect(cx - 220, 420, 200, 40), "CONTROLS: WASD", self.toggle_controls),
            UIButton(pygame.Rect(cx + 20, 420, 200, 40), "CUSTOMIZE KEYS", lambda: self.change_state("KEYBINDINGS")),
            UIButton(pygame.Rect(cx - 220, 480, 200, 40), "DIFFICULTY: MED", self.toggle_difficulty),
            UIButton(pygame.Rect(cx + 20, 480, 200, 40), "HORROR MODE: OFF", self.toggle_horror_mode, Settings.COLOR_BLOOD_RED, Settings.COLOR_RED),
            UIButton(pygame.Rect(cx - 100, 540, 200, 40), "BACK", lambda: self.change_state("MAIN"), Settings.COLOR_GRAY, Settings.COLOR_WHITE)
        ]
        
        # 3.5. KEYBINDINGS MENU
        self.buttons["KEYBINDINGS"] = [
            UIButton(pygame.Rect(cx - 210, 180, 420, 40), "UP: W", lambda: self.start_rebind("UP")),
            UIButton(pygame.Rect(cx - 210, 240, 420, 40), "DOWN: S", lambda: self.start_rebind("DOWN")),
            UIButton(pygame.Rect(cx - 210, 300, 420, 40), "LEFT: A", lambda: self.start_rebind("LEFT")),
            UIButton(pygame.Rect(cx - 210, 360, 420, 40), "RIGHT: D", lambda: self.start_rebind("RIGHT")),
            UIButton(pygame.Rect(cx - 210, 430, 200, 40), "RESET DEFAULTS", self.reset_keys, Settings.COLOR_BLOOD_RED, Settings.COLOR_RED),
            UIButton(pygame.Rect(cx + 10, 430, 200, 40), "BACK", lambda: self.change_state("SETTINGS"), Settings.COLOR_GRAY, Settings.COLOR_WHITE)
        ]
        # Set slider coordinates
        sets = self.save_manager.get_settings()
        self.sliders = [
            Slider(cx - 200, 250, 400, 12, sets.get("music_volume", 0.5), "MUSIC VOLUME"),
            Slider(cx - 200, 330, 400, 12, sets.get("sfx_volume", 0.6), "SFX VOLUME")
        ]
        # Sync label states
        self.sync_settings_buttons_labels()

        # 4. HIGHSCORES MENU
        self.buttons["HIGHSCORES"] = [
            UIButton(pygame.Rect(cx - 100, 560, 200, 40), "BACK", lambda: self.change_state("MAIN"), Settings.COLOR_GRAY, Settings.COLOR_WHITE)
        ]
        
        # 5. ACHIEVEMENTS MENU
        self.buttons["ACHIEVEMENTS"] = [
            UIButton(pygame.Rect(cx - 100, 580, 200, 40), "BACK", lambda: self.change_state("MAIN"), Settings.COLOR_GRAY, Settings.COLOR_WHITE)
        ]

    def sync_settings_buttons_labels(self) -> None:
        """Reads variables from save manager and sets current text label descriptions."""
        sets = self.save_manager.get_settings()
        
        # Update Controls Toggle
        self.buttons["SETTINGS"][0].text = f"CONTROLS: {sets.get('control_scheme', 'WASD')}"
        # Update Difficulty Toggle
        self.buttons["SETTINGS"][2].text = f"DIFFICULTY: {sets.get('difficulty', 'Medium').upper()}"
        # Update Horror Toggle
        h_str = "ON" if sets.get("horror_mode", False) else "OFF"
        self.buttons["SETTINGS"][3].text = f"HORROR MODE: {h_str}"
        
        # Sync Keybindings labels
        if "KEYBINDINGS" in self.buttons:
            kb = sets.get("keybindings", {
                "UP": pygame.K_UP,
                "DOWN": pygame.K_DOWN,
                "LEFT": pygame.K_LEFT,
                "RIGHT": pygame.K_RIGHT
            })
            up_name = pygame.key.name(kb["UP"]).upper()
            down_name = pygame.key.name(kb["DOWN"]).upper()
            left_name = pygame.key.name(kb["LEFT"]).upper()
            right_name = pygame.key.name(kb["RIGHT"]).upper()
            
            self.buttons["KEYBINDINGS"][0].text = f"UP: {up_name}" if self.rebind_target != "UP" else "UP: PRESS ANY KEY..."
            self.buttons["KEYBINDINGS"][1].text = f"DOWN: {down_name}" if self.rebind_target != "DOWN" else "DOWN: PRESS ANY KEY..."
            self.buttons["KEYBINDINGS"][2].text = f"LEFT: {left_name}" if self.rebind_target != "LEFT" else "LEFT: PRESS ANY KEY..."
            self.buttons["KEYBINDINGS"][3].text = f"RIGHT: {right_name}" if self.rebind_target != "RIGHT" else "RIGHT: PRESS ANY KEY..."

    def toggle_controls(self) -> None:
        sets = self.save_manager.get_settings()
        curr = sets.get("control_scheme", "WASD")
        new_scheme = "ARROWS" if curr == "WASD" else ("CUSTOM" if curr == "ARROWS" else "WASD")
        sets["control_scheme"] = new_scheme
        self.save_manager.update_settings(sets)
        self.sync_settings_buttons_labels()
        self.audio_manager.play_sound("button_click")
        
    def start_rebind(self, action: str) -> None:
        self.rebind_target = action
        self.sync_settings_buttons_labels()
        self.audio_manager.play_sound("button_click")
        
    def reset_keys(self) -> None:
        sets = self.save_manager.get_settings()
        sets["keybindings"] = {
            "UP": pygame.K_UP,
            "DOWN": pygame.K_DOWN,
            "LEFT": pygame.K_LEFT,
            "RIGHT": pygame.K_RIGHT
        }
        sets["control_scheme"] = "ARROWS"
        self.save_manager.update_settings(sets)
        self.sync_settings_buttons_labels()
        self.audio_manager.play_sound("button_click")
        
    def save_keybinding(self, action: str, key_val: int) -> None:
        sets = self.save_manager.get_settings()
        if "keybindings" not in sets:
            sets["keybindings"] = {
                "UP": pygame.K_UP,
                "DOWN": pygame.K_DOWN,
                "LEFT": pygame.K_LEFT,
                "RIGHT": pygame.K_RIGHT
            }
        sets["keybindings"][action] = key_val
        sets["control_scheme"] = "CUSTOM"
        self.save_manager.update_settings(sets)

    def toggle_difficulty(self) -> None:
        sets = self.save_manager.get_settings()
        diffs = ["Easy", "Medium", "Hard", "Impossible"]
        cur = sets.get("difficulty", "Medium")
        next_idx = (diffs.index(cur) + 1) % len(diffs)
        sets["difficulty"] = diffs[next_idx]
        self.save_manager.update_settings(sets)
        self.sync_settings_buttons_labels()
        self.audio_manager.play_sound("button_click")

    def toggle_horror_mode(self) -> None:
        sets = self.save_manager.get_settings()
        sets["horror_mode"] = not sets.get("horror_mode", False)
        self.save_manager.update_settings(sets)
        self.sync_settings_buttons_labels()
        self.audio_manager.play_sound("button_click")

    def update(self, current_menu_state: str, mouse_pos: Tuple[int, int], mouse_down: bool, clicked_trigger: bool, dt: float) -> None:
        """Updates active widgets (buttons and sliders) for the currently running state."""
        # Intercept if waiting for rebind key
        if getattr(self, "rebind_target", None) is not None:
            keys = pygame.event.get(pygame.KEYDOWN)
            if keys:
                pressed_key = keys[0].key
                if pressed_key != pygame.K_ESCAPE:
                    self.save_keybinding(self.rebind_target, pressed_key)
                self.rebind_target = None
                self.sync_settings_buttons_labels()
            return
            
        # 1. Update logo pulsing animation
        self.logo_pulse += 4.0 * dt
        
        # 2. Update Buttons
        btns = self.buttons.get(current_menu_state, [])
        for b in btns:
            # Check click
            old_hover = b.is_hovered
            b.update(mouse_pos, clicked_trigger, dt)
            # Play click sound
            if b.is_hovered and clicked_trigger:
                self.audio_manager.play_sound("button_click")
            # Hover tick sound
            if b.is_hovered and not old_hover:
                self.audio_manager.play_sound("button_click")
                
        # 3. Update Sliders (only on Settings menu)
        if current_menu_state == "SETTINGS":
            music_val = self.sliders[0].update(mouse_pos, mouse_down)
            if self.sliders[0].is_dragging:
                self.audio_manager.set_music_volume(music_val)
                
            sfx_val = self.sliders[1].update(mouse_pos, mouse_down)
            if self.sliders[1].is_dragging:
                self.audio_manager.set_sfx_volume(sfx_val)

        # 4. Handle Shop Skin Grid clicks
        if current_menu_state == "SHOP" and clicked_trigger:
            self.handle_shop_clicks(mouse_pos)

    def handle_shop_clicks(self, mouse_pos: Tuple[int, int]) -> None:
        """Matches grid coordinate mouse clicks to buy or equip skins."""
        mx, my = mouse_pos
        
        # Grid parameters (matching draw layout below)
        start_x = self.width // 2 - 400
        start_y = 150
        grid_w = 180
        grid_h = 130
        gap = 20
        
        for idx, skin in enumerate(Settings.SKINS):
            row = idx // 4
            col = idx % 4
            sx = start_x + col * (grid_w + gap)
            sy = start_y + row * (grid_h + gap)
            
            skin_rect = pygame.Rect(sx, sy, grid_w, grid_h)
            if skin_rect.collidepoint(mx, my):
                unlocked = skin["id"] in self.save_manager.data["unlocked_skins"]
                cost = skin["cost"]
                
                if unlocked:
                    # Select/equip skin
                    self.save_manager.set_current_skin(skin["id"])
                    self.audio_manager.play_sound("button_click")
                else:
                    # Buy skin
                    if self.save_manager.get_coins() >= cost:
                        if self.save_manager.unlock_skin(skin["id"], cost):
                            self.save_manager.set_current_skin(skin["id"])
                            self.audio_manager.play_sound("victory")
                    else:
                        self.audio_manager.play_sound("hit")  # Error buzz/denied

    def draw(self, surface: pygame.Surface, current_state: str, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        """Main delegator to draw specific menu styles."""
        # Background gets drawn by game loop parallax, we draw widgets
        
        if current_state == "MAIN":
            self.draw_main_menu(surface, font_lg)
        elif current_state == "SHOP":
            self.draw_shop_menu(surface, font_sm, font_md, font_lg)
        elif current_state == "SETTINGS":
            self.draw_settings_menu(surface, font_sm, font_md, font_lg)
        elif current_state == "HIGHSCORES":
            self.draw_highscores_menu(surface, font_sm, font_md, font_lg)
        elif current_state == "ACHIEVEMENTS":
            self.draw_achievements_menu(surface, font_sm, font_md, font_lg)
        elif current_state == "KEYBINDINGS":
            self.draw_keybindings_menu(surface, font_sm, font_md, font_lg)
            
        # Draw base navigation buttons
        for b in self.buttons.get(current_state, []):
            b.draw(surface, font_sm)

    def draw_main_menu(self, surface: pygame.Surface, font_lg: pygame.font.Font) -> None:
        # Title text overlay with glow
        title_y = 100
        cx = self.width // 2
        
        # Draw bouncing title logo
        pulse = int(5.0 * math.sin(self.logo_pulse))
        logo_y = title_y + pulse
        
        # Synthesize beautiful neon outline logo
        title_text = "NEON SNAKE"
        glow_surf = font_lg.render(title_text, True, Settings.COLOR_CYAN)
        core_surf = font_lg.render(title_text, True, Settings.COLOR_WHITE)
        
        # Glow layer offsets
        for ox, oy in [(-3,-3), (3,3), (-3,3), (3,-3), (0,-4), (0,4), (-4,0), (4,0)]:
            surface.blit(glow_surf, (cx - glow_surf.get_width()//2 + ox, logo_y + oy), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(core_surf, (cx - core_surf.get_width()//2, logo_y))
        
        # Subheading tag
        tag_font = pygame.font.SysFont("Verdana", 14)
        tag_surf = tag_font.render("ULTIMATE EXPERT COMMUNITY EDITION", True, Settings.COLOR_PINK)
        surface.blit(tag_surf, (cx - tag_surf.get_width()//2, logo_y + 70))
        
        # Draw Daily Quests panel on the right side of Main Menu
        q_rect = pygame.Rect(820, 210, 400, 350)
        Utils.draw_rounded_rect(surface, q_rect, (15, 15, 25, 200), radius=10)
        Utils.draw_rounded_rect(surface, q_rect, Settings.COLOR_CYAN, radius=10, border_width=1)
        
        # Header text
        q_title = tag_font.render("DAILY TARGETS", True, Settings.COLOR_GOLD)
        surface.blit(q_title, (840, 225))
        
        # Load missions
        missions = self.save_manager.data.get("missions", [])
        m_y = 265
        for m in missions:
            # Mission text description
            color = Settings.COLOR_WHITE if not m["completed"] else Settings.COLOR_GRAY
            m_surf = tag_font.render(m["text"], True, color)
            surface.blit(m_surf, (840, m_y))
            
            # Progress fraction
            prog_text = f"{m['current']}/{m['target']}"
            if m["completed"]:
                prog_text = "COMPLETE! (+{} C)".format(m['reward'])
                prog_col = Settings.COLOR_GREEN
            else:
                prog_col = Settings.COLOR_CYAN
                
            p_surf = tag_font.render(prog_text, True, prog_col)
            surface.blit(p_surf, (1200 - p_surf.get_width(), m_y))
            
            # Progress bar background
            bar_rect = pygame.Rect(840, m_y + 22, 340, 6)
            pygame.draw.rect(surface, Settings.COLOR_DARK_GRAY, bar_rect, border_radius=3)
            
            # Progress bar fill
            if m["target"] > 0:
                pct = min(1.0, max(0.0, m["current"] / m["target"]))
                if pct > 0:
                    fill_w = int(340 * pct)
                    fill_rect = pygame.Rect(840, m_y + 22, fill_w, 6)
                    pygame.draw.rect(surface, prog_col, fill_rect, border_radius=3)
                    
            m_y += 65

    def draw_shop_menu(self, surface: pygame.Surface, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        # Header
        t_surf = font_lg.render("SKIN INVENTORY SHOP", True, Settings.COLOR_PINK)
        surface.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, 50))
        
        # Coins Wallet indicator
        coin_text = f"YOUR COINS: {self.save_manager.get_coins()}"
        wallet_surf = font_md.render(coin_text, True, Settings.COLOR_GOLD)
        surface.blit(wallet_surf, (self.width - wallet_surf.get_width() - 50, 55))
        
        # Draw Skins Grid
        start_x = self.width // 2 - 400
        start_y = 150
        grid_w = 180
        grid_h = 130
        gap = 20
        
        cur_skin = self.save_manager.get_current_skin()
        unlocked_list = self.save_manager.data["unlocked_skins"]
        
        for idx, skin in enumerate(Settings.SKINS):
            row = idx // 4
            col = idx % 4
            sx = start_x + col * (grid_w + gap)
            sy = start_y + row * (grid_h + gap)
            
            skin_rect = pygame.Rect(sx, sy, grid_w, grid_h)
            is_unlocked = skin["id"] in unlocked_list
            is_equipped = skin["id"] == cur_skin
            
            # Hover highlighting border
            mx, my = pygame.mouse.get_pos()
            is_hover = skin_rect.collidepoint(mx, my)
            
            # Draw Panel Box
            bg_color = (25, 25, 35) if is_hover else (15, 15, 20)
            border_color = Settings.COLOR_CYAN if is_equipped else (Settings.COLOR_GOLD if is_hover else Settings.COLOR_DARK_GRAY)
            border_w = 2 if (is_equipped or is_hover) else 1
            
            Utils.draw_rounded_rect(surface, skin_rect, bg_color, radius=10)
            Utils.draw_rounded_rect(surface, skin_rect, border_color, radius=10, border_width=border_w)
            
            # Draw visual sample segment circles in center of box
            seg_cx = sx + grid_w // 2
            seg_cy = sy + grid_h // 2 - 10
            
            for i in range(3):
                # Slithering layout
                cx = seg_cx - (1 - i) * 16
                cy = seg_cy + int(4.0 * math.sin(pygame.time.get_ticks() * 0.006 - i * 0.5))
                # Alternate segment drawing
                pygame.draw.circle(surface, skin["primary"], (cx, cy), 11 - i * 2)
                pygame.draw.circle(surface, skin["secondary"], (cx, cy), 8 - i * 2)
                
            # Draw text labels
            name_surf = font_sm.render(skin["name"], True, Settings.COLOR_WHITE)
            surface.blit(name_surf, (sx + grid_w//2 - name_surf.get_width()//2, sy + grid_h - 45))
            
            # Status tag (EQUIPPED, SELECT, BUY x COINS)
            if is_equipped:
                status_text = "EQUIPPED"
                status_color = Settings.COLOR_CYAN
            elif is_unlocked:
                status_text = "EQUIP"
                status_color = Settings.COLOR_GREEN
            else:
                status_text = f"BUY: {skin['cost']} C"
                status_color = Settings.COLOR_GOLD
                
            stat_surf = font_sm.render(status_text, True, status_color)
            surface.blit(stat_surf, (sx + grid_w//2 - stat_surf.get_width()//2, sy + grid_h - 22))

    def draw_settings_menu(self, surface: pygame.Surface, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        cx = self.width // 2
        # Title
        t_surf = font_lg.render("SETTINGS UTILITY", True, Settings.COLOR_CYAN)
        surface.blit(t_surf, (cx - t_surf.get_width()//2, 50))
        
        # Draw Sliders
        for s in self.sliders:
            s.draw(surface, font_md)

    def draw_highscores_menu(self, surface: pygame.Surface, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        cx = self.width // 2
        # Title
        t_surf = font_lg.render("ARCADE HALL OF FAME", True, Settings.COLOR_GOLD)
        surface.blit(t_surf, (cx - t_surf.get_width()//2, 50))
        
        # Under construction Offline leaderboard layout
        # Read player's score
        top_score = self.save_manager.get_high_score()
        
        leaderboard_panel = pygame.Rect(cx - 250, 140, 500, 390)
        Utils.draw_rounded_rect(surface, leaderboard_panel, (15, 15, 25, 200), radius=12)
        Utils.draw_rounded_rect(surface, leaderboard_panel, Settings.COLOR_GOLD, radius=12, border_width=1)
        
        # Render lists headers
        h_rank = font_md.render("RANK", True, Settings.COLOR_GOLD)
        h_name = font_md.render("PLAYER", True, Settings.COLOR_GOLD)
        h_score = font_md.render("SCORE", True, Settings.COLOR_GOLD)
        
        surface.blit(h_rank, (cx - 200, 160))
        surface.blit(h_name, (cx - 50, 160))
        surface.blit(h_score, (cx + 100, 160))
        
        pygame.draw.line(surface, Settings.COLOR_DARK_GRAY, (cx - 220, 195), (cx + 220, 195), 1)
        
        # Dummy bot leaderboard filled around user's high score
        mock_leaders = [
            ("ApexViper", 12500),
            ("ByteEater", 9800),
            ("SlitherLord", 7600),
            ("YOU", top_score),
            ("CyberWorm", 4200),
            ("NeonGrid", 2100)
        ]
        # Sort desc
        mock_leaders.sort(key=lambda x: x[1], reverse=True)
        
        list_y = 215
        for idx, (name, val) in enumerate(mock_leaders[:7]):
            color = Settings.COLOR_PINK if name == "YOU" else Settings.COLOR_WHITE
            
            # Rank
            r_surf = font_md.render(f"#{idx + 1}", True, color)
            # Name
            n_surf = font_md.render(name, True, color)
            # Score
            s_surf = font_md.render(f"{val}", True, color)
            
            surface.blit(r_surf, (cx - 200, list_y))
            surface.blit(n_surf, (cx - 50, list_y))
            surface.blit(s_surf, (cx + 100, list_y))
            
            list_y += 42

    def draw_achievements_menu(self, surface: pygame.Surface, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        cx = self.width // 2
        # Title
        t_surf = font_lg.render("OFFLINE TROPHY VAULT", True, Settings.COLOR_PINK)
        surface.blit(t_surf, (cx - t_surf.get_width()//2, 50))
        
        # Achievements panel container
        ach_panel = pygame.Rect(cx - 350, 130, 700, 420)
        Utils.draw_rounded_rect(surface, ach_panel, (15, 15, 20, 200), radius=12)
        Utils.draw_rounded_rect(surface, ach_panel, Settings.COLOR_PINK, radius=12, border_width=1)
        
        unlocked_list = self.save_manager.data["unlocked_achievements"]
        
        # Render top 5 achievements dynamically slithered inside scroll view
        ach_y = 150
        for ach in Settings.ACHIEVEMENTS[:5]:  # Display first 5 (can add scroll paging in updates)
            unlocked = ach["id"] in unlocked_list
            bg_col = (20, 30, 20) if unlocked else (30, 30, 35)
            border_col = Settings.COLOR_GREEN if unlocked else Settings.COLOR_GRAY
            
            item_rect = pygame.Rect(cx - 320, ach_y, 640, 65)
            Utils.draw_rounded_rect(surface, item_rect, bg_col, radius=8)
            Utils.draw_rounded_rect(surface, item_rect, border_col, radius=8, border_width=1)
            
            # Title
            title_color = Settings.COLOR_GREEN if unlocked else Settings.COLOR_GRAY
            title_surf = font_md.render(ach["name"], True, title_color)
            surface.blit(title_surf, (cx - 300, ach_y + 10))
            
            # Description
            desc_surf = font_sm.render(ach["desc"], True, Settings.COLOR_WHITE if unlocked else Settings.COLOR_GRAY)
            surface.blit(desc_surf, (cx - 300, ach_y + 35))
            
            # Reward
            rew_text = f"+{ach['reward']} COINS"
            rew_color = Settings.COLOR_GOLD if unlocked else Settings.COLOR_GRAY
            rew_surf = font_sm.render(rew_text, True, rew_color)
            surface.blit(rew_surf, (cx + 300 - rew_surf.get_width(), ach_y + 22))
            
            ach_y += 75
            
        # Draw simple page tag
        page_surf = font_sm.render("Showing top achievements - Unlock in game!", True, Settings.COLOR_GRAY)
        surface.blit(page_surf, (cx - page_surf.get_width()//2, 515))

    def draw_keybindings_menu(self, surface: pygame.Surface, font_sm: pygame.font.Font, font_md: pygame.font.Font, font_lg: pygame.font.Font) -> None:
        cx = self.width // 2
        # Title
        t_surf = font_lg.render("KEY REBINDING", True, Settings.COLOR_CYAN)
        surface.blit(t_surf, (cx - t_surf.get_width()//2, 50))
        
        # Subtitle instructions
        desc = "Click an action, then press any key. Esc to cancel."
        desc_surf = font_md.render(desc, True, Settings.COLOR_GRAY)
        surface.blit(desc_surf, (cx - desc_surf.get_width()//2, 120))
