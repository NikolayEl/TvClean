"""Аудит списка пакетов: поиск подозрительных (реклама, телеметрия)."""

import re

import config

# Имя пакета делится на сегменты по точкам, дефисам и подчёркиваниям:
# "com.google.android.gms.ads" -> ["com", "google", "android", "gms", "ads"].
_SEGMENT = re.compile(r"[.\-_]+")


def _matches(package, rules):
    """True, если имя пакета попадает под одно из правил списка."""
    for rule in rules:
        if rule.endswith("."):
            if package.startswith(rule):
                return True
        elif package == rule or package.startswith(rule + "."):
            return True
    return False


def is_whitelisted(package):
    """True, если пакет защищён белым списком и отключать его нельзя."""
    return _matches(package, config.WHITELIST)


def is_critical(package):
    """True, если без пакета телевизор не загрузится или потеряет пульт.

    Строже белого списка: WHITELIST защищает от автоматического аудита, а
    критичные пакеты нельзя отключить и вручную.
    """
    return _matches(package, config.CRITICAL)


def find_reason(package):
    """Слово-признак, из-за которого пакет подозрительный, или None.

    Слово-признак сравнивается с сегментом имени пакета, а не ищется внутри
    строки: «recommend» находит «com.smartdevice.recommendation», но «ads»
    больше не находит «com.android.providers.downloads» (там «downl**ads**»).
    """
    for segment in _SEGMENT.split(package.lower()):
        for keyword in config.SUSPICIOUS_KEYWORDS:
            if segment.startswith(keyword):
                return keyword
    return None


def find_suspicious(packages):
    """Возвращает список кортежей (пакет, причина) для подозрительных пакетов.

    Белый список имеет приоритет: пакет из WHITELIST в результат не попадёт,
    даже если в его имени есть слово из SUSPICIOUS_KEYWORDS.
    """
    found = []
    for package in packages:
        if is_whitelisted(package):
            continue
        reason = find_reason(package)
        if reason:
            found.append((package, reason))
    return found
