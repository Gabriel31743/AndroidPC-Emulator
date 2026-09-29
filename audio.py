def qemu_audio_args(enabled=True):
    return [] if not enabled else ["-audiodev", "driver=dsound,id=audio0", "-device", "AC97,audiodev=audio0"]
