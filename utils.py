"""
utils.py - Custom mathematics, graphics drawing utilities, and procedural asset generators.
"""
import os
import sys
import math
import struct
import pygame
from typing import Tuple, List, Callable, Any


def get_base_dir() -> str:
    """Returns the base directory for asset loading.
    Handles PyInstaller frozen executables via sys._MEIPASS."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

class Utils:
    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        """Linear interpolation between a and b by t."""
        return a + (b - a) * max(0.0, min(1.0, t))

    @staticmethod
    def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculates Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    @staticmethod
    def draw_rounded_rect(
        surface: pygame.Surface, 
        rect: pygame.Rect, 
        color: Tuple[int, int, int], 
        radius: int = 8, 
        border_width: int = 0
    ) -> None:
        """Draws a rounded rectangle using Pygame's built-in draw capabilities."""
        pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)

    @staticmethod
    def draw_glow_circle(
        surface: pygame.Surface, 
        center: Tuple[int, int], 
        radius: int, 
        color: Tuple[int, int, int], 
        intensity: int = 150, 
        layers: int = 4
    ) -> None:
        """Draws concentric semi-transparent circles to create a neon bloom glow effect."""
        glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        surf_center = (radius * 2, radius * 2)
        
        r, g, b = color
        for i in range(layers, 0, -1):
            layer_radius = int(radius * (1.0 + i * 0.4))
            alpha = int(intensity * (1.0 - (i / layers)) / layers)
            # Clip alpha
            alpha = max(0, min(255, alpha))
            
            # Draw on transparent surface
            pygame.draw.circle(glow_surf, (r, g, b, alpha), surf_center, layer_radius)
            
        # Draw base core circle
        pygame.draw.circle(glow_surf, (r, g, b, 255), surf_center, radius)
        
        # Blit centered
        surface.blit(glow_surf, (center[0] - radius * 2, center[1] - radius * 2), special_flags=pygame.BLEND_RGBA_ADD)

    @staticmethod
    def create_gradient_surface(
        width: int, 
        height: int, 
        start_color: Tuple[int, int, int], 
        end_color: Tuple[int, int, int], 
        vertical: bool = True
    ) -> pygame.Surface:
        """Creates a surface with a smooth linear gradient between two colors."""
        surf = pygame.Surface((width, height))
        sr, sg, sb = start_color
        er, eg, eb = end_color
        
        if vertical:
            for y in range(height):
                t = y / max(1, height - 1)
                r = int(Utils.lerp(sr, er, t))
                g = int(Utils.lerp(sg, eg, t))
                b = int(Utils.lerp(sb, eb, t))
                pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
        else:
            for x in range(width):
                t = x / max(1, width - 1)
                r = int(Utils.lerp(sr, er, t))
                g = int(Utils.lerp(sg, eg, t))
                b = int(Utils.lerp(sb, eb, t))
                pygame.draw.line(surf, (r, g, b), (x, 0), (x, height))
                
        return surf

    @staticmethod
    def create_radial_gradient_surface(
        radius: int, 
        inner_color: Tuple[int, int, int, int], 
        outer_color: Tuple[int, int, int, int]
    ) -> pygame.Surface:
        """Creates a square surface containing a radial alpha gradient."""
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        ir, ig, ib, ia = inner_color
        or_val, og, ob, oa = outer_color
        
        for y in range(size):
            for x in range(size):
                dx = x - radius
                dy = y - radius
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= radius:
                    t = dist / radius
                    r = int(Utils.lerp(ir, or_val, t))
                    g = int(Utils.lerp(ig, og, t))
                    b = int(Utils.lerp(ib, ob, t))
                    a = int(Utils.lerp(ia, oa, t))
                    surf.set_at((x, y), (r, g, b, a))
        return surf

    @staticmethod
    def synthesize_wav(
        filepath: str, 
        frequency_func: Callable[[float], float], 
        duration: float, 
        volume_func: Callable[[float], float] = None, 
        sample_rate: int = 22050
    ) -> None:
        """
        Synthesizes a 16-bit Mono PCM WAV file programmatically using struct.
        This provides offline audio placeholders and sound effects without asset dependencies.
        """
        num_samples = int(sample_rate * duration)
        data = bytearray()
        
        phase = 0.0
        for i in range(num_samples):
            t = i / sample_rate
            freq = frequency_func(t)
            
            # Integrate phase to avoid clicking with frequency sweeps
            phase += 2.0 * math.pi * freq / sample_rate
            
            # Waveform type (defaulting to Sine with a bit of triangle harmonics)
            wave = 0.7 * math.sin(phase) + 0.3 * (abs((phase % (2 * math.pi)) - math.pi) / math.pi * 2 - 1)
            
            # Apply volume envelope
            vol = volume_func(t) if volume_func else 0.5
            val = int(32767 * vol * wave)
            val = max(-32768, min(32767, val)) # Clamp
            
            data.extend(struct.pack('<h', val))
            
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + len(data),
            b'WAVE',
            b'fmt ',
            16,
            1,  # PCM
            1,  # Mono
            sample_rate,
            sample_rate * 2,
            2,  # BlockAlign
            16, # BitsPerSample
            b'data',
            len(data)
        )
        
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(data)

    @staticmethod
    def generate_all_assets() -> None:
        """Generates mock images, skins textures, sound effects, and music loop placeholders at startup."""
        base_dir = get_base_dir()
        
        # Create folder structure
        paths = [
            os.path.join(base_dir, "assets", "images"),
            os.path.join(base_dir, "assets", "sounds"),
            os.path.join(base_dir, "assets", "music"),
            os.path.join(base_dir, "assets", "fonts"),
            os.path.join(base_dir, "assets", "skins"),
            os.path.join(base_dir, "data")
        ]
        
        for path in paths:
            os.makedirs(path, exist_ok=True)
            
        # Initialize pygame temporarily to generate graphics
        pygame.display.init()
        pygame.font.init()
        
        # 1. Synthesize SFX WAV Files if not present
        sounds_dir = os.path.join(base_dir, "assets", "sounds")
        
        sfx_configs = {
            "eat.wav": (lambda t: 250.0 + 800.0 * t, 0.12, lambda t: 0.4 * (1.0 - t)),
            "powerup.wav": (lambda t: 400.0 + 400.0 * math.sin(t * 30) + 200.0 * t, 0.4, lambda t: 0.5 * (1.0 - t)),
            "button_click.wav": (lambda t: 800.0, 0.05, lambda t: 0.3 * (1.0 - t)),
            "hit.wav": (lambda t: 200.0 - 180.0 * t, 0.35, lambda t: 0.6 * (1.0 - t)),
            "level_up.wav": (lambda t: 300.0 if t < 0.1 else (450.0 if t < 0.2 else (600.0 if t < 0.3 else 800.0)), 0.5, lambda t: 0.4 * (1.0 - t)),
            "game_over.wav": (lambda t: 300.0 - 200.0 * t, 0.8, lambda t: 0.5 * (1.0 - t)),
            "victory.wav": (lambda t: 400.0 + 300.0 * math.sin(t * 12) + 200.0 * t, 0.8, lambda t: 0.5 * (1.0 - t)),
            "boss_phase.wav": (lambda t: 500.0 if (int(t * 10) % 2 == 0) else 350.0, 0.8, lambda t: 0.5),
            "explosion.wav": (lambda t: 100.0 - 80.0 * t + 30.0 * math.sin(t * 50), 0.6, lambda t: 0.7 * (1.0 - t))
        }
        
        for name, (freq_f, dur, vol_f) in sfx_configs.items():
            path = os.path.join(sounds_dir, name)
            if not os.path.exists(path):
                Utils.synthesize_wav(path, freq_f, dur, vol_f)

        # 2. Synthesize Music Loops if not present
        music_dir = os.path.join(base_dir, "assets", "music")
        
        music_configs = {
            "menu.wav": (
                # Simple melodic sine wave arpeggio (loops well)
                lambda t: [130.81, 164.81, 196.00, 261.63][int(t * 8) % 4] + 2.0 * math.sin(t * 20),
                3.0, 
                lambda t: 0.25 + 0.05 * math.sin(t * 10)
            ),
            "gameplay.wav": (
                # Bass drone + driving rhythm synth
                lambda t: [110.00, 110.00, 130.81, 146.83][int(t * 6) % 4] + [0, 2, 0, -2][int(t * 12) % 4],
                4.0, 
                lambda t: 0.20 + 0.08 * (1.0 if int(t * 8) % 2 == 0 else 0.2)
            ),
            "boss.wav": (
                # Heavy tension synth
                lambda t: [73.42, 77.78, 65.41, 69.30][int(t * 4) % 4] + 15 * math.sin(t * 60),
                4.0, 
                lambda t: 0.30 * (0.8 + 0.2 * math.cos(t * 15))
            )
        }
        
        for name, (freq_f, dur, vol_f) in music_configs.items():
            path = os.path.join(music_dir, name)
            if not os.path.exists(path):
                Utils.synthesize_wav(path, freq_f, dur, vol_f)

        # 3. Create mock graphical image assets if not present
        images_dir = os.path.join(base_dir, "assets", "images")
        
        # Logo PNG
        logo_path = os.path.join(images_dir, "logo.png")
        if not os.path.exists(logo_path):
            surf = pygame.Surface((400, 100), pygame.SRCALPHA)
            # Create a simple neon glow logo in a surface
            # Underlay shadow
            font = pygame.font.SysFont("Impact", 64)
            text_surf_glow = font.render("NEON SNAKE", True, (0, 240, 255))
            text_surf_white = font.render("NEON SNAKE", True, (255, 255, 255))
            
            # Simple glow blit
            for ox, oy in [(-3,-3), (3,3), (-3,3), (3,-3), (0,-4), (0,4), (-4,0), (4,0)]:
                surf.blit(text_surf_glow, (200 - text_surf_glow.get_width()//2 + ox, 50 - text_surf_glow.get_height()//2 + oy))
            surf.blit(text_surf_white, (200 - text_surf_white.get_width()//2, 50 - text_surf_white.get_height()//2))
            pygame.image.save(surf, logo_path)

        pygame.display.quit()
        pygame.font.quit()


class SpriteManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self.sprites = {}
        self.loaded = False
        
    def load_assets(self) -> None:
        if self.loaded:
            return
        try:
            path = os.path.join(get_base_dir(), "assets", "images", "spritesheet.png")
            if not os.path.exists(path):
                return
            sheet = pygame.image.load(path).convert_alpha()
            w, h = sheet.get_size()
            cw = w // 3
            ch = h // 3
            
            # Row 0
            self.sprites["Magnet"] = self._slice(sheet, 0, 0, cw, ch)
            self.sprites["Shield"] = self._slice(sheet, 1, 0, cw, ch)
            self.sprites["Speed Boost"] = self._slice(sheet, 2, 0, cw, ch)
            
            # Row 1
            self.sprites["Slow Motion"] = self._slice(sheet, 0, 1, cw, ch)
            self.sprites["Freeze Time"] = self._slice(sheet, 0, 1, cw, ch)
            self.sprites["Frozen"] = self._slice(sheet, 1, 1, cw, ch)
            self.sprites["Invincibility"] = self._slice(sheet, 2, 1, cw, ch)
            self.sprites["Double Score"] = self._slice(sheet, 2, 1, cw, ch)
            self.sprites["Golden"] = self._slice(sheet, 2, 1, cw, ch)
            
            # Row 2
            self.sprites["Ghost"] = self._slice(sheet, 0, 2, cw, ch)
            self.sprites["Ghost Mode"] = self._slice(sheet, 0, 2, cw, ch)
            self.sprites["Lucky"] = self._slice(sheet, 1, 2, cw, ch)
            self.sprites["Teleport"] = self._slice(sheet, 1, 2, cw, ch)
            self.sprites["Food Multiplier"] = self._slice(sheet, 1, 2, cw, ch)
            self.sprites["Random Power"] = self._slice(sheet, 2, 2, cw, ch)
            self.sprites["Mystery Box"] = self._slice(sheet, 2, 2, cw, ch)
            
            self.loaded = True
        except Exception as e:
            print(f"[SpriteManager] Failed to load spritesheet: {e}")

    def _slice(self, sheet: pygame.Surface, col: int, row: int, cw: int, ch: int) -> pygame.Surface:
        sub = pygame.Surface((cw, ch), pygame.SRCALPHA)
        sub.blit(sheet, (0, 0), pygame.Rect(col * cw, row * ch, cw, ch))
        sub.set_colorkey((0, 0, 0))
        return sub

    def get_sprite(self, name: str, size: int) -> pygame.Surface:
        if not self.loaded:
            self.load_assets()
        if name in self.sprites:
            return pygame.transform.smoothscale(self.sprites[name], (size, size))
        return None
