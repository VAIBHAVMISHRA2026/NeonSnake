"""
main.py - Entry point, window initialization, event dispatcher, and clock driver.
"""
import sys
import os
import pygame
from settings import Settings
from utils import Utils
from game import GameEngine

def main() -> None:
    # 1. Procedurally generate assets on first boot if they are missing
    print("[Main] Initializing procedural asset generators...")
    try:
        Utils.generate_all_assets()
    except Exception as e:
        print(f"[Main] Warning: Failed to generate some mock asset files: {e}")

    # 2. Safely initialize Pygame core modules
    pygame.init()
    pygame.font.init()
    
    # 3. Create double-buffered game window
    screen_w = Settings.SCREEN_WIDTH
    screen_h = Settings.SCREEN_HEIGHT
    
    pygame.display.set_caption("NEON SNAKE: EXPERT CE")
    
    # Check fullscreen setting
    try:
        # Check if saved fullscreen setting is true
        from save import SaveManager
        temp_save = SaveManager()
        is_fullscreen = temp_save.get_settings().get("fullscreen", False)
    except Exception:
        is_fullscreen = False
        
    flags = pygame.DOUBLEBUF | pygame.HWSURFACE
    if is_fullscreen:
        flags |= pygame.FULLSCREEN
        
    try:
        screen = pygame.display.set_mode((screen_w, screen_h), flags)
    except pygame.error:
        # Fallback to standard windowed mode if hardware surface fails
        print("[Main] Hardware graphics context failed, falling back to windowed software rendering.")
        screen = pygame.display.set_mode((screen_w, screen_h))

    # 4. Instantiate central Game Engine
    try:
        engine = GameEngine(screen)
    except Exception as e:
        print(f"[Main] Critical failure: Game Engine failed to boot. {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
        
    clock = pygame.time.Clock()
    
    # Load FPS constraints
    fps_limit = engine.save_manager.get_settings().get("fps_limit", Settings.DEFAULT_FPS)
    
    # 5. Core Game Loop
    running = True
    print("[Main] Entering main loop cycle.")
    
    while running:
        # Delta time in seconds
        raw_dt = clock.tick(fps_limit) / 1000.0
        # Clamp dt to prevent massive coordinate skips during window dragging/lag spikes
        dt = min(0.08, raw_dt)
        
        # Poll windows events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # State dependent escape behaviors
                    if engine.state == "PLAYING":
                        engine.set_state("PAUSED")
                    elif engine.state == "PAUSED":
                        engine.set_state("PLAYING")
                    elif engine.state in ["SHOP", "SETTINGS", "HIGHSCORES", "ACHIEVEMENTS", "KEYBINDINGS", "HOWTOPLAY", "STATISTICS", "CREDITS"]:
                        engine.set_state("MAIN")
                    elif engine.state == "GAMEOVER":
                        engine.set_state("MAIN")
                        
                elif event.key == pygame.K_r:
                    # Quick reset triggers
                    if engine.state in ["PLAYING", "GAMEOVER", "PAUSED", "COUNTDOWN"]:
                        engine.audio_manager.play_sound("button_click")
                        engine.start_new_game()
                        
                elif event.key == pygame.K_f:
                    # Toggle fullscreen flag
                    is_fullscreen = not is_fullscreen
                    # Update settings
                    sets = engine.save_manager.get_settings()
                    sets["fullscreen"] = is_fullscreen
                    engine.save_manager.update_settings(sets)
                    
                    # Reset display mode
                    pygame.display.quit()
                    pygame.display.init()
                    pygame.display.set_caption("NEON SNAKE: EXPERT CE")
                    
                    current_flags = pygame.DOUBLEBUF | pygame.HWSURFACE
                    if is_fullscreen:
                        current_flags |= pygame.FULLSCREEN
                    screen = pygame.display.set_mode((screen_w, screen_h), current_flags)
                    engine.screen = screen
                    
                elif event.key == pygame.K_m:
                    # Quick mute toggle
                    engine.audio_manager.toggle_mute()
                    
                elif event.key == pygame.K_p and engine.state == "PLAYING":
                    # Alternate pause mapping
                    engine.set_state("PAUSED")

        # Read active keys pressed for real-time movement vectors
        keys = pygame.key.get_pressed()
        engine.handle_input(keys)
        
        # Engine tick (updates physics positions)
        engine.update(dt)
        
        # Render scene buffers to screen
        engine.draw()
        
        # Flip display backbuffer
        pygame.display.flip()

    # 6. Clean Exit Shutdown
    print("[Main] Deinitializing game systems.")
    try:
        engine.save_game_progress()
    except Exception as e:
        print(f"[Main] Failed to auto-save profile during exit: {e}")
        
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
