from __future__ import annotations

import threading

from k70corergb.colors import Color, Colors
from k70corergb.device import Device
from k70corergb.keys import Key, SLOT_COUNT, all_keys
from k70corergb.protocol import (
    INIT_PACKETS,
    DEINIT_PACKETS,
    KEEPALIVE_PACKET,
    KEEPALIVE_INTERVAL_MS,
    build_color_packets,
)


class Keyboard:
    def __init__(self, device: Device | None = None) -> None:
        self._device = device or Device()
        self._state: dict[int, Color] = {slot: Colors.OFF for slot in range(SLOT_COUNT)}
        self._keepalive_timer: threading.Timer | None = None

    def open(self) -> None:
        self._device.open()
        # Take software control: disables the firmware effect engine so it
        # stops overwriting our color frames with the default static-white pattern.
        self._device.write_all(INIT_PACKETS)
        self._schedule_keepalive()

    def close(self) -> None:
        self._cancel_keepalive()
        self._device.write_all(DEINIT_PACKETS)
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

    def _send_keepalive(self) -> None:
        try:
            self._device.write(KEEPALIVE_PACKET)
        except Exception:
            pass
        self._schedule_keepalive()

    def _schedule_keepalive(self) -> None:
        self._cancel_keepalive()
        interval = KEEPALIVE_INTERVAL_MS / 1000.0
        self._keepalive_timer = threading.Timer(interval, self._send_keepalive)
        self._keepalive_timer.daemon = True
        self._keepalive_timer.start()

    def _cancel_keepalive(self) -> None:
        if self._keepalive_timer is not None:
            self._keepalive_timer.cancel()
            self._keepalive_timer = None

    def __repr__(self) -> str:
        return f"Keyboard(device={self._device!r})"