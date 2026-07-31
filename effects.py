"""
effects.py - Handles screen shake, screen flash, bloom simulations, chromatic aberration, and horror vignettes.
"""
import random
import math
import pygame
from typing import Tuple

class ScreenEffects:
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width = screen_width
        self.height = screen_height
        
        # Screen Shake parameters
        self.shake_time: float = 0.0
        self.shake_duration: float = 0.0
        self.shake_amplitude: float = 0.0
        self.shake_offset: Tuple[float, float] = (0.0, 0.0)
        
        # Screen Flash parameters
        self.flash_color: Tuple[int, int, int] = (255, 255, 255)
        self.flash_duration: float = 0.0
        self.flash_timer: float = 0.0
        self.flash_alpha: int = 0
        
        # Horror vignette surface
        self.vignette_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._build_vignette()

        # Glitch parameters for horror/void skin
        self.glitch_active: bool = False
        self.glitch_timer: float = 0.0
        self.glitch_duration: float = 0.0

    def _build_vignette(self) -> None:
        """Pre-renders a large vignette mask to dark out corners for horror mode."""
        self.vignette_surf.fill((0, 0, 0, 255))
        # Draw a transparent radial gradient in the center
        center_x = self.width // 2
        center_y = self.height // 2
        radius = 250
        
        # Draw concentric rings of decreasing alpha towards center
        for r in range(radius, 0, -5):
            alpha = int(255 * (r / radius))
            pygame.draw.circle(self.vignette_surf, (0, 0, 0, alpha), (center_x, center_y), r)

    def trigger_shake(self, amplitude: float, duration: float) -> None:
        """Triggers screen vibration (shake) effect."""
        self.shake_amplitude = amplitude
        self.shake_duration = duration
        self.shake_time = duration

    def trigger_flash(self, color: Tuple[int, int, int], duration: float) -> None:
        """Triggers full screen color overlay flash."""
        self.flash_color = color
        self.flash_duration = duration
        self.flash_timer = duration
        self.flash_alpha = 150

    def trigger_glitch(self, duration: float) -> None:
        """Triggers horizontal offset glitches."""
        self.glitch_active = True
        self.glitch_duration = duration
        self.glitch_timer = duration

    def update(self, dt: float) -> None:
        """Updates timestamps and intensities for all visual screen transitions."""
        # Update Screen Shake
        if self.shake_time > 0.0:
            self.shake_time -= dt
            # Decay shake magnitude linearly
            current_amp = self.shake_amplitude * (self.shake_time / self.shake_duration)
            self.shake_offset = (
                random.uniform(-current_amp, current_amp),
                random.uniform(-current_amp, current_amp)
            )
        else:
            self.shake_offset = (0.0, 0.0)
            
        # Update Screen Flash
        if self.flash_timer > 0.0:
            self.flash_timer -= dt
            self.flash_alpha = int(180 * (self.flash_timer / self.flash_duration))
        else:
            self.flash_alpha = 0
            
        # Update Glitch
        if self.glitch_timer > 0.0:
            self.glitch_timer -= dt
        else:
            self.glitch_active = False

    def get_shake_offset(self) -> Tuple[float, float]:
        return self.shake_offset

    def draw_flash(self, target_surf: pygame.Surface) -> None:
        """Draws the screen overlay flash if active."""
        if self.flash_alpha > 0:
            flash_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            r, g, b = self.flash_color
            flash_overlay.fill((r, g, b, self.flash_alpha))
            target_surf.blit(flash_overlay, (0, 0))

    def draw_horror_vignette(self, target_surf: pygame.Surface, player_screen_pos: Tuple[float, float], flicker: bool = False) -> None:
        """
        Draws the dark fog surrounding the player's coordinate,
        restricting visible range. Optionally flickers the light source radius.
        """
        # Create dynamic mask surface
        mask = pygame.Surface((self.width, self.height))
        mask.fill((10, 10, 15))  # Dark ambient color
        
        # Center of illumination is the snake's head
        px, py = player_screen_pos
        
        # Calculate dynamic light radius with noise (flashlight flicker)
        base_radius = 180.0
        if flicker:
            base_radius += random.uniform(-15.0, 15.0) + 10.0 * math.sin(pygame.time.get_ticks() * 0.05)
            
        # Draw soft circle on the dark mask to clear it
        # Concentric steps for soft light edge
        for r in range(int(base_radius), 0, -8):
            t = 1.0 - (r / base_radius)
            cr = int(10 + (255 - 10) * t)
            cg = int(10 + (255 - 10) * t)
            cb = int(15 + (255 - 15) * t)
            pygame.draw.circle(mask, (cr, cg, cb), (int(px), int(py)), r)
            
        # Blit using multiply blend to make corners pitch black/dark and center illuminated
        target_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_MULT)

    def apply_chromatic_aberration(self, target_surf: pygame.Surface, offset_x: int = 4) -> None:
        """
        Simulates chromatic aberration by extracting red/cyan offsets of the target surface.
        Only runs when trigger_shake is active or when explicitly glitched to preserve CPU performance.
        """
        if offset_x <= 0:
            return
            
        # Extract surface width/height
        w, h = target_surf.get_size()
        
        # Copy the target frame
        temp_surf = target_surf.copy()
        
        # Clear target surface to combine channel buffers
        target_surf.fill((0, 0, 0))
        
        # Red channel offshoot
        red_surf = temp_surf.copy()
        # Set blue and green channels to 0 using raw surface modification
        # Use standard BLEND_MULT which is compatible with RGB surfaces
        red_surf.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
        
        # Cyan channel offshoot (Green + Blue)
        cyan_surf = temp_surf.copy()
        cyan_surf.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
        
        # Blit together with offset
        target_surf.blit(red_surf, (-offset_x, 0))
        target_surf.blit(cyan_surf, (offset_x, 0), special_flags=pygame.BLEND_ADD)

    def apply_screen_glitch(self, target_surf: pygame.Surface) -> None:
        """Slices and offsets random horizontal scanline sections for horror/cyberpunk damage effects."""
        if not self.glitch_active and random.random() > 0.05:
            return
            
        # Perform 2-5 slice glitches
        slices = random.randint(2, 6)
        for _ in range(slices):
            slice_y = random.randint(0, self.height - 40)
            slice_h = random.randint(10, 40)
            offset_x = random.randint(-25, 25)
            
            # Sub-surface copy
            try:
                sub_rect = pygame.Rect(0, slice_y, self.width, slice_h)
                sub_surf = target_surf.subsurface(sub_rect).copy()
                
                # Draw black cover
                pygame.draw.rect(target_surf, (10, 10, 15), sub_rect)
                
                # Blit offsetted slice
                target_surf.blit(sub_surf, (offset_x, slice_y))
            except ValueError:
                # Subsurface bounds issues can happen with rounding
                continue
                
        # Draw occasional random static line
        if random.random() < 0.3:
            y = random.randint(0, self.height)
            pygame.draw.line(target_surf, (255, 255, 255, 100), (0, y), (self.width, y), 2)
            
    def apply_bloom_effect(self, target_surf: pygame.Surface, game_surf: pygame.Surface) -> None:
        """
        Blurs and adds bright elements to create standard bloom.
        Optimized by scaling down the surface, blurring it by small increments, and drawing it additive.
        """
        # Downscale
        small_w = self.width // 4
        small_h = self.height // 4
        small_surf = pygame.transform.smoothscale(game_surf, (small_w, small_h))
        
        # Upscale back to full screen
        bloom_glow = pygame.transform.smoothscale(small_surf, (self.width, self.height))
        
        # Blend onto main screen additive
        target_surf.blit(bloom_glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
