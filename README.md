# RemnaWatch v2

> 🦾 Telegram-бот для мониторинга [Remnawave](https://remna.st): статусы нод, метрики (RAM/CPU), трафик и data-plane проверка inbound'ов через `sing-box`.

Бот не парсит subscription URL — все данные берутся напрямую из Remnawave API.

---

## 🆕 Что нового в v2

- ✅ **Hysteria2** — теперь поддерживается, `alpn: ["h3"]`, пароль = `monitor_user.vlessUuid`
- 🔧 **Метрики починены** — читаются из корня ноды или `response.system.info/stats`, `memoryUsed` вычисляется если отсутствует
- ⚡ **Быстрые алерты** — inbound алерт за ~2–4 мин (было 8–15), `fail_threshold=2`, кд 30 мин
- 📋 **Строгая очередь** — хосты проверяются последовательно, таймаут 60 с на хост
- 🚀 **Discovery быстрее** — каждые 300 с (было 600)
- 🔢 **Порядок как в панели** — сортировка по `viewPosition`
- 📦 **Ротация логов** — 20 MB на файл, 5 бэкапов (~100 MB макс)
- 🇷🇺 **Русский интерфейс** — статусы в Telegram на русском, в БД/логах английские
- 🧭 **Навигация** — кнопка Menu, «◀️ Назад» и «❌ Отмена» во всех меню

---

## 📡 Что мониторится

- 🖥️ **Ноды**: статусы (Активна / Недоступна / Отключена)
- 🧠 **Метрики**: CPU, RAM, LoadAvg
- 🚦 **Трафик**: used/limit, предупреждение при 90%
- 🌐 **Inbound'ы**: реальная проверка через sing-box + SOCKS5 probe
- 🛡️ **Wrong IP**: алерт если IP не совпадает с ожидаемым
- 🆕 **Новые/удалённые объекты** — автообнаружение, админ включает вручную

## ✅ Поддерживаемые inbound'ы

| Протокол | Network | Статус |
|---|---|---|
| VLESS + Reality | TCP | ✅ `flow=xtls-rprx-vision` |
| VLESS + Reality | gRPC | ✅ `flow=""`, `transport.type=grpc` |
| Hysteria2 | hysteria2 | ✅ пароль = `vlessUuid`, `alpn: ["h3"]` |
| VLESS + Reality | XHTTP | ❌ не поддерживается |
| TUIC | — | ❌ не поддерживается |

---

## 🐳 Быстрый старт (Docker)

```bash
git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2
cp .env.example .env       # или python3 install.py
# Заполните .env своими данными
docker compose up -d --build
```

## 🖥️ Установка без Docker

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip wget ca-certificates
# Установка sing-box v1.11.5
wget -qO /tmp/sing-box.tar.gz https://github.com/SagerNet/sing-box/releases/download/v1.11.5/sing-box-1.11.5-linux-amd64.tar.gz
# Проверка контрольной суммы
echo "be0c0f8d7d7feaa09821d52ab1c07c2a202a234c8c6002c1538c7d048de82f3d /tmp/sing-box.tar.gz" | sha256sum -c -
tar -xzf /tmp/sing-box.tar.gz -C /tmp
sudo mv /tmp/sing-box-1.11.5-linux-amd64/sing-box /usr/local/bin/
git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 install.py
python -m src.main
```

---

## 🗑️ Полное удаление

**Docker:**
```bash
docker compose down && docker rmi remnawatch-v2 2>/dev/null
cd .. && rm -rf RemnaWatch-v2
```

**Без Docker:**
```bash
pkill -f "python.*src.main" 2>/dev/null
pkill -f "sing-box" 2>/dev/null
rm -rf RemnaWatch-v2 venv
sudo rm -f /usr/local/bin/sing-box
```

---

## 🤖 Telegram интерфейс

Кнопка **Menu**: `/start`, `/status`, `/setup`, `/help`

Главное меню:
📊 Статус | 🖥️ Ноды | 🌐 Inbound'ы | 📈 Метрики | 🚦 Трафик | ⏱️ Интервалы | ⚙️ Пороги | 🔢 Параллелизм | 🆕 Новые объекты | 📜 История алертов | 🔄 Проверить сейчас

---

## ⚙️ Настройки (SQLite)

| Ключ | По умолч. | Описание |
|---|---|---|
| `nodes_interval_seconds` | 60 | проверка нод |
| `metrics_interval_seconds` | 60 | проверка метрик |
| `traffic_interval_seconds` | 120 | проверка трафика |
| `inbounds_interval_seconds` | 120 | проверка inbound'ов |
| `discovery_interval_seconds` | 300 | автообнаружение |
| `fail_threshold` | 3 | ошибок до алерта (ноды/метрики/трафик) |
| `inbound_fail_threshold` | 2 | ошибок до алерта (inbound'ы) |
| `recovery_threshold` | 2 | успехов до восстановления |
| `alert_cooldown_seconds` | 1800 | повторный алерт (сек) |
| `traffic_warn_percent` | 90 | порог предупреждения по трафику |

> 🔢 `singbox_parallel_count` не используется — проверки строго последовательные.

---

## 🔍 Диагностика

**Метрики пустые:**
```bash
curl -s -H "Authorization: Bearer $REMNA_API_TOKEN" "$REMNA_API_URL/api/nodes" | python3 -m json.tool | grep -iE "memoryTotal|memoryUsed|memoryFree|loadAvg|cpus"
```

**Inbound не проверяется:**
```bash
docker compose logs -f remnawatch | grep -E "Checking host|Building sing-box|Inbound"
```

**Статусы inbound'ов:**

| Код | В UI | Что значит |
|---|---|---|
| `HEALTHY` | ✅ Работает | трафик прошёл |
| `WARNING` | ⚠️ Предупреждение | IP не совпал |
| `BROKEN` | 🔴 Не работает | таймаут / ошибка |
| `SKIPPED_UNSUPPORTED` | ⏭️ Пропущен | xhttp/tuic |
| `DISABLED` | ⚪ Отключена | выключен в панели |
| `CONFIG_ERROR` | ❌ Ошибка конфига | inbound не найден |

**Hysteria2 не работает?** Проверьте версию sing-box ≥ 1.8.0, `alpn: ["h3"]` и пароль = `vlessUuid` пользователя.

**Удалённые объекты** автоматически архивируются при discovery и исключаются из проверок.

---

## 📁 Структура проекта

```
src/
├── api/remnawave_api.py       # клиент Remnawave API
├── checks/
│   ├── nodes_checker.py       # статус нод
│   ├── metrics_checker.py     # RAM/CPU/Load
│   ├── traffic_checker.py     # трафик
│   ├── inbound_checker.py     # data-plane проверка
│   ├── probe.py               # HTTP probe через SOCKS5
│   └── singbox_runner.py      # запуск sing-box
├── alert/engine.py            # антифлад, кд, восстановление
├── scheduler/manager.py       # APScheduler
├── telegram/
│   ├── bot.py                 # aiogram, кнопка Menu
│   ├── keyboards.py           # клавиатуры, статусы
│   ├── handlers/              # обработчики кнопок
│   ├── middleware.py          # проверка админов
│   └── notifier.py            # отправка алертов
├── crypto/x25519.py           # X25519 для Reality
├── discovery.py               # автообнаружение
├── database.py                # SQLite
├── config.py                  # pydantic-settings
└── main.py                    # точка входа
```

---

## ❤️ Community

Сделано для сикретнова чатика камунити Remnawave

---

## 📄 Лицензия

MIT
