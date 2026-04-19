import pytest
from k70corergb.colors import Color, Colors


class TestColorConstruction:
    def test_valid_color(self):
        c = Color(255, 61, 65)
        assert (c.r, c.g, c.b) == (255, 61, 65)

    def test_from_hex_with_hash(self):
        assert Color.from_hex("#ff3d41") == Color(255, 61, 65)

    def test_from_hex_without_hash(self):
        assert Color.from_hex("ff3d41") == Color(255, 61, 65)

    def test_from_bgr_bytes(self):
        assert Color.from_bgr_bytes(65, 61, 255) == Color(255, 61, 65)

    def test_invalid_channel_too_high(self):
        with pytest.raises(ValueError):
            Color(256, 0, 0)

    def test_invalid_channel_negative(self):
        with pytest.raises(ValueError):
            Color(-1, 0, 0)

    def test_invalid_hex_length(self):
        with pytest.raises(ValueError):
            Color.from_hex("fff")

    def test_immutable(self):
        with pytest.raises(Exception):
            Color(255, 0, 0).r = 0


class TestColorConversion:
    def test_to_bgr_bytes(self):
        assert Color(255, 61, 65).to_bgr_bytes() == (65, 61, 255)

    def test_to_hex(self):
        assert Color(255, 61, 65).to_hex() == "ff3d41"

    def test_bgr_roundtrip(self):
        original = Color(255, 61, 65)
        assert Color.from_bgr_bytes(*original.to_bgr_bytes()) == original


class TestColorBlend:
    def test_blend_at_zero(self):
        assert Colors.RED.blend(Colors.BLUE, 0.0) == Colors.RED

    def test_blend_at_one(self):
        assert Colors.RED.blend(Colors.BLUE, 1.0) == Colors.BLUE

    def test_blend_midpoint(self):
        assert Color(0, 0, 0).blend(Color(254, 254, 254), 0.5) == Color(127, 127, 127)

    def test_blend_invalid_factor(self):
        with pytest.raises(ValueError):
            Colors.RED.blend(Colors.BLUE, 1.5)


class TestNamedColors:
    def test_off_is_black(self):
        assert Colors.OFF == Color(0, 0, 0)

    def test_red(self):
        assert Colors.RED == Color(255, 0, 0)

    def test_blue(self):
        assert Colors.BLUE == Color(0, 0, 255)