# firmware_updater.py
#
# Flashes a .uf2 file without touching the BOOT button: the device is sent to its
# UF2 bootloader over USB serial, then the file is copied to the RPI-RP2 drive.

import glob
import os
import string
import struct
import sys
import threading
import time


UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FLAG_FAMILY_ID = 0x00002000
UF2_BLOCK_SIZE = 512

RP2040_FAMILY_ID = 0xE48BFF56

BOOTLOADER_LABEL = "RPI-RP2"

BOOTSEL_TIMEOUT = 6         # seconds to wait for the drive after the BOOTSEL command
TOUCH_TIMEOUT = 10          # ... after the 1200 baud touch
MANUAL_TIMEOUT = 60         # ... when the user has to hold BOOT and plug in
RECONNECT_TIMEOUT = 15      # seconds to wait for the new firmware to come back


def check_uf2(path):
    """
    Checks that the file is a complete RP2040 UF2 image.
    Returns the number of blocks, or raises ValueError with a readable reason.
    """

    with open(path, "rb") as f:
        data = f.read()

    if not data or len(data) % UF2_BLOCK_SIZE:
        raise ValueError("This is not a valid .uf2 file (wrong size).")

    count = len(data) // UF2_BLOCK_SIZE

    for i in range(count):

        block = data[i * UF2_BLOCK_SIZE:(i + 1) * UF2_BLOCK_SIZE]

        magic0, magic1, flags, _, _, _, total, family = struct.unpack_from("<8I", block)
        magic_end, = struct.unpack_from("<I", block, UF2_BLOCK_SIZE - 4)

        if magic0 != UF2_MAGIC_START0 or magic1 != UF2_MAGIC_START1 or magic_end != UF2_MAGIC_END:
            raise ValueError("This is not a valid .uf2 file (bad block header).")

        if not (flags & UF2_FLAG_FAMILY_ID) or family != RP2040_FAMILY_ID:
            raise ValueError("This .uf2 file is not built for the RP2040.")

        if total != count:
            raise ValueError("This .uf2 file is incomplete.")

    return count


def find_bootloader_drive():
    """
    Returns the mount path of a connected RPI-RP2 bootloader drive, or None.
    """

    if sys.platform == "win32":

        import ctypes

        kernel32 = ctypes.windll.kernel32

        # Don't let Windows pop "insert a disk" dialogs for empty card readers.
        SEM_FAILCRITICALERRORS = 0x0001
        old_mode = kernel32.SetErrorMode(SEM_FAILCRITICALERRORS)

        try:

            mask = kernel32.GetLogicalDrives()

            for i, letter in enumerate(string.ascii_uppercase):

                if not mask & (1 << i):
                    continue

                root = f"{letter}:\\"

                if is_bootloader_drive(root):
                    return root

        finally:

            kernel32.SetErrorMode(old_mode)

        return None

    patterns = [
        f"/Volumes/{BOOTLOADER_LABEL}",
        f"/media/*/{BOOTLOADER_LABEL}",
        f"/run/media/*/{BOOTLOADER_LABEL}",
    ]

    for pattern in patterns:
        for root in glob.glob(pattern):
            if is_bootloader_drive(root):
                return root

    return None


def is_bootloader_drive(root):

    try:

        with open(os.path.join(root, "INFO_UF2.TXT"), encoding="ascii", errors="ignore") as f:
            return BOOTLOADER_LABEL in f.read()

    except OSError:

        return False


def wait_for(condition, timeout):

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        result = condition()

        if result:
            return result

        time.sleep(0.25)

    return None


class FirmwareUpdater:
    """
    Runs one update in a background thread.

    on_log(message) and on_done(success, message) are called from that thread,
    so the UI must hand them over to its own thread.
    """

    def __init__(self, serial_manager, path, on_log, on_done):

        self.serial = serial_manager
        self.path = path
        self.on_log = on_log
        self.on_done = on_done

    def start(self):

        threading.Thread(target=self.run, daemon=True).start()

    def run(self):

        try:

            self.on_done(*self.update())

        except Exception as e:

            self.on_done(False, f"Update failed: {e}")

    def update(self):

        name = os.path.basename(self.path)

        check_uf2(self.path)

        drive = find_bootloader_drive()

        if drive:

            self.on_log(f"Bootloader drive already at {drive}")

        elif self.serial.connected:

            self.on_log("Sending device to bootloader...")
            self.serial.send("BOOTSEL")

            drive = wait_for(find_bootloader_drive, BOOTSEL_TIMEOUT)

            if not drive:

                self.on_log("No response, trying 1200 baud reset...")
                self.serial.touch_1200()

                drive = wait_for(find_bootloader_drive, TOUCH_TIMEOUT)

        else:

            self.on_log("No device connected.")
            self.on_log("Hold the BOOT button and plug in the device...")

            drive = wait_for(find_bootloader_drive, MANUAL_TIMEOUT)

        if not drive:
            return False, (
                f"The {BOOTLOADER_LABEL} drive did not appear.\n\n"
                "Hold the BOOT button while plugging in the device, "
                "then click Update Firmware again."
            )

        self.on_log(f"Copying {name} to {drive}...")

        size = os.path.getsize(self.path)
        written = 0

        try:

            with open(self.path, "rb") as src, open(os.path.join(drive, name), "wb") as dst:

                while True:

                    chunk = src.read(64 * 1024)

                    if not chunk:
                        break

                    dst.write(chunk)
                    written += len(chunk)

                dst.flush()
                os.fsync(dst.fileno())

        except OSError:

            # The RP2040 reboots as soon as it has the last block, which can
            # pull the drive away before the file is closed. That is a success.
            if written < size:
                raise

        self.on_log("Firmware copied, device restarting...")

        wait_for(lambda: not find_bootloader_drive(), RECONNECT_TIMEOUT)

        if wait_for(lambda: self.serial.connected, RECONNECT_TIMEOUT):
            return True, "Firmware updated successfully."

        return True, (
            "Firmware was copied, but the device has not reconnected yet.\n\n"
            "If it does not appear, unplug it and plug it back in."
        )
