import serial

# ----------------------------
# USB Identification
# ----------------------------

VID = 0x2E8A

# Waveshare RP2040-Zero product IDs (arduino-pico sets PID bits per USB class)
PIDS = (
    0x8103,       # v1.2+: serial + keyboard + joystick
    0x8003,       # v1.0.x: serial + keyboard
)

BAUDRATE = 115200

# ----------------------------
# Firmware Commands
# ----------------------------

CMD_PING = "PING"
CMD_GET_KEY = "GETKEY"
CMD_GET_BRIGHTNESS = "GETBRIGHTNESS"
CMD_GET_MODE = "GETMODE"
CMD_GET_JOY_BUTTON = "GETJOYBTN"
CMD_SAVE = "SAVE"
CMD_RESET = "RESET"
CMD_BOOTSEL = "BOOTSEL"

# Prefix
CMD_SET_KEY = "SETKEY:"
CMD_SET_BRIGHTNESS = "SETBRIGHTNESS:"
CMD_SET_MODE = "SETMODE:"
CMD_SET_JOY_BUTTON = "SETJOYBTN:"

# ----------------------------
# Output Modes
# ----------------------------

MODE_KEYBOARD = 0
MODE_JOYSTICK = 1

JOY_BUTTON_MIN = 1
JOY_BUTTON_MAX = 32

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
