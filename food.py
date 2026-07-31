"""
food.py - Specialized food items, spawn/hover animations, custom glows, and spectral properties.
"""
import random
import math
import pygame
from typing import Tuple, Dict, Any
from settings import Settings
from utils import Utils
from particles import ParticleManager

class Food:
    def __init__(self, x: float, y: float, food_type: str) -> None:
        self.x = x
        self.y = y
        self.type = food_type
        
        # Load type configuration from settings
        config = Settings.FOOD_TYPES.get(food_type, Settings.FOOD_TYPES["Normal"])
        self.color: Tuple[int, int, int] = config["color"]
        self.score_value: int = config["score"]
        self.glow_radius: int = config["glow"]
        
        # Size specs
        self.base_radius: float = 8.0
        self.radius: float = 0.0  # Starts at 0 for spawn scale-in
        self.target_radius: float = self.base_radius
        
        # Timers and animations
        self.pulse_timer: float = random.uniform(0.0, 5.0)
        self.spawn_progress: float = 0.0
        self.is_collected: bool = False
        
        # Bomb food countdown timer
        self.bomb_timer: float = 6.0 if food_type == "Bomb" else 0.0
        
        # Rainbow food hue cycle
        self.hue_shift: float = 0.0

    def update(self, dt: float, particles: ParticleManager) -> bool:
        """Updates animation cycles (spawning scale, hover bobbing, pulse). Returns False if bomb exploded."""
        # 1. Spawn Scale Animation
        if self.spawn_progress < 1.0:
            self.spawn_progress = min(1.0, self.spawn_progress + 4.0 * dt)
            self.radius = self.base_radius * self.spawn_progress
            
            # Spawn burst particle trail
            if random.random() < 0.2:
                particles.spawn_trail((self.x, self.y), self.color, self.radius)
        else:
            # 2. Hover Bobbing & Pulsing
            self.pulse_timer += 4.0 * dt
            pulse_offset = 2.0 * math.sin(self.pulse_timer)
            self.radius = self.base_radius + pulse_offset
            
        # 3. Dynamic Visual Types
        if self.type == "Rainbow":
            # Cycle colors
            self.hue_shift = (self.hue_shift + 120.0 * dt) % 360.0
            # Convert HSV to RGB (simplified inline for pygame)
            hue_rad = math.radians(self.hue_shift)
            r = int(127 + 127 * math.sin(hue_rad))
            g = int(127 + 127 * math.sin(hue_rad + 2.0*math.pi/3.0))
            b = int(127 + 127 * math.sin(hue_rad + 4.0*math.pi/3.0))
            self.color = (r, g, b)
            
            # Magic particles emitter
            if random.random() < 0.15:
                particles.spawn_magic((self.x, self.y), self.color, count=1)
                
        elif self.type == "Golden":
            if random.random() < 0.1:
                particles.spawn_magic((self.x, self.y), Settings.COLOR_GOLD, count=1)
                
        elif self.type == "Bomb":
            self.bomb_timer -= dt
            # Flash bomb red rapidly if expiring
            if self.bomb_timer < 2.0:
                flash_speed = 15.0 if self.bomb_timer < 1.0 else 7.0
                flash = int(127 + 127 * math.sin(self.pulse_timer * flash_speed))
                self.color = (flash, 20, 20)
            else:
                self.color = Settings.COLOR_RED
                
            if self.bomb_timer <= 0.0:
                # Trigger explosion (causes screen shake/damage handled in Game class)
                particles.spawn_explosion((self.x, self.y), Settings.COLOR_RED, count=25)
                particles.spawn_smoke((self.x, self.y), count=6)
                return False
                
        elif self.type == "Poison":
            # Swirling dark dots particles
            if random.random() < 0.08:
                particles.spawn_trail((self.x, self.y), Settings.COLOR_BLOOD_RED, 3)

        return True

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders the custom glow halo and the primary core shape."""
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
        glow_rad = int(self.glow_radius * (1.0 + 0.1 * math.sin(self.pulse_timer)))
        if glow_rad > 0:
            Utils.draw_glow_circle(surface, (px, py), radius, self.color, intensity=100, layers=3)
            
        # Draw core graphic based on food type
        if self.type == "Mystery Box":
            # Draw spinning orange diamond box
            box_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            angle = self.pulse_timer * 0.5
            points = []
            for i in range(4):
                theta = angle + i * (math.pi / 2.0)
                tx = radius + radius * math.cos(theta)
                ty = radius + radius * math.sin(theta)
                points.append((tx, ty))
            pygame.draw.polygon(box_surf, self.color, points)
            pygame.draw.polygon(box_surf, Settings.COLOR_WHITE, points, 1)
            surface.blit(box_surf, (px - radius, py - radius))
            
        elif self.type == "Bomb":
            # Draw black circular bomb core with fuse spark
            pygame.draw.circle(surface, (20, 20, 25), (px, py), radius)
            pygame.draw.circle(surface, self.color, (px, py), radius, 2)
            # Fuse line drawing
            fuse_end = (px + radius, py - radius)
            pygame.draw.line(surface, Settings.COLOR_GRAY, (px, py - radius + 2), fuse_end, 2)
            # Spark fire particle at end
            spark_r = int(3 + random.uniform(-1, 1))
            pygame.draw.circle(surface, Settings.COLOR_GOLD, fuse_end, spark_r)
            
        elif self.type == "Poison":
            # Draw skull-like crossbones shape
            pygame.draw.circle(surface, self.color, (px, py), radius)
            pygame.draw.line(surface, (10, 10, 15), (px - radius, py), (px + radius, py), 2)
            pygame.draw.line(surface, (10, 10, 15), (px, py - radius), (px, py + radius), 2)
            
        elif self.type == "Teleport":
            # Draw a portal/spiral ring shape
            for i in range(3):
                offset_r = int(radius * (1.0 - i * 0.3))
                if offset_r > 0:
                    pygame.draw.circle(surface, self.color if i % 2 == 0 else Settings.COLOR_WHITE, (px, py), offset_r, 2)
            
        elif self.type == "Golden":
            # Draw a 5-pointed star
            points = []
            for i in range(10):
                r = radius if i % 2 == 0 else radius // 2
                theta = i * (math.pi / 5.0) - (math.pi / 2.0)
                points.append((px + r * math.cos(theta), py + r * math.sin(theta)))
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, Settings.COLOR_WHITE, points, 1)
            
        elif self.type == "Rainbow":
            # Concentric multi-color circles
            colors = [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,255,255), (0,0,255), (139,0,255)]
            for i, col in enumerate(colors):
                r_sub = int(radius * (1.0 - i * 0.13))
                if r_sub > 0:
                    pygame.draw.circle(surface, col, (px, py), r_sub)
                    
        elif self.type == "Frozen":
            # Draw a snowflake crystal
            pygame.draw.circle(surface, self.color, (px, py), radius, 1)
            pygame.draw.line(surface, Settings.COLOR_WHITE, (px - radius, py), (px + radius, py), 2)
            pygame.draw.line(surface, Settings.COLOR_WHITE, (px, py - radius), (px, py + radius), 2)
            pygame.draw.line(surface, Settings.COLOR_WHITE, (px - radius*0.7, py - radius*0.7), (px + radius*0.7, py + radius*0.7), 2)
            pygame.draw.line(surface, Settings.COLOR_WHITE, (px - radius*0.7, py + radius*0.7), (px + radius*0.7, py - radius*0.7), 2)
            
        elif self.type == "Ghost":
            # Draw ghost body
            points = [
                (px - radius, py + radius),
                (px - radius, py - radius // 2),
                (px - radius // 2, py - radius),
                (px + radius // 2, py - radius),
                (px + radius, py - radius // 2),
                (px + radius, py + radius),
                (px + radius // 2, py + radius // 2),
                (px, py + radius),
                (px - radius // 2, py + radius // 2)
            ]
            pygame.draw.polygon(surface, self.color, points)
            # Eyes
            pygame.draw.circle(surface, (0, 0, 0), (px - 3, py - 2), 2)
            pygame.draw.circle(surface, (0, 0, 0), (px + 3, py - 2), 2)
            
        elif self.type == "Lucky":
            # Four-leaf clover
            offset = radius // 2
            pygame.draw.circle(surface, self.color, (px - offset, py), offset + 1)
            pygame.draw.circle(surface, self.color, (px + offset, py), offset + 1)
            pygame.draw.circle(surface, self.color, (px, py - offset), offset + 1)
            pygame.draw.circle(surface, self.color, (px, py + offset), offset + 1)
            # Stem
            pygame.draw.line(surface, self.color, (px, py), (px + radius, py + radius), 2)
            
        else:
            # Normal: Red apple-like shape with leaf
            pygame.draw.circle(surface, self.color, (px, py), radius)
            # Highlight
            pygame.draw.circle(surface, Settings.COLOR_WHITE, (px - int(radius*0.3), py - int(radius*0.3)), int(radius*0.2))
            # Green leaf
            pygame.draw.line(surface, (0, 255, 100), (px, py - radius), (px + 4, py - radius - 5), 2)

    def on_eat(self, particles: ParticleManager) -> None:
        """Triggered when the player digests this item. Spawns custom burst graphics."""
        self.is_collected = True
        
        # Explosion bursts matching type color
        particles.spawn_explosion((self.x, self.y), self.color, count=12)
        if self.type == "Golden":
            particles.spawn_coin_burst((self.x, self.y), count=16)
        elif self.type == "Rainbow":
            particles.spawn_magic((self.x, self.y), self.color, count=15)
        elif self.type == "Lucky":
            particles.spawn_magic((self.x, self.y), Settings.COLOR_GREEN, count=12)
