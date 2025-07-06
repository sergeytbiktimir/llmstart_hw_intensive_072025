"""
Абстракция и реализации каталога услуг для LLM Telegram-ассистента.
- ServiceCatalog (интерфейс)
- FileServiceCatalog (чтение из JSON)
- DBServiceCatalog (чтение из БД через storage)
Оформление по code_conventions.md.
"""
import os
import json
from typing import List, Dict, Optional
from storage import storage

class ServiceCatalog:
  """Базовый интерфейс каталога услуг."""
  def get_services(self) -> List[Dict]:
    raise NotImplementedError

class FileServiceCatalog(ServiceCatalog):
  """Каталог услуг из JSON-файла."""
  def __init__(self, file_path: Optional[str] = None):
    self.file_path = file_path or os.path.join(os.path.dirname(__file__), 'services_catalog.json')
  def get_services(self) -> List[Dict]:
    with open(self.file_path, encoding='utf-8') as f:
      return json.load(f)

class DBServiceCatalog(ServiceCatalog):
  """Каталог услуг из БД (таблица services)."""
  def get_services(self) -> List[Dict]:
    # Таблица services: id, name, description
    with storage._get_connection() as conn:
      c = conn.cursor()
      c.execute('SELECT id, name, description FROM services')
      return [
        {"id": row[0], "name": row[1], "description": row[2]}
        for row in c.fetchall()
      ]

# Экземпляр по умолчанию (из файла)
service_catalog = FileServiceCatalog() 