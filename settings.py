"""
settings.py - Game configurations, design system, colors, and constant data structures.
"""
from typing import Dict, List, Tuple, Any

class Settings:
    # Screen & System Configs
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    DEFAULT_FPS: int = 60
    CELL_SIZE: int = 24  # Size of a grid cell
    GRID_WIDTH: int = SCREEN_WIDTH // CELL_SIZE
    GRID_HEIGHT: int = SCREEN_HEIGHT // CELL_SIZE

    # Design System & Colors
    # Deep Cyberpunk Dark Background and Neon Accents
    BG_COLOR: Tuple[int, int, int] = (10, 10, 15)
    BG_GRID_COLOR: Tuple[int, int, int] = (20, 20, 30)
    
    # Neon Colors
    COLOR_CYAN: Tuple[int, int, int] = (0, 240, 255)
    COLOR_PINK: Tuple[int, int, int] = (255, 0, 85)
    COLOR_GREEN: Tuple[int, int, int] = (57, 255, 20)
    COLOR_GOLD: Tuple[int, int, int] = (255, 215, 0)
    COLOR_PURPLE: Tuple[int, int, int] = (189, 0, 255)
    COLOR_ORANGE: Tuple[int, int, int] = (255, 127, 80)
    COLOR_RED: Tuple[int, int, int] = (255, 20, 20)
    COLOR_BLUE: Tuple[int, int, int] = (30, 144, 255)
    COLOR_WHITE: Tuple[int, int, int] = (245, 245, 250)
    COLOR_GRAY: Tuple[int, int, int] = (120, 120, 130)
    COLOR_DARK_GRAY: Tuple[int, int, int] = (40, 40, 45)
    COLOR_BLOOD_RED: Tuple[int, int, int] = (139, 0, 0)

    # Difficulty Settings
    DIFFICULTIES: Dict[str, Dict[str, Any]] = {
        "Easy": {
            "start_speed": 4.5,
            "speed_increment": 0.05,
            "enemy_spawn_chance": 0.05,
            "coin_multiplier": 1.0,
            "boss_health_multiplier": 0.7,
        },
        "Medium": {
            "start_speed": 6.0,
            "speed_increment": 0.08,
            "enemy_spawn_chance": 0.12,
            "coin_multiplier": 1.5,
            "boss_health_multiplier": 1.0,
        },
        "Hard": {
            "start_speed": 8.0,
            "speed_increment": 0.12,
            "enemy_spawn_chance": 0.22,
            "coin_multiplier": 2.0,
            "boss_health_multiplier": 1.4,
        },
        "Impossible": {
            "start_speed": 10.5,
            "speed_increment": 0.18,
            "enemy_spawn_chance": 0.35,
            "coin_multiplier": 3.0,
            "boss_health_multiplier": 2.0,
        }
    }

    # Food Configurations
    # Format: (Score Value, Base Chance, Color, Glow Radius, Description)
    FOOD_TYPES: Dict[str, Dict[str, Any]] = {
        "Normal": {"score": 10, "chance": 65, "color": COLOR_CYAN, "glow": 12, "desc": "Standard energy block"},
        "Golden": {"score": 50, "chance": 12, "color": COLOR_GOLD, "glow": 16, "desc": "Gives extra points + coins"},
        "Rainbow": {"score": 100, "chance": 5, "color": COLOR_PINK, "glow": 20, "desc": "Ultimate high score feed"},
        "Frozen": {"score": 15, "chance": 5, "color": COLOR_BLUE, "glow": 14, "desc": "Slows game speed temporarily"},
        "Poison": {"score": -20, "chance": 4, "color": COLOR_BLOOD_RED, "glow": 10, "desc": "Reduces size & score"},
        "Teleport": {"score": 15, "chance": 3, "color": COLOR_PURPLE, "glow": 14, "desc": "Teleports head location"},
        "Ghost": {"score": 20, "chance": 2, "color": COLOR_WHITE, "glow": 14, "desc": "Enables passing through body"},
        "Lucky": {"score": 30, "chance": 2, "color": COLOR_GREEN, "glow": 16, "desc": "Spawns visual items/coins"},
        "Mystery Box": {"score": 0, "chance": 1, "color": COLOR_ORANGE, "glow": 18, "desc": "Random reward or trick"},
        "Bomb": {"score": -5, "chance": 1, "color": COLOR_RED, "glow": 22, "desc": "Explodes if eaten or timed out"}
    }

    # Powerup Configurations
    # Format: (Duration in seconds, Color, Description)
    POWERUP_TYPES: Dict[str, Dict[str, Any]] = {
        "Magnet": {"duration": 12.0, "color": COLOR_CYAN, "desc": "Attracts food within range"},
        "Shield": {"duration": 15.0, "color": COLOR_BLUE, "desc": "Absorbs one crash hazard"},
        "Double Score": {"duration": 10.0, "color": COLOR_GOLD, "desc": "Double points for food"},
        "Slow Motion": {"duration": 8.0, "color": COLOR_GREEN, "desc": "Slows down obstacles/speed"},
        "Speed Boost": {"duration": 7.0, "color": COLOR_ORANGE, "desc": "Increases speed + multiplier"},
        "Invincibility": {"duration": 6.0, "color": COLOR_PINK, "desc": "Immune to all hazards"},
        "Freeze Time": {"duration": 5.0, "color": COLOR_WHITE, "desc": "Stops all moving enemies"},
        "Ghost Mode": {"duration": 10.0, "color": COLOR_PURPLE, "desc": "Allows passing self body"},
        "Teleport": {"duration": 1.0, "color": COLOR_RED, "desc": "Blink forwards instantly"},
        "Food Multiplier": {"duration": 10.0, "color": COLOR_GREEN, "desc": "Multiplies food spawn rate"},
        "Random Power": {"duration": 8.0, "color": COLOR_GOLD, "desc": "Applies a random perk"}
    }

    # Unlockable Snake Skins
    # Format: Name, Unlock Cost (Coins), Style/Type, Primary Color, Secondary Color
    SKINS: List[Dict[str, Any]] = [
        {"id": "classic", "name": "Classic Neon", "cost": 0, "primary": COLOR_CYAN, "secondary": COLOR_BLUE, "style": "solid"},
        {"id": "cyberpunk", "name": "Cyberpunk Gold", "cost": 100, "primary": COLOR_GOLD, "secondary": COLOR_PINK, "style": "gradient"},
        {"id": "fire", "name": "Solar Inferno", "cost": 250, "primary": COLOR_RED, "secondary": COLOR_ORANGE, "style": "fire"},
        {"id": "frost", "name": "Glacial Frost", "cost": 250, "primary": COLOR_WHITE, "secondary": COLOR_BLUE, "style": "gradient"},
        {"id": "shadow", "name": "Shadow Stalker", "cost": 400, "primary": COLOR_DARK_GRAY, "secondary": COLOR_PURPLE, "style": "translucent"},
        {"id": "zebra", "name": "Zebra Stripe", "cost": 500, "primary": COLOR_WHITE, "secondary": BG_COLOR, "style": "stripes"},
        {"id": "tiger", "name": "Tiger Strike", "cost": 600, "primary": COLOR_ORANGE, "secondary": BG_COLOR, "style": "stripes"},
        {"id": "hazard", "name": "Bio Hazard", "cost": 750, "primary": COLOR_GREEN, "secondary": COLOR_DARK_GRAY, "style": "stripes"},
        {"id": "disco", "name": "Retro Disco", "cost": 1000, "primary": COLOR_PINK, "secondary": COLOR_PURPLE, "style": "glow_shift"},
        {"id": "rainbow", "name": "Chroma Prism", "cost": 1500, "primary": COLOR_GREEN, "secondary": COLOR_CYAN, "style": "rainbow"},
        {"id": "void", "name": "Void Lord", "cost": 2000, "primary": (15, 15, 25), "secondary": COLOR_PURPLE, "style": "glitch"}
    ]

    # Offline Achievements list
    ACHIEVEMENTS: List[Dict[str, Any]] = [
        {"id": "first_bite", "name": "First Bite", "desc": "Eat your first piece of food", "reward": 50},
        {"id": "level_10", "name": "Leveling Up", "desc": "Reach Level 10", "reward": 100},
        {"id": "level_50", "name": "Snake Veteran", "desc": "Reach Level 50", "reward": 500},
        {"id": "level_100", "name": "Snake Deity", "desc": "Reach Level 100", "reward": 2000},
        {"id": "slayer_1", "name": "Boss Slayer I", "desc": "Defeat the Level 10 Boss", "reward": 200},
        {"id": "slayer_5", "name": "Boss Slayer V", "desc": "Defeat the Level 50 Boss", "reward": 1000},
        {"id": "high_score_1k", "name": "Point Accumulator", "desc": "Reach 1,000 score in a single run", "reward": 250},
        {"id": "high_score_5k", "name": "Apex Predator", "desc": "Reach 5,000 score in a single run", "reward": 1000},
        {"id": "coin_collector", "name": "Golden Greed", "desc": "Collect 1,000 total coins", "reward": 300},
        {"id": "skin_hoarder", "name": "Tailor Shop", "desc": "Unlock 5 different skins", "reward": 500},
        {"id": "power_trip", "name": "Charged Up", "desc": "Have 3 powerups active simultaneously", "reward": 400},
        {"id": "horror_survivor", "name": "Fearing Nothing", "desc": "Score 500 points in Horror Mode", "reward": 600}
    ]
