from __future__ import annotations
from k70corergb.colors import Color, Colors
from k70corergb.device import Device
from k70corergb.keys import Key, SLOT_COUNT, all_keys
from k70corergb.protocol import build_color_packets


class Keyboard:
    def __init__(self, device: Device | None = None) -> None:
        self._device = device or Device()
        self._state: dict[int, Color] = {slot: Colors.OFF for slot in range(SLOT_COUNT)}

    def open(self) -> None:
        self._device.open()

    def close(self) -> None:
        self._device.close()

    def __enter__(self) -> Keyboard:
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def set_key(self, key: Key, color: Color) -> None:
        if not isinstance(key, Key):
            raise TypeError(f"Expected Key, got {type(key).__name__!r}")
        if not isinstance(color, Color):
            raise TypeError(f"Expected Color, got {type(color).__name__!r}")
        self._state[key.value] = color
        self._flush()

    def set_keys(self, key_colors: dict[Key, Color]) -> None:
        if not key_colors:
            raise ValueError("key_colors must not be empty")
        for key, color in key_colors.items():
            if not isinstance(key, Key):
                raise TypeError(f"Expected Key, got {type(key).__name__!r}")
            if not isinstance(color, Color):
                raise TypeError(f"Expected Color, got {type(color).__name__!r}")
            self._state[key.value] = color
        self._flush()

    def set_all(self, color: Color) -> None:
        if not isinstance(color, Color):
            raise TypeError(f"Expected Color, got {type(color).__name__!r}")
        for slot in range(SLOT_COUNT):
            self._state[slot] = color
        self._flush()

    def off(self) -> None:
        self.set_all(Colors.OFF)

    def _flush(self) -> None:
        packets = build_color_packets(self._state)
        self._device.write_all(packets)

    def __repr__(self) -> str:
        return f"Keyboard(device={self._device!r})"