from __future__ import annotations
from k70corergb.colors import Color
from k70corergb.keys import SLOT_COUNT

PACKET_SIZE      = 64
HEADER_BYTE      = 0x08
START_CMD        = 0x06
CONT_CMD         = 0x07
CHANNEL          = 0x01

_START_HEADER = bytes([
    0x79, 0x01, 0x00, 0x00, 0x12,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
])

_START_PAYLOAD_OFFSET  = 3 + len(_START_HEADER)
_CONT_PAYLOAD_OFFSET   = 3


def _build_bgr_stream(color_map: dict[int, Color]) -> bytes:
    buf = bytearray(SLOT_COUNT * 3)
    for slot, color in color_map.items():
        b, g, r = color.to_bgr_bytes()
        buf[slot * 3]     = b
        buf[slot * 3 + 1] = g
        buf[slot * 3 + 2] = r
    return bytes(buf)


def _start_packet(payload_chunk: bytes) -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = HEADER_BYTE
    pkt[1] = START_CMD
    pkt[2] = CHANNEL
    pkt[3 : 3 + len(_START_HEADER)] = _START_HEADER
    capacity = PACKET_SIZE - _START_PAYLOAD_OFFSET
    pkt[_START_PAYLOAD_OFFSET : _START_PAYLOAD_OFFSET + len(payload_chunk)] = payload_chunk[:capacity]
    return bytes(pkt)


def _cont_packet(payload_chunk: bytes) -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = HEADER_BYTE
    pkt[1] = CONT_CMD
    pkt[2] = CHANNEL
    capacity = PACKET_SIZE - _CONT_PAYLOAD_OFFSET
    pkt[_CONT_PAYLOAD_OFFSET : _CONT_PAYLOAD_OFFSET + len(payload_chunk)] = payload_chunk[:capacity]
    return bytes(pkt)


def build_color_packets(color_map: dict[int, Color]) -> list[bytes]:
    if not color_map:
        raise ValueError("color_map must not be empty")
    invalid = [s for s in color_map if not (0 <= s < SLOT_COUNT)]
    if invalid:
        raise ValueError(f"Invalid slot indices: {invalid}")

    stream = _build_bgr_stream(color_map)

    start_capacity = PACKET_SIZE - _START_PAYLOAD_OFFSET
    cont_capacity  = PACKET_SIZE - _CONT_PAYLOAD_OFFSET

    packets: list[bytes] = []
    packets.append(_start_packet(stream[:start_capacity]))

    remaining = stream[start_capacity:]
    while remaining:
        chunk    = remaining[:cont_capacity]
        remaining = remaining[cont_capacity:]
        packets.append(_cont_packet(chunk))

    return packets