"""
Абстракция и реализации логирования для LLM Telegram-ассистента.
- Logger (интерфейс)
- FileLogger (лог в файл)
- DBLogger (лог в БД через storage)
- CloudLogger (пример интерфейса)
Оформление по code_conventions.md.
"""
import os
import json
from datetime import datetime
from typing import Optional
from src.storage import storage

LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

def should_log(level: str) -> bool:
  log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
  log_level_num = LOG_LEVELS.get(log_level, 20)
  return LOG_LEVELS.get(level, 20) >= log_level_num

class Logger:
  """Базовый интерфейс логирования."""
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    raise NotImplementedError

class FileLogger(Logger):
  """Логирование в файл (по умолчанию logs/bot.log) с ротацией по размеру (5 МБ)."""
  MAX_SIZE = 5 * 1024 * 1024  # 5 МБ
  def __init__(self, file_path: Optional[str] = None):
    env_path = os.environ.get("LOG_FILE_PATH")
    self.file_path = file_path or env_path or os.path.join(os.path.dirname(__file__), '..', 'logs', 'bot.log')
    os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
  def _rotate(self):
    if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > self.MAX_SIZE:
      ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
      rotated = f"{self.file_path}.{ts}"
      os.rename(self.file_path, rotated)
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    if not should_log(level):
      return
    self._rotate()
    record = {
      "timestamp": datetime.utcnow().isoformat(),
      "level": level,
      "user_id": user_id,
      "event_type": event_type,
      "message": message
    }
    with open(self.file_path, 'a', encoding='utf-8') as f:
      f.write(json.dumps(record, ensure_ascii=False) + '\n')

class DBLogger(Logger):
  """Логирование в БД (таблица logs)."""
  def __init__(self):
    self._init_db()
  def _init_db(self):
    with storage.get_connection() as conn:
      c = conn.cursor()
      c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          timestamp TEXT,
          level TEXT,
          user_id INTEGER,
          event_type TEXT,
          message TEXT
        );
      ''')
      conn.commit()
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    if not should_log(level):
      return
    with storage.get_connection() as conn:
      c = conn.cursor()
      c.execute(
        'INSERT INTO logs (timestamp, level, user_id, event_type, message) VALUES (?, ?, ?, ?, ?)',
        (datetime.utcnow().isoformat(), level, user_id, event_type, message)
      )
      conn.commit()

class CloudLogger(Logger):
  """Пример интерфейса для логирования в облако (реализация зависит от API)."""
  def __init__(self, api_url: str, api_key: str):
    self.api_url = api_url
    self.api_key = api_key
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    if not should_log(level):
      return
    # Пример: отправка POST-запроса на облачный endpoint
    # import requests
    # data = {...}
    # requests.post(self.api_url, headers={"Authorization": f"Bearer {self.api_key}"}, json=data)
    pass

class ConsoleLogger(Logger):
  """Логирование в консоль (stdout)."""
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    if LOG_LEVELS.get(level, 20) >= LOG_LEVELS["INFO"]:
      record = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "user_id": user_id,
        "event_type": event_type,
        "message": message
      }
      print(json.dumps(record, ensure_ascii=False))

class MultiLogger(Logger):
  """Логгер, делегирующий запись в несколько источников."""
  def __init__(self, *loggers):
    self.loggers = loggers
  def log(self, level: str, message: str, user_id: Optional[int] = None, event_type: str = "event") -> None:
    for logger in self.loggers:
      logger.log(level, message, user_id, event_type)

# Экземпляр по умолчанию: MultiLogger (файл + консоль)
logger = MultiLogger(FileLogger(), ConsoleLogger()) 