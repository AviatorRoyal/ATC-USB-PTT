import serial

# ----------------------------
# USB Identification
# ----------------------------

VID = 0x2E8A
PID = 0xF00B      # Change if you change PID later

BAUDRATE = 115200

# ----------------------------
# Firmware Commands
# ----------------------------

CMD_PING = "PING"
CMD_GET_KEY = "GETKEY"
CMD_SAVE = "SAVE"
CMD_RESET = "RESET"
CMD_BOOTSEL = "BOOTSEL"

# Prefix
CMD_SET_KEY = "SETKEY:"

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