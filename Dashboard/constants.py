import serial

# ----------------------------
# USB Identification
# ----------------------------

VID = 0x2E8A
PID = 0x8003      # Waveshare RP2040-Zero USB CDC product ID

BAUDRATE = 115200

# ----------------------------
# Firmware Commands
# ----------------------------

CMD_PING = "PING"
CMD_GET_KEY = "GETKEY"
CMD_GET_BRIGHTNESS = "GETBRIGHTNESS"
CMD_SAVE = "SAVE"
CMD_RESET = "RESET"
CMD_BOOTSEL = "BOOTSEL"

# Prefix
CMD_SET_KEY = "SETKEY:"
CMD_SET_BRIGHTNESS = "SETBRIGHTNESS:"

# ----------------------------
# Responses
# ----------------------------

RESP_READY = "READY"
RESP_OK = "OK"
RESP_ERROR = "ERROR"
RESP_PONG = "PONG"

# ----------------------------
# UI Refresh
# ----------------------------

SERIAL_TIMEOUT = 0.1
