def qemu_network_args(cfg):
    if not cfg.get("network", True): return []
    port = int(cfg.get("adb_port", 5555))
    return ["-netdev", f"user,id=net0,hostfwd=tcp::{port}-:5555", "-device", "virtio-net-pci,netdev=net0"]
