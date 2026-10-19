import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from serial_manager import SerialManager
from firmware_updater import FirmwareUpdater, check_uf2
from protocol import parse
from keymap import KEYS
from constants import MODE_KEYBOARD, MODE_JOYSTICK, JOY_BUTTON_MIN, JOY_BUTTON_MAX


class SharkLiteUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SharkLite Configurator v1.2.0")
        self.root.geometry("560x530")
        self.root.resizable(False, False)

        self.statusVar = tk.StringVar(value="Disconnected")
        self.versionVar = tk.StringVar(value="-")
        self.buttonVar = tk.StringVar(value="-")
        self.keyVar = tk.StringVar(value=list(KEYS.keys())[0])
        self.brightnessVar = tk.IntVar(value=100)
        self.modeVar = tk.IntVar(value=MODE_KEYBOARD)
        self.joyButtonVar = tk.IntVar(value=JOY_BUTTON_MIN)
        self.outputLabelVar = tk.StringVar(value="PTT Key")

        # Set once the firmware reports MODE: (v1.2+); older firmware is keyboard-only.
        self.supportsJoystick = False

        self.serial = SerialManager()
        self.serial.on_connect = self.on_connect
        self.serial.on_disconnect = self.on_disconnect
        self.serial.on_message = self.on_message

        self.build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Status").grid(row=0,column=0,sticky="w")
        ttk.Label(frame,textvariable=self.statusVar).grid(row=0,column=1,sticky="w")

        ttk.Label(frame,text="Firmware").grid(row=1,column=0,sticky="w")
        ttk.Label(frame,textvariable=self.versionVar).grid(row=1,column=1,sticky="w")

        ttk.Separator(frame).grid(row=2,column=0,columnspan=3,sticky="ew",pady=8)

        ttk.Label(frame,text="Output").grid(row=3,column=0,sticky="w")

        modeFrame = ttk.Frame(frame)
        modeFrame.grid(row=3,column=1,columnspan=2,sticky="w")

        self.keyboardRadio = ttk.Radiobutton(
            modeFrame,
            text="Keyboard",
            variable=self.modeVar,
            value=MODE_KEYBOARD,
            command=self.update_output_widgets,
            state="disabled"
        )
        self.keyboardRadio.pack(side="left")

        self.joystickRadio = ttk.Radiobutton(
            modeFrame,
            text="Joystick",
            variable=self.modeVar,
            value=MODE_JOYSTICK,
            command=self.update_output_widgets,
            state="disabled"
        )
        self.joystickRadio.pack(side="left",padx=(15,0))

        ttk.Label(frame,textvariable=self.outputLabelVar).grid(row=4,column=0,sticky="w")

        self.combo = ttk.Combobox(
            frame,
            state="disabled",
            values=list(KEYS.keys()),
            textvariable=self.keyVar,
            width=25
        )
        self.combo.grid(row=4,column=1,sticky="w")

        # Shares the key combobox's grid cell; update_output_widgets() swaps them.
        self.joySpin = ttk.Spinbox(
            frame,
            from_=JOY_BUTTON_MIN,
            to=JOY_BUTTON_MAX,
            textvariable=self.joyButtonVar,
            width=6,
            state="disabled"
        )
        self.joySpin.grid(row=4,column=1,sticky="w")
        self.joySpin.grid_remove()

        ttk.Button(frame,text="Save",command=self.save_settings)\
            .grid(row=4,column=2,padx=5)

        ttk.Label(frame,text="LED Brightness").grid(row=5,column=0,sticky="w")

        self.brightnessSpin = ttk.Spinbox(
            frame,
            from_=0,
            to=100,
            textvariable=self.brightnessVar,
            width=6,
            state="disabled"
        )
        self.brightnessSpin.grid(row=5,column=1,sticky="w")
        ttk.Label(frame,text="% (max LED output: 80%)").grid(row=5,column=2,sticky="w")

        ttk.Separator(frame).grid(row=6,column=0,columnspan=3,sticky="ew",pady=8)

        ttk.Label(frame,text="Button").grid(row=7,column=0,sticky="w")
        ttk.Label(frame,textvariable=self.buttonVar).grid(row=7,column=1,sticky="w")

        ttk.Separator(frame).grid(row=8,column=0,columnspan=3,sticky="ew",pady=8)

        ttk.Button(frame,text="Factory Reset",command=self.factory_reset)\
            .grid(row=9,column=0,pady=5)

        ttk.Button(frame,text="Reset Device",command=self.reset_device)\
            .grid(row=9,column=1,pady=5)

        self.updateButton = ttk.Button(frame,text="Update Firmware",command=self.update_firmware)
        self.updateButton.grid(row=9,column=2,pady=5)

        ttk.Separator(frame).grid(row=10,column=0,columnspan=3,sticky="ew",pady=8)

        self.console = tk.Text(frame,height=12,width=65,state="disabled")
        self.console.grid(row=11,column=0,columnspan=3)

    def update_output_widgets(self):
        connected = self.serial.connected
        joystick = self.supportsJoystick and self.modeVar.get() == MODE_JOYSTICK

        radioState = "normal" if connected and self.supportsJoystick else "disabled"
        self.keyboardRadio.configure(state=radioState)
        self.joystickRadio.configure(state=radioState)

        if joystick:
            self.outputLabelVar.set("Joystick Button")
            self.combo.grid_remove()
            self.joySpin.grid()
            self.joySpin.configure(state="normal" if connected else "disabled")
        else:
            self.outputLabelVar.set("PTT Key")
            self.joySpin.grid_remove()
            self.combo.grid()
            self.combo.configure(state="readonly" if connected else "disabled")

    def log(self,msg):
        ts=datetime.now().strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert("end",f"[{ts}] {msg}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def on_connect(self):
        self.root.after(0,self._connected)

    def _connected(self):
        self.statusVar.set("Connected")
        self.supportsJoystick = False
        self.modeVar.set(MODE_KEYBOARD)
        self.update_output_widgets()
        self.brightnessSpin.configure(state="normal")
        self.serial.send("GETINFO")

    def on_disconnect(self):
        self.root.after(0,self._disconnected)

    def _disconnected(self):
        self.statusVar.set("Disconnected")
        self.versionVar.set("-")
        self.buttonVar.set("-")
        self.update_output_widgets()
        self.brightnessSpin.configure(state="disabled")

    def on_message(self,line):
        self.root.after(0,lambda:self.process(line))

    def process(self,line):
        self.log(line)

        pkt=parse(line)
        t=pkt["type"]

        if t=="button":
            self.buttonVar.set("Pressed" if pkt["pressed"] else "Released")

        elif t=="key":
            self.keyVar.set(pkt["name"])

        elif t=="brightness":
            self.brightnessVar.set(pkt["value"])

        elif t=="mode":
            self.supportsJoystick = True
            self.modeVar.set(pkt["value"])
            self.update_output_widgets()

        elif t=="joybutton":
            self.joyButtonVar.set(pkt["value"])

        elif t=="version":
            self.versionVar.set(pkt["version"])

        elif t=="unknown":
            self.log("Unknown packet")

    def save_settings(self):
        try:
            brightness = int(self.brightnessSpin.get())

            if brightness < 0 or brightness > 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Brightness", "Enter a whole number from 0 to 100.")
            return

        commands = []

        if self.supportsJoystick:
            try:
                joy_button = int(self.joySpin.get())

                if joy_button < JOY_BUTTON_MIN or joy_button > JOY_BUTTON_MAX:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Joystick Button",
                    f"Enter a whole number from {JOY_BUTTON_MIN} to {JOY_BUTTON_MAX}."
                )
                return

            self.joyButtonVar.set(joy_button)
            commands.append(f"SETMODE:{self.modeVar.get()}")
            commands.append(f"SETJOYBTN:{joy_button}")

        self.brightnessVar.set(brightness)
        key_id=KEYS[self.keyVar.get()]
        commands.append(f"SETKEY:{key_id}")
        commands.append(f"SETBRIGHTNESS:{brightness}")
        commands.append("SAVE")

        for i, cmd in enumerate(commands):
            self.root.after(i * 50, lambda cmd=cmd: self.serial.send(cmd))

    def factory_reset(self):
        if messagebox.askyesno("Factory Reset","Restore default settings?"):
            self.serial.send("FACTORYRESET")
            self.root.after(200,lambda:self.serial.send("GETINFO"))

    def reset_device(self):
        if messagebox.askyesno("Reset Device","Restart SharkLite?"):
            self.serial.send("RESET")

    def update_firmware(self):
        path = filedialog.askopenfilename(
            title="Select firmware",
            filetypes=[("UF2 firmware","*.uf2"),("All files","*.*")]
        )

        if not path:
            return

        try:
            check_uf2(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Update Firmware", str(e))
            return

        name = os.path.basename(path)

        if self.serial.connected:
            prompt = f"Flash {name}?\n\nThe device will restart into the bootloader and update automatically."
        else:
            prompt = (f"Flash {name}?\n\nNo device is connected. After you click Yes, "
                      "hold the BOOT button while plugging in the device.")

        if not messagebox.askyesno("Update Firmware", prompt):
            return

        self.updateButton.configure(state="disabled", text="Updating...")
        self.log(f"Firmware update: {name}")

        FirmwareUpdater(
            self.serial,
            path,
            on_log=lambda msg: self.root.after(0, lambda: self.log(msg)),
            on_done=lambda ok, msg: self.root.after(0, lambda: self.update_finished(ok, msg))
        ).start()

    def update_finished(self, ok, msg):
        self.updateButton.configure(state="normal", text="Update Firmware")
        self.log(msg.split("\n")[0])

        if ok:
            messagebox.showinfo("Update Firmware", msg)
        else:
            messagebox.showerror("Update Firmware", msg)

    def close(self):
        self.serial.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
