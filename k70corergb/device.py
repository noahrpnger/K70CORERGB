from __future__ import annotations
import hid
from k70corergb.protocol import PACKET_SIZE

CORSAIR_VID = 0x1B1C
K70_CORE_TKL_PID = 0x2B01
_USAGE_PAGE = 0xFF42
_INTERFACE  = 1


class DeviceNotFoundError(Exception):
    pass


class DeviceError(Exception):
    pass


def _find_device_path() -> bytes:
    devices = hid.enumerate(CORSAIR_VID, K70_CORE_TKL_PID)
    if not devices:
        raise DeviceNotFoundError(
            "K70 CORE TKL RGB not found. Make sure it is connected."
        )
    for info in devices:
        if info.get("usage_page") == _USAGE_PAGE and info.get("usage") == 1:
            return info["path"]
    for info in devices:
        if info.get("interface_number") == _INTERFACE:
            return info["path"]
    raise DeviceNotFoundError(
        "K70 CORE TKL RGB found but no suitable HID interface detected."
    )


class Device:
    def __init__(self) -> None:
        self._dev: hid.device | None = None

    def open(self) -> None:
        if self._dev is not None:
            return
        path = _find_device_path()
        dev = hid.device()
        try:
            dev.open_path(path)
        except OSError as exc:
            raise DeviceError(f"Failed to open device: {exc}") from exc
        self._dev = dev

    def close(self) -> None:
        if self._dev is None:
            return
        self._dev.close()
        self._dev = None

    def write(self, packet: bytes) -> None:
        if self._dev is None:
            raise DeviceError("Device is not open.")
        if len(packet) != PACKET_SIZE:
            raise ValueError(f"Packet must be {PACKET_SIZE} bytes, got {len(packet)}.")
        report = b"\x00" + packet
        try:
            self._dev.write(report)
        except OSError as exc:
            raise DeviceError(f"Write failed: {exc}") from exc

    def write_all(self, packets: list[bytes]) -> None:
        for packet in packets:
            self.write(packet)

    def __enter__(self) -> Device:
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "open" if self._dev is not None else "closed"
        return f"Device(vid=0x{CORSAIR_VID:04x}, pid=0x{K70_CORE_TKL_PID:04x}, state={state})"