import json
import os
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
import bomb
pygame.init()


def key(ch):
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode=ch)


def key_k(k, ch=''):
    """Tastatur-Event mit korrekt gesetztem key - wie es pygame im Spiel liefert."""
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)


def enter():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r')


def bs():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)


def frames(game, n, events=(), ui=None):
    """Spiegelt die Event-Reihenfolge aus main(): erst das Highscore-Popup,
    danach (nur wenn es zu ist) die Einstellungen."""
    for ev in events:
        pygame.event.post(ev)
    for _ in range(n):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if game.hs_popup:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_BACKSPACE:
                        game.hs_name = game.hs_name[:-1]
                    elif ev.key == pygame.K_RETURN:
                        game.hs_rank = bomb.add_highscore(game.hiscores, game.hs_name, game.score)
                        game.hs_popup = False
                        bomb.save_highscores(game.hiscores)
                    else:
                        c = ev.unicode
                        if len(c) == 1 and (c.isalnum() or c == ' '):
                            if len(game.hs_name) < bomb.HS_NAME_MAX:
                                game.hs_name += c
                continue
            if ui is not None and ev.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
                if ui.handle_joy_event(ev):
                    continue
                if ui.handle_event(ev):
                    continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p and game.state == bomb.STATE_PLAY:
                game.toggle_pause()
        game.update(0.02)


def setup(score, hs=None):
    game = bomb.Game()
    game.score = score
    game.player.lives = 1
    game.hiscores = list(hs or [])
    game.hurt_player()
    return game


TMP = tempfile.mkdtemp()
bomb._hs_file = lambda: os.path.join(TMP, 'highscores.json')


def test_load_empty():
    assert bomb.load_highscores() == []
    data = [{'name': '  AB ', 'score': 50}, {'name': 'CD', 'score': 1}, {'name': 'Z', 'score': 100}]
    # Alte, unsignierte Dateien werden abgelehnt (Manipulationsschutz)
    with open(bomb._hs_file(), 'w') as fh:
        json.dump(data, fh)
    out = bomb.load_highscores()
    assert out == []


def test_popup_and_save():
    if os.path.exists(bomb._hs_file()):
        os.remove(bomb._hs_file())
    game = setup(500, [])
    assert game.state == bomb.STATE_OVER
    assert game.hs_popup is True
    frames(game, 30, [key('m'), key('a'), key('x')])
    assert game.hs_name == 'max'
    frames(game, 5, [enter()])
    assert game.hs_popup is False
    assert game.hs_rank == 0
    assert game.hiscores == [['MAX', 500]]
    data = json.load(open(bomb._hs_file()))
    assert isinstance(data, dict)
    assert 'scores' in data and 'sig' in data
    assert data['scores'] == [['MAX', 500]]
    assert bomb.load_highscores() == [['MAX', 500]]


def test_backspace_and_cap():
    game = setup(500, [])
    assert game.hs_popup
    frames(game, 30, [key('a'), key('b'), key('c'), key('d'), key('z'), key('z'), key('z'), key('z'), key('z'), key('z'), key('z')])
    assert game.hs_name == 'abcdzzzzzz'
    frames(game, 5, [bs()])
    assert game.hs_name == 'abcdzzzzz'
    frames(game, 5, [key('q')])
    assert game.hs_name == 'abcdzzzzzq'
    frames(game, 5, [bs()])
    assert game.hs_name == 'abcdzzzzz'
    frames(game, 5, [key(' '), key('#')])
    assert game.hs_name == 'abcdzzzzz '
    frames(game, 5, [enter()])
    assert game.hiscores == [['ABCDZZZZZ', 500]]


def test_name_limit_is_10():
    assert bomb.HS_NAME_MAX == 10
    game = setup(500, [])
    frames(game, 40, [key(c) for c in 'abcdefghijklmno'])
    assert game.hs_name == 'abcdefghij'
    assert len(game.hs_name) == 10
    frames(game, 5, [enter()])
    assert game.hiscores == [['ABCDEFGHIJ', 500]]
    assert len(game.hiscores[0][0]) == 10


def test_name_stored_is_capped_on_load_too():
    bomb.save_highscores([['ABCDEFGHIJKLMNOP', 500]])
    assert bomb.load_highscores() == [['ABCDEFGHIJ', 500]]
    assert bomb._clean_name('ABCDEFGHIJKLMNOP') == 'ABCDEFGHIJ'


def test_letters_do_not_open_settings_while_popup_is_open():
    game = setup(500, [])
    assert game.hs_popup is True
    ui = bomb.SettingsUI(bomb.Settings())
    frames(game, 40, [key('m'), key('p'), key('w'), key('s'), key('a'),
                      key_k(pygame.K_m, 'm'), key_k(pygame.K_p, 'p')], ui=ui)
    # "M" und "P" wurden als Buchstaben getippt, nicht als Menü-Öffner / Pause
    assert ui.open is False
    assert game.state == bomb.STATE_OVER
    assert game.hs_name == 'mpwsa' + 'mp'
    frames(game, 5, [enter()])
    assert game.hiscores == [['MPWSAMP', 500]]
    # nach dem Popup funktioniert M wieder
    frames(game, 5, [key_k(pygame.K_m, 'm')], ui=ui)
    assert ui.open is True


def test_default_name():
    game = setup(500, [])
    frames(game, 5, [enter()])
    assert game.hiscores == [['PLAYER', 500]]


def test_rank_insertion():
    hs = [['A', 1000], ['B', 900], ['C', 800], ['D', 700]]
    game = setup(950, hs)
    assert game.hs_popup
    frames(game, 5, [enter()])
    assert game.hiscores == [['A', 1000], ['PLAYER', 950], ['B', 900], ['C', 800], ['D', 700]]
    assert game.hs_rank == 1


def test_no_popup_below():
    full = [['P%d' % i, 1000 - i * 100] for i in range(10)]
    assert bomb.hs_qualifies(100, full) is False
    assert bomb.hs_qualifies(0, full) is False
    assert bomb.hs_qualifies(200, full) is True
    assert bomb.hs_qualifies(500, []) is True
    game = setup(100, full)
    assert game.hs_popup is False
    assert game.hs_rank is None
    game = setup(200, full)
    assert game.hs_popup is True


def test_hs_confirm_helper():
    game = setup(500, [])
    game.hs_name = 'x'
    bomb._hs_confirm(game)
    assert game.hs_popup is False
    assert game.hs_popup_t > 0
    assert game.hiscores == [['X', 500]]
    assert bomb.load_highscores() == [['X', 500]]


def test_popup_enter_flow():
    game = setup(500, [])
    assert game.hs_popup
    frames(game, 5, [enter()])
    assert game.hs_popup is False
    assert game.hiscores == [['MAX', 500]]
    assert game.state == bomb.STATE_OVER
    assert game.hs_popup_t >= 0


def test_joys_dir():
    assert bomb._joy_dir() == (0, 0)
    assert bomb._joy_button(0) is False
    fake = {'axis': {0: 0.7, 1: 0.0}, 'btn': [False] * 16}
    class J:
        def get_axis(self, i):
            return fake['axis'][i]
        def get_button(self, i):
            return fake['btn'][i]
    bomb.JOY = J()
    assert bomb._joy_dir() == (1, 0)
    fake['axis'][0] = -0.9
    assert bomb._joy_dir() == (-1, 0)
    fake['axis'][1] = -0.5
    fake['axis'][0] = 0.0
    assert bomb._joy_dir() == (0, -1)
    fake['axis'][1] = 0.0
    fake['btn'][15] = True
    assert bomb._joy_dir() == (1, 0)
    fake['btn'][15] = False
    fake['btn'][14] = True
    assert bomb._joy_dir() == (-1, 0)
    fake['btn'][14] = False
    fake['btn'][12] = True
    assert bomb._joy_dir() == (0, -1)
    bomb.JOY = None
    assert bomb._joy_dir() == (0, 0)


def test_music_resume():
    mp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bomb.mp3')
    if not os.path.exists(mp):
        return
    m = pygame.mixer.music
    m.set_volume(0.0)
    m.load(mp)
    m.play()
    assert m.get_busy() is True
    bomb._sync_music(bomb.STATE_PAUSED)
    assert m.get_busy() is True and m.is_playing() is False
    bomb._sync_music(bomb.STATE_START)
    assert m.get_busy() is True and m.is_playing() is True
    bomb._sync_music(bomb.STATE_OVER)
    assert m.get_busy() is True and m.is_playing() is True
    m.stop()
    assert m.get_busy() is False
    bomb._sync_music(bomb.STATE_START)
    assert m.get_busy() is True and m.is_playing() is True
    m.stop()
    m.set_volume(1.0)


def test_draw():
    surf = pygame.display.set_mode((bomb.SCREEN_W, bomb.SCREEN_H))
    g1 = bomb.Game()
    g1.hiscores = [['MAX', 99999], ['AB', 1234]]
    bomb.draw(surf, g1, 0.0)
    g2 = setup(42, [])
    bomb.draw(surf, g2, 0.0)
    g2.hs_rank = 0
    g2.hs_popup = False
    bomb.draw(surf, g2, 0.0)
    g3 = bomb.Game()
    g3.hiscores = []
    bomb.draw(surf, g3, 0.0)
    g4 = setup(950, [['A', 1000], ['B', 900], ['C', 800], ['D', 700]])
    assert g4.hs_popup
    bomb.draw(surf, g4, 0.0)
    full10 = [['P%d' % i, 1000 - i * 100] for i in range(10)]
    g5 = setup(999, full10)
    assert g5.hs_popup
    bomb.draw(surf, g5, 0.0)
    g6 = bomb.Game()
    g6.state = bomb.STATE_PLAY
    g6.hiscores = [['MAX', 12345]]
    bomb.draw(surf, g6, 0.0)
    print('all tests ok')


if __name__ == '__main__':
    test_load_empty()
    test_popup_and_save()
    test_backspace_and_cap()
    test_name_limit_is_10()
    test_name_stored_is_capped_on_load_too()
    test_letters_do_not_open_settings_while_popup_is_open()
    test_default_name()
    test_rank_insertion()
    test_no_popup_below()
    test_draw()
