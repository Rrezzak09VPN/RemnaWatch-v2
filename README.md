# RemnaWatch v2

Telegram-бот для мониторинга [Remnawave](https://remna.st): статусы нод, системные метрики (RAM/CPU), трафик и реальная data-plane проверка inbound'ов через `sing-box`.

Это вторая версия проекта ([первая — RemnaWatch](https://github.com/Rrezzak09VPN/RemnaWatch)). Бот не парсит subscription URL — все параметры берутся напрямую из Remnawave API.

## Что нового в v2

- **Ротация логов** — `RotatingFileHandler`: 20 MB на файл, 5 бэкапов (максимум ~100 MB на диске). Диагностический спам API-ответов переведён на уровень DEBUG.
- **Метрики починены** — `memoryTotal / memoryUsed / memoryFree / loadAvg / cpus` читаются из корня объекта ноды (как реально отдаёт API). Если `memoryUsed` отсутствует, вычисляется как `memoryTotal − memoryFree`. Предупреждение «no metrics» пишется один раз на ноду, а не каждые 60 секунд.
- **Строгая очередь проверок inbound'ов** — хосты проверяются последовательно, в порядке панели, с прогрессом в логах (`Checking host 3/7: ...`) и жёстким таймаутом **60 секунд на хост**. Один «мёртвый» хост больше не блокирует очередь на 9+ минут.
- **Порядок как в панели** — ноды и хосты сортируются по `viewPosition` из Remnawave API (в списках Telegram и в очереди проверок). Порядок переживает перезапуск.
- **Запрет неподдерживаемых протоколов в UI** — `xhttp / tuic / hysteria` показываются как `🚫 ... (не поддерживается)` и не включаются в мониторинг (валидация и в клавиатуре, и на сервере).
- **Корректные алерты** — отключённая нода теперь `🔴` (был белый кружок), тексты восстановления описывают нормальное состояние (`✅ Inbound X снова пропускает трафик` вместо противоречивого «восстановлено — не пропускает трафик»).
- **Русифицированный интерфейс** — статусы в Telegram на русском (`Активна / Недоступна / Работает / Не работает / Пропущен...`). В БД и логах остаются английские коды для совместимости.
- **Кнопка Menu** — слева от поля ввода: `/start`, `/status`, `/setup`, `/help`.
- **Навигация** — кнопки «◀️ Назад» во всех подменю и «❌ Отмена» при вводе порогов (с корректным сбросом FSM-состояния).

## Что мониторится

- **Ноды**: статусы по `/api/nodes` (в UI: Активна / Недоступна / Отключена / Неизвестно).
- **Метрики железа**: CPU cores, RAM, LoadAvg — из корня объекта ноды; при отсутствии в списке делается детальный запрос `/api/nodes/{uuid}`.
- **Трафик нод**: `trafficUsedBytes`, `trafficLimitBytes`, `trafficResetDay`, `isTrafficTrackingActive`.
- **Inbound'ы / hosts**: бот собирает временный `sing-box` конфиг из `/api/hosts`, `/api/config-profiles/inbounds` и `node.configProfile.activeInbounds`, поднимает SOCKS-прокси и делает HTTP-probe через реальный inbound.
- **Wrong IP**: если выходной IP не совпадает с ожидаемым IP или DNS-резолвом адреса хоста — отдельный алерт.
- **Новые объекты**: после discovery новые ноды/хосты не включаются автоматически — админ включает их в Telegram (`/setup` или «🆕 Новые объекты»).

## Поддерживаемые проверки inbound'ов

| Протокол | Network | Статус |
|---|---:|---|
| VLESS + Reality | TCP | поддерживается, `flow=xtls-rprx-vision` |
| VLESS + Reality | gRPC | поддерживается, `flow=""`, `transport.type=grpc` |
| Hysteria2 | hysteria | поддерживается, password = `monitor_user.vlessUuid` |
| VLESS + Reality | XHTTP | не поддерживается sing-box: в UI помечен 🚫, в проверки не попадает |
| TUIC / Hysteria (v1) | — | не поддерживается: в UI помечен 🚫 |

## Быстрый старт через Docker

### 1. Клонирование

```bash
git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2
```

### 2. Конфигурация

Вариант А — вручную:

```bash
cp .env.example .env
nano .env
```

Вариант Б — интерактивный мастер:

```bash
python3 install.py
```

Заполните:

```env
BOT_TOKEN=123456:ABC-your_bot_token_here
ADMIN_IDS=123456789

REMNA_API_URL=https://panel.example.com
REMNA_API_TOKEN=your_remnawave_api_jwt_token
MONITOR_USER_UUID=00000000-0000-0000-0000-000000000000

SINGBOX_BIN=/usr/local/bin/sing-box
DB_PATH=./data/bot.db
LOG_PATH=./logs/bot.log
TZ=Europe/Moscow
```

`MONITOR_USER_UUID` — UUID активного пользователя Remnawave, через которого бот будет проверять inbound'ы. Пользователь должен иметь доступ к нужным squads/hosts и статус `ACTIVE`.

### 3. Запуск

```bash
docker compose up -d --build
```

### 4. Логи

```bash
docker compose logs -f remnawatch
```

Ожидаемые строки после включения объектов:

```text
Metrics Node-1: RAM 512/961 MiB (53.2%), CPU 1, Load 0.20 / 0.10 / 0.05
Inbound check started: 7 hosts, 5 config inbounds (sequential)
Checking host 1/7: Node-1
sing-box started for Node-1 on 127.0.0.1:20001 pid=...
Inbound Node-1: HEALTHY (IP: ...)
Checking host 2/7: Node-2
...
```

## Установка без Docker

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip wget ca-certificates

wget -qO /tmp/sing-box.tar.gz \
  https://github.com/SagerNet/sing-box/releases/download/v1.11.5/sing-box-1.11.5-linux-amd64.tar.gz

echo "be0c0f8d7d7feaa09821d52ab1c07c2a202a234c8c6002c1538c7d048de82f3d  /tmp/sing-box.tar.gz" | sha256sum -c -
tar -xzf /tmp/sing-box.tar.gz -C /tmp
sudo mv /tmp/sing-box-1.11.5-linux-amd64/sing-box /usr/local/bin/
sudo chmod +x /usr/local/bin/sing-box

git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env

python -m src.main
```

## Обновление с RemnaWatch v1

База данных совместима: при первом запуске v2 автоматически выполняются миграции (добавляется колонка `view_position` и др.). Достаточно:

```bash
git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2
cp /path/to/old/RemnaWatch/.env .env      # перенести конфиг
cp -r /path/to/old/RemnaWatch/data ./data # перенести БД (опционально)
docker compose up -d --build
```

## Telegram интерфейс

Кнопка **Menu** (слева от поля ввода): `/start` — главное меню, `/status` — общий статус, `/setup` — настройка мониторинга, `/help` — справка.

Главное меню:

- `📊 Общий статус`
- `🖥️ Ноды`
- `🌐 Inbound'ы`
- `📈 Метрики нод`
- `🚦 Трафик нод`
- `⏱️ Интервалы`
- `⚙️ Пороги`
- `🔢 Параллелизм`
- `🆕 Новые объекты`
- `📜 История алертов`
- `🔄 Проверить сейчас`

После первого запуска нажмите `/setup` или «🆕 Новые объекты» и включите только те ноды/hosts, которые нужно мониторить.

## Настройки в SQLite

Настраиваются из Telegram UI или через таблицу `settings`:

| Key | Default | Назначение |
|---|---:|---|
| `nodes_interval_seconds` | 60 | проверка статуса нод |
| `metrics_interval_seconds` | 60 | проверка RAM/Load |
| `traffic_interval_seconds` | 120 | проверка расхода трафика |
| `inbounds_interval_seconds` | 300 | data-plane проверка inbound'ов |
| `discovery_interval_seconds` | 600 | автообнаружение новых/удалённых объектов |
| `singbox_parallel_count` | 2 | (v2: не используется — проверки строго последовательные) |
| `fail_threshold` | 3 | сколько ошибок подряд до алерта |
| `recovery_threshold` | 2 | сколько успехов подряд до recovery |
| `alert_cooldown_seconds` | 3600 | повторный алерт активного инцидента |
| `traffic_warn_percent` | 90 | предупреждение по лимиту трафика |

Для `disabled` и `traffic_limit` алерт отправляется с первого обнаружения.

> **Примечание:** начиная с v2 inbound'ы проверяются строго последовательно (один за другим, таймаут 60 с на хост). Настройка `singbox_parallel_count` и меню «🔢 Параллелизм» оставлены для совместимости, но на проверку inbound'ов не влияют.

## Диагностика

### Метрики пустые

Проверьте, отдаёт ли панель метрики:

```bash
curl -s -H "Authorization: Bearer $REMNA_API_TOKEN" \
  "$REMNA_API_URL/api/nodes" | python3 -m json.tool | grep -iE "memoryTotal|memoryUsed|memoryFree|loadAvg|cpus"
```

Бот ищет поля `memoryTotal`, `memoryUsed`, `memoryFree`, `loadAvg`, `cpus` **в корне объекта ноды**. Если `memoryUsed` отсутствует, он вычисляется из `memoryTotal − memoryFree`. Предупреждение `no metrics in API response` пишется один раз на ноду до восстановления метрик.

### Inbound не проверяется

```bash
docker compose logs -f remnawatch | grep -E "Checking host|Building sing-box|Inbound"
```

Статусы (в БД/логах — английские, в Telegram UI — русские):

| Код | В UI | Значение |
|---|---|---|
| `HEALTHY` | Работает | трафик прошёл |
| `WARNING` | Предупреждение | трафик прошёл, но выходной IP не совпал |
| `BROKEN` | Не работает | трафик не прошёл, sing-box упал или таймаут 60 с |
| `SKIPPED_UNSUPPORTED` | Пропущен (не поддерживается) | xhttp/tuic/hysteria |
| `DISABLED` | Отключена | host выключен в Remnawave |
| `CONFIG_ERROR` | Ошибка конфигурации | не найден raw/config inbound |

### Логи слишком большие

В v2 логи ротируются автоматически: `bot.log` + `bot.log.1 ... bot.log.5`, максимум ~100 MB. Если нужно ещё меньше — уменьшите `maxBytes`/`backupCount` в `src/main.py` (`setup_logging`).

### Порядок нод не совпадает с панелью

Порядок берётся из поля `viewPosition` API и обновляется при каждом discovery (раз в `discovery_interval_seconds`). После перестановки нод в панели подождите до 10 минут или нажмите «🔄 Проверить сейчас».

## Безопасность

- Никогда не коммитьте `.env` (он в `.gitignore`).
- Если Remnawave API token, Telegram bot token или GitHub PAT попал в чат/лог/git history — немедленно отзовите его и создайте новый.
- `.env.example` содержит только placeholders.
- Telegram-команды доступны только `ADMIN_IDS`.

## Структура

```text
src/
  api/remnawave_api.py        # Remnawave API client
  checks/nodes_checker.py     # control-plane статус нод
  checks/metrics_checker.py   # RAM/Load (метрики из корня объекта ноды)
  checks/traffic_checker.py   # traffic checker
  checks/inbound_checker.py   # последовательный sing-box data-plane checker (60s timeout)
  checks/probe.py             # HTTP probes через SOCKS
  checks/singbox_runner.py    # lifecycle sing-box процесса
  alert/engine.py             # anti-flap/cooldown/recovery, русские тексты алертов
  scheduler/manager.py        # APScheduler + locks
  telegram/bot.py             # aiogram init, кнопка Menu, /status /help
  telegram/keyboards.py       # клавиатуры, переводы статусов, фильтр xhttp
  telegram/handlers/          # aiogram UI handlers
  database.py                 # SQLite schema + миграции (view_position и др.)
  main.py                     # запуск, ротация логов
```

## Лицензия

MIT
