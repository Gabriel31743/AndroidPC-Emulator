# Architecture

The prototype has four layers:

1. **UI** — Tkinter desktop launcher.
2. **Configuration** — `config.json`.
3. **Runtime** — QEMU process management.
4. **Android bridge** — ADB for device detection and APK installation.

## Planned hardware acceleration

The Windows build can later select WHPX/Hyper-V acceleration when the host supports it. GPU acceleration is intentionally kept as a separate layer because it depends on the Android image, graphics backend and QEMU build.

## Audio and network

The launcher passes a basic QEMU audio device and user-mode networking configuration. Exact audio/GPU options may need adjustment for the selected Android image.
