# BOMB!

A classic bomb-throwing arcade game (a Bomberman-like) written in **Python** with **Pygame**.
Blackscreen grid of bricks, exploding bombs, patrolling enemies that hunt you via BFS pathfinding, power-ups, levels, lives, and a local high-score board.

## Features

- **Bombs** – up to 3 at once, 2.2 s fuse, explosion range up to 3 cells (expandable)
- **Enemies** – up to 1 per 1 s, more each level, chase the player with **BFS pathfinding** (they dodge around placed bombs)
- **Power-ups** (drop when a brick breaks, 15 % chance):
  - extra bomb
  - bigger explosion range
  - speed boost (8 s)
  - extra life
- **Levels** – 90 s timer, grid regenerates, enemy cap increases
- **Lives** – 3 per run, 1.3 s invulnerability after a hit
- **High scores** – top 10, name up to 8 characters, saved to `highscores.json`
- **Sound** – procedural sound effects generated at runtime with `numpy` (optional); background music via a `bomb.mp3` file
- **Input** – full keyboard + gamepad support (stick / D-pad / hat, A = confirm, B = bomb, X = pause)
- **Visuals** – 60 FPS, particle effects, explosion flashes, screen shake, animated HUD

## Controls

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | WASD / Arrow keys | Stick, D-pad or hat |
| Place bomb | Space | Button B |
| Start / confirm | Enter | Button A |
| Pause | P | Buttons X / Y |
| Restart (game over) | R, Enter or Space | Button A |
| Edit high-score name | Letters, Backspace | Button A to confirm |

## Requirements

- Python 3.10 or newer
- [Pygame](https://www.pygame.org/)
- [numpy](https://numpy.org/) – optional, only for procedural sound effects (the game runs fine without it)
- Pillow – optional, only if you want to regenerate the icon

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python bomb.py
```

The game opens a 1170×780 window. Music is optional: drop any `bomb.mp3` next to `bomb.py` and it will play on loop; without it the game simply runs silent.

High scores are stored in `highscores.json` next to the game.

## Tests

Both test scripts work standalone and with pytest:

```bash
python test_logic.py
python test_highscores.py
```

or

```bash
pip install pytest
pytest test_logic.py test_highscores.py
```

`test_logic.py` covers grid generation, collisions, bomb explosions, player wall collision, BFS enemy pathfinding and power-ups.
`test_highscores.py` covers the high-score file, the in-game name-entry popup, ranking and joystick input helpers.

## Building a Windows executable

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed bomb.py
```

The resulting `dist/bomb.exe` is self-contained (just add your `bomb.mp3` and `assets/steuerung.png` next to it, or place them in the same folder as the source files – paths are resolved relative to the executable).

## Project structure

```
bomb.py            – the game (single file, ~1150 lines)
make_icon.py       – regenerates bomb.ico from the PNG icon
assets/
    steuerung.png  – control chart shown on the start screen
test_logic.py      – game logic unit tests
test_highscores.py – high-score / input tests
requirements.txt   – dependencies
```

## Notes

- All graphics are drawn procedurally at runtime (no external image assets except the control chart).
- Sound effects are synthesized in code, so nothing is shipped with the game.
- The music file is intentionally not included in this repository – place your own `bomb.mp3` in the game folder.

## License

[MIT](LICENSE) – see `LICENSE` file.
