# BOMB!

A classic bomb-throwing arcade game (a Bomberman-like) written in **Python** with **Pygame**.
Blackscreen grid of bricks, exploding bombs, patrolling enemies that hunt you via BFS pathfinding, power-ups, levels, lives, and a local high-score board.

## Features

- **Bombs** – up to 3 at once, 2.2 s fuse, explosion range up to 3 cells (expandable). If you run out of bombs and stay undamaged, you get a free one after 10 s; the counter resets on damage
- **Bomb placement cooldown (500 ms)** – after placing a bomb the placement is locked for `BOMB_COOLDOWN = 0.5` s. This prevents accidental double clicks and stops a held space bar / gamepad B button from carpet-bombing the whole map. While the lock is active the `BOMBS` slots in the HUD pulse dimmed and show the remaining seconds (`0.4s`), so the block is visible instead of feeling like an unresponsive key. The cooldown never consumes a bomb slot and never blocks the automatic free bomb; a new level resets it
- **Enemies** – up to 1 per 1 s, more each level, chase the player with **BFS pathfinding** (they dodge around placed bombs)
- **Power-ups** (drop when a brick breaks, 15 % chance):
  - extra bomb
  - bigger explosion range
  - speed boost (8 s)
  - extra life
- **Levels** – 90 s timer, grid regenerates, enemy cap increases
- **Lives** – 3 per run, 1.3 s invulnerability after a hit
- **Kill rewards**: double kill (2+ enemies killed by one bomb) grants an extra bomb, multi-kill (5+ enemies with one bomb) grants an extra life and counts toward the sniper streak. The double- and multi-kill tiers spawn a star effect: a five-pointed star outline drawn at the explosion point grows continuously until it is out of frame, flickering between #FFDE21 and #FF13F0; a "Double-Kill" / "Multi-Kill" text at 50 % transparency flickers with the star and only disappears when the star leaves the frame
- **Sniper** – after 3 multi-kills (5+ enemies per bomb) without taking damage in between, a sniper enemy appears in a distant spot. There is never more than one sniper at a time, and a **30 s cooldown** keeps them apart: after the last sniper is gone no new one can appear for `SNIPER_COOLDOWN = 30.0` seconds. **Only damage resets the streak** – a bomb with fewer than 5 kills neither advances nor clears it, and killing the sniper does not clear it either. The sniper moves like the other enemies (BFS chase, same speed) and can only shoot horizontally or vertically across the map, with 5 s reload between shots, and only while you are not standing next to a brick/wall (cover). Spawn effect: a flickering crosshair (red ↔ white) with a "Sniper WARNING!!!" text at 50 % transparency, both disappearing only when the crosshair leaves the frame. Shot trail: a short red line along the row/column
- **Sniper cooldown (30 s)** – the anti-chain lock. It is armed as soon as the **last** sniper disappears – both when a bomb kills it and when a level change clears it – and blocks every further sniper spawn until it runs out. The multi-kill streak itself keeps counting during the cooldown, so nothing is lost: the first multi-kill *after* the cooldown has expired immediately summons the next sniper again.
  - Shown in the HUD as a dim, non-pulsing `SNIPER COOLDOWN 30s` badge (seconds remaining, rounded up) in the same spot as the `SNIPER - HOLD` badge. The two can never appear together, because the badge only shows while `sniper_cd > 0` and a live sniper always has `sniper_cd == 0`.
  - The counter runs only in `STATE_PLAY`, so a paused game does not burn it down, and it survives a level change. Only a **new game** clears it.
  - One bomb that takes down several snipers at once arms the cooldown only once (`Game._sniper_removed` bails out while any sniper is still alive).
- **Stacking kill streaks (reset only on damage)** – both streaks are pure counters that run until you take damage. A bomb that kills **2 or more** enemies advances *both*: `multi_kill_streak` (5+ kills) drives the sniper, `double_kill_streak` (2+ kills) drives the score bonus. Any order counts, so double-kills and multi-kills freely mix and add up. A single kill advances nothing and clears nothing, and killing a sniper is not an enemy kill, so it feeds neither streak. The sniper streak is *gated* by the 30 s sniper cooldown but not consumed by it
- **Double-/Multi-Kill score streak** – every bomb with 2+ kills adds one to `double_kill_streak`, no matter whether it was a double- or a multi-kill. At **5** in a row the score multiplier becomes **2×**, at **10** it becomes **5×**, and it keeps running until you take damage. This is a second, independent route to the same 2×/5× bonuses that a sniper grants
- **Frozen countdown** – while a sniper is alive the round timer stops. The level clock only runs again once the sniper is dead; the HUD shows a blinking `SNIPER - HOLD` badge during that time. Shooting the sniper down therefore buys you time instead of costing you a level
- **Faster free bomb while a sniper is alive** – the sniper freezes the *level* countdown, but deliberately not the "undamaged for N seconds" counter that hands out a free bomb when you are out of bombs. That threshold drops from **10 s to 7 s** as long as a sniper is alive, so the sniper phase really is a shooting gallery instead of a 10 s dry spell. Once the sniper is dead the threshold is back to 10 s
- **Sniper warning stops with the sniper** – the warning sound plays on its own `pygame.mixer` channel and is cut off the instant the sniper disappears, instead of playing to the end of the file. This is guaranteed twice over: every removal path calls `stop_sniper_warning()` explicitly, and `Game.update` additionally runs a watchdog that stops the sound in the very first frame in which `self.snipers` is empty – no matter whether the sniper was killed by a bomb, removed by a level change, or the run ended. The stop targets the stored channel *and* the sound object, so a lost channel handle can never leave the tone running
- **Score multiplier** – four sources feed one effective multiplier and **the highest active bonus always wins**: **2×** while a sniper is alive, **5×** after killing a sniper, **2×** from a double-/multi-kill streak of 5 and **5×** from a streak of 10. Every score is worth it (bricks, power-ups, enemies). Taking damage clears all of them at once, because it resets both streaks and the sniper-kill flag. Whenever the effective multiplier is above 1 the HUD shows `MULTI x2` / `MULTI x5` in a small font between `LEVEL` and `TIME`, flickering in exactly the same yellow (#FFDE21) ↔ magenta (#FF13F0) as the star effect
- **Settings menu (BIOS style)** – press `M` on the keyboard or the **Menu** button on the gamepad (the button to the *right* of the Xbox logo) to open a keyboard-driven settings screen. It works on the start screen, while playing and while paused; the game is frozen while it is open. Navigate with `W`/`S` or the arrow keys, change values with `+`/`-`, confirm with `Enter`, close with `M` or `Esc`. Three entries:
  - **Lautstärke** – master volume from `0` to `255`, scaled in 5-step increments with `+`/`-`, or typed directly as a number (`Enter` opens the input field, digits, `Enter` confirms, `Esc` cancels, clamped to 0–255). Every change plays a beep at exactly the selected volume. The value scales background music and every sound effect
  - **Vollbild** – toggle between the 1180 × 810 window and fullscreen at the desktop resolution (`Enter` or `+`/`-`; `F11` works from anywhere in the menu). The hint line always shows the resulting image size
  - **Highscores** – deletes the entire high-score list. Because this cannot be undone it needs a confirmation: the first `Enter` only arms the row (value changes to `WIRKLICH?`), the second one really empties `highscores.json`. `Esc`, `M` or navigating to another row cancels, so a stray press never wipes the board. The in-memory list and the start screen are updated immediately, without a restart
  - Settings are stored in `settings.json` next to the game and reloaded on start. On the gamepad the menu is opened and closed with the **Menu** button, **D-pad up/down** selects the row, **D-pad left/right** changes the value (volume in steps of 5, clamped at 0/255; fullscreen toggles; the Highscores row ignores left/right), **A** activates the selected row (fullscreen toggles, the Highscores row arms and then confirms the reset, on the volume row it mutes and unmutes) and **B** closes the menu. **B** never opens the menu, so it still places bombs in the game. The direct number entry for the volume stays keyboard-only, because a gamepad cannot type digits
- The D-pad is accepted both as raw buttons 12–15 and as a hat (`JOYHATMOTION`), because Windows drivers differ: some report the D-pad as buttons, others only as a hat. A press counts once, diagonals use the dominant axis, and in-game D-pad movement has always worked through both paths
- **High scores** – top 10, name up to 10 characters, saved to `highscores.json`. While the name entry popup is open it takes over **all** input: keyboard events reach the name field before the settings menu, so typing `M` or `P` enters the letter instead of opening the settings or the pause menu, and you can type any name without navigating away. The popup shows an `n / 10` counter plus the line `max. 10 Characters`
- **Sound** – procedural sound effects generated at runtime with `numpy` (optional); a short beep for the volume settings is generated without `numpy` so it always works; double-kill jingle from `G:\bomb\Double Kill Sound Effect.mp3` (falls back to `doublekill.mp3` next to the game, then a synthesized chime), multi-kill jingle from `G:\bomb\Multi Kill  - Sound Effect.mp3` (falls back to `multikill.mp3` next to the game, then the double-kill sound), sniper warning at 50 % volume from `G:\bomb\sniper warning.mp3` (falls back to `sniperwarning.mp3` next to the game, then the double-kill sound); background music via a `bomb.mp3` file next to the game. Music and all effects pass through the master volume from the settings
- **Input** – full keyboard + gamepad support (stick / D-pad / hat, A = confirm, B = bomb, View = pause, Menu = settings)
- **Visuals** – 60 FPS, particle effects, explosion flashes, screen shake, star outline flickering between yellow (#FFDE21) and magenta (#FF13F0) plus semi-transparent "Double-Kill" / "Multi-Kill" text, floating score numbers at the spot of the damage (several at once), animated HUD

## Controls

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | WASD / Arrow keys | Stick, D-pad or hat |
| Place bomb | Space (500 ms cooldown) | Button B (500 ms cooldown) |
| Start / confirm | Enter | Button A |
| Pause | P | View button (left of the Xbox button) |
| Settings | M (M or Esc to close) | Menu button (right of the Xbox button) |
| Settings: select row | W / S or Up / Down | D-pad up / down |
| Settings: change value | + / - | D-pad left / right |
| Settings: type a number | Enter, digits, Enter | – |
| Settings: confirm / toggle (fullscreen toggles, volume row mutes) | Enter | Button A |
| Settings: clear all high scores (twice) | Enter, Enter | Button A twice |
| Settings: cancel the high-score confirmation | Esc, M or navigate away | Button B or navigate away |
| Settings: close | M or Esc | Button B or Menu |
| Settings: fullscreen quick toggle | F11 | – |
| Restart (game over) | R, Enter or Space | Button A |
| Edit high-score name | Letters, Backspace | Button A to confirm |
| Confirm high-score name | Enter | Button A |

While the high-score popup is open, only these three keys act on it – `M`, `P`
and every other letter are typed into the name instead of reaching the settings
menu or the pause key. The gamepad D-pad and the Menu button are swallowed too,
so nothing can navigate away mid-entry.

Placing a bomb locks the placement for 500 ms. A double click therefore only ever
places one bomb, and holding Space or B places at most two bombs per second
instead of one per rendered frame.

The gamepad mapping is measured on an Xbox controller ("Controller (Xbox One For
Windows)") with SDL raw button indices: A = 0, B = 1, D-pad up = 12, down = 13,
left = 14, right = 15, View = 6, Menu = 7. The settings menu additionally
accepts the D-pad as a hat, so it also works with drivers that never expose the
raw buttons 12–15.

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

The game opens in a 1180×810 window and can be switched to fullscreen at the desktop resolution in the settings. Music is optional: drop any `bomb.mp3` next to `bomb.py` and it will play on loop; without it the game simply runs silent.

High scores are stored in `highscores.json` next to the game, settings in `settings.json`.

## Tests

Both test scripts work standalone and with pytest:

```bash
python test_logic.py
python test_highscores.py
python test_settings.py
```

or

```bash
pip install pytest
pytest test_logic.py test_highscores.py test_settings.py
```

`test_logic.py` covers grid generation, collisions, bomb explosions, player wall collision, BFS enemy pathfinding, power-ups and the kill rewards (2+ kills: extra bomb, 5+ kills: extra life, 3 multi-kills without damage: sniper), the sniper (streak trigger, streak surviving non-multi-kill bombs, double-kills and the sniper's own death, streak reset by damage and by a new game, streak surviving a level change, re-spawns over a run while never having two snipers at once, the 30 s cooldown blocking the chain and expiring before the next re-spawn, the warning channel being released when the sniper dies or the level resets, moves like the other enemies, horizontal/vertical shots, cover, line of sight, 5 s reload, death by bomb, crosshair effect), the score multiplier (2× while a sniper lives, 5× for the following scores after the sniper kill, the sniper's own score still paid at the previous rate, 5× winning over a new sniper, both multipliers ending on damage) and the frozen countdown (timer runs normally, stops while a sniper is alive, resumes after the sniper dies), the bomb placement cooldown (a second bomb inside the 500 ms window is rejected, a blocked click does not consume a bomb slot, the lock expires after 0.5 s, the timer clamps at 0 and a new level resets it), the stacking kill streaks (a double-kill and a multi-kill each advance `double_kill_streak`, any mix of both reaches 5, 2× at 5 and 5× at 10 with the threshold one short still unbonused, a single kill advances nothing and clears nothing, damage clears it, it survives a level change and is cleared by a new game, a sniper kill feeds neither streak), plus the free-bomb counter (10 s without damage normally, 7 s while a sniper is alive, back to 10 s after the sniper dies, not granted at all while the bomb slots are full, and reset by taking damage) and the bomb score display at the damage location (one display per scoring cell with its position on that cell instead of on the player, the sum of all displays equalling the score gain, one display per destroyed brick, the position of an enemy kill sitting on the enemy, the `FT_MAX_COUNT` cap dropping the oldest entry, the 15 → 100 px growth range and the halved `FT_ALPHA`), plus the sniper cooldown in full detail (the `SNIPER_COOLDOWN` = 30.0 constant, starting at zero, not counting down while a sniper is alive, being armed at full strength by a bomb kill and by a level change, ticking down in real time, clamping at zero, blocking the re-spawn while a full streak keeps counting, letting the next multi-kill summon the next sniper afterwards, surviving a level change, being cleared by `new_game`, standing still while paused or on the start screen, and the HUD badge drawing in both states).
`test_highscores.py` covers the high-score file, the in-game name-entry popup, ranking and joystick input helpers. It includes the 10-character name limit (typed, after backspace and when reloaded from disk) and that the popup swallows the whole keyboard: pressing `M` and `P` while the popup is open enters `mp` into the name, leaves the state at `STATE_OVER` and does not open the settings menu, while `M` opens the menu again once the popup is closed.
`test_settings.py` covers the settings: volume clamping to 0–255, the 0–255 → 0.0–1.0 volume scale, JSON persistence, the windowed/fullscreen target sizes, the gamepad button mapping (Menu = button 7 opens the menu, View = button 6 is pause and must not open it, B = button 1 stays the bomb) and the full gamepad menu navigation (D-pad up/down wraps between the rows, D-pad left/right changes the volume in `VOL_STEP` increments and clamps at 0/255, D-pad left/right and A both toggle fullscreen, A mutes and unmutes on the volume row, B closes the menu even while a number entry is open, and B never opens the menu so it still places bombs in the game), plus the hat path (`JOYHATMOTION`) as an alternative to raw buttons 12–15 – navigation and value changes, one step per press, diagonals resolved by the dominant axis, and no reaction while the menu is closed, the high-score reset row (two confirmations before the file is emptied, cancel with `Esc`/`M`/navigation, left/right doing nothing on that row, and the same two A presses on the gamepad), and the whole BIOS menu – opening/closing with `M` or the Menu button, row navigation with wrap-around, `+`/`-` adjustment, direct number entry including clamping and cancel, and drawing every menu state without errors. It writes to a temporary directory, so your real `settings.json` is never touched.

## Building a Windows executable

```bash
pip install pyinstaller
python make_icon.py
python -m PyInstaller --onefile --windowed --icon bomb.ico bomb.py
```

The resulting `dist/bomb.exe` is self-contained (just add your `bomb.mp3` and `assets/steuerung.png` next to it, or place them in the same folder as the source files – paths are resolved relative to the executable).

The control chart `assets/steuerung.png` is **not** embedded in the executable – it is loaded from disk at runtime and scaled into the box on the start screen. You can therefore replace the chart (699 × 504 px PNG works well) at any time without rebuilding the exe.

A ready-to-run build including all runtime files lives in `C:\Users\matth\Desktop\retro ki games\bomb_test`:

```
bomb_test/
    bomb.exe            - das Spiel (onefile, Icon eingebettet)
    bomb.ico            - das Icon des Builds
    bomb.mp3            - Hintergrundmusik
    doublekill.mp3      - Double-Kill Jingle
    multikill.mp3       - Multi-Kill Jingle
    megakill.mp3        - Mega-Kill Jingle
    sniperwarning.mp3   - Sniper-Warnung
    highscores.json     - lokales Highscore-Board
    .bombkey            - Salt fuer die Highscore-Signatur (mitnehmen!)
    assets/steuerung.png - Steuerungstabelle auf dem Startbildschirm
    settings.json       - wird bei der ersten Einstellungaenderung angelegt
    README.md           - diese Datei
    LICENSE             - Lizenz des Projekts
```

Den Ordner einfach als ZIP kopieren und auf einem anderen Windows-PC entpacken – das Spiel laeuft dort direkt per Doppelklick. **`bomb.exe` ist alles, was gebraucht wird**: Python, pygame, numpy, Pillow, SDL2 und sogar die Visual-C++-Laufzeitbibliotheken (`VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `msvcp140`) sind im Onefile-Container eingebettet. Es ist **keine** Python-Installation und **kein** Visual-Studio-Redistribut auf dem Ziel-PC noetig. Nur `.bombkey` muss mit dem Ordner mitlaufen, sonst wird die Highscore-Liste (maschinengebunden signiert) verworfen.

## Project structure

```
bomb.py            – the game (single file, ~2450 lines)
make_icon.py       – regenerates bomb.ico from the PNG icon
assets/
    steuerung.png  – control chart shown on the start screen (699 × 504 px; swapped
                     in from G:\bomb\steuerung_neu2.png, loaded from disk at
                     runtime – no rebuild needed)
test_logic.py      – game logic unit tests
test_highscores.py – high-score / input tests
test_settings.py   – settings / volume / fullscreen / menu tests
requirements.txt   – dependencies
```

## Notes

- All graphics are drawn procedurally at runtime (no external image assets except the control chart `assets/steuerung.png`, which is loaded from disk next to the game and scaled to the box on the start screen).
- Sound effects are synthesized in code, so nothing is shipped with the game.
- The three kill streaks/bonuses are deliberately asymmetric: the streak *counters* are permanent until damage, while the bomb cooldown is a per-click lock. Both live on the `Player`/`Game` objects and are covered by tests.
- The game renders into a fixed 1180×810 buffer and scales that to the output window, so toggling fullscreen never changes the field of view or the layout.
- While a sniper is alive the level countdown is frozen (`Game.sniper_active`); the HUD shows a blinking `SNIPER - HOLD` badge. While the 30 s sniper cooldown runs instead, the same spot shows the dim `SNIPER COOLDOWN <n>s` badge.
- The two timers are deliberately independent: `Game.update` freezes `self.time` during a sniper, but the free-bomb grant below it picks its threshold with `FREE_BOMB_TIME_SNIPER if self.sniper_active else FREE_BOMB_TIME` (7 s vs 10 s). `Player.no_damage_time` accumulates during a sniper phase and is reset in `Game.hurt_player`.
- The effective score multiplier lives in `Game.score_mult` and combines four sources; the highest one wins: a living sniper (`SNIPER_MULT` = 2), the flat `self.mult` = 5 that a sniper kill sets, and the streak bonuses `DK_STREAK_X2` = 5 / `DK_STREAK_X5` = 10 hits on `double_kill_streak`. Taking damage (`Game.hurt_player`) resets `self.mult`, `multi_kill_streak` and `double_kill_streak`, so every bonus ends at the same moment. The HUD only draws the badge while the effective multiplier is above 1.
- Both streaks are cleared **only** by damage (`Game.hurt_player`) and by `new_game`. `Game.explode` never zeroes them: a bomb with fewer than 2 kills falls through all branches without touching either counter, and the streak therefore also survives a level change (`reset_level` deliberately leaves it alone).
- Because the sniper streak never resets on its own, the **30 s sniper cooldown** is what breaks the chain: `_sniper_removed` arms it the moment the last sniper dies, and `Game.explode` refuses to spawn while `sniper_cd > 0`. The streak keeps counting during that window, so the very next multi-kill after the cooldown summons the next one.
- `BOMB_COOLDOWN` = 0.5 s is enforced in `Game.try_place_bomb` via `Player.bomb_cd`, which `Player.update` decrements and clamps at 0. The check sits *before* `bombs_left` is decremented, so a rejected click never destroys a bomb slot, and it never touches the automatic free bomb. `reset_level` creates a new `Player`, which resets the cooldown for free.
- `SNIPER_COOLDOWN` = 30.0 s lives in `Game.sniper_cd` and is deliberately **not** tied to any streak: it is a real-time timer, not a kill counter. It is armed in `Game._sniper_removed` (bomb kill and, via `reset_level`, a level change that removes the last sniper) and cleared again by `_spawn_sniper`; `Game.update` only decrements it inside `STATE_PLAY`. That split keeps it independent of damage – taking damage does not shorten it, and the streak is not consumed by it.
- Only one sniper can exist at a time: `Game.explode` spawns a new sniper whenever the streak is reached, `self.snipers` is empty, the game is in `STATE_PLAY` and `sniper_cd <= 0`.
- The sniper warning runs on a dedicated channel (`play_sniper_warning` / `stop_sniper_warning`) so it can be cut off the instant the sniper is gone; `Game.reset_level` stops it as well.
- `HS_NAME_MAX` is 10. The name is stored as typed (lower case) and upper-cased plus trimmed to 10 characters by `_clean_name`, both when saving and when loading an existing `highscores.json`, so old files with longer names stay intact but are cut to 10 when shown.
- The event loop dispatches the high-score popup **before** the settings menu and the pause key. That block `continue`s for every input event, so a stray `M` in the name cannot open the BIOS menu any more.
- The settings menu freezes the game completely, so nothing can be hit while you are changing options.
- `settings.json` is only written once a setting is actually changed, so a fresh installation starts from the defaults (volume 160, windowed). It only contains `volume` and `fullscreen`; an old `resolution` entry from an earlier build is ignored. The high-score reset is not stored there – it empties `highscores.json` and `Game.hiscores` immediately via the `SettingsUI.hiscores_reset` flag.
- The menu keeps the row you last selected, so reopening it lands on the same setting.
- The double-kill jingle is loaded from `G:\bomb\Double Kill Sound Effect.mp3` if present, otherwise from `doublekill.mp3` next to the game, with a synthesized chime as last resort.
- The multi-kill jingle is loaded from `G:\bomb\Multi Kill  - Sound Effect.mp3` if present, otherwise from `multikill.mp3` next to the game, with the double-kill sound as fallback.
- The sniper warning is loaded from `G:\bomb\sniper warning.mp3` if present, otherwise from `sniperwarning.mp3` next to the game, with the double-kill sound as fallback. That file runs for 18 s, which is why it is bound to a dedicated channel and hard-stopped together with the sniper instead of being allowed to run out.
- The music file is optional – place your own `bomb.mp3` next to the game to enable background music.

## Linux (Flatpak)

The game runs on Linux via [Flatpak](https://flatpak.org/). No Python installation is needed on the target system – the Flatpak bundles Python, pygame and numpy.

### Install

```bash
flatpak install flathub com.absentplayer.bomb
```

Or build locally:

```bash
flatpak-builder build-dir com.absentplayer.bomb.json --install --user
```

### Run

```bash
flatpak run com.absentplayer.bomb
```

### Permissions

The Flatpak requests the following permissions:

- **Wayland + X11** – video output
- **PulseAudio** – sound
- **All devices** – gamepad/joystick input
- **IPC** – shared memory for SDL

### Files

Runtime files are stored in `~/.var/app/com.absentplayer.bomb/`:

- `highscores.json` – local high-score board
- `settings.json` – volume and fullscreen settings
- `.bombkey` – machine-bound high-score signing salt

### Building from source

```bash
git clone https://github.com/AbsentPlayer/Bomb.exe.git
cd Bomb.exe
flatpak-builder build-dir com.absentplayer.bomb.json --force-clean
flatpak build-export repo build-dir
flatpak remote-add --user bomb-repo repo
flatpak install --user bomb-repo com.absentplayer.bomb
```

### Linux release asset

The `bomb.v1.1.3-linux.zip` release asset contains everything needed to run on Linux without Flatpak:

```
bomb.v1.1.3-linux.zip
    bomb.py              - the game (Python 3.10+)
    bomb.ico             - icon
    bomb.mp3             - background music
    doublekill.mp3       - double-kill jingle
    multikill.mp3        - multi-kill jingle
    sniperwarning.mp3    - sniper warning sound
    requirements.txt     - Python dependencies (pygame, numpy, Pillow)
    com.absentplayer.bomb.json       - Flatpak manifest
    com.absentplayer.bomb.desktop    - Desktop entry
    com.absentplayer.bomb.metainfo.xml - AppStream metainfo
    assets/steuerung.png - control chart
    README.md
    LICENSE
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python bomb.py
```

## License

[MIT](LICENSE) – see `LICENSE` file.

## Version history

| Version | Release asset | Changes |
|---|---|---|
| **v1.1.3** | `bomb.v1.1.3.zip` (Windows) · `bomb.v1.1.3-linux.zip` (Linux) | **Sniper cooldown 30 s** (`SNIPER_COOLDOWN`) against sniper chains · **Bomben-Punkte-Anzeige an der Schadensstelle**: eine Anzeige je beschädigter Zelle statt einer Summe am Spieler, Position auf Brick/Power-up/Gegner/Sniper, mehrere gleichzeitig (Deckel `FT_MAX_COUNT = 40`) · Größe **15 → 100 px** (vorher 30 → 200) · nochmal **50 % mehr Transparenz** (`FT_ALPHA` 153 → 76) · **Linux Flatpak** (`com.absentplayer.bomb.json`, Desktop-Eintrag, Metainfo) |
| v1.1.2 | `bomb.v1.1.2.zip` | Mega-Kill mit 10+ Kills durch eine einzige Bombe, 7 s Immunität mit Farbflackern, Bomben-Punkte-Transparenz |
| v1.1.1 | `bomb.v1.1.zip` | DPad-Trennung Menü/Spiel, Bomben-Punkte-Anzeige 30 → 200 px |
| v1.0.3 | `bomb_1_0_3.zip` | Mega-Kill, Bomben-Punkte-Anzeige, DPad-Korrektur, HMAC-signierte Highscores |
| v1.0.0 | `bomb.zip` | Erstes Release |

## Mega-Kill, Bomben-Punkte-Anzeige an der Schadensstelle, Sniper-Cooldown und DPad

- **Mega-Kill**: 10+ Gegner durch eine einzige Bombe (`MEGA_KILL_KILLS = 10`, nicht die Streak) löst den Mega-Kill aus.
  - **Sound**: `megakill.mp3` neben dem Spiel (oder `G:\bomb\Mega Kill - Sound Effect.mp3`, falls vorhanden); ohne Datei wird auf den Multi-Kill-Sound zurückgefallen.
  - **Stern-Effekt**: Ein fünfziger Stern mit "Mega-Kill"-Text am Explosionsort, der zwischen den Farben #FFFF00, #FF0000, #00FF00 und #00FFFF wechselt und wächst wie der normale Stern, bis er den Bildschirm verlässt.
  - **Immunität**: Nach einem Mega-Kill ist der Spieler 7 Sekunden unverwundbar (`MEGA_INVULN_TIME = 7.0`).
  - **Flicker**: Während der Immunitätszeit flackert der Spieler in den Farben #FFFF00, #FF0000, #00FF00 und #00FFFF.
  - Der Immunitätsstatus endet mit Levelwechsel (`reset_level`) bzw. neuem Spiel.

- **Bomben-Punkte-Anzeige an der Schadensstelle**: Bei jeder Bomben-Explosion erscheint für **jede Zelle, die Punkte gebracht hat**, eine eigene Punkte-Anzeige – und zwar **genau dort, wo der Schaden entstanden ist**, nicht (mehr) am Spieler:
  - **Position = Ort des Schadens**: zerstörter Brick → auf dem Brick, eingesammeltes Power-up → auf dem Power-up, getöteter Gegner → **auf dem Gegner**, getöteter Sniper → auf dem Sniper. Die Pixelkoordinaten werden beim Erzeugen der Anzeige mitgeschrieben (`x`/`y`), gezeichnet wird mittig auf diesem Punkt.
  - **Mehrere Anzeigen gleichzeitig**: Es gibt keinen gesammelten Text mehr, der die Summe einer Explosion am Spieler zeigt. Stattdessen legt jede Zelle über `Game._score_text` eine eigene Anzeige ab – eine Bombe mit Radius 3 kann damit bis zu 29 Anzeigen auf einmal erzeugen (Brick 10, Power-up 5, Gegner 50, Sniper 100, jeweils noch mit dem aktiven Score-Multiplikator). Die Summe aller Anzeigen einer Explosion ergibt exakt den Punktezuwachs.
  - **Menge pro Anzeige**: nur der an dieser Stelle erzielte Betrag (nicht der Gesamtwert der Explosion).
  - **Farbe**: Gelb (255, 255, 0).
  - **Größe**: wächst linear von **15 auf 100 Pixel** (`FT_START_SIZE = 15` → `FT_END_SIZE = 100`) und verschwindet nach 4 Sekunden (`FT_MAX_AGE = 4.0`).
  - **Transparenz**: rund 70 % durchsichtig, also nochmal 50 % mehr als vorher. Umgesetzt mit `FT_ALPHA = 76` (vorher 153); der Wert wird per `BLEND_RGBA_MULT` auf das Bild multipliziert, kleiner Wert = durchsichtiger.
  - **Deckel**: höchstens `FT_MAX_COUNT = 40` Anzeigen gleichzeitig; wird das Limit überschritten, verschwindet die älteste zuerst, damit eine große Explosion die Bildrate nicht mit Text belastet.
  - Einträge ohne `x`/`y` (Altbestand) zeichnet `_draw_score_floating_texts` weiterhin am Spieler.

- **Sniper-Cooldown (30 Sekunden)**: Die Anti-Ketten-Sperre. Sie wird scharf geschaltet, sobald der **letzte** Sniper verschwunden ist – sowohl wenn eine Bombe ihn erledigt als auch wenn ein Levelwechsel ihn mitnimmt – und blockiert jeden weiteren Sniper-Spawn, bis sie abgelaufen ist:
  - **Konstante**: `SNIPER_COOLDOWN = 30.0`, gespeichert in `Game.sniper_cd`.
  - **Kein Ketten-Reflex mehr**: Vorher rief schon der nächste Multi-Kill direkt den nächsten Sniper. Jetzt gilt: voller Streak, aber in diesen 30 Sekunden kein Sniper.
  - **Der Streak geht dabei nicht verloren**: `multi_kill_streak` zählt während der Sperre weiter. Sobald sie abgelaufen ist, ruft der allererste Multi-Kill den nächsten Sniper – ohne dass man die 3 Kills erneut sammeln muss.
  - **HUD**: ein gedimmtes, **nicht pulsierendes** `SNIPER COOLDOWN 30s` (Restsekunden, aufgerundet) an derselben Stelle wie das blinkende `SNIPER - HOLD`. Beide erscheinen nie gleichzeitig, weil das Cooldown-Badge nur bei `sniper_cd > 0` gezeichnet wird und ein lebender Sniper immer `sniper_cd == 0` hat.
  - **Echte Zeit, kein Kill-Zähler**: Der Timer läuft nur in `STATE_PLAY` – ein pausiertes Spiel verbraucht ihn nicht – und er überlebt einen Levelwechsel. Nur ein **neues Spiel** löscht ihn (`new_game`); Schaden verkürzt ihn nicht.
  - **Mehrfach-Snipers**: Eine Bombe, die mehrere Snipers gleichzeitig trifft, schaltet die Sperre nur einmal (`Game._sniper_removed` bricht ab, solange noch ein Sniper lebt).
  - **Umsetzung**: `Game._sniper_removed` scharf schalten, `Game._spawn_sniper` löscht sie wieder, `Game.update` zieht sie pro Frame herunter, und die Spawn-Bedingung in `Game.explode` verlangt zusätzlich `self.sniper_cd <= 0.0`.

- **DPad-Steuerung (getrennt pro Kontext)**:
  - **Settings-Menü (unverändert, vom Nutzer bestätigt so wie es jetzt ist)**:
    D-Pad als Buttons 12-15 *und* als Hat akzeptiert; die Laufrichtung ist so implementiert, dass DOWN das nächste Menüelement und UP das vorherige wählt (wie vom Nutzer gewünscht).
  - **Spielbewegung**: Die DPad-Steuerung im Spiel ist unabhängig vom Menü gemappt (die Hat y-Achse ist invertiert: `fy = -int(hy)`), damit die physische DPad-Richtung im Spiel der im Menü bestätigten Richtung entspricht. Buttons 12-15 und der Analog-Stick sind standardmäßig gemappt (12 = up, 13 = down, 14 = left, 15 = right).

## Portabilität / Laufzeit

- Die `bomb.exe` ist ein PyInstaller-`onefile`-Build: **pygame, numpy und Pillow sind eingebettet** - es ist keine Python-Installation und kein zusätzlicher Runtime nötig, auch nicht auf dem Ziel-PC. Dasselbe gilt für die Visual-C++-Laufzeit (`VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `msvcp140`): alle drei liegen im Container, ein Redistribut muss auf dem Ziel-PC nicht installiert sein.
- Alle Laufzeitdateien liegen im selben Ordner wie die Exe (Pfade werden relativ zur Exe aufgelöst): `bomb.mp3`, `doublekill.mp3`, `multikill.mp3`, `megakill.mp3`, `sniperwarning.mp3`, `bomb.ico`, `assets/steuerung.png`, `.bombkey`, `highscores.json`.
- **Highscores sind maschinengebunden** (HMAC-Signatur aus Windows-Maschinen-ID und Salt der Datei `.bombkey`): Wird der Ordner auf einem anderen PC dezippt, wird die alte Score-Liste verworfen und eine neue, gültige Datei angelegt. `.bombkey` muss mit dem Ordner mitlaufen.
- `settings.json` wird erst bei der ersten Einstellungänderung angelegt.
