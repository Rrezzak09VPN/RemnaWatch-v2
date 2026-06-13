# RemnaWatch v2

> рџ¦ѕ Telegram-Р±РѕС‚ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° [Remnawave](https://remna.st): СЃС‚Р°С‚СѓСЃС‹ РЅРѕРґ, РјРµС‚СЂРёРєРё (RAM/CPU), С‚СЂР°С„РёРє Рё data-plane РїСЂРѕРІРµСЂРєР° inbound'РѕРІ С‡РµСЂРµР· `sing-box`.

Р‘РѕС‚ РЅРµ РїР°СЂСЃРёС‚ subscription URL вЂ” РІСЃРµ РґР°РЅРЅС‹Рµ Р±РµСЂСѓС‚СЃСЏ РЅР°РїСЂСЏРјСѓСЋ РёР· Remnawave API.

---

## рџ†• Р§С‚Рѕ РЅРѕРІРѕРіРѕ РІ v2

- вњ… **Hysteria2** вЂ” С‚РµРїРµСЂСЊ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ, `alpn: ["h3"]`, РїР°СЂРѕР»СЊ = `monitor_user.vlessUuid`
- рџ”§ **РњРµС‚СЂРёРєРё РїРѕС‡РёРЅРµРЅС‹** вЂ” С‡РёС‚Р°СЋС‚СЃСЏ РёР· РєРѕСЂРЅСЏ РЅРѕРґС‹ РёР»Рё `response.system.info/stats`, `memoryUsed` РІС‹С‡РёСЃР»СЏРµС‚СЃСЏ РµСЃР»Рё РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚
- вљЎ **Р‘С‹СЃС‚СЂС‹Рµ Р°Р»РµСЂС‚С‹** вЂ” inbound Р°Р»РµСЂС‚ Р·Р° ~2вЂ“4 РјРёРЅ (Р±С‹Р»Рѕ 8вЂ“15), `fail_threshold=2`, РєРґ 30 РјРёРЅ
- рџ“‹ **РЎС‚СЂРѕРіР°СЏ РѕС‡РµСЂРµРґСЊ** вЂ” С…РѕСЃС‚С‹ РїСЂРѕРІРµСЂСЏСЋС‚СЃСЏ РїРѕСЃР»РµРґРѕРІР°С‚РµР»СЊРЅРѕ, С‚Р°Р№РјР°СѓС‚ 60 СЃ РЅР° С…РѕСЃС‚
- рџљЂ **Discovery Р±С‹СЃС‚СЂРµРµ** вЂ” РєР°Р¶РґС‹Рµ 300 СЃ (Р±С‹Р»Рѕ 600)
- рџ”ў **РџРѕСЂСЏРґРѕРє РєР°Рє РІ РїР°РЅРµР»Рё** вЂ” СЃРѕСЂС‚РёСЂРѕРІРєР° РїРѕ `viewPosition`
- рџ“¦ **Р РѕС‚Р°С†РёСЏ Р»РѕРіРѕРІ** вЂ” 20 MB РЅР° С„Р°Р№Р», 5 Р±СЌРєР°РїРѕРІ (~100 MB РјР°РєСЃ)
- рџ‡·рџ‡є **Р СѓСЃСЃРєРёР№ РёРЅС‚РµСЂС„РµР№СЃ** вЂ” СЃС‚Р°С‚СѓСЃС‹ РІ Telegram РЅР° СЂСѓСЃСЃРєРѕРј, РІ Р‘Р”/Р»РѕРіР°С… Р°РЅРіР»РёР№СЃРєРёРµ
- рџ§­ **РќР°РІРёРіР°С†РёСЏ** вЂ” РєРЅРѕРїРєР° Menu, В«в—ЂпёЏ РќР°Р·Р°РґВ» Рё В«вќЊ РћС‚РјРµРЅР°В» РІРѕ РІСЃРµС… РјРµРЅСЋ

---

## рџ“Ў Р§С‚Рѕ РјРѕРЅРёС‚РѕСЂРёС‚СЃСЏ

- рџ–ҐпёЏ **РќРѕРґС‹**: СЃС‚Р°С‚СѓСЃС‹ (РђРєС‚РёРІРЅР° / РќРµРґРѕСЃС‚СѓРїРЅР° / РћС‚РєР»СЋС‡РµРЅР°)
- рџ§  **РњРµС‚СЂРёРєРё**: CPU, RAM, LoadAvg
- рџљ¦ **РўСЂР°С„РёРє**: used/limit, РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ РїСЂРё 90%
- рџЊђ **Inbound'С‹**: СЂРµР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° С‡РµСЂРµР· sing-box + SOCKS5 probe
- рџ›ЎпёЏ **Wrong IP**: Р°Р»РµСЂС‚ РµСЃР»Рё IP РЅРµ СЃРѕРІРїР°РґР°РµС‚ СЃ РѕР¶РёРґР°РµРјС‹Рј
- рџ†• **РќРѕРІС‹Рµ/СѓРґР°Р»С‘РЅРЅС‹Рµ РѕР±СЉРµРєС‚С‹** вЂ” Р°РІС‚РѕРѕР±РЅР°СЂСѓР¶РµРЅРёРµ, Р°РґРјРёРЅ РІРєР»СЋС‡Р°РµС‚ РІСЂСѓС‡РЅСѓСЋ

## вњ… РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ inbound'С‹

| РџСЂРѕС‚РѕРєРѕР» | Network | РЎС‚Р°С‚СѓСЃ |
|---|---|---|
| VLESS + Reality | TCP | вњ… `flow=xtls-rprx-vision` |
| VLESS + Reality | gRPC | вњ… `flow=""`, `transport.type=grpc` |
| Hysteria2 | hysteria2 | вњ… РїР°СЂРѕР»СЊ = `vlessUuid`, `alpn: ["h3"]` |
| VLESS + Reality | XHTTP | вќЊ РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ |
| TUIC | вЂ” | вќЊ РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ |

---

## рџђі Р‘С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚ (Docker)

```bash
git clone https://github.com/Rrezzak09VPN/RemnaWatch-v2.git
cd RemnaWatch-v2
cp .env.example .env       # РёР»Рё python3 install.py
# Р—Р°РїРѕР»РЅРёС‚Рµ .env СЃРІРѕРёРјРё РґР°РЅРЅС‹РјРё
docker compose up -d --build
```

## рџ–ҐпёЏ РЈСЃС‚Р°РЅРѕРІРєР° Р±РµР· Docker

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip wget ca-certificates
# РЈСЃС‚Р°РЅРѕРІРєР° sing-box v1.11.5
wget -qO /tmp/sing-box.tar.gz https://github.com/SagerNet/sing-box/releases/download/v1.11.5/sing-box-1.11.5-linux-amd64.tar.gz
# РџСЂРѕРІРµСЂРєР° РєРѕРЅС‚СЂРѕР»СЊРЅРѕР№ СЃСѓРјРјС‹
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

## рџ—‘пёЏ РџРѕР»РЅРѕРµ СѓРґР°Р»РµРЅРёРµ

**Docker:**
```bash
docker compose down && docker rmi remnawatch-v2 2>/dev/null
cd .. && rm -rf RemnaWatch-v2
```

**Р‘РµР· Docker:**
```bash
pkill -f "python.*src.main" 2>/dev/null
pkill -f "sing-box" 2>/dev/null
rm -rf RemnaWatch-v2 venv
sudo rm -f /usr/local/bin/sing-box
```

---

## рџ¤– Telegram РёРЅС‚РµСЂС„РµР№СЃ

РљРЅРѕРїРєР° **Menu**: `/start`, `/status`, `/setup`, `/help`

Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ:
рџ“Љ РЎС‚Р°С‚СѓСЃ | рџ–ҐпёЏ РќРѕРґС‹ | рџЊђ Inbound'С‹ | рџ“€ РњРµС‚СЂРёРєРё | рџљ¦ РўСЂР°С„РёРє | вЏ±пёЏ РРЅС‚РµСЂРІР°Р»С‹ | вљ™пёЏ РџРѕСЂРѕРіРё | рџ”ў РџР°СЂР°Р»Р»РµР»РёР·Рј | рџ†• РќРѕРІС‹Рµ РѕР±СЉРµРєС‚С‹ | рџ“њ РСЃС‚РѕСЂРёСЏ Р°Р»РµСЂС‚РѕРІ | рџ”„ РџСЂРѕРІРµСЂРёС‚СЊ СЃРµР№С‡Р°СЃ

---

## вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё (SQLite)

| РљР»СЋС‡ | РџРѕ СѓРјРѕР»С‡. | РћРїРёСЃР°РЅРёРµ |
|---|---|---|
| `nodes_interval_seconds` | 60 | РїСЂРѕРІРµСЂРєР° РЅРѕРґ |
| `metrics_interval_seconds` | 60 | РїСЂРѕРІРµСЂРєР° РјРµС‚СЂРёРє |
| `traffic_interval_seconds` | 120 | РїСЂРѕРІРµСЂРєР° С‚СЂР°С„РёРєР° |
| `inbounds_interval_seconds` | 120 | РїСЂРѕРІРµСЂРєР° inbound'РѕРІ |
| `discovery_interval_seconds` | 300 | Р°РІС‚РѕРѕР±РЅР°СЂСѓР¶РµРЅРёРµ |
| `fail_threshold` | 3 | РѕС€РёР±РѕРє РґРѕ Р°Р»РµСЂС‚Р° (РЅРѕРґС‹/РјРµС‚СЂРёРєРё/С‚СЂР°С„РёРє) |
| `inbound_fail_threshold` | 2 | РѕС€РёР±РѕРє РґРѕ Р°Р»РµСЂС‚Р° (inbound'С‹) |
| `recovery_threshold` | 2 | СѓСЃРїРµС…РѕРІ РґРѕ РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ |
| `alert_cooldown_seconds` | 1800 | РїРѕРІС‚РѕСЂРЅС‹Р№ Р°Р»РµСЂС‚ (СЃРµРє) |
| `traffic_warn_percent` | 90 | РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РїРѕ С‚СЂР°С„РёРєСѓ |

> рџ”ў `singbox_parallel_count` РЅРµ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ вЂ” РїСЂРѕРІРµСЂРєРё СЃС‚СЂРѕРіРѕ РїРѕСЃР»РµРґРѕРІР°С‚РµР»СЊРЅС‹Рµ.

---

## рџ”Ќ Р”РёР°РіРЅРѕСЃС‚РёРєР°

**РњРµС‚СЂРёРєРё РїСѓСЃС‚С‹Рµ:**
```bash
curl -s -H "Authorization: Bearer $REMNA_API_TOKEN" "$REMNA_API_URL/api/nodes" | python3 -m json.tool | grep -iE "memoryTotal|memoryUsed|memoryFree|loadAvg|cpus"
```

**Inbound РЅРµ РїСЂРѕРІРµСЂСЏРµС‚СЃСЏ:**
```bash
docker compose logs -f remnawatch | grep -E "Checking host|Building sing-box|Inbound"
```

**РЎС‚Р°С‚СѓСЃС‹ inbound'РѕРІ:**

| РљРѕРґ | Р’ UI | Р§С‚Рѕ Р·РЅР°С‡РёС‚ |
|---|---|---|
| `HEALTHY` | вњ… Р Р°Р±РѕС‚Р°РµС‚ | С‚СЂР°С„РёРє РїСЂРѕС€С‘Р» |
| `WARNING` | вљ пёЏ РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ | IP РЅРµ СЃРѕРІРїР°Р» |
| `BROKEN` | рџ”ґ РќРµ СЂР°Р±РѕС‚Р°РµС‚ | С‚Р°Р№РјР°СѓС‚ / РѕС€РёР±РєР° |
| `SKIPPED_UNSUPPORTED` | вЏ­пёЏ РџСЂРѕРїСѓС‰РµРЅ | xhttp/tuic |
| `DISABLED` | вљЄ РћС‚РєР»СЋС‡РµРЅР° | РІС‹РєР»СЋС‡РµРЅ РІ РїР°РЅРµР»Рё |
| `CONFIG_ERROR` | вќЊ РћС€РёР±РєР° РєРѕРЅС„РёРіР° | inbound РЅРµ РЅР°Р№РґРµРЅ |

**Hysteria2 РЅРµ СЂР°Р±РѕС‚Р°РµС‚?** РџСЂРѕРІРµСЂСЊС‚Рµ РІРµСЂСЃРёСЋ sing-box в‰Ґ 1.8.0, `alpn: ["h3"]` Рё РїР°СЂРѕР»СЊ = `vlessUuid` РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.

**РЈРґР°Р»С‘РЅРЅС‹Рµ РѕР±СЉРµРєС‚С‹** Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё Р°СЂС…РёРІРёСЂСѓСЋС‚СЃСЏ РїСЂРё discovery Рё РёСЃРєР»СЋС‡Р°СЋС‚СЃСЏ РёР· РїСЂРѕРІРµСЂРѕРє.

---

## рџ“Ѓ РЎС‚СЂСѓРєС‚СѓСЂР° РїСЂРѕРµРєС‚Р°

```
src/
в”њв”Ђв”Ђ api/remnawave_api.py       # РєР»РёРµРЅС‚ Remnawave API
в”њв”Ђв”Ђ checks/
в”‚   в”њв”Ђв”Ђ nodes_checker.py       # СЃС‚Р°С‚СѓСЃ РЅРѕРґ
в”‚   в”њв”Ђв”Ђ metrics_checker.py     # RAM/CPU/Load
в”‚   в”њв”Ђв”Ђ traffic_checker.py     # С‚СЂР°С„РёРє
в”‚   в”њв”Ђв”Ђ inbound_checker.py     # data-plane РїСЂРѕРІРµСЂРєР°
в”‚   в”њв”Ђв”Ђ probe.py               # HTTP probe С‡РµСЂРµР· SOCKS5
в”‚   в””в”Ђв”Ђ singbox_runner.py      # Р·Р°РїСѓСЃРє sing-box
в”њв”Ђв”Ђ alert/engine.py            # Р°РЅС‚РёС„Р»Р°Рґ, РєРґ, РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёРµ
в”њв”Ђв”Ђ scheduler/manager.py       # APScheduler
в”њв”Ђв”Ђ telegram/
в”‚   в”њв”Ђв”Ђ bot.py                 # aiogram, РєРЅРѕРїРєР° Menu
в”‚   в”њв”Ђв”Ђ keyboards.py           # РєР»Р°РІРёР°С‚СѓСЂС‹, СЃС‚Р°С‚СѓСЃС‹
в”‚   в”њв”Ђв”Ђ handlers/              # РѕР±СЂР°Р±РѕС‚С‡РёРєРё РєРЅРѕРїРѕРє
в”‚   в”њв”Ђв”Ђ middleware.py          # РїСЂРѕРІРµСЂРєР° Р°РґРјРёРЅРѕРІ
в”‚   в””в”Ђв”Ђ notifier.py            # РѕС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚РѕРІ
в”њв”Ђв”Ђ crypto/x25519.py           # X25519 РґР»СЏ Reality
в”њв”Ђв”Ђ discovery.py               # Р°РІС‚РѕРѕР±РЅР°СЂСѓР¶РµРЅРёРµ
в”њв”Ђв”Ђ database.py                # SQLite
в”њв”Ђв”Ђ config.py                  # pydantic-settings
в””в”Ђв”Ђ main.py                    # С‚РѕС‡РєР° РІС…РѕРґР°
```

---

## вќ¤пёЏ Community

РЎРґРµР»Р°РЅРѕ РґР»СЏ СЃРёРєСЂРµС‚РЅРѕРІР° С‡Р°С‚РёРєР° РєР°РјСѓРЅРёС‚Рё Remnawave

---

## рџ“„ Р›РёС†РµРЅР·РёСЏ

MIT
