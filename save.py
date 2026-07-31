import os
import sys
import json
import pygame
from typing import Dict, List, Any
from settings import Settings

class SaveManager:
    def __init__(self, data_dir: str = None) -> None:
        if data_dir is None:
            # For frozen exe: save data next to the executable (writable)
            # For dev mode: save data next to the script
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            
        self.save_path = os.path.join(self.data_dir, "save.json")
        self.data: Dict[str, Any] = self.get_default_data()
        self.load()

    def get_default_data(self) -> Dict[str, Any]:
        """Returns the default profile structure for a fresh player profile."""
        return {
            "high_score": 0,
            "coins": 0,
            "unlocked_skins": ["classic"],
            "current_skin": "classic",
            "unlocked_achievements": [],
            "missions": [
                {"id": "eat_food", "text": "Eat 25 Food Units", "target": 25, "current": 0, "reward": 80, "completed": False},
                {"id": "defeat_boss", "text": "Defeat a Boss Core", "target": 1, "current": 0, "reward": 150, "completed": False},
                {"id": "score_points", "text": "Reach 1,500 Score", "target": 1500, "current": 0, "reward": 100, "completed": False}
            ],
            "settings": {
                "music_volume": 0.5,
                "sfx_volume": 0.6,
                "fullscreen": False,
                "fps_limit": 60,
                "resolution": "1280x720",
                "control_scheme": "WASD",  # WASD or Arrows
                "difficulty": "Medium",
                "horror_mode": False,
                "keybindings": {
                    "UP": pygame.K_UP,
                    "DOWN": pygame.K_DOWN,
                    "LEFT": pygame.K_LEFT,
                    "RIGHT": pygame.K_RIGHT
                }
            },
            "stats": {
                "total_food_eaten": 0,
                "total_deaths": 0,
                "total_bosses_defeated": 0,
                "total_coins_collected": 0,
                "ai_snakes_killed": 0,
                "games_played": 0,
                "time_played_seconds": 0.0,
                "max_level_reached": 1,
                "max_combo_reached": 0,
                "max_kills_in_run": 0
            }
        }

    def load(self) -> None:
        """Loads save game data from the JSON file. Reverts to default if file is missing or corrupt."""
        if not os.path.exists(self.save_path):
            self.data = self.get_default_data()
            self.save()
            return

        try:
            with open(self.save_path, 'r') as f:
                loaded = json.load(f)
                # Verify loaded structure and fill missing keys to maintain backward compatibility
                self.data = self._merge_dict(self.get_default_data(), loaded)
        except (json.JSONDecodeError, IOError):
            print("[SaveManager] Warning: Save file corrupted or unreadable. Resetting to defaults.")
            self.data = self.get_default_data()
            self.save()

    def save(self) -> bool:
        """Writes current data state to JSON save path."""
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            return True
        except IOError as e:
            print(f"[SaveManager] Error: Failed to write save file. {e}")
            return False

    def _merge_dict(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merges a loaded dictionary into default structure to keep keys synchronized."""
        for k, v in default.items():
            if k not in loaded:
                loaded[k] = v
            elif isinstance(v, dict):
                loaded[k] = self._merge_dict(v, loaded[k])
        return loaded

    # Convenience API helper methods
    def get_high_score(self) -> int:
        return self.data.get("high_score", 0)

    def update_high_score(self, score: int) -> bool:
        if score > self.data["high_score"]:
            self.data["high_score"] = score
            self.save()
            return True
        return False

    def get_coins(self) -> int:
        return self.data.get("coins", 0)

    def add_coins(self, amount: int) -> None:
        if amount > 0:
            self.data["coins"] += amount
            self.data["stats"]["total_coins_collected"] += amount
            self.save()

    def deduct_coins(self, amount: int) -> bool:
        if 0 <= amount <= self.data["coins"]:
            self.data["coins"] -= amount
            self.save()
            return True
        return False

    def get_current_skin(self) -> str:
        return self.data.get("current_skin", "classic")

    def set_current_skin(self, skin_id: str) -> None:
        if skin_id in self.data["unlocked_skins"]:
            self.data["current_skin"] = skin_id
            self.save()

    def unlock_skin(self, skin_id: str, cost: int) -> bool:
        if skin_id not in self.data["unlocked_skins"]:
            if self.deduct_coins(cost):
                self.data["unlocked_skins"].append(skin_id)
                self.save()
                return True
        return False

    def unlock_achievement(self, achievement_id: str) -> bool:
        """Returns True if the achievement was newly unlocked, False if already unlocked."""
        if achievement_id not in self.data["unlocked_achievements"]:
            self.data["unlocked_achievements"].append(achievement_id)
            # Fetch reward amount from settings
            reward = 0
            for ach in Settings.ACHIEVEMENTS:
                if ach["id"] == achievement_id:
                    reward = ach["reward"]
                    break
            self.add_coins(reward)
            self.save()
            return True
        return False

    def get_settings(self) -> Dict[str, Any]:
        return self.data.get("settings", {})

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        self.data["settings"].update(new_settings)
        self.save()

    def increment_stat(self, key: str, increment: int = 1) -> None:
        if key in self.data["stats"]:
            self.data["stats"][key] += increment
            self.save()

    def set_max_stat(self, key: str, value: int) -> None:
        if key in self.data["stats"]:
            if value > self.data["stats"][key]:
                self.data["stats"][key] = value
                self.save()

    def increment_mission(self, mission_id: str, amount: int = 1, game_engine: Any = None) -> None:
        """Increments current progress of a specific mission, triggering completion rewards if achieved."""
        for m in self.data.get("missions", []):
            if m["id"] == mission_id and not m["completed"]:
                m["current"] += amount
                if m["current"] >= m["target"]:
                    m["current"] = m["target"]
                    m["completed"] = True
                    # Reward coins
                    reward = m["reward"]
                    self.add_coins(reward)
                    if game_engine:
                        game_engine.add_floating_text(
                            f"MISSION COMPLETED: {m['text']} (+{reward} Coins)!",
                            game_engine.snake.x,
                            game_engine.snake.y - 45,
                            Settings.COLOR_GOLD,
                            size=20
                        )
                self.save()
