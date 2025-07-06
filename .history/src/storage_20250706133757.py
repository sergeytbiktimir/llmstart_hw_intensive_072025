"""
Модуль для работы с SQLite: хранение контактов и истории обращений.
Оформление по code_conventions.md.
"""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'contacts.db')

CREATE_CONTACTS = '''
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  name TEXT,
  contact TEXT,
  created_at TEXT
);
'''

CREATE_HISTORY = '''
CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT,
  details TEXT,
  created_at TEXT
);
'''

def init_db():
  """Инициализация базы данных и таблиц."""
  os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
  with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute(CREATE_CONTACTS)
    c.execute(CREATE_HISTORY)
    conn.commit()

def save_contact(user_id: int, name: str, contact: str) -> None:
  """Сохраняет контактные данные пользователя."""
  now = datetime.utcnow().isoformat()
  with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute(
      'INSERT INTO contacts (user_id, name, contact, created_at) VALUES (?, ?, ?, ?)',
      (user_id, name, contact, now)
    )
    conn.commit()

def save_history(user_id: int, action: str, details: str = None) -> None:
  """Сохраняет событие/действие пользователя."""
  now = datetime.utcnow().isoformat()
  with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute(
      'INSERT INTO history (user_id, action, details, created_at) VALUES (?, ?, ?, ?)',
      (user_id, action, details, now)
    )
    conn.commit()

init_db() 