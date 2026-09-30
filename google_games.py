"""
Google Play / Games integration helpers
for AndroidPC-Emulator.

Este módulo não distribui arquivos do Google.
Ele usa ADB para trabalhar com uma imagem Android
que já tenha Google Play compatível.
"""

import shutil
import subprocess
from pathlib import Path


class GoogleGames:
    def __init__(self, adb_path="adb", device="127.0.0.1:5555"):
        self.adb_path = adb_path
        self.device = device

    def find_adb(self):
        """Procura o executável ADB no sistema."""
        found = shutil.which(self.adb_path)

        if found:
            return found

        path = Path(self.adb_path)

        if path.exists():
            return str(path)

        raise FileNotFoundError(
            "ADB não encontrado. Instale o Android SDK Platform Tools."
        )

    def run_adb(self, *arguments, timeout=30):
        """Executa um comando ADB no Android."""
        adb = self.find_adb()

        command = [
            adb,
            "-s",
            self.device,
            *arguments
        ]

        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def connect(self):
        """Conecta ao Android através do ADB."""
        adb = self.find_adb()

        return subprocess.run(
            [
                adb,
                "connect",
                self.device
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

    def check_connection(self):
        """Verifica se o Android está conectado."""
        result = self.run_adb("get-state")

        return (
            result.returncode == 0
            and "device" in result.stdout.lower()
        )

    def android_version(self):
        """Obtém a versão do Android."""
        result = self.run_adb(
            "shell",
            "getprop",
            "ro.build.version.release"
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    def android_architecture(self):
        """Obtém a arquitetura do Android."""
        result = self.run_adb(
            "shell",
            "getprop",
            "ro.product.cpu.abi"
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    def list_packages(self):
        """Lista os aplicativos instalados."""
        result = self.run_adb(
            "shell",
            "pm",
            "list",
            "packages"
        )

        if result.returncode != 0:
            return []

        packages = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("package:"):
                packages.append(
                    line.replace("package:", "", 1)
                )

        return packages

    def has_google_play(self):
        """Verifica se o Google Play Store está instalado."""
        packages = self.list_packages()

        google_packages = {
            "com.android.vending",
            "com.google.android.gms",
            "com.google.android.gsf",
        }

        return any(
            package in packages
            for package in google_packages
        )

    def install_apk(self, apk_path):
        """Instala um APK através do ADB."""
        apk = Path(apk_path)

        if not apk.exists():
            raise FileNotFoundError(
                f"APK não encontrado: {apk}"
            )

        return self.run_adb(
            "install",
            "-r",
            str(apk),
            timeout=120
        )

    def launch_app(self, package_name):
        """Abre um aplicativo pelo nome do pacote."""
        return self.run_adb(
            "shell",
            "monkey",
            "-p",
            package_name,
            "1"
        )

    def stop_app(self, package_name):
        """Fecha um aplicativo."""
        return self.run_adb(
            "shell",
            "am",
            "force-stop",
            package_name
        )

    def open_play_store(self):
        """Abre a Google Play Store."""
        return self.launch_app(
            "com.android.vending"
        )

    def open_google_games(self):
        """Tenta abrir o Google Play Games."""
        packages = [
            "com.google.android.play.games",
            "com.google.android.play.games.services",
        ]

        installed = self.list_packages()

        for package in packages:
            if package in installed:
                return self.launch_app(package)

        return None

    def device_info(self):
        """Retorna informações básicas do Android."""
        return {
            "connected": self.check_connection(),
            "android_version": self.android_version(),
            "architecture": self.android_architecture(),
            "google_play": self.has_google_play(),
        }


def main():
    """Teste simples do módulo."""
    google = GoogleGames()

    try:
        google.connect()

        info = google.device_info()

        print("AndroidPC Emulator")
        print("------------------")
        print(f"Conectado: {info['connected']}")
        print(f"Android: {info['android_version']}")
        print(f"Arquitetura: {info['architecture']}")
        print(f"Google Play: {info['google_play']}")

    except Exception as error:
        print(f"Erro: {error}")


if __name__ == "__main__":
    main()
