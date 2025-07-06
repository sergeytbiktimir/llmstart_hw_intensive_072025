import os
import base64
import sys
from src.llm_models import encrypt_key

LLM_DECRYPT_KEY_ENV = "LLM_MODEL_DECRYPT_KEY"

def main():
    if len(sys.argv) < 2:
        print("Usage: python encrypt_llm_key.py <api_key> [master_key_base64]")
        sys.exit(1)
    api_key = sys.argv[1]
    master_key = sys.argv[2] if len(sys.argv) > 2 else os.environ.get(LLM_DECRYPT_KEY_ENV)
    if not master_key:
        print(f"Set {LLM_DECRYPT_KEY_ENV} or pass master_key as arg (base64-encoded 32 bytes)")
        sys.exit(1)
    encrypted = encrypt_key(api_key, master_key)
    print(f"Encrypted key (use in llm_models.json):\n{encrypted}")

if __name__ == "__main__":
    main() 