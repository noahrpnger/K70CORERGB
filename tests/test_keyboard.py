import pytest
from unittest.mock import MagicMock, patch
from k70corergb.keyboard import Keyboard
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key, SLOT_COUNT


def _make_keyboard() -> tuple[Keyboard, MagicMock]:
    device = MagicMock()
    kb = Keyboard(device=device)
    return kb, device


class TestKeyboardInit:
    def test_default_state_is_off(self):
        kb, _ = _make_keyboard()
        assert all(v == Colors.OFF for v in kb._state.values())

    def test_state_has_all_slots(self):
        kb, _ = _make_keyboard()
        assert len(kb._state) == SLOT_COUNT


class TestSetKey:
    def test_updates_state(self):
        kb, _ = _make_keyboard()
        kb.set_key(Key.ESC, Colors.RED)
        assert kb._state[Key.ESC] == Colors.RED

    def test_flushes_to_device(self):
        kb, device = _make_keyboard()
        kb.set_key(Key.ESC, Colors.RED)
        assert device.write_all.called

    def test_invalid_key_type_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(TypeError):
            kb.set_key("ESC", Colors.RED)

    def test_invalid_color_type_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(TypeError):
            kb.set_key(Key.ESC, (255, 0, 0))

    def test_does_not_affect_other_keys(self):
        kb, _ = _make_keyboard()
        kb.set_key(Key.ESC, Colors.RED)
        assert kb._state[Key.SPACE] == Colors.OFF


class TestSetKeys:
    def test_updates_multiple_keys(self):
        kb, _ = _make_keyboard()
        kb.set_keys({Key.ESC: Colors.RED, Key.SPACE: Colors.BLUE})
        assert kb._state[Key.ESC] == Colors.RED
        assert kb._state[Key.SPACE] == Colors.BLUE

    def test_single_flush_for_multiple_keys(self):
        kb, device = _make_keyboard()
        kb.set_keys({Key.ESC: Colors.RED, Key.SPACE: Colors.BLUE})
        assert device.write_all.call_count == 1

    def test_empty_dict_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(ValueError):
            kb.set_keys({})

    def test_invalid_key_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(TypeError):
            kb.set_keys({"ESC": Colors.RED})

    def test_invalid_color_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(TypeError):
            kb.set_keys({Key.ESC: "red"})


class TestSetAll:
    def test_sets_every_slot(self):
        kb, _ = _make_keyboard()
        kb.set_all(Colors.RED)
        assert all(v == Colors.RED for v in kb._state.values())

    def test_flushes_once(self):
        kb, device = _make_keyboard()
        kb.set_all(Colors.RED)
        assert device.write_all.call_count == 1

    def test_invalid_color_raises(self):
        kb, _ = _make_keyboard()
        with pytest.raises(TypeError):
            kb.set_all("red")


class TestOff:
    def test_sets_all_slots_to_off(self):
        kb, _ = _make_keyboard()
        kb.set_all(Colors.RED)
        kb.off()
        assert all(v == Colors.OFF for v in kb._state.values())


class TestContextManager:
    def test_opens_and_closes_device(self):
        kb, device = _make_keyboard()
        with kb:
            device.open.assert_called_once()
        device.close.assert_called_once()