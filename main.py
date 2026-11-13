"""TV Cleaner — безопасная очистка телевизора Digma Pro 55L (Google TV).

Меню: справка про CleanYourTV, подключение к телевизору, список пакетов,
аудит, отключение рекламы и восстановление отключённых пакетов. Пакеты не
удаляются — только отключаются (pm disable-user), поэтому любую правку можно
отменить.
"""

import os
import sys

from colorama import Fore, init

import adb_manager
import analyzer
import checklist
import cleaner
import config

init(autoreset=True)

MENU_WIDTH = 62

# Готовое решение для Android/Google TV: списки пакетов по моделям в папке examples/.
CLEANYOURTV_URL = "https://github.com/Gathin23/cleanyourtv"

# Последний полученный список пакетов и найденные подозрительные —
# чтобы не запрашивать их у телевизора на каждой команде меню.
_state = {"packages": [], "suspicious": []}


def ok(text):
    """Зелёное сообщение об успехе."""
    print(Fore.GREEN + text)


def warn(text):
    """Жёлтое предупреждение."""
    print(Fore.YELLOW + text)


def err(text):
    """Красное сообщение об ошибке."""
    print(Fore.RED + text)


def info(text):
    """Голубое пояснение."""
    print(Fore.CYAN + text)


def _ask_yes_no(question):
    """Спрашивает подтверждение. Принимает y/n и русские «да»/«нет»."""
    while True:
        try:
            answer = input(f"{question} [y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if answer in ("y", "yes", "да", "н"):
            return True
        if answer in ("n", "no", "нет", "т"):
            return False
        warn("Ответьте y (да) или n (нет).")


def _load_packages(force=False):
    """Список пакетов с телевизора (с кэшем в памяти)."""
    if _state["packages"] and not force:
        return _state["packages"]
    _state["packages"] = adb_manager.get_packages(include_disabled=True)
    return _state["packages"]


def cmd_cleanyourtv():
    """Пункт 0: справка про готовое решение CleanYourTV."""
    info("Вариант А — готовое решение CleanYourTV (репозиторий на GitHub):")
    print(f"  {CLEANYOURTV_URL}")
    print("  Списки пакетов по моделям — в папке examples/ "
          "(одна папка на модель, внутри debloat.txt).")
    print()
    print("  1. Проверьте наличие вашей модели (Digma Pro 55L) в репозитории "
          "CleanYourTV на GitHub.")
    print("  2. Если список найден, следуйте инструкциям из их README.")
    print("  3. Если списка нет — используйте пункт 3 (Аудит) в нашем меню "
          "для анализа вашего телевизора.")


def cmd_connect():
    """Пункт 1: подключение к телевизору."""
    try:
        message = adb_manager.connect()
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return
    ok(f"Подключено. {message}")


def cmd_show_packages():
    """Пункт 2: показать все пакеты (защищённые помечены)."""
    try:
        packages = _load_packages(force=True)
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return
    info(f"Пакетов найдено: {len(packages)}")
    for package in packages:
        mark = "  [защищён] " if analyzer.is_whitelisted(package) else "  "
        print(mark + package)


def cmd_audit():
    """Пункт 3: аудит — показать подозрительные, ничего не меняя."""
    try:
        packages = _load_packages(force=True)
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return []
    _state["suspicious"] = analyzer.find_suspicious(packages)
    if not _state["suspicious"]:
        ok("Подозрительных пакетов не найдено — очищать нечего.")
        return _state["suspicious"]
    warn(f"Найдено подозрительных пакетов: {len(_state['suspicious'])}")
    for package, reason in _state["suspicious"]:
        print(f"  {package}  (слово-признак: {reason})")
    info("Пока ничего не изменено. Пункт 4 отключит эти пакеты.")
    return _state["suspicious"]


def cmd_disable():
    """Пункт 4: отключить подозрительные пакеты (с подтверждением)."""
    suspicious = _state["suspicious"] or cmd_audit()
    if not suspicious:
        return
    print()
    warn("Будут ОТКЛЮЧЕНЫ следующие пакеты (удаления нет, всё обратимо):")
    for package, reason in suspicious:
        print(f"  {package}  (слово-признак: {reason})")
    if not _ask_yes_no("Отключать эти пакеты?"):
        info("Отменено. Ничего не изменено.")
        return
    try:
        path, count = cleaner.backup(_load_packages())
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return
    ok(f"Резервная копия сохранена: {path} ({count} пакетов)")

    disabled, errors = cleaner.disable_suspicious(suspicious)
    ok(f"Отключено пакетов: {len(disabled)}")
    for package in disabled:
        print("  " + package)
    if errors:
        warn(f"Не удалось отключить: {len(errors)}")
        for package, text in errors:
            err(f"  {package}: {text}")
    _state["packages"] = []  # список на телевизоре изменился — сбрасываем кэш
    info(f"Журнал изменений: {os.path.abspath(config.LOG_FILE)}")


def cmd_restore():
    """Пункт 5: включить обратно пакеты, отключённые программой."""
    packages = cleaner.read_disabled_packages()
    if not packages:
        info(f"В журнале нет отключённых пакетов: {os.path.abspath(config.LOG_FILE)}")
        return
    warn(f"В журнале отключённых пакетов: {len(packages)}")
    for package in packages:
        print("  " + package)
    if not _ask_yes_no("Включить их обратно?"):
        info("Отменено.")
        return
    enabled, errors = cleaner.enable_packages(packages)
    ok(f"Включено пакетов: {len(enabled)}")
    for package in enabled:
        print("  " + package)
    if errors:
        warn(f"Не удалось включить: {len(errors)}")
        for package, text in errors:
            err(f"  {package}: {text}")
    _state["packages"] = []


def cmd_checklist():
    """Пункт 6: отметить приложения галочками и отключить отмеченные."""
    try:
        packages = _load_packages(force=True)
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return
    to_disable = checklist.choose(packages)
    if not to_disable:
        info("Ничего не отмечено. Отменено.")
        return
    warn(f"Будут отключены {len(to_disable)} пакетов:")
    for package in to_disable:
        print("  " + package)
    if not _ask_yes_no("Отключать?"):
        info("Отменено. Ничего не изменено.")
        return
    try:
        path, count = cleaner.backup(_load_packages())
    except adb_manager.AdbError as exc:
        err(f"Ошибка: {exc}")
        return
    ok(f"Резервная копия сохранена: {path} ({count} пакетов)")
    disabled, errors = cleaner.disable_suspicious(
        [(package, "вручную отмечен") for package in to_disable]
    )
    ok(f"Отключено пакетов: {len(disabled)}")
    for package in disabled:
        print("  " + package)
    if errors:
        warn(f"Не удалось отключить: {len(errors)}")
        for package, text in errors:
            err(f"  {package}: {text}")
    _state["packages"] = []
    info(f"Журнал изменений: {os.path.abspath(config.LOG_FILE)}")


def _print_menu():
    """Заголовок и пункты меню."""
    info("=" * MENU_WIDTH)
    info(f" TV Cleaner — очистка Digma Pro 55L (Google TV)   IP: {config.TV_IP}")
    info("=" * MENU_WIDTH)
    print(" 0. Инструкция по проверке CleanYourTV")
    print(" 1. Подключиться к телевизору")
    print(" 2. Показать все пакеты")
    print(" 3. Провести аудит (только показать подозрительные)")
    print(" 4. Отключить подозрительные пакеты")
    print(" 5. Восстановить отключённые пакеты")
    print(" 6. Отметить приложения галочками (что отключить)")
    print(" 7. Выход")
    warn("Внимание: действия на свой страх и риск. Пакеты только отключаются,")
    warn("не удаляются — пункт 5 возвращает всё обратно.")
    print()


def main():
    """Точка входа: меню в цикле."""
    _print_menu()
    while True:
        try:
            choice = input("Выберите пункт (0-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            info("Выход.")
            return 0
        if choice == "0":
            cmd_cleanyourtv()
        elif choice == "1":
            cmd_connect()
        elif choice == "2":
            cmd_show_packages()
        elif choice == "3":
            cmd_audit()
        elif choice == "4":
            cmd_disable()
        elif choice == "5":
            cmd_restore()
        elif choice == "6":
            cmd_checklist()
        elif choice == "7":
            info("Выход.")
            return 0
        else:
            warn("Нет такого пункта. Введите число от 0 до 7.")
        print()


if __name__ == "__main__":
    sys.exit(main())
