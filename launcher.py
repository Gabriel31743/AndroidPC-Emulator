import json
import os
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config.json"

DEFAULTS = {
    "qemu_path": "qemu-system-x86_64",
    "adb_path": "adb",
    "android_image": "images/android.img",
    "memory_mb": 4096,
    "cpus": 4,
    "width": 1280,
    "height": 720,
    "audio": True,
    "network": True,
    "adb_port": 5555,
}

def load_config():
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return DEFAULTS.copy()

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

class EmulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AndroidPC Emulator — Prototype")
        self.geometry("760x600")
        self.minsize(700, 520)
        self.proc = None
        self.cfg = load_config()
        self._build()
        self._refresh_status()

    def _build(self):
        pad = {"padx": 10, "pady": 6}
        ttk.Label(self, text="AndroidPC Emulator", font=("Segoe UI", 20, "bold")).pack(anchor="w", **pad)
        ttk.Label(self, text="Android PC emulator prototype / QEMU + ADB").pack(anchor="w", **pad)

        box = ttk.LabelFrame(self, text="Configuração")
        box.pack(fill="x", **pad)

        self.vars = {}
        fields = [
            ("RAM (MB)", "memory_mb"),
            ("CPUs", "cpus"),
            ("Largura", "width"),
            ("Altura", "height"),
            ("Porta ADB", "adb_port"),
        ]
        for row, (label, key) in enumerate(fields):
            ttk.Label(box, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
            v = tk.StringVar(value=str(self.cfg[key]))
            self.vars[key] = v
            ttk.Entry(box, textvariable=v, width=18).grid(row=row, column=1, sticky="w", padx=8, pady=4)

        self.audio_var = tk.BooleanVar(value=self.cfg["audio"])
        self.network_var = tk.BooleanVar(value=self.cfg["network"])
        ttk.Checkbutton(box, text="Áudio", variable=self.audio_var).grid(row=0, column=2, padx=12)
        ttk.Checkbutton(box, text="Rede", variable=self.network_var).grid(row=1, column=2, padx=12)

        ttk.Label(box, text="Imagem Android").grid(row=2, column=2, sticky="w", padx=8)
        self.image_var = tk.StringVar(value=self.cfg["android_image"])
        ttk.Entry(box, textvariable=self.image_var, width=28).grid(row=3, column=2, padx=8)
        ttk.Button(box, text="Procurar", command=self.choose_image).grid(row=4, column=2, padx=8, pady=4)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", **pad)
        ttk.Button(buttons, text="Salvar configuração", command=self.save).pack(side="left", padx=4)
        ttk.Button(buttons, text="Iniciar Android", command=self.start).pack(side="left", padx=4)
        ttk.Button(buttons, text="Reiniciar", command=self.restart).pack(side="left", padx=4)
        ttk.Button(buttons, text="Desligar", command=self.stop).pack(side="left", padx=4)
        ttk.Button(buttons, text="Instalar APK", command=self.install_apk).pack(side="left", padx=4)

        self.status = tk.StringVar(value="Verificando ferramentas...")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", **pad)

        logbox = ttk.LabelFrame(self, text="Log")
        logbox.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(logbox, height=15, wrap="word")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def log_msg(self, msg):
        self.after(0, lambda: (self.log.insert("end", msg + "\n"), self.log.see("end")))

    def choose_image(self):
        path = filedialog.askopenfilename(title="Selecionar imagem Android")
        if path:
            try:
                self.image_var.set(str(Path(path).resolve().relative_to(BASE.resolve())).replace("\\", "/"))
            except ValueError:
                self.image_var.set(path)

    def save(self):
        try:
            cfg = {
                **self.cfg,
                "memory_mb": int(self.vars["memory_mb"].get()),
                "cpus": int(self.vars["cpus"].get()),
                "width": int(self.vars["width"].get()),
                "height": int(self.vars["height"].get()),
                "adb_port": int(self.vars["adb_port"].get()),
                "audio": self.audio_var.get(),
                "network": self.network_var.get(),
                "android_image": self.image_var.get(),
            }
            save_config(cfg)
            self.cfg = cfg
            self.log_msg("Configuração salva.")
        except ValueError:
            messagebox.showerror("Configuração", "RAM, CPUs, resolução e porta devem ser números.")

    def _tool(self, name):
        configured = self.cfg.get(name, name)
        return shutil.which(configured) or configured

    def _refresh_status(self):
        q = self._tool("qemu_path")
        a = self._tool("adb_path")
        q_ok = shutil.which(q) is not None or Path(q).exists()
        a_ok = shutil.which(a) is not None or Path(a).exists()
        self.status.set(f"QEMU: {'OK' if q_ok else 'não encontrado'}   |   ADB: {'OK' if a_ok else 'não encontrado'}")

    def start(self):
        if self.proc and self.proc.poll() is None:
            self.log_msg("O emulador já está em execução.")
            return
        self.save()
        image = Path(self.cfg["android_image"])
        if not image.is_absolute():
            image = BASE / image
        if not image.exists():
            messagebox.showerror("Imagem Android", f"Imagem não encontrada:\n{image}")
            self.log_msg("Coloque uma imagem Android x86_64 em images/ e ajuste config.json.")
            return

        qemu = self._tool("qemu_path")
        cmd = [
            qemu, "-m", str(self.cfg["memory_mb"]),
            "-smp", str(self.cfg["cpus"]),
            "-drive", f"file={image},format=raw,if=virtio",
            "-display", "gtk",
            "-serial", "mon:stdio",
        ]
        if self.cfg["network"]:
            cmd += ["-netdev", f"user,id=net0,hostfwd=tcp::{self.cfg['adb_port']}-:5555",
                    "-device", "virtio-net-pci,netdev=net0"]
        if self.cfg["audio"]:
            cmd += ["-audiodev", "driver=dsound,id=audio0", "-device", "AC97,audiodev=audio0"]

        self.log_msg("Iniciando: " + " ".join(map(str, cmd)))
        try:
            self.proc = subprocess.Popen(cmd, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            threading.Thread(target=self._read_output, daemon=True).start()
        except Exception as e:
            messagebox.showerror("QEMU", str(e))
            self.log_msg(f"Erro ao iniciar QEMU: {e}")

    def _read_output(self):
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            self.log_msg(line.rstrip())
        self.log_msg("QEMU encerrou.")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.log_msg("Solicitado desligamento do emulador.")
        else:
            self.log_msg("Nenhum emulador em execução.")

    def restart(self):
        self.stop()
        self.after(1200, self.start)

    def install_apk(self):
        adb = self._tool("adb_path")
        apk = filedialog.askopenfilename(title="Selecionar APK", filetypes=[("APK", "*.apk")])
        if not apk:
            return
        try:
            result = subprocess.run([adb, "connect", f"127.0.0.1:{self.cfg['adb_port']}"], capture_output=True, text=True, timeout=10)
            self.log_msg(result.stdout.strip() or result.stderr.strip())
            result = subprocess.run([adb, "install", "-r", apk], capture_output=True, text=True, timeout=120)
            self.log_msg(result.stdout.strip() or result.stderr.strip())
            if result.returncode == 0:
                messagebox.showinfo("APK", "APK instalado com sucesso.")
            else:
                messagebox.showerror("APK", result.stderr or "Falha na instalação.")
        except Exception as e:
            messagebox.showerror("ADB", str(e))

if __name__ == "__main__":
    EmulatorApp().mainloop()
