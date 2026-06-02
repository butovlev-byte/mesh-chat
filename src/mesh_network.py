"""Mesh-сеть — Wi-Fi Direct, Bluetooth и ретрансляция сообщений."""
import asyncio
import json
import socket
import threading
import time
import uuid
from typing import Callable, Dict, Set
from dataclasses import dataclass, asdict

from config import MESH_PORT, WIFI_DIRECT_PORT, MAX_HOPS, TTL_DEFAULT


@dataclass
class MeshMessage:
    """Структура сообщения в mesh-сети."""
    msg_id: str
    sender_id: str
    recipient_id: str = None
    content: str = ""
    encrypted_payload: dict = None
    signature: str = ""
    hops: int = 0
    ttl: int = TTL_DEFAULT
    timestamp: float = 0.0
    msg_type: str = "chat"  # chat, broadcast, heartbeat, discovery

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str):
        d = json.loads(data)
        return cls(**d)


class MeshNetwork:
    """Ядро mesh-сети — прослушивание, ретрансляция, обнаружение узлов."""

    def __init__(self, node_id: str, crypto_manager):
        self.node_id = node_id
        self.crypto = crypto_manager
        self.peers: Dict[str, dict] = {}  # node_id -> {ip, port, last_seen}
        self.seen_messages: Set[str] = set()  # дедупликация
        self.running = False
        self.server = None
        self._callbacks: list[Callable] = []
        self._lock = threading.Lock()

    def add_message_callback(self, callback: Callable):
        """Подписка на входящие сообщения."""
        self._callbacks.append(callback)

    def _notify(self, msg: MeshMessage, from_addr: tuple = None):
        """Уведомление всех подписчиков."""
        for cb in self._callbacks:
            try:
                cb(msg, from_addr)
            except Exception as e:
                print(f"[Mesh] Callback error: {e}")

    # === TCP-сервер (основной транспорт) ===
    async def start_server(self, host: str = "0.0.0.0", port: int = MESH_PORT):
        """Запуск TCP-сервера для приёма сообщений."""
        self.running = True
        self.server = await asyncio.start_server(
            self._handle_connection, host, port
        )
        addr = self.server.sockets[0].getsockname()
        print(f"[Mesh] Сервер запущен на {addr}")
        async with self.server:
            await self.server.serve_forever()

    async def _handle_connection(self, reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter):
        """Обработка входящего соединения."""
        addr = writer.get_extra_info("peername")
        try:
            data = await reader.read(65536)
            if not data:
                return
            msg = MeshMessage.from_json(data.decode("utf-8"))
            await self._process_message(msg, addr)
        except Exception as e:
            print(f"[Mesh] Ошибка обработки от {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _process_message(self, msg: MeshMessage, from_addr: tuple):
        """Обработка полученного сообщения."""
        # Дедупликация
        if msg.msg_id in self.seen_messages:
            return
        self.seen_messages.add(msg.msg_id)

        # TTL проверка
        if msg.ttl <= 0:
            return

        # Обновление списка пиров
        if from_addr:
            with self._lock:
                self.peers[msg.sender_id] = {
                    "ip": from_addr[0],
                    "port": from_addr[1] if len(from_addr) > 1 else MESH_PORT,
                    "last_seen": time.time(),
                }

        # Если сообщение для нас — уведомляем UI
        if msg.recipient_id == self.node_id or msg.recipient_id is None:
            self._notify(msg, from_addr)

        # Ретрансляция (flooding с ограничением hops)
        if msg.hops < MAX_HOPS:
            msg.hops += 1
            msg.ttl -= 1
            await self._flood_message(msg, exclude=from_addr[0] if from_addr else None)

    async def _flood_message(self, msg: MeshMessage, exclude: str = None):
        """Рассылка сообщения всем известным пирам."""
        tasks = []
        with self._lock:
            peers_copy = dict(self.peers)
        for peer_id, peer_info in peers_copy.items():
            if exclude and peer_info.get("ip") == exclude:
                continue
            tasks.append(self._send_to_peer(msg, peer_info))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_peer(self, msg: MeshMessage, peer_info: dict):
        """Отправка сообщения конкретному пиру."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(peer_info["ip"], peer_info.get("port", MESH_PORT)),
                timeout=5.0
            )
            writer.write(msg.to_json().encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            # Peer недоступен — удалим позже при cleanup
            pass

    # === Отправка сообщений ===
    async def send_message(self, content: str, recipient_id: str = None,
                          encrypted_payload: dict = None, signature: str = "") -> str:
        """Отправка сообщения в сеть."""
        msg = MeshMessage(
            msg_id=str(uuid.uuid4()),
            sender_id=self.node_id,
            recipient_id=recipient_id,
            content=content,
            encrypted_payload=encrypted_payload,
            signature=signature,
            hops=0,
            ttl=TTL_DEFAULT,
            timestamp=time.time(),
        )
        self.seen_messages.add(msg.msg_id)
        await self._flood_message(msg)
        return msg.msg_id

    async def send_broadcast(self, content: str):
        """Отправка широковещательного сообщения."""
        return await self.send_message(content, recipient_id=None)

    # === Discovery ===
    async def start_discovery(self):
        """Периодическая отправка heartbeat для обнаружения."""
        while self.running:
            heartbeat = MeshMessage(
                msg_id=str(uuid.uuid4()),
                sender_id=self.node_id,
                msg_type="heartbeat",
                content=self.crypto.public_key_pem,
                timestamp=time.time(),
                ttl=3,
            )
            self.seen_messages.add(heartbeat.msg_id)
            await self._flood_message(heartbeat)
            await asyncio.sleep(10)

    # === Bluetooth (заглушка для Android) ===
    async def start_bluetooth_server(self):
        """BLE/GATT сервер для Android (заглушка)."""
        # TODO: реализовать через bleak/pybluez при сборке под Android
        print("[Mesh] Bluetooth сервер — заглушка (требует Android SDK)")
        while self.running:
            await asyncio.sleep(60)

    def stop(self):
        """Остановка сети."""
        self.running = False
        if self.server:
            self.server.close()
