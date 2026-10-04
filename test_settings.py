import os
import sys
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

pygame.init()
pygame.display.set_mode((2, 2))

import bomb

TMP = None
_real_base_dir = bomb._base_dir


def _tmp_base_dir():
    return _real_base_dir() if TMP is None else TMP


bomb._base_dir = _tmp_base_dir


def key_event(key, unicode=''):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0, scancode=0)


def fresh_settings():
    p = os.path.join(bomb._base_dir(), bomb.SETTINGS_FILE)
    if os.path.exists(p):
        os.remove(p)
    bomb.SETTINGS = bomb.Settings()
    return bomb.SETTINGS


def test_volume_range_clamped():
    s = fresh_settings()
    s.set_volume(300)
    assert s.volume == bomb.VOL_MAX
    s.set_volume(-20)
    assert s.volume == bomb.VOL_MIN


def test_volume_defaults_and_bounds():
    s = fresh_settings()
    assert bomb.VOL_MIN == 0
    assert bomb.VOL_MAX == 255
    assert 0 <= s.volume <= 255


def test_volume_adjust_step():
    s = fresh_settings()
    s.set_volume(100)
    s.adjust_volume(+bomb.VOL_STEP)
    assert s.volume == 100 + bomb.VOL_STEP
    s.adjust_volume(-bomb.VOL_STEP)
    assert s.volume == 100


def test_volume_scale_maps_0_255():
    s = fresh_settings()
    s.set_volume(0)
    assert bomb._volume_scale() == 0.0
    s.set_volume(255)
    assert bomb._volume_scale() == 1.0
    s.set_volume(128)
    assert 0.49 < bomb._volume_scale() < 0.51


def test_volume_persisted_to_settings_json():
    s = fresh_settings()
    s.set_volume(77)
    assert os.path.isfile(s.path)
    s2 = bomb.Settings()
    assert s2.volume == 77


def test_windowed_target_size_is_native():
    s = fresh_settings()
    s.fullscreen = False
    assert s.target_size() == (bomb.SCREEN_W, bomb.SCREEN_H)


def test_fullscreen_toggle_persisted():
    s = fresh_settings()
    s.fullscreen = False
    assert s.toggle_fullscreen() is True
    assert bomb.Settings().fullscreen is True
    s.toggle_fullscreen()
    assert bomb.Settings().fullscreen is False


def test_fullscreen_uses_desktop_size():
    s = fresh_settings()
    s.fullscreen = True
    desktop = bomb._desktop_size()
    if desktop:
        assert s.target_size() == desktop
    else:
        assert s.target_size() == (bomb.SCREEN_W, bomb.SCREEN_H)
    s.fullscreen = False


def test_menu_has_only_volume_fullscreen_and_highscore_reset():
    assert bomb.SettingsUI.ROWS == ('volume', 'fullscreen', 'reset_scores')
    assert bomb.SettingsUI.ROWS != ('volume', 'resolution', 'fullscreen')
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    for row in bomb.SettingsUI.ROWS:
        ui.index = bomb.SettingsUI.ROWS.index(row)
        assert isinstance(ui.row_value(row), str)
        assert isinstance(ui.row_hint(row), str)
        assert 'Auflösung' not in ui.row_value(row)


def test_settings_ui_opens_with_m():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    assert ui.open is False
    assert ui.handle_event(key_event(pygame.K_m)) is True
    assert ui.open is True
    assert ui.handle_event(key_event(pygame.K_m)) is True
    assert ui.open is False


def test_settings_ui_navigation_wraps():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.ROWS[ui.index] == 'volume'
    ui.handle_event(key_event(pygame.K_DOWN))
    assert ui.ROWS[ui.index] == 'fullscreen'
    ui.handle_event(key_event(pygame.K_DOWN))
    assert ui.ROWS[ui.index] == 'reset_scores'
    ui.handle_event(key_event(pygame.K_DOWN))
    assert ui.ROWS[ui.index] == 'volume'
    ui.handle_event(key_event(pygame.K_UP))
    assert ui.ROWS[ui.index] == 'reset_scores'


def test_settings_ui_plus_minus_volume():
    s = fresh_settings()
    s.set_volume(120)
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.handle_event(key_event(pygame.K_PLUS))
    assert s.volume == 120 + bomb.VOL_STEP
    ui.handle_event(key_event(pygame.K_MINUS))
    ui.handle_event(key_event(pygame.K_MINUS))
    assert s.volume == 120 - bomb.VOL_STEP


def test_settings_ui_number_entry():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.editing is True
    for ch in '200':
        ui.handle_event(key_event(pygame.K_0 + int(ch), unicode=ch))
    assert ui.buffer == '200'
    ui.handle_event(key_event(pygame.K_BACKSPACE))
    assert ui.buffer == '20'
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.editing is False
    assert s.volume == 20


def test_settings_ui_number_entry_clamps():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.handle_event(key_event(pygame.K_RETURN))
    ui.buffer = '999'
    ui.handle_event(key_event(pygame.K_RETURN))
    assert s.volume == 255


def test_settings_ui_number_entry_cancel():
    s = fresh_settings()
    s.set_volume(90)
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.handle_event(key_event(pygame.K_RETURN))
    ui.buffer = '10'
    ui.handle_event(key_event(pygame.K_ESCAPE))
    assert ui.editing is False
    assert s.volume == 90


def test_settings_ui_escape_closes():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.handle_event(key_event(pygame.K_ESCAPE)) is True
    assert ui.open is False


def test_settings_ui_fullscreen_toggle():
    s = fresh_settings()
    s.fullscreen = False
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.handle_event(key_event(pygame.K_DOWN))
    assert ui.ROWS[ui.index] == 'fullscreen'
    ui.handle_event(key_event(pygame.K_RETURN))
    assert s.fullscreen is True
    assert ui.needs_display is True
    ui.needs_display = False
    ui.handle_event(key_event(pygame.K_MINUS))
    assert s.fullscreen is False


def test_settings_ui_ignores_events_when_closed():
    s = fresh_settings()
    s.set_volume(100)
    ui = bomb.SettingsUI(s)
    ui.open = False
    assert ui.handle_event(key_event(pygame.K_DOWN)) is False
    assert ui.handle_event(key_event(pygame.K_PLUS)) is False
    assert s.volume == 100


def test_settings_ui_row_values():
    s = fresh_settings()
    s.set_volume(200)
    ui = bomb.SettingsUI(s)
    assert '200' in ui.row_value('volume')
    assert '255' in ui.row_value('volume')
    s.fullscreen = True
    assert ui.row_value('fullscreen') == 'AN'
    s.fullscreen = False
    assert ui.row_value('fullscreen') == 'AUS'


def test_joy_menu_button_is_not_bomb_button():
    assert bomb.JOY_BTN_MENU == (7,)
    assert bomb.JOY_BTN_B == 1
    assert 1 not in bomb.JOY_BTN_MENU


def test_joy_pause_is_view_button():
    assert bomb.JOY_BTN_PAUSE == (6,)
    assert 7 not in bomb.JOY_BTN_PAUSE


def joy_event(button):
    return pygame.event.Event(pygame.JOYBUTTONDOWN, button=button, joy=0, instance_id=0)


def test_menu_opens_with_joy_menu_button():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    assert ui.open is False
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0])) is True
    assert ui.open is True
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0])) is True
    assert ui.open is False


def test_menu_ignores_joy_bomb_button():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_B)) is False
    assert ui.open is False


def test_menu_closes_with_joy_bomb_button():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    assert ui.open is True
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_B)) is True
    assert ui.open is False


def test_menu_joy_bomb_button_closes_even_while_editing():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    ui.open = True
    ui.editing = True
    ui.buffer = '77'
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_B)) is True
    assert ui.open is False
    assert ui.editing is False
    assert ui.buffer == ''
    assert s.volume != 77


def hat_event(value):
    return pygame.event.Event(pygame.JOYHATMOTION, value=value, joy=0, instance_id=0)


def test_menu_joy_hat_navigates_and_changes_volume():
    s = fresh_settings()
    s.set_volume(120)
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.handle_joy_event(hat_event((0, 1))) is True
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((0, -1))) is True
    assert ui.ROWS[ui.index] == 'volume'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((1, 0))) is True
    assert s.volume == 120 + bomb.VOL_STEP
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((-1, 0))) is True
    assert s.volume == 120


def test_menu_joy_hat_steps_only_once_per_press():
    s = fresh_settings()
    s.set_volume(100)
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.handle_joy_event(hat_event((1, 0))) is True
    assert s.volume == 100 + bomb.VOL_STEP
    for _ in range(5):
        assert ui.handle_joy_event(hat_event((1, 0))) is True
    assert s.volume == 100 + bomb.VOL_STEP
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((1, 0))) is True
    assert s.volume == 100 + 2 * bomb.VOL_STEP


def test_menu_joy_hat_diagonal_uses_dominant_axis():
    s = fresh_settings()
    s.fullscreen = False
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.handle_joy_event(hat_event((0, 1))) is True
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((0.5, 1))) is True
    assert ui.ROWS[ui.index] == 'reset_scores'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((0.5, -1))) is True
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((-1, 0.5))) is True
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((0, -1))) is True
    assert ui.ROWS[ui.index] == 'volume'
    assert ui.handle_joy_event(hat_event((0, 0))) is False
    assert ui.handle_joy_event(hat_event((1, 0.5))) is True
    assert s.volume == bomb.VOL_DEFAULT + bomb.VOL_STEP


def test_menu_joy_hat_does_nothing_when_closed():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    assert ui.handle_joy_event(hat_event((0, 1))) is False
    assert ui.open is False


def test_menu_joy_a_button_mutes_volume_row():
    s = fresh_settings()
    s.set_volume(140)
    ui = bomb.SettingsUI(s)
    ui.open = True
    assert ui.ROWS[ui.index] == 'volume'
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert s.volume == 0
    assert ui.editing is False
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert s.volume == 140


def test_menu_ignores_joy_view_button():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_PAUSE[0])) is False
    assert ui.open is False


def test_menu_joy_dpad_up_down_selects_row():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    assert ui.index == 0
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1])) is True
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1])) is True
    assert ui.ROWS[ui.index] == 'reset_scores'
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1])) is True
    assert ui.ROWS[ui.index] == 'volume'
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[0])) is True
    assert ui.ROWS[ui.index] == 'reset_scores'


def test_menu_joy_dpad_left_right_changes_volume():
    s = fresh_settings()
    s.set_volume(120)
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    assert ui.ROWS[ui.index] == 'volume'
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[3])) is True
    assert s.volume == 120 + bomb.VOL_STEP
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[2])) is True
    assert s.volume == 120


def test_menu_joy_dpad_left_right_clamps_volume():
    s = fresh_settings()
    s.set_volume(bomb.VOL_MAX)
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    for _ in range(3):
        ui.handle_joy_event(joy_event(bomb.JOY_DPAD[3]))
    assert s.volume == bomb.VOL_MAX
    s.set_volume(bomb.VOL_MIN)
    for _ in range(3):
        ui.handle_joy_event(joy_event(bomb.JOY_DPAD[2]))
    assert s.volume == bomb.VOL_MIN


def test_menu_joy_dpad_left_right_toggles_fullscreen():
    s = fresh_settings()
    s.fullscreen = False
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1]))
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(joy_event(bomb.JOY_DPAD[3])) is True
    assert s.fullscreen is True


def test_menu_joy_a_button_toggles_fullscreen():
    s = fresh_settings()
    s.fullscreen = False
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1]))
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert s.fullscreen is True
    assert ui.needs_display is True
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert s.fullscreen is False


def test_menu_joy_navigation_and_activate():
    s = fresh_settings()
    s.set_volume(100)
    s.fullscreen = False
    ui = bomb.SettingsUI(s)
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_MENU[0]))
    assert ui.ROWS[ui.index] == 'volume'
    ui.handle_joy_event(joy_event(bomb.JOY_DPAD[1]))
    assert ui.ROWS[ui.index] == 'fullscreen'
    ui.handle_joy_event(joy_event(bomb.JOY_DPAD[0]))
    assert ui.ROWS[ui.index] == 'volume'
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_A))
    assert s.volume == 0
    ui.index = 1
    ui.handle_joy_event(joy_event(bomb.JOY_BTN_A))
    assert s.fullscreen is True


def test_settings_ui_draw_smoke():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    surf = pygame.Surface((bomb.SCREEN_W, bomb.SCREEN_H))
    ui.open = True
    ui.update(0.016)
    ui.draw(surf)
    ui.handle_event(key_event(pygame.K_RETURN))
    ui.draw(surf)


def test_beep_registered_and_tracks_volume():
    s = fresh_settings()
    bomb._init_beep()
    assert 'beep' in bomb.SFX
    s.set_volume(0)
    assert bomb.SFX['beep'].get_volume() == 0.0
    s.set_volume(255)
    assert bomb.SFX['beep'].get_volume() == 1.0
    s.set_volume(128)
    assert 0.49 < bomb.SFX['beep'].get_volume() < 0.51


def test_apply_volume_scales_all_sfx():
    s = fresh_settings()
    bomb.SFX['explosion'] = pygame.mixer.Sound(buffer=b'\x00\x00' * 1000)
    bomb.SFX_BASE['explosion'] = 0.5
    s.set_volume(255)
    assert abs(bomb.SFX['explosion'].get_volume() - 0.5) < 0.001
    s.set_volume(0)
    assert bomb.SFX['explosion'].get_volume() == 0.0


def test_apply_display_uses_settings():
    s = fresh_settings()
    s.fullscreen = False
    surf = bomb.apply_display()
    assert surf.get_size() == (bomb.SCREEN_W, bomb.SCREEN_H)
    s.fullscreen = False


def test_highscore_reset_row_needs_two_confirmations():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.index = ui.ROWS.index('reset_scores')
    assert ui.row_value('reset_scores') == 'LOESCHEN'
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.confirm_reset is True
    assert ui.row_value('reset_scores') == 'WIRKLICH?'
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.confirm_reset is False
    assert ui.hiscores_reset is True


def test_highscore_reset_row_escape_and_navigation_cancel():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.index = ui.ROWS.index('reset_scores')
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.confirm_reset is True
    ui.handle_event(key_event(pygame.K_ESCAPE))
    assert ui.open is False
    assert ui.confirm_reset is False
    # Navigieren hebt die Bestaetigung ebenfalls auf
    ui.open = True
    ui.index = ui.ROWS.index('reset_scores')
    ui.handle_event(key_event(pygame.K_RETURN))
    assert ui.confirm_reset is True
    ui.handle_event(key_event(pygame.K_UP))
    assert ui.confirm_reset is False
    assert ui.ROWS[ui.index] == 'fullscreen'
    assert ui.hiscores_reset is False


def test_highscore_reset_row_left_right_does_nothing():
    s = fresh_settings()
    before = (s.fullscreen, s.volume)
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.index = ui.ROWS.index('reset_scores')
    ui.handle_event(key_event(pygame.K_PLUS))
    ui.handle_event(key_event(pygame.K_MINUS))
    assert (s.fullscreen, s.volume) == before
    assert ui.hiscores_reset is False


def test_highscore_reset_row_gamepad_a_twice():
    s = fresh_settings()
    ui = bomb.SettingsUI(s)
    ui.open = True
    ui.index = ui.ROWS.index('reset_scores')
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert ui.confirm_reset is True
    assert ui.hiscores_reset is False
    assert ui.handle_joy_event(joy_event(bomb.JOY_BTN_A)) is True
    assert ui.hiscores_reset is True


def test_highscore_reset_writes_empty_file():
    tmp = TMP + '.json'
    original = bomb._hs_file
    bomb._hs_file = lambda: tmp
    try:
        bomb.save_highscores([['AAA', 300], ['BBB', 200]])
        assert bomb.load_highscores() == [['AAA', 300], ['BBB', 200]]
        s = fresh_settings()
        ui = bomb.SettingsUI(s)
        ui.open = True
        ui.index = ui.ROWS.index('reset_scores')
        ui.handle_event(key_event(pygame.K_RETURN))
        ui.handle_event(key_event(pygame.K_RETURN))
        assert ui.hiscores_reset is True
        assert bomb.load_highscores() == []
        assert ui.row_value('reset_scores') == 'LOESCHEN'
    finally:
        bomb._hs_file = original


def main():
    global TMP
    tests = [
        test_volume_range_clamped,
        test_volume_defaults_and_bounds,
        test_volume_adjust_step,
        test_volume_scale_maps_0_255,
        test_volume_persisted_to_settings_json,
        test_windowed_target_size_is_native,
        test_fullscreen_toggle_persisted,
        test_fullscreen_uses_desktop_size,
        test_menu_has_only_volume_fullscreen_and_highscore_reset,
        test_settings_ui_opens_with_m,
        test_settings_ui_navigation_wraps,
        test_settings_ui_plus_minus_volume,
        test_settings_ui_number_entry,
        test_settings_ui_number_entry_clamps,
        test_settings_ui_number_entry_cancel,
        test_settings_ui_escape_closes,
        test_settings_ui_fullscreen_toggle,
        test_settings_ui_ignores_events_when_closed,
        test_settings_ui_row_values,
        test_joy_menu_button_is_not_bomb_button,
        test_joy_pause_is_view_button,
        test_menu_opens_with_joy_menu_button,
        test_menu_ignores_joy_bomb_button,
        test_menu_closes_with_joy_bomb_button,
        test_menu_joy_bomb_button_closes_even_while_editing,
        test_menu_joy_hat_navigates_and_changes_volume,
        test_menu_joy_hat_steps_only_once_per_press,
        test_menu_joy_hat_diagonal_uses_dominant_axis,
        test_menu_joy_hat_does_nothing_when_closed,
        test_menu_joy_a_button_mutes_volume_row,
        test_menu_ignores_joy_view_button,
        test_menu_joy_dpad_up_down_selects_row,
        test_menu_joy_dpad_left_right_changes_volume,
        test_menu_joy_dpad_left_right_clamps_volume,
        test_menu_joy_dpad_left_right_toggles_fullscreen,
        test_menu_joy_a_button_toggles_fullscreen,
        test_menu_joy_navigation_and_activate,
        test_settings_ui_draw_smoke,
        test_highscore_reset_row_needs_two_confirmations,
        test_highscore_reset_row_escape_and_navigation_cancel,
        test_highscore_reset_row_left_right_does_nothing,
        test_highscore_reset_row_gamepad_a_twice,
        test_highscore_reset_writes_empty_file,
        test_beep_registered_and_tracks_volume,
        test_apply_volume_scales_all_sfx,
        test_apply_display_uses_settings,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        TMP = tmp
        passed = 0
        for fn in tests:
            try:
                fn()
                passed += 1
                print('PASS ' + fn.__name__)
            except Exception as e:
                print('FAIL ' + fn.__name__ + ': ' + repr(e))
    TMP = None
    print('%d/%d tests passed' % (passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    sys.exit(main())