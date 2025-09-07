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
