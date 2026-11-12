#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторная работа №1
Скрипт определяет операционную систему, на которой выполняется,
собирает набор её параметров и сохраняет результат в JSON-файл.

Работает на Windows, Linux и macOS без вызова внешних утилит ОС
(systeminfo, uname, sw_vers, free, lscpu и т.п.) — все данные
получены через стандартную библиотеку Python (модули platform, os,
socket, sys, getpass, shutil, locale, time) напрямую из интерфейсов
языка/ОС, предоставляемых интерпретатором.

Опционально используется внешний модуль psutil (см. README.md —
раздел "Обоснование использования psutil") для получения объёма
оперативной памяти и времени запуска системы. Если psutil не
установлен, скрипт продолжает работать, просто оставляя эти поля
пустыми (null).

Запуск:
    python my_script.py [путь_к_файлу.json]

Если путь не указан, результат сохраняется в os_info_<hostname>.json
в текущей директории.
"""

import os
import sys
import json
import time
import socket
import getpass
import shutil
import locale
import platform
import datetime

# psutil — необязательная зависимость, см. README.md
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ---------------------------------------------------------------------------
# 1. Определение ОС
# ---------------------------------------------------------------------------
def detect_os():
    """
    Возвращает нормализованное имя ОС: 'Windows', 'Linux' или 'macOS'.
    platform.system() для macOS возвращает 'Darwin' — приводим к
    привычному человеку названию.
    """
    system = platform.system()
    mapping = {
        "Darwin": "macOS",
        "Windows": "Windows",
        "Linux": "Linux",
    }
    return mapping.get(system, system), system


# ---------------------------------------------------------------------------
# 2. Сбор параметров текущей ОС
# ---------------------------------------------------------------------------
def collect_os_block(raw_system):
    """Общие и ОС-специфичные параметры."""
    os_name_human, _ = detect_os()

    block = {
        "system": raw_system,                 # 'Windows' | 'Linux' | 'Darwin'
        "os_name_human": os_name_human,        # 'Windows' | 'Linux' | 'macOS'
        "release": platform.release(),
        "version": platform.version(),
        "platform_string": platform.platform(),
    }

    # --- Linux: информация о дистрибутиве ---
    if raw_system == "Linux":
        distro_info = {}
        try:
            # Python 3.10+: стандартный способ прочитать /etc/os-release
            distro_info = dict(platform.freedesktop_os_release())
        except (AttributeError, OSError):
            # Фолбэк для более старых версий Python: читаем файл сами
            # (это обычный файл конфигурации, а не вызов утилиты ОС)
            os_release_path = "/etc/os-release"
            if os.path.exists(os_release_path):
                with open(os_release_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, _, value = line.partition("=")
                        distro_info[key] = value.strip('"')
        block["linux_distribution"] = distro_info or None

    # --- macOS: версия и имя релиза ---
    elif raw_system == "Darwin":
        mac_release, mac_versioninfo, mac_machine = platform.mac_ver()
        block["macos_version"] = {
            "release": mac_release or None,
            "machine": mac_machine or None,
        }

    # --- Windows: версия и редакция ---
    elif raw_system == "Windows":
        win_release, win_version, win_csd, win_ptype = platform.win32_ver()
        block["windows_version"] = {
            "release": win_release or None,
            "version": win_version or None,
            "service_pack": win_csd or None,
            "edition": getattr(platform, "win32_edition", lambda: None)(),
        }

    return block


def collect_hardware_block():
    """Параметры оборудования, доступные через стандартную библиотеку."""
    block = {
        "machine": platform.machine(),          # напр. 'x86_64', 'AMD64', 'arm64'
        "processor": platform.processor() or None,
        "architecture_bits": platform.architecture()[0],
        "architecture_linkage": platform.architecture()[1] or None,
        "cpu_count_logical": os.cpu_count(),
        "cpu_count_physical": None,
        "total_memory_bytes": None,
        "total_memory_gb": None,
    }

    if HAS_PSUTIL:
        try:
            block["cpu_count_physical"] = psutil.cpu_count(logical=False)
            total_mem = psutil.virtual_memory().total
            block["total_memory_bytes"] = total_mem
            block["total_memory_gb"] = round(total_mem / (1024 ** 3), 2)
        except Exception:
            pass

    return block


def collect_python_block():
    """Информация о самом интерпретаторе Python."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "build": list(platform.python_build()),
        "executable_path": sys.executable,
    }


def collect_user_and_host_block():
    """Данные о пользователе, хосте и файловой системе."""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = None

    try:
        fqdn = socket.getfqdn()
    except Exception:
        fqdn = None

    try:
        local_ip = socket.gethostbyname(hostname) if hostname else None
    except Exception:
        local_ip = None

    try:
        username = getpass.getuser()
    except Exception:
        username = None

    return {
        "hostname": hostname,
        "fqdn": fqdn,
        "local_ip": local_ip,
        "username": username,
        "home_dir": os.path.expanduser("~"),
        "current_working_dir": os.getcwd(),
        "path_separator": os.sep,
    }


def collect_filesystem_block():
    """Сведения о дисковом пространстве корневого/системного раздела."""
    # На Windows корня '/' нет — используем системный диск из переменной окружения
    if platform.system() == "Windows":
        root_path = os.environ.get("SystemDrive", "C:") + "\\"
    else:
        root_path = "/"

    try:
        usage = shutil.disk_usage(root_path)
        return {
            "checked_path": root_path,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_gb": round(usage.free / (1024 ** 3), 2),
        }
    except Exception:
        return {
            "checked_path": root_path,
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "free_gb": None,
        }


def collect_locale_and_time_block():
    """Часовой пояс, локаль и время загрузки системы."""
    try:
        system_locale = locale.getlocale()
    except Exception:
        system_locale = (None, None)

    boot_time_iso = None
    uptime_seconds = None
    if HAS_PSUTIL:
        try:
            boot_ts = psutil.boot_time()
            boot_time_iso = datetime.datetime.fromtimestamp(boot_ts).isoformat()
            uptime_seconds = round(time.time() - boot_ts)
        except Exception:
            pass

    return {
        "timezone_names": list(time.tzname),
        "utc_offset_seconds": -time.timezone if not time.daylight else -time.altzone,
        "system_locale_language": system_locale[0],
        "system_locale_encoding": system_locale[1],
        "system_boot_time_iso": boot_time_iso,
        "uptime_seconds": uptime_seconds,
    }


def collect_environment_block():
    """Базовая статистика окружения процесса."""
    path_value = os.environ.get("PATH", "")
    return {
        "env_variables_count": len(os.environ),
        "path_entries_count": len(path_value.split(os.pathsep)) if path_value else 0,
        "temp_dir": os.environ.get("TEMP") or os.environ.get("TMPDIR") or "/tmp",
    }


# ---------------------------------------------------------------------------
# 3. Сборка итоговой структуры и запись в JSON
# ---------------------------------------------------------------------------
def build_report():
    _, raw_system = detect_os()
    return {
        "meta": {
            "generated_at_iso": datetime.datetime.now().isoformat(),
            "script": os.path.basename(__file__),
            "psutil_available": HAS_PSUTIL,
        },
        "os": collect_os_block(raw_system),
        "hardware": collect_hardware_block(),
        "python": collect_python_block(),
        "user_and_host": collect_user_and_host_block(),
        "filesystem": collect_filesystem_block(),
        "locale_and_time": collect_locale_and_time_block(),
        "environment": collect_environment_block(),
    }


def main():
    report = build_report()

    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        hostname = report["user_and_host"]["hostname"] or "unknown_host"
        safe_hostname = "".join(c if c.isalnum() or c in "-_." else "_" for c in hostname)
        output_path = f"os_info_{safe_hostname}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[OK] Обнаружена ОС: {report['os']['os_name_human']} "
          f"({report['os']['release']})")
    print(f"[OK] Результат сохранён в файл: {os.path.abspath(output_path)}")
    if not HAS_PSUTIL:
        print("[i] Модуль psutil не найден — поля total_memory_* и "
              "system_boot_time_iso будут равны null. "
              "Установите его командой: pip install psutil (необязательно).")


if __name__ == "__main__":
    main()
