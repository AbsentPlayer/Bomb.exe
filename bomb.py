import math
import json
import os
import random
import sys
import hashlib
import hmac
import base64
import ctypes
import pygame
from collections import deque

# ------------------------------------------------------------- constants
TILE = 50
GRID_W = 22
GRID_H = 14
MARGIN_L = 40
MARGIN_R = 40
MARGIN_T = 90
MARGIN_B = 20
SCREEN_W = MARGIN_L + GRID_W * TILE + MARGIN_R
SCREEN_H = MARGIN_T + GRID_H * TILE + MARGIN_B
FPS = 60

EMPTY = 0
BRICK = 1
WALL = 2

PLAYER_START = (3, 6)
PLAYER_SPEED = 3.0
BOMB_FUSE = 2.2
MAX_BOMBS = 3
MAX_RANGE = 3
MAX_LIVES = 3
DOUBLE_KILL_KILLS = 2
MULTI_KILL_KILLS = 5
SNIPER_STREAK = 3
SNIPER_MULT = 2
SNIPER_KILL_MULT = 5
BOMB_COOLDOWN = 0.5
# Double-/Multi-Kill-Streak: belohnt jede Bombe mit 2+ Kills, unabhaengig
# davon ob es 2 oder 5 waren. Reset nur bei Schaden.
DK_STREAK_X2 = 5
DK_STREAK_X5 = 10
FREE_BOMB_TIME = 10.0
FREE_BOMB_TIME_SNIPER = 7.0
ENEMY_INTERVAL = 1.0
MAX_ENEMIES = 8
LEVEL_TIME = 90.0
MEGA_KILL_STREAK = 10
MEGA_INVULN_TIME = 15.0
MEGA_COLORS = ((255, 255, 0), (255, 0, 0), (0, 255, 0), (0, 255, 255))
FT_MAX_AGE = 4.0
FT_START_SIZE = 30
FT_END_SIZE = 200
FT_COLOR = (255, 255, 0)

STATE_START = 0
STATE_PLAY = 1
STATE_PAUSED = 2
STATE_OVER = 3

HIGHSCORES_MAX = 10
HS_NAME_MAX = 10
JOY_DZ = 0.4
JOY_BTN_A = 0
JOY_BTN_B = 1
# links neben der Xbox-Taste, zwei Rechtecke = Ansicht/View (bei "Xbox One For
# Windows" und allen XInput-Mappings Button 6 - empirisch gemessen)
JOY_BTN_PAUSE = (6,)
# rechts neben der Xbox-Taste = Menue/Start (Button 7)
JOY_BTN_MENU = (7,)
JOY_DPAD = (12, 13, 14, 15)

JOY = None

BG = (16, 18, 30)
FLOOR = (26, 29, 47)
FLOOR_ALT = (31, 35, 56)
WALL = (40, 43, 64)
WALL_TOP = (58, 62, 92)
WALL_GLOW = (96, 102, 150)
BRICK = (166, 118, 62)
BRICK_TOP = (202, 152, 92)
BRICK_SHADY = (118, 82, 46)
PBODY = (46, 212, 232)
PBODY2 = (22, 150, 172)
PHAT = (72, 232, 246)
PEYE = (244, 246, 252)
PEYE2 = (20, 22, 28)
PFOOT = (26, 100, 112)
ENEMY = (196, 72, 82)
ENEMY2 = (148, 46, 58)
EYE = (255, 240, 90)
PBOMB = (96, 212, 160)
PRANGE = (196, 140, 236)
PSPEED = (92, 182, 236)
PLIFE = (236, 152, 70)
PUP_OUT = (40, 40, 60)
PUP_IN = (255, 255, 255)
FUSE = (255, 150, 60)
FUSE_GLOW = (255, 210, 90)
FX_RED = (255, 120, 84)
FX_YEL = (255, 232, 92)
FX_GREEN = (120, 244, 160)
HUD_BG = (28, 31, 52)
HUD_TXT = (240, 244, 252)
HUD_ACC = (120, 222, 246)
TEXT = (245, 247, 252)
TEXT_DIM = (150, 158, 182)

# ------------------------------------------------------------- settings
SETTINGS_FILE = 'settings.json'
VOL_MIN = 0
VOL_MAX = 255
VOL_STEP = 5
VOL_DEFAULT = 160
MUSIC_VOL = 0.8

BIOS_BG = (10, 12, 40)
BIOS_PANEL = (18, 26, 74)
BIOS_BORDER = (86, 110, 190)
BIOS_TEXT = (188, 198, 226)
BIOS_DIM = (110, 122, 160)
BIOS_SEL = (32, 62, 148)
BIOS_SEL_TEXT = (245, 248, 255)
BIOS_ACC = (120, 226, 255)
BIOS_ON = (130, 240, 170)
BIOS_OFF = (226, 140, 130)

SETTINGS = None


def make_font(name, size, bold=False):
    f = pygame.font.SysFont(name, size)
    if bold:
        f.set_bold(True)
    return f


_DESKTOP_SIZE = None


def _desktop_size():
    """Echte Desktop-Auflösung (einmalig ermittelt, nicht die Fenstergröße)."""
    global _DESKTOP_SIZE
    if _DESKTOP_SIZE is not None:
        return _DESKTOP_SIZE
    size = None
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            size = (int(sizes[0][0]), int(sizes[0][1]))
    except Exception:
        size = None
    if size is None:
        try:
            info = pygame.display.Info()
            if info.current_w > 0 and info.current_h > 0:
                size = (int(info.current_w), int(info.current_h))
        except Exception:
            size = None
    _DESKTOP_SIZE = size
    return _DESKTOP_SIZE


class Settings:
    """Einstellungen des Spiels, persistiert als settings.json neben dem Spiel."""

    def __init__(self):
        self.volume = VOL_DEFAULT
        self.fullscreen = False
        self.load()

    @property
    def path(self):
        return os.path.join(_base_dir(), SETTINGS_FILE)

    def target_size(self):
        """Fenster = interne Spielaufloesung, Vollbild = Desktopaufloesung."""
        if self.fullscreen:
            desktop = _desktop_size()
            if desktop:
                return desktop
        return (SCREEN_W, SCREEN_H)

    def set_volume(self, value):
        self.volume = max(VOL_MIN, min(VOL_MAX, int(value)))
        apply_volume()
        self.save()
        play_sfx('beep')

    def adjust_volume(self, delta):
        self.set_volume(self.volume + delta)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.save()
        apply_volume()
        return self.fullscreen

    def to_dict(self):
        return {
            'volume': self.volume,
            'fullscreen': bool(self.fullscreen),
        }

    def load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            return
        try:
            self.volume = max(VOL_MIN, min(VOL_MAX, int(data.get('volume', VOL_DEFAULT))))
        except (TypeError, ValueError):
            self.volume = VOL_DEFAULT
        self.fullscreen = bool(data.get('fullscreen', False))

    def save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as fh:
                json.dump(self.to_dict(), fh, indent=2)
        except Exception:
            pass


class SettingsUI:
    """BIOS-artiges Einstellungsmenue: W/S wählen, +/- ändern, M schliesst."""

    ROWS = ('volume', 'fullscreen', 'reset_scores')

    def __init__(self, settings):
        self.s = settings
        self.open = False
        self.index = 0
        self.editing = False
        self.buffer = ''
        self.blink = 0.0
        self.needs_display = False
        self._hat_down = False
        self._last_volume = 0
        self.confirm_reset = False
        self.hiscores_reset = False

    # -------------------------------------------------- wert-Darstellung
    def row_value(self, row):
        if row == 'volume':
            return '%3d / 255' % self.s.volume
        if row == 'fullscreen':
            return 'AN' if self.s.fullscreen else 'AUS'
        return 'WIRKLICH?' if self.confirm_reset else 'LOESCHEN'

    def row_hint(self, row):
        if row == 'volume':
            if self.editing:
                return 'Zahl eingeben  ENTER = OK  ESC = Abbrechen'
            return 'ENTER = Zahl eingeben  -/+ = ändern'
        if row == 'reset_scores':
            if self.confirm_reset:
                return 'ENTER = endgueltig leeren  ESC = abbrechen'
            return 'ENTER = Highscores loeschen (alle)'
        w, h = self.s.target_size()
        return 'ENTER oder -/+ = umschalten  -  Bild %d x %d' % (w, h)

    # -------------------------------------------------- Eingabe
    def handle_event(self, ev):
        """Verarbeitet ein Tastatur-/Joystick-Event. True = Event konsumiert."""
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
            self._toggle()
            return True
        if not self.open:
            return False
        if ev.type != pygame.KEYDOWN:
            return False
        k = ev.key
        if self.editing:
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.buffer.strip():
                    try:
                        self.s.set_volume(int(self.buffer.strip()))
                    except ValueError:
                        play_sfx('buzz')
                self.editing = False
                self.buffer = ''
            elif k == pygame.K_ESCAPE:
                self.editing = False
                self.buffer = ''
            elif k == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
            else:
                c = getattr(ev, 'unicode', '') or ''
                if c.isdigit() and len(self.buffer) < 3:
                    self.buffer += c
            return True
        if k in (pygame.K_ESCAPE, pygame.K_m):
            self._close()
            return True
        if k in (pygame.K_UP, pygame.K_w):
            self.confirm_reset = False
            self.index = (self.index - 1) % len(self.ROWS)
            return True
        if k in (pygame.K_DOWN, pygame.K_s):
            self.confirm_reset = False
            self.index = (self.index + 1) % len(self.ROWS)
            return True
        if k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_PERIOD):
            self._adjust(+1)
            return True
        if k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._adjust(-1)
            return True
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._activate()
            return True
        if k in (pygame.K_F11,):
            self.needs_display = True
            self._apply_fullscreen()
            return True
        return False

    def handle_joy_event(self, ev):
        if ev.type == pygame.JOYHATMOTION:
            return self._handle_hat(ev)
        if ev.type != pygame.JOYBUTTONDOWN:
            return False
        if ev.button in JOY_BTN_MENU:
            self._toggle()
            return True
        if not self.open:
            return False
        if ev.button == JOY_BTN_B:
            self._close()
            return True
        if ev.button == JOY_BTN_A:
            return self._activate_pad()
        if ev.button in JOY_DPAD:
            return self._nudge(*self._pad_dir(ev.button))
        return False

    def _handle_hat(self, ev):
        """D-Pad kommt je nach Treiber als Hat statt als Buttons 12-15."""
        try:
            hx, hy = ev.value
        except Exception:
            return False
        if hx == 0 and hy == 0:
            self._hat_down = False
            return False
        if self._hat_down:
            return True
        self._hat_down = True
        if not self.open:
            return False
        if abs(hx) >= abs(hy):
            return self._nudge(-1 if hx < 0 else (1 if hx > 0 else 0), 0)
        return self._nudge(0, -1 if hy > 0 else 1)

    def _pad_dir(self, button):
        if button == JOY_DPAD[0]:
            return (0, -1)
        if button == JOY_DPAD[1]:
            return (0, 1)
        if button == JOY_DPAD[2]:
            return (-1, 0)
        return (1, 0)

    def _nudge(self, dx, dy):
        if self.editing:
            return True
        if dy:
            self.confirm_reset = False
            self.index = (self.index + dy) % len(self.ROWS)
            return True
        if dx:
            self._adjust(dx)
            return True
        return False

    def _activate_pad(self):
        """A: Vollbild umschalten, auf der Lautstaerke stummschalten."""
        row = self.ROWS[self.index]
        if row == 'volume':
            if self.s.volume == 0:
                self.s.set_volume(self._last_volume or VOL_DEFAULT)
            else:
                self._last_volume = self.s.volume
                self.s.set_volume(0)
            return True
        self._activate()
        return True

    def _toggle(self):
        if self.open:
            self._close()
        else:
            self.open = True
            self.editing = False
            self.buffer = ''
            self.confirm_reset = False

    def _close(self):
        self.open = False
        self.editing = False
        self.buffer = ''
        self.confirm_reset = False

    def _adjust(self, direction):
        row = self.ROWS[self.index]
        if row == 'volume':
            self.s.adjust_volume(VOL_STEP * direction)
        elif row == 'fullscreen':
            self.needs_display = True
            self._apply_fullscreen()

    def _activate(self):
        row = self.ROWS[self.index]
        if row == 'volume':
            self.editing = True
            self.buffer = ''
        elif row == 'fullscreen':
            self.needs_display = True
            self._apply_fullscreen()
        else:
            if not self.confirm_reset:
                self.confirm_reset = True
            else:
                self._do_reset()

    def _do_reset(self):
        save_highscores([])
        self.hiscores_reset = True
        self.confirm_reset = False
        play_sfx('buzz')

    def _apply_fullscreen(self):
        self.s.toggle_fullscreen()
        self.needs_display = True

    # -------------------------------------------------- Darstellung
    def update(self, dt):
        self.blink += dt

    def draw(self, surf):
        w, h = 780, 380
        bx = (SCREEN_W - w) // 2
        by = (SCREEN_H - h) // 2
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(shade, (0, 0, 0, 170), pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        surf.blit(shade, (0, 0))

        p = pygame.Surface((w, h))
        pygame.draw.rect(p, BIOS_PANEL, pygame.Rect(0, 0, w, h))
        pygame.draw.rect(p, BIOS_BORDER, pygame.Rect(2, 2, w - 4, h - 4), width=2)
        pygame.draw.rect(p, BIOS_BORDER, pygame.Rect(0, 0, w, 42), width=2)
        pygame.draw.line(p, BIOS_BORDER, (1, 42), (w - 2, 42), 2)
        pygame.draw.line(p, BIOS_BORDER, (1, h - 46), (w - 2, h - 46), 2)

        f_title = make_font(None, 26, True)
        img = f_title.render('BOMB!  -  EINSTELLUNGEN', True, BIOS_ACC)
        p.blit(img, (18, 10))
        img = f_title.render('[M]  ESC', True, BIOS_DIM)
        p.blit(img, (w - 18 - img.get_width(), 10))

        f_head = make_font(None, 20, True)
        img = f_head.render('EINSTELLUNG', True, BIOS_DIM)
        p.blit(img, (18, 56))
        img = f_head.render('WERT', True, BIOS_DIM)
        p.blit(img, (430, 56))

        f_row = make_font(None, 26)
        f_val = make_font(None, 26, True)
        f_hint = make_font(None, 20)
        y = 86
        for i, row in enumerate(self.ROWS):
            sel = i == self.index
            if sel:
                pygame.draw.rect(p, BIOS_SEL, pygame.Rect(10, y - 4, w - 20, 36))
                if self.editing and int(self.blink * 3) % 2 == 0:
                    pygame.draw.rect(p, BIOS_SEL_TEXT, pygame.Rect(w - 26, y + 2, 14, 20))
            col = BIOS_SEL_TEXT if sel else BIOS_TEXT
            label = {'volume': 'Lautstärke', 'fullscreen': 'Vollbild', 'reset_scores': 'Highscores'}[row]
            p.blit(f_row.render(label, sel, col), (24, y))
            val = self.row_value(row)
            vcol = BIOS_ACC if sel else BIOS_TEXT
            if row == 'fullscreen':
                vcol = BIOS_ON if self.s.fullscreen else BIOS_OFF
            if row == 'reset_scores':
                vcol = BIOS_OFF if (self.confirm_reset or sel) else BIOS_DIM
            if row == 'volume' and not sel:
                vcol = BIOS_TEXT
            if sel and row == 'volume':
                self._draw_volume_bar(p, 430, y + 11, self.s.volume, sel)
                p.blit(f_val.render('%3d' % self.s.volume, True, vcol), (606, y))
            else:
                p.blit(f_val.render(val, True, vcol), (606, y))
            y += 44

        y += 6
        hint = self.row_hint(self.ROWS[self.index])
        img = f_hint.render(hint, True, BIOS_ACC if self.editing else BIOS_DIM)
        p.blit(img, (24, y))
        img = f_hint.render('W/S oder Pfeiltasten = wählen    -/+ = ändern    ENTER = bestätigen', True, BIOS_DIM)
        p.blit(img, (24, y + 28))
        img = f_hint.render('Gamepad:  D-Pad = wählen/ändern    A = umschalten    B = schließen', True, BIOS_DIM)
        p.blit(img, (24, y + 54))
        img = f_hint.render('ESC bricht eine offene Bestätigung ab.', True, BIOS_DIM)
        p.blit(img, (24, y + 80))
        img = f_hint.render('Das Spiel ist während der Einstellungen angehalten.', True, BIOS_DIM)
        p.blit(img, (24, y + 106))
        surf.blit(p, (bx, by))

        if self.editing:
            f_in = make_font(None, 24, True)
            lw = 260
            lx = bx + 300
            ly = by + h + 18
            if ly + 44 > SCREEN_H:
                ly = by - 62
            box = pygame.Surface((lw, 40))
            pygame.draw.rect(box, (4, 6, 22), pygame.Rect(0, 0, lw, 40))
            pygame.draw.rect(box, BIOS_ACC, pygame.Rect(1, 1, lw - 2, 38), width=2)
            shown = self.buffer or '0'
            box.blit(f_in.render(shown, True, BIOS_SEL_TEXT), (12, 6))
            if int(self.blink * 3) % 2 == 0:
                box.blit(f_in.render('_', True, BIOS_SEL_TEXT), (12 + 8 + f_in.size(shown)[0] + 4, 6))
            surf.blit(box, (lx, ly))
            t = f_hint.render('Neue Lautstärke (0-255):', True, BIOS_DIM)
            surf.blit(t, (lx - t.get_width() - 12, ly + 10))

    def _draw_volume_bar(self, p, x, y, value, sel):
        bw, bh = 156, 14
        pygame.draw.rect(p, (8, 10, 28), pygame.Rect(x, y - bh // 2, bw, bh))
        pygame.draw.rect(p, BIOS_DIM, pygame.Rect(x, y - bh // 2, bw, bh), width=1)
        frac = (value - VOL_MIN) / float(VOL_MAX - VOL_MIN)
        fill = int((bw - 2) * frac)
        if fill > 0:
            col = BIOS_ON if value <= 170 else (BIOS_ACC if value <= 220 else BIOS_OFF)
            pygame.draw.rect(p, col, pygame.Rect(x + 1, y - bh // 2 + 1, fill, bh - 2))
        _ = sel


def rrect(s, x, y, w, h, col, r):
    pygame.draw.rect(s, col, pygame.Rect(x, y, w, h))


def cell_solid(grid, tx, ty):
    x = int(math.floor(tx + 1e-9))
    y = int(math.floor(ty + 1e-9))
    if not (0 <= x < GRID_W and 0 <= y < GRID_H):
        return True
    return grid[y][x] in (BRICK, WALL)


def collides(grid, x, y, half):
    for cx, cy in ((x + half, y + half), (x - half, y - half), (x + half, y - half), (x - half, y + half)):
        if cell_solid(grid, cx, cy):
            return True
    return False


class Particle:
    def __init__(self, x, y, vx, vy, gv, life, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.gv = gv
        self.life = life
        self.tl = life
        self.color = color
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gv * dt
        self.life -= dt

    def alive(self):
        return self.life > 0

    def draw(self, s):
        if not self.alive():
            return
        a = int(255 * (self.life / self.tl))
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, a), (self.size // 2, self.size // 2), self.size // 2)
        s.blit(surf, (int(self.x), int(self.y)))


class Powerup:
    def __init__(self, sx, sy, kind):
        self.sx = sx
        self.sy = sy
        self.kind = kind
        self.t = 0.0

    def update(self, dt):
        self.t += dt


class Effect:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.life = 0.0

    def update(self, dt):
        self.life += dt

    def draw(self, s, ox, oy):
        px = int(ox + self.x * TILE - TILE)
        py = int(oy + self.y * TILE - TILE)
        surf = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
        if self.life < 0.22:
            r = int(TILE * 2 * self.life / 0.22)
            col = FX_YEL if self.kind == 'brick' else FX_RED
            a = int(120 * max(0, 1.0 - self.life / 0.22))
            pygame.draw.circle(surf, (*col, a), (TILE, TILE), r)
        if self.life < 0.16:
            r2 = int(TILE * (0.4 + 0.9 * (self.life / 0.16)))
            a2 = int(70 * max(0, 1.0 - self.life / 0.16))
            pygame.draw.circle(surf, (235, 235, 240, a2), (TILE, TILE), r2)
        s.blit(surf, (px, py))


def star_color(t):
    """Dasselbe Flackern wie der Stern: Gelb (255,222,33) -> Magenta (255,19,240)."""
    k = 0.5 + 0.5 * math.sin(t * 4.0)
    return (
        int(255),
        int(222 + (19 - 222) * k),
        int(33 + (240 - 33) * k),
    )


def mega_color(t):
    return MEGA_COLORS[int(t * 8.0) % len(MEGA_COLORS)]


class StarEffect:
    GROW = 300.0
    START_R = 30.0
    C1 = (255, 222, 33)
    C2 = (255, 19, 240)

    def __init__(self, x, y, label=None, color_fn=None):
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.label = label
        self.color_fn = color_fn or star_color
        self.font = make_font(None, 34, True) if label is not None else None

    def update(self, dt):
        self.age += dt

    def radius(self):
        return self.START_R + self.age * self.GROW

    def dead(self):
        return self.radius() > max(self.x + SCREEN_W, self.y + SCREEN_H)

    def color(self):
        return self.color_fn(self.age)

    def _points(self, r, rot):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = rot + i * math.pi / 5
            pts.append((self.x + rr * math.cos(a), self.y + rr * math.sin(a)))
        return pts

    def draw(self, s):
        r = self.radius()
        if r < 2:
            return
        base_rot = -math.pi / 2 + self.age * 0.5
        c = self.color()
        w = 3 + int(r * 0.004)
        pygame.draw.polygon(s, c, self._points(r, base_rot), w)
        if self.label is not None:
            fade_in = min(1.0, self.age / 0.15)
            a = int(128 * fade_in)
            if a > 0:
                surf = self.font.render(self.label, True, c)
                surf.set_alpha(a)
                s.blit(surf, (int(self.x - surf.get_width() // 2), int(self.y - surf.get_height() // 2 - self.age * 14)))


class CrosshairEffect:
    GROW = 300.0
    START_R = 30.0
    C1 = (255, 0, 0)
    C2 = (255, 255, 255)

    def __init__(self, x, y, label='Sniper WARNING!!!'):
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.label = label
        self.font = make_font(None, 34, True) if label is not None else None

    def update(self, dt):
        self.age += dt

    def radius(self):
        return self.START_R + self.age * self.GROW

    def dead(self):
        return self.radius() > max(self.x + SCREEN_W, self.y + SCREEN_H)

    def color(self):
        t = 0.5 + 0.5 * math.sin(self.age * 4.0)
        return (
            int(self.C1[0] + (self.C2[0] - self.C1[0]) * t),
            int(self.C1[1] + (self.C2[1] - self.C1[1]) * t),
            int(self.C1[2] + (self.C2[2] - self.C1[2]) * t),
        )

    def draw(self, s):
        r = self.radius()
        if r < 2:
            return
        c = self.color()
        w = 3 + int(r * 0.004)
        gap = max(2, int(r * 0.3))
        pygame.draw.line(s, c, (self.x, self.y - r), (self.x, self.y - gap), w)
        pygame.draw.line(s, c, (self.x, self.y + gap), (self.x, self.y + r), w)
        pygame.draw.line(s, c, (self.x - r, self.y), (self.x - gap, self.y), w)
        pygame.draw.line(s, c, (self.x + gap, self.y), (self.x + r, self.y), w)
        pygame.draw.circle(s, c, (int(self.x), int(self.y)), max(2, int(r * 0.05)), w)
        if self.label is not None:
            fade_in = min(1.0, self.age / 0.15)
            a = int(128 * fade_in)
            if a > 0:
                surf = self.font.render(self.label, True, c)
                surf.set_alpha(a)
                s.blit(surf, (int(self.x - surf.get_width() // 2), int(self.y - surf.get_height() // 2 - self.age * 14)))


class ShotLine:
    LIFE = 0.25

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def dead(self):
        return self.age >= self.LIFE

    def draw(self, s):
        a = max(0.0, 1.0 - self.age / self.LIFE)
        col = (int(255 * a), int(200 * a), int(60 * a))
        w = 1 + int(3 * a)
        pygame.draw.line(s, col, (int(self.x1), int(self.y1)), (int(self.x2), int(self.y2)), w)
        pygame.draw.circle(s, col, (int(self.x2), int(self.y2)), max(2, int(5 * a)))
def bfs_next(grid, blocked, sx, sy, gx, gy):
    if (sx, sy) == (gx, gy):
        return None
    q = deque([(sx, sy)])
    seen = {(sx, sy)}
    parent = {(sx, sy): None}
    goal = None
    while q and goal is None:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and (nx, ny) not in seen:
                if grid[ny][nx] not in (BRICK, WALL) and (nx, ny) not in blocked:
                    seen.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    q.append((nx, ny))
                    if (nx, ny) == (gx, gy):
                        goal = (nx, ny)
                        break
    if goal is None:
        return None
    node = goal
    while parent.get(node) != (sx, sy):
        node = parent[node]
        if node is None:
            return None
    return node


def generate_grid():
    g = []
    for y in range(GRID_H):
        row = []
        for x in range(GRID_W):
            if x in (0, GRID_W - 1) or y in (0, GRID_H - 1):
                row.append(WALL)
            else:
                row.append(BRICK if (x % 2 == 0) and (y % 2 == 0) else EMPTY)
        g.append(row)
    for base in (PLAYER_START, (GRID_W - 4, GRID_H // 2)):
        bx, by = base
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x, y = bx + dx, by + dy
                if 0 <= x < GRID_W and 0 <= y < GRID_H:
                    g[y][x] = EMPTY
    return g


class Enemy:
    def __init__(self, sx, sy):
        self.sx, self.sy = sx, sy
        self.tx, self.ty = sx, sy
        self.x, self.y = float(sx), float(sy)
        self.speed = 1.6
        self.t = 0.0
        self.dead = False
        self.blink = 0
        self.prev_sx, self.prev_sy = sx, sy

    def next_step(self, grid, px, py, bombs):
        blocked = {(b.sx, b.sy) for b in bombs}
        nxt = bfs_next(grid, blocked, self.sx, self.sy, px, py)
        return (nxt[0], nxt[1]) if nxt else (self.sx, self.sy)

    def update(self, dt, game):
        self.prev_sx, self.prev_sy = self.sx, self.sy
        self.t += dt
        self.blink = (int(self.t * 3) % 2) == 0
        if abs(self.x - self.tx) < 0.02 and abs(self.y - self.ty) < 0.02:
            self.sx, self.sy = self.tx, self.ty
            self.tx, self.ty = self.next_step(game.grid, game.player.sx, game.player.sy, game.bombs)
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist > 0.05:
            if step >= dist:
                self.x = self.tx
                self.y = self.ty
            else:
                self.x += (dx / dist) * step
                self.y += (dy / dist) * step
        else:
            self.x = self.tx
            self.y = self.ty


class Sniper(Enemy):
    RELOAD = 5.0

    def __init__(self, sx, sy):
        Enemy.__init__(self, sx, sy)
        self.cooldown = 0.0
        self.aim_t = random.uniform(1.0, 2.0)

    def _player_in_cover(self, grid, sx, sy):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = sx + dx, sy + dy
            if not (0 <= x < GRID_W and 0 <= y < GRID_H):
                return True
            if grid[y][x] in (BRICK, WALL):
                return True
        return False

    def _los_clear(self, grid, sx, sy, px, py):
        dx = (px > sx) - (px < sx)
        dy = (py > sy) - (py < sy)
        x, y = sx + dx, sy + dy
        while (x, y) != (px, py):
            if grid[y][x] in (BRICK, WALL):
                return False
            x += dx
            y += dy
        return True

    def _can_shoot(self, grid, player):
        px, py = player.sx, player.sy
        if self.sx != px and self.sy != py:
            return False
        if self._player_in_cover(grid, px, py):
            return False
        return self._los_clear(grid, self.sx, self.sy, px, py)

    def _shoot(self, game):
        p = game.player
        game.hurt_player()
        sx1 = MARGIN_L + self.sx * TILE + TILE // 2
        sy1 = MARGIN_T + self.sy * TILE + TILE // 2
        sx2 = MARGIN_L + p.sx * TILE + TILE // 2
        sy2 = MARGIN_T + p.sy * TILE + TILE // 2
        game.shots.append(ShotLine(sx1, sy1, sx2, sy2))
        self.cooldown = self.RELOAD
        self.aim_t = 0.0

    def update(self, dt, game):
        Enemy.update(self, dt, game)
        if self.cooldown > 0:
            self.cooldown -= dt
            return
        if self.aim_t > 0:
            self.aim_t -= dt
        if self._can_shoot(game.grid, game.player):
            self._shoot(game)


class Bomb:
    def __init__(self, sx, sy, radius):
        self.sx = sx
        self.sy = sy
        self.radius = radius
        self.t = 0.0
        self.dead = False
        self.flicker = 0.0

    def update(self, dt, game):
        self.t += dt
        self.flicker += dt * 10
        if self.t >= BOMB_FUSE and not self.dead:
            self.dead = True
            game.explode(self.sx, self.sy, self.radius)


class Player:
    def __init__(self, sx, sy):
        self.sx, self.sy = sx, sy
        self.tx, self.ty = sx, sy
        self.x, self.y = float(sx), float(sy)
        self.facing = (0, 1)
        self.speed = PLAYER_SPEED
        self.speed_timer = 0.0
        self.bombs_left = MAX_BOMBS
        self.range = MAX_RANGE
        self.lives = MAX_LIVES
        self.invuln = 0.0
        self.anim = 0.0
        self.moving = False
        self.prev_sx, self.prev_sy = sx, sy
        self.no_damage_time = 0.0
        self.bomb_cd = 0.0
        self.mega = 0.0

    def cell_open(self, grid, sx, sy):
        if not (0 <= sx < GRID_W and 0 <= sy < GRID_H):
            return False
        return grid[sy][sx] not in (BRICK, WALL)

    def update(self, grid, dt):
        self.prev_sx, self.prev_sy = self.sx, self.sy
        self.anim += dt
        self.invuln = max(0.0, self.invuln - dt)
        self.bomb_cd = max(0.0, self.bomb_cd - dt)
        self.mega = max(0.0, self.mega - dt)
        self.no_damage_time += dt
        if self.speed_timer > 0:
            self.speed_timer -= dt
            if self.speed_timer <= 0:
                self.speed = PLAYER_SPEED
        fx, fy = self.facing
        if abs(self.x - self.tx) < 0.02 and abs(self.y - self.ty) < 0.02:
            self.sx, self.sy = self.tx, self.ty
            nx, ny = self.sx + fx, self.sy + fy
            if (fx or fy) and self.cell_open(grid, nx, ny):
                self.tx, self.ty = nx, ny
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        self.moving = dist > 0.05
        step = self.speed * dt
        if dist > 0.05:
            if step >= dist:
                self.x = self.tx
                self.y = self.ty
            else:
                self.x += (dx / dist) * step
                self.y += (dy / dist) * step
        else:
            self.x = self.tx
            self.y = self.ty
class Game:
    def __init__(self):
        self.new_game()

    def new_game(self):
        self.score = 0
        self.mult = 1
        # Streaks laufen ueber Levelgrenzen hinweg weiter und werden nur bei
        # Schaden zurueckgesetzt (Game.hurt_player).
        self.multi_kill_streak = 0
        self.double_kill_streak = 0
        self.level = 1
        self.score_floating_texts = []
        self.state = STATE_START
        self.state_t = 0.0
        self.hiscores = load_highscores()
        self.hs_popup = False
        self.hs_name = ''
        self.hs_rank = None
        self.hs_popup_t = 0.0
        self.reset_level()

    def reset_level(self):
        self.grid = generate_grid()
        self.bombs = []
        self.enemies = []
        self.powerups = []
        self.particles = []
        self.effects = []
        self.stars = []
        self.snipers = []
        self.shots = []
        self.sniper_hold = 0.0
        stop_sniper_warning()
        self.player = Player(*PLAYER_START)
        self.time = LEVEL_TIME
        self.spawn_t = ENEMY_INTERVAL
        self.shake = 0.0

    def max_enemies(self):
        return min(MAX_ENEMIES, 1 + self.level)

    @property
    def sniper_active(self):
        return bool(self.snipers)

    @property
    def score_mult(self):
        """Score-Multiplikator: mit jedem 5er-Block der Double-/Multi-Kill-
        Streak verdoppelt sich der Basis-Mult (5 -> x2, 10 -> x4, 15 -> x8, ...).
        Ist ein Sniper aktiv, wird mit *2 multipliziert. Nach einem Sniper-Kill
        wird mit *5 multipliziert. Alle Boni werden nur bei Schaden zurueckgesetzt."""
        st = self.double_kill_streak
        if st < 5:
            base = 1
        else:
            k = st // 5  # 1 bei 5-9, 2 bei 10-14, 3 bei 15-19 usw.
            base = 1 << k  # 2^k
        m = base
        if self.snipers:
            m *= SNIPER_MULT
        if self.mult >= SNIPER_KILL_MULT:
            m *= SNIPER_KILL_MULT
        return m

    def spawn_enemy(self):
        px, py = self.player.sx, self.player.sy
        cands = []
        for y in range(1, GRID_H - 1):
            for x in range(1, GRID_W - 1):
                if self.grid[y][x] == EMPTY and (x != px or y != py):
                    cands.append((x, y))
        if not cands:
            return
        x, y = random.choice(cands)
        self.enemies.append(Enemy(x, y))

    def _spawn_sniper(self):
        px, py = self.player.sx, self.player.sy
        occupied = {(px, py)}
        for e in self.enemies:
            occupied.add((e.sx, e.sy))
        for sn in self.snipers:
            occupied.add((sn.sx, sn.sy))
        cands = []
        for y in range(1, GRID_H - 1):
            for x in range(1, GRID_W - 1):
                if self.grid[y][x] == EMPTY and (x, y) not in occupied:
                    cands.append((x, y))
        if not cands:
            return
        x, y = max(cands, key=lambda c: math.hypot(c[0] - px, c[1] - py))
        self.snipers.append(Sniper(x, y))
        sx = MARGIN_L + x * TILE + TILE // 2
        sy = MARGIN_T + y * TILE + TILE // 2
        self.stars.append(CrosshairEffect(sx, sy))
        play_sniper_warning()

    def hurt_player(self):
        if self.player.invuln > 0:
            return
        self.multi_kill_streak = 0
        self.double_kill_streak = 0
        self.mult = 1
        self.player.lives -= 1
        self.player.no_damage_time = 0.0
        self.player.invuln = 1.3
        self.shake = max(self.shake, 1.0)
        play_sfx('buzz')
        sx = MARGIN_L + self.player.x * TILE + TILE // 2
        sy = MARGIN_T + self.player.y * TILE + TILE // 2
        self.particles.append(Particle(sx, sy, 0, -70, 0, 120, (255, 90, 70), 6))
        self.particles.append(Particle(sx, sy, -45, -50, 0, 110, (255, 120, 80), 5))
        self.particles.append(Particle(sx, sy, 45, -50, 0, 110, (255, 120, 80), 5))
        if self.player.lives <= 0:
            self.state = STATE_OVER
            self.state_t = 0.0
            self.hs_rank = None
            # Runde vorbei: der Sniper ist weg, also auch sein Warnton
            stop_sniper_warning()
            if hs_qualifies(self.score, self.hiscores):
                self.hs_popup = True
                self.hs_name = ''

    def apply_powerup(self, kind):
        p = self.player
        if kind == 'bomb':
            p.bombs_left = min(MAX_BOMBS, p.bombs_left + 1)
        elif kind == 'range':
            p.range = min(MAX_RANGE, p.range + 1)
        elif kind == 'speed':
            p.speed = PLAYER_SPEED * 1.35
            p.speed_timer = 8.0
        elif kind == 'life':
            p.lives = min(MAX_LIVES, p.lives + 1)
        sx = MARGIN_L + p.x * TILE + TILE // 2
        sy = MARGIN_T + p.y * TILE + TILE // 2
        self.particles.append(Particle(sx, sy, 0, -50, 0, 140, (140, 230, 200), 6))

    def try_place_bomb(self):
        p = self.player
        if p.bombs_left <= 0:
            return
        # 500 ms Cooldown gegen versehentliche Doppelklicks / gehaltene Taste
        if p.bomb_cd > 0.0:
            return
        sx, sy = int(round(p.x)), int(round(p.y))
        if any(b.sx == sx and b.sy == sy for b in self.bombs):
            return
        if self.grid[sy][sx] in (BRICK, WALL):
            return
        p.bombs_left -= 1
        p.bomb_cd = BOMB_COOLDOWN
        self.bombs.append(Bomb(sx, sy, p.range))
        p.invuln = max(p.invuln, 0.6)

    def _check_enemy_collisions(self):
        psx, psy = self.player.sx, self.player.sy
        ppx, ppy = self.player.prev_sx, self.player.prev_sy
        for e in self.enemies + self.snipers:
            if (e.sx == psx and e.sy == psy) or \
               (e.prev_sx == psx and e.prev_sy == psy and e.sx == ppx and e.sy == ppy):
                self.hurt_player()

    def explode(self, cx, cy, radius):
        self.score_before = self.score
        self.shake = max(self.shake, 1.0)
        play_sfx('explosion')
        self.effects.append(Effect(cx, cy, 'exp'))
        killed_enemies = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                x, y = cx + dx, cy + dy
                if not (0 <= x < GRID_W and 0 <= y < GRID_H):
                    continue
                cell = self.grid[y][x]
                mult = self.score_mult
                if cell == BRICK:
                    self.grid[y][x] = EMPTY
                    self.score += 10 * mult
                    self.effects.append(Effect(x, y, 'brick'))
                    bx = MARGIN_L + x * TILE + TILE // 2
                    by = MARGIN_T + y * TILE + TILE // 2
                    self.particles.append(Particle(bx, by, random.uniform(-60, 60), random.uniform(-90, -10), 0, 120, BRICK_SHADY, 5))
                    self.particles.append(Particle(bx, by, random.uniform(-80, 80), random.uniform(-80, 80), 0, 120, BRICK_TOP, 4))
                    if random.random() < 0.15:
                        if not (x == self.player.sx and y == self.player.sy):
                            self.powerups.append(Powerup(x, y, random.choice(['bomb', 'range', 'speed', 'life'])))
                elif cell == WALL:
                    continue
                else:
                    for pw in list(self.powerups):
                        if pw.sx == x and pw.sy == y:
                            self.powerups.remove(pw)
                            self.score += 5 * mult
                            bx = MARGIN_L + x * TILE + TILE // 2
                            by = MARGIN_T + y * TILE + TILE // 2
                            self.particles.append(Particle(bx, by, random.uniform(-60, 60), random.uniform(-60, 60), 0, 120, PUP_IN, 5))
                    for e in list(self.enemies):
                        if e.sx == x and e.sy == y:
                            self.enemies.remove(e)
                            killed_enemies += 1
                            self.score += 50 * mult
                            ex = MARGIN_L + e.x * TILE + TILE // 2
                            ey = MARGIN_T + e.y * TILE + TILE // 2
                            self.particles.append(Particle(ex, ey, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, ENEMY, 6))
                            self.particles.append(Particle(ex, ey, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, EYE, 5))
                    for sn in list(self.snipers):
                        if sn.sx == x and sn.sy == y:
                            self.snipers.remove(sn)
                            self.score += 100 * mult
                            self.mult = SNIPER_KILL_MULT
                            stop_sniper_warning()
                            snx = MARGIN_L + sn.sx * TILE + TILE // 2
                            sny = MARGIN_T + sn.sy * TILE + TILE // 2
                            self.particles.append(Particle(snx, sny, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, (120, 124, 150), 6))
                            self.particles.append(Particle(snx, sny, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, EYE, 5))
                    if self.player.sx == x and self.player.sy == y and self.player.invuln <= 0:
                        self.hurt_player()
        if killed_enemies >= MULTI_KILL_KILLS:
            self.multi_kill_streak += 1
            self.double_kill_streak += 1
            self.player.lives = min(MAX_LIVES, self.player.lives + 1)
            sx = MARGIN_L + cx * TILE + TILE // 2
            sy = MARGIN_T + cy * TILE + TILE // 2
            self.stars.append(StarEffect(sx, sy, 'Multi-Kill'))
            play_sfx('multikill')
            if self.multi_kill_streak >= SNIPER_STREAK and not self.snipers and self.state == STATE_PLAY:
                self._spawn_sniper()
        elif killed_enemies >= DOUBLE_KILL_KILLS:
            # Auch ein reiner Double-Kill zaehlt fuer die Belohnungs-Streak -
            # addiert wird jede Bombe mit 2+ Kills, in beliebiger Reihenfolge.
            self.double_kill_streak += 1
            self.player.bombs_left = min(MAX_BOMBS, self.player.bombs_left + 1)
            sx = MARGIN_L + cx * TILE + TILE // 2
            sy = MARGIN_T + cy * TILE + TILE // 2
            self.stars.append(StarEffect(sx, sy, 'Double-Kill'))
            play_sfx('doublekill')
        # Weder Double- noch Multi-Kill: die Streaks laufen weiter, sie werden
        # ausschliesslich bei Schaden zurueckgesetzt.
        if self.double_kill_streak >= MEGA_KILL_STREAK:
            self._mega_kill(cx, cy)
        score_delta = self.score - self.score_before
        if score_delta > 0:
            self.score_floating_texts.append({
                'text': str(score_delta),
                'age': 0.0,
            })

    def _mega_kill(self, cx, cy):
        sx = MARGIN_L + cx * TILE + TILE // 2
        sy = MARGIN_T + cy * TILE + TILE // 2
        self.stars.append(StarEffect(sx, sy, 'Mega-Kill', mega_color))
        play_sfx('megakill')
        self.player.invuln = MEGA_INVULN_TIME
        self.player.mega = MEGA_INVULN_TIME

    def start(self):
        self.state = STATE_PLAY
        self.state_t = 0.0

    def toggle_pause(self):
        if self.state == STATE_PLAY:
            self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            self.state = STATE_PLAY

    def handle_input(self):
        if self.state == STATE_PLAY:
            keys = pygame.key.get_pressed()
            fx = fy = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                fx = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                fx = 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                fy = -1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                fy = 1
            if fx == 0 or fy == 0:
                jfx, jfy = _joy_dir()
                fx = fx or jfx
                fy = fy or jfy
            if fx or fy:
                self.player.facing = (fx, fy)
            if keys[pygame.K_SPACE] or _joy_button(JOY_BTN_B):
                self.try_place_bomb()
        elif self.state == STATE_START:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN] or _joy_button(JOY_BTN_A):
                self.start()
        elif self.state == STATE_OVER:
            keys = pygame.key.get_pressed()
            if not self.hs_popup and self.hs_popup_t <= 0:
                if keys[pygame.K_r] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
                    self.new_game()

    def update(self, dt):
        # Watchdog: der Warnton darf den Sniper nie ueberleben, egal wie er
        # verschwunden ist (Bombe, Levelwechsel, Game Over, direkt entfernt).
        if not self.snipers and sniper_warning_playing():
            stop_sniper_warning()
        for ft in list(self.score_floating_texts):
            ft['age'] += dt
            if ft['age'] >= FT_MAX_AGE:
                self.score_floating_texts.remove(ft)
        if self.state == STATE_PLAY:
            self.shake = max(0.0, self.shake - dt * 4.0)
            if self.sniper_active:
                self.sniper_hold = max(0.0, self.sniper_hold - dt)
            else:
                self.sniper_hold = 0.0
                self.time -= dt
            if self.time <= 0:
                self.level += 1
                self.reset_level()
                self.time = LEVEL_TIME
            self.spawn_t -= dt
            while self.spawn_t <= 0 and len(self.enemies) < self.max_enemies():
                self.spawn_enemy()
                self.spawn_t += ENEMY_INTERVAL
            for e in list(self.enemies):
                if e.dead:
                    self.enemies.remove(e)
                else:
                    e.update(dt, self)
            for sn in self.snipers:
                sn.update(dt, self)
            for b in self.bombs:
                b.update(dt, self)
            self.bombs = [b for b in self.bombs if not b.dead]
            for p in self.powerups:
                p.update(dt)
            for pt in list(self.particles):
                if pt.alive():
                    pt.update(dt)
            self.particles = [pt for pt in self.particles if pt.alive()]
            for ef in list(self.effects):
                ef.update(dt)
                if ef.life > 0.35:
                    self.effects.remove(ef)
            for st in self.stars:
                st.update(dt)
            self.stars = [st for st in self.stars if not st.dead()]
            for sh in list(self.shots):
                sh.update(dt)
            self.shots = [sh for sh in self.shots if not sh.dead()]
            self.handle_input()
            self.player.update(self.grid, dt)
            self._check_enemy_collisions()
            px, py = self.player.sx, self.player.sy
            for p in list(self.powerups):
                if p.sx == px and p.sy == py:
                    self.powerups.remove(p)
                    self.apply_powerup(p.kind)
            p = self.player
            # Der Sniper friert den Levelcountdown ein, nicht diesen
            # Nachschuss - solange er lebt, gibt es ihn schon nach 7 statt 10 s.
            free_after = FREE_BOMB_TIME_SNIPER if self.sniper_active else FREE_BOMB_TIME
            if p.bombs_left <= 0 and p.no_damage_time >= free_after:
                p.bombs_left = min(MAX_BOMBS, p.bombs_left + 1)
                p.no_damage_time = 0.0
        else:
            self.hs_popup_t = max(0.0, self.hs_popup_t - dt)
            self.handle_input()
def draw_grid(g, surf, ox, oy):
    for y in range(GRID_H):
        for x in range(GRID_W):
            rx, ry = ox + x * TILE, oy + y * TILE
            cell = g[y][x]
            if cell == WALL:
                pygame.draw.rect(surf, WALL_TOP, pygame.Rect(rx + 1, ry + 1, TILE - 2, TILE - 2))
                pygame.draw.rect(surf, WALL, pygame.Rect(rx + 3, ry + 3, TILE - 6, TILE - 6))
                pygame.draw.rect(surf, WALL_GLOW, pygame.Rect(rx + 3, ry + 3, TILE - 6, 3))
            elif cell == BRICK:
                pygame.draw.rect(surf, BRICK, pygame.Rect(rx + 2, ry + 2, TILE - 4, TILE - 4))
                pygame.draw.rect(surf, BRICK_TOP, pygame.Rect(rx + 3, ry + 3, (TILE - 6) // 2, (TILE - 6) // 2))
                pygame.draw.rect(surf, BRICK_SHADY, pygame.Rect(rx + 2, ry + 2, TILE - 4, 2))
                pygame.draw.rect(surf, BRICK_SHADY, pygame.Rect(rx + 2, ry + TILE - 4, TILE - 4, 2))
                pygame.draw.line(surf, BRICK_SHADY, (rx + TILE // 2, ry + 2), (rx + TILE // 2, ry + TILE - 2), 2)
                pygame.draw.line(surf, BRICK_SHADY, (rx + 2, ry + TILE // 2), (rx + TILE - 2, ry + TILE // 2), 2)
            else:
                pygame.draw.rect(surf, FLOOR if (x + y) % 2 == 0 else FLOOR_ALT, pygame.Rect(rx, ry, TILE, TILE))


def draw_powerups(surf, powerups, ox, oy, t):
    for p in powerups:
        cx = ox + p.sx * TILE + TILE // 2
        cy = oy + p.sy * TILE + TILE // 2
        r = 14 + int(math.sin(t * 4 + p.sx) * 3)
        surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
        if p.kind == 'bomb':
            col = PBOMB
        elif p.kind == 'range':
            col = PRANGE
        elif p.kind == 'speed':
            col = PSPEED
        else:
            col = PLIFE
        pygame.draw.circle(surf2, (*PUP_OUT,), (TILE, TILE), r + 2)
        pygame.draw.circle(surf2, (*col,), (TILE, TILE), r)
        pygame.draw.circle(surf2, (*PUP_IN,), (TILE - 3, TILE - 3), 5)
        surf.blit(surf2, (cx - TILE, cy - TILE))


def draw_enemies(surf, enemies, ox, oy, t):
    for e in enemies:
        cx = ox + e.x * TILE + TILE // 2
        cy = oy + e.y * TILE + TILE // 2
        surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf2, ENEMY2, (TILE - 22, TILE - 20, 44, 38))
        body = ENEMY if e.blink else ENEMY2
        pygame.draw.ellipse(surf2, body, (TILE - 19, TILE - 17, 38, 32))
        pygame.draw.ellipse(surf2, EYE, (TILE - 12, TILE - 9, 12, 12))
        pygame.draw.ellipse(surf2, EYE, (TILE, TILE - 9, 12, 12))
        pygame.draw.ellipse(surf2, PEYE2, (TILE - 9, TILE - 7, 6, 6))
        pygame.draw.ellipse(surf2, PEYE2, (TILE + 3, TILE - 7, 6, 6))
        pygame.draw.rect(surf2, ENEMY, (TILE - 15, TILE + 14, 13, 10))
        pygame.draw.rect(surf2, ENEMY, (TILE + 2, TILE + 14, 13, 10))
        surf.blit(surf2, (cx - TILE, cy - TILE))


def draw_snipers(surf, snipers, ox, oy):
    for sn in snipers:
        cx = ox + sn.sx * TILE + TILE // 2
        cy = oy + sn.sy * TILE + TILE // 2
        surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf2, (60, 64, 88), (TILE - 19, TILE - 13, 38, 24))
        pygame.draw.ellipse(surf2, (80, 84, 110), (TILE - 15, TILE - 22, 30, 16))
        pygame.draw.ellipse(surf2, (100, 104, 130), (TILE - 7, TILE - 26, 14, 8))
        pygame.draw.line(surf2, (210, 214, 234), (TILE - 4, TILE - 26), (TILE + 14, TILE - 26), 2)
        pygame.draw.circle(surf2, (255, 60, 60), (TILE + 9, TILE - 26), 2)
        pygame.draw.ellipse(surf2, EYE, (TILE - 8, TILE - 17, 7, 5))
        pygame.draw.ellipse(surf2, EYE, (TILE + 2, TILE - 17, 7, 5))
        pygame.draw.ellipse(surf2, PEYE2, (TILE - 6, TILE - 15, 3, 3))
        pygame.draw.ellipse(surf2, PEYE2, (TILE + 4, TILE - 15, 3, 3))
        surf.blit(surf2, (cx - TILE, cy - TILE))


def draw_bombs(surf, bombs, ox, oy, t):
    for b in bombs:
        cx = ox + b.sx * TILE + TILE // 2
        cy = oy + b.sy * TILE + TILE // 2
        surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
        a = int(60 + 40 * math.sin(b.flicker * 6))
        a = max(0, min(140, a))
        pygame.draw.circle(surf2, (*FUSE_GLOW, a), (TILE, TILE), int(TILE * 0.65))
        pygame.draw.circle(surf2, (40, 40, 58), (TILE, TILE), int(TILE * 0.42))
        pygame.draw.circle(surf2, (72, 76, 98), (TILE - 12, TILE - 12), int(TILE * 0.22))
        if b.t < BOMB_FUSE:
            pygame.draw.circle(surf2, FUSE, (TILE + 14, TILE - 12), 5)
        surf.blit(surf2, (cx - TILE, cy - TILE))


def draw_player(surf, p, ox, oy, t):
    fx, fy = p.facing
    cx = ox + p.x * TILE + TILE // 2
    cy = oy + p.y * TILE + TILE // 2
    inv = p.invuln > 0
    body, hatc = PBODY, PHAT
    if p.mega > 0:
        body, hatc = mega_color(t), mega_color(t)
    bob = math.sin(t * 6) * (1 if p.moving else 0)
    surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(surf2, (0, 0, 0, 60), (TILE - 15, TILE + 18, 30, 7))
    pygame.draw.rect(surf2, PFOOT, (TILE - 11, TILE + 7, 10, 9))
    pygame.draw.rect(surf2, PFOOT, (TILE + 1, TILE + 7, 10, 9))
    pygame.draw.rect(surf2, body, (TILE - 12, TILE - 5, 24, 15))
    pygame.draw.circle(surf2, body, (TILE, TILE - 11 + bob), 13)
    pygame.draw.arc(surf2, hatc, pygame.Rect(TILE - 10, TILE - 19 + bob, 20, 20), 0, 3.14, 3)
    pygame.draw.circle(surf2, hatc, (TILE, TILE - 16 + bob), 10)
    if fx > 0:
        ex, ex2 = TILE + 3, TILE + 9
    elif fx < 0:
        ex, ex2 = TILE - 11, TILE - 5
    else:
        ex, ex2 = TILE - 5, TILE + 1
    ey = TILE - 9 + bob
    pygame.draw.ellipse(surf2, PEYE, (ex - 4, ey, 9, 9))
    pygame.draw.ellipse(surf2, PEYE, (ex2 - 4, ey, 9, 9))
    pygame.draw.ellipse(surf2, PEYE2, (ex - 2, ey + 2, 4, 4))
    pygame.draw.ellipse(surf2, PEYE2, (ex2 - 2, ey + 2, 4, 4))
    if inv:
        a = 190 if (int(t * 20) % 2 == 0) else 50
        surf2.set_alpha(a)
    surf.blit(surf2, (cx - TILE, cy - TILE))


def draw_hud(surf, game, ox, oy, t=0.0):
    h = MARGIN_T
    pygame.draw.rect(surf, HUD_BG, pygame.Rect(0, 0, SCREEN_W, h))
    f = make_font(None, 34)
    fs = make_font(None, 26)
    def txt(s, x, y, str, font, col):
        img = font.render(str, True, col)
        s.blit(img, (x, y))
    txt(surf, ox, 16, 'SCORE %d' % game.score, f, TEXT)
    txt(surf, ox + 340, 16, 'LEVEL %d' % game.level, f, HUD_ACC)
    mult = game.score_mult
    if mult > 1:
        fm = make_font(None, 26, True)
        img = fm.render('MULTI x%d' % mult, True, star_color(t))
        surf.blit(img, (ox + 505, 21))
    txt(surf, ox + 640, 16, 'TIME %d' % int(max(0, game.time)), f, TEXT)
    if game.sniper_active:
        hold = make_font(None, 22, True)
        pulse = 0.55 + 0.45 * math.sin(t * 8.0)
        col = (int(255 * pulse), int(110 * pulse), int(80 * pulse))
        img = hold.render('SNIPER - HOLD', True, col)
        hx = SCREEN_W // 2 - img.get_width() // 2
        surf.blit(img, (hx, 52))
        pygame.draw.rect(surf, col, pygame.Rect(hx, 76, img.get_width(), 2))
    txt(surf, ox + 920, 16, 'BOMBS', fs, TEXT_DIM)
    bomb_x = ox + 920
    cooling = game.player.bomb_cd > 0.0
    for i in range(MAX_BOMBS):
        filled = i < game.player.bombs_left
        cx = bomb_x + 18 + i * 28
        col = (210, 230, 250) if filled else (70, 72, 95)
        r = 16 if filled else 7
        if cooling:
            # Cooldown: die Slots pulsieren gedimmt, damit die Sperre sichtbar ist
            col = (int(col[0] * 0.45), int(col[1] * 0.45), int(col[2] * 0.55))
            r = max(5, int(r * 0.75))
        pygame.draw.circle(surf, col, (cx, 60), r)
    if cooling:
        cdl = make_font(None, 18, True).render('%.1fs' % game.player.bomb_cd, True, HUD_ACC)
        surf.blit(cdl, (bomb_x + 18, 78))
    txt(surf, ox + 1060, 16, 'RANGE %d' % game.player.range, fs, TEXT_DIM)
    txt(surf, SCREEN_W - 320, 16, 'LIVES', fs, TEXT_DIM)
    life_x = SCREEN_W - 320
    for i in range(MAX_LIVES):
        filled = i < game.player.lives
        cx = life_x + 16 + i * 26
        pygame.draw.circle(surf, (255, 120, 80) if filled else (70, 72, 95), (cx, 60), 12 if filled else 6)
    if game.hiscores:
        n1, s1 = game.hiscores[0]
        img1 = make_font(None, 24).render('1ST  %s  %d' % (n1, s1), True, HUD_ACC)
        surf.blit(img1, (ox, 48))
    pygame.draw.rect(surf, WALL_GLOW, pygame.Rect(0, h - 2, SCREEN_W, 2))


def draw_hs_popup(surf, game, t):
    bw, bh = 540, 430
    bx = SCREEN_W // 2 - bw // 2
    by = (SCREEN_H - bh) // 2
    p = pygame.Surface((bw, bh), pygame.SRCALPHA)
    pygame.draw.rect(p, (20, 22, 36, 235), (0, 0, bw, bh), border_radius=16)
    pygame.draw.rect(p, HUD_ACC, (3, 3, bw - 6, bh - 6), border_radius=13, width=2)
    f_big = make_font(None, 30)
    f_field = make_font(None, 28)
    f_small = make_font(None, 20)
    f_head = make_font(None, 18)
    name = _clean_name(game.hs_name)
    title = f_big.render('NEW HIGHSCORE!', True, HUD_ACC)
    p.blit(title, (bw // 2 - title.get_width() // 2, 14))
    pygame.draw.rect(p, (244, 246, 252, 16), (30, 58, bw - 60, 46))
    name_img = f_field.render('  ' + name, True, TEXT)
    p.blit(name_img, (22, 66))
    cursor = f_field.render('|', True, TEXT)
    if int(t * 3) % 2 == 0:
        p.blit(cursor, (22 + name_img.get_width() + 8, 66))
    cnt = f_head.render('%d / %d' % (len(name), HS_NAME_MAX), True, TEXT_DIM)
    p.blit(cnt, (bw - 30 - cnt.get_width(), 70))
    cap = f_head.render('max. %d Characters' % HS_NAME_MAX, True, TEXT_DIM)
    p.blit(cap, (bw // 2 - cap.get_width() // 2, 100))
    head = f_head.render('CURRENT TOP 10', True, HUD_ACC)
    p.blit(head, (30, 124))
    ins = sum(1 for n, s in game.hiscores if s > game.score)
    full = []
    inserted = False
    for idx, (n, s) in enumerate(game.hiscores):
        if ins == idx and not inserted:
            full.append((name, game.score, True))
            inserted = True
        full.append((n, s, False))
    if not inserted:
        full.append((name, game.score, True))
    for i, (n, s, new) in enumerate(full[:10]):
        y = 154 + i * 22
        line = '%2d.  %s  %d' % (i + 1, n, s)
        if new:
            line += '   NEW'
        col = FX_GREEN if new else TEXT_DIM
        img = f_small.render(line, True, col)
        p.blit(img, (30, y))
    hint = f_small.render('ENTER to confirm   -   backspace to delete', True, TEXT_DIM)
    p.blit(hint, (bw // 2 - hint.get_width() // 2, bh - 44))
    surf.blit(p, (bx, by))


def _draw_key(surf, cx, cy, label, size, col, border, text):
    r = max(2, size // 5)
    x, y = cx - size // 2, cy - size // 2
    pygame.draw.rect(surf, col, (x, y, size, size), border_radius=r)
    pygame.draw.rect(surf, border, (x + 2, y + 2, size - 4, size - 4), border_radius=r, width=2)
    if label:
        f = make_font(None, max(8, int(size * 0.45)))
        img = f.render(label, True, text)
        surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))


def _draw_face(surf, cx, cy, letter, col):
    pygame.draw.circle(surf, (col[0] - 25, col[1] - 25, col[2] - 25), (cx - 16, cy - 16), 16)
    pygame.draw.circle(surf, col, (cx - 14, cy - 14), 14)
    f = make_font(None, 18)
    img = f.render(letter, True, (245, 245, 245))
    surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))


def _base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONTROL_IMG = os.path.join(_base_dir(), 'assets', 'steuerung.png')
_MISSING = object()
_CONTROL_IMG = _MISSING


def _get_control_image():
    global _CONTROL_IMG
    if _CONTROL_IMG is _MISSING:
        try:
            _CONTROL_IMG = pygame.image.load(CONTROL_IMG)
        except Exception:
            _CONTROL_IMG = None
    return _CONTROL_IMG


def _draw_image_centered(surf, box, img, pad=24):
    bx, by, bw, bh = box
    mw, mh = img.get_width(), img.get_height()
    maxw = bw - 2 * pad
    maxh = bh - 2 * pad
    scale = min(maxw / mw, maxh / mh)
    nw = max(1, int(mw * scale))
    nh = max(1, int(mh * scale))
    resized = pygame.transform.scale(img, (nw, nh))
    cx = bx + (bw - nw) // 2
    cy = by + (bh - nh) // 2
    surf.blit(resized, (cx, cy))


def draw_start_screen(surf, game):
    bg = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 140), (0, 0, SCREEN_W, SCREEN_H))
    surf.blit(bg, (0, 0))
    f_t = make_font(None, 96)
    ti = f_t.render('BOMB!', True, TEXT)
    surf.blit(ti, (SCREEN_W // 2 - ti.get_width() // 2, 24))
    KEY_COL = (160, 168, 190)
    KEY_BORD = (90, 96, 120)
    KEY_TXT = (25, 25, 35)
    f_lab = make_font(None, 20)

    def lab(s, cx, y):
        img = f_lab.render(s, True, (150, 156, 182))
        surf.blit(img, (cx - img.get_width() // 2, y))

    bx, by, bw, bh = 40, 130, 720, 520
    pygame.draw.rect(surf, (30, 34, 54), (bx, by, bw, bh), border_radius=16)
    pygame.draw.rect(surf, HUD_ACC, (bx + 3, by + 3, bw - 6, bh - 6), border_radius=14, width=2)
    ctrl_img = _get_control_image()
    if ctrl_img is not None:
        _draw_image_centered(surf, (bx, by, bw, bh), ctrl_img)
    else:
        f_err = make_font(None, 24)
        err = f_err.render('Steuerungs-Bild nicht gefunden', True, (210, 120, 90))
        surf.blit(err, (bx + bw // 2 - err.get_width() // 2, by + bh // 2 - err.get_height() // 2))
        f_err2 = make_font(None, 18)
        err2 = f_err2.render(CONTROL_IMG, True, (150, 156, 182))
        surf.blit(err2, (bx + bw // 2 - err2.get_width() // 2, by + bh // 2 + 12))

    hx, hy = 780, 130
    hw, hh = 360, 520
    pygame.draw.rect(surf, (24, 26, 44), (hx, hy, hw, hh), border_radius=16)
    pygame.draw.rect(surf, (70, 74, 100), (hx + 3, hy + 3, hw - 6, hh - 6), border_radius=14, width=2)
    f_hh = make_font(None, 28, True)
    hh_i = f_hh.render('HIGH SCORES', True, HUD_ACC)
    surf.blit(hh_i, (hx + hw // 2 - hh_i.get_width() // 2, hy + 24))
    f_h = make_font(None, 20)
    for i, (n, sc) in enumerate(game.hiscores):
        li = f_h.render('%d.  %s  %d' % (i + 1, n, sc), True, TEXT)
        surf.blit(li, (hx + 24, hy + 64 + i * 34))
    if not game.hiscores:
        li = f_h.render('no scores yet - be first!', True, (150, 156, 182))
        surf.blit(li, (hx + 24, hy + 64))

    f_p = make_font(None, 30)
    pi = f_p.render('Press ENTER to play', True, HUD_ACC)
    surf.blit(pi, (SCREEN_W // 2 - pi.get_width() // 2, SCREEN_H - 92))
    f_s = make_font(None, 24)
    si = f_s.render('Press M for settings', True, TEXT_DIM)
    surf.blit(si, (SCREEN_W // 2 - si.get_width() // 2, SCREEN_H - 50))


def draw_state(surf, game, t):
    if game.state == STATE_START:
        draw_start_screen(surf, game)
    elif game.state == STATE_PAUSED:
        surf2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(surf2, (0, 0, 0, 110), pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        f = make_font(None, 84)
        img = f.render('PAUSED', True, TEXT)
        surf.blit(img, (SCREEN_W // 2 - img.get_width() // 2, SCREEN_H // 2 - 40))
        f2 = make_font(None, 26)
        img2 = f2.render('P = weiter     M = Einstellungen', True, HUD_ACC)
        surf.blit(img2, (SCREEN_W // 2 - img2.get_width() // 2, SCREEN_H // 2 + 60))
    elif game.state == STATE_OVER:
        surf2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(surf2, (0, 0, 0, 160), pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        f = make_font(None, 96)
        f2 = make_font(None, 30)
        img = f.render('GAME OVER', True, FX_RED)
        surf.blit(img, (SCREEN_W // 2 - img.get_width() // 2, SCREEN_H // 2 - 60))
        img2 = f2.render('SCORE %d' % game.score, True, TEXT)
        surf.blit(img2, (SCREEN_W // 2 - img2.get_width() // 2, SCREEN_H // 2 + 25))
        y3 = SCREEN_H // 2 + 65
        if game.hs_rank is not None:
            fr = make_font(None, 28)
            img_rank = fr.render('NEW HIGHSCORE - #%d!' % (game.hs_rank + 1), True, FX_GREEN)
            surf.blit(img_rank, (SCREEN_W // 2 - img_rank.get_width() // 2, y3 - 30))
            y3 += 34
        img3 = f2.render('Press R to play again', True, HUD_ACC)
        surf.blit(img3, (SCREEN_W // 2 - img3.get_width() // 2, y3))
        if game.hs_popup:
            draw_hs_popup(surf, game, t)


def draw(surf, game, t):
    surf.fill(BG)
    ox, oy = MARGIN_L, MARGIN_T
    draw_grid(game.grid, surf, ox, oy)
    draw_powerups(surf, game.powerups, ox, oy, t)
    draw_enemies(surf, game.enemies, ox, oy, t)
    draw_snipers(surf, game.snipers, ox, oy)
    draw_bombs(surf, game.bombs, ox, oy, t)
    draw_player(surf, game.player, ox, oy, t)
    for ef in game.effects:
        ef.draw(surf, ox, oy)
    for pt in game.particles:
        pt.draw(surf)
    for st in game.stars:
        st.draw(surf)
    for sh in game.shots:
        sh.draw(surf)
    draw_hud(surf, game, ox, oy, t)
    draw_state(surf, game, t)


_FT_FONT_CACHE = {}

def _floating_font(size):
    f = _FT_FONT_CACHE.get(size)
    if f is None:
        f = make_font(None, size)
        _FT_FONT_CACHE[size] = f
    return f

def _draw_score_floating_texts(frame, game):
    for ft in game.score_floating_texts:
        p = ft['age'] / FT_MAX_AGE
        size = int(round(FT_START_SIZE + (FT_END_SIZE - FT_START_SIZE) * p))
        px = MARGIN_L + game.player.sx * TILE + TILE // 2
        py = MARGIN_T + game.player.sy * TILE + TILE // 2
        img = _floating_font(size).render(ft['text'], True, FT_COLOR)
        frame.blit(img, (px - img.get_width() // 2, py - img.get_height() // 2))

SFX = {}
SFX_BASE = {}
_SNIPERWARN_CH = None


def play_sfx(name):
    s = SFX.get(name) or SFX.get('doublekill')
    if s is not None:
        try:
            s.play()
        except Exception:
            pass


def play_sniper_warning():
    """Warnton auf einem eigenen Channel, damit er exakt stoppbar ist."""
    global _SNIPERWARN_CH
    stop_sniper_warning()
    s = SFX.get('sniperwarning') or SFX.get('doublekill')
    if s is None:
        return
    try:
        _SNIPERWARN_CH = s.play(loops=0)
    except Exception:
        _SNIPERWARN_CH = None


def sniper_warning_playing():
    global _SNIPERWARN_CH
    if _SNIPERWARN_CH is None:
        return False
    try:
        return _SNIPERWARN_CH.get_busy()
    except Exception:
        return False


def stop_sniper_warning():
    global _SNIPERWARN_CH
    ch = _SNIPERWARN_CH
    _SNIPERWARN_CH = None
    if ch is not None:
        try:
            ch.stop()
        except Exception:
            pass
    # zusaetzlich alle Kanäle des Sounds selbst anhalten - der Channel-Handle
    # kann verloren gehen, das Sound-Objekt nicht
    for key in ('sniperwarning', 'doublekill'):
        s = SFX.get(key)
        if s is None:
            continue
        try:
            s.stop()
        except Exception:
            pass


def register_sfx(name, sound, base_volume):
    SFX[name] = sound
    SFX_BASE[name] = base_volume
    _apply_sfx_volume(name)


def _apply_sfx_volume(name):
    s = SFX.get(name)
    if s is None:
        return
    try:
        s.set_volume(max(0.0, min(1.0, SFX_BASE.get(name, 1.0) * _volume_scale())))
    except Exception:
        pass


def _volume_scale():
    try:
        return max(0.0, min(1.0, SETTINGS.volume / float(VOL_MAX)))
    except Exception:
        return 1.0


def apply_volume():
    """Ueberträgt die Master-Lautstärke (0-255) auf Musik und alle Effekte."""
    scale = _volume_scale()
    try:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, MUSIC_VOL * scale)))
    except Exception:
        pass
    for name in list(SFX):
        _apply_sfx_volume(name)


def _beep_buffer(duration=0.07, freq=1200.0, amp=0.7):
    """Beep-PCM ohne numpy erzeugen (array + struct)."""
    import array
    init = pygame.mixer.get_init()
    if not init:
        return None
    rate, _size, channels = init
    n = max(1, int(rate * duration))
    samples = array.array('h')
    for i in range(n):
        env = max(0.0, 1.0 - i / float(n))
        s = math.sin(2.0 * math.pi * freq * i / rate)
        if s > 0.35:
            s = 1.0
        elif s < -0.35:
            s = -1.0
        else:
            s = 0.0
        samples.append(int(32767 * amp * env * s))
    if channels == 1:
        return bytearray(samples.tobytes())
    inter = array.array('h')
    for v in samples:
        inter.append(v)
        inter.append(v)
    return bytearray(inter.tobytes())


def _init_beep():
    try:
        buf = _beep_buffer()
        if buf is not None:
            register_sfx('beep', pygame.mixer.Sound(buffer=buf), 1.0)
    except Exception:
        pass


def _init_sfx():
    _init_beep()
    try:
        import numpy as np
    except ImportError:
        apply_volume()
        return
    freq = pygame.mixer.get_init()[0]

    def make(duration, fn):
        n = max(1, int(freq * duration))
        t = np.arange(n) / freq
        s = np.clip(fn(t), -1.0, 1.0)
        if s.ndim == 1:
            s = np.column_stack((s, s))
        pcm = (s * 32767.0).astype(np.int16).reshape(-1)
        return bytearray(pcm.tobytes())

    def explosion_fn(t):
        noise = np.random.rand(len(t)) * 2.0 - 1.0
        decay = np.exp(-t / 0.16)
        thump = np.sin(2.0 * np.pi * 52.0 * t) * np.exp(-t / 0.14)
        return (noise * 0.95 + thump * 0.8) * decay

    def buzz_fn(t):
        f = 90.0
        s = np.sign(np.sin(2.0 * np.pi * f * t))
        s += 0.5 * np.sin(2.0 * np.pi * f * 2.0 * t)
        s += 0.3 * np.sin(2.0 * np.pi * f * 3.0 * t)
        return s * np.exp(-t * 6.0)

    def doublekill_fn(t):
        s = np.zeros_like(t)
        for i, f in enumerate((392.0, 523.25, 698.46, 1046.5)):
            tt = t - i * 0.08
            m = tt >= 0.0
            if m.any():
                s[m] += np.sin(2.0 * np.pi * f * tt[m]) * np.exp(-tt[m] * 3.5)
        return s * 0.9

    try:
        register_sfx('explosion', pygame.mixer.Sound(buffer=make(0.55, explosion_fn)), 0.16)
        register_sfx('buzz', pygame.mixer.Sound(buffer=make(0.35, buzz_fn)), 0.18)
        register_sfx('doublekill', pygame.mixer.Sound(buffer=make(0.55, doublekill_fn)), 0.18)
    except Exception:
        pass

    dk = _doublekill_sound_path()
    if dk is not None:
        try:
            register_sfx('doublekill', pygame.mixer.Sound(dk), 0.45)
        except Exception:
            pass

    mk = _multikill_sound_path()
    if mk is not None:
        try:
            register_sfx('multikill', pygame.mixer.Sound(mk), 0.45)
        except Exception:
            pass
    if 'multikill' not in SFX:
        SFX['multikill'] = SFX.get('doublekill')
        SFX_BASE['multikill'] = SFX_BASE.get('doublekill', 0.45)

    mg = _megakill_sound_path()
    if mg is not None:
        try:
            register_sfx('megakill', pygame.mixer.Sound(mg), 0.45)
        except Exception:
            pass
    if 'megakill' not in SFX:
        SFX['megakill'] = SFX.get('multikill')
        SFX_BASE['megakill'] = SFX_BASE.get('multikill', 0.45)

    sw = _sniperwarning_sound_path()
    if sw is not None:
        try:
            register_sfx('sniperwarning', pygame.mixer.Sound(sw), 0.5)
        except Exception:
            pass
    apply_volume()


def _resolve_music_path():
    p = os.path.join(_base_dir(), 'bomb.mp3')
    if os.path.exists(p):
        return p
    return None


def _doublekill_sound_path():
    for p in (
        r"G:\bomb\Double Kill Sound Effect.mp3",
        os.path.join(_base_dir(), 'doublekill.mp3'),
    ):
        if os.path.isfile(p):
            return p
    return None


def _multikill_sound_path():
    for p in (
        r"G:\bomb\Multi Kill  - Sound Effect.mp3",
        os.path.join(_base_dir(), 'multikill.mp3'),
    ):
        if os.path.isfile(p):
            return p
    return None


def _sniperwarning_sound_path():
    for p in (
        r"G:\bomb\sniper warning.mp3",
        os.path.join(_base_dir(), 'sniperwarning.mp3'),
    ):
        if os.path.isfile(p):
            return p
    return None

def _megakill_sound_path():
    for p in (
        r"G:\bomb\Mega Kill - Sound Effect.mp3",
        os.path.join(_base_dir(), 'megakill.mp3'),
    ):
        if os.path.isfile(p):
            return p
    return None


def apply_display():
    """Legt das Ausgabefenster gemäß Auflösungs-/Vollbild-Einstellung an."""
    size = SETTINGS.target_size()
    flags = 0
    if SETTINGS.fullscreen:
        flags = pygame.FULLSCREEN
    else:
        flags = pygame.RESIZABLE
    try:
        canvas = pygame.display.set_mode(size, flags)
    except Exception:
        flags = 0
        canvas = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    return canvas


def _sync_music(state):
    try:
        m = pygame.mixer.music
        if state == STATE_PAUSED:
            if m.get_busy() and m.is_playing():
                m.pause()
        else:
            if not m.get_busy():
                m.play()
            elif not m.is_playing():
                m.unpause()
    except Exception:
        pass


def _hs_file():
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'highscores.json')


def _machine_seed():
    """Geraetegebundener Wert. Laeuft nicht auf einem Datentraeger, den der
    Spieler einfach kopieren kann: die Windows MachineGuid aus der
    Registry, ergaenzt um den Hostnamen. Ohne Registry-Zugriff (portable
    Builds) faellt der Hostname allein zurueck."""
    parts = []
    try:
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SOFTWARE\Microsoft\Cryptography',
                               0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            with k:
                parts.append(str(winreg.QueryValueEx(k, 'MachineGuid')[0]))
        except OSError:
            pass
    except Exception:
        pass
    try:
        parts.append(os.environ.get('COMPUTERNAME', ''))
    except Exception:
        pass
    try:
        # Prozess-/Installationsbreite Streuung gegen triviales Kopieren
        parts.append(str(ctypes.windll.kernel32.GetCurrentProcessId()))
    except Exception:
        pass
    return '|'.join(p for p in parts if p)


def _hs_key():
    """Schluessel fuer die Signatur der Highscore-Datei.

    Bewusst KEIN geheimer Wert im Quelltext: ein im Programm sichtbarer
    Schluessel laesst sich aus der EXE auslesen und damit nachbilden. Der
    Schluessel wird deshalb zur Laufzeit aus Maschinen-ID und einem
    pro Installationsordner zufaelligen Salt abgeleitet. Damit sind
    nachtraegliche Edits von highscores.json auf diesem Rechner nicht mehr
    moeglich - und weil der Salt in einer zweiten Datei steckt, deren Wert
    sich pro Neuinstallation aendert, gilt das auch nicht fuer eine
    weitergegebene Datei."""
    salt_path = os.path.join(os.path.dirname(_hs_file()), '.bombkey')
    salt = b''
    try:
        with open(salt_path, 'rb') as fh:
            salt = fh.read(64)
    except Exception:
        pass
    if not salt:
        salt = base64.b64encode(os.urandom(32))
        try:
            with open(salt_path, 'wb') as fh:
                fh.write(salt)
        except Exception:
            # Nur-Lese-Ordner: dann bleibt der Key stabil fuer die Session
            salt = b'fallback-salt'
    return hashlib.sha256(salt + _machine_seed().encode('utf-8', 'replace')).digest()


def _hs_payload(hs):
    return json.dumps([[n, int(s)] for n, s in hs],
                      ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _hs_sign(hs):
    return hmac.new(_hs_key(), _hs_payload(hs).encode('utf-8'), hashlib.sha256).hexdigest()


def _hs_write(path, hs):
    """Atomar schreiben: erst in eine Temp-Datei, dann os.replace. So kann ein
    Absturz mitten im Schreiben die Liste nicht zerstoeren."""
    doc = {
        'version': 2,
        'sig': _hs_sign(hs),
        'scores': [[n, int(s)] for n, s in hs],
    }
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, ensure_ascii=False)
    os.replace(tmp, path)


def _hs_read(path):
    """Liefert (entries, signiert). Fehlt die Signatur oder passt sie nicht,
    ist die Datei manipuliert und wird verworfen."""
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        entries = data.get('scores') or []
        sig = data.get('sig') or ''
        parsed = []
        for e in entries:
            if isinstance(e, (list, tuple)) and len(e) == 2:
                parsed.append([str(e[0]), int(e[1])])
            elif isinstance(e, dict):
                parsed.append([str(e.get('name', '')), int(e.get('score', 0))])
        return parsed, (sig if isinstance(sig, str) else '')
    # Altes, unsigniertes Format (v1): wird nicht mehr akzeptiert
    raise ValueError('unsigned highscore file')


def load_highscores():
    """Liest die Liste und verifiziert die Signatur. Bei Manipulation, korrupter
    Datei oder fehlender Datei wird eine leere Liste geliefert."""
    out = []
    try:
        raw, sig = _hs_read(_hs_file())
        if not hmac.compare_digest(sig, _hs_sign(raw)):
            return []
        for name, score in raw:
            name = str(name).strip().upper()[:HS_NAME_MAX] or 'PLAYER'
            if score > 0:
                out.append([name, score])
    except Exception:
        pass
    out.sort(key=lambda e: -e[1])
    return out[:HIGHSCORES_MAX]


def save_highscores(hs):
    try:
        _hs_write(_hs_file(), hs)
    except Exception:
        pass


def hs_qualifies(score, hs):
    if score <= 0:
        return False
    if len(hs) < HIGHSCORES_MAX:
        return True
    return score > hs[-1][1]


def _clean_name(name):
    name = (name or 'PLAYER').strip().upper()[:HS_NAME_MAX]
    if not name:
        name = 'PLAYER'
    return name


def add_highscore(hs, name, score):
    name = _clean_name(name)
    hs.append([name, score])
    hs.sort(key=lambda e: -e[1])
    for i, e in enumerate(hs):
        if e[0] == name and e[1] == score:
            return i
    return len(hs) - 1


def _init_joystick():
    global JOY
    try:
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            j = pygame.joystick.Joystick(0)
            j.init()
            JOY = j
    except Exception:
        JOY = None


def _joy_button(i):
    if JOY is None:
        return False
    try:
        return bool(JOY.get_button(i))
    except Exception:
        return False


def _joy_dir():
    if JOY is None:
        return (0, 0)
    try:
        ax = JOY.get_axis(0)
        ay = JOY.get_axis(1)
        fx = (1 if ax > JOY_DZ else -1 if ax < -JOY_DZ else 0)
        fy = (1 if ay > JOY_DZ else -1 if ay < -JOY_DZ else 0)
        if fx == 0:
            dleft = _joy_button(JOY_DPAD[2])
            dright = _joy_button(JOY_DPAD[3])
            if dleft and not dright:
                fx = -1
            elif dright and not dleft:
                fx = 1
        if fy == 0:
            dup = _joy_button(JOY_DPAD[0])
            ddn = _joy_button(JOY_DPAD[1])
            if dup and not ddn:
                fy = -1
            elif ddn and not dup:
                fy = 1
        try:
            hx, hy = JOY.get_hat(0)
            if fx == 0 and hx != 0:
                fx = int(hx)
            if fy == 0 and hy != 0:
                fy = -int(hy)
        except Exception:
            pass
        return (fx, fy)
    except Exception:
        return (0, 0)


def _hs_confirm(game):
    game.hs_rank = add_highscore(game.hiscores, game.hs_name, game.score)
    game.hs_popup = False
    game.hs_popup_t = 0.2
    save_highscores(game.hiscores)


def main():
    global SETTINGS
    try:
        pygame.mixer.pre_init(44100, 16, 2, 2048)
    except Exception:
        pass
    pygame.init()
    SETTINGS = Settings()
    _init_sfx()
    _init_joystick()
    mp = _resolve_music_path()
    try:
        pygame.mixer.music.load(mp)
        apply_volume()
        pygame.mixer.music.play(-1)
    except Exception:
        pass
    import time
    time.sleep(1.0)
    clock = pygame.time.Clock()
    canvas = apply_display()
    pygame.display.set_caption('BOMB!')
    frame = pygame.Surface((SCREEN_W, SCREEN_H))
    ui = SettingsUI(SETTINGS)
    game = Game()
    t = 0.0
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 1.0 / 30.0)
        t += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except Exception:
                    pass
                pygame.quit()
                sys.exit(0)
            if game.hs_popup:
                # Während der Namenseingabe gehört jedes Tastatur- und
                # Gamepad-Event dem Popup. Sonst würde z.B. "M" die
                # Einstellungen öffnen, während man den Namen tippt.
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_BACKSPACE:
                        game.hs_name = game.hs_name[:-1]
                    elif ev.key == pygame.K_RETURN:
                        _hs_confirm(game)
                    else:
                        c = ev.unicode
                        if len(c) == 1 and (c.isalnum() or c == ' '):
                            if len(game.hs_name) < HS_NAME_MAX:
                                game.hs_name += c
                elif JOY is not None and ev.type == pygame.JOYBUTTONDOWN and ev.button == JOY_BTN_A:
                    _hs_confirm(game)
                continue
            if ev.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
                if ui.handle_joy_event(ev):
                    continue
                if ui.handle_event(ev):
                    continue
            if ui.hiscores_reset:
                ui.hiscores_reset = False
                game.hiscores = load_highscores()
                game.hs_rank = None
            if ui.needs_display:
                ui.needs_display = False
                canvas = apply_display()
                pygame.display.set_caption('BOMB!')
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p and game.state in (STATE_PLAY, STATE_PAUSED):
                game.toggle_pause()
            elif JOY is not None and ev.type == pygame.JOYBUTTONDOWN and ev.button in JOY_BTN_PAUSE and game.state in (STATE_PLAY, STATE_PAUSED):
                game.toggle_pause()
        if game.state == STATE_OVER and not game.hs_popup and game.hs_popup_t <= 0:
            if _joy_button(JOY_BTN_A):
                game.new_game()
        if ui.open:
            ui.update(dt)
        else:
            game.update(dt)
            _sync_music(game.state)
        draw(frame, game, t)
        _draw_score_floating_texts(frame, game)
        if ui.open:
            ui.draw(frame)
        cw, ch = canvas.get_size()
        if (cw, ch) == (SCREEN_W, SCREEN_H):
            canvas.blit(frame, (0, 0))
        else:
            canvas.blit(pygame.transform.smoothscale(frame, (cw, ch)), (0, 0))
        pygame.display.flip()


if __name__ == '__main__':
    main()
