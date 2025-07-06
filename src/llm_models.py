import os
import json
import base64
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
except ImportError:
    raise ImportError("Для работы с шифрованием ключей необходим пакет 'cryptography'. Установите его через conda или pip.")
from typing import List, Dict, Optional

LLM_MODELS_FILE = os.environ.get("LLM_MODELS_FILE") or os.path.join(os.path.dirname(__file__), "llm_models.json")
DEFAULT_LLM_MODEL = os.environ.get("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
LLM_DECRYPT_KEY_ENV = "LLM_MODEL_DECRYPT_KEY"


def _get_master_key() -> bytes:
    key = os.environ.get(LLM_DECRYPT_KEY_ENV)
    if not key:
        raise RuntimeError(f"Переменная окружения {LLM_DECRYPT_KEY_ENV} не задана!")
    key_bytes = base64.urlsafe_b64decode(key)
    if len(key_bytes) != 32:
        raise ValueError("Мастер-ключ должен быть 32 байта (base64-encoded)")
    return key_bytes


def encrypt_key(api_key: str, master_key_b64: str) -> str:
    key = base64.urlsafe_b64decode(master_key_b64)
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(api_key.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.urlsafe_b64encode(iv + ct).decode()


def decrypt_key(encrypted_api_key: str) -> str:
    key = _get_master_key()
    data = base64.urlsafe_b64decode(encrypted_api_key)
    iv, ct = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode()


def load_llm_models(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        models = json.load(f)
    for m in models:
        if "encrypted_api_key" in m:
            m["api_key"] = decrypt_key(m["encrypted_api_key"])
    return models


class LLMModels:
    def __init__(self, source: Optional[str] = None):
        self.source = source or LLM_MODELS_FILE
        self._models = self._load_models()

    def _load_models(self) -> List[Dict]:
        if not os.path.exists(self.source):
            return []
        with open(self.source, encoding="utf-8") as f:
            models = json.load(f)
        for m in models:
            if "encrypted_api_key" in m:
                m["api_key"] = decrypt_key(m["encrypted_api_key"])
        return models

    def get_models(self) -> List[Dict]:
        return self._models

    def get_model_by_name(self, name: str) -> Optional[Dict]:
        for m in self._models:
            if m["name"] == name:
                return m
        return None

    def get_default_model(self) -> Optional[Dict]:
        return self.get_model_by_name(DEFAULT_LLM_MODEL)

llm_models = LLMModels() 