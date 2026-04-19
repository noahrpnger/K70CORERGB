import pytest
from k70corergb.keys import Key, SLOT_COUNT, key_from_name, all_keys


class TestKeyEnum:
    def test_slot_count(self):
        assert len(Key) == SLOT_COUNT

    def test_no_duplicate_slots(self):
        slots = [k.value for k in Key]
        assert len(slots) == len(set(slots))

    def test_slots_are_contiguous(self):
        slots = sorted(k.value for k in Key)
        assert slots == list(range(SLOT_COUNT))

    def test_known_keys(self):
        assert Key.ESC == 0
        assert Key.SPACE == 72
        assert Key.LOGO == 111


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
        assert len(all_keys()) == SLOT_COUNT

    def test_returns_key_instances(self):
        assert all(isinstance(k, Key) for k in all_keys())