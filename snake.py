"""
snake.py - Player snake controller, sub-pixel slither interpolation, animated facial parts, and skins styles.
"""
import math
import pygame
import random
from typing import Tuple, List, Dict, Any
from settings import Settings
from utils import Utils
from particles import ParticleManager

class Snake:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.base_speed = 150.0  # Pixels per second
        self.speed = self.base_speed
        
        # Heading angle in radians
        self.angle: float = 0.0
        self.target_angle: float = 0.0
        self.turn_speed: float = 8.0  # Radians per second for smooth rotation
        
        # Spacing configurations
        self.length: int = 6  # Starting length
        self.step_size: float = 2.0  # Spacing distance between history path records (pixels)
        self.segment_spacing: int = 7  # Index steps in history between body segments (total pixels = 7 * 2 = 14)
        
        # Path history of coordinates
        self.path: List[Tuple[float, float]] = [(x, y)]
        self.distance_accumulator: float = 0.0
        
        # Face details timers
        self.tongue_timer: float = 0.0
        self.breathing_timer: float = 0.0
        
        # Powerup modifiers
        self.magnet_active: bool = False
        self.shield_active: bool = False
        self.invincible_active: bool = False
        self.ghost_active: bool = False
        
        # Death flag
        self.is_dead: bool = False

    def reset(self, x: float, y: float) -> None:
        """Resets snake configuration to starting coordinate."""
        self.x = x
        self.y = y
        self.angle = 0.0
        self.target_angle = 0.0
        self.length = 6
        self.path = [(x, y)]
        self.distance_accumulator = 0.0
        self.tongue_timer = 0.0
        self.breathing_timer = 0.0
        self.is_dead = False
        self.magnet_active = False
        self.shield_active = False
        self.invincible_active = False
        self.ghost_active = False

    def grow(self, amount: int = 1) -> None:
        self.length += amount

    def shrink(self, amount: int = 1) -> None:
        self.length = max(3, self.length - amount)

    def set_target_direction(self, dx: float, dy: float) -> None:
        """Sets target angle to smoothly rotate towards, avoiding instant hard turns."""
        if dx == 0 and dy == 0:
            return
            
        target = math.atan2(dy, dx)
        # Prevent rotating backwards instantly (180 deg) if player goes in opposite direction,
        # but standard classic snake can do it. In grid-free slithering we restrict instant 180s.
        diff = (target - self.angle + math.pi) % (2.0 * math.pi) - math.pi
        if abs(diff) > math.pi - 0.2:
            # Block direct 180 degrees spin
            return
            
        self.target_angle = target

    def update(self, dt: float, speed_multiplier: float, particles: ParticleManager) -> None:
        """Handles movement interpolation, angle rotation, tail growth path, and animations."""
        if self.is_dead:
            return
            
        # 1. Smoothly rotate current angle towards target direction
        angle_diff = (self.target_angle - self.angle + math.pi) % (2.0 * math.pi) - math.pi
        self.angle += angle_diff * self.turn_speed * dt
        
        # 2. Advance coordinates
        move_speed = self.speed * speed_multiplier
        dx = math.cos(self.angle) * move_speed * dt
        dy = math.sin(self.angle) * move_speed * dt
        
        self.x += dx
        self.y += dy
        
        # 3. Accumulate distance to insert point in path history
        dist_moved = math.sqrt(dx*dx + dy*dy)
        self.distance_accumulator += dist_moved
        
        while self.distance_accumulator >= self.step_size:
            # Interpolate exact point
            ratio = self.step_size / max(0.01, dist_moved)
            ix = self.x - dx * (1.0 - ratio)
            iy = self.y - dy * (1.0 - ratio)
            
            # Prepend coordinate
            self.path.insert(0, (ix, iy))
            self.distance_accumulator -= self.step_size
            
        # Trim excess path size
        max_path_len = self.length * self.segment_spacing + 5
        if len(self.path) > max_path_len:
            self.path = self.path[:max_path_len]
            
        # 4. Update animations timers
        self.tongue_timer += 10.0 * dt
        self.breathing_timer += 5.0 * dt
        
        # 5. Emit movement particle trails from tail end
        if len(self.path) > 0 and random.random() < 0.15:
            tail_idx = min(len(self.path) - 1, self.length * self.segment_spacing - 1)
            tail_pos = self.path[tail_idx]
            particles.spawn_trail(tail_pos, Settings.COLOR_CYAN, 3)

    def get_segments(self) -> List[Tuple[float, float]]:
        """Extracts absolute world positions of all body segments along history path."""
        segments = []
        for i in range(self.length):
            idx = i * self.segment_spacing
            if idx < len(self.path):
                segments.append(self.path[idx])
            else:
                # Fill missing with tail tip
                segments.append(self.path[-1] if len(self.path) > 0 else (self.x, self.y))
        return segments

    def draw(
        self, 
        surface: pygame.Surface, 
        camera_offset: Tuple[float, float], 
        skin_id: str, 
        nearest_food: Tuple[float, float] = None
    ) -> None:
        """Renders the entire snake body procedurally applying selected Skin styling rules."""
        segments = self.get_segments()
        if not segments:
            return
            
        ticks = pygame.time.get_ticks()
        
        # Draw body segments from tail to head (so head layers on top)
        for idx in range(len(segments) - 1, -1, -1):
            x, y = segments[idx]
            px = int(x - camera_offset[0])
            py = int(y - camera_offset[1])
            
            # Segment size tapering towards tail
            taper_factor = (len(segments) - idx) / len(segments)
            # Size limits: 13 (head) down to 7 (tail)
            r = int(7.0 + 6.0 * taper_factor)
            
            # Apply breathing animation to head size
            if idx == 0:
                r += int(1.5 * math.sin(self.breathing_timer))
                
            # Determine Segment styling based on skin
            self._draw_segment_by_skin(surface, px, py, r, idx, skin_id, ticks)
            
        # Draw head features (eyes, tongue)
        self._draw_head_features(surface, segments[0], camera_offset, nearest_food)

    def _draw_segment_by_skin(
        self, 
        surf: pygame.Surface, 
        px: int, 
        py: int, 
        r: int, 
        idx: int, 
        skin_id: str, 
        ticks: int
    ) -> None:
        """Helper to render individual body segment applying colors/textures matching selected skin."""
        
        # Skin colors default structures
        skin_conf = next((s for s in Settings.SKINS if s["id"] == skin_id), Settings.SKINS[0])
        c1 = skin_conf["primary"]
        c2 = skin_conf["secondary"]
        style = skin_conf["style"]
        
        if style == "solid":
            pygame.draw.circle(surf, c1, (px, py), r)
            pygame.draw.circle(surf, c2, (px, py), r - 3)
            
        elif style == "gradient":
            # Lerp color from primary to secondary along length
            t = idx / max(1, self.length)
            r_c = int(Utils.lerp(c1[0], c2[0], t))
            g_c = int(Utils.lerp(c1[1], c2[1], t))
            b_c = int(Utils.lerp(c1[2], c2[2], t))
            pygame.draw.circle(surf, (r_c, g_c, b_c), (px, py), r)
            
        elif style == "fire":
            # Fire flickers size and colors
            flicker = random.randint(-1, 1)
            # Alternate red/orange
            color = c1 if (idx % 2 == 0) else c2
            if idx == 0:
                color = Settings.COLOR_GOLD
            pygame.draw.circle(surf, color, (px, py), max(3, r + flicker))
            
        elif style == "stripes":
            # Alternates colors for striped patterns (e.g. zebra, hazard)
            color = c1 if (idx // 2 % 2 == 0) else c2
            pygame.draw.circle(surf, color, (px, py), r)
            pygame.draw.circle(surf, c1 if color == c2 else c2, (px, py), r - 4)
            
        elif style == "translucent":
            # Shadow transparency
            alpha = int(220 * (1.0 - (idx / self.length)))
            alpha = max(30, min(220, alpha))
            
            p_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (c1[0], c1[1], c1[2], alpha), (r, r), r)
            pygame.draw.circle(p_surf, (c2[0], c2[1], c2[2], alpha), (r, r), r - 3)
            surf.blit(p_surf, (px - r, py - r))
            
        elif style == "glow_shift":
            # Dynamic wave shifts hue over time
            val = math.sin(ticks * 0.005 - idx * 0.3)
            color = c1 if val > 0 else c2
            Utils.draw_glow_circle(surf, (px, py), r, color, intensity=70, layers=2)
            
        elif style == "rainbow":
            # Complete spectrum
            hue = (ticks * 0.1 - idx * 20.0) % 360.0
            hue_rad = math.radians(hue)
            r_c = int(127 + 127 * math.sin(hue_rad))
            g_c = int(127 + 127 * math.sin(hue_rad + 2.0*math.pi/3.0))
            b_c = int(127 + 127 * math.sin(hue_rad + 4.0*math.pi/3.0))
            pygame.draw.circle(surf, (r_c, g_c, b_c), (px, py), r)
            
        elif style == "glitch":
            # Offsets rendering slightly to look bugged (Void skin)
            gx = px + (random.randint(-2, 2) if random.random() < 0.1 else 0)
            gy = py + (random.randint(-2, 2) if random.random() < 0.1 else 0)
            pygame.draw.rect(surf, c1, (gx - r, gy - r, r*2, r*2))
            pygame.draw.rect(surf, c2, (gx - r + 3, gy - r + 3, r*2 - 6, r*2 - 6))
            
        else:
            # Fallback
            pygame.draw.circle(surf, c1, (px, py), r)

    def _draw_head_features(
        self, 
        surf: pygame.Surface, 
        head_pos: Tuple[float, float], 
        camera_offset: Tuple[float, float],
        nearest_food: Tuple[float, float]
    ) -> None:
        """Renders face items (tracking eyes, flicker tongue, shield glow overlays)."""
        hx, hy = head_pos
        px = int(hx - camera_offset[0])
        py = int(hy - camera_offset[1])
        r = 13 + int(1.5 * math.sin(self.breathing_timer))
        ticks = pygame.time.get_ticks()
        
        # 1. Draw flickering tongue
        # Tongue extends forward in direction of angle
        if math.sin(self.tongue_timer) > 0.3:
            t_len = r + 8
            # Forked tongue points
            f_x = px + t_len * math.cos(self.angle)
            f_y = py + t_len * math.sin(self.angle)
            
            f1_x = f_x + 5 * math.cos(self.angle + 0.5)
            f1_y = f_y + 5 * math.sin(self.angle + 0.5)
            f2_x = f_x + 5 * math.cos(self.angle - 0.5)
            f2_y = f_y + 5 * math.sin(self.angle - 0.5)
            
            pygame.draw.line(surf, Settings.COLOR_RED, (px, py), (int(f_x), int(f_y)), 2)
            pygame.draw.line(surf, Settings.COLOR_RED, (int(f_x), int(f_y)), (int(f1_x), int(f1_y)), 2)
            pygame.draw.line(surf, Settings.COLOR_RED, (int(f_x), int(f_y)), (int(f2_x), int(f2_y)), 2)

        # 2. Draw Eyes tracking food coordinate
        # Eye offsets relative to angle
        eye_dist = 6.0
        eye_angle_offset = 0.6
        
        le_x = px + eye_dist * math.cos(self.angle - eye_angle_offset)
        le_y = py + eye_dist * math.sin(self.angle - eye_angle_offset)
        re_x = px + eye_dist * math.cos(self.angle + eye_angle_offset)
        re_y = py + eye_dist * math.sin(self.angle + eye_angle_offset)
        
        pygame.draw.circle(surf, Settings.COLOR_WHITE, (int(le_x), int(le_y)), 4)
        pygame.draw.circle(surf, Settings.COLOR_WHITE, (int(re_x), int(re_y)), 4)
        
        # Pupils trace closest target vector
        look_dx, look_dy = math.cos(self.angle), math.sin(self.angle)
        if nearest_food:
            fdx = nearest_food[0] - hx
            fdy = nearest_food[1] - hy
            fdist = math.sqrt(fdx*fdx + fdy*fdy)
            if fdist > 1.0:
                look_dx, look_dy = fdx / fdist, fdy / fdist
                
        # Draw pupils
        lp_x = le_x + 1.5 * look_dx
        lp_y = le_y + 1.5 * look_dy
        rp_x = re_x + 1.5 * look_dx
        rp_y = re_y + 1.5 * look_dy
        pygame.draw.circle(surf, (0, 0, 0), (int(lp_x), int(lp_y)), 2)
        pygame.draw.circle(surf, (0, 0, 0), (int(rp_x), int(rp_y)), 2)

        # 3. Draw active powerup indicator glow overlays
        if self.shield_active:
            # Blue outer energy ring
            shield_r = r + 8
            pygame.draw.circle(surf, Settings.COLOR_BLUE, (px, py), shield_r, 2)
            
            # Subtle alpha filler
            s_surf = pygame.Surface((shield_r*2, shield_r*2), pygame.SRCALPHA)
            pygame.draw.circle(s_surf, (30, 144, 255, 30), (shield_r, shield_r), shield_r)
            surf.blit(s_surf, (px - shield_r, py - shield_r))
            
        if self.invincible_active:
            # Rainbow cycling shield ring
            inv_r = r + 10
            hue = (ticks * 0.2) % 360
            hr = math.radians(hue)
            rc = int(127 + 127*math.sin(hr))
            gc = int(127 + 127*math.sin(hr + 2.0*math.pi/3.0))
            bc = int(127 + 127*math.sin(hr + 4.0*math.pi/3.0))
            pygame.draw.circle(surf, (rc, gc, bc), (px, py), inv_r, 2)
            
        if self.magnet_active:
            # Cyan lightning ring particles
            if random.random() < 0.2:
                mag_ang = random.uniform(0, 2*math.pi)
                mx = px + int((r+6)*math.cos(mag_ang))
                my = py + int((r+6)*math.sin(mag_ang))
                pygame.draw.circle(surf, Settings.COLOR_CYAN, (mx, my), 2)
