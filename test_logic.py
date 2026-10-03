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
