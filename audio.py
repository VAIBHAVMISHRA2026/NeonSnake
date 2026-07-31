"""
audio.py - Handles sound effects playback, background music loops, and volume configurations.
"""
import os
import pygame
from typing import Dict
from save import SaveManager
from utils import get_base_dir

class AudioManager:
    def __init__(self, save_manager: SaveManager) -> None:
        self.save_manager = save_manager
        self.sfx_volume: float = self.save_manager.get_settings().get("sfx_volume", 0.6)
        self.music_volume: float = self.save_manager.get_settings().get("music_volume", 0.5)
        self.muted: bool = False
        
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music: str = ""
        self.base_dir = get_base_dir()
        
        self.init_mixer()
        self.load_assets()

    def init_mixer(self) -> None:
        """Initializes pygame mixer safely, taking system audio capabilities into account."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
        except Exception as e:
            print(f"[AudioManager] Critical: Failed to initialize sound card mixer. {e}")

    def load_assets(self) -> None:
        """Loads synthesized WAV files into memory for low-latency SFX triggers."""
        if not pygame.mixer.get_init():
            return
            
        sounds_dir = os.path.join(self.base_dir, "assets", "sounds")
        if not os.path.exists(sounds_dir):
            return
            
        sfx_files = ["eat.wav", "powerup.wav", "button_click.wav", "hit.wav", "level_up.wav", "game_over.wav", "victory.wav", "boss_phase.wav", "explosion.wav"]
        
        for file in sfx_files:
            name = os.path.splitext(file)[0]
            path = os.path.join(sounds_dir, file)
            if os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.sfx_volume)
                    self.sounds[name] = sound
                except pygame.error as e:
                    print(f"[AudioManager] Failed to load sound {file}: {e}")

    def play_sound(self, name: str) -> None:
        """Plays an SFX by its identifier, accounting for volume settings and mute state."""
        if self.muted or not pygame.mixer.get_init():
            return
            
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(0.0 if self.muted else self.sfx_volume)
            sound.play()

    def play_music(self, name: str, loops: int = -1) -> None:
        """Loads and streams a background music file from disk using mixer.music."""
        if not pygame.mixer.get_init():
            return
            
        if self.current_music == name and pygame.mixer.music.get_busy():
            return  # Music is already playing
            
        music_path = os.path.join(self.base_dir, "assets", "music", f"{name}.wav")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
                pygame.mixer.music.play(loops)
                self.current_music = name
            except pygame.error as e:
                print(f"[AudioManager] Failed to load music {name}: {e}")

    def stop_music(self) -> None:
        """Stops background music track streaming."""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            self.current_music = ""

    def pause_music(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.unpause()

    def set_music_volume(self, volume: float) -> None:
        """Adjusts current music volume and saves changes to settings."""
        self.music_volume = max(0.0, min(1.0, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            
        # Update settings
        settings = self.save_manager.get_settings()
        settings["music_volume"] = self.music_volume
        self.save_manager.update_settings(settings)

    def set_sfx_volume(self, volume: float) -> None:
        """Adjusts SFX volume across all sounds and saves configuration."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
            
        # Update settings
        settings = self.save_manager.get_settings()
        settings["sfx_volume"] = self.sfx_volume
        self.save_manager.update_settings(settings)

    def toggle_mute(self) -> bool:
        """Toggles audio mute state. Returns the new muted state."""
        self.muted = not self.muted
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            for sound in self.sounds.values():
                sound.set_volume(0.0 if self.muted else self.sfx_volume)
        return self.muted
