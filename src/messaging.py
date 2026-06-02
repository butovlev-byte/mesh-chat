"""Высокоуровневая логика обмена сообщениями."""
import asyncio
import uuid
from typing import Optional

from config import TTL_DEFAULT
from crypto_utils import CryptoManager
from database import Database
from mesh_network import MeshNetwork, MeshMessage


class MessagingService:
    """Сервис сообщений — шифрование, хранение, отправка."""

    def __init__(self, crypto: CryptoManager, mesh: MeshNetwork, db: Database):
        self.crypto = crypto
        self.mesh = mesh
        self.db = db
        self.my_id = crypto.node_id

    async def send_text(self, text: str, recipient_id: str,
                        recipient_pubkey: str) -> str:
        """Отправка зашифрованного текстового сообщения."""
        # Шифруем
        encrypted = self.crypto.encrypt(text, recipient_pubkey)
        # Подписываем оригинал
        signature = self.crypto.sign(text)

        msg_id = await self.mesh.send_message(
            content=text,  # для ретрансляции (опционально)
            recipient_id=recipient_id,
            encrypted_payload=encrypted,
            signature=signature,
        )

        # Сохраняем в БД
        self.db.save_message(
            msg_id=msg_id,
            sender_id=self.my_id,
            recipient_id=recipient_id,
            content=text,
            encrypted_payload=str(encrypted),
            signature=signature,
        )
        return msg_id

    async def send_broadcast(self, text: str) -> str:
        """Отправка нешифрованного широковещательного сообщения."""
        signature = self.crypto.sign(text)
        msg_id = await self.mesh.send_broadcast(text)
        self.db.save_message(
            msg_id=msg_id,
            sender_id=self.my_id,
            content=text,
            signature=signature,
        )
        return msg_id

    def on_message_received(self, msg: MeshMessage, from_addr):
        """Обработчик входящих сообщений от mesh-сети."""
        # Сохраняем в БД
        self.db.save_message(
            msg_id=msg.msg_id,
            sender_id=msg.sender_id,
            recipient_id=msg.recipient_id,
            content=msg.content,
            encrypted_payload=str(msg.encrypted_payload) if msg.encrypted_payload else None,
            signature=msg.signature,
            hops=msg.hops,
            ttl=msg.ttl,
        )

        # Обновляем контакт (heartbeat)
        if msg.msg_type == "heartbeat":
            self.db.update_node(
                node_id=msg.sender_id,
                ip_address=from_addr[0] if from_addr else None,
            )
            # Если пришёл публичный ключ — сохраняем контакт
            if msg.content and "BEGIN PUBLIC KEY" in msg.content:
                self.db.add_contact(
                    node_id=msg.sender_id,
                    public_key=msg.content,
                    display_name=f"Peer_{msg.sender_id[:6]}",
                )

        # Проверяем подпись если есть
        if msg.signature and msg.content:
            contact = self.db.get_contact(msg.sender_id)
            if contact:
                valid = self.crypto.verify(msg.content, msg.signature, contact["public_key"])
                if not valid:
                    print(f"[Messaging] Неверная подпись от {msg.sender_id}")

    def get_chat_history(self, contact_id: str, limit: int = 100) -> list:
        """История переписки с контактом."""
        return self.db.get_messages(contact_id, limit)

    def get_contacts(self) -> list:
        """Список контактов."""
        return self.db.get_all_contacts()

    def decrypt_message(self, encrypted_payload: dict) -> str:
        """Расшифровка сообщения."""
        return self.crypto.decrypt(encrypted_payload)
