#!/bin/bash
# Скрипт для macOS: шифрует API-ключ для LLM моделей
# Использует переменную LLM_MODEL_DECRYPT_KEY из .env или окружения

if [ -z "$1" ]; then
  echo "Usage: $0 <api_key>"
  exit 1
fi

API_KEY="$1"
MASTER_KEY="${LLM_MODEL_DECRYPT_KEY}"

if [ -z "$MASTER_KEY" ]; then
  # Попробовать загрузить из .env
  if [ -f .env ]; then
    export $(grep LLM_MODEL_DECRYPT_KEY .env | xargs)
    MASTER_KEY="${LLM_MODEL_DECRYPT_KEY}"
  fi
fi

if [ -z "$MASTER_KEY" ]; then
  echo "Error: LLM_MODEL_DECRYPT_KEY is not set in environment or .env file."
  exit 2
fi

python3 -c "import base64, os, sys; from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes; from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives import padding; key=base64.urlsafe_b64decode('$MASTER_KEY'); iv=os.urandom(16); padder=padding.PKCS7(128).padder(); padded=padder.update('$API_KEY'.encode())+padder.finalize(); cipher=Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()); encryptor=cipher.encryptor(); ct=encryptor.update(padded)+encryptor.finalize(); print(base64.urlsafe_b64encode(iv+ct).decode())" 