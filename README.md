# RemnaWatch

Telegram-бот для мониторинга Remnawave: статусы нод, системные метрики, трафик и реальная data-plane проверка inbound'ов через `sing-box`.

Проект не парсит subscription URL. Все параметры берутся из Remnawave API, потому что подписки могут зависеть от User-Agent/HWID и не являются надежным источником для мониторинга.

## Что мониторится

- **Ноды**: `UP / DOWN / DISABLED / UNKNOWN` по `/api/nodes`.
- **Метрики железа**: CPU cores, RAM, LoadAvg. Если список `/api/nodes` не содержит метрики, бот делает детальный запрос `/api/nodes/{uuid}` и читает также вложенный блок `system`.
- **Трафик нод**: `trafficUsedBytes`, `trafficLimitBytes`, `trafficResetDay`, `isTrafficTrackingActive`.
- **Inbound'ы / hosts**: бот собирает временный `sing-box` конфиг из `/api/hosts`, `/api/config-profiles/inbounds` и `node.configProfile.activeInbounds`, запускает SOCKS-прокси и делает HTTP probe через реальный inbound.
- **Wrong IP**: если выходной IP не совпадает с ожидаемым IP или DNS-резолвом host address — отправляется отдельный алерт.
- **Новые объекты**: новые ноды/хосты после discovery не включаются автоматически — админ включает их в Telegram.

## Поддерживаемые проверки inbound'ов

| Протокол | Network | Статус |
|---|---:|---|
| VLESS + Reality | TCP | поддерживается, `flow=xtls-rprx-vision`, без `transport: tcp` |
| VLESS + Reality | gRPC | поддерживается, `flow=""`, `transport.type=grpc` |
| Hysteria2 | hysteria | поддерживается, password = `monitor_user.vlessUuid` |
| VLESS + Reality | XHTTP | не проверяется через sing-box, статус `SKIPPED_UNSUPPORTED` |

## Важные исправления текущей версии

- Метрики больше не показывают `0/1 MB`: поддержаны `memoryTotal/memoryUsed/loadAvg/cpus` как на верхнем уровне, так и внутри `system`.
- Значения памяти считаются как bytes и отображаются в MiB.
- В БД сохраняются `sni`, `fingerprint`, `allowInsecure`, `isDisabled`, `path`, `host`, `expected_ip` из `/api/hosts`.
- SOCKS-проверки работают через `httpx[socks]`.
- Ошибки `sing-box` больше не выбрасываются в `/dev/null`: stderr сохраняется и пишется в лог при падении.
- `get_or_create_incident` сделан атомарным через `INSERT OR IGNORE`, поэтому ручная проверка и scheduler не ловят `UNIQUE constraint failed`.
- DISABLED-ноды имеют нормальные тексты:
  - `⚪ Нода X отключена в панели Remnawave`
  - `✅ Нода X снова включена в панели Remnawave`
- Telegram UI закрыт по `ADMIN_IDS`.
- Добавлен периодический discovery и защита от наложения одинаковых проверок.

## Быстрый старт через Docker

### 1. Клонирование

```bash
git clone https://github.com/Rrezzak09VPN/RemnaWatch.git
cd RemnaWatch
```

### 2. Конфиг

```bash
cp .env.example .env
nano .env
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

`MONITOR_USER_UUID` — UUID активного пользователя Remnawave, через которого бот будет проверять inbound'ы. У пользователя должны быть доступны нужные squads/hosts, статус должен быть `ACTIVE`.

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
Building sing-box config for Node-1: protocol=vless, network=tcp, security=reality, sni=..., fingerprint=firefox
sing-box started for Node-1 on 127.0.0.1:20001 pid=...
Inbound Node-1: HEALTHY (IP: ...)
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

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python -m src.main
```

## Telegram интерфейс

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

После первого запуска нажмите `/setup` или `🆕 Новые объекты` и включите только те ноды/hosts, которые нужно мониторить.

## Настройки в SQLite

Настраиваются из Telegram UI или через таблицу `settings`:

| Key | Default | Назначение |
|---|---:|---|
| `nodes_interval_seconds` | 60 | проверка статуса нод |
| `metrics_interval_seconds` | 60 | проверка RAM/Load |
| `traffic_interval_seconds` | 120 | проверка расхода трафика |
| `inbounds_interval_seconds` | 300 | data-plane проверка inbound'ов |
| `discovery_interval_seconds` | 600 | автообнаружение новых/удаленных объектов |
| `singbox_parallel_count` | 2 | параллельные sing-box проверки |
| `fail_threshold` | 3 | сколько ошибок подряд до алерта |
| `recovery_threshold` | 2 | сколько успехов подряд до recovery |
| `alert_cooldown_seconds` | 3600 | повторный алерт активного инцидента |
| `traffic_warn_percent` | 90 | предупреждение по лимиту трафика |

Для `disabled` и `traffic_limit` алерт отправляется с первого обнаружения.

## Диагностика

### Метрики всё равно пустые

Проверьте, отдает ли ваша панель метрики:

```bash
curl -s -H "Authorization: Bearer $REMNA_API_TOKEN" \
  "$REMNA_API_URL/api/nodes/<NODE_UUID>" | python3 -m json.tool | grep -iE "cpu|memory|load|system"
```

Бот ищет поля:

- `memoryTotal`
- `memoryUsed`
- `memoryFree`
- `loadAvg`
- `cpus`

на верхнем уровне объекта и внутри `system`.

### Inbound не проверяется

Смотрите лог:

```bash
docker compose logs -f remnawatch | grep -E "Building sing-box|sing-box|Inbound"
```

Статусы:

- `HEALTHY` — трафик прошел.
- `WARNING` — трафик прошел, но выходной IP не совпал.
- `BROKEN` — трафик не прошел или sing-box упал.
- `SKIPPED_UNSUPPORTED` — например XHTTP.
- `DISABLED` — host выключен в Remnawave.
- `CONFIG_ERROR` — бот не нашел raw inbound/config inbound.

### SOCKS ошибка в httpx

Убедитесь, что установлен пакет из requirements:

```txt
httpx[socks]==0.27.0
```

## Безопасность

- Никогда не коммитьте `.env`.
- Если Remnawave API token или GitHub PAT попал в чат, лог или git history — немедленно отзовите его и создайте новый.
- `.env.example` содержит только placeholders.
- Telegram-команды доступны только `ADMIN_IDS`.

## Структура

```text
src/
  api/remnawave_api.py        # Remnawave API client
  checks/nodes_checker.py     # control-plane статус нод
  checks/metrics_checker.py   # RAM/Load checker
  checks/traffic_checker.py   # traffic checker
  checks/inbound_checker.py   # sing-box data-plane checker
  checks/probe.py             # HTTP probes через SOCKS
  checks/singbox_runner.py    # lifecycle sing-box процесса
  alert/engine.py             # anti-flap/cooldown/recovery
  scheduler/manager.py        # APScheduler + locks
  telegram/                  # aiogram UI
  database.py                 # SQLite schema + migrations
```

## Лицензия

MIT
