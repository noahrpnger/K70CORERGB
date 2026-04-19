from __future__ import annotations
from dataclasses import dataclass


def _validate_channel(name: str, value: int) -> None:
    if not isinstance(value, int) or not (0 <= value <= 255):
        raise ValueError(f"Channel '{name}' must be an integer 0-255, got {value!r}")


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        _validate_channel("r", self.r)
        _validate_channel("g", self.g)
        _validate_channel("b", self.b)

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        h = hex_str.lstrip("#")
        if len(h) != 6:
            raise ValueError(f"Expected 6-character hex string, got {hex_str!r}")
        return cls(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @classmethod
    def from_bgr_bytes(cls, b: int, g: int, r: int) -> Color:
        return cls(r, g, b)

    def to_bgr_bytes(self) -> tuple[int, int, int]:
        return (self.b, self.g, self.r)

    def to_hex(self) -> str:
        return f"{self.r:02x}{self.g:02x}{self.b:02x}"

    def blend(self, other: Color, t: float) -> Color:
        if not (0.0 <= t <= 1.0):
            raise ValueError(f"Blend factor must be 0.0-1.0, got {t}")
        return Color(
            r=round(self.r + (other.r - self.r) * t),
            g=round(self.g + (other.g - self.g) * t),
            b=round(self.b + (other.b - self.b) * t),
        )

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b})"


class Colors:
    OFF     = Color(0,   0,   0)
    WHITE   = Color(255, 255, 255)
    RED     = Color(255, 0,   0)
    GREEN   = Color(0,   255, 0)
    BLUE    = Color(0,   0,   255)
    YELLOW  = Color(255, 255, 0)
    CYAN    = Color(0,   255, 255)
    MAGENTA = Color(255, 0,   255)
    ORANGE  = Color(255, 165, 0)
    PURPLE  = Color(128, 0,   128)