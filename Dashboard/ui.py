import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from serial_manager import SerialManager
from protocol import parse
from keymap import KEYS


class SharkLiteUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SharkLite Configurator v1.0.1")
        self.root.geometry("560x500")
        self.root.resizable(False, False)

        self.statusVar = tk.StringVar(value="Disconnected")
        self.versionVar = tk.StringVar(value="-")
        self.buttonVar = tk.StringVar(value="-")
        self.keyVar = tk.StringVar(value=list(KEYS.keys())[0])
        self.brightnessVar = tk.IntVar(value=100)

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

        ttk.Label(frame,text="PTT Key").grid(row=3,column=0,sticky="w")

        self.combo = ttk.Combobox(
            frame,
            state="disabled",
            values=list(KEYS.keys()),
            textvariable=self.keyVar,
            width=25
        )
        self.combo.grid(row=3,column=1,sticky="w")

        ttk.Button(frame,text="Save",command=self.save_settings)\
            .grid(row=3,column=2,padx=5)

        ttk.Label(frame,text="LED Brightness").grid(row=4,column=0,sticky="w")

        self.brightnessSpin = ttk.Spinbox(
            frame,
            from_=0,
            to=100,
            textvariable=self.brightnessVar,
            width=6,
            state="disabled"
        )
        self.brightnessSpin.grid(row=4,column=1,sticky="w")
        ttk.Label(frame,text="% (max LED output: 80%)").grid(row=4,column=2,sticky="w")

        ttk.Separator(frame).grid(row=5,column=0,columnspan=3,sticky="ew",pady=8)

        ttk.Label(frame,text="Button").grid(row=6,column=0,sticky="w")
        ttk.Label(frame,textvariable=self.buttonVar).grid(row=6,column=1,sticky="w")

        ttk.Separator(frame).grid(row=7,column=0,columnspan=3,sticky="ew",pady=8)

        ttk.Button(frame,text="Factory Reset",command=self.factory_reset)\
            .grid(row=8,column=0,pady=5)

        ttk.Button(frame,text="Reset Device",command=self.reset_device)\
            .grid(row=8,column=1,pady=5)

        ttk.Button(frame,text="Bootloader",command=self.enter_bootloader)\
            .grid(row=8,column=2,pady=5)

        ttk.Separator(frame).grid(row=9,column=0,columnspan=3,sticky="ew",pady=8)

        self.console = tk.Text(frame,height=12,width=65,state="disabled")
        self.console.grid(row=10,column=0,columnspan=3)

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
        self.combo.configure(state="readonly")
        self.brightnessSpin.configure(state="normal")
        self.serial.send("GETINFO")

    def on_disconnect(self):
        self.root.after(0,self._disconnected)

    def _disconnected(self):
        self.statusVar.set("Disconnected")
        self.versionVar.set("-")
        self.buttonVar.set("-")
        self.combo.configure(state="disabled")
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

        self.brightnessVar.set(brightness)
        key_id=KEYS[self.keyVar.get()]
        self.serial.send(f"SETKEY:{key_id}")
        self.root.after(50,lambda:self.serial.send(f"SETBRIGHTNESS:{brightness}"))
        self.root.after(100,lambda:self.serial.send("SAVE"))

    def factory_reset(self):
        if messagebox.askyesno("Factory Reset","Restore default settings?"):
            self.serial.send("FACTORYRESET")
            self.root.after(200,lambda:self.serial.send("GETINFO"))

    def reset_device(self):
        if messagebox.askyesno("Reset Device","Restart SharkLite?"):
            self.serial.send("RESET")

    def enter_bootloader(self):
        if messagebox.askyesno("Bootloader","Enter BOOTSEL mode?"):
            self.serial.send("BOOTSEL")

    def close(self):
        self.serial.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
