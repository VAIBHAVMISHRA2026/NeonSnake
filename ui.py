"""
ui.py - Custom user interface elements including glowing buttons, animated panels, HUD bars, and floating text.
"""
import math
import pygame
from typing import Tuple, List, Callable, Dict, Any
from settings import Settings
from utils import Utils

class FloatingText:
    def __init__(self, text: str, x: float, y: float, color: Tuple[int, int, int], size: int = 24, duration: float = 1.0) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.vy = -60.0  # Drift speed upwards (pixels per sec)
        self.color = color
        self.size = size
        self.life = duration
        self.max_life = duration

    def update(self, dt: float) -> bool:
        """Drifts upwards and updates life. Returns True if alive, False if expired."""
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0.0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, camera_offset: Tuple[float, float]) -> None:
        """Renders text translated by camera offset, with fading opacity."""
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        
        alpha = int(255 * (self.life / self.max_life))
        alpha = max(0, min(255, alpha))
        
        # Render outline
        outline_surf = font.render(self.text, True, (0, 0, 0))
        text_surf = font.render(self.text, True, self.color)
        
        # Create alpha-capable surface
        surf = pygame.Surface((text_surf.get_width() + 4, text_surf.get_height() + 4), pygame.SRCALPHA)
        
        # Draw outline offsets
        for dx, dy in [(-1,-1), (1,1), (-1,1), (1,-1)]:
            surf.blit(outline_surf, (2 + dx, 2 + dy))
        surf.blit(text_surf, (2, 2))
        
        # Set transparency
        surf.set_alpha(alpha)
        
        # Blit centered
        surface.blit(surf, (px - surf.get_width()//2, py - surf.get_height()//2))

class UIButton:
    def __init__(
        self, 
        rect: pygame.Rect, 
        text: str, 
        callback: Callable[[], None], 
        base_color: Tuple[int, int, int] = Settings.COLOR_CYAN, 
        hover_color: Tuple[int, int, int] = Settings.COLOR_PINK
    ) -> None:
        self.rect = rect
        self.text = text
        self.callback = callback
        self.base_color = base_color
        self.hover_color = hover_color
        
        # Animation state
        self.hover_progress: float = 0.0  # 0.0 to 1.0
        self.scale_factor: float = 1.0
        self.target_scale: float = 1.0
        
        self.is_hovered: bool = False

    def update(self, mouse_pos: Tuple[int, int], clicked: bool, dt: float) -> None:
        """Updates hover states and scale micro-animations. Triggers callback on click."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Lerp hover progress
        if self.is_hovered:
            self.hover_progress = Utils.lerp(self.hover_progress, 1.0, 12.0 * dt)
            self.target_scale = 1.05
        else:
            self.hover_progress = Utils.lerp(self.hover_progress, 0.0, 8.0 * dt)
            self.target_scale = 1.0
            
        self.scale_factor = Utils.lerp(self.scale_factor, self.target_scale, 15.0 * dt)
        
        if self.is_hovered and clicked:
            self.callback()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Renders button with smooth size changes and neon glows on hover."""
        # Scale rect calculations
        center = self.rect.center
        w = int(self.rect.w * self.scale_factor)
        h = int(self.rect.h * self.scale_factor)
        scaled_rect = pygame.Rect(center[0] - w // 2, center[1] - h // 2, w, h)
        
        # Calculate dynamic color
        r = int(Utils.lerp(self.base_color[0], self.hover_color[0], self.hover_progress))
        g = int(Utils.lerp(self.base_color[1], self.hover_color[1], self.hover_progress))
        b = int(Utils.lerp(self.base_color[2], self.hover_color[2], self.hover_progress))
        color = (r, g, b)
        
        # Draw background panel
        # Glow frame when hovered
        if self.hover_progress > 0.05:
            glow_w = scaled_rect.w + 6
            glow_h = scaled_rect.h + 6
            glow_rect = pygame.Rect(center[0] - glow_w//2, center[1] - glow_h//2, glow_w, glow_h)
            glow_alpha = int(80 * self.hover_progress)
            glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
            Utils.draw_rounded_rect(glow_surf, pygame.Rect(0, 0, glow_w, glow_h), (r, g, b, glow_alpha), radius=10)
            surface.blit(glow_surf, glow_rect.topleft)

        # Draw main button box
        Utils.draw_rounded_rect(surface, scaled_rect, Settings.COLOR_DARK_GRAY, radius=8)
        Utils.draw_rounded_rect(surface, scaled_rect, color, radius=8, border_width=2)
        
        # Render text
        text_color = Settings.COLOR_WHITE
        if self.is_hovered:
            text_color = color
            
        t_surf = font.render(self.text, True, text_color)
        t_rect = t_surf.get_rect(center=center)
        surface.blit(t_surf, t_rect.topleft)


class HUD:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        
        # Popping size trackers
        self.score_scale: float = 1.0
        self.coins_scale: float = 1.0
        self.combo_scale: float = 1.0
        
        self.cached_score: int = 0
        self.cached_coins: int = 0
        self.cached_combo: int = 0

    def update(self, score: int, coins: int, combo: int, dt: float) -> None:
        """Triggers scaling visual pops if hud values have updated."""
        if score != self.cached_score:
            self.score_scale = 1.4
            self.cached_score = score
        else:
            self.score_scale = Utils.lerp(self.score_scale, 1.0, 8.0 * dt)
            
        if coins != self.cached_coins:
            self.coins_scale = 1.4
            self.cached_coins = coins
        else:
            self.coins_scale = Utils.lerp(self.coins_scale, 1.0, 8.0 * dt)
            
        if combo != self.cached_combo:
            if combo > self.cached_combo:
                self.combo_scale = 1.5
            self.cached_combo = combo
        else:
            self.combo_scale = Utils.lerp(self.combo_scale, 1.0, 5.0 * dt)

    def draw_hud(
        self, 
        surface: pygame.Surface, 
        score: int, 
        coins: int, 
        combo: int, 
        combo_timer: float, 
        combo_max: float,
        level: int, 
        xp: float, 
        xp_needed: float,
        lives: int,
        shield_active: bool,
        active_powerups: Dict[str, float],
        font_sm: pygame.font.Font,
        font_md: pygame.font.Font
    ) -> None:
        """Renders HUD layout: Level progress bar, powerups, combo, scores, lives."""
        
        # 1. Top Left - Score & Coins
        # Draw gradient panel under score
        score_panel = pygame.Rect(15, 15, 260, 80)
        # Background
        Utils.draw_rounded_rect(surface, score_panel, (15, 15, 25, 200), radius=10)
        Utils.draw_rounded_rect(surface, score_panel, Settings.COLOR_CYAN, radius=10, border_width=1)
        
        # Render values with scaling triggers
        score_text = f"SCORE: {score}"
        score_surf = font_md.render(score_text, True, Settings.COLOR_CYAN)
        if self.score_scale > 1.01:
            score_surf = pygame.transform.smoothscale(
                score_surf, 
                (int(score_surf.get_width() * self.score_scale), int(score_surf.get_height() * self.score_scale))
            )
        surface.blit(score_surf, (30, 25))
        
        coin_text = f"COINS: {coins}"
        coin_surf = font_sm.render(coin_text, True, Settings.COLOR_GOLD)
        if self.coins_scale > 1.01:
            coin_surf = pygame.transform.smoothscale(
                coin_surf,
                (int(coin_surf.get_width() * self.coins_scale), int(coin_surf.get_height() * self.coins_scale))
            )
        surface.blit(coin_surf, (30, 55))
        
        # 2. Top Center - Level Progress (XP bar)
        progress_w = 400
        progress_h = 16
        progress_x = (self.width - progress_w) // 2
        progress_y = 20
        
        # Draw background bar
        bg_bar_rect = pygame.Rect(progress_x, progress_y, progress_w, progress_h)
        Utils.draw_rounded_rect(surface, bg_bar_rect, Settings.COLOR_DARK_GRAY, radius=6)
        
        # Draw filled progress percentage
        xp_pct = min(1.0, max(0.0, xp / max(1.0, xp_needed)))
        if xp_pct > 0.0:
            fill_bar_rect = pygame.Rect(progress_x, progress_y, int(progress_w * xp_pct), progress_h)
            Utils.draw_rounded_rect(surface, fill_bar_rect, Settings.COLOR_GREEN, radius=6)
            
        level_text = f"LEVEL {level}"
        lvl_surf = font_sm.render(level_text, True, Settings.COLOR_WHITE)
        surface.blit(lvl_surf, (progress_x + progress_w // 2 - lvl_surf.get_width() // 2, progress_y + 20))

        # 3. Top Right - Health/Shield Indicators
        heart_panel = pygame.Rect(self.width - 200, 15, 185, 45)
        Utils.draw_rounded_rect(surface, heart_panel, (15, 15, 25, 200), radius=10)
        Utils.draw_rounded_rect(surface, heart_panel, Settings.COLOR_PINK, radius=10, border_width=1)
        
        # Draw lives hearts
        life_x = self.width - 180
        for i in range(3):
            color = Settings.COLOR_PINK if i < lives else Settings.COLOR_GRAY
            # Draw simple triangle/circle hearts procedurally
            center_x = life_x + i * 35 + 10
            center_y = 35
            if i < lives:
                pygame.draw.circle(surface, color, (center_x - 6, center_y - 4), 6)
                pygame.draw.circle(surface, color, (center_x + 6, center_y - 4), 6)
                pygame.draw.polygon(surface, color, [(center_x - 12, center_y - 2), (center_x + 12, center_y - 2), (center_x, center_y + 11)])
            else:
                pygame.draw.circle(surface, color, (center_x, center_y), 6, 2)
                
        # Shield active light indicator
        if shield_active:
            shield_surf = font_sm.render("[SHIELD]", True, Settings.COLOR_BLUE)
            surface.blit(shield_surf, (self.width - 130, 68))

        # 4. Combo Counter Overlay (Pops at screen side)
        if combo > 1:
            combo_panel = pygame.Rect(15, 120, 200, 50)
            Utils.draw_rounded_rect(surface, combo_panel, (25, 10, 20, 180), radius=8)
            Utils.draw_rounded_rect(surface, combo_panel, Settings.COLOR_PINK, radius=8, border_width=1)
            
            combo_text = f"COMBO x{combo}"
            combo_surf = font_md.render(combo_text, True, Settings.COLOR_PINK)
            if self.combo_scale > 1.01:
                combo_surf = pygame.transform.smoothscale(
                    combo_surf,
                    (int(combo_surf.get_width() * self.combo_scale), int(combo_surf.get_height() * self.combo_scale))
                )
            surface.blit(combo_surf, (25, 127))
            
            # Progress bar timer decay under combo panel
            timer_pct = min(1.0, max(0.0, combo_timer / max(0.01, combo_max)))
            timer_w = int(180 * timer_pct)
            if timer_w > 0:
                pygame.draw.line(surface, Settings.COLOR_PINK, (25, 160), (25 + timer_w, 160), 3)

        # 5. Right Screen - Powerup duration lists
        pw_y = 120
        for name, duration in list(active_powerups.items()):
            if duration <= 0:
                continue
                
            pw_panel = pygame.Rect(self.width - 220, pw_y, 200, 32)
            Utils.draw_rounded_rect(surface, pw_panel, (15, 15, 20, 180), radius=6)
            
            # Draw duration progress line
            total_duration = Settings.POWERUP_TYPES.get(name, {}).get("duration", 10.0)
            pw_pct = min(1.0, max(0.0, duration / total_duration))
            pw_color = Settings.POWERUP_TYPES.get(name, {}).get("color", Settings.COLOR_GOLD)
            
            # Draw visual filled border overlay
            border_w = int(200 * pw_pct)
            if border_w > 0:
                pygame.draw.rect(surface, pw_color, (self.width - 220, pw_y + 28, border_w, 4), border_radius=2)
                
            # Powerup label
            p_text = f"{name.upper()}: {duration:.1f}s"
            p_surf = font_sm.render(p_text, True, pw_color)
            surface.blit(p_surf, (self.width - 210, pw_y + 6))
            
            pw_y += 40

    def draw_boss_health(self, surface: pygame.Surface, health: float, max_health: float, name: str, font: pygame.font.Font) -> None:
        """Renders huge health banner at the center top during active Boss encounters."""
        bar_w = 600
        bar_h = 24
        bar_x = (self.width - bar_w) // 2
        bar_y = 75
        
        # Red warning background outline
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        Utils.draw_rounded_rect(surface, bg_rect, Settings.COLOR_DARK_GRAY, radius=6)
        
        pct = min(1.0, max(0.0, health / max_health))
        if pct > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, int(bar_w * pct), bar_h)
            Utils.draw_rounded_rect(surface, fill_rect, Settings.COLOR_RED, radius=6)
            
        # Draw boss title centered
        title_text = f"BOSS: {name.upper()}"
        t_surf = font.render(title_text, True, Settings.COLOR_RED)
        surface.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, bar_y - 28))
        
        # Visual glowing borders on boss health
        pygame.draw.rect(surface, Settings.COLOR_RED, bg_rect, 2, border_radius=6)

    def draw_minimap(self, surface: pygame.Surface, snake: Any, foods: List[Any], powerups: List[Any], enemies: List[Any], boss: Any) -> None:
        """Renders square glassmorphic radar/minimap at bottom-right HUD to cover the full arena."""
        # Minimap dimensions & placement (bottom-right with 15px margins)
        size = 130
        mx = self.width - size - 15
        my = self.height - size - 15
        
        # 1. Draw radar square background panel
        mini_rect = pygame.Rect(mx, my, size, size)
        Utils.draw_rounded_rect(surface, mini_rect, (15, 15, 25, 200), radius=8)
        Utils.draw_rounded_rect(surface, mini_rect, Settings.COLOR_CYAN, radius=8, border_width=2)
        
        # Draw radial crosshair lines
        pygame.draw.line(surface, (0, 240, 255, 45), (mx + size // 2, my), (mx + size // 2, my + size), 1)
        pygame.draw.line(surface, (0, 240, 255, 45), (mx, my + size // 2), (mx + size, my + size // 2), 1)
        
        # Math scales maps world coordinate (wx, wy) into local map space (lx, ly)
        # World space dimensions are Settings.SCREEN_WIDTH x Settings.SCREEN_HEIGHT
        rx = size / Settings.SCREEN_WIDTH
        ry = size / Settings.SCREEN_HEIGHT
        
        def map_coords(wx: float, wy: float) -> Tuple[int, int]:
            lx = mx + int(wx * rx)
            ly = my + int(wy * ry)
            # Clamp inside minimap box just in case
            lx = max(mx + 2, min(mx + size - 2, lx))
            ly = max(my + 2, min(my + size - 2, ly))
            return lx, ly

        # 2. Draw Food Items on Minimap
        for f in foods:
            lx, ly = map_coords(f.x, f.y)
            pygame.draw.circle(surface, f.color, (lx, ly), 2)
                
        # 3. Draw Powerups on Minimap
        for p in powerups:
            lx, ly = map_coords(p.x, p.y)
            pygame.draw.circle(surface, Settings.COLOR_GOLD, (lx, ly), 3)
                
        # 4. Draw Enemies on Minimap
        for e in enemies:
            lx, ly = map_coords(e.x, e.y)
            # Custom color for AI vs normal enemy
            color = getattr(e, "color", Settings.COLOR_RED)
            pygame.draw.circle(surface, color, (lx, ly), 2.5)
                
        # 5. Draw Boss on Minimap
        if boss:
            lx, ly = map_coords(boss.x, boss.y)
            pulse_r = int(5.0 + 2.0 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(surface, Settings.COLOR_ORANGE, (lx, ly), pulse_r)
                
        # 6. Draw Player Snake on Minimap
        # Draw tail segments
        for seg in snake.path[::10]:
            lx, ly = map_coords(seg[0], seg[1])
            pygame.draw.circle(surface, Settings.COLOR_CYAN, (lx, ly), 1.5)
        # Draw head
        lx, ly = map_coords(snake.x, snake.y)
        pygame.draw.circle(surface, Settings.COLOR_WHITE, (lx, ly), 3)
