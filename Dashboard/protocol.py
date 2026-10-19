# protocol.py

from keymap import KEYS_REVERSE
from constants import MODE_KEYBOARD, MODE_JOYSTICK, JOY_BUTTON_MIN, JOY_BUTTON_MAX


def parse(message: str):
    """
    Converts firmware messages into Python dictionaries.
    """

    message = message.strip()

    # --------------------------
    # Simple replies
    # --------------------------

    if message == "READY":
        return {"type": "ready"}

    if message == "OK":
        return {"type": "ok"}

    if message == "ERROR":
        return {"type": "error"}

    if message == "PONG":
        return {"type": "pong"}

    # --------------------------
    # Button state
    # --------------------------

    if message.startswith("BTN:"):

        value = message.split(":")[1]

        return {
            "type": "button",
            "pressed": value == "1"
        }

    # --------------------------
    # Current Key
    # --------------------------

    if message.startswith("KEY:"):

        try:

            keyID = int(message.split(":")[1])

            return {
                "type": "key",
                "id": keyID,
                "name": KEYS_REVERSE.get(keyID, "Unknown")
            }

        except:

            return {
                "type": "unknown",
                "raw": message
            }

    # --------------------------
    # LED Brightness
    # --------------------------

    if message.startswith("BRIGHTNESS:"):

        try:

            brightness = int(message.split(":")[1])

            if brightness < 0 or brightness > 100:
                raise ValueError

            return {
                "type": "brightness",
                "value": brightness
            }

        except (ValueError, IndexError):

            return {
                "type": "unknown",
                "raw": message
            }

    # --------------------------
    # Output Mode
    # --------------------------

    if message.startswith("MODE:"):

        try:

            mode = int(message.split(":")[1])

            if mode not in (MODE_KEYBOARD, MODE_JOYSTICK):
                raise ValueError

            return {
                "type": "mode",
                "value": mode
            }

        except (ValueError, IndexError):

            return {
                "type": "unknown",
                "raw": message
            }

    # --------------------------
    # Joystick Button
    # --------------------------

    if message.startswith("JOYBTN:"):

        try:

            button = int(message.split(":")[1])

            if button < JOY_BUTTON_MIN or button > JOY_BUTTON_MAX:
                raise ValueError

            return {
                "type": "joybutton",
                "value": button
            }

        except (ValueError, IndexError):

            return {
                "type": "unknown",
                "raw": message
            }

    # --------------------------
    # Firmware Version
    # --------------------------

    if message.startswith("VERSION:"):

        version = message.split(":")[1]

        return {
            "type": "version",
            "version": version
        }

    # --------------------------

    return {
        "type": "unknown",
        "raw": message
    }
