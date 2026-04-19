from __future__ import annotations
from enum import IntEnum


class Key(IntEnum):
    ESC         = 0
    F1          = 1
    F2          = 2
    F3          = 3
    F4          = 4
    F5          = 5
    F6          = 6
    F7          = 7
    F8          = 8
    F9          = 9
    F10         = 10
    F11         = 11
    F12         = 12
    PRINT_SCREEN = 13
    SCROLL_LOCK = 14
    PAUSE       = 15

    GRAVE       = 16
    N1          = 17
    N2          = 18
    N3          = 19
    N4          = 20
    N5          = 21
    N6          = 22
    N7          = 23
    N8          = 24
    N9          = 25
    N0          = 26
    MINUS       = 27
    EQUALS      = 28
    BACKSPACE   = 29

    TAB         = 30
    Q           = 31
    W           = 32
    E           = 33
    R           = 34
    T           = 35
    Y           = 36
    U           = 37
    I           = 38
    O           = 39
    P           = 40
    LBRACKET    = 41
    RBRACKET    = 42
    BACKSLASH   = 43

    CAPS_LOCK   = 44
    A           = 45
    S           = 46
    D           = 47
    F           = 48
    G           = 49
    H           = 50
    J           = 51
    K           = 52
    L           = 53
    SEMICOLON   = 54
    QUOTE       = 55
    ENTER       = 56

    LSHIFT      = 57
    Z           = 58
    X           = 59
    C           = 60
    V           = 61
    B           = 62
    N           = 63
    M           = 64
    COMMA       = 65
    PERIOD      = 66
    SLASH       = 67
    RSHIFT      = 68

    LCTRL       = 69
    LWIN        = 70
    LALT        = 71
    SPACE       = 72
    RALT        = 73
    RWIN        = 74
    FN          = 75
    RCTRL       = 76

    INSERT      = 77
    HOME        = 78
    PAGE_UP     = 79
    DELETE      = 80
    END         = 81
    PAGE_DOWN   = 82

    UP          = 83
    LEFT        = 84
    DOWN        = 85
    RIGHT       = 86

    NUM_LOCK    = 87
    KP_SLASH    = 88
    KP_ASTERISK = 89
    KP_MINUS    = 90
    KP_7        = 91
    KP_8        = 92
    KP_9        = 93
    KP_PLUS     = 94
    KP_4        = 95
    KP_5        = 96
    KP_6        = 97
    KP_1        = 98
    KP_2        = 99
    KP_3        = 100
    KP_0        = 101
    KP_PERIOD   = 102
    KP_ENTER    = 103

    MUTE        = 104
    VOLUME_DOWN = 105
    VOLUME_UP   = 106
    STOP        = 107
    PREV        = 108
    PLAY_PAUSE  = 109
    NEXT        = 110

    LOGO        = 111

    UNDERGLOW_1 = 112
    UNDERGLOW_2 = 113
    UNDERGLOW_3 = 114
    UNDERGLOW_4 = 115
    UNDERGLOW_5 = 116
    UNDERGLOW_6 = 117
    UNDERGLOW_7 = 118
    UNDERGLOW_8 = 119
    UNDERGLOW_9 = 120
    UNDERGLOW_10 = 121
    UNDERGLOW_11 = 122
    UNDERGLOW_12 = 123
    UNDERGLOW_13 = 124
    UNDERGLOW_14 = 125
    UNDERGLOW_15 = 126
    UNDERGLOW_16 = 127
    UNDERGLOW_17 = 128
    UNDERGLOW_18 = 129
    UNDERGLOW_19 = 130
    UNDERGLOW_20 = 131
    UNDERGLOW_21 = 132
    UNDERGLOW_22 = 133
    UNDERGLOW_23 = 134
    UNDERGLOW_24 = 135


SLOT_COUNT = 136

_KEY_NAMES: dict[str, Key] = {k.name: k for k in Key}


def key_from_name(name: str) -> Key:
    normalized = name.upper().replace(" ", "_")
    if normalized not in _KEY_NAMES:
        raise KeyError(f"Unknown key: {name!r}")
    return _KEY_NAMES[normalized]


def all_keys() -> list[Key]:
    return list(Key)