from pathlib import Path
import shutil, subprocess

def find_executable(configured):
    return shutil.which(configured) or (configured if Path(configured).exists() else None)

def build_command(cfg, base_dir):
    qemu = find_executable(cfg["qemu_path"])
    if not qemu: raise FileNotFoundError("QEMU não encontrado.")
    image = Path(cfg["android_image"])
    if not image.is_absolute(): image = Path(base_dir) / image
    if not image.exists(): raise FileNotFoundError(f"Imagem Android não encontrada: {image}")
    cmd = [qemu, "-m", str(cfg["memory_mb"]), "-smp", str(cfg["cpus"]),
           "-drive", f"file={image},format=raw,if=virtio", "-display", "gtk"]
    if cfg.get("network", True):
        cmd += ["-netdev", f"user,id=net0,hostfwd=tcp::{cfg['adb_port']}-:5555",
                "-device", "virtio-net-pci,netdev=net0"]
    if cfg.get("audio", True):
        cmd += ["-audiodev", "driver=dsound,id=audio0", "-device", "AC97,audiodev=audio0"]
    return cmd

def start(cfg, base_dir):
    return subprocess.Popen(build_command(cfg, base_dir), cwd=base_dir)
