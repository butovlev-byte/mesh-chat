# 🔗 MeshChat — P2P Messenger

Децентрализованный мессенджер на базе mesh-сетей. Общайтесь без интернета, серверов и цензуры.

## Возможности

- 📡 **Mesh-сеть** — работает через Wi-Fi Direct и Bluetooth
- 🔐 **End-to-End шифрование** — ECIES на эллиптических кривых
- 💬 **P2P чаты** — без центральных серверов
- 📴 **Оффлайн-режим** — сообщения доставляются через соседние узлы
- 🎨 **Material Design** — современный интерфейс на KivyMD

## Установка и запуск

### Локально (Desktop)
```bash
git clone https://github.com/yourusername/mesh-chat.git
cd mesh-chat
pip install -r requirements.txt
python src/main.py
```

### Сборка APK (Android)
```bash
# Установи Buildozer
pip install buildozer cython

# Собери APK
buildozer android debug deploy run
```

## Архитектура

```
src/
├── main.py              # Точка входа
├── mesh_network.py      # Mesh-сеть
├── messaging.py         # Логика сообщений
├── crypto_utils.py      # Шифрование
├── database.py          # SQLite хранилище
├── ui/                  # Интерфейс
└── utils/               # Утилиты
```

## Лицензия
MIT
