"""
camera.py - Handles viewport scroll offsets, smooth player tracking, and zoom matrices.
"""
import pygame
from typing import Tuple, List
from utils import Utils
from settings import Settings

class Camera:
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width = screen_width
        self.height = screen_height
        
        # World tracking position
        self.x: float = Settings.SCREEN_WIDTH / 2.0
        self.y: float = Settings.SCREEN_HEIGHT / 2.0
        
        # Zoom scale factor
        self.zoom: float = 1.0
        self.target_zoom: float = 1.0
        self.zoom_speed: float = 2.0
        
        # Follow settings
        self.lerp_speed: float = 6.0
        
        # Grid boundaries
        self.min_x: float = 0.0
        self.max_x: float = float(Settings.SCREEN_WIDTH)
        self.min_y: float = 0.0
        self.max_y: float = float(Settings.SCREEN_HEIGHT)
        
    def reset(self, target_x: float, target_y: float) -> None:
        """Resets camera position and zoom instantly to target coordinates."""
        self.x = target_x
        self.y = target_y
        self.zoom = 1.0
        self.target_zoom = 1.0

    def update(self, target_x: float, target_y: float, dt: float) -> None:
        """Interpolates camera coordinates towards the target focus point, updating zoom scale."""
        # Lerp position towards target
        self.x = Utils.lerp(self.x, target_x, self.lerp_speed * dt)
        self.y = Utils.lerp(self.y, target_y, self.lerp_speed * dt)
        
        # Lerp zoom towards target zoom
        self.zoom = Utils.lerp(self.zoom, self.target_zoom, self.zoom_speed * dt)
        
    def set_zoom(self, val: float) -> None:
        """Sets the target zoom level to interpolate towards."""
        self.target_zoom = max(0.6, min(1.8, val))

    def get_offset(self, shake_offset: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """
        Calculates top-left coordinate offsets needed to translate world positions
        to screen space, taking zoom and screenshake into account.
        """
        # Offset calculates: camera tracking center minus screen half dimensions
        ox = self.x - (self.width / 2.0) / self.zoom - shake_offset[0]
        oy = self.y - (self.height / 2.0) / self.zoom - shake_offset[1]
        return (ox, oy)

    def to_screen(self, world_x: float, world_y: float, shake_offset: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """Converts a coordinate from absolute world space to screen coordinates, applying zoom and shake."""
        ox, oy = self.get_offset(shake_offset)
        sx = (world_x - ox) * self.zoom
        sy = (world_y - oy) * self.zoom
        return (sx, sy)

    def to_world(self, screen_x: float, screen_y: float, shake_offset: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """Converts a screen coordinate (e.g. mouse position) back to world coordinates."""
        ox, oy = self.get_offset(shake_offset)
        wx = ox + screen_x / self.zoom
        wy = oy + screen_y / self.zoom
        return (wx, wy)

    def draw_parallax_background(self, surface: pygame.Surface, stars: List[Tuple[float, float, int]], shake_offset: Tuple[float, float] = (0.0, 0.0)) -> None:
        """
        Draws infinite stars or space dust moving at different speed layers (parallax)
        relative to camera movement coordinates.
        """
        # Fill deep space color
        surface.fill(Settings.BG_COLOR)
        
        # Draw parallax layers (0.1x scroll, 0.3x scroll, 0.5x scroll)
        ox, oy = self.get_offset(shake_offset)
        
        for idx, (sx, sy, size) in enumerate(stars):
            # Speed coefficients for parallax effect
            if idx % 3 == 0:
                parallax_factor = 0.15
                color = (70, 70, 95)
            elif idx % 3 == 1:
                parallax_factor = 0.35
                color = (0, 180, 200, 120)
            else:
                parallax_factor = 0.6
                color = (255, 0, 100, 180)
                
            # Scroll coordinates based on parallax factor
            # Wrap around screenspace coordinates to loop infinitely
            wx = (sx - ox * parallax_factor) % self.width
            wy = (sy - oy * parallax_factor) % self.height
            
            if len(color) == 4:
                # Alpha support for glowing stars
                star_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, color, (size, size), size)
                surface.blit(star_surf, (wx - size, wy - size))
            else:
                pygame.draw.circle(surface, color, (int(wx), int(wy)), size)
                
        # Draw game boundaries (neon borders)
        self.draw_world_boundaries(surface, shake_offset)

    def draw_world_boundaries(self, surface: pygame.Surface, shake_offset: Tuple[float, float]) -> None:
        """Draws glowing gridlines indicating level boundaries."""
        # Top-left and bottom-right world boundary corners
        tl_x, tl_y = self.to_screen(self.min_x, self.min_y, shake_offset)
        br_x, br_y = self.to_screen(self.max_x, self.max_y, shake_offset)
        
        w = br_x - tl_x
        h = br_y - tl_y
        
        rect = pygame.Rect(int(tl_x), int(tl_y), int(w), int(h))
        # Draw boundary box
        pygame.draw.rect(surface, Settings.COLOR_PINK, rect, int(max(1.0, 3 * self.zoom)))
        
        # Subtle glowing boundary outline using alpha
        glow_size = int(6 * self.zoom)
        if glow_size > 0:
            glow_rect = pygame.Rect(rect.x - glow_size, rect.y - glow_size, rect.w + glow_size * 2, rect.h + glow_size * 2)
            glow_surf = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 0, 85, 50), (0, 0, glow_rect.w, glow_rect.h), glow_size, border_radius=4)
            surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
