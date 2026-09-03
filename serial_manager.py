import threading
import time

import serial
import serial.tools.list_ports

from constants import *


class SerialManager:

    def __init__(self):

        self.ser = None

        self.running = True

        self.connected = False

        self.thread = threading.Thread(
            target=self.worker,
            daemon=True
        )

        self.thread.start()

        self.on_message = None
        self.on_connect = None
        self.on_disconnect = None

    # ------------------------------------------------

    def find_device(self):

        for port in serial.tools.list_ports.comports():

            if port.vid == VID and port.pid == PID:
                return port.device

        return None

    # ------------------------------------------------

    def connect(self):

        if self.connected:
            return True

        port = self.find_device()

        if port is None:
            return False

        try:

            self.ser = serial.Serial(
                port,
                BAUDRATE,
                timeout=SERIAL_TIMEOUT
            )

            self.connected = True

            print("Connected:", port)

            if self.on_connect:
                self.on_connect()

            return True

        except Exception as e:

            print(e)

            self.connected = False

            return False

    # ------------------------------------------------

    def disconnect(self):

        if self.ser:

            try:
                self.ser.close()
            except:
                pass

        self.ser = None

        if self.connected:

            self.connected = False

            print("Disconnected")

            if self.on_disconnect:
                self.on_disconnect()

    # ------------------------------------------------

    def send(self, text):

        if not self.connected:
            return False

        try:

            self.ser.write((text + "\n").encode())

            return True

        except:

            self.disconnect()

            return False

    # ------------------------------------------------

    def worker(self):

        while self.running:

            # -------------------------
            # Try reconnecting
            # -------------------------

            if not self.connected:

                self.connect()

                time.sleep(1)

                continue

            # -------------------------
            # Read serial
            # -------------------------

            try:

                line = self.ser.readline()

                if not line:
                    continue

                line = line.decode(errors="ignore").strip()

                if line:

                    print("RX:", line)

                    if self.on_message:
                        self.on_message(line)

            except:

                self.disconnect()

    # ------------------------------------------------

    def close(self):

        self.running = False

        self.disconnect()

        self.thread.join(timeout=2)