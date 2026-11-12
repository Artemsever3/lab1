# Лабораторная работа №1. Определение параметров ОС и запись в JSON

Скрипт `my_script.py` определяет, на какой операционной системе он
запущен (**Windows / Linux / macOS**), собирает набор параметров этой
ОС, окружения и оборудования, и сохраняет результат в JSON-файл.

## Как это работает

1. **Определение ОС.**
   Функция `detect_os()` вызывает `platform.system()` — это
   стандартная функция Python, которая читает информацию об ОС через
   внутренние вызовы интерпретатора (а не через запуск внешних команд).
   Она возвращает `'Windows'`, `'Linux'` или `'Darwin'` (macOS); второе
   значение приводится к привычному человеку виду `'macOS'`.

2. **Сбор параметров.**
   В зависимости от результата п.1 собирается общий набор параметров
   (одинаковый для всех ОС) плюс несколько ОС-специфичных полей
   (например, информация о дистрибутиве Linux из `/etc/os-release`,
   версия macOS, редакция Windows).

3. **Запись в JSON.**
   Все собранные данные складываются в единый словарь и записываются
   в файл с помощью `json.dump(..., ensure_ascii=False, indent=2)`.

## Запуск

```bash
# без аргументов — файл сохранится как os_info_<hostname>.json
python my_script.py

# с указанием имени/пути файла
python my_script.py result.json
```

Зависимостей из стандартной библиотеки достаточно для полной работы
скрипта. Модуль `psutil` — опциональный (см. ниже), для его установки:

```bash
pip install -r requirements.txt
```

Скрипт универсален: один и тот же файл `my_script.py` запускается без
изменений на Windows, Linux и macOS.

## Ограничение задания и как оно соблюдено

По заданию **нельзя использовать стандартные утилиты ОС** для сбора
данных (например, запускать `systeminfo`, `uname -a`, `sw_vers`,
`free`, `lscpu`, `wmic` и т.п. через `subprocess`/`os.system`).

Скрипт не вызывает `subprocess`, `os.system` или `os.popen` ни разу —
все данные получены через:
- стандартный модуль **`platform`** — читает атрибуты ОС/интерпретатора
  напрямую через системные вызовы/API, которые предоставляет сама
  Python (не через запуск консольных утилит);
- стандартные модули **`os`**, **`socket`**, **`sys`**, **`getpass`**,
  **`shutil`**, **`locale`**, **`time`**, **`datetime`**, **`json`** —
  обращаются к ОС через их собственные системные вызовы
  (`os.cpu_count`, `shutil.disk_usage`, `socket.gethostname` и т.д.),
  а не через вызов внешних программ;
- чтение файла `/etc/os-release` на Linux — это обычное чтение
  текстового конфигурационного файла средствами `open()`, а не вызов
  утилиты.

## Обоснование использования внешнего модуля `psutil`

Стандартная библиотека Python **не предоставляет кроссплатформенного
способа** узнать:
- общий объём оперативной памяти;
- время запуска (boot time) системы,

не прибегая к вызову утилит ОС (`free`/`vm_stat`/`systeminfo`) или к
написанию отдельного кода под каждую ОС через низкоуровневые средства
(`ctypes` + вызовы Win32 API на Windows, разбор `/proc/meminfo` на
Linux, `ctypes` + `sysctl()` на macOS) — такой код получился бы
громоздким, платформенно-зависимым и трудным для поддержки в рамках
учебной работы.

Модуль **`psutil`** даёт эти данные одним кроссплатформенным вызовом
(`psutil.virtual_memory().total`, `psutil.boot_time()`), **не
запуская никаких внешних программ** — он сам обращается к системным
интерфейсам ОС (тем же `/proc` на Linux, Win32 API на Windows, Mach/
sysctl на macOS), просто инкапсулируя эту платформенно-зависимую
логику внутри себя. Поэтому выбор сделан в пользу `psutil`, а не
написания собственной платформенно-зависимой реализации.

**Важно:** зависимость необязательна. Если `psutil` не установлен,
скрипт полностью работает и выполняет все остальные пункты задания —
просто поля `total_memory_bytes`, `total_memory_gb`,
`cpu_count_physical`, `system_boot_time_iso`, `uptime_seconds`
записываются как `null`, о чём скрипт сообщает в консоли.

## Структура JSON-результата

```json
{
  "meta": {
    "generated_at_iso": "дата и время формирования отчёта",
    "script": "имя файла скрипта",
    "psutil_available": true
  },
  "os": {
    "system": "Linux | Windows | Darwin",
    "os_name_human": "Linux | Windows | macOS",
    "release": "...",
    "version": "...",
    "platform_string": "...",
    "linux_distribution": { "...": "...поля из /etc/os-release, только на Linux" },
    "macos_version": { "release": "...", "machine": "...   только на macOS" },
    "windows_version": { "release": "...", "version": "...", "service_pack": "...", "edition": "...   только на Windows" }
  },
  "hardware": {
    "machine": "...",
    "processor": "...",
    "architecture_bits": "32bit | 64bit",
    "architecture_linkage": "...",
    "cpu_count_logical": 0,
    "cpu_count_physical": 0,
    "total_memory_bytes": 0,
    "total_memory_gb": 0.0
  },
  "python": {
    "version": "...",
    "implementation": "CPython | PyPy | ...",
    "compiler": "...",
    "build": ["...", "..."],
    "executable_path": "..."
  },
  "user_and_host": {
    "hostname": "...",
    "fqdn": "...",
    "local_ip": "...",
    "username": "...",
    "home_dir": "...",
    "current_working_dir": "...",
    "path_separator": "/ | \\"
  },
  "filesystem": {
    "checked_path": "/ | C:\\",
    "total_bytes": 0,
    "used_bytes": 0,
    "free_bytes": 0,
    "free_gb": 0.0
  },
  "locale_and_time": {
    "timezone_names": ["...", "..."],
    "utc_offset_seconds": 0,
    "system_locale_language": "...",
    "system_locale_encoding": "...",
    "system_boot_time_iso": "...",
    "uptime_seconds": 0
  },
  "environment": {
    "env_variables_count": 0,
    "path_entries_count": 0,
    "temp_dir": "..."
  }
}
```

## Перечень собираемых параметров

### Блок `os` — операционная система
| Параметр | Описание |
|---|---|
| `system` | Сырое имя ОС от `platform.system()` (`Windows`/`Linux`/`Darwin`) |
| `os_name_human` | То же, но `Darwin` заменено на привычное `macOS` |
| `release` | Версия релиза ядра/ОС (`platform.release()`) |
| `version` | Подробная версия сборки ОС (`platform.version()`) |
| `platform_string` | Сводная строка платформы (`platform.platform()`) |
| `linux_distribution` | *(только Linux)* словарь из `/etc/os-release`: `NAME`, `PRETTY_NAME`, `VERSION_ID` и т.д. |
| `macos_version` | *(только macOS)* версия macOS и архитектура (`platform.mac_ver()`) |
| `windows_version` | *(только Windows)* версия, сборка, сервис-пак, редакция (`platform.win32_ver()` / `win32_edition()`) |

### Блок `hardware` — оборудование
| Параметр | Описание |
|---|---|
| `machine` | Архитектура процессора (`x86_64`, `AMD64`, `arm64`...) |
| `processor` | Название процессора, если ОС его сообщает |
| `architecture_bits` | Разрядность Python-процесса (`32bit`/`64bit`) |
| `architecture_linkage` | Формат бинарей (`ELF`, `WindowsPE` и т.п.) |
| `cpu_count_logical` | Количество логических ядер CPU (`os.cpu_count()`) |
| `cpu_count_physical` | Количество физических ядер *(требует `psutil`)* |
| `total_memory_bytes` / `total_memory_gb` | Объём оперативной памяти *(требует `psutil`)* |

### Блок `python` — интерпретатор
| Параметр | Описание |
|---|---|
| `version` | Версия Python |
| `implementation` | Реализация (`CPython`, `PyPy`...) |
| `compiler` | Компилятор, которым собран интерпретатор |
| `build` | Номер сборки и дата |
| `executable_path` | Путь к исполняемому файлу интерпретатора |

### Блок `user_and_host` — пользователь и хост
| Параметр | Описание |
|---|---|
| `hostname` | Имя компьютера |
| `fqdn` | Полное доменное имя |
| `local_ip` | Локальный IP-адрес |
| `username` | Имя текущего пользователя ОС |
| `home_dir` | Домашняя директория пользователя |
| `current_working_dir` | Текущая рабочая директория |
| `path_separator` | Разделитель путей (`/` или `\`) |

### Блок `filesystem` — файловая система
| Параметр | Описание |
|---|---|
| `checked_path` | Проверяемый раздел (`/` на Unix, системный диск на Windows) |
| `total_bytes` / `used_bytes` / `free_bytes` / `free_gb` | Общий/занятый/свободный объём диска |

### Блок `locale_and_time` — локаль и время
| Параметр | Описание |
|---|---|
| `timezone_names` | Названия часового пояса (зима/лето) |
| `utc_offset_seconds` | Смещение от UTC в секундах |
| `system_locale_language` / `system_locale_encoding` | Язык и кодировка локали |
| `system_boot_time_iso` | Время загрузки системы *(требует `psutil`)* |
| `uptime_seconds` | Время работы системы в секундах *(требует `psutil`)* |

### Блок `environment` — окружение процесса
| Параметр | Описание |
|---|---|
| `env_variables_count` | Количество переменных окружения |
| `path_entries_count` | Количество путей в переменной `PATH` |
| `temp_dir` | Директория для временных файлов |

Итого собирается **около 35 параметров**, сгруппированных в 7
смысловых блоков — баланс между полнотой картины о системе и
читаемостью результата.

## Пример результата

Файл `example_output_linux.json` в этом репозитории содержит реальный
пример JSON, полученный при запуске скрипта на Linux-машине.

## Размещение в репозитории

```bash
git init
git add my_script.py requirements.txt README.md example_output_linux.json
git commit -m "Lab1: cross-platform OS info collector"
git branch -M main
git remote add origin <URL_вашего_репозитория>
git push -u origin main
```
