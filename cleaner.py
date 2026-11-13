"""Безопасные действия: резервная копия, отключение, восстановление.

Программа НИКОГДА не удаляет пакеты: используется только pm disable-user
(обратимая операция) и pm enable.
"""

import datetime
import os
import re

import adb_manager
import config

# Строка журнала вида: "2026-11-13 12:00:00 ОТКЛЮЧЁН com.foo.ads — причина: ads"
_DISABLED_PATTERN = re.compile(r"ОТКЛЮЧЁН\s+(\S+)")


def _now():
    """Текущее время для журнала."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(lines):
    """Дописывает строки в журнал изменений."""
    with open(config.LOG_FILE, "a", encoding="utf-8") as file:
        for line in lines:
            file.write(line + "\n")


def backup(packages, filename=None):
    """Сохраняет список активных пакетов. Возвращает (путь, количество)."""
    path = os.path.abspath(filename or config.BACKUP_FILE)
    with open(path, "w", encoding="utf-8") as file:
        file.write("# TV Cleaner: список пакетов до изменений.\n")
        file.write(f"# Дата: {_now()}\n")
        file.write(f"# Телевизор: {config.TV_IP}\n")
        file.write(f"# Всего пакетов: {len(packages)}\n")
        for package in sorted(packages):
            file.write(package + "\n")
    return path, len(packages)


def disable_suspicious(suspicious_list, ip=None):
    """Отключает подозрительные пакеты и пишет журнал.

    Возвращает (отключённые, ошибки), где ошибки — список (пакет, текст).
    """
    disabled, errors, log_lines = [], [], []
    for package, reason in suspicious_list:
        try:
            adb_manager.disable_package(package, ip=ip)
        except adb_manager.AdbError as exc:
            errors.append((package, str(exc)))
            log_lines.append(f"{_now()} ОШИБКА {package} — {exc}")
            continue
        disabled.append(package)
        log_lines.append(f"{_now()} ОТКЛЮЧЁН {package} — причина: {reason}")
    if log_lines:
        _log(log_lines)
    return disabled, errors


def enable_packages(packages, ip=None):
    """Включает пакеты обратно и пишет журнал.

    Возвращает (включённые, ошибки).
    """
    enabled, errors, log_lines = [], [], []
    for package in packages:
        try:
            adb_manager.enable_package(package, ip=ip)
        except adb_manager.AdbError as exc:
            errors.append((package, str(exc)))
            log_lines.append(f"{_now()} ОШИБКА ВОЗВРАТА {package} — {exc}")
            continue
        enabled.append(package)
        log_lines.append(f"{_now()} ВКЛЮЧЁН {package}")
    if log_lines:
        _log(log_lines)
    return enabled, errors


def read_disabled_packages(filename=None):
    """Пакеты, отключённые программой, по журналу (без повторов, по порядку)."""
    filename = filename or config.LOG_FILE
    if not os.path.exists(filename):
        return []
    packages = []
    with open(filename, encoding="utf-8") as file:
        for line in file:
            for match in _DISABLED_PATTERN.finditer(line):
                package = match.group(1)
                if package not in packages:
                    packages.append(package)
    return packages
