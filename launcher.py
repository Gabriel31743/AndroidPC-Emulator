import json
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from google_games import GoogleGames


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
            data = json.loads(
                CONFIG_PATH.read_text(encoding="utf-8")
            )
            return {**DEFAULTS, **data}
        except Exception:
            pass

    return DEFAULTS.copy()


def save_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2),
        encoding="utf-8"
    )


class EmulatorApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("AndroidPC Emulator")
        self.geometry("800x650")
        self.minsize(720, 560)

        self.proc = None
        self.cfg = load_config()

        self.google = GoogleGames(
            adb_path=self.cfg["adb_path"],
            device=f"127.0.0.1:{self.cfg['adb_port']}"
        )

        self._build()
        self._refresh_status()

    def _build(self):

        pad = {"padx": 10, "pady": 6}

        ttk.Label(
            self,
            text="AndroidPC Emulator",
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", **pad)

        ttk.Label(
            self,
            text="Emulador Android com QEMU + ADB + Google Play"
        ).pack(anchor="w", **pad)

        box = ttk.LabelFrame(
            self,
            text="Configuração"
        )
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

            ttk.Label(
                box,
                text=label
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=8,
                pady=4
            )

            value = tk.StringVar(
                value=str(self.cfg[key])
            )

            self.vars[key] = value

            ttk.Entry(
                box,
                textvariable=value,
                width=18
            ).grid(
                row=row,
                column=1,
                sticky="w",
                padx=8,
                pady=4
            )

        self.audio_var = tk.BooleanVar(
            value=self.cfg["audio"]
        )

        self.network_var = tk.BooleanVar(
            value=self.cfg["network"]
        )

        ttk.Checkbutton(
            box,
            text="Áudio",
            variable=self.audio_var
        ).grid(
            row=0,
            column=2,
            padx=12
        )

        ttk.Checkbutton(
            box,
            text="Rede",
            variable=self.network_var
        ).grid(
            row=1,
            column=2,
            padx=12
        )

        ttk.Label(
            box,
            text="Imagem Android"
        ).grid(
            row=2,
            column=2,
            sticky="w",
            padx=8
        )

        self.image_var = tk.StringVar(
            value=self.cfg["android_image"]
        )

        ttk.Entry(
            box,
            textvariable=self.image_var,
            width=28
        ).grid(
            row=3,
            column=2,
            padx=8
        )

        ttk.Button(
            box,
            text="Procurar",
            command=self.choose_image
        ).grid(
            row=4,
            column=2,
            padx=8,
            pady=4
        )

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", **pad)

        ttk.Button(
            buttons,
            text="Salvar configuração",
            command=self.save
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Iniciar Android",
            command=self.start
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Reiniciar",
            command=self.restart
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Desligar",
            command=self.stop
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Instalar APK",
            command=self.install_apk
        ).pack(side="left", padx=4)

        google_box = ttk.LabelFrame(
            self,
            text="Google Play / Jogos"
        )

        google_box.pack(
            fill="x",
            **pad
        )

        ttk.Button(
            google_box,
            text="Conectar ADB",
            command=self.connect_adb
        ).pack(
            side="left",
            padx=5,
            pady=5
        )

        ttk.Button(
            google_box,
            text="Verificar Google Play",
            command=self.check_google_play
        ).pack(
            side="left",
            padx=5,
            pady=5
        )

        ttk.Button(
            google_box,
            text="Abrir Play Store",
            command=self.open_play_store
        ).pack(
            side="left",
            padx=5,
            pady=5
        )

        ttk.Button(
            google_box,
            text="Abrir Play Games",
            command=self.open_google_games
        ).pack(
            side="left",
            padx=5,
            pady=5
        )

        self.status = tk.StringVar(
            value="Verificando ferramentas..."
        )

        ttk.Label(
            self,
            textvariable=self.status
        ).pack(
            anchor="w",
            **pad
        )

        logbox = ttk.LabelFrame(
            self,
            text="Log"
        )

        logbox.pack(
            fill="both",
            expand=True,
            **pad
        )

        self.log = tk.Text(
            logbox,
            height=15,
            wrap="word"
        )

        self.log.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=6
        )

    def log_msg(self, msg):

        self.after(
            0,
            lambda: (
                self.log.insert("end", msg + "\n"),
                self.log.see("end")
            )
        )

    def choose_image(self):

        path = filedialog.askopenfilename(
            title="Selecionar imagem Android"
        )

        if path:

            try:

                relative = Path(
                    path
                ).resolve().relative_to(
                    BASE.resolve()
                )

                self.image_var.set(
                    str(relative).replace("\\", "/")
                )

            except ValueError:

                self.image_var.set(path)

    def save(self):

        try:

            cfg = {
                **self.cfg,
                "memory_mb": int(
                    self.vars["memory_mb"].get()
                ),
                "cpus": int(
                    self.vars["cpus"].get()
                ),
                "width": int(
                    self.vars["width"].get()
                ),
                "height": int(
                    self.vars["height"].get()
                ),
                "adb_port": int(
                    self.vars["adb_port"].get()
                ),
                "audio": self.audio_var.get(),
                "network": self.network_var.get(),
                "android_image": self.image_var.get(),
            }

            save_config(cfg)

            self.cfg = cfg

            self.google = GoogleGames(
                adb_path=self.cfg["adb_path"],
                device=f"127.0.0.1:{self.cfg['adb_port']}"
            )

            self.log_msg(
                "Configuração salva."
            )

        except ValueError:

            messagebox.showerror(
                "Configuração",
                "RAM, CPUs, resolução e porta devem ser números."
            )

    def _tool(self, name):

        configured = self.cfg.get(
            name,
            name
        )

        return (
            shutil.which(configured)
            or configured
        )

    def _refresh_status(self):

        qemu = self._tool("qemu_path")
        adb = self._tool("adb_path")

        qemu_ok = (
            shutil.which(qemu) is not None
            or Path(qemu).exists()
        )

        adb_ok = (
            shutil.which(adb) is not None
            or Path(adb).exists()
        )

        self.status.set(
            f"QEMU: {'OK' if qemu_ok else 'não encontrado'}"
            f"   |   ADB: {'OK' if adb_ok else 'não encontrado'}"
        )

    def start(self):

        if self.proc and self.proc.poll() is None:

            self.log_msg(
                "O emulador já está em execução."
            )

            return

        self.save()

        image = Path(
            self.cfg["android_image"]
        )

        if not image.is_absolute():
            image = BASE / image

        if not image.exists():

            messagebox.showerror(
                "Imagem Android",
                f"Imagem não encontrada:\n{image}"
            )

            self.log_msg(
                "Coloque uma imagem Android x86_64 em "
                "images/ e ajuste config.json."
            )

            return

        qemu = self._tool(
            "qemu_path"
        )

        cmd = [
            qemu,
            "-m",
            str(self.cfg["memory_mb"]),
            "-smp",
            str(self.cfg["cpus"]),
            "-drive",
            f"file={image},format=raw,if=virtio",
            "-display",
            "gtk",
            "-serial",
            "mon:stdio",
        ]

        if self.cfg["network"]:

            cmd += [
                "-netdev",
                f"user,id=net0,"
                f"hostfwd=tcp::{self.cfg['adb_port']}-:5555",
                "-device",
                "virtio-net-pci,netdev=net0"
            ]

        if self.cfg["audio"]:

            cmd += [
                "-audiodev",
                "driver=dsound,id=audio0",
                "-device",
                "AC97,audiodev=audio0"
            ]

        self.log_msg(
            "Iniciando: "
            + " ".join(map(str, cmd))
        )

        try:

            self.proc = subprocess.Popen(
                cmd,
                cwd=BASE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            threading.Thread(
                target=self._read_output,
                daemon=True
            ).start()

        except Exception as error:

            messagebox.showerror(
                "QEMU",
                str(error)
            )

            self.log_msg(
                f"Erro ao iniciar QEMU: {error}"
            )

    def _read_output(self):

        if not self.proc:
            return

        if not self.proc.stdout:
            return

        for line in self.proc.stdout:

            self.log_msg(
                line.rstrip()
            )

        self.log_msg(
            "QEMU encerrou."
        )

    def stop(self):

        if self.proc and self.proc.poll() is None:

            self.proc.terminate()

            self.log_msg(
                "Solicitado desligamento do emulador."
            )

        else:

            self.log_msg(
                "Nenhum emulador em execução."
            )

    def restart(self):

        self.stop()

        self.after(
            1200,
            self.start
        )

    def connect_adb(self):

        try:

            result = self.google.connect()

            output = (
                result.stdout.strip()
                or result.stderr.strip()
            )

            if result.returncode == 0:

                self.status.set(
                    "ADB: conectado"
                )

                self.log_msg(
                    output or "ADB conectado."
                )

            else:

                self.status.set(
                    "ADB: erro"
                )

                self.log_msg(
                    output or "Falha ao conectar ADB."
                )

                messagebox.showwarning(
                    "ADB",
                    output or "Não foi possível conectar."
                )

        except Exception as error:

            messagebox.showerror(
                "ADB",
                str(error)
            )

    def check_google_play(self):

        try:

            self.google.connect()

            info = self.google.device_info()

            self.log_msg(
                f"Android: {info['android_version']}"
            )

            self.log_msg(
                f"Arquitetura: {info['architecture']}"
            )

            if info["google_play"]:

                self.log_msg(
                    "Google Play encontrado."
                )

                messagebox.showinfo(
                    "Google Play",
                    "Google Play foi encontrado."
                )

            else:

                self.log_msg(
                    "Google Play não encontrado."
                )

                messagebox.showwarning(
                    "Google Play",
                    "Google Play não foi encontrado nessa imagem Android."
                )

        except Exception as error:

            self.log_msg(
                f"Erro Google Play: {error}"
            )

            messagebox.showerror(
                "Google Play",
                str(error)
            )

    def open_play_store(self):

        try:

            self.google.connect()

            if not self.google.check_connection():

                messagebox.showwarning(
                    "Play Store",
                    "O Android não está conectado pelo ADB."
                )

                return

            if not self.google.has_google_play():

                messagebox.showwarning(
                    "Play Store",
                    "Google Play não foi encontrado no Android."
                )

                return

            result = self.google.open_play_store()

            output = (
                result.stdout.strip()
                or result.stderr.strip()
                or "Play Store aberta."
            )

            self.log_msg(output)

        except Exception as error:

            self.log_msg(
                f"Erro ao abrir Play Store: {error}"
            )

            messagebox.showerror(
                "Play Store",
                str(error)
            )

    def open_google_games(self):

        try:

            self.google.connect()

            if not self.google.check_connection():

                messagebox.showwarning(
                    "Google Play Games",
                    "O Android não está conectado pelo ADB."
                )

                return

            result = self.google.open_google_games()

            if result is None:

                messagebox.showwarning(
                    "Google Play Games",
                    "Google Play Games não está instalado."
                )

                self.log_msg(
                    "Google Play Games não encontrado."
                )

                return

            output = (
                result.stdout.strip()
                or result.stderr.strip()
                or "Google Play Games aberto."
            )

            self.log_msg(output)

        except Exception as error:

            self.log_msg(
                f"Erro ao abrir Google Play Games: {error}"
            )

            messagebox.showerror(
                "Google Play Games",
                str(error)
            )

    def install_apk(self):

        adb = self._tool(
            "adb_path"
        )

        apk = filedialog.askopenfilename(
            title="Selecionar APK",
            filetypes=[
                ("APK", "*.apk")
            ]
        )

        if not apk:
            return

        try:

            result = subprocess.run(
                [
                    adb,
                    "connect",
                    f"127.0.0.1:{self.cfg['adb_port']}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            self.log_msg(
                result.stdout.strip()
                or result.stderr.strip()
            )

            result = subprocess.run(
                [
                    adb,
                    "install",
                    "-r",
                    apk
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            self.log_msg(
                result.stdout.strip()
                or result.stderr.strip()
            )

            if result.returncode == 0:

                messagebox.showinfo(
                    "APK",
                    "APK instalado com sucesso."
                )

            else:

                messagebox.showerror(
                    "APK",
                    result.stderr
                    or "Falha na instalação."
                )

        except Exception as error:

            messagebox.showerror(
                "ADB",
                str(error)
            )


if __name__ == "__main__":
    EmulatorApp().mainloop()
