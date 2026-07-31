"""
game.py - Core GameEngine driver managing state pipelines, level generation, collision vectors, and active buffers.
"""
import random
import math
import pygame
from typing import Tuple, List, Dict, Any
from utils import Utils
from settings import Settings
from save import SaveManager
from audio import AudioManager
from camera import Camera
from effects import ScreenEffects
from particles import ParticleManager
from ui import FloatingText, HUD
from food import Food
from powerups import PowerUp
from enemy import BaseEnemy, Spikes, MovingBomb, HunterSnake, LaserWall, BossEnemy, EnemyProjectile
from snake import Snake
from menu import MenuSystem

class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Core Manager Subsystems
        self.save_manager = SaveManager()
        self.audio_manager = AudioManager(self.save_manager)
        
        # State Machine: MENU, PLAYING, PAUSED, GAMEOVER, VICTORY, SHOP, SETTINGS, HIGHSCORES, ACHIEVEMENTS, COUNTDOWN
        self.state: str = "MAIN"
        
        self.menu_system = MenuSystem(self.save_manager, self.audio_manager, self.set_state)
        self.camera = Camera(self.width, self.height)
        self.effects = ScreenEffects(self.width, self.height)
        self.particles = ParticleManager()
        self.hud = HUD(self.width, self.height)
        
        # Player and entity buffers
        self.snake = Snake(Settings.SCREEN_WIDTH / 2.0, Settings.SCREEN_HEIGHT / 2.0)
        self.foods: List[Food] = []
        self.powerups: List[PowerUp] = []
        self.enemies: List[BaseEnemy] = []
        self.boss: BossEnemy = None
        self.floating_texts: List[FloatingText] = []
        self.boss_projectiles: List[EnemyProjectile] = []
        
        # Game stats
        self.score: int = 0
        self.coins_earned: int = 0
        self.lives: int = 3
        self.level: int = 1
        
        # Level thresholds
        self.xp: float = 0.0
        self.xp_needed: float = 100.0
        
        # Combo mechanics
        self.combo: int = 0
        self.combo_timer: float = 0.0
        self.combo_max: float = 4.0  # Seconds combo lasts
        
        # Game loops timing modifiers
        self.speed_multiplier: float = 1.0
        self.active_powerups: Dict[str, float] = {}
        
        # State trackers
        self.countdown_timer: float = 3.0
        self.invulnerability_timer: float = 0.0  # Hit recovery i-frames
        
        # Kill counter and game time
        self.kills: int = 0
        self.game_time: float = 0.0
        
        # Level-up banner
        self.levelup_banner_timer: float = 0.0
        self.levelup_banner_level: int = 0
        
        # Background space parallax starfield
        self.stars: List[Tuple[float, float, int]] = []
        self.generate_starfield()
        
        # Custom Fonts
        self.font_sm = pygame.font.SysFont("Verdana", 14)
        self.font_md = pygame.font.SysFont("Impact", 24)
        self.font_lg = pygame.font.SysFont("Impact", 56)
        
        # Start menu music
        self.audio_manager.play_music("menu")
        
        # Proactively load spritesheet
        from utils import SpriteManager
        SpriteManager.get_instance().load_assets()

    def generate_starfield(self) -> None:
        """Generates static background coordinates for parallax depth rendering."""
        self.stars.clear()
        for _ in range(120):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            size = random.randint(1, 3)
            self.stars.append((x, y, size))

    def set_state(self, new_state: str) -> None:
        """Handles transitions between states, configuring custom music overlays."""
        old_state = self.state
        self.state = new_state
        
        # State transition audio configuration
        if new_state == "PLAYING":
            if old_state in ["MAIN", "GAMEOVER", "VICTORY"]:
                self.start_new_game()
            else:
                # Resuming from pause
                self.audio_manager.unpause_music()
        elif new_state == "MAIN":
            self.audio_manager.play_music("menu")
        elif new_state in ["SHOP", "SETTINGS", "HIGHSCORES", "ACHIEVEMENTS", "KEYBINDINGS", "HOWTOPLAY", "STATISTICS", "CREDITS"]:
            if old_state == "MAIN":
                pass  # Keep menu music playing
        elif new_state == "PAUSED":
            self.audio_manager.pause_music()
        elif new_state == "GAMEOVER":
            self.audio_manager.play_music("game_over", loops=0)
            self.save_game_progress()
        elif new_state == "VICTORY":
            self.audio_manager.play_music("victory", loops=0)
            self.save_game_progress()

    def start_new_game(self) -> None:
        """Resets all player scores, levels, coordinates, and builds initial stage."""
        self.score = 0
        self.coins_earned = 0
        self.lives = 3
        self.level = 1
        self.xp = 0.0
        self.xp_needed = 100.0
        self.combo = 0
        self.combo_timer = 0.0
        self.active_powerups.clear()
        self.floating_texts.clear()
        self.particles.clear()
        
        # Reset run trackers
        self.kills = 0
        self.game_time = 0.0
        self.levelup_banner_timer = 0.0
        self.countdown_timer = 3.0
        
        # Increment games played
        self.save_manager.increment_stat("games_played", 1)
        
        # Reset snake
        self.snake.reset(Settings.SCREEN_WIDTH / 2.0, Settings.SCREEN_HEIGHT / 2.0)
        
        # Build stage
        self.load_level()
        
        # Start countdown state
        self.state = "COUNTDOWN"

    def load_level(self) -> None:
        """Constructs level hazards, enemy counts, boss fights based on level index."""
        self.foods.clear()
        self.powerups.clear()
        self.enemies.clear()
        self.boss = None
        self.boss_projectiles.clear()
        self.particles.clear()
        
        # Difficulty adjusts parameters
        sets = self.save_manager.get_settings()
        diff_name = sets.get("difficulty", "Medium")
        diff_conf = Settings.DIFFICULTIES.get(diff_name, Settings.DIFFICULTIES["Medium"])
        
        # Update speed factors
        self.snake.speed = self.snake.base_speed * (diff_conf["start_speed"] / 6.0) + (self.level * diff_conf["speed_increment"])
        
        # Set viewport tracking
        self.camera.reset(self.snake.x, self.snake.y)
        
        # 1. BOSS STAGE ENCOUNTERS
        if self.level % 10 == 0:
            self.boss = BossEnemy(self.level)
            self.audio_manager.play_music("boss")
            self.effects.trigger_flash(Settings.COLOR_RED, 1.2)
            self.effects.trigger_shake(15.0, 1.0)
            self.audio_manager.play_sound("boss_phase")
            # Add boss helper floating texts
            self.add_floating_text(f"BOSS FIGHT: {self.boss.name.upper()}", Settings.SCREEN_WIDTH/2, Settings.SCREEN_HEIGHT/2 - 50, Settings.COLOR_RED, size=32)
        else:
            # Standard level music
            self.audio_manager.play_music("gameplay")
            
            # Spawn random food units (3 - 5 based on level)
            food_count = min(8, 3 + self.level // 12)
            for _ in range(food_count):
                self.spawn_food()
                
            # 2. Spawning Standard Enemy Hazards
            # Level increments hazard complexities
            enemy_spawn_chance = diff_conf["enemy_spawn_chance"] * (1.0 + self.level * 0.05)
            
            # Spawn stationary Spikes
            spike_count = min(12, int(self.level // 3))
            for _ in range(spike_count):
                rx = random.uniform(80.0, Settings.SCREEN_WIDTH - 80.0)
                ry = random.uniform(80.0, Settings.SCREEN_HEIGHT - 80.0)
                # Keep away from starting center spot
                if Utils.distance((rx, ry), (Settings.SCREEN_WIDTH/2, Settings.SCREEN_HEIGHT/2)) > 120.0:
                    self.enemies.append(Spikes(rx, ry))
                    
            # Spawn Hunter Snakes (phase unlock)
            if self.level >= 5 and random.random() < enemy_spawn_chance:
                hx = random.choice([50.0, Settings.SCREEN_WIDTH - 50.0])
                hy = random.choice([50.0, Settings.SCREEN_HEIGHT - 50.0])
                self.enemies.append(HunterSnake(hx, hy))
                
            # Spawn Moving Bombs
            if self.level >= 3 and random.random() < enemy_spawn_chance:
                bx = random.uniform(100.0, Settings.SCREEN_WIDTH - 100.0)
                by = random.uniform(100.0, Settings.SCREEN_HEIGHT - 100.0)
                vx = random.choice([-1.0, 1.0]) * random.uniform(60.0, 120.0)
                vy = random.choice([-1.0, 1.0]) * random.uniform(60.0, 120.0)
                self.enemies.append(MovingBomb(bx, by, vx, vy))
                
            # Spawn Laser Walls (fires horizontal or vertical scanbeams)
            if self.level >= 7 and random.random() < enemy_spawn_chance:
                is_horiz = random.choice([True, False])
                coord = random.uniform(150.0, Settings.SCREEN_HEIGHT - 150.0) if is_horiz else random.uniform(150.0, Settings.SCREEN_WIDTH - 150.0)
                self.enemies.append(LaserWall(is_horiz, coord))

            # Spawn AI vs Battle Snakes
            if self.level >= 1:
                ai_count = min(5, 2 + (self.level // 3))
                from enemy import AISnakeEnemy
                for _ in range(ai_count):
                    for _ in range(5):  # retry limit
                        ax = random.uniform(80.0, Settings.SCREEN_WIDTH - 80.0)
                        ay = random.uniform(80.0, Settings.SCREEN_HEIGHT - 80.0)
                        if Utils.distance((ax, ay), (self.snake.x, self.snake.y)) > 200.0:
                            self.enemies.append(AISnakeEnemy(ax, ay, self.level))
                            break

        # Setup Level transition floating text notifications
        self.add_floating_text(f"LEVEL {self.level}", self.snake.x, self.snake.y - 40, Settings.COLOR_CYAN, size=28)
        self.xp_needed = 100.0 + (self.level * 45.0)

    def spawn_food(self, fixed_type: str = None) -> None:
        """Rolls probabilities for foods spawning at random empty coordinate vectors."""
        rx = random.uniform(40.0, Settings.SCREEN_WIDTH - 40.0)
        ry = random.uniform(40.0, Settings.SCREEN_HEIGHT - 40.0)
        
        # Probabilistic roll
        if fixed_type:
            ftype = fixed_type
        else:
            choices = []
            weights = []
            for name, conf in Settings.FOOD_TYPES.items():
                choices.append(name)
                # Boost rare items at higher levels
                chance = conf["chance"]
                if name != "Normal" and self.level > 10:
                    chance *= (1.0 + self.level * 0.02)
                weights.append(chance)
                
            ftype = random.choices(choices, weights=weights)[0]
            
        self.foods.append(Food(rx, ry, ftype))

    def spawn_powerup(self) -> None:
        """Spawns an active item modifier on board."""
        rx = random.uniform(80.0, Settings.SCREEN_WIDTH - 80.0)
        ry = random.uniform(80.0, Settings.SCREEN_HEIGHT - 80.0)
        
        ptype = random.choice(list(Settings.POWERUP_TYPES.keys()))
        self.powerups.append(PowerUp(rx, ry, ptype))

    def add_floating_text(self, text: str, x: float, y: float, color: Tuple[int, int, int], size: int = 24) -> None:
        self.floating_texts.append(FloatingText(text, x, y, color, size))

    def handle_input(self, keys: Any) -> None:
        """Converts keyboard key bindings or touch coordinates into 2D directional vectors for snake slithering path."""
        if self.state != "PLAYING":
            return
            
        # 1. Check Mouse / Touch steer
        mouse_down = pygame.mouse.get_pressed()[0]
        if mouse_down:
            mx, my = pygame.mouse.get_pos()
            # Convert snake coordinates to screen space
            shake_offset = self.effects.get_shake_offset()
            spx, spy = self.camera.to_screen(self.snake.x, self.snake.y, shake_offset)
            
            dx = mx - spx
            dy = my - spy
            dist = (dx**2 + dy**2)**0.5
            if dist > 15.0:
                dx /= dist
                dy /= dist
                self.snake.set_target_direction(dx, dy)
                return  # Touch/Mouse overrides keyboard keys
            
        # 2. Keyboard steer fallback
        sets = self.save_manager.get_settings()
        control_scheme = sets.get("control_scheme", "WASD")
        
        dx, dy = 0.0, 0.0
        
        if control_scheme == "CUSTOM":
            kb = sets.get("keybindings", {
                "UP": pygame.K_UP,
                "DOWN": pygame.K_DOWN,
                "LEFT": pygame.K_LEFT,
                "RIGHT": pygame.K_RIGHT
            })
            if keys[kb["UP"]]: dy = -1.0
            elif keys[kb["DOWN"]]: dy = 1.0
            if keys[kb["LEFT"]]: dx = -1.0
            elif keys[kb["RIGHT"]]: dx = 1.0
        elif control_scheme == "WASD":
            if keys[pygame.K_w]: dy = -1.0
            elif keys[pygame.K_s]: dy = 1.0
            if keys[pygame.K_a]: dx = -1.0
            elif keys[pygame.K_d]: dx = 1.0
        else:
            # Arrow controls mapping
            if keys[pygame.K_UP]: dy = -1.0
            elif keys[pygame.K_DOWN]: dy = 1.0
            if keys[pygame.K_LEFT]: dx = -1.0
            elif keys[pygame.K_RIGHT]: dx = 1.0
            
        self.snake.set_target_direction(dx, dy)

    def update(self, dt: float) -> None:
        """Updates physics ticks, check collisions, and increments state frames."""
        self.effects.update(dt)
        
        # Toggle background rendering settings if Horror Mode
        sets = self.save_manager.get_settings()
        horror_mode_active = sets.get("horror_mode", False)
        
        if self.state == "PLAYING":
            # Apply Slow Motion factor if powerup is active
            time_scale = 0.4 if "Slow Motion" in self.active_powerups else 1.0
            tick_dt = dt * time_scale
            
            # Increment game timers
            self.game_time += dt
            self.save_manager.increment_stat("time_played_seconds", dt)
            
            # Level-up banner timer decay
            if self.levelup_banner_timer > 0.0:
                self.levelup_banner_timer -= dt
            
            # 1. Update powerup durations
            for name in list(self.active_powerups.keys()):
                self.active_powerups[name] -= dt
                if self.active_powerups[name] <= 0.0:
                    del self.active_powerups[name]
                    # Restore snake flags
                    self.sync_active_powerups_flags()
                    
            # Invulnerability timer
            if self.invulnerability_timer > 0.0:
                self.invulnerability_timer -= dt

            # 2. Update Snake Player
            # Speed boost powerup modifier
            speed_mult = 1.5 if "Speed Boost" in self.active_powerups else 1.0
            self.snake.update(tick_dt, speed_mult, self.particles)
            
            # Boundary checks
            self.check_boundary_collisions()
            # Body crashes
            self.check_self_collisions()

            # 3. Update Camera slither tracking
            self.camera.update(self.snake.x, self.snake.y, dt)
            
            # Zoom changes at speeds
            if speed_mult > 1.0:
                self.camera.set_zoom(0.85)
            elif self.boss:
                self.camera.set_zoom(0.9)
            else:
                self.camera.set_zoom(1.0)

            # 4. Update Foods (check bombs)
            for f in list(self.foods):
                alive = f.update(tick_dt, self.particles)
                if not alive:
                    # Bomb detonated
                    self.foods.remove(f)
                    self.audio_manager.play_sound("explosion")
                    self.effects.trigger_shake(12.0, 0.4)
                    # Check damage proximity to snake
                    dist_to_snake = Utils.distance((self.snake.x, self.snake.y), (f.x, f.y))
                    if dist_to_snake < 130.0:
                        self.take_damage(1)
                        
            # Attract food towards snake head if Magnet powerup is active
            if "Magnet" in self.active_powerups:
                self.apply_magnet_forces(tick_dt)
                
            # Collisions on food eating
            self.check_food_collisions()

            # 5. Spawning items randomly
            # Rare chance to drop powerup during gameplay
            if random.random() < 0.003 * tick_dt * 60.0 and len(self.powerups) < 2:
                self.spawn_powerup()
            # Replenish foods if count drops below target
            target_food_count = min(8, 3 + self.level // 12)
            if "Food Multiplier" in self.active_powerups:
                target_food_count *= 2
                
            if len(self.foods) < target_food_count and not self.boss:
                if len(self.foods) == 0 or random.random() < 0.01 * (tick_dt * 60.0):
                    self.spawn_food()

            # Respawn / Continuous Spawning of AI Battle Snakes
            if not self.boss:
                from enemy import AISnakeEnemy
                current_ai_snakes = [e for e in self.enemies if isinstance(e, AISnakeEnemy)]
                target_ai_cap = min(10, 3 + (self.level // 2))
                
                if not hasattr(self, "ai_spawn_timer"):
                    self.ai_spawn_timer = 0.0
                self.ai_spawn_timer += tick_dt
                
                should_spawn = False
                if len(current_ai_snakes) == 0:
                    should_spawn = True
                    self.ai_spawn_timer = 0.0
                elif self.ai_spawn_timer >= 12.0 and len(current_ai_snakes) < target_ai_cap:
                    should_spawn = True
                    self.ai_spawn_timer = 0.0
                    
                if should_spawn:
                    for _ in range(5):  # retry limit
                        ax = random.uniform(80.0, Settings.SCREEN_WIDTH - 80.0)
                        ay = random.uniform(80.0, Settings.SCREEN_HEIGHT - 80.0)
                        if Utils.distance((ax, ay), (self.snake.x, self.snake.y)) > 250.0:
                            self.enemies.append(AISnakeEnemy(ax, ay, self.level))
                            break

            # Update Powerups
            for p in self.powerups:
                p.update(tick_dt, self.particles)
            self.check_powerup_collisions()

            # 6. Update Enemy Hazards (Freeze Time pauses movements)
            enemy_dt = 0.0 if "Freeze Time" in self.active_powerups else tick_dt
            from enemy import AISnakeEnemy
            for e in self.enemies:
                if isinstance(e, AISnakeEnemy):
                    e.update((self.snake.x, self.snake.y), enemy_dt, self.particles, self.foods, self.powerups)
                else:
                    e.update((self.snake.x, self.snake.y), enemy_dt, self.particles)
            self.check_enemy_collisions()

            # 7. Update Boss Core
            if self.boss:
                boss_dt = 0.0 if "Freeze Time" in self.active_powerups else tick_dt
                self.boss.update((self.snake.x, self.snake.y), boss_dt, self.particles)
                self.check_boss_collisions()
                
            # 8. Update particles and texts buffers
            self.particles.update(tick_dt)
            self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]
            
            # 9. Update HUD ticks
            self.hud.update(self.score, self.save_manager.get_coins(), self.combo, dt)
            
            # Decay combo counter
            if self.combo > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0.0:
                    self.combo = 0

            # 10. Check Level Up constraints (not on Boss fights)
            if not self.boss and self.xp >= self.xp_needed:
                self.level_up()
                
        elif self.state == "MAIN":
            self.menu_system.update("MAIN", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "SHOP":
            self.menu_system.update("SHOP", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "SETTINGS":
            self.menu_system.update("SETTINGS", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "HIGHSCORES":
            self.menu_system.update("HIGHSCORES", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "ACHIEVEMENTS":
            self.menu_system.update("ACHIEVEMENTS", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "KEYBINDINGS":
            self.menu_system.update("KEYBINDINGS", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "HOWTOPLAY":
            self.menu_system.update("HOWTOPLAY", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "STATISTICS":
            self.menu_system.update("STATISTICS", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "CREDITS":
            self.menu_system.update("CREDITS", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "COUNTDOWN":
            self.countdown_timer -= dt
            if self.countdown_timer <= 0.0:
                self.state = "PLAYING"
                self.countdown_timer = 3.0
        elif self.state == "PAUSED":
            self.menu_system.update("PAUSED", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)
        elif self.state == "GAMEOVER":
            self.menu_system.update("GAMEOVER", pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0], self.is_mouse_clicked_frame(), dt)

    def is_mouse_clicked_frame(self) -> bool:
        """Returns True if the mouse button was newly pressed this frames."""
        return pygame.mouse.get_pressed()[0] and not hasattr(self, "_old_mouse_state") or (pygame.mouse.get_pressed()[0] and not self._old_mouse_state)

    def sync_active_powerups_flags(self) -> None:
        """Synchronizes snake modifiers to active timers dictionary."""
        self.snake.magnet_active = "Magnet" in self.active_powerups
        self.snake.shield_active = "Shield" in self.active_powerups
        self.snake.invincible_active = "Invincibility" in self.active_powerups
        self.snake.ghost_active = "Ghost Mode" in self.active_powerups

    def activate_powerup(self, name: str) -> None:
        """Sets active timer values on specific modifiers."""
        if name == "Random Power":
            power_choices = ["Magnet", "Shield", "Double Score", "Slow Motion", "Speed Boost", "Invincibility", "Freeze Time", "Ghost Mode", "Teleport", "Food Multiplier"]
            selected_power = random.choice(power_choices)
            self.activate_powerup(selected_power)
            return

        if name == "Teleport":
            # Blink forwards instantly along current direction
            blink_dist = 150.0
            bx = math.cos(self.snake.angle) * blink_dist
            by = math.sin(self.snake.angle) * blink_dist
            self.snake.x += bx
            self.snake.y += by
            # Offset all tail segments by the same distance so they follow smoothly
            self.snake.path = [(px + bx, py + by) for px, py in self.snake.path]
            self.particles.spawn_trail((self.snake.x, self.snake.y), Settings.COLOR_RED, 15)

        duration = Settings.POWERUP_TYPES.get(name, {}).get("duration", 10.0)
        self.active_powerups[name] = duration
        self.sync_active_powerups_flags()
        self.audio_manager.play_sound("powerup")
        self.add_floating_text(f"+{name.upper()} ACTIVE", self.snake.x, self.snake.y - 30, Settings.COLOR_GOLD)

        # Unlock Achievement "Charged Up" if 3 powerups are active
        if len(self.active_powerups) >= 3:
            self.trigger_achievement("power_trip")

    def apply_magnet_forces(self, dt: float) -> None:
        """Pulls foods towards snake head vector if within range bounds."""
        hx, hy = self.snake.x, self.snake.y
        magnet_range = 160.0
        pull_force = 220.0
        
        for f in self.foods:
            dx = hx - f.x
            dy = hy - f.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < magnet_range:
                # Add vector pull
                f.x += (dx / dist) * pull_force * dt
                f.y += (dy / dist) * pull_force * dt

    def check_food_collisions(self) -> None:
        hx, hy = self.snake.x, self.snake.y
        head_radius = 13.0
        
        for f in list(self.foods):
            dist = Utils.distance((hx, hy), (f.x, f.y))
            if dist < (head_radius + f.radius):
                # Eaten!
                f.on_eat(self.particles)
                self.foods.remove(f)
                self.audio_manager.play_sound("eat")
                
                # Grow snake (except Poison and Bomb)
                if f.type not in ["Poison", "Bomb"]:
                    self.snake.grow(1)
                
                # Apply score calculations + combo multipliers
                self.combo += 1
                self.combo_timer = self.combo_max
                
                score_mult = 2 if "Double Score" in self.active_powerups else 1
                added_points = f.score_value * self.combo * score_mult
                
                self.score += added_points
                self.xp += f.score_value * 0.8
                
                # Increment daily targets
                self.save_manager.increment_mission("eat_food", 1, self)
                self.save_manager.increment_mission("score_points", added_points, self)
                
                # Spawn float texts popup
                text_col = f.color if f.color != Settings.COLOR_CYAN else Settings.COLOR_WHITE
                self.add_floating_text(f"+{added_points}", f.x, f.y, text_col)
                if self.combo > 1:
                    self.add_floating_text(f"x{self.combo} Combo!", f.x, f.y + 15, Settings.COLOR_PINK, size=18)
                    
                # Store statistics
                self.save_manager.increment_stat("total_food_eaten", 1)
                self.save_manager.set_max_stat("max_combo_reached", self.combo)
                
                # Triggers custom food action values
                self.apply_food_eating_actions(f)

    def apply_food_eating_actions(self, f: Food) -> None:
        """Triggered upon contact to execute specific modifier shifts."""
        if f.type == "Golden":
            # Grant immediate coins
            coins_qty = 10
            self.coins_earned += coins_qty
            self.save_manager.add_coins(coins_qty)
            self.add_floating_text(f"+{coins_qty} Coins!", self.snake.x, self.snake.y - 30, Settings.COLOR_GOLD)
            self.trigger_achievement("first_bite")
            
        elif f.type == "Rainbow":
            coins_qty = 25
            self.coins_earned += coins_qty
            self.save_manager.add_coins(coins_qty)
            self.add_floating_text(f"+{coins_qty} Coins!", self.snake.x, self.snake.y - 30, Settings.COLOR_PINK)
            
        elif f.type == "Frozen":
            self.activate_powerup("Slow Motion")
            
        elif f.type == "Poison":
            # Cuts length and inflicts flash
            self.snake.shrink(2)
            self.take_damage(0)  # doesn't reduce lives, just visual shock/shrink
            self.add_floating_text("SHRINK!", self.snake.x, self.snake.y - 30, Settings.COLOR_RED)
            
        elif f.type == "Teleport":
            # Move snake coordinate randomly
            tx = random.uniform(100, Settings.SCREEN_WIDTH - 100)
            ty = random.uniform(100, Settings.SCREEN_HEIGHT - 100)
            self.snake.reset(tx, ty)
            self.particles.spawn_explosion((tx, ty), Settings.COLOR_PURPLE, count=15)
            self.audio_manager.play_sound("powerup")
            self.add_floating_text("BLINK!", tx, ty - 30, Settings.COLOR_PURPLE)
            
        elif f.type == "Ghost":
            self.activate_powerup("Ghost Mode")
            
        elif f.type == "Lucky":
            # Spawns random cluster of coins or golden items around
            for i in range(4):
                theta = i * (math.pi / 2.0)
                cx = self.snake.x + 50.0 * math.cos(theta)
                cy = self.snake.y + 50.0 * math.sin(theta)
                self.foods.append(Food(cx, cy, "Golden"))
            self.add_floating_text("LUCKY SPAWN!", self.snake.x, self.snake.y - 30, Settings.COLOR_GREEN)
            
        elif f.type == "Mystery Box":
            # Appraises random powerup
            power = random.choice(list(Settings.POWERUP_TYPES.keys()))
            self.activate_powerup(power)
            
        elif f.type == "Bomb":
            # Detonates bomb food
            self.audio_manager.play_sound("explosion")
            self.effects.trigger_shake(12.0, 0.4)
            self.take_damage(1)

        # BOSS LASER PROJECTILE EMISSION:
        # If fighting a boss, eating food fires a rocket laser directly at the boss Core!
        if self.boss:
            bx, by = self.boss.x, self.boss.y
            hx, hy = self.snake.x, self.snake.y
            dx = bx - hx
            dy = by - hy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 1.0:
                vx = (dx / dist) * 450.0
                vy = (dy / dist) * 450.0
                # Spawn rocket tracking projectile
                p = EnemyProjectile(hx, hy, vx, vy, size=8.0, color=Settings.COLOR_CYAN)
                self.boss_projectiles.append(p)
                self.audio_manager.play_sound("button_click")

    def check_powerup_collisions(self) -> None:
        hx, hy = self.snake.x, self.snake.y
        head_radius = 13.0
        
        for p in list(self.powerups):
            dist = Utils.distance((hx, hy), (p.x, p.y))
            if dist < (head_radius + p.radius):
                # Picked up!
                p.on_collect(self.particles)
                self.powerups.remove(p)
                self.activate_powerup(p.type)

    def check_boundary_collisions(self) -> None:
        """Prevents escaping boundaries, damaging snake or consuming shields."""
        hx, hy = self.snake.x, self.snake.y
        r = 13.0
        
        hit_wall = False
        
        if hx - r < 0:
            self.snake.x = r
            hit_wall = True
        elif hx + r > Settings.SCREEN_WIDTH:
            self.snake.x = Settings.SCREEN_WIDTH - r
            hit_wall = True
            
        if hy - r < 0:
            self.snake.y = r
            hit_wall = True
        elif hy + r > Settings.SCREEN_HEIGHT:
            self.snake.y = Settings.SCREEN_HEIGHT - r
            hit_wall = True
            
        if hit_wall:
            # Force immediate rebound bounce angle
            self.snake.angle = (self.snake.angle + math.pi) % (2.0 * math.pi)
            self.snake.target_angle = self.snake.angle
            
            # Inflict damage
            self.take_damage(1)

    def check_self_collisions(self) -> None:
        """Determines if snake slithers into its own body path."""
        # Ghost mode ignores self tail crash
        if "Ghost Mode" in self.active_powerups or "Invincibility" in self.active_powerups:
            return
            
        segments = self.snake.get_segments()
        if len(segments) < 8:
            return
            
        hx, hy = segments[0]
        # Ignore first 7 head-adjacent segments to avoid fake turn collisions
        for sx, sy in segments[7:]:
            dist = Utils.distance((hx, hy), (sx, sy))
            if dist < 14.0:
                # Crashed body!
                self.take_damage(1)
                break

    def check_enemy_collisions(self) -> None:
        """Updates collision overlaps with spikes, lasers, fireballs, and AI snakes."""
        hx, hy = self.snake.x, self.snake.y
        r = 13.0
        
        from enemy import AISnakeEnemy, LaserWall, MovingBomb
        
        player_segments = self.snake.get_segments()
        
        for e in list(self.enemies):
            if isinstance(e, AISnakeEnemy):
                # 1. AI head colliding with Player body
                # If the AI's head is close to any player segment: the AI snake dies!
                for idx, (psx, psy) in enumerate(player_segments):
                    dist = Utils.distance((e.x, e.y), (psx, psy))
                    if dist < (e.size + r):
                        if idx == 0:
                            self.take_damage(1)
                        # Check if AI has active shield
                        if hasattr(e, "shield_active") and e.shield_active:
                            if "Shield" in e.powerup_timers:
                                del e.powerup_timers["Shield"]
                            e.shield_active = False
                            e.angle += math.pi
                            e.target_angle = e.angle
                            break
                            
                        e.die(self.foods, self.particles)
                        self.audio_manager.play_sound("explosion")
                        if idx > 0:
                            self.kills += 1
                            self.save_manager.increment_stat("ai_snakes_killed", 1)
                            self.save_manager.set_max_stat("max_kills_in_run", self.kills)
                            self.add_floating_text("+1 KILL!", e.x, e.y, Settings.COLOR_PINK, size=24)
                        if e in self.enemies:
                            self.enemies.remove(e)
                        break
                        
                if e.is_dead:
                    continue
                    
                # 2. Player head colliding with AI body
                ai_segments = []
                for i in range(e.length):
                    idx_path = i * 10
                    if idx_path < len(e.path):
                        ai_segments.append(e.path[idx_path])
                # Skip first segment which is the head
                for asx, asy in ai_segments[1:]:
                    dist = Utils.distance((hx, hy), (asx, asy))
                    if dist < (r + e.size - 2):
                        self.take_damage(1)
                        break
                        
                # 3. AI head colliding with other AI body
                for other_e in self.enemies:
                    if other_e is not e and isinstance(other_e, AISnakeEnemy):
                        other_segments = []
                        for i in range(other_e.length):
                            idx_path = i * 10
                            if idx_path < len(other_e.path):
                                other_segments.append(other_e.path[idx_path])
                        for osx, osy in other_segments:
                            dist = Utils.distance((e.x, e.y), (osx, osy))
                            if dist < (e.size + other_e.size - 2):
                                # Check if AI has active shield
                                if hasattr(e, "shield_active") and e.shield_active:
                                    if "Shield" in e.powerup_timers:
                                        del e.powerup_timers["Shield"]
                                    e.shield_active = False
                                    e.angle += math.pi
                                    e.target_angle = e.angle
                                    break
                                    
                                e.die(self.foods, self.particles)
                                self.audio_manager.play_sound("explosion")
                                if e in self.enemies:
                                    self.enemies.remove(e)
                                break
                        if e.is_dead:
                            break
            
            # Laser wall handles coordinate intersection calculations separately
            elif isinstance(e, LaserWall):
                if e.collides_with_point((hx, hy)):
                    self.take_damage(1)
            else:
                # Sphere obstacle collider
                dist = Utils.distance((hx, hy), (e.x, e.y))
                if dist < (r + e.size):
                    self.take_damage(1)
                    
                    # Explode Moving Bombs on contact
                    if isinstance(e, MovingBomb):
                        e.is_dead = True
                        self.particles.spawn_explosion((e.x, e.y), Settings.COLOR_RED, count=20)
                        self.audio_manager.play_sound("explosion")
                        self.enemies.remove(e)

    def check_boss_collisions(self) -> None:
        """Runs collision ticks over Boss body shells, boss projectiles, and player counter-missiles."""
        if not self.boss:
            return
            
        hx, hy = self.snake.x, self.snake.y
        r = 13.0
        
        # 1. Player colliding directly with Boss Core
        dist = Utils.distance((hx, hy), (self.boss.x, self.boss.y))
        if dist < (r + self.boss.size):
            self.take_damage(1)
            # Rebound
            self.snake.angle = (self.snake.angle + math.pi) % (2.0 * math.pi)
            self.snake.target_angle = self.snake.angle
            
        # 2. Boss bullets hitting Player
        for p in list(self.boss.projectiles):
            p_dist = Utils.distance((hx, hy), (p.x, p.y))
            if p_dist < (r + p.size):
                self.take_damage(1)
                self.boss.projectiles.remove(p)
                
        # 3. Player counter-missiles hitting Boss Core
        for mp in list(self.boss_projectiles):
            # Advance counter missiles
            alive = mp.update(pygame.time.get_ticks() / 1000.0) # Dummy dt context
            if not alive:
                self.boss_projectiles.remove(mp)
                continue
                
            # Hit check on boss
            b_dist = Utils.distance((mp.x, mp.y), (self.boss.x, self.boss.y))
            if b_dist < (mp.size + self.boss.size):
                # Deals damage to boss Core!
                is_dead = self.boss.take_damage(15.0, self.particles)
                self.boss_projectiles.remove(mp)
                self.audio_manager.play_sound("hit")
                self.effects.trigger_shake(8.0, 0.2)
                
                # Floating damage indicator
                self.add_floating_text("-15 HP", self.boss.x, self.boss.y - 20, Settings.COLOR_RED)
                
                if is_dead:
                    self.defeat_boss()
                    break

    def defeat_boss(self) -> None:
        """Updates coins/achievements on boss defeat, clears board and loads next stage."""
        self.audio_manager.stop_music()
        self.audio_manager.play_sound("victory")
        self.effects.trigger_flash(Settings.COLOR_GOLD, 1.5)
        self.effects.trigger_shake(20.0, 1.2)
        
        # Boss coins rewards
        boss_reward_coins = 150 + (self.level // 10) * 100
        self.coins_earned += boss_reward_coins
        self.save_manager.add_coins(boss_reward_coins)
        
        # Stats
        self.save_manager.increment_stat("total_bosses_defeated", 1)
        self.save_manager.increment_mission("defeat_boss", 1, self)
        
        # Unlock Boss achievement
        if self.level == 10:
            self.trigger_achievement("slayer_1")
        elif self.level == 50:
            self.trigger_achievement("slayer_5")
            
        self.add_floating_text("BOSS DEFEATED!", Settings.SCREEN_WIDTH/2, Settings.SCREEN_HEIGHT/2, Settings.COLOR_GOLD, size=32)
        self.add_floating_text(f"+{boss_reward_coins} COINS", Settings.SCREEN_WIDTH/2, Settings.SCREEN_HEIGHT/2 + 40, Settings.COLOR_GOLD, size=24)
        
        # Immediate Level Up transition
        self.level_up()

    def take_damage(self, amount: int) -> None:
        """Reduces player lives, applies shield buffers, and flashes screen."""
        if self.snake.is_dead:
            return
            
        # 1. Check Invulnerability buffers or shield active
        if self.invulnerability_timer > 0.0 or "Invincibility" in self.active_powerups:
            return
            
        if "Shield" in self.active_powerups:
            # Consume shield
            del self.active_powerups["Shield"]
            self.sync_active_powerups_flags()
            
            # Visual protection triggers
            self.invulnerability_timer = 1.5  # Temporary relief
            self.audio_manager.play_sound("hit")
            self.effects.trigger_flash(Settings.COLOR_BLUE, 0.4)
            self.effects.trigger_shake(8.0, 0.3)
            self.particles.spawn_sparks((self.snake.x, self.snake.y), Settings.COLOR_BLUE, count=12)
            self.add_floating_text("SHIELD BROKEN!", self.snake.x, self.snake.y - 30, Settings.COLOR_BLUE)
            return

        # 2. Subtract life
        self.lives -= amount
        self.invulnerability_timer = 2.0  # i-frames
        self.combo = 0  # reset combo
        
        self.audio_manager.play_sound("hit")
        self.effects.trigger_flash(Settings.COLOR_RED, 0.6)
        self.effects.trigger_shake(15.0, 0.5)
        self.particles.spawn_explosion((self.snake.x, self.snake.y), Settings.COLOR_RED, count=25)
        
        if self.lives > 0:
            self.add_floating_text(f"LIVES: {self.lives}", self.snake.x, self.snake.y - 30, Settings.COLOR_RED)
        else:
            # Trigger Death state
            self.snake.is_dead = True
            self.audio_manager.play_sound("game_over")
            self.set_state("GAMEOVER")
            self.add_floating_text("GAME OVER!", self.snake.x, self.snake.y, Settings.COLOR_RED, size=36)
            
            # Save stats
            self.save_manager.increment_stat("total_deaths", 1)

    def level_up(self) -> None:
        """Increments stage, plays indicators, triggers next level spawn."""
        self.level += 1
        self.xp = 0.0
        
        # Trigger level-up banner
        self.levelup_banner_timer = 2.5
        self.levelup_banner_level = self.level
        
        # Increment max levels stat
        self.save_manager.set_max_stat("max_level_reached", self.level)
        
        # Check level awards achievements
        if self.level == 10:
            self.trigger_achievement("level_10")
        elif self.level == 50:
            self.trigger_achievement("level_50")
        elif self.level == 100:
            self.trigger_achievement("level_100")
            
        # Play sounds
        self.audio_manager.play_sound("level_up")
        self.effects.trigger_flash(Settings.COLOR_GREEN, 0.8)
        
        # Load the new stage structures
        self.load_level()

    def trigger_achievement(self, ach_id: str) -> None:
        """Unlocks an achievement via SaveManager and triggers popup on HUD."""
        newly_unlocked = self.save_manager.unlock_achievement(ach_id)
        if newly_unlocked:
            # Alert floating text
            ach_title = ""
            reward = 0
            for a in Settings.ACHIEVEMENTS:
                if a["id"] == ach_id:
                    ach_title = a["name"]
                    reward = a["reward"]
                    break
                    
            self.add_floating_text("ACHIEVEMENT UNLOCKED!", self.snake.x, self.snake.y - 60, Settings.COLOR_PINK, size=24)
            self.add_floating_text(f"'{ach_title.upper()}' (+{reward} Coins)", self.snake.x, self.snake.y - 35, Settings.COLOR_GOLD, size=18)

    def save_game_progress(self) -> None:
        """Saves current accumulated profile stats to JSON files."""
        # Update high score
        self.save_manager.update_score = self.save_manager.update_high_score(self.score)
        
        # Check score achievements
        if self.score >= 1000:
            self.trigger_achievement("high_score_1k")
        if self.score >= 5000:
            self.trigger_achievement("high_score_5k")
            
        # Check coins achievements
        total_coins = self.save_manager.data["stats"]["total_coins_collected"]
        if total_coins >= 1000:
            self.trigger_achievement("coin_collector")
            
        # Check skin hoarder
        unlocked_skins_cnt = len(self.save_manager.data["unlocked_skins"])
        if unlocked_skins_cnt >= 5:
            self.trigger_achievement("skin_hoarder")
            
        # Check horror mode score
        sets = self.save_manager.get_settings()
        if sets.get("horror_mode", False) and self.score >= 500:
            self.trigger_achievement("horror_survivor")
            
        # Auto save to file
        self.save_manager.save()

    def draw(self) -> None:
        """Core draw pipeline: parallax, snake paths, items, camera transformations, post-effects, HUDS."""
        # Clean screen buffer first using camera parallax sky
        shake_offset = self.effects.get_shake_offset()
        self.camera.draw_parallax_background(self.screen, self.stars, shake_offset)
        
        # Fetch current equipped skin
        equipped_skin = self.save_manager.get_current_skin()
        
        if self.state in ["PLAYING", "GAMEOVER", "PAUSED", "COUNTDOWN"]:
            # Camera offset values to apply coordinates transformations
            ox, oy = self.camera.get_offset(shake_offset)
            
            if pygame.time.get_ticks() % 60 == 0:
                food_info = f"({self.foods[0].x:.1f}, {self.foods[0].y:.1f}, {self.foods[0].radius:.1f})" if self.foods else "None"
                print(f"[DEBUG] State: {self.state}, Snake: ({self.snake.x:.1f}, {self.snake.y:.1f}), Camera: ({self.camera.x:.1f}, {self.camera.y:.1f}), ox/oy: ({ox:.1f}, {oy:.1f}), Zoom: {self.camera.zoom:.2f}, Foods Count: {len(self.foods)}, First Food: {food_info}")
            
            # Find closest food coords for eyes look vector
            closest_f_pos = None
            if len(self.foods) > 0:
                closest_f = min(self.foods, key=lambda f: Utils.distance((self.snake.x, self.snake.y), (f.x, f.y)))
                closest_f_pos = (closest_f.x, closest_f.y)
                
            # 1. Render Spikes/Hazards
            for e in self.enemies:
                e.draw(self.screen, (ox, oy))
                
            # 2. Render Power-ups
            for p in self.powerups:
                p.draw(self.screen, (ox, oy))
                
            # 3. Render Foods
            for f in self.foods:
                f.draw(self.screen, (ox, oy))
                
            # 4. Render Snake segments
            # Toggle visibility during i-frames to show hit flashes
            if self.invulnerability_timer > 0.0:
                # Blink head every 0.15s
                if int(self.invulnerability_timer * 10) % 2 == 0:
                    self.snake.draw(self.screen, (ox, oy), equipped_skin, closest_f_pos)
            else:
                self.snake.draw(self.screen, (ox, oy), equipped_skin, closest_f_pos)
                
            # 5. Render Boss core
            if self.boss:
                self.boss.draw(self.screen, (ox, oy))
                
            # 6. Render Player missile lasers
            for mp in self.boss_projectiles:
                mp.draw(self.screen, (ox, oy))
                
            # 7. Render Particle Emitters
            self.particles.draw(self.screen, (ox, oy))
            
            # 8. Render Floating Points text
            for ft in self.floating_texts:
                ft.draw(self.screen, self.font_sm, (ox, oy))
                
            # 9. Apply HORROR MODE overlay multiply textures
            sets = self.save_manager.get_settings()
            if sets.get("horror_mode", False):
                # Screen center of flashlight is player head screenspace coordinate
                spx, spy = self.camera.to_screen(self.snake.x, self.snake.y, shake_offset)
                # Flicker light source occasionally
                self.effects.draw_horror_vignette(self.screen, (spx, spy), flicker=True)
                
            # 10. Draw Screen Space overlays (damage static glitches)
            if self.effects.glitch_active or (sets.get("horror_mode", False) and random.random() < 0.02):
                self.effects.apply_screen_glitch(self.screen)
                
            # Apply Chromatic Aberrations during heavy hits
            if self.invulnerability_timer > 1.5:
                self.effects.apply_chromatic_aberration(self.screen, offset_x=6)
                
            # Apply additive Bloom glowing simulation filter
            # Render game elements to a smaller surface to blur it
            if not sets.get("horror_mode", False):
                # Draw bloom
                pass  # Optional additional pass if required, standard glow circles cover base bloom visually

            # 11. Draw HUD overlays
            self.hud.draw_hud(
                self.screen, 
                self.score, 
                self.coins_earned, 
                self.combo, 
                self.combo_timer, 
                self.combo_max,
                self.level, 
                self.xp, 
                self.xp_needed, 
                self.lives, 
                self.snake.shield_active,
                self.active_powerups, 
                self.kills,
                self.font_sm, 
                self.font_md
            )
            
            # Draw boss HP bar
            if self.boss:
                self.hud.draw_boss_health(self.screen, self.boss.health, self.boss.max_health, self.boss.name, self.font_md)
                
            # Draw Minimap
            self.hud.draw_minimap(self.screen, self.snake, self.foods, self.powerups, self.enemies, self.boss)
                
            # Draw Level-Up Banner
            if self.levelup_banner_timer > 0.0:
                self.draw_levelup_banner()

            # Countdown Screen
            if self.state == "COUNTDOWN":
                self.draw_countdown_screen()

            # Pause Screen Overlay Text
            if self.state == "PAUSED":
                self.draw_pause_screen()
                
            # GameOver overlay panel
            if self.state == "GAMEOVER":
                self.draw_gameover_screen()

        else:
            # Render Navigation Menu System widgets
            self.menu_system.draw(self.screen, self.state, self.font_sm, self.font_md, self.font_lg)
            
        # Draw screen flashes overlay
        self.effects.draw_flash(self.screen)
        
        # Save mouse state
        self._old_mouse_state = pygame.mouse.get_pressed()[0]

    def draw_pause_screen(self) -> None:
        """Renders blurry screen overlay indicating pause with interactive buttons."""
        pause_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pause_overlay.fill((10, 10, 15, 200))  # Semi-transparent dark mask
        self.screen.blit(pause_overlay, (0, 0))
        
        t_surf = self.font_lg.render("GAME PAUSED", True, Settings.COLOR_CYAN)
        self.screen.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, 130))
        
        # Draw buttons
        for b in self.menu_system.buttons.get("PAUSED", []):
            b.draw(self.screen, self.font_sm)

    def draw_gameover_screen(self) -> None:
        """Renders score panels, detailed stats breakdown, and retry buttons."""
        go_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        go_overlay.fill((20, 5, 5, 220))
        self.screen.blit(go_overlay, (0, 0))
        
        t_surf = self.font_lg.render("GAME OVER", True, Settings.COLOR_RED)
        self.screen.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, 80))
        
        # Stats panel card
        stats_rect = pygame.Rect(self.width // 2 - 200, 160, 400, 190)
        Utils.draw_rounded_rect(self.screen, stats_rect, (15, 15, 25, 200), radius=12)
        Utils.draw_rounded_rect(self.screen, stats_rect, Settings.COLOR_RED, radius=12, border_width=1)
        
        stats = [
            ("FINAL SCORE", f"{self.score}"),
            ("STAGE LEVEL", f"{self.level}"),
            ("COINS EARNED", f"{self.coins_earned}"),
            ("AI KILLS", f"{self.kills}"),
            ("TIME SURVIVED", f"{int(self.game_time)}s")
        ]
        
        y = 175
        for label, val in stats:
            label_surf = self.font_sm.render(label, True, Settings.COLOR_GRAY)
            val_surf = self.font_md.render(val, True, Settings.COLOR_WHITE)
            self.screen.blit(label_surf, (self.width // 2 - 170, y + 3))
            self.screen.blit(val_surf, (self.width // 2 + 170 - val_surf.get_width(), y))
            y += 32
            
        # Draw buttons
        for b in self.menu_system.buttons.get("GAMEOVER", []):
            b.draw(self.screen, self.font_sm)

    def draw_countdown_screen(self) -> None:
        """Renders a pulsing 3...2...1...GO! overlay text."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 100))
        self.screen.blit(overlay, (0, 0))
        
        val = int(math.ceil(self.countdown_timer))
        text = f"{val}" if val > 0 else "GO!"
        
        fract = self.countdown_timer - int(self.countdown_timer)
        if fract < 0: fract = 0
        scale = 1.0 + 0.4 * math.sin(fract * math.pi)
        
        txt_surf = self.font_lg.render(text, True, Settings.COLOR_CYAN if text != "GO!" else Settings.COLOR_GREEN)
        scaled_w = int(txt_surf.get_width() * scale)
        scaled_h = int(txt_surf.get_height() * scale)
        txt_surf = pygame.transform.smoothscale(txt_surf, (scaled_w, scaled_h))
        
        self.screen.blit(txt_surf, (self.width // 2 - scaled_w // 2, self.height // 2 - scaled_h // 2))

    def draw_levelup_banner(self) -> None:
        """Renders an animated LEVEL UP! banner notification."""
        alpha = 255
        if self.levelup_banner_timer < 0.5:
            alpha = int(255 * (self.levelup_banner_timer / 0.5))
            
        banner_surf = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        banner_surf.fill((15, 25, 15, int(180 * (alpha / 255.0))))
        
        pygame.draw.line(banner_surf, Settings.COLOR_GREEN, (0, 0), (self.width, 0), 2)
        pygame.draw.line(banner_surf, Settings.COLOR_GREEN, (0, 98), (self.width, 98), 2)
        
        lvl_surf = self.font_lg.render(f"LEVEL UP! REACHED LEVEL {self.levelup_banner_level}", True, Settings.COLOR_GREEN)
        banner_surf.blit(lvl_surf, (self.width // 2 - lvl_surf.get_width() // 2, 50 - lvl_surf.get_height() // 2))
        
        banner_surf.set_alpha(alpha)
        self.screen.blit(banner_surf, (0, self.height // 2 - 120))
