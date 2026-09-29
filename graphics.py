import platform

def host_info():
    return {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()}

def acceleration_note():
    return "WHPX/Hyper-V pode ser usado no Windows quando suportado pelo host." if platform.system()=="Windows" else "Aceleração depende do sistema hospedeiro."
