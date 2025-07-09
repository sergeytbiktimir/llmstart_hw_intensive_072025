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

  def get_contacts(self):
    with self.get_connection() as conn:
      c = conn.cursor()
      c.execute('SELECT user_id, name, contact, created_at FROM contacts')
      return [
        {"user_id": row[0], "name": row[1], "contact": row[2], "created_at": row[3]}
        for row in c.fetchall()
      ]

  def get_history(self, user_id=None):
    with self.get_connection() as conn:
      c = conn.cursor()
      if user_id is not None:
        c.execute('SELECT user_id, action, details, created_at FROM history WHERE user_id=?', (user_id,))
      else:
        c.execute('SELECT user_id, action, details, created_at FROM history')
      return [
        {"user_id": row[0], "action": row[1], "details": row[2], "created_at": row[3]}
        for row in c.fetchall()
      ]

  def get_recent_history(self, user_id: int, limit: int = 10):
    """Возвращает последние limit сообщений пользователя из истории."""
    from src.logger import logger
    logger.log('DEBUG', f'get_recent_history: user_id={user_id}, limit={limit}', user_id, event_type='storage_query')
    with self.get_connection() as conn:
      c = conn.cursor()
      c.execute(
        """
        SELECT user_id, action, details, created_at FROM history
        WHERE user_id=? AND action IN ('user_message', 'assistant_reply')
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit)
      )
      rows = c.fetchall()
      logger.log('DEBUG', f'get_recent_history: returned {len(rows)} rows (user+assistant only)', user_id, event_type='storage_query')
      # Возвращаем в хронологическом порядке (от старых к новым)
      return [
        {"user_id": row[0], "action": row[1], "details": row[2], "created_at": row[3]}
        for row in reversed(rows)
      ]

# Экземпляр хранилища по умолчанию
storage = SQLiteStorage() 