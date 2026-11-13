"""Выбор приложений «галочками» в терминале.

По умолчанию все пакеты отмечены как «оставить» ([x]). Пользователь вводит
номер, чтобы убрать галочку с того, что нужно отключить, и «a», чтобы применить.
Пакеты только отключаются, ничего не удаляется.
"""

import os
import sys

import analyzer

PAGE_SIZE = 20


def _clear_screen():
    """Очищает экран, чтобы список не разрастался."""
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def _render(packages, keep, page):
    """Показывает текущую страницу списка."""
    _clear_screen()
    pages = max(1, (len(packages) + PAGE_SIZE - 1) // PAGE_SIZE)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(packages))
    print("Отметьте приложения, которые нужно ОТКЛЮЧИТЬ.")
    print("[x] — оставить, [ ] — отключить.  «a» — применить, «q» — отмена.")
    print()
    for index in range(start, end):
        mark = "x" if keep[index] else " "
        if analyzer.is_critical(packages[index]):
            protected = "  [не трогать: без него ТВ не заработает]"
        elif analyzer.is_whitelisted(packages[index]):
            protected = "  [не рекомендуется]"
        else:
            protected = ""
        print(f"  {index + 1:3d}. [{mark}] {packages[index]}{protected}")
    print()
    print(f"Страница {page + 1} из {pages}.  К отключению: {sum(1 for k in keep if not k)}")
    print()


def choose(packages):
    """Возвращает список пакетов, отмеченных к отключению.

    Пустой список — отмена или ничего не отмечено.
    """
    keep = [True] * len(packages)
    page = 0
    pages = max(1, (len(packages) + PAGE_SIZE - 1) // PAGE_SIZE)
    while True:
        _render(packages, keep, page)
        try:
            answer = input("Номер / a / q / n / p: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return []
        if answer in ("a", "ф", "apply", "готово", "д"):
            return [p for p, k in zip(packages, keep) if not k]
        if answer in ("q", "й", "exit", "выход", "отмена"):
            return []
        if answer in ("n", "т", "next", "далее", ">"):
            page = min(page + 1, pages - 1)
            continue
        if answer in ("p", "з", "prev", "назад", "<"):
            page = max(page - 1, 0)
            continue
        if answer.isdigit():
            index = int(answer) - 1
            if 0 <= index < len(packages):
                if analyzer.is_critical(packages[index]):
                    print("Этот пакет критичен — отключить его нельзя.")
                    continue
                keep[index] = not keep[index]
                continue
        print("Не понял. Введите номер, «a», «q», «n» или «p».")
