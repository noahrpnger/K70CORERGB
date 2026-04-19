import pytest
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key, SLOT_COUNT
from k70corergb.protocol import (
    build_color_packets,
    PACKET_SIZE,
    HEADER_BYTE,
    START_CMD,
    CONT_CMD,
    CHANNEL,
)

_ALL_RED = {slot: Colors.RED for slot in range(SLOT_COUNT)}


class TestBuildColorPackets:
    def test_returns_list_of_bytes(self):
        packets = build_color_packets(_ALL_RED)
        assert all(isinstance(p, bytes) for p in packets)

    def test_all_packets_are_64_bytes(self):
        packets = build_color_packets(_ALL_RED)
        assert all(len(p) == PACKET_SIZE for p in packets)

    def test_first_packet_is_start(self):
        pkt = build_color_packets(_ALL_RED)[0]
        assert pkt[0] == HEADER_BYTE
        assert pkt[1] == START_CMD
        assert pkt[2] == CHANNEL

    def test_continuation_packets_are_cont(self):
        for pkt in build_color_packets(_ALL_RED)[1:]:
            assert pkt[0] == HEADER_BYTE
            assert pkt[1] == CONT_CMD
            assert pkt[2] == CHANNEL

    def test_packet_count_covers_all_slots(self):
        packets = build_color_packets(_ALL_RED)
        start_capacity = PACKET_SIZE - 22
        cont_capacity  = PACKET_SIZE - 3
        total_bytes    = start_capacity + (len(packets) - 1) * cont_capacity
        assert total_bytes >= SLOT_COUNT * 3

    def test_empty_color_map_raises(self):
        with pytest.raises(ValueError):
            build_color_packets({})

    def test_invalid_slot_raises(self):
        with pytest.raises(ValueError):
            build_color_packets({SLOT_COUNT: Colors.RED})

    def test_negative_slot_raises(self):
        with pytest.raises(ValueError):
            build_color_packets({-1: Colors.RED})

    def test_bgr_order_in_stream(self):
        color_map = {0: Colors.RED}
        packets = build_color_packets(color_map)
        stream_start = 22
        b, g, r = packets[0][stream_start], packets[0][stream_start + 1], packets[0][stream_start + 2]
        assert (r, g, b) == (Colors.RED.r, Colors.RED.g, Colors.RED.b)

    def test_lights_off_produces_zero_stream(self):
        off_map = {slot: Colors.OFF for slot in range(SLOT_COUNT)}
        packets = build_color_packets(off_map)
        for pkt in packets:
            assert pkt[3:] == bytes(PACKET_SIZE - 3) or pkt[22:] == bytes(PACKET_SIZE - 22)

    def test_single_slot_does_not_affect_others(self):
        color_map = {Key.ESC: Colors.RED}
        packets = build_color_packets(color_map)
        stream_start = 22
        b, g, r = packets[0][stream_start], packets[0][stream_start + 1], packets[0][stream_start + 2]
        assert (r, g, b) == (255, 0, 0)
        assert packets[0][stream_start + 3] == 0