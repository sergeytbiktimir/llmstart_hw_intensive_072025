"""
Абстракция слоя хранения для LLM Telegram-ассистента.
Storage (базовый класс), SQLiteStorage (реализация по умолчанию).
Оформление по code_conventions.md.
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'contacts.db')

class Storage:
  """Базовый интерфейс для слоя хранения."""
  def save_contact(self, user_id: int, name: str, contact: str) -> None:
    raise NotImplementedError

  def save_history(self, user_id: int, action: str, details: str = "") -> None:
    raise NotImplementedError

class SQLiteStorage(Storage):
  """Реализация слоя хранения на SQLite."""
  def __init__(self, db_path: Optional[str] = None):
    self.db_path = db_path or DB_PATH
    self._init_db()

  def _init_db(self):
    os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    with sqlite3.connect(self.db_path) as conn:
      c = conn.cursor()
      c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          name TEXT,
          contact TEXT,
          created_at TEXT
        );
      ''')
      c.execute('''
        CREATE TABLE IF NOT EXISTS history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          action TEXT,
          details TEXT,
          created_at TEXT
        );
      ''')
      conn.commit()

  def save_contact(self, user_id: int, name: str, contact: str) -> None:
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(self.db_path) as conn:
      c = conn.cursor()
      c.execute(
        'INSERT INTO contacts (user_id, name, contact, created_at) VALUES (?, ?, ?, ?)',
        (user_id, name, contact, now)
      )
      conn.commit()

  def save_history(self, user_id: int, action: str, details: str = "") -> None:
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(self.db_path) as conn:
      c = conn.cursor()
      c.execute(
        'INSERT INTO history (user_id, action, details, created_at) VALUES (?, ?, ?, ?)',
        (user_id, action, details or "", now)
      )
      conn.commit()

  def get_connection(self):
    """Публичный метод для получения соединения с БД (для внешних модулей)."""
    return sqlite3.connect(self.db_path)

# Экземпляр хранилища по умолчанию
storage = SQLiteStorage() 