# Neon Snake: Expert Community Edition 🐍✨

## 🚀 Play Live in Browser & Download Desktop App

- **🌐 Play Instantly on Mobile & PC (Web Browser):** [**Click Here to Play Live**](https://vaibhavmishra2026.github.io/NeonSnake/)
- **💻 Download for Desktop (Windows App):** [**Download NeonSnakeArena.exe (17.5 MB)**](https://github.com/VAIBHAVMISHRA2026/NeonSnake/raw/main/dist/NeonSnakeArena.exe)

---

Neon Snake is a highly polished, arcade-action, modern reimagining of the classic snake game written in Python 3.14+ using **Pygame Community Edition**. It features sub-pixel movement interpolation, 11 different unlockable skins, procedural audio synthesizer, particle explosion bursts, screen effects (shake, flash, chromatic aberration, glitched scanlines), boss fights, multiple items/powerups, and an optional atmosphere-driven **Horror Mode**.

## Features

- **Procedural Graphics & Audio**: Generates all game texture/image/audio files at first launch using custom waveform math overlays to run instantly, out-of-the-box, without heavy external downloads.
- **Fluid Sub-pixel Slithering**: Snake body segments dynamically trace head history coordinates with distance-based interpolation step filters, producing fluid slithering movements.
- **11 Unlockable Skins**: Equip skins like Solar Inferno (fire size/color ripples), Glacial Frost, Shadow Stalker (translucent overlays), Chroma Prism (dynamic rainbow hue shifts), or Void Lord (bugged offsets).
- **10 Foods & 11 Powerups**: Feed on Rainbow or Teleport items, fire laser missiles at Boss cores, magnetize surroundings, slow time, or deploy energy shields.
- **Special Boss Fights**: Defeat custom bosses (e.g. "Viper Mech") every 10 levels, dodging projectile bullet circles, sweeps, and shields.
- **Horror Mode Toggle**: Restricts screen views using vignette fog centers attached to the head, adds static line glitches, and changes soundtrack loops.

---

## Directory Structure

```
game/
│
├── main.py                # Entry point & Windows event handlers
├── game.py                # Core GameEngine orchestrator
├── settings.py            # Design themes, skin arrays, constant parameters
├── snake.py               # Interpolated path slithering & skin renders
├── food.py                # 10 specialized glowing foods
├── powerups.py            # Active item timers & status icons
├── enemy.py               # Standard hazards (Spikes, LaserWall) & Bosses
├── particles.py           # Bursts, smoke, spark trails manager
├── effects.py             # Aberration, screen shake & horror vignetting
├── camera.py              # Lerp-focused viewports & parallax space stars
├── audio.py               # Sound channels controller & volume sliders
├── ui.py                  # Custom buttons, floating text popups, HUD sliders
├── menu.py                # State-driven dashboards (Shop, Settings, Trophy Vault)
├── save.py                # Persistent JSON progress trackers
├── utils.py               # Math, line-drawing, audio synth WAV engines
│
├── requirements.txt       # Dependencies declaration
├── README.md              # Project documentation
└── LICENSE                # MIT details
```

---

## Installation & Running

### 1. Requirements

Make sure you have **Python 3.13+** installed. Install the Python dependency:

```bash
pip install -r requirements.txt
```

*(Note: `pygame-ce` is required, which is fully compatible with standard `pygame` but includes additional optimizations and features)*

### 2. Run the Game

Execute the main controller module:

```bash
python main.py
```

---

## Game Controls

| Key | Action |
| --- | --- |
| **W, A, S, D** or **Arrow Keys** | Slither movement directions |
| **ESC** | Pause / Unpause playing (or Back from menus) |
| **R** | Quick restart round (during play or game over) |
| **F** | Toggle Fullscreen |
| **M** | Toggle Mute |

---

## Screenshots Placeholder

![Neon Snake Menu](assets/images/logo.png)
*(Procedural neon title text generated at startup in `assets/images/logo.png`)*

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
