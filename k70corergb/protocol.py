from __future__ import annotations
from k70corergb.colors import Color
from k70corergb.keys import SLOT_COUNT

PACKET_SIZE     = 64
HEADER_BYTE     = 0x08
START_CMD       = 0x06
CONT_CMD        = 0x07
CHANNEL         = 0x01

# Bytes 3..20 of a color-start packet. iCUE's real header is 18 bytes
# (byte 3..6 = u32 LE magic 0x179, byte 7 = subcmd 0x12, bytes 8..20 = 13 pad).
# The RGB payload begins at byte 21.
_START_HEADER = bytes([
    0x79, 0x01, 0x00, 0x00, 0x12,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00,
])

_START_PAYLOAD_OFFSET = 3 + len(_START_HEADER)  # = 21
_CONT_PAYLOAD_OFFSET  = 3


def _pad(data: bytes) -> bytes:
    return (data + bytes(PACKET_SIZE))[:PACKET_SIZE]


def _reg_write(reg: int, val: int) -> bytes:
    """Build a register-write packet: 08 01 <reg_lo> <reg_hi> <val_lo> <val_hi>"""
    return _pad(bytes([
        0x08, 0x01,
        reg & 0xFF, (reg >> 8) & 0xFF,
        val & 0xFF, (val >> 8) & 0xFF,
    ]))


# Register 0x03 — hardware lighting mode:
#   0x02 = prep / transient
#   0x01 = software control (accepts direct color packets)
#   0x00 = firmware effect engine (reverts to default pattern)
#
# Register 0x4A — onboard memory commit flag:
#   0x00 = software-only mode (colors lost on power loss)
#   0x01 = memory mode (colors written to flash, survive power loss)
#
# iCUE sets 0x4A=0x0000 during normal software control and 0x4A=0x0001
# when "Device Memory Mode" is enabled. Everything else in the init
# sequence is identical between the two modes.


def _build_register_init(memory_mode: bool) -> list[bytes]:
    return [
        _reg_write(0x0003, 0x0002),  # mode: prep
        _reg_write(0x0003, 0x0001),  # mode: software control
        _reg_write(0x0003, 0x0002),  # mode: prep (iCUE cycles it)
        _reg_write(0x00fb, 0x0000),
        _reg_write(0x00fc, 0x0001),
        _reg_write(0x00fe, 0x0004),
        _reg_write(0x00ff, 0x0007),
        _reg_write(0x0009, 0x0001),
        _reg_write(0x0039, 0x0001),
        _reg_write(0x000a, 0x0005),
        _reg_write(0x0038, 0x0005),
        # 0x4A = 0x0001 commits colors to onboard flash; 0x0000 = software-only
        _reg_write(0x004a, 0x0001 if memory_mode else 0x0000),
        _reg_write(0x00fb, 0x0000),  # repeated
        _reg_write(0x00fc, 0x0001),  # repeated
        _reg_write(0x00fe, 0x0004),  # repeated
        _reg_write(0x00ff, 0x0007),  # repeated
    ]


# Config tables uploaded verbatim from iCue_startUp.pcapng frames 10045-10125.
_CONFIG_INIT_PACKETS: list[bytes] = [
    # --- Config table 1 (channel 0, subcmd 0x01, 125-byte body) ---
    bytes.fromhex(
        "0806027d000000010101013939393939"
        "39393939393939393939393939393939"
        "39393939393939393939393939393939"
        "39393939393939390139393939393939"
    ),
    bytes.fromhex(
        "08070239393939393939393939393939"
        "01010139393939393939393939010101"
        "01010101010101010101010101013939"
        "0101013f3f3f393f3f3f010101010101"
    ),
    bytes.fromhex(
        "080702010101013f0139000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000"
    ),
    _pad(bytes([0x08, 0x05, 0x01])),
    _pad(bytes([0x08, 0x0d, 0x00, 0x2e])),

    # --- Config table 2 (channel 0, subcmd 0x2b, 457-byte body) ---
    bytes.fromhex(
        "080600c90100002b0000000000000000"
        "00000000000000000400000000050000"
        "00000600000000070000000008000000"
        "0009000000000a000000000b00000000"
    ),
    bytes.fromhex(
        "0807000c000000000d000000000e0000"
        "00000f00000000100000000011000000"
        "00120000000013000000001400000000"
        "15000000001600000000170000000018"
    ),
    bytes.fromhex(
        "0807000000000019000000001a000000"
        "001b000000001c000000001d00000000"
        "1e000000001f00000000200000000021"
        "00000000220000000023000000002400"
    ),
    bytes.fromhex(
        "08070000000025000000002600000000"
        "2700000000280000000029000000002a"
        "000000002b000000002c000000002d00"
        "0000002e000000002f00000000300000"
    ),
    bytes.fromhex(
        "08070000003200000000330000000034"
        "00000000350000000036000000003700"
        "000000380000000039000000003a0000"
        "00003b000000003c000000003d000000"
    ),
    bytes.fromhex(
        "080700003e000000003f000000004000"
        "00000041000000004200000000430000"
        "00004400000000450000000049000000"
        "004a000000004b000000004c00000000"
    ),
    bytes.fromhex(
        "0807004d000000004e000000004f0000"
        "00005000000000510000000052000000"
        "00640000000065000000006900000000"
        "6a000000006b000000006c000000006d"
    ),
    bytes.fromhex(
        "080700000000006e000000006f000000"
        "007a000000007c000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000"
    ),
    _pad(bytes([0x08, 0x0d, 0x01, 0x22])),
]


def build_memory_mode_packet(enabled: bool) -> bytes:
    """Single reg 0x4A write — flips memory mode without re-running full init."""
    return _reg_write(0x004a, 0x0001 if enabled else 0x0000)


def build_init_packets(memory_mode: bool = False) -> list[bytes]:
    return [
        _pad(bytes([0x08, 0x02, 0x03])),
        _pad(bytes([0x08, 0x0d, 0x00, 0x24])),
        _pad(bytes([0x08, 0x0d, 0x00, 0x36])),
        _pad(bytes([0x08, 0x09, 0x00])),
        _pad(bytes([0x08, 0x08, 0x00])),
        *_build_register_init(memory_mode),
        *_CONFIG_INIT_PACKETS,
        _pad(bytes([0x08, 0x05, 0x01])),
    ]


# Keep a pre-built default for callers that don't need memory mode.
INIT_PACKETS: list[bytes] = build_init_packets(memory_mode=False)

KEEPALIVE_PACKET: bytes = _pad(bytes([0x08, 0x05, 0x01]))
KEEPALIVE_INTERVAL_MS: int = 1500

# iCUE never sends a deinit packet on close — sending 08 05 00 hands control
# back to the firmware effect engine, causing the default pattern to play.
# We send nothing on close so the last colors set persist after the app exits.
DEINIT_PACKETS: list[bytes] = []


def _build_rgb_stream(color_map: dict[int, Color]) -> bytes:
    buf = bytearray(SLOT_COUNT * 3)
    for slot, color in color_map.items():
        buf[slot * 3]     = color.r
        buf[slot * 3 + 1] = color.g
        buf[slot * 3 + 2] = color.b
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

    stream = _build_rgb_stream(color_map)
    start_capacity = PACKET_SIZE - _START_PAYLOAD_OFFSET
    cont_capacity  = PACKET_SIZE - _CONT_PAYLOAD_OFFSET

    packets: list[bytes] = [_start_packet(stream[:start_capacity])]
    remaining = stream[start_capacity:]
    while remaining:
        chunk, remaining = remaining[:cont_capacity], remaining[cont_capacity:]
        packets.append(_cont_packet(chunk))

    return packets