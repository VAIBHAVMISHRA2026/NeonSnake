"""
particles.py - High-performance modular Particle engine for drawing bursts, trails, and sparks.
"""
import random
import math
import pygame
from typing import List, Tuple

class Particle:
    def __init__(
        self, 
        x: float, 
        y: float, 
        vx: float, 
        vy: float, 
        color: Tuple[int, int, int], 
        size: float, 
        life: float, 
        decay: float, 
        shape: str = "circle",
        glow: bool = False
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.start_size = size
        self.life = life  # Duration in seconds
        self.max_life = life
        self.decay = decay  # Speed at which life decreases
        self.shape = shape
        self.glow = glow

    def update(self, dt: float) -> bool:
        """Updates particle mechanics. Returns True if particle is still alive, False if dead."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Friction/drag deceleration
        self.vx *= (1.0 - 0.5 * dt)
        self.vy *= (1.0 - 0.5 * dt)
        
        self.life -= self.decay * dt
        # Shrink size relative to remaining life
        self.size = max(0.5, self.start_size * (self.life / self.max_life))
        
        return self.life > 0.0

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders the individual particle onto the screen, applying camera offset translation."""
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        size = int(self.size)
        
        if size <= 0:
            return
            
        alpha = int(255 * (self.life / self.max_life))
        alpha = max(0, min(255, alpha))
        
        # Draw particle with alpha
        # Standard pygame shapes don't support per-shape alpha unless drawn to custom surface or using rect with custom blend
        if self.glow:
            # Render a soft halo glow
            glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (self.color[0], self.color[1], self.color[2], alpha // 3), (size * 2, size * 2), size * 2)
            pygame.draw.circle(glow_surf, (self.color[0], self.color[1], self.color[2], alpha), (size * 2, size * 2), size)
            surface.blit(glow_surf, (px - size * 2, py - size * 2), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            # Basic drawing, drawing smaller shapes direct is faster
            if alpha >= 250:
                if self.shape == "circle":
                    pygame.draw.circle(surface, self.color, (px, py), size)
                elif self.shape == "square":
                    pygame.draw.rect(surface, self.color, (px - size, py - size, size * 2, size * 2))
            else:
                # Create alpha surface
                p_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                if self.shape == "circle":
                    pygame.draw.circle(p_surf, (self.color[0], self.color[1], self.color[2], alpha), (size, size), size)
                elif self.shape == "square":
                    pygame.draw.rect(p_surf, (self.color[0], self.color[1], self.color[2], alpha), (0, 0, size * 2, size * 2))
                surface.blit(p_surf, (px - size, py - size))

class ParticleManager:
    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self.max_particles: int = 400  # Cap active count to guarantee smooth AAA frame rate

    def clear(self) -> None:
        self.particles.clear()

    def update(self, dt: float) -> None:
        """Updates physics on all active particles, clearing expired instances."""
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders all particles onto screen."""
        for p in self.particles:
            p.draw(surface, camera_offset)

    def add_particle(self, p: Particle) -> None:
        if len(self.particles) < self.max_particles:
            self.particles.append(p)

    def spawn_explosion(self, pos: Tuple[float, float], color: Tuple[int, int, int], count: int = 15) -> None:
        """Spawns radial burst particles (e.g. food eaten, obstacle crash)."""
        x, y = pos
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80.0, 240.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(3.0, 7.0)
            life = random.uniform(0.3, 0.7)
            
            p = Particle(
                x=x, y=y, vx=vx, vy=vy, 
                color=color, size=size, life=life, 
                decay=1.0, shape="circle", glow=(random.random() < 0.3)
            )
            self.add_particle(p)

    def spawn_trail(self, pos: Tuple[float, float], color: Tuple[int, int, int], size: float) -> None:
        """Spawns dynamic linear trail behind moving snake body."""
        x, y = pos
        vx = random.uniform(-10.0, 10.0)
        vy = random.uniform(-10.0, 10.0)
        life = random.uniform(0.2, 0.4)
        
        p = Particle(
            x=x, y=y, vx=vx, vy=vy,
            color=color, size=size * 0.5, life=life,
            decay=1.2, shape="circle", glow=False
        )
        self.add_particle(p)

    def spawn_magic(self, pos: Tuple[float, float], color: Tuple[int, int, int], count: int = 8) -> None:
        """Spawns rising, glowing magical sparks for special items or powerups."""
        x, y = pos
        for _ in range(count):
            vx = random.uniform(-30.0, 30.0)
            vy = random.uniform(-60.0, -10.0)  # Ascending
            size = random.uniform(2.0, 5.0)
            life = random.uniform(0.4, 0.8)
            
            p = Particle(
                x=x + random.uniform(-10, 10), y=y + random.uniform(-10, 10),
                vx=vx, vy=vy, color=color, size=size, life=life,
                decay=1.0, shape="circle", glow=True
            )
            self.add_particle(p)

    def spawn_smoke(self, pos: Tuple[float, float], count: int = 8) -> None:
        """Spawns grey, rising dust/smoke clouds for bombs."""
        x, y = pos
        for _ in range(count):
            vx = random.uniform(-20.0, 20.0)
            vy = random.uniform(-40.0, -10.0)
            size = random.uniform(6.0, 14.0)
            life = random.uniform(0.5, 1.0)
            grey_val = random.randint(80, 140)
            color = (grey_val, grey_val, grey_val)
            
            p = Particle(
                x=x, y=y, vx=vx, vy=vy,
                color=color, size=size, life=life,
                decay=1.0, shape="square", glow=False
            )
            self.add_particle(p)

    def spawn_coin_burst(self, pos: Tuple[float, float], count: int = 12) -> None:
        """Spawns gold starbursts when picking up coins."""
        x, y = pos
        gold_color = (255, 215, 0)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100.0, 200.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(4.0, 8.0)
            life = random.uniform(0.4, 0.6)
            
            p = Particle(
                x=x, y=y, vx=vx, vy=vy,
                color=gold_color, size=size, life=life,
                decay=1.2, shape="circle", glow=True
            )
            self.add_particle(p)
            
    def spawn_sparks(self, pos: Tuple[float, float], color: Tuple[int, int, int], count: int = 10) -> None:
        """Spawns sharp, fast linear sparks (e.g. projectile collisions)."""
        x, y = pos
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(120.0, 300.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2.0, 4.0)
            life = random.uniform(0.2, 0.4)
            
            p = Particle(
                x=x, y=y, vx=vx, vy=vy,
                color=color, size=size, life=life,
                decay=2.0, shape="square", glow=False
            )
            self.add_particle(p)
