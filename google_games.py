"""
Google Play / Games integration helpers
for AndroidPC-Emulator.

Este módulo NÃO contém nem redistribui arquivos da Google.
Ele apenas usa ADB para trabalhar com uma imagem Android
que você já tenha instalado e que seja compatível com Google Play.
"""

import subprocess
import shutil
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
        """Executa um comando ADB no dispositivo Android."""
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
            return None

        return result.stdout.strip()

    def architecture(self):
        """Obtém a arquitetura do Android."""
        result = self.run_adb(
            "shell",
            "getprop",
            "ro.product.cpu.abi"
        )

        if result.returncode != 0:
            return None

        return result.stdout.strip()

    def list_installed_apps(self):
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

    def install_apk(self, apk_file):
        """Instala um APK no Android."""
        apk = Path(apk_file)

        if not apk.exists():
            raise FileNotFoundError(
                f"APK não encontrado: {apk}"
            )

        return self.run_adb(
            "install",
            "-r",
            str(apk),
            timeout=180
        )

    def launch_package(self, package_name):
        """
        Tenta iniciar um aplicativo instalado.

        O nome do pacote deve ser conhecido.
        """
        return self.run_adb(
            "shell",
            "monkey",
            "-p",
            package_name,
            "1"
        )

    def stop_package(self, package_name):
        """Encerra um aplicativo."""
        return self.run_adb(
            "shell",
            "am",
            "force-stop",
            package_name
        )

    def device_info(self):
        """Retorna informações básicas do Android."""
        return {
            "connected": self.check_connection(),
            "android": self.android_version(),
            "architecture": self.architecture()
        }


def main():
    """
    Teste simples quando o arquivo é executado diretamente.
    """

    google = GoogleGames()

    try:
        result = google.connect()

        print(result.stdout.strip())

        if not google.check_connection():
            print("Android não conectado.")
            return

        info = google.device_info()

        print("Android:", info["android"])
        print("Arquitetura:", info["architecture"])

        print("\nIntegração ADB funcionando.")

    except Exception as error:
        print("Erro:", error)


if __name__ == "__main__":
    main()
