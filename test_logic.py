import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import pygame
pygame.init()
pygame.display.set_mode((2, 2))

import bomb


def setup():
    game = bomb.Game()
    game.state = bomb.STATE_PLAY
    return game


def test_grid_shape():
    g = bomb.generate_grid()
    assert len(g) == bomb.GRID_H
    for row in g:
        assert len(row) == bomb.GRID_W


def test_grid_borders_are_walls():
    g = bomb.generate_grid()
    for x in range(bomb.GRID_W):
        assert g[0][x] == bomb.WALL
        assert g[bomb.GRID_H - 1][x] == bomb.WALL
    for y in range(bomb.GRID_H):
        assert g[y][0] == bomb.WALL
        assert g[y][bomb.GRID_W - 1] == bomb.WALL


def test_spawn_area_clear():
    g = bomb.generate_grid()
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            x, y = bomb.PLAYER_START[0] + dx, bomb.PLAYER_START[1] + dy
            if 0 <= x < bomb.GRID_W and 0 <= y < bomb.GRID_H:
                assert g[y][x] == bomb.EMPTY


def test_grid_has_bricks():
    g = bomb.generate_grid()
    n = sum(row.count(bomb.BRICK) for row in g)
    assert n > 30


def test_bomb_explode_destroys_bricks():
    g = bomb.generate_grid()
    g[6][8] = bomb.BRICK
    g[6][9] = bomb.BRICK
    game = setup()
    game.grid = g
    before = sum(row.count(bomb.BRICK) for row in game.grid)
    game.explode(6, 8, 3)
    after = sum(row.count(bomb.BRICK) for row in game.grid)
    assert after < before


def test_bomb_explode_hurts_player():
    game = setup()
    game.player.sx, game.player.sy = 10, 6
    game.player.x, game.player.y = 10.0, 6.0
    game.player.invuln = 0.0
    game.grid[6][10] = bomb.EMPTY
    game.explode(11, 6, 3)
    assert game.player.lives < bomb.MAX_LIVES


def test_player_collision_wall():
    game = setup()
    g = game.grid
    p = game.player
    # push player toward the top wall (row 0); player must never reach y <= 0
    for _ in range(200):
        ny = p.y - 0.5
        if not bomb.collides(g, p.x, ny, 0.42):
            p.y = ny
    assert p.y > 0.0


def test_bfs_open_path():
    g = bomb.generate_grid()
    nxt = bomb.bfs_next(g, set(), 3, 6, 3, 4)
    assert nxt is not None


def test_bfs_avoids_bomb():
    g = bomb.generate_grid()
    g[6][4] = bomb.EMPTY
    g[6][5] = bomb.EMPTY
    nxt = bomb.bfs_next(g, {(6, 4)}, 3, 6, 5, 6)
    assert nxt is not None
    assert nxt != (6, 4)


def test_apply_powerup():
    game = setup()
    game.player.bombs_left = 1
    game.apply_powerup('bomb')
    assert game.player.bombs_left == 2
    game.player.range = 1
    game.apply_powerup('range')
    assert game.player.range == 2
    game.player.lives = 1
    game.apply_powerup('life')
    assert game.player.lives == 2
    game.apply_powerup('speed')
    assert game.player.speed > bomb.PLAYER_SPEED


def test_game_update_smoke():
    game = setup()
    for _ in range(120):
        game.update(1.0 / 60.0)
    assert isinstance(game.score, int)
    assert game.state == bomb.STATE_PLAY


def test_single_kill_no_star_no_life():
    game = setup()
    g = game.grid
    for x, y in ((8, 6), (8, 5), (8, 7)):
        g[y][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(8, 6)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = 2
    game.player.bombs_left = 2
    game.explode(8, 6, 1)
    assert len(game.enemies) == 0
    assert game.player.lives == 2
    assert game.player.bombs_left == 2
    assert len(game.stars) == 0


def test_doublekill_extra_bomb_and_star():
    game = setup()
    g = game.grid
    for x, y in ((7, 6), (8, 6), (9, 6), (8, 5), (8, 7)):
        g[y][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(8, 6), bomb.Enemy(9, 6)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES - 1
    game.player.bombs_left = bomb.MAX_BOMBS - 1
    game.explode(8, 6, 2)
    assert len(game.enemies) == 0
    assert game.player.lives == bomb.MAX_LIVES - 1
    assert game.player.bombs_left == bomb.MAX_BOMBS
    assert game.stars[0].label == 'Double-Kill'


def test_multikill_extra_life_and_star():
    game = setup()
    g = game.grid
    for x, y in ((6, 6), (7, 6), (8, 6), (9, 6), (10, 6)):
        g[y][x] = bomb.EMPTY
    for x in range(6, 11):
        game.enemies.append(bomb.Enemy(x, 6))
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES - 1
    game.player.bombs_left = 2
    game.explode(8, 6, 3)
    assert len(game.enemies) == 0
    assert game.player.lives == bomb.MAX_LIVES
    assert game.player.bombs_left == 2
    assert game.stars[0].label == 'Multi-Kill'


def test_three_kills_doublekill():
    game = setup()
    g = game.grid
    for x, y in ((7, 6), (8, 6), (9, 6), (10, 6), (8, 5), (8, 7)):
        g[y][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(8, 6), bomb.Enemy(9, 6), bomb.Enemy(10, 6)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES
    game.player.bombs_left = bomb.MAX_BOMBS
    game.explode(8, 6, 3)
    assert len(game.enemies) == 0
    assert game.player.lives == bomb.MAX_LIVES
    assert game.player.bombs_left == bomb.MAX_BOMBS
    assert len(game.stars) == 1
    assert game.stars[0].label == 'Double-Kill'
    assert len(game.snipers) == 0


def test_seven_kills_multikill_no_sniper():
    game = setup()
    g = game.grid
    for x in range(3, 12):
        g[6][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(x, 6) for x in range(4, 11)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES - 1
    game.explode(7, 6, 4)
    assert len(game.enemies) == 0
    assert game.player.lives == bomb.MAX_LIVES
    assert len(game.stars) == 1
    assert game.stars[0].label == 'Multi-Kill'
    assert len(game.snipers) == 0


def test_multikill_capped():
    game = setup()
    g = game.grid
    for x in (4, 6, 8):
        g[6][x] = bomb.EMPTY
    for x in range(4, 9):
        game.enemies.append(bomb.Enemy(x, 6))
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES
    game.explode(6, 6, 3)
    assert len(game.enemies) == 0
    assert game.player.lives == bomb.MAX_LIVES
    assert game.stars[0].label == 'Multi-Kill'


def _sniper_test_game():
    game = setup()
    g = game.grid
    for x in range(3, 16):
        g[6][x] = bomb.EMPTY
    return game


def test_sniper_shoots_across_row():
    game = _sniper_test_game()
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 6
    game.player.x, game.player.y = 12.0, 6.0
    sn.cooldown = 0.0
    sn.aim_t = 0.0
    life_before = game.player.lives
    sn.update(1.0 / 60.0, game)
    assert game.player.lives < life_before
    assert len(game.shots) == 1
    assert sn.cooldown > 0


def test_sniper_no_shoot_in_cover():
    game = _sniper_test_game()
    g = game.grid
    g[6][13] = bomb.BRICK
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 6
    game.player.x, game.player.y = 12.0, 6.0
    sn.cooldown = 0.0
    sn.aim_t = 0.0
    life_before = game.player.lives
    sn.update(1.0 / 60.0, game)
    assert game.player.lives == life_before
    assert len(game.shots) == 0
    assert sn.cooldown == 0.0


def test_sniper_no_shoot_blocked_los():
    game = _sniper_test_game()
    g = game.grid
    g[6][8] = bomb.BRICK
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 6
    game.player.x, game.player.y = 12.0, 6.0
    sn.cooldown = 0.0
    sn.aim_t = 0.0
    life_before = game.player.lives
    sn.update(1.0 / 60.0, game)
    assert game.player.lives == life_before
    assert len(game.shots) == 0


def test_sniper_no_shoot_wrong_line():
    game = _sniper_test_game()
    g = game.grid
    for x in range(3, 16):
        g[12][x] = bomb.EMPTY
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 12
    game.player.x, game.player.y = 12.0, 12.0
    sn.cooldown = 0.0
    sn.aim_t = 0.0
    life_before = game.player.lives
    sn.update(1.0 / 60.0, game)
    assert game.player.lives == life_before
    assert len(game.shots) == 0


def test_sniper_reload():
    game = _sniper_test_game()
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 6
    game.player.x, game.player.y = 12.0, 6.0
    sn.cooldown = 0.0
    sn.aim_t = 0.0
    life_before = game.player.lives
    sn.update(1.0 / 60.0, game)
    assert game.player.lives < life_before
    for _ in range(4 * 60):
        sn.update(1.0 / 60.0, game)
    assert game.player.lives == life_before - 1
    game.player.invuln = 0.0
    for _ in range(2 * 60):
        sn.update(1.0 / 60.0, game)
    assert game.player.lives == life_before - 2


def _five_row(g, row):
    for x in range(4, 9):
        g[row][x] = bomb.EMPTY
    return [bomb.Enemy(x, row) for x in range(4, 9)]


def _quiet(game, invincible=True):
    """Deterministische Ausgangslage fuer zeitbasierte Tests.

    `Game.update` wird in den Free-Bomb-Tests mit einem einzelnen sehr grossen
    dt aufgerufen. Ohne diese Absicherung spawnen bzw. erreichen die Gegner
    den Spieler zufaellig und setzen `no_damage_time` zurueck - der Test
    scheitert dann je nach generiertem Level.
    """
    for y in range(bomb.GRID_H):
        for x in range(bomb.GRID_W):
            game.grid[y][x] = bomb.EMPTY
    game.enemies = []
    game.spawn_t = 1e9
    if invincible:
        game.player.invuln = 1e9
    return game


def test_sniper_spawns_after_3_multikills():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    sn = game.snipers[0]
    assert game.grid[sn.sy][sn.sx] == bomb.EMPTY
    assert (sn.sx, sn.sy) != (15, 12)
    assert any(isinstance(st, bomb.CrosshairEffect) and st.label == 'Sniper WARNING!!!' for st in game.stars)
    assert any(getattr(st, 'label', None) == 'Multi-Kill' for st in game.stars)


def test_sniper_respawns_unlimited_but_never_two_at_once():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12, 6, 10, 1, 4, 7, 9, 11, 13, 2, 5):
        for x in range(4, 9):
            g[row][x] = bomb.EMPTY
    rows = (3, 8, 6, 10, 1, 4, 7, 9, 11, 13, 2, 5, 12)
    i = 0

    def multi_kill():
        nonlocal i
        row = rows[i % len(rows)]
        i += 1
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)

    for _ in range(6):
        for _ in range(3):
            multi_kill()
            assert len(game.snipers) <= 1
        assert len(game.snipers) == 1
        sn = game.snipers[0]
        # weitere Multi-Kills waehrend der Sniper lebt: kein zweiter Sniper
        for _ in range(2):
            multi_kill()
            assert len(game.snipers) == 1
        # Sniper wegschiessen
        game.grid[sn.sy][sn.sx] = bomb.EMPTY
        game.explode(sn.sx, sn.sy, 0)
        assert len(game.snipers) == 0
        assert bomb._SNIPERWARN_CH is None


def test_sniper_warning_stops_when_sniper_dies():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    sn = game.snipers[0]
    game.grid[sn.sy][sn.sx] = bomb.EMPTY
    game.explode(sn.sx, sn.sy, 0)
    assert len(game.snipers) == 0
    assert bomb._SNIPERWARN_CH is None


def test_sniper_warning_stops_on_level_reset():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    game.reset_level()
    assert len(game.snipers) == 0
    assert bomb._SNIPERWARN_CH is None


def test_sniper_warning_stops_even_without_explosion():
    """Der Watchdog muss den Ton auch stoppen, wenn der Sniper auf andere Weise
    verschwindet - nicht nur bei der Bombe."""
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    # Sniper "verschwindet" ohne Explosion
    game.snipers.clear()
    assert bomb.sniper_warning_playing() is False
    game.update(1.0 / 60.0)
    assert bomb._SNIPERWARN_CH is None


def test_sniper_warning_stops_on_game_over():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    game.player.invuln = 0.0
    game.player.lives = 1
    game.hurt_player()
    assert game.state == bomb.STATE_OVER
    assert bomb._SNIPERWARN_CH is None


def test_score_mult_2x_while_sniper_alive_5x_after_kill_until_damage():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    assert game.score_mult == 1
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    # Sniper lebt -> 2x
    assert game.score_mult == bomb.SNIPER_MULT
    sn = game.snipers[0]
    game.grid[sn.sy][sn.sx] = bomb.EMPTY
    # Zufallsfundstellen auf dem Sniperfeld entfernen, sonst waere die
    # Summe nicht deterministisch
    game.enemies = [e for e in game.enemies if (e.sx, e.sy) != (sn.sx, sn.sy)]
    game.powerups = [p for p in game.powerups if (p.sx, p.sy) != (sn.sx, sn.sy)]
    before = game.score
    game.explode(sn.sx, sn.sy, 0)
    # eigener Sniper-Score noch mit 2x ...
    assert game.score == before + 100 * bomb.SNIPER_MULT
    # ... danach 5x fuer alle kommenden Scores
    assert game.mult == bomb.SNIPER_KILL_MULT
    assert game.score_mult == bomb.SNIPER_KILL_MULT
    for y in range(bomb.GRID_H):
        for x in range(bomb.GRID_W):
            g[y][x] = bomb.EMPTY
    for x in range(4, 9):
        g[3][x] = bomb.BRICK
    game.enemies = []
    game.powerups = []
    game.score = 0
    game.explode(6, 3, 2)
    assert game.score == 5 * 10 * bomb.SNIPER_KILL_MULT
    game.score = 0
    game.enemies = _five_row(g, 8)
    game.explode(6, 8, 2)
    assert game.score == 5 * 50 * bomb.SNIPER_KILL_MULT
    # Der vierte Multi-Kill addiert weiter (Streak resettet nur bei Schaden)
    # und spawnt deshalb sofort den naechsten Sniper.
    assert game.multi_kill_streak == 4
    assert len(game.snipers) == 1
    game.player.invuln = 0.0
    game.hurt_player()
    assert game.mult == 1
    assert game.multi_kill_streak == 0
    assert game.double_kill_streak == 0
    # Der Sniper lebt noch, deshalb 2x statt 1x
    assert game.score_mult == bomb.SNIPER_MULT
    game.snipers = []
    assert game.score_mult == 1


def test_score_mult_returns_to_2x_after_damage_while_sniper_lives():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    sn = game.snipers[0]
    game.grid[sn.sy][sn.sx] = bomb.EMPTY
    game.explode(sn.sx, sn.sy, 0)
    assert game.score_mult == bomb.SNIPER_KILL_MULT
    game.player.invuln = 0.0
    game.hurt_player()
    assert game.mult == 1
    assert game.score_mult == 1


def test_score_mult_5x_wins_over_new_sniper():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    sn = game.snipers[0]
    game.grid[sn.sy][sn.sx] = bomb.EMPTY
    game.explode(sn.sx, sn.sy, 0)
    assert game.score_mult == bomb.SNIPER_KILL_MULT
    game.mult = bomb.SNIPER_KILL_MULT
    game.snipers.append(bomb.Sniper(1, 1))
    assert game.score_mult == bomb.SNIPER_KILL_MULT * bomb.SNIPER_MULT
    game.mult = 1
    assert game.score_mult == bomb.SNIPER_MULT


def test_sniper_streak_reset_by_damage():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        for x in range(4, 9):
            g[row][x] = bomb.EMPTY
    game.enemies = _five_row(g, 3)
    game.explode(6, 3, 2)
    game.enemies = _five_row(g, 8)
    game.explode(6, 8, 2)
    assert game.multi_kill_streak == 2
    game.player.invuln = 0.0
    game.hurt_player()
    assert game.multi_kill_streak == 0
    game.enemies = _five_row(g, 12)
    game.explode(6, 12, 2)
    assert len(game.snipers) == 0
    assert game.multi_kill_streak == 1


def test_sniper_streak_survives_non_multikill_bomb():
    """Streaks resetten ausschliesslich bei Schaden - eine Bombe mit nur einem
    Kill darf den Multi-Kill-Streak also nicht loeschen."""
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in range(4, 9):
        g[3][x] = bomb.EMPTY
    g[6][6] = bomb.EMPTY
    for x in range(4, 9):
        g[8][x] = bomb.EMPTY
    for x in range(4, 9):
        g[12][x] = bomb.EMPTY
    game.enemies = _five_row(g, 3)
    game.explode(6, 3, 2)
    assert game.multi_kill_streak == 1
    game.enemies = [bomb.Enemy(6, 6)]
    game.explode(6, 6, 1)
    # Ein Non-Multi-Kill addiert nichts, setzt aber nichts zurueck
    assert game.multi_kill_streak == 1
    game.enemies = _five_row(g, 8)
    game.explode(6, 8, 2)
    assert game.multi_kill_streak == 2
    game.enemies = _five_row(g, 12)
    game.explode(6, 12, 2)
    assert game.multi_kill_streak == 3
    assert len(game.snipers) == 1
    # Der Sniper-Kill zaehlt nicht als Multi-Kill, der Streak bleibt bei 3
    sn = game.snipers[0]
    game.explode(sn.sx, sn.sy, 0)
    assert len(game.snipers) == 0
    assert game.multi_kill_streak == 3


def test_sniper_streak_survives_doublekill():
    """Auch ein Double-Kill loescht den Sniper-Streak nicht mehr."""
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in range(4, 9):
        g[1][x] = bomb.EMPTY
    for x in (5, 6, 7):
        g[8][x] = bomb.EMPTY
    for x in range(4, 9):
        g[12][x] = bomb.EMPTY
    game.enemies = _five_row(g, 1)
    game.explode(6, 1, 2)
    assert game.multi_kill_streak == 1
    game.enemies = [bomb.Enemy(5, 8), bomb.Enemy(7, 8)]
    game.explode(6, 8, 1)
    assert game.stars[-1].label == 'Double-Kill'
    assert game.multi_kill_streak == 1
    game.enemies = _five_row(g, 12)
    game.explode(6, 12, 2)
    assert game.multi_kill_streak == 2
    assert len(game.snipers) == 0


def test_sniper_only_one():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for row in (3, 8, 12):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    sn0 = game.snipers[0]
    sn0.sx, sn0.sy, sn0.x, sn0.y = 18, 1, 18.0, 1.0
    assert game.grid[1][18] == bomb.EMPTY
    for row in (9, 5, 1):
        game.enemies = _five_row(g, row)
        game.explode(6, row, 2)
    assert len(game.snipers) == 1
    assert game.snipers[0] is sn0


def test_sniper_dies_to_bomb():
    game = setup()
    g = game.grid
    for x, y in ((3, 6), (4, 6), (5, 6), (4, 5), (4, 7)):
        g[y][x] = bomb.EMPTY
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.explode(4, 6, 1)
    assert len(game.snipers) == 0
    assert game.player.lives == bomb.MAX_LIVES


def test_sniper_crosshair():
    st = bomb.CrosshairEffect(bomb.SCREEN_W // 2, bomb.SCREEN_H // 2)
    assert st.label == 'Sniper WARNING!!!'
    colors = set()
    for _ in range(60):
        st.update(1.0 / 6.0)
        c = st.color()
        colors.add(c)
    assert len(colors) > 1
    for c in colors:
        assert c[0] == 255
        assert c[1] == c[2]
        assert 0 <= c[1] <= 255
def test_star_label_lives_with_star():
    st = bomb.StarEffect(bomb.MARGIN_L + 5 * bomb.TILE, bomb.MARGIN_T + 5 * bomb.TILE, 'Multi-Kill')
    frames = 0
    while not st.dead() and frames < 30000:
        st.update(1.0 / 60.0)
        frames += 1
    assert st.dead()
    assert st.label == 'Multi-Kill'


def test_star_flicker_color():
    st = bomb.StarEffect(bomb.MARGIN_L + 5 * bomb.TILE, bomb.MARGIN_T + 5 * bomb.TILE)
    colors = set()
    for _ in range(60):
        st.update(1.0 / 6.0)
        c = st.color()
        colors.add(c)
        assert all(0 <= ch <= 255 for ch in c)
    assert len(colors) > 1
    for c in colors:
        assert 19 <= c[1] <= 222
        assert 33 <= c[2] <= 240


def test_star_removed_in_update():
    game = setup()
    g = game.grid
    for x, y in ((7, 6), (8, 6), (9, 6), (8, 5), (8, 7)):
        g[y][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(8, 6), bomb.Enemy(9, 6)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.invuln = 1e9
    game.explode(8, 6, 2)
    assert len(game.stars) == 1
    for _ in range(2000):
        game.update(1.0 / 60.0)
    assert game.stars == []


def test_star_effect_grows_offscreen():
    st = bomb.StarEffect(bomb.MARGIN_L + 5 * bomb.TILE, bomb.MARGIN_T + 5 * bomb.TILE)
    assert not st.dead()
    frames = 0
    while not st.dead() and frames < 30000:
        st.update(1.0 / 60.0)
        frames += 1
    assert st.dead()
    assert frames < 30000


def test_star_effect_draw():
    surf = pygame.display.set_mode((bomb.SCREEN_W, bomb.SCREEN_H))
    st = bomb.StarEffect(bomb.SCREEN_W // 2, bomb.SCREEN_H // 2, 'Double-Kill')
    st.update(1.0)
    st.draw(surf)


def test_sniper_moves_toward_player():
    game = setup()
    g = game.grid
    for x in range(3, 16):
        g[6][x] = bomb.EMPTY
    for x in range(3, 16):
        g[12][x] = bomb.EMPTY
    sn = bomb.Sniper(4, 6)
    game.snipers = [sn]
    game.player.sx, game.player.sy = 12, 12
    game.player.x, game.player.y = 12.0, 12.0
    start = (sn.sx, sn.sy)
    moved = False
    for _ in range(20000):
        sn.update(1.0 / 60.0, game)
        if (sn.sx, sn.sy) != start:
            moved = True
            break
        assert game.grid[sn.sy][sn.sx] == bomb.EMPTY
    assert moved
    assert game.grid[sn.sy][sn.sx] == bomb.EMPTY


def test_countdown_runs_without_sniper():
    game = setup()
    assert not game.sniper_active
    t0 = game.time
    game.update(1.0)
    assert game.time < t0


def test_countdown_stops_while_sniper_active():
    game = setup()
    game.snipers.append(bomb.Sniper(18, 6))
    assert game.sniper_active
    t0 = game.time
    for _ in range(30):
        game.update(1.0 / 60.0)
    assert game.time == t0
    assert game.level == 1


def test_countdown_resumes_after_sniper_dies():
    game = setup()
    sn = bomb.Sniper(18, 6)
    game.snipers.append(sn)
    t0 = game.time
    game.update(0.5)
    assert game.time == t0
    game.snipers.remove(sn)
    assert not game.sniper_active
    game.update(0.5)
    assert game.time < t0


def test_free_bomb_after_10s_without_sniper():
    game = _quiet(setup())
    assert not game.sniper_active
    assert bomb.FREE_BOMB_TIME == 10.0
    assert bomb.FREE_BOMB_TIME_SNIPER == 7.0
    game.player.bombs_left = 0
    game.player.no_damage_time = 0.0
    game.update(bomb.FREE_BOMB_TIME - 0.5)
    assert game.player.bombs_left == 0, 'Bombe kam zu frueh'
    game.update(0.6)
    assert game.player.bombs_left == 1
    assert game.player.no_damage_time == 0.0


def test_free_bomb_after_7s_while_sniper_alive():
    """Der Sniper friert den Levelcountdown ein, nicht den Bombennachschuss."""
    game = _quiet(setup())
    game.snipers.append(bomb.Sniper(18, 6))
    game.player.bombs_left = 0
    game.player.no_damage_time = 0.0
    game.update(bomb.FREE_BOMB_TIME_SNIPER - 0.5)
    assert game.player.bombs_left == 0, 'Bombe kam vor 7s'
    game.update(0.6)
    assert game.player.bombs_left == 1
    assert game.player.no_damage_time == 0.0


def test_free_bomb_back_to_10s_after_sniper_dies():
    game = _quiet(setup())
    sn = bomb.Sniper(18, 6)
    game.snipers.append(sn)
    game.player.bombs_left = 0
    game.player.no_damage_time = 0.0
    game.update(bomb.FREE_BOMB_TIME_SNIPER - 0.5)
    game.update(0.6)
    assert game.player.bombs_left == 1
    # zweite Runde ohne Sniper: wieder 10 s
    game.player.bombs_left = 0
    game.player.no_damage_time = 0.0
    game.snipers.remove(sn)
    game.update(bomb.FREE_BOMB_TIME - 0.5)
    assert game.player.bombs_left == 0, 'Bombe kam nach dem Tod des Sniper zu frueh'
    game.update(0.6)
    assert game.player.bombs_left == 1


def test_free_bomb_needs_no_bombs_left():
    """Bei vollem Bombenvorrat wird der Timer nicht verbraucht."""
    game = _quiet(setup())
    game.snipers.append(bomb.Sniper(18, 6))
    game.player.bombs_left = bomb.MAX_BOMBS
    game.player.no_damage_time = 0.0
    game.update(bomb.FREE_BOMB_TIME_SNIPER + 1.0)
    assert game.player.bombs_left == bomb.MAX_BOMBS
    assert game.player.no_damage_time > 0.0


def test_free_bomb_counter_resets_on_damage():
    game = _quiet(setup(), invincible=False)
    game.snipers.append(bomb.Sniper(18, 6))
    game.player.bombs_left = 0
    game.player.no_damage_time = bomb.FREE_BOMB_TIME_SNIPER - 0.2
    game.player.invuln = 0.0
    game.hurt_player()
    assert game.player.no_damage_time == 0.0
    game.player.bombs_left = 0
    game.update(bomb.FREE_BOMB_TIME_SNIPER - 0.5)
    assert game.player.bombs_left == 0


def test_sniper_active_false_when_empty():
    game = setup()
    assert game.sniper_active is False
    game.snipers.append(bomb.Sniper(4, 4))
    assert game.sniper_active is True


def test_bomb_cooldown_blocks_second_bomb():
    game = setup()
    game.player.bombs_left = bomb.MAX_BOMBS
    game.try_place_bomb()
    assert len(game.bombs) == 1
    assert game.player.bombs_left == bomb.MAX_BOMBS - 1
    assert game.player.bomb_cd == bomb.BOMB_COOLDOWN
    # Zeit ist mit 0 simuliert -> zweite Bombe wird abgewiesen
    game.try_place_bomb()
    assert len(game.bombs) == 1
    assert game.player.bombs_left == bomb.MAX_BOMBS - 1


def test_bomb_cooldown_does_not_consume_extra_bomb_slot():
    """Ein blockierter Klick darf keinen zweiten Slot verbrauchen, sonst wuerde
    der Cooldown bei Rapid-Klicks Bomben vernichten."""
    game = setup()
    game.player.bombs_left = 1
    game.try_place_bomb()
    assert game.player.bombs_left == 0
    game.player.bombs_left = 1
    game.try_place_bomb()
    assert len(game.bombs) == 1
    assert game.player.bombs_left == 1


def test_bomb_cooldown_expires_after_half_second():
    game = setup()
    game.player.bombs_left = bomb.MAX_BOMBS
    game.try_place_bomb()
    assert game.player.bomb_cd > 0.0
    # 0.49 s reichen noch nicht ...
    game.player.update(game.grid, bomb.BOMB_COOLDOWN - 0.01)
    assert game.player.bomb_cd > 0.0
    game.try_place_bomb()
    assert len(game.bombs) == 1
    # ... 0.51 s schon
    game.player.update(game.grid, 0.02)
    assert game.player.bomb_cd == 0.0
    game.try_place_bomb()
    assert len(game.bombs) == 2


def test_bomb_cooldown_ticks_down_and_clamps_at_zero():
    game = setup()
    game.player.bomb_cd = 0.3
    game.player.update(game.grid, 1.0)
    assert game.player.bomb_cd == 0.0
    game.player.update(game.grid, 5.0)
    assert game.player.bomb_cd == 0.0


def test_bomb_cooldown_resets_on_new_level():
    game = setup()
    game.player.bomb_cd = bomb.BOMB_COOLDOWN
    game.reset_level()
    assert game.player.bomb_cd == 0.0
    game.try_place_bomb()
    assert len(game.bombs) == 1


def test_double_kill_streak_increments_on_doublekill():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in (5, 6, 7):
        g[8][x] = bomb.EMPTY
    assert game.double_kill_streak == 0
    game.enemies = [bomb.Enemy(5, 8), bomb.Enemy(7, 8)]
    game.explode(6, 8, 1)
    assert game.double_kill_streak == 1
    # Ein Multi-Kill zaehlt ebenfalls
    game.enemies = _five_row(g, 3)
    game.explode(6, 3, 2)
    assert game.double_kill_streak == 2


def test_double_kill_streak_mixes_double_and_multikills_arbitrarily():
    """Beliebige Reihenfolge: 3 Double-Kills + 2 Multi-Kills = Streak 5."""
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0

    def double(row):
        for x in (5, 6, 7):
            g[row][x] = bomb.EMPTY
        return [bomb.Enemy(5, row), bomb.Enemy(7, row)]

    game.enemies = _five_row(g, 1)
    game.explode(6, 1, 2)
    game.enemies = double(4)
    game.explode(6, 4, 1)
    game.enemies = double(7)
    game.explode(6, 7, 1)
    assert game.double_kill_streak == 3
    game.enemies = _five_row(g, 10)
    game.explode(6, 10, 2)
    game.enemies = double(13)
    game.explode(6, 13, 1)
    assert game.double_kill_streak == 5


def test_double_kill_streak_grants_x2_at_five_and_x5_at_ten():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0

    def dbl(row):
        for x in (5, 6, 7):
            g[row][x] = bomb.EMPTY
        return [bomb.Enemy(5, row), bomb.Enemy(7, row)]

    def five(row):
        for x in range(4, 9):
            g[row][x] = bomb.EMPTY
        return [bomb.Enemy(x, row) for x in range(4, 9)]

    def feed(maker):
        game.enemies = maker(1)
        game.explode(6, 1, 2)

    assert game.score_mult == 1
    for i in range(4):
        feed(five if i % 2 == 0 else dbl)
    assert game.double_kill_streak == 4
    assert game.score_mult == 1
    feed(dbl)
    assert game.double_kill_streak == bomb.DK_STREAK_X2
    assert game.score_mult == bomb.SNIPER_MULT
    for _ in range(bomb.DK_STREAK_X5 - bomb.DK_STREAK_X2 - 1):
        feed(dbl)
    assert game.double_kill_streak == bomb.DK_STREAK_X5 - 1
    assert game.score_mult == bomb.SNIPER_MULT
    feed(dbl)
    assert game.double_kill_streak == bomb.DK_STREAK_X5
    # Neue Logik: 10er-Streak -> x4 (2^(10//5)=4), ohne Sniper-Kill-Flag bleibt es 4
    assert game.score_mult == 4


def test_double_kill_streak_survives_single_kill_bomb():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in range(4, 9):
        g[3][x] = bomb.EMPTY
    g[6][6] = bomb.EMPTY
    for x in (5, 6, 7):
        g[8][x] = bomb.EMPTY
    game.enemies = _five_row(g, 3)
    game.explode(6, 3, 2)
    game.enemies = [bomb.Enemy(5, 8), bomb.Enemy(7, 8)]
    game.explode(6, 8, 1)
    assert game.double_kill_streak == 2
    # Ein Single-Kill addiert nichts, setzt aber nichts zurueck
    game.enemies = [bomb.Enemy(6, 6)]
    game.explode(6, 6, 1)
    assert game.double_kill_streak == 2


def test_double_kill_streak_resets_on_damage():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in (5, 6, 7):
        g[3][x] = bomb.EMPTY
    for _ in range(bomb.DK_STREAK_X5):
        game.enemies = [bomb.Enemy(5, 3), bomb.Enemy(7, 3)]
        game.explode(6, 3, 1)
    assert game.double_kill_streak == bomb.DK_STREAK_X5
    assert game.score_mult == 4
    game.player.invuln = 0.0
    game.hurt_player()
    assert game.double_kill_streak == 0
    assert game.score_mult == 1


def test_double_kill_streak_survives_level_change():
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in (5, 6, 7):
        g[8][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(5, 8), bomb.Enemy(7, 8)]
    game.explode(6, 8, 1)
    assert game.double_kill_streak == 1
    game.reset_level()
    # Kein Schaden genommen -> Streak und Bonus laufen weiter
    assert game.double_kill_streak == 1
    assert game.score_mult == 1
    game.new_game()
    assert game.double_kill_streak == 0
    assert game.multi_kill_streak == 0


def test_sniper_kill_does_not_feed_double_kill_streak():
    """Ein Sniper ist kein Feind im Kill-Zaehler - er faehrt den Streak nicht hoch."""
    game = setup()
    g = game.grid
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    for x in range(4, 9):
        g[1][x] = bomb.EMPTY
    game.enemies = _five_row(g, 1)
    game.explode(6, 1, 2)
    assert game.multi_kill_streak == 1
    assert game.double_kill_streak == 1
    game.grid[4][4] = bomb.EMPTY
    game.snipers.append(bomb.Sniper(4, 4))
    game.explode(4, 4, 0)
    assert game.double_kill_streak == 1
    assert len(game.snipers) == 0



def test_megakill_at_single_bomb_ten_kills_sets_invuln_and_star():
    game = setup()
    for x in range(5, 16):
        game.grid[11][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(x, 11) for x in range(6, 16)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES
    game.explode(10, 11, 5)
    assert len(game.enemies) == 0
    assert game.player.mega == bomb.MEGA_INVULN_TIME
    assert game.player.invuln == bomb.MEGA_INVULN_TIME
    assert game.stars[-1].label == 'Mega-Kill'


def test_megakill_not_at_single_bomb_nine_kills():
    game = setup()
    for x in range(5, 16):
        game.grid[11][x] = bomb.EMPTY
    game.enemies = [bomb.Enemy(x, 11) for x in range(6, 15)]
    game.player.sx, game.player.sy = 15, 12
    game.player.x, game.player.y = 15.0, 12.0
    game.player.lives = bomb.MAX_LIVES
    game.explode(10, 11, 5)
    assert game.player.mega == 0.0
    assert game.player.invuln == 0.0
    assert 'Mega-Kill' not in [s.label for s in game.stars]


def test_megakill_star_color_cycles():
    seen = set()
    for i in range(8):
        seen.add(bomb.mega_color(i * 0.125))
    assert len(seen) == len(bomb.MEGA_COLORS)


def test_megakill_star_draws():
    game = setup()
    game.stars.append(bomb.StarEffect(200.0, 200.0, 'Mega-Kill', bomb.mega_color))
    surf = pygame.Surface((bomb.SCREEN_W, bomb.SCREEN_H))
    bomb.draw(surf, game, 0.5)


def test_score_text_on_explosion_with_gain():
    game = setup()
    g = game.grid
    g[6][8] = bomb.BRICK
    game.player.sx, game.player.sy = 15, 12
    game.explode(6, 8, 3)
    assert len(game.score_floating_texts) == 1
    ft = game.score_floating_texts[0]
    assert ft['text'] == str(game.score)
    assert ft['age'] == 0.0


def test_score_text_none_on_no_score_gain():
    game = setup()
    game.grid[10][10] = bomb.WALL
    game.explode(10, 10, 1)
    assert len(game.score_floating_texts) == 0


def test_score_text_ages_out_in_update():
    game = setup()
    g = game.grid
    g[6][8] = bomb.BRICK
    game.explode(6, 8, 3)
    assert len(game.score_floating_texts) == 1
    for _ in range(int(bomb.FT_MAX_AGE * 60) + 1):
        game.update(1.0 / 60.0)
    assert len(game.score_floating_texts) == 0


def test_score_text_draw():
    game = setup()
    g = game.grid
    g[6][8] = bomb.BRICK
    game.explode(6, 8, 3)
    surf = pygame.Surface((bomb.SCREEN_W, bomb.SCREEN_H))
    bomb._draw_score_floating_texts(surf, game)

def main():
    tests = [
        test_grid_shape,
        test_grid_borders_are_walls,
        test_spawn_area_clear,
        test_grid_has_bricks,
        test_bomb_explode_destroys_bricks,
        test_bomb_explode_hurts_player,
        test_player_collision_wall,
        test_bfs_open_path,
        test_bfs_avoids_bomb,
        test_apply_powerup,
        test_game_update_smoke,
        test_single_kill_no_star_no_life,
        test_doublekill_extra_bomb_and_star,
        test_multikill_extra_life_and_star,
        test_multikill_capped,
        test_three_kills_doublekill,
        test_seven_kills_multikill_no_sniper,
        test_sniper_shoots_across_row,
        test_sniper_no_shoot_in_cover,
        test_sniper_no_shoot_blocked_los,
        test_sniper_no_shoot_wrong_line,
        test_sniper_reload,
        test_sniper_spawns_after_3_multikills,
        test_sniper_respawns_unlimited_but_never_two_at_once,
        test_sniper_warning_stops_when_sniper_dies,
        test_sniper_warning_stops_on_level_reset,
        test_sniper_warning_stops_even_without_explosion,
        test_sniper_warning_stops_on_game_over,
        test_score_mult_2x_while_sniper_alive_5x_after_kill_until_damage,
        test_score_mult_returns_to_2x_after_damage_while_sniper_lives,
        test_score_mult_5x_wins_over_new_sniper,
        test_sniper_streak_reset_by_damage,
        test_sniper_streak_survives_non_multikill_bomb,
        test_sniper_streak_survives_doublekill,
        test_sniper_only_one,
        test_sniper_dies_to_bomb,
        test_sniper_crosshair,
        test_star_label_lives_with_star,
        test_star_flicker_color,
        test_star_removed_in_update,
        test_sniper_moves_toward_player,
        test_star_effect_grows_offscreen,
        test_star_effect_draw,
        test_countdown_runs_without_sniper,
        test_countdown_stops_while_sniper_active,
        test_countdown_resumes_after_sniper_dies,
        test_free_bomb_after_10s_without_sniper,
        test_free_bomb_after_7s_while_sniper_alive,
        test_free_bomb_back_to_10s_after_sniper_dies,
        test_free_bomb_needs_no_bombs_left,
        test_free_bomb_counter_resets_on_damage,
        test_sniper_active_false_when_empty,
        test_bomb_cooldown_blocks_second_bomb,
        test_bomb_cooldown_does_not_consume_extra_bomb_slot,
        test_bomb_cooldown_expires_after_half_second,
        test_bomb_cooldown_ticks_down_and_clamps_at_zero,
        test_bomb_cooldown_resets_on_new_level,
        test_double_kill_streak_increments_on_doublekill,
        test_double_kill_streak_mixes_double_and_multikills_arbitrarily,
        test_double_kill_streak_grants_x2_at_five_and_x5_at_ten,
        test_double_kill_streak_survives_single_kill_bomb,
        test_double_kill_streak_resets_on_damage,
        test_double_kill_streak_survives_level_change,
        test_sniper_kill_does_not_feed_double_kill_streak,
        test_megakill_at_single_bomb_ten_kills_sets_invuln_and_star,
        test_megakill_not_at_single_bomb_nine_kills,
        test_megakill_star_color_cycles,
        test_megakill_star_draws,
        test_score_text_on_explosion_with_gain,
        test_score_text_none_on_no_score_gain,
        test_score_text_ages_out_in_update,
        test_score_text_draw,
    ]
    passed = 0
    for fn in tests:
        try:
            fn()
            passed += 1
            print('PASS ' + fn.__name__)
        except Exception as e:
            print('FAIL ' + fn.__name__ + ': ' + repr(e))
    print('%d/%d tests passed' % (passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    sys.exit(main())
