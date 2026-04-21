import pytest
from k70corergb.keys import Key, SLOT_COUNT, key_from_name, all_keys


class TestKeyEnum:
    def test_slot_count_constant(self):
        # SLOT_COUNT is the size of the hardware LED buffer, not the number
        # of named keys — the keyboard has ghost/unused slots that don't
        # correspond to any physical key.
        assert SLOT_COUNT == 136

    def test_every_key_slot_is_in_range(self):
        for k in Key:
            assert 0 <= k.value < SLOT_COUNT

    def test_no_duplicate_slots(self):
        slots = [k.value for k in Key]
        assert len(slots) == len(set(slots))

    def test_known_keys(self):
        # Values verified by running calibrate.py against a real K70 Core TKL.
        assert Key.ESC == 37
        assert Key.SPACE == 40
        assert Key.A == 0
        assert Key.N1 == 26
        assert Key.F1 == 54


class TestKeyFromName:
    def test_exact_name(self):
        assert key_from_name("ESC") == Key.ESC

    def test_lowercase(self):
        assert key_from_name("space") == Key.SPACE

    def test_space_separator(self):
        assert key_from_name("caps lock") == Key.CAPS_LOCK

    def test_unknown_key(self):
        with pytest.raises(KeyError):
            key_from_name("DOESNOTEXIST")


class TestAllKeys:
    def test_returns_all_keys(self):
        assert len(all_keys()) == len(Key)

    def test_returns_key_instances(self):
        assert all(isinstance(k, Key) for k in all_keys())