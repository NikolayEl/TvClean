"""Работа с ADB: подключение к телевизору и управление пакетами.

Модуль ничего не печатает сам: он либо возвращает результат, либо бросает
AdbError с текстом на русском — что показать пользователю, решает main.py.

Удаление пакетов здесь НЕ используется: только pm disable-user (обратимо)
и pm enable.
"""

import subprocess

import config


class AdbError(Exception):
    """Ошибка ADB. Текст исключения уже готов к показу пользователю."""


def _device_args(ip=None):
    """Аргументы выбора устройства, если известен адрес телевизора."""
    if ip:
        return ["-s", f"{ip}:{config.ADB_PORT}"]
    return []


def run_adb(args, timeout=config.CMD_TIMEOUT):
    """Запускает adb с аргументами и возвращает (код возврата, вывод)."""
    command = [config.ADB_PATH] + [str(arg) for arg in args]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError:
        raise AdbError(
            "ADB не найден. Укажите в config.py путь ADB_PATH "
            "(например, C:\\platform-tools\\adb.exe) или добавьте adb в PATH."
        )
    except subprocess.TimeoutExpired:
        raise AdbError("ADB не отвечает (превышено время ожидания).")
    output = "\n".join(part for part in (process.stdout, process.stderr) if part)
    return process.returncode, output.strip()


def is_online(ip=None):
    """True, если телевизор виден ADB и готов принимать команды."""
    ip = ip or config.TV_IP
    code, output = run_adb(["devices"])
    target = f"{ip}:{config.ADB_PORT}"
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == target and parts[1] == "device":
            return True
    return False


def connect(ip=None):
    """Подключается к телевизору по сети. Возвращает строку-подтверждение."""
    ip = ip or config.TV_IP
    if not ip or "XX" in ip:
        raise AdbError(
            "В config.py не указан IP телевизора (TV_IP). Впишите свой адрес."
        )
    code, output = run_adb(
        ["connect", f"{ip}:{config.ADB_PORT}"], timeout=config.CONNECT_TIMEOUT
    )
    low = output.lower()
    if code != 0 or "cannot" in low or "failed" in low or "unable" in low:
        raise AdbError(
            f"Устройство не найдено. Проверьте IP и отладку (адрес {ip}).\n"
            f"Ответ ADB: {output or 'пусто'}"
        )
    if not is_online(ip):
        raise AdbError(
            f"Устройство {ip} не в состоянии «device». Проверьте, что телевизор "
            "включён, отладка по ADB разрешена, а компьютер в той же сети.\n"
            f"Ответ ADB: {output or 'пусто'}"
        )
    return output or f"connected to {ip}:{config.ADB_PORT}"


def get_packages(include_disabled=False, ip=None):
    """Возвращает отсортированный список имён пакетов.

    include_disabled=False — только включённые сейчас пакеты;
    include_disabled=True  — все, включая уже отключённые.
    """
    command = ["shell", "pm", "list", "packages"]
    if not include_disabled:
        command.append("-e")
    code, output = run_adb(_device_args(ip) + command)

    packages = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line[len("package:"):].strip())
    if not packages:
        raise AdbError(
            "Не удалось получить список пакетов. Телевизор подключён?\n"
            f"Ответ ADB: {output or 'пусто'}"
        )
    return sorted(set(packages))


def _package_action(package, action, ip=None):
    """Общая часть disable_package/enable_package."""
    code, output = run_adb(_device_args(ip) + ["shell", "pm", action, package])
    low = output.lower()
    if code != 0 or "error" in low or "exception" in low or "not allowed" in low:
        raise AdbError(
            f"Не удалось выполнить «pm {action}» для {package}: "
            f"{output or 'без ответа'}"
        )
    return output or f"ok: {package}"


def disable_package(package, ip=None):
    """Отключает пакет для пользователя 0 (обратимо). Возвращает ответ ADB."""
    return _package_action(package, "disable-user --user 0", ip)


def enable_package(package, ip=None):
    """Включает ранее отключённый пакет. Возвращает ответ ADB."""
    return _package_action(package, "enable", ip)
