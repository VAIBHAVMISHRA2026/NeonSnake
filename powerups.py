"""
powerups.py - Implement active items, shield modifiers, magnetic attraction vectors, and duration timers.
"""
import random
import math
import pygame
from typing import Tuple, Dict, Any
from settings import Settings
from utils import Utils
from particles import ParticleManager

class PowerUp:
    def __init__(self, x: float, y: float, power_type: str) -> None:
        self.x = x
        self.y = y
        self.type = power_type
        
        # Load details from settings
        config = Settings.POWERUP_TYPES.get(power_type, Settings.POWERUP_TYPES["Magnet"])
        self.color: Tuple[int, int, int] = config["color"]
        self.duration: float = config["duration"]
        
        # Animation specs
        self.base_radius: float = 15.0
        self.radius: float = 0.0
        self.target_radius: float = self.base_radius
        
        self.pulse_timer: float = random.uniform(0.0, 5.0)
        self.spawn_progress: float = 0.0
        self.is_collected: bool = False
        
        # Powerup glowing shape rotation angle
        self.angle: float = 0.0

    def update(self, dt: float, particles: ParticleManager) -> None:
        """Handles spawning, rotation, and particle trail emissions."""
        # 1. Scale-in Animation
        if self.spawn_progress < 1.0:
            self.spawn_progress = min(1.0, self.spawn_progress + 3.0 * dt)
            self.radius = self.base_radius * self.spawn_progress
        else:
            # 2. Hover bobbing pulse
            self.pulse_timer += 5.0 * dt
            pulse_offset = 1.5 * math.sin(self.pulse_timer)
            self.radius = self.base_radius + pulse_offset
            
        self.angle += 90.0 * dt  # Degrees per sec
        
        # Emission particles
        if random.random() < 0.12:
            particles.spawn_magic((self.x, self.y), self.color, count=1)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders power-up container with custom icon shape and glowing ring."""
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        radius = int(self.radius)
        
        if radius <= 0:
            return
            
        # Draw high-res sprite if available
        from utils import SpriteManager
        sprite = SpriteManager.get_instance().get_sprite(self.type, radius * 2)
        if sprite is not None:
            surface.blit(sprite, (px - radius, py - radius))
            return

        # Draw neon glow base circle
        Utils.draw_glow_circle(surface, (px, py), radius, self.color, intensity=120, layers=3)
            
        # Draw rotating outline container
        box_w = radius * 2
        box_surf = pygame.Surface((box_w, box_w), pygame.SRCALPHA)
        
        # Draw dynamic rotating polygons based on type
        points = []
        angle_rad = math.radians(self.angle)
        for i in range(4):
            theta = angle_rad + i * (math.pi / 2.0)
            tx = radius + radius * math.cos(theta)
            ty = radius + radius * math.sin(theta)
            points.append((tx, ty))
            
        pygame.draw.polygon(box_surf, (self.color[0], self.color[1], self.color[2], 120), points)
        pygame.draw.polygon(box_surf, Settings.COLOR_WHITE, points, 2)
        
        # Draw center powerup symbol
        self._draw_symbol(box_surf, radius, radius)
        
        surface.blit(box_surf, (px - radius, py - radius))

    def _draw_symbol(self, surf: pygame.Surface, cx: int, cy: int) -> None:
        """Draws clean, bold icon shapes representing each powerup type."""
        col = Settings.COLOR_WHITE
        
        if self.type == "Magnet":
            # Horseshoe Magnet icon shape (U-shape)
            pygame.draw.rect(surf, (220, 40, 40), (cx - 6, cy - 8, 4, 10))
            pygame.draw.rect(surf, (220, 40, 40), (cx + 2, cy - 8, 4, 10))
            pygame.draw.rect(surf, (220, 40, 40), (cx - 6, cy + 2, 12, 4))
            pygame.draw.rect(surf, Settings.COLOR_WHITE, (cx - 6, cy - 10, 4, 3))
            pygame.draw.rect(surf, Settings.COLOR_WHITE, (cx + 2, cy - 10, 4, 3))
            
        elif self.type == "Shield":
            # Crest shield icon
            points = [(cx - 7, cy - 7), (cx + 7, cy - 7), (cx + 7, cy - 1), (cx, cy + 9), (cx - 7, cy - 1)]
            pygame.draw.polygon(surf, (30, 160, 255), points)
            pygame.draw.polygon(surf, Settings.COLOR_WHITE, points, 2)
            
        elif self.type == "Double Score":
            # Bold golden "2X" text logo
            # Draw '2'
            pygame.draw.lines(surf, Settings.COLOR_GOLD, False, [(cx - 7, cy - 6), (cx - 2, cy - 6), (cx - 7, cy + 5), (cx - 2, cy + 5)], 3)
            # Draw 'X'
            pygame.draw.line(surf, Settings.COLOR_GOLD, (cx + 2, cy - 5), (cx + 7, cy + 5), 3)
            pygame.draw.line(surf, Settings.COLOR_GOLD, (cx + 7, cy - 5), (cx + 2, cy + 5), 3)
            
        elif self.type == "Slow Motion":
            # Hourglass shape filled with sand
            points_top = [(cx - 5, cy - 8), (cx + 5, cy - 8), (cx, cy)]
            points_bottom = [(cx - 5, cy + 8), (cx + 5, cy + 8), (cx, cy)]
            pygame.draw.polygon(surf, Settings.COLOR_GOLD, points_top)
            pygame.draw.polygon(surf, Settings.COLOR_GOLD, points_bottom)
            pygame.draw.polygon(surf, Settings.COLOR_WHITE, points_top + points_bottom, 2)
            
        elif self.type == "Speed Boost":
            # Yellow lightning bolt
            points = [(cx + 2, cy - 9), (cx - 6, cy + 1), (cx, cy + 1), (cx - 2, cy + 9), (cx + 6, cy - 1), (cx, cy - 1)]
            pygame.draw.polygon(surf, (255, 225, 0), points)
            pygame.draw.polygon(surf, Settings.COLOR_WHITE, points, 1)
            
        elif self.type == "Invincibility":
            # Glowing star shape
            points = []
            for i in range(10):
                r = 10 if i % 2 == 0 else 5
                theta = i * (math.pi / 5.0) - (math.pi / 2.0)
                points.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
            pygame.draw.polygon(surf, (255, 0, 180), points)
            pygame.draw.polygon(surf, Settings.COLOR_WHITE, points, 1.5)
            
        elif self.type == "Freeze Time":
            # Pocket clock shape
            pygame.draw.circle(surf, Settings.COLOR_WHITE, (cx, cy), 8, 2)
            pygame.draw.line(surf, Settings.COLOR_WHITE, (cx, cy), (cx, cy - 5), 2)
            pygame.draw.line(surf, Settings.COLOR_WHITE, (cx, cy), (cx + 4, cy), 2)
            
        elif self.type == "Ghost Mode":
            # Small ghost sprite shape
            points = [
                (cx - 7, cy + 7), (cx - 7, cy - 3), (cx - 4, cy - 7),
                (cx + 4, cy - 7), (cx + 7, cy - 3), (cx + 7, cy + 7),
                (cx + 3, cy + 4), (cx, cy + 7), (cx - 3, cy + 4)
            ]
            pygame.draw.polygon(surf, (180, 180, 200), points)
            pygame.draw.circle(surf, (0, 0, 0), (cx - 2, cy - 2), 1)
            pygame.draw.circle(surf, (0, 0, 0), (cx + 2, cy - 2), 1)
            
        elif self.type == "Teleport":
            # Portal vortex
            pygame.draw.circle(surf, (150, 0, 255), (cx, cy), 8, 3)
            pygame.draw.circle(surf, Settings.COLOR_WHITE, (cx, cy), 4, 2)
            
        elif self.type == "Food Multiplier":
            # Double green leaf sprout
            pygame.draw.circle(surf, (0, 220, 100), (cx - 3, cy + 2), 4)
            pygame.draw.circle(surf, (0, 220, 100), (cx + 3, cy + 2), 4)
            pygame.draw.line(surf, Settings.COLOR_WHITE, (cx, cy - 4), (cx, cy + 6), 2)
            
        else:
            # Random Power (or fallback): Neon Question Mark "?"
            # Draw curve
            pygame.draw.arc(surf, Settings.COLOR_WHITE, (cx - 4, cy - 8, 8, 8), 0, math.pi, 2)
            pygame.draw.line(surf, Settings.COLOR_WHITE, (cx + 4, cy - 4), (cx, cy), 2)
            pygame.draw.line(surf, Settings.COLOR_WHITE, (cx, cy), (cx, cy + 3), 2)
            # Dot
            pygame.draw.circle(surf, Settings.COLOR_WHITE, (cx, cy + 6), 1.5)

    def on_collect(self, particles: ParticleManager) -> None:
        """Triggered when the player eats this power-up."""
        self.is_collected = True
        
        # Explosion bursts matching powerup color
        particles.spawn_explosion((self.x, self.y), self.color, count=16)
        particles.spawn_magic((self.x, self.y), Settings.COLOR_WHITE, count=12)
