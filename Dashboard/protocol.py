# protocol.py

from keymap import KEYS_REVERSE


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
