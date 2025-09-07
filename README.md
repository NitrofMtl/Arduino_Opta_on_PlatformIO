# Arduino Opta with PlatformIO (DFU Upload)

This guide explains how to use the Arduino Opta inside PlatformIO with DFU auto-upload, just like in Arduino IDE (no need to manually double-reset into bootloader).

---

## 0. Prerequisites

- Install **Arduino IDE 2.x** (or Arduino CLI).
- Open Arduino IDE → Boards Manager → Install "Arduino Mbed OS Opta" core.
- This ensures that the `opta` board definition and DFU tools are present on your system.

---

## 1. Install Arduino Opta Core in PlatformIO

Add the Arduino-provided board core to your PlatformIO configuration. In your global platformio.ini (or project), include:

Example:
```
pio pkg install -p framework-arduino-mbed
```

## 2. Create a New Project for Opta

Open VS Code with the PlatformIO extension.

Create a new project, select Arduino Opta as the board.

Confirm the default framework = arduino.

## 3. Edit platformio.ini

Keep only your opta environment and add a custom upload setup that points to Arduino’s DFU utility.

Example:
```
[env:opta]
platform = ststm32
board = opta
framework = arduino

; --- Use Arduino’s dfu-util instead of PIO’s ---
upload_protocol = custom
upload_command  = ${sysenv.LOCALAPPDATA}/Arduino15/packages/arduino/tools/dfu-util/0.10.0-arduino1/dfu-util --device=2341:0364 -a 0 -D $SOURCE --dfuse-address=0x08040000:leave

extra_scripts = pre:extra_scripts/pre_upload.py

```

## 4. Add extra_script.py

```
import os, time
import serial.tools.list_ports

Import("env")

# VID/PID pairs
VID_NORMAL, PID_NORMAL = "2341", "0164"
VID_DFU, PID_DFU = "2341", "0364"

def find_ports(vid, pid):
    return [p.device for p in serial.tools.list_ports.comports() if f"VID:PID={vid}:{pid}" in p.hwid]

def before_upload(source, target, env):
    normal = find_ports(VID_NORMAL, PID_NORMAL)
    dfu = find_ports(VID_DFU, PID_DFU)

    if dfu:
        print("✅ Opta already in DFU mode")
        return

    if normal:
        port = normal[0]
        print(f"🔎 Found Opta runtime on {port} — sending 1200bps touch...")
        try:
            import serial
            with serial.Serial(port, 1200) as s:
                pass
        except Exception as e:
            print(f"⚠️ Could not toggle {port}: {e}")
        time.sleep(2)
    else:
        print("❌ No Opta device found (neither runtime nor DFU)")
        env.Exit(1)

    # Wait for DFU device
    for _ in range(10):
        dfu = find_ports(VID_DFU, PID_DFU)
        if dfu:
            print("✅ Opta entered DFU mode")
            return
        time.sleep(1)

    print("❌ Timeout: Opta did not enter DFU mode")
    env.Exit(1)

def after_upload(source, target, env):
    print("🎉 Upload complete — resetting Opta...")

env.AddPreAction("upload", before_upload)
env.AddPostAction("upload", after_upload)

```

## 5. Build & Upload

Use:

```
pio run -t upload
```

The Opta will automatically switch to bootloader and upload (no double-reset required).


✅ That’s it! You now have a working Opta workflow in PlatformIO using Arduino’s DFU tools.

## Notes

Arduino IDE (or CLI) installation is mandatory.

If Arduino updates the core, you may need to adjust the dfu-util version number in the script.

PlatformIO’s built-in dfu-util is not compatible with Opta auto-upload, so we use Arduino’s version.
