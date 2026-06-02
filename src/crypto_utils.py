"""Модуль шифрования — ECIES на эллиптических кривых."""
import os
import hashlib
import json
from pathlib import Path

from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

from config import KEYS_DIR, CURVE_NAME


class CryptoManager:
    """Управление ключами и ECIES-шифрованием."""

    def __init__(self, identity: str = "default"):
        self.identity = identity
        self.private_key_path = KEYS_DIR / f"{identity}_private.pem"
        self.public_key_path = KEYS_DIR / f"{identity}_public.pem"
        self._private_key = None
        self._public_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Загружает или генерирует пару ключей."""
        if self.private_key_path.exists():
            with open(self.private_key_path, "rt") as f:
                self._private_key = ECC.import_key(f.read())
            with open(self.public_key_path, "rt") as f:
                self._public_key = ECC.import_key(f.read())
        else:
            self._private_key = ECC.generate(curve=CURVE_NAME)
            self._public_key = self._private_key.public_key()
            with open(self.private_key_path, "wt") as f:
                f.write(self._private_key.export_key(format="PEM"))
            with open(self.public_key_path, "wt") as f:
                f.write(self._public_key.export_key(format="PEM"))

    @property
    def public_key_pem(self) -> str:
        """Возвращает публичный ключ в PEM-формате."""
        return self._public_key.export_key(format="PEM")

    @property
    def public_key_bytes(self) -> bytes:
        """Возвращает публичный ключ как байты (compressed)."""
        return self._public_key.export_key(format="SEC1")

    @property
    def node_id(self) -> str:
        """Уникальный ID узла = SHA256 от публичного ключа."""
        return hashlib.sha256(self.public_key_bytes).hexdigest()[:16]

    def encrypt(self, plaintext: str, recipient_pubkey_pem: str) -> dict:
        """ECIES-шифрование для получателя."""
        recipient_key = ECC.import_key(recipient_pubkey_pem)

        # Эфемерный ключ
        ephemeral = ECC.generate(curve=CURVE_NAME)
        shared_point = recipient_key.pointQ * ephemeral.d
        shared_secret = int(shared_point.x).to_bytes(32, "big")

        # KDF
        aes_key = HKDF(shared_secret, 32, b"", SHA256)

        # AES-GCM
        nonce = os.urandom(12)
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

        return {
            "ephemeral_pubkey": ephemeral.public_key().export_key(format="PEM"),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
            "tag": tag.hex(),
        }

    def decrypt(self, encrypted_data: dict) -> str:
        """ECIES-расшифровка."""
        ephemeral_key = ECC.import_key(encrypted_data["ephemeral_pubkey"])
        shared_point = ephemeral_key.pointQ * self._private_key.d
        shared_secret = int(shared_point.x).to_bytes(32, "big")

        aes_key = HKDF(shared_secret, 32, b"", SHA256)
        cipher = AES.new(
            aes_key,
            AES.MODE_GCM,
            nonce=bytes.fromhex(encrypted_data["nonce"])
        )
        plaintext = cipher.decrypt_and_verify(
            bytes.fromhex(encrypted_data["ciphertext"]),
            bytes.fromhex(encrypted_data["tag"])
        )
        return plaintext.decode("utf-8")

    def sign(self, message: str) -> str:
        """Подпись сообщения ECDSA."""
        from Crypto.Signature import DSS
        h = SHA256.new(message.encode("utf-8"))
        signer = DSS.new(self._private_key, "fips-186-3")
        return signer.sign(h).hex()

    def verify(self, message: str, signature: str, pubkey_pem: str) -> bool:
        """Проверка подписи."""
        from Crypto.Signature import DSS
        try:
            key = ECC.import_key(pubkey_pem)
            h = SHA256.new(message.encode("utf-8"))
            verifier = DSS.new(key, "fips-186-3")
            verifier.verify(h, bytes.fromhex(signature))
            return True
        except Exception:
            return False
