"""
enemy.py - Defines standard AI hazards (Ghost Snake, Hunter Snake, Fire Ball) and Boss Fight encounter patterns.
"""
import random
import math
import pygame
from typing import Tuple, List, Dict, Any
from settings import Settings
from utils import Utils
from particles import ParticleManager

class EnemyProjectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, size: float = 6.0, color: Tuple[int, int, int] = Settings.COLOR_RED) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.life: float = 5.0  # Seconds to live

    def update(self, dt: float) -> bool:
        """Moves projectile. Returns True if alive, False if expired."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0.0

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        Utils.draw_glow_circle(surface, (px, py), int(self.size), self.color, intensity=80, layers=2)


class BaseEnemy:
    def __init__(self, x: float, y: float, enemy_type: str) -> None:
        self.x = x
        self.y = y
        self.type = enemy_type
        self.color = Settings.COLOR_RED
        self.is_dead: bool = False
        self.size: float = 12.0

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        pass

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2.0, self.size * 2.0)


class Spikes(BaseEnemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, "Spikes")
        self.color = Settings.COLOR_ORANGE
        self.angle: float = 0.0
        self.size = 14.0

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        self.angle += 45.0 * dt  # Spin spikes slowly

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        r = int(self.size)
        
        # Draw spikes gear look procedurally
        points = []
        num_spikes = 8
        for i in range(num_spikes * 2):
            theta = math.radians(self.angle) + i * (math.pi / num_spikes)
            dist = r if (i % 2 == 0) else r - 6
            tx = px + dist * math.cos(theta)
            ty = py + dist * math.sin(theta)
            points.append((tx, ty))
            
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, Settings.COLOR_WHITE, points, 1)


class MovingBomb(BaseEnemy):
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, "Moving Bomb")
        self.vx = vx
        self.vy = vy
        self.color = Settings.COLOR_RED
        self.size = 12.0
        self.pulse_timer: float = 0.0

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Screen bouncing bounds
        if self.x - self.size < 0:
            self.x = self.size
            self.vx *= -1
            particles.spawn_sparks((self.x, self.y), self.color, count=4)
        elif self.x + self.size > Settings.SCREEN_WIDTH:
            self.x = Settings.SCREEN_WIDTH - self.size
            self.vx *= -1
            particles.spawn_sparks((self.x, self.y), self.color, count=4)
            
        if self.y - self.size < 0:
            self.y = self.size
            self.vy *= -1
            particles.spawn_sparks((self.x, self.y), self.color, count=4)
        elif self.y + self.size > Settings.SCREEN_HEIGHT:
            self.y = Settings.SCREEN_HEIGHT - self.size
            self.vy *= -1
            particles.spawn_sparks((self.x, self.y), self.color, count=4)
            
        self.pulse_timer += 8.0 * dt
        if random.random() < 0.1:
            particles.spawn_trail((self.x, self.y), self.color, self.size * 0.5)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        r = int(self.size + 2.0 * math.sin(self.pulse_timer))
        
        # Red pulsing circle bomb
        Utils.draw_glow_circle(surface, (px, py), r, self.color, intensity=90, layers=2)
        pygame.draw.circle(surface, Settings.BG_COLOR, (px, py), r - 4)
        # Inner ticking dot
        pygame.draw.circle(surface, self.color, (px, py), 4)


class HunterSnake(BaseEnemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, "Hunter Snake")
        self.color = Settings.COLOR_PURPLE
        self.size = 11.0
        self.speed = 100.0
        
        # AI coordinates history to render a small trail/segments
        self.segments: List[Tuple[float, float]] = [(x, y)]
        self.max_segments: int = 8

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        # Move towards player coordinates slowly
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 5.0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            
        # Append history
        self.segments.insert(0, (self.x, self.y))
        if len(self.segments) > self.max_segments:
            self.segments.pop()
            
        if random.random() < 0.08:
            particles.spawn_trail((self.x, self.y), self.color, 4)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        # Draw segmented tail body
        for idx, (sx, sy) in enumerate(reversed(self.segments)):
            px = int(sx - camera_offset[0])
            py = int(sy - camera_offset[1])
            alpha = int(255 * ((idx + 1) / len(self.segments)))
            r = int(self.size * (0.5 + 0.5 * (idx / len(self.segments))))
            
            # Simple transparent overlay circle
            color_alpha = (self.color[0], self.color[1], self.color[2], alpha)
            p_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, color_alpha, (r, r), r)
            surface.blit(p_surf, (px - r, py - r))
            
        # Red glowing tracking eyes on head
        if len(self.segments) > 0:
            hx = int(self.x - camera_offset[0])
            hy = int(self.y - camera_offset[1])
            pygame.draw.circle(surface, Settings.COLOR_WHITE, (hx - 4, hy - 4), 3)
            pygame.draw.circle(surface, Settings.COLOR_RED, (hx - 4, hy - 4), 1)
            pygame.draw.circle(surface, Settings.COLOR_WHITE, (hx + 4, hy - 4), 3)
            pygame.draw.circle(surface, Settings.COLOR_RED, (hx + 4, hy - 4), 1)


class LaserWall(BaseEnemy):
    def __init__(self, is_horizontal: bool, offset_coord: float) -> None:
        # If horizontal, offset_coord is Y line; if vertical, offset_coord is X line
        super().__init__(0, 0, "Laser Wall")
        self.is_horizontal = is_horizontal
        self.coord = offset_coord
        self.color = Settings.COLOR_PINK
        
        # State machine timers
        # Laser fires for 1.5 seconds, cools down for 4.5 seconds
        self.cycle_timer: float = 0.0
        self.is_firing: bool = False
        self.warning_alpha: int = 0
        self.laser_width: float = 0.0

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        self.cycle_timer += dt
        cycle_dur = 6.0
        time_in_cycle = self.cycle_timer % cycle_dur
        
        # Timings
        # 0.0s - 3.0s: Warn Player
        # 3.0s - 4.5s: Fire Laser Beam
        # 4.5s - 6.0s: Cooldown
        if time_in_cycle < 3.0:
            self.is_firing = False
            # Pulse warning line alpha
            self.warning_alpha = int(127 + 127 * math.sin(time_in_cycle * 12.0))
        elif 3.0 <= time_in_cycle < 4.5:
            if not self.is_firing:
                self.is_firing = True
                
            # Laser beams expands/decays
            fire_t = time_in_cycle - 3.0
            if fire_t < 0.15:
                self.laser_width = Utils.lerp(0.0, 16.0, fire_t / 0.15)
            elif fire_t > 1.35:
                self.laser_width = Utils.lerp(16.0, 0.0, (fire_t - 1.35) / 0.15)
            else:
                self.laser_width = 16.0
                
            # Sparks smoke trails
            if random.random() < 0.3:
                rx = random.uniform(0, Settings.SCREEN_WIDTH) if self.is_horizontal else self.coord
                ry = self.coord if self.is_horizontal else random.uniform(0, Settings.SCREEN_HEIGHT)
                particles.spawn_sparks((rx, ry), self.color, count=2)
        else:
            self.is_firing = False
            self.warning_alpha = 0
            self.laser_width = 0.0

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        # Draw warning line
        if self.warning_alpha > 0 and not self.is_firing:
            line_surf = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            if self.is_horizontal:
                y = int(self.coord - camera_offset[1])
                # Draw dashed line
                for x in range(0, Settings.SCREEN_WIDTH, 20):
                    pygame.draw.line(line_surf, (255, 0, 85, self.warning_alpha), (x, y), (x + 10, y), 2)
            else:
                x = int(self.coord - camera_offset[0])
                for y in range(0, Settings.SCREEN_HEIGHT, 20):
                    pygame.draw.line(line_surf, (255, 0, 85, self.warning_alpha), (x, y), (x, y + 10), 2)
            surface.blit(line_surf, (0, 0))
            
        # Draw active laser beam
        if self.is_firing and self.laser_width > 0.1:
            lw = int(self.laser_width)
            laser_surf = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            
            if self.is_horizontal:
                y = int(self.coord - camera_offset[1])
                # Draw thick glowing beam
                pygame.draw.line(laser_surf, (255, 0, 85, 100), (0, y), (Settings.SCREEN_WIDTH, y), lw + 8)
                pygame.draw.line(laser_surf, (255, 255, 255, 255), (0, y), (Settings.SCREEN_WIDTH, y), lw)
            else:
                x = int(self.coord - camera_offset[0])
                pygame.draw.line(laser_surf, (255, 0, 85, 100), (x, 0), (x, Settings.SCREEN_HEIGHT), lw + 8)
                pygame.draw.line(laser_surf, (255, 255, 255, 255), (x, 0), (x, Settings.SCREEN_HEIGHT), lw)
                
            surface.blit(laser_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def collides_with_point(self, pt: Tuple[float, float]) -> bool:
        """Returns True if laser fires and coordinates intersect the thickness area."""
        if not self.is_firing or self.laser_width < 4.0:
            return False
            
        px, py = pt
        half_w = self.laser_width / 2.0
        
        if self.is_horizontal:
            return abs(py - self.coord) <= half_w
        else:
            return abs(px - self.coord) <= half_w


# BOSS BOSS STATE ENEMY
class BossEnemy(BaseEnemy):
    def __init__(self, level: int) -> None:
        super().__init__(Settings.SCREEN_WIDTH / 2.0, 180.0, "Boss Core")
        self.level = level
        self.name = f"Viper Mech V{level // 10}"
        
        # Difficulty adjusts health
        diff = Settings.DIFFICULTIES.get("Medium", {}) # defaults
        hm = diff.get("boss_health_multiplier", 1.0)
        self.max_health: float = 300.0 * (1.0 + (level // 10) * 0.5) * hm
        self.health: float = self.max_health
        
        self.size = 28.0
        self.color = Settings.COLOR_RED
        
        # Boss custom weapon states
        self.state = "IDLE"  # IDLE, SHOOTING, CHARGING, SHIELDED
        self.state_timer: float = 2.0
        
        self.projectiles: List[EnemyProjectile] = []
        self.attack_timer: float = 0.0
        
        # Rotational indicators
        self.shield_angle: float = 0.0
        self.movement_timer: float = 0.0
        self.target_x = self.x
        self.target_y = self.y

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager) -> None:
        """Updates boss weapon patterns, movement target tracking, and active projectiles."""
        # 1. Update Projectiles
        self.projectiles = [p for p in self.projectiles if p.update(dt)]
        
        # Particles trailing Core
        if random.random() < 0.15:
            particles.spawn_magic((self.x, self.y), self.color, count=2)
            
        # 2. State-driven Combat Pattern Engine
        self.state_timer -= dt
        if self.state_timer <= 0.0:
            # Change state randomly
            states = ["SHOOTING", "CHARGING", "IDLE"]
            if self.health < self.max_health * 0.5:
                states.append("SHIELDED")  # Phase 2 unlock
            self.state = random.choice(states)
            self.state_timer = random.uniform(3.0, 5.0)
            
        # 3. Apply state action details
        self.attack_timer -= dt
        if self.state == "SHOOTING":
            # Fire rapid round projectiles
            fire_rate = 0.4 - (0.05 * (self.level // 10))
            fire_rate = max(0.12, fire_rate)
            if self.attack_timer <= 0.0:
                self.attack_timer = fire_rate
                # Shoot directly towards player
                dx = player_pos[0] - self.x
                dy = player_pos[1] - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 1.0:
                    vx = (dx / dist) * 280.0
                    vy = (dy / dist) * 280.0
                    self.projectiles.append(EnemyProjectile(self.x, self.y, vx, vy, size=7.0))
                    particles.spawn_sparks((self.x, self.y), Settings.COLOR_RED, count=4)
                    
        elif self.state == "CHARGING":
            # Fire radial energy circles
            fire_rate = 1.2
            if self.attack_timer <= 0.0:
                self.attack_timer = fire_rate
                # 8-way fire pattern
                for i in range(8):
                    theta = i * (math.pi / 4.0)
                    vx = math.cos(theta) * 180.0
                    vy = math.sin(theta) * 180.0
                    self.projectiles.append(EnemyProjectile(self.x, self.y, vx, vy, size=6.0, color=Settings.COLOR_ORANGE))
                particles.spawn_explosion((self.x, self.y), Settings.COLOR_ORANGE, count=10)
                
        elif self.state == "SHIELDED":
            # Spins energy shield
            self.shield_angle += 180.0 * dt
            # Slowly regenerate small health
            self.health = min(self.max_health, self.health + 2.0 * dt)
            
        # 4. Movement Logic
        self.movement_timer -= dt
        if self.movement_timer <= 0.0:
            self.movement_timer = random.uniform(1.5, 3.0)
            # Random position inside core grid arena boundaries
            self.target_x = random.uniform(150.0, Settings.SCREEN_WIDTH - 150.0)
            self.target_y = random.uniform(100.0, 320.0)  # Top half of board only
            
        # Smoothly slide towards targets
        self.x = Utils.lerp(self.x, self.target_x, 2.0 * dt)
        self.y = Utils.lerp(self.y, self.target_y, 2.0 * dt)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders boss core graphics and dynamic orbital energy layers."""
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        r = int(self.size)
        
        # Draw all active projectiles first
        for p in self.projectiles:
            p.draw(surface, camera_offset)
            
        # Glowing base
        color = Settings.COLOR_PINK if self.state == "CHARGING" else self.color
        Utils.draw_glow_circle(surface, (px, py), r, color, intensity=130, layers=3)
        
        # Steel metal capsule core
        pygame.draw.circle(surface, Settings.COLOR_DARK_GRAY, (px, py), r - 4)
        pygame.draw.circle(surface, Settings.COLOR_WHITE, (px, py), r - 10, 2)
        
        # Pulsing center eye light
        eye_pulse = int(5 + 3 * math.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.circle(surface, color, (px, py), eye_pulse)
        
        # Shield orbital graphics
        if self.state == "SHIELDED":
            # Draw semi-transparent shield circle around Core
            shield_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 240, 255, 60), (r * 2, r * 2), r + 15)
            pygame.draw.circle(shield_surf, Settings.COLOR_CYAN, (r * 2, r * 2), r + 15, 2)
            
            # Spin two dots around ring outline
            for i in range(3):
                theta = math.radians(self.shield_angle) + i * (2.0 * math.pi / 3.0)
                dx = int(r*2 + (r + 15) * math.cos(theta))
                dy = int(r*2 + (r + 15) * math.sin(theta))
                pygame.draw.circle(shield_surf, Settings.COLOR_WHITE, (dx, dy), 5)
                
            surface.blit(shield_surf, (px - r * 2, py - r * 2))

    def take_damage(self, amount: float, particles: ParticleManager) -> bool:
        """Inflicts damage on boss. Returns True if dead."""
        # Reduce damage if shielded
        if self.state == "SHIELDED":
            amount *= 0.2
            self.health -= amount
            particles.spawn_sparks((self.x, self.y), Settings.COLOR_CYAN, count=8)
        else:
            self.health -= amount
            particles.spawn_explosion((self.x, self.y), Settings.COLOR_RED, count=6)
            
        self.health = max(0.0, self.health)
        
        if self.health <= 0.0:
            self.is_dead = True
            # Super explosion particle trigger
            particles.spawn_explosion((self.x, self.y), Settings.COLOR_RED, count=45)
            particles.spawn_smoke((self.x, self.y), count=15)
            return True
        return False


class AISnakeEnemy(BaseEnemy):
    def __init__(self, x: float, y: float, level: int) -> None:
        super().__init__(x, y, 12.0)
        self.length = 6 + int(level * 0.5)
        self.angle = random.uniform(0, 2.0 * math.pi)
        self.target_angle = self.angle
        self.speed = 100.0 + min(50.0, level * 2.0)
        self.turn_speed = 3.5
        self.path: List[Tuple[float, float]] = [(x, y)] * (self.length * 10)
        
        # Pick random neon skin color
        colors = [
            (0, 255, 200),  # Cyan-green
            (255, 0, 180),  # Pink
            (180, 0, 255),  # Purple
            (255, 180, 0),  # Gold/Orange
            (0, 200, 255)   # Light Blue
        ]
        self.color = random.choice(colors)
        self.is_dead = False
        
        # Wander timer
        self.wander_timer = 0.0
        
        # Powerup timers
        self.powerup_timers: Dict[str, float] = {}
        self.speed_boost_active = False
        self.shield_active = False
        self.invincible_active = False
        self.magnet_active = False

    def update(self, player_pos: Tuple[float, float], dt: float, particles: ParticleManager, foods: List[Any] = None, powerups: List[Any] = None) -> None:
        """Updates AI path navigation tracking food, powerups, or player, check collisions with items."""
        if dt <= 0.0:
            return
            
        # Update active powerup timers
        if not hasattr(self, "powerup_timers"):
            self.powerup_timers = {}
        for k in list(self.powerup_timers.keys()):
            self.powerup_timers[k] -= dt
            if self.powerup_timers[k] <= 0:
                del self.powerup_timers[k]
                
        self.speed_boost_active = "Speed Boost" in self.powerup_timers
        self.shield_active = "Shield" in self.powerup_timers
        self.invincible_active = "Invincibility" in self.powerup_timers or "Ghost Mode" in self.powerup_timers
        self.magnet_active = "Magnet" in self.powerup_timers
        
        # Adjust current speed
        current_speed = self.speed
        if self.speed_boost_active:
            current_speed *= 1.6
            
        # 1. AI Decision Making: target closest food, powerup or wander
        target_found = False
        closest_dist = 9999.0
        tx, ty = self.x, self.y
        
        # Target close powerups first (valuable!)
        if powerups:
            for p in powerups:
                dist = Utils.distance((self.x, self.y), (p.x, p.y))
                if dist < closest_dist and dist < 350.0:
                    closest_dist = dist
                    tx, ty = p.x, p.y
                    target_found = True
                    
        # Otherwise target closest food
        if not target_found and foods:
            for f in foods:
                dist = Utils.distance((self.x, self.y), (f.x, f.y))
                if dist < closest_dist and f.type not in ["Poison", "Bomb"]:
                    closest_dist = dist
                    tx, ty = f.x, f.y
                    target_found = True
                    
        if target_found and closest_dist < 400.0:
            # Head towards target
            self.target_angle = math.atan2(ty - self.y, tx - self.x)
        else:
            # Wander around
            self.wander_timer -= dt
            if self.wander_timer <= 0.0:
                self.wander_timer = random.uniform(1.0, 2.5)
                self.target_angle += random.uniform(-1.2, 1.2)
                
        # 2. Smoothly steer towards target_angle
        diff = (self.target_angle - self.angle + math.pi) % (2.0 * math.pi) - math.pi
        step = math.copysign(self.turn_speed * dt, diff)
        if abs(step) > abs(diff):
            self.angle = self.target_angle
        else:
            self.angle += step
            
        # 3. Move forward using current_speed
        self.x += math.cos(self.angle) * current_speed * dt
        self.y += math.sin(self.angle) * current_speed * dt
        
        # 4. Out of bounds safety bounce
        margin = 60.0
        if self.x < margin or self.x > Settings.SCREEN_WIDTH - margin or self.y < margin or self.y > Settings.SCREEN_HEIGHT - margin:
            self.target_angle = math.atan2(Settings.SCREEN_HEIGHT / 2.0 - self.y, Settings.SCREEN_WIDTH / 2.0 - self.x)
            
        # 5. Record path history
        self.path.insert(0, (self.x, self.y))
        max_path_len = self.length * 10
        if len(self.path) > max_path_len:
            self.path = self.path[:max_path_len]
            
        # 6. Check food collisions (AI can eat!)
        if foods:
            for f in list(foods):
                dist = Utils.distance((self.x, self.y), (f.x, f.y))
                if dist < (self.size + f.radius):
                    # Eat it!
                    f.on_eat(particles)
                    if f in foods:
                        foods.remove(f)
                    self.grow(1)
                    particles.spawn_explosion((self.x, self.y), self.color, count=8)
                    
        # 7. Check powerup collisions (AI can collect and use powerups!)
        if powerups:
            for p in list(powerups):
                dist = Utils.distance((self.x, self.y), (p.x, p.y))
                if dist < (self.size + p.radius):
                    p.on_collect(particles)
                    if p in powerups:
                        powerups.remove(p)
                    # Activate powerup for AI
                    dur = p.duration
                    if p.type == "Random Power":
                        chosen = random.choice(["Speed Boost", "Shield", "Magnet", "Invincibility"])
                        self.powerup_timers[chosen] = 8.0
                    else:
                        self.powerup_timers[p.type] = dur
                    particles.spawn_explosion((self.x, self.y), p.color, count=15)

    def grow(self, amount: int = 1) -> None:
        self.length += amount
        for _ in range(amount * 10):
            self.path.append(self.path[-1])

    def die(self, foods_list: List[Any], particles: ParticleManager) -> None:
        """Explodes the AI snake into multiple food items along its length."""
        self.is_dead = True
        particles.spawn_explosion((self.x, self.y), self.color, count=25)
        # Spawn food items along body segments
        segment_indices = [i * 10 for i in range(self.length)]
        for idx in segment_indices:
            if idx < len(self.path):
                px, py = self.path[idx]
                # Avoid spawning out of bounds
                px = max(40.0, min(Settings.SCREEN_WIDTH - 40.0, px))
                py = max(40.0, min(Settings.SCREEN_HEIGHT - 40.0, py))
                # Only spawn sometimes to avoid flooding the screen
                if random.random() < 0.5:
                    from food import Food
                    foods_list.append(Food(px, py, "Normal"))

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Renders AI snake segments with gradient scaling and eyes."""
        # 1. Extract segment coordinates
        segments = []
        for i in range(self.length):
            idx = i * 10
            if idx < len(self.path):
                segments.append(self.path[idx])
            else:
                segments.append(self.path[-1])
                
        # 2. Draw segments from tail to head
        for idx in reversed(range(self.length)):
            pos = segments[idx]
            px = int(pos[0] - camera_offset[0])
            py = int(pos[1] - camera_offset[1])
            
            # Segment size scales down towards tail
            t = idx / max(1, self.length - 1)
            size = int(self.size * (1.0 - t * 0.4))
            
            # Draw segment circle
            # Fade body color towards tail
            seg_col = (
                max(0, int(self.color[0] * (1.0 - t * 0.3))),
                max(0, int(self.color[1] * (1.0 - t * 0.3))),
                max(0, int(self.color[2] * (1.0 - t * 0.3)))
            )
            pygame.draw.circle(surface, seg_col, (px, py), size)
            pygame.draw.circle(surface, (10, 10, 15), (px, py), size, 1)  # dark outline
            
        # 3. Draw head details
        hx = int(self.x - camera_offset[0])
        hy = int(self.y - camera_offset[1])
        
        # Eyes
        eye_offset = 6.0
        eye_angle = 0.5  # radians outward
        
        # Left eye
        le_angle = self.angle - eye_angle
        lex = hx + math.cos(le_angle) * eye_offset
        ley = hy + math.sin(le_angle) * eye_offset
        pygame.draw.circle(surface, Settings.COLOR_WHITE, (int(lex), int(ley)), 3.5)
        # Left pupil
        lpx = lex + math.cos(self.angle) * 1.5
        lpy = ley + math.sin(self.angle) * 1.5
        pygame.draw.circle(surface, (0, 0, 0), (int(lpx), int(lpy)), 1.5)
        
        # Right eye
        re_angle = self.angle + eye_angle
        rex = hx + math.cos(re_angle) * eye_offset
        rey = hy + math.sin(re_angle) * eye_offset
        pygame.draw.circle(surface, Settings.COLOR_WHITE, (int(rex), int(rey)), 3.5)
        # Right pupil
        rpx = rex + math.cos(self.angle) * 1.5
        rpy = rey + math.sin(self.angle) * 1.5
        pygame.draw.circle(surface, (0, 0, 0), (int(rpx), int(rpy)), 1.5)
        
        # 4. Draw Active Powerup Halos
        if hasattr(self, "shield_active") and self.shield_active:
            pygame.draw.circle(surface, (30, 160, 255), (hx, hy), int(self.size * 1.7), 2)
            
        if hasattr(self, "invincible_active") and self.invincible_active:
            ticks = pygame.time.get_ticks()
            hue = (ticks * 0.25) % 360
            color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 100)
            pygame.draw.circle(surface, color, (hx, hy), int(self.size * 1.7), 2)
