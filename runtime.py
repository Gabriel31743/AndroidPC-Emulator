from dataclasses import dataclass

@dataclass
class RuntimeState:
    running: bool = False
    pid: int | None = None
    adb_connected: bool = False

class EmulatorRuntime:
    def __init__(self):
        self.state = RuntimeState()
    def mark_started(self, process):
        self.state.running, self.state.pid = True, process.pid
    def mark_stopped(self):
        self.state = RuntimeState()
