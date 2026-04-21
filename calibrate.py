"""
Interactive slot calibration for the K70 Core TKL RGB.

For each of the 136 LED slots, this script:
  1. Lights ONLY that slot (white, bright) and turns everything else off.
  2. Waits for you to press the physical key that lit up.
  3. Records which key you pressed for that slot.

At the end it writes the result to `calibration_result.json` and also
generates a fresh `keys_calibrated.py` that you can diff against
`k70corergb/keys.py` before replacing it.

Every physical key is recorded as-is — including ESC, space, and backspace,
which are themselves LEDs we need to calibrate. Control commands are CHORDS
so they can't collide with a single-key press:

  <any single key>  = record that key for the current slot, advance
  Ctrl+S            = mark current slot as empty/ghost, advance
  Ctrl+Z            = redo the previous slot
  Ctrl+Q            = abort and save progress so far

Requires: pynput  (pip install pynput)
On Linux you may need to run with sudo or give your user input-device perms.
On macOS grant your terminal Accessibility permission.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    from pynput import keyboard as pk
except ImportError:
    print("This script needs pynput. Install it with:  pip install pynput")
    sys.exit(1)

from k70corergb.colors import Color, Colors
from k70corergb.keyboard import Keyboard
from k70corergb.keys import SLOT_COUNT


WHITE = Color(255, 255, 255)
RESULT_JSON = Path(__file__).parent / "calibration_result.json"
OUTPUT_PY   = Path(__file__).parent / "keys_calibrated.py"


# Slots are sent as a dict; any slot not in the dict defaults to black via _flush,
# but to be explicit we build a full map each time.
def _light_only(kb: Keyboard, slot: int) -> None:
    state = {s: Colors.OFF for s in range(SLOT_COUNT)}
    state[slot] = WHITE
    # Use the keyboard's internal state/flush path for consistency.
    kb._state.update(state)   # noqa: SLF001 — intentional for calibration tool
    kb._flush()               # noqa: SLF001


def _keysym(key) -> str:
    """Turn a pynput key event into a stable, human-readable name."""
    if isinstance(key, pk.KeyCode):
        if key.char is not None:
            return key.char
        # Dead keys / special chars sometimes have no .char
        return f"vk_{key.vk}"
    # Special keys like Key.space, Key.esc, Key.f1, ...
    return f"<{key.name}>"


def _prompt(slot: int) -> None:
    sys.stdout.write(f"\rSlot {slot:3d} / {SLOT_COUNT - 1}: press the lit key "
                     f"(Ctrl+S=skip, Ctrl+Z=redo, Ctrl+Q=abort)   ")
    sys.stdout.flush()


class Calibrator:
    def __init__(self, kb: Keyboard) -> None:
        self.kb = kb
        self.results: dict[int, str] = {}
        self.slot = 0
        self.done = False
        self.aborted = False
        self._ctrl_down = False

    def _advance(self) -> None:
        self.slot += 1
        if self.slot >= SLOT_COUNT:
            self.done = True
            return
        _light_only(self.kb, self.slot)
        _prompt(self.slot)

    def _redo_prev(self) -> None:
        if self.slot == 0:
            print()
            print("  (already at first slot, nothing to redo)")
            _prompt(self.slot)
            return
        self.slot -= 1
        self.results.pop(self.slot, None)
        _light_only(self.kb, self.slot)
        print()
        print(f"  ↶ redoing slot {self.slot}")
        _prompt(self.slot)

    def _is_ctrl(self, key) -> bool:
        return key in (pk.Key.ctrl, pk.Key.ctrl_l, pk.Key.ctrl_r)

    # Ctrl+<letter> arrives from pynput as a KeyCode with char == '\x01' for
    # Ctrl+A, '\x02' for Ctrl+B, ..., so 's' = 0x13, 'z' = 0x1a, 'q' = 0x11.
    # We also match against the raw char in case the platform delivers it that
    # way, and against our _ctrl_down flag for modifier-tracking.
    def _chord_char(self, key) -> str | None:
        if not isinstance(key, pk.KeyCode):
            return None
        ch = key.char
        if ch is None:
            return None
        # Control characters
        if len(ch) == 1 and 1 <= ord(ch) <= 26:
            return chr(ord('a') + ord(ch) - 1)
        # If the OS delivers the plain letter but ctrl is held
        if self._ctrl_down and len(ch) == 1 and ch.isalpha():
            return ch.lower()
        return None

    def on_press(self, key) -> None:
        # NOTE: we never return False here unless we really want the listener
        # to stop. Returning None keeps it alive.
        try:
            if self.done:
                return

            if self._is_ctrl(key):
                self._ctrl_down = True
                return  # modifier alone doesn't record anything

            chord = self._chord_char(key)
            if chord is not None:
                if chord == 'q':
                    self.aborted = True
                    self.done = True
                    return
                if chord == 's':
                    self.results[self.slot] = "<skip>"
                    print(f"  slot {self.slot:3d} -> <skip>")
                    self._advance()
                    return
                if chord == 'z':
                    self._redo_prev()
                    return
                # Any other Ctrl+letter: ignore, don't record as key press.
                return

            # Normal single-key press — record it.
            name = _keysym(key)
            self.results[self.slot] = name
            print(f"  slot {self.slot:3d} -> {name}")
            self._advance()
        except Exception as exc:
            # A crashing callback would silently kill the listener and leave
            # the main loop spinning forever. Surface it and stop cleanly.
            print(f"\n[calibrate] callback error: {exc!r}")
            self.aborted = True
            self.done = True

    def on_release(self, key) -> None:
        if self._is_ctrl(key):
            self._ctrl_down = False


def _save_json(results: dict[int, str]) -> None:
    RESULT_JSON.write_text(
        json.dumps({str(k): v for k, v in sorted(results.items())}, indent=2)
    )
    print(f"\nRaw results saved to {RESULT_JSON}")


# --- code generation ------------------------------------------------------

# Map common OS keysyms onto the Key enum names used by the existing keys.py.
# Physical layout (QWERTZ) vs sent character: the user presses the key that
# lit up, so we get the CHARACTER it sends. The existing keys.py names keys
# by their QWERTY-ish logical position (Z=QWERTZ-Z-position, Y=QWERTZ-Y-
# position, etc.) with QWERTZ-specific comments. We'll use the character as
# the enum name where sensible and leave a TODO where it's ambiguous.
_SPECIAL_NAMES = {
    "<esc>": "ESC",
    "<f1>": "F1", "<f2>": "F2", "<f3>": "F3", "<f4>": "F4",
    "<f5>": "F5", "<f6>": "F6", "<f7>": "F7", "<f8>": "F8",
    "<f9>": "F9", "<f10>": "F10", "<f11>": "F11", "<f12>": "F12",
    "<tab>": "TAB",
    "<caps_lock>": "CAPS_LOCK",
    "<shift>": "LSHIFT",
    "<shift_r>": "RSHIFT",
    "<ctrl>": "LCTRL",
    "<ctrl_l>": "LCTRL",
    "<ctrl_r>": "RCTRL",
    "<alt>": "LALT",
    "<alt_l>": "LALT",
    "<alt_r>": "RALT",
    "<alt_gr>": "RALT",
    "<cmd>": "LWIN",
    "<cmd_l>": "LWIN",
    "<cmd_r>": "RWIN",
    "<enter>": "ENTER",
    "<space>": "SPACE",
    "<backspace>": "BACKSPACE",
    "<up>": "UP", "<down>": "DOWN", "<left>": "LEFT", "<right>": "RIGHT",
    "<home>": "HOME", "<end>": "END",
    "<page_up>": "PAGE_UP", "<page_down>": "PAGE_DOWN",
    "<insert>": "INSERT", "<delete>": "DELETE",
    "<print_screen>": "PRINT_SCREEN",
    "<scroll_lock>": "SCROLL_LOCK",
    "<pause>": "PAUSE",
    "<menu>": "MENU",
    "<fn>": "FN",
}

_CHAR_NAMES = {
    "`": "GRAVE",
    "1": "N1", "2": "N2", "3": "N3", "4": "N4", "5": "N5",
    "6": "N6", "7": "N7", "8": "N8", "9": "N9", "0": "N0",
    "-": "MINUS", "=": "EQUALS",
    "[": "LBRACKET", "]": "RBRACKET", "\\": "BACKSLASH",
    ";": "SEMICOLON", "'": "QUOTE",
    ",": "COMMA", ".": "PERIOD", "/": "SLASH",
    # --- QWERTZ (German / Swiss-German) layout characters ---
    # Names match the semantic QWERTY-position names used in the original
    # keys.py so downstream code keeps working.
    "ü": "LBRACKET",   # where [ is on QWERTY
    "+": "RBRACKET",   # where ] is on QWERTY
    "ö": "SEMICOLON",  # where ; is on QWERTY
    "ä": "QUOTE",      # where ' is on QWERTY
    "$": "BACKSLASH",  # $ / £ key on Swiss layout (where \ sits on QWERTY)
    "#": "BACKSLASH",  # # / ' key on German layout
    "^": "GRAVE",      # ^ / ° key sits where ` is on QWERTY
    "<": "EXTRA",      # extra key between LSHIFT and Y on ISO QWERTZ
    "ß": "MINUS",      # where - is on QWERTY (German)
    "´": "EQUALS",     # dead acute, where = is on QWERTY (German)
}


def _sanitize(name: str) -> str:
    """Last-resort scrub: make sure we never emit a non-ASCII identifier."""
    return "".join(c if c.isascii() and (c.isalnum() or c == "_") else "_"
                   for c in name)


def _enum_name(keysym: str) -> str | None:
    """Return the Key enum name for this keysym, or None if unmappable."""
    if keysym == "<skip>":
        return None
    if keysym in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[keysym]
    if keysym in _CHAR_NAMES:
        return _CHAR_NAMES[keysym]
    # ASCII letter -> uppercase enum name. We deliberately exclude non-ASCII
    # letters (ü, ö, ä, ß, …) here — those MUST go through _CHAR_NAMES above
    # so they map onto ASCII QWERTY-position names. Otherwise the generated
    # file would contain non-ASCII identifiers, which break str-based lookups.
    if len(keysym) == 1 and keysym.isascii() and keysym.isalpha():
        return keysym.upper()
    return None


def _generate_keys_py(results: dict[int, str]) -> str:
    lines = [
        "from __future__ import annotations",
        "from enum import IntEnum",
        "",
        "",
        "class Key(IntEnum):",
        "    # Slot values generated by calibrate.py on "
        + time.strftime("%Y-%m-%d %H:%M:%S"),
        "    # Each entry was verified by lighting the slot and recording the",
        "    # physical key the user pressed in response.",
    ]
    used_names: dict[str, int] = {}
    emitted = 0
    for slot in sorted(results):
        keysym = results[slot]
        name = _enum_name(keysym)
        if name is None:
            lines.append(f"    # slot {slot:3d} = {keysym!r} (skipped / unmapped)")
            continue
        # Belt-and-braces: even if a mapping slipped through with non-ASCII
        # content, never emit it as a raw identifier — comment it out instead.
        safe = _sanitize(name)
        if safe != name or not safe or not safe[0].isalpha():
            lines.append(
                f"    # slot {slot:3d} = {keysym!r} -> unsafe name {name!r}, skipped"
            )
            continue
        if safe in used_names:
            lines.append(
                f"    # slot {slot:3d} = {keysym!r} -> duplicate of "
                f"{safe} at slot {used_names[safe]}, skipped"
            )
            continue
        used_names[safe] = slot
        lines.append(f"    {safe:<12} = {slot}")
        emitted += 1
    # IntEnum class bodies must contain at least one member/statement, so if
    # the calibration was empty or fully unmapped we leave a placeholder.
    if emitted == 0:
        lines.append("    pass  # no keys mapped — re-run calibration")
    lines += [
        "",
        "",
        f"SLOT_COUNT = {SLOT_COUNT}",
        "",
        "_KEY_NAMES: dict[str, Key] = {k.name: k for k in Key}",
        "",
        "",
        "def key_from_name(name: str) -> Key:",
        "    normalized = name.upper().replace(' ', '_')",
        "    if normalized not in _KEY_NAMES:",
        "        raise KeyError(f'Unknown key: {name!r}')",
        "    return _KEY_NAMES[normalized]",
        "",
        "",
        "def all_keys() -> list[Key]:",
        "    return list(Key)",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    print("K70 Core TKL RGB — slot calibration")
    print("====================================")
    print(f"About to walk through all {SLOT_COUNT} slots.")
    print("For each slot, one LED will light up white. Press the physical key")
    print("that lit up. If nothing visibly lights (ghost slot), press Ctrl+S.")
    print("Ctrl+Z redoes the previous slot. Ctrl+Q aborts.\n")
    input("Press ENTER when ready...")

    with Keyboard() as kb:
        # Start with everything off
        kb.off()
        time.sleep(0.2)
        _light_only(kb, 0)
        _prompt(0)

        cal = Calibrator(kb)
        listener = pk.Listener(
            on_press=cal.on_press,
            on_release=cal.on_release,
            suppress=False,
        )
        listener.start()
        try:
            while not cal.done:
                # Detect a dead listener so we don't spin forever if it crashes
                if not listener.running:
                    print("\n[calibrate] keyboard listener stopped unexpectedly.")
                    cal.aborted = True
                    break
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n[calibrate] interrupted from terminal.")
            cal.aborted = True
        finally:
            listener.stop()

        kb.off()

    print()
    if cal.aborted:
        print(f"Aborted at slot {cal.slot}. Saving partial results.")
    else:
        print("All slots done!")

    _save_json(cal.results)
    OUTPUT_PY.write_text(_generate_keys_py(cal.results))
    print(f"Generated {OUTPUT_PY}")
    print("\nReview it, compare against k70corergb/keys.py, and replace when happy:")
    print(f"  diff k70corergb/keys.py {OUTPUT_PY.name}")
    print(f"  mv {OUTPUT_PY.name} k70corergb/keys.py")


if __name__ == "__main__":
    main()