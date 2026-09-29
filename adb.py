from pathlib import Path
import shutil, subprocess

def adb_path(configured):
    return shutil.which(configured) or (configured if Path(configured).exists() else None)

def connect(cfg):
    adb = adb_path(cfg["adb_path"])
    if not adb: raise FileNotFoundError("ADB não encontrado.")
    return subprocess.run([adb, "connect", f"127.0.0.1:{cfg['adb_port']}"], capture_output=True, text=True)

def install_apk(cfg, apk):
    adb = adb_path(cfg["adb_path"])
    if not adb: raise FileNotFoundError("ADB não encontrado.")
    return subprocess.run([adb, "install", "-r", str(apk)], capture_output=True, text=True, timeout=120)

def devices(cfg):
    adb = adb_path(cfg["adb_path"])
    if not adb: return ""
    return subprocess.run([adb, "devices"], capture_output=True, text=True).stdout
