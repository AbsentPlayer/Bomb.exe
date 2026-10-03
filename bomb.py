import math
import json
import os
import random
import sys
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
ENEMY_INTERVAL = 1.0
MAX_ENEMIES = 8
LEVEL_TIME = 90.0

STATE_START = 0
STATE_PLAY = 1
STATE_PAUSED = 2
STATE_OVER = 3

HIGHSCORES_MAX = 10
HS_NAME_MAX = 8
JOY_DZ = 0.4
JOY_BTN_A = 0
JOY_BTN_B = 1
JOY_BTN_PAUSE = (8, 9)
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


def make_font(name, size, bold=False):
    f = pygame.font.SysFont(name, size)
    if bold:
        f.set_bold(True)
    return f


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

    def cell_open(self, grid, sx, sy):
        if not (0 <= sx < GRID_W and 0 <= sy < GRID_H):
            return False
        return grid[sy][sx] not in (BRICK, WALL)

    def update(self, grid, dt):
        self.prev_sx, self.prev_sy = self.sx, self.sy
        self.anim += dt
        self.invuln = max(0.0, self.invuln - dt)
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
        self.level = 1
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
        self.player = Player(*PLAYER_START)
        self.time = LEVEL_TIME
        self.spawn_t = ENEMY_INTERVAL
        self.shake = 0.0

    def max_enemies(self):
        return min(MAX_ENEMIES, 1 + self.level)

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

    def hurt_player(self):
        if self.player.invuln > 0:
            return
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
        sx, sy = int(round(p.x)), int(round(p.y))
        if any(b.sx == sx and b.sy == sy for b in self.bombs):
            return
        if self.grid[sy][sx] in (BRICK, WALL):
            return
        p.bombs_left -= 1
        self.bombs.append(Bomb(sx, sy, p.range))
        p.invuln = max(p.invuln, 0.6)

    def _check_enemy_collisions(self):
        psx, psy = self.player.sx, self.player.sy
        ppx, ppy = self.player.prev_sx, self.player.prev_sy
        for e in self.enemies:
            if (e.sx == psx and e.sy == psy) or \
               (e.prev_sx == psx and e.prev_sy == psy and e.sx == ppx and e.sy == ppy):
                self.hurt_player()

    def explode(self, cx, cy, radius):
        self.shake = max(self.shake, 1.0)
        play_sfx('explosion')
        self.effects.append(Effect(cx, cy, 'exp'))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                x, y = cx + dx, cy + dy
                if not (0 <= x < GRID_W and 0 <= y < GRID_H):
                    continue
                cell = self.grid[y][x]
                if cell == BRICK:
                    self.grid[y][x] = EMPTY
                    self.score += 10
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
                            self.score += 5
                            bx = MARGIN_L + x * TILE + TILE // 2
                            by = MARGIN_T + y * TILE + TILE // 2
                            self.particles.append(Particle(bx, by, random.uniform(-60, 60), random.uniform(-60, 60), 0, 120, PUP_IN, 5))
                    for e in list(self.enemies):
                        if e.sx == x and e.sy == y:
                            self.enemies.remove(e)
                            self.score += 50
                            ex = MARGIN_L + e.x * TILE + TILE // 2
                            ey = MARGIN_T + e.y * TILE + TILE // 2
                            self.particles.append(Particle(ex, ey, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, ENEMY, 6))
                            self.particles.append(Particle(ex, ey, random.uniform(-90, 90), random.uniform(-90, 90), 0, 120, EYE, 5))
                    if self.player.sx == x and self.player.sy == y and self.player.invuln <= 0:
                        self.hurt_player()

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
        if self.state == STATE_PLAY:
            self.shake = max(0.0, self.shake - dt * 4.0)
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
            self.handle_input()
            self.player.update(self.grid, dt)
            self._check_enemy_collisions()
            px, py = self.player.sx, self.player.sy
            for p in list(self.powerups):
                if p.sx == px and p.sy == py:
                    self.powerups.remove(p)
                    self.apply_powerup(p.kind)
            p = self.player
            if p.bombs_left <= 0 and p.no_damage_time >= 10.0:
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
    bob = math.sin(t * 6) * (1 if p.moving else 0)
    surf2 = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(surf2, (0, 0, 0, 60), (TILE - 15, TILE + 18, 30, 7))
    pygame.draw.rect(surf2, PFOOT, (TILE - 11, TILE + 7, 10, 9))
    pygame.draw.rect(surf2, PFOOT, (TILE + 1, TILE + 7, 10, 9))
    pygame.draw.rect(surf2, PBODY, (TILE - 12, TILE - 5, 24, 15))
    pygame.draw.circle(surf2, PBODY, (TILE, TILE - 11 + bob), 13)
    pygame.draw.arc(surf2, PHAT, pygame.Rect(TILE - 10, TILE - 19 + bob, 20, 20), 0, 3.14, 3)
    pygame.draw.circle(surf2, PHAT, (TILE, TILE - 16 + bob), 10)
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


def draw_hud(surf, game, ox, oy):
    h = MARGIN_T
    pygame.draw.rect(surf, HUD_BG, pygame.Rect(0, 0, SCREEN_W, h))
    f = make_font(None, 34)
    fs = make_font(None, 26)
    def txt(s, x, y, str, font, col):
        img = font.render(str, True, col)
        s.blit(img, (x, y))
    txt(surf, ox, 16, 'SCORE %d' % game.score, f, TEXT)
    txt(surf, ox + 340, 16, 'LEVEL %d' % game.level, f, HUD_ACC)
    txt(surf, ox + 640, 16, 'TIME %d' % int(max(0, game.time)), f, TEXT)
    txt(surf, ox + 920, 16, 'BOMBS', fs, TEXT_DIM)
    bomb_x = ox + 920
    for i in range(MAX_BOMBS):
        filled = i < game.player.bombs_left
        cx = bomb_x + 18 + i * 28
        pygame.draw.circle(surf, (210, 230, 250) if filled else (70, 72, 95), (cx, 60), 16 if filled else 7)
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
    surf.blit(pi, (SCREEN_W // 2 - pi.get_width() // 2, SCREEN_H - 80))


def draw_state(surf, game, t):
    if game.state == STATE_START:
        draw_start_screen(surf, game)
    elif game.state == STATE_PAUSED:
        surf2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(surf2, (0, 0, 0, 110), pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        f = make_font(None, 84)
        img = f.render('PAUSED', True, TEXT)
        surf.blit(img, (SCREEN_W // 2 - img.get_width() // 2, SCREEN_H // 2 - 20))
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
    draw_bombs(surf, game.bombs, ox, oy, t)
    draw_player(surf, game.player, ox, oy, t)
    for ef in game.effects:
        ef.draw(surf, ox, oy)
    for pt in game.particles:
        pt.draw(surf)
    draw_hud(surf, game, ox, oy)
    draw_state(surf, game, t)


SFX = {}


def play_sfx(name):
    s = SFX.get(name)
    if s is not None:
        try:
            s.play()
        except Exception:
            pass


def _init_sfx():
    try:
        import numpy as np
    except ImportError:
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

    try:
        SFX['explosion'] = pygame.mixer.Sound(buffer=make(0.55, explosion_fn))
        SFX['explosion'].set_volume(0.16)
        SFX['buzz'] = pygame.mixer.Sound(buffer=make(0.35, buzz_fn))
    except Exception:
        pass


def _resolve_music_path():
    p = os.path.join(_base_dir(), 'bomb.mp3')
    if os.path.exists(p):
        return p
    return None


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


def load_highscores():
    out = []
    try:
        with open(_hs_file(), 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        for e in data:
            name = str(e.get('name', '')).strip().upper()[:HS_NAME_MAX]
            try:
                score = int(e.get('score', 0))
            except (TypeError, ValueError):
                score = 0
            if score > 0:
                out.append([name or 'PLAYER', score])
    except Exception:
        pass
    out.sort(key=lambda e: -e[1])
    return out[:HIGHSCORES_MAX]


def save_highscores(hs):
    try:
        with open(_hs_file(), 'w', encoding='utf-8') as fh:
            json.dump([{'name': n, 'score': s} for n, s in hs], fh, ensure_ascii=False)
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
    try:
        pygame.mixer.pre_init(44100, 16, 2, 2048)
    except Exception:
        pass
    pygame.init()
    _init_sfx()
    _init_joystick()
    mp = _resolve_music_path()
    try:
        pygame.mixer.music.load(mp)
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play(-1)
    except Exception:
        pass
    import time
    time.sleep(1.0)
    clock = pygame.time.Clock()
    surf = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption('BOMB!')
    game = Game()
    t = 0.0
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 1.0 / 30.0)
        t += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p and game.state in (STATE_PLAY, STATE_PAUSED):
                game.toggle_pause()
            if JOY is not None and ev.type == pygame.JOYBUTTONDOWN and ev.button in JOY_BTN_PAUSE and game.state in (STATE_PLAY, STATE_PAUSED):
                game.toggle_pause()
            if game.hs_popup:
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
        if game.state == STATE_OVER and not game.hs_popup and game.hs_popup_t <= 0:
            if _joy_button(JOY_BTN_A):
                game.new_game()
        game.update(dt)
        _sync_music(game.state)
        draw(surf, game, t)
        pygame.display.flip()


if __name__ == '__main__':
    main()
