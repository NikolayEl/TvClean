"""Настройки TV Cleaner.

Здесь собрано всё, что может понадобиться поменять руками: адрес телевизора,
путь к ADB, белый список пакетов и слова-признаки рекламы.
"""

# --- Подключение к телевизору -------------------------------------------------

# IP-адрес телевизора в вашей домашней сети. Впишите свой (например, "192.168.1.21").
# Узнать можно на телевизоре: Настройки -> Сеть и Интернет -> Сеть -> IP-адрес.
TV_IP = "192.168.1.21"

# Порт отладочного моста ADB. На телевизорах он всегда 5555.
ADB_PORT = 5555

# Как вызывать ADB:
#   "adb"                          — если adb добавлен в PATH;
#   r"C:\platform-tools\adb.exe"   — полный путь к adb.exe.
# На этом компьютере adb в PATH НЕ добавлен, поэтому указан полный путь.
ADB_PATH = r"C:\platform-tools\adb.exe"

# Сколько секунд ждать ответа ADB (подключение и обычные команды).
CONNECT_TIMEOUT = 15
CMD_TIMEOUT = 30

# --- Белый список (отключать НЕЛЬЗЯ ни при каких условиях) ---------------------

# Критически важные пакеты. Правило с точкой на конце ("com.digma.") означает
# «всё, что начинается с этого»; остальные правила — сам пакет и его части.
WHITELIST = (
    # Android и оболочка Google: без них телевизор не загрузится, потеряет
    # настройки, Wi-Fi, HDMI, Play Store, пульт или голосовой поиск.
    "android",
    "com.android.",
    "com.google.android.",
    # Сервисы телевизора MediaTek: тюнер, HDMI, звук, загрузка, настройка.
    "com.mediatek.",
    "mediatek.",
    # Пульт по Bluetooth и трансляция с телефона — это не реклама.
    "com.smartdevice.bleconnectservice",
    "com.smartdevice.dtv.icast",
    # Бренды платы и самого телевизора.
    "com.digma.",
    "com.skyworth.",
    "com.sky.",
    "com.mstar.android.tv.",
    "com.dolby.",
)

# --- Критичные пакеты (нельзя отключать даже вручную) ------------------------

# Строже белого списка: WHITELIST защищает от автоматического аудита, а CRITICAL
# не даёт отключить руками то, без чего телевизор не загрузится, потеряет пульт,
# Wi-Fi, HDMI, тюнер, Play Store или настройки. Проверено на Digma Pro 55L.
CRITICAL = (
    "android",
    "com.android.systemui",
    "com.android.settings",
    "com.android.tv.settings",
    "com.android.shell",
    "com.android.phone",
    "com.android.permissioncontroller",
    "com.google.android.permissioncontroller",
    "com.android.packageinstaller",
    "com.google.android.packageinstaller",
    "com.android.providers.",
    "com.google.android.ext.services",
    "com.google.android.ext.shared",
    "com.google.android.modulemetadata",
    "com.google.android.overlay.modules.",
    "com.android.vending",
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.google.android.webview",
    "com.google.android.inputmethod.latin",
    "com.google.android.tts",
    # Ассистент (katniss) не критичен: без него ТВ загружается и работает,
    # теряется только голосовой поиск и «Окей Google». Отключён по просьбе
    # пользователя 2026-11-13, поэтому из CRITICAL убран.
    "com.google.android.tv.assistant",
    "com.google.android.tv.remote.service",
    "com.google.android.apps.tv.launcherx",
    "com.google.android.apps.tv.dreamx",
    "com.google.android.apps.nbu.smartconnect.tv",
    "com.google.android.tungsten.setupwraith",
    "com.google.android.tv.frameworkpackagestubs",
    "com.google.android.onetimeinitializer",
    "com.google.android.partnersetup",
    "com.google.android.sss.authbridge",
    "com.google.android.syncadapters.",
    "com.google.android.feedback",
    "com.google.android.apps.mediashell",
    "com.google.android.marvin.talkback",
    "com.android.bluetooth",
    "com.android.networkstack",
    "com.android.wifi.resources",
    "com.android.captiveportallogin",
    "com.android.proxyhandler",
    "com.android.vpndialogs",
    "com.android.certinstaller",
    "com.android.pacprocessor",
    "com.android.statementservice",
    "com.android.hotspot2.osulogin",
    "com.android.soundpicker",
    "com.android.htmlviewer",
    "com.android.printspooler",
    "com.android.dreams.basic",
    "com.android.backupconfirm",
    "com.android.localtransport",
    "com.android.sharedstoragebackup",
    "com.android.wallpaperbackup",
    "com.android.companiondevicemanager",
    "com.android.dynsystem",
    "com.android.externalstorage",
    "com.android.se",
    "com.android.keychain",
    "com.android.inputdevices",
    "com.android.location.fused",
    "com.android.settings.intelligence",
    "com.android.cts.",
    "com.android.tv.overlay.lowram",
    "com.mediatek.",
    "mediatek.",
    "com.mstar.android.tv.",
    "com.dolby.",
    "com.sky.",
    "com.skyworth.",
    "com.digma.",
    "com.smartdevice.bleconnectservice",
    "com.smartdevice.dtv.icast",
    "com.smartdevice.service",
    "com.smartdevice.global.service",
    "com.smartdevice.factory",
)

# --- Признаки «подозрительных» пакетов ---------------------------------------

# Если в имени пакета встречается одно из этих слов — пакет попадает в список
# подозрительных. Отключаются они только вручную, после подтверждения.
SUSPICIOUS_KEYWORDS = (
    "ads",
    "analytics",
    "tracking",
    "recommend",
    "telemetry",
    "adservice",
    "monitor",
    "stats",
    "metrics",
    "demo",
)

# --- Файлы --------------------------------------------------------------------

# Резервная копия списка пакетов (состояние до изменений).
BACKUP_FILE = "backup_packages.txt"

# Журнал: что и когда отключено или включено обратно.
LOG_FILE = "cleaner_log.txt"
