"""Конфигурация приложения MeshChat."""
import os
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "meshchat.db"
KEYS_DIR = DATA_DIR / "keys"
KEYS_DIR.mkdir(exist_ok=True)

# Сеть
MESH_PORT = 8765
BROADCAST_INTERVAL = 5  # секунды между broadcast
MAX_HOPS = 10           # максимальное число прыжков для сообщения
TTL_DEFAULT = 300       # время жизни сообщения (сек)

# Bluetooth
BT_SERVICE_UUID = "00001101-0000-1000-8000-00805F9B34FB"
BT_SCAN_TIMEOUT = 10

# Wi-Fi Direct
WIFI_DIRECT_PORT = 8766
WIFI_DIRECT_GROUP = "MeshChat_Group"

# UI
APP_NAME = "MeshChat"
PRIMARY_COLOR = "#6200EE"
ACCENT_COLOR = "#03DAC6"
THEME_STYLE = "Dark"

# Шифрование
CURVE_NAME = "secp256k1"
KEY_SIZE = 32
