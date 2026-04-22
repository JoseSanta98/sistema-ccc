import os
import sys
import time

VERSION    = "5.0"
BUILD_DATE = "2026-04-22"


def _log(msg: str, nivel: str) -> None:
    colores = {
        "INFO": "\033[96m",
        "OK": "\033[92m",
        "WARN": "\033[93m",
        "ERR": "\033[91m",
    }
    ts = time.strftime("%H:%M:%S")
    color_nivel = colores.get(nivel, "\033[0m")
    print(f"  \033[90m[{ts}]\033[0m {color_nivel}[{nivel}]\033[0m  {msg}")


def log_ok(msg: str) -> None:
    _log(msg, "OK")


def log_warn(msg: str) -> None:
    _log(msg, "WARN")


def log_info(msg: str) -> None:
    _log(msg, "INFO")


def log_err(msg: str) -> None:
    _log(msg, "ERR")


def splash() -> None:
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    banner = r"""________/\\\\\\\\\________/\\\\\\\\\________/\\\\\\\\\_
 _____/\\\////////______/\\\////////______/\\\////////__
  ___/\\\/_____________/\\\/_____________/\\\/___________
   __/\\\_____________/\\\_____________/\\\______________
    _\/\\\_____________\/\\\_____________\/\\\_____________
     _\//\\\____________\//\\\____________\//\\\____________
      __\///\\\___________\///\\\___________\///\\\__________
       ____\////\\\\\\\\\____\////\\\\\\\\\____\////\\\\\\\\\_
        _______\/////////________\/////////________\/////////__"""

    print("\033[96m\033[1m" + banner + "\033[0m")
    print("\033[97m\033[1m  Sistema CCC — Control de Cajas y Cortes\033[0m")
    print("\033[97m\033[1m  ──────────────────────────────────────────────\033[0m")
    print(f"\033[90m  v{VERSION}  ·  {BUILD_DATE}\033[0m")
    log_info("Sistema iniciando...")
    time.sleep(0.2)
    log_info("Cargando módulos...")
    time.sleep(0.1)
