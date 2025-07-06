# LLM Telegram-ассистент (MVP)

## Документация и ссылки
- [docs/product_idea.md](docs/product_idea.md) — продуктовая идея, цели и задачи
- [docs/design_vision.md](docs/design_vision.md) — техническое и архитектурное видение
- [docs/code_conventions.md](docs/code_conventions.md) — стандарты кода и соглашения
- [tasklist.md](mdc:tasklist.md) — центральный документ управления задачами, статусами и итерациями
- [commitmessage.mdc](mdc:commitmessage.mdc) — шаблоны и правила оформления коммитов
- [trash/git_commit_change.md](trash/git_commit_change.md) — инструкция по изменению сообщений коммитов через git rebase

## Архитектурные принципы и политика безопасности
- Все секретные данные (токены, ключи, пароли, приватные URL) хранятся только во внешнем файле `.env`, который не коммитится в репозиторий
- Для загрузки переменных окружения используется python-dotenv
- Пример .env приведён только в этом README.md, в других документах — только ссылка на этот раздел
- Абстракции для всех источников данных (каталог услуг, логи, промпты, хранилище контактов и истории)
- Возможность смены источника данных без изменения остального кода (Storage, ServiceCatalog, Logger)
- Централизованное логирование с поддержкой разных источников (файл, БД, облако), настройка уровня через LOG_LEVEL
- Покрытие тестами ключевых модулей, pull request для всех изменений
- Соблюдение структуры репозитория и стандартов кода

## Работа с задачами и git
- Управление задачами ведётся строго через [tasklist.md](mdc:tasklist.md) по согласованной структуре (статусы, шаги, итерации, приоритеты)
- Перед началом работы над задачей — согласование плана, после завершения — обновление статуса и комментариев в tasklist.md
- Для коммитов используется шаблон: `<type>(урок<step>): <summary>` с подробным описанием на русском (см. [commitmessage.mdc](mdc:commitmessage.mdc))
- Для изменения истории коммитов используйте инструкцию из [trash/git_commit_change.md](trash/git_commit_change.md)

## Описание
Минимальный Telegram-бот для консультаций. Приветствует пользователя и собирает контактные данные. Все секреты — только через .env.

## Быстрый старт
1. Скопируйте `.env.example` в `.env` и укажите свой токен Telegram-бота.
2. Установите зависимости: `conda env create -f environment.yml`
3. Активируйте окружение: `conda activate llm-tg-bot`
4. Запустите бота: `python -m src`

## Пример .env
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
OPENAI_API_KEY=your-openai-api-key-here
```

## Переменные окружения
| Переменная           | Обязательность | Назначение                                      | Пример значения                                 |
|----------------------|:--------------:|-------------------------------------------------|-------------------------------------------------|
| TELEGRAM_BOT_TOKEN   |     Да         | Токен Telegram-бота                             | your-telegram-bot-token-here                    |
| OPENAI_API_KEY       |     Нет        | Ключ OpenAI API для работы с LLM                | your-openai-api-key-here                        |
| DB_PATH              |     Нет        | Путь к базе данных SQLite                       | data/contacts.db                                |
| LOG_LEVEL            |     Нет        | Уровень логирования (INFO/DEBUG/WARNING/ERROR)  | INFO                                            |
| POSTGRES_DSN         |     Нет        | Строка подключения к PostgreSQL                 | postgresql://user:pass@host:port/dbname         |
| MYSQL_DSN            |     Нет        | Строка подключения к MySQL                      | mysql://user:pass@host:port/dbname              |
| MONGO_URI            |     Нет        | Строка подключения к MongoDB                    | mongodb://user:pass@host:port/dbname            |
| CATALOG_API_URL      |     Нет        | URL облачного API каталога услуг                | https://example.com/api/services                |
| CATALOG_API_KEY      |     Нет        | Ключ доступа к облачному API каталога услуг     | your-api-key                                    |

Описание:
- Обязательные переменные должны быть обязательно заданы в .env для запуска бота.
- Необязательные переменные используются только при соответствующей конфигурации (например, смена типа хранилища или источника каталога услуг).
- LOG_LEVEL по умолчанию INFO, если не указано иное.

## Структура проекта
- src/ — исходный код бота
- tests/ — тесты
- .env.example — пример переменных окружения
- environment.yml — зависимости
- README.md — инструкция

## Требования
- Все секреты только в .env (python-dotenv)
- Оформление кода по PEP8, snake_case, 2 пробела
- Покрытие тестами не менее 99% для ключевых модулей 

## Смена типа хранилища (БД)

По умолчанию используется SQLite (файл data/contacts.db) через класс `SQLiteStorage`.

Чтобы заменить тип хранилища (например, на файловое или внешнюю БД):
1. Реализуйте свой класс-наследник от `Storage` в `src/storage.py`.
2. В файле `src/storage.py` создайте экземпляр вашего класса вместо `SQLiteStorage`:
   ```python
   # storage = SQLiteStorage()  # по умолчанию
   storage = MyCustomStorage(...)
   ```
3. Весь код бота использует только экземпляр `storage` — менять остальной код не требуется.

Чтобы изменить путь к базе данных SQLite:
- Передайте путь при создании экземпляра:
  ```python
  storage = SQLiteStorage(db_path='data/my_db.db')
  ``` 

## Использование внешней БД (PostgreSQL, MySQL, MongoDB и др.)

1. Реализуйте класс-наследник от `Storage` (см. `src/storage.py`) для вашей СУБД.
2. Все параметры подключения храните в `.env`. Примеры:
   - PostgreSQL:
     ```
     POSTGRES_DSN=postgresql://user:password@host:port/dbname
     ```
   - MySQL:
     ```
     MYSQL_DSN=mysql://user:password@host:port/dbname
     ```
   - MongoDB:
     ```
     MONGO_URI=mongodb://user:password@host:port/dbname
     ```
3. В `src/storage.py` создайте экземпляр вашего класса:
   - PostgreSQL (psycopg2):
     ```python
     import os
     import psycopg2
     from storage import Storage
     class PostgresStorage(Storage):
         def __init__(self, dsn):
             self.conn = psycopg2.connect(dsn)
         def save_contact(self, user_id, name, contact):
             with self.conn, self.conn.cursor() as c:
                 c.execute('INSERT INTO contacts (user_id, name, contact, created_at) VALUES (%s, %s, %s, NOW())', (user_id, name, contact))
         def save_history(self, user_id, action, details=""):
             with self.conn, self.conn.cursor() as c:
                 c.execute('INSERT INTO history (user_id, action, details, created_at) VALUES (%s, %s, %s, NOW())', (user_id, action, details))
     # storage = PostgresStorage(os.environ["POSTGRES_DSN"])
     ```
   - MySQL (pymysql):
     ```python
     import os
     import pymysql
     from storage import Storage
     class MySQLStorage(Storage):
         def __init__(self, dsn):
             self.conn = pymysql.connect(dsn)
         def save_contact(self, user_id, name, contact):
             with self.conn.cursor() as c:
                 c.execute('INSERT INTO contacts (user_id, name, contact, created_at) VALUES (%s, %s, %s, NOW())', (user_id, name, contact))
             self.conn.commit()
         def save_history(self, user_id, action, details=""):
             with self.conn.cursor() as c:
                 c.execute('INSERT INTO history (user_id, action, details, created_at) VALUES (%s, %s, %s, NOW())', (user_id, action, details))
             self.conn.commit()
     # storage = MySQLStorage(os.environ["MYSQL_DSN"])
     ```
   - MongoDB (pymongo):
     ```python
     import os
     import pymongo
     from storage import Storage
     class MongoStorage(Storage):
         def __init__(self, uri):
             self.client = pymongo.MongoClient(uri)
             self.db = self.client.get_default_database()
         def save_contact(self, user_id, name, contact):
             self.db.contacts.insert_one({"user_id": user_id, "name": name, "contact": contact, "created_at": datetime.utcnow()})
         def save_history(self, user_id, action, details=""):
             self.db.history.insert_one({"user_id": user_id, "action": action, "details": details, "created_at": datetime.utcnow()})
     # storage = MongoStorage(os.environ["MONGO_URI"])
     ```
4. Весь остальной код менять не требуется — используйте только экземпляр `storage`. 

## Каталог услуг: структура и смена источника

Каталог услуг реализован через абстракцию `ServiceCatalog` и может храниться в разных источниках:
- JSON-файл (по умолчанию, src/services_catalog.json)
- БД (таблица services)
- (В перспективе) облачные сервисы

### Формат услуги
```json
{
  "id": 1,
  "name": "Название услуги",
  "description": "Описание услуги"
}
```

### Пример файла src/services_catalog.json
```
[
  {
    "id": 1,
    "name": "Консультация по LLM",
    "description": "Персональная консультация по внедрению и использованию LLM в бизнесе."
  },
  {
    "id": 2,
    "name": "Анализ бизнес-процессов",
    "description": "Экспертный анализ процессов компании для поиска точек автоматизации."
  }
]
```

### Смена источника каталога

- По умолчанию используется файл:
  ```python
  from service_catalog import FileServiceCatalog
  service_catalog = FileServiceCatalog()
  ```
- Для использования БД (таблица services: id, name, description):
  ```python
  from service_catalog import DBServiceCatalog
  service_catalog = DBServiceCatalog()
  ```
- Для добавления облачного или другого источника реализуйте свой класс-наследник от ServiceCatalog.

Весь код бота использует только экземпляр `service_catalog` — менять остальной код не требуется. 

### Примеры реализации ServiceCatalog для других источников

- **PostgreSQL** (psycopg2):
  ```python
  import os
  import psycopg2
  from service_catalog import ServiceCatalog
  class PostgresServiceCatalog(ServiceCatalog):
      def __init__(self, dsn):
          self.conn = psycopg2.connect(dsn)
      def get_services(self):
          with self.conn, self.conn.cursor() as c:
              c.execute('SELECT id, name, description FROM services')
              return [
                  {"id": row[0], "name": row[1], "description": row[2]}
                  for row in c.fetchall()
              ]
  # service_catalog = PostgresServiceCatalog(os.environ["POSTGRES_DSN"])
  ```
  В .env:
  ```
  POSTGRES_DSN=postgresql://user:password@host:port/dbname
  ```

- **MongoDB** (pymongo):
  ```python
  import os
  import pymongo
  from datetime import datetime
  from service_catalog import ServiceCatalog
  class MongoServiceCatalog(ServiceCatalog):
      def __init__(self, uri):
          self.client = pymongo.MongoClient(uri)
          self.db = self.client.get_default_database()
      def get_services(self):
          return list(self.db.services.find({}, {"_id": 0}))
  # service_catalog = MongoServiceCatalog(os.environ["MONGO_URI"])
  ```
  В .env:
  ```
  MONGO_URI=mongodb://user:password@host:port/dbname
  ```

- **Облачное API** (пример):
  ```python
  import requests
  from service_catalog import ServiceCatalog
  class CloudServiceCatalog(ServiceCatalog):
      def __init__(self, api_url, api_key):
          self.api_url = api_url
          self.api_key = api_key
      def get_services(self):
          resp = requests.get(self.api_url, headers={"Authorization": f"Bearer {self.api_key}"})
          resp.raise_for_status()
          return resp.json()
  # service_catalog = CloudServiceCatalog(api_url=os.environ["CATALOG_API_URL"], api_key=os.environ["CATALOG_API_KEY"])
  ```
  В .env:
  ```
  CATALOG_API_URL=https://example.com/api/services
  CATALOG_API_KEY=your-api-key
  ``` 

## Настройка логирования

- Уровень логирования задаётся переменной окружения `LOG_LEVEL` (пример: `LOG_LEVEL=INFO`)
- Возможные значения: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- INFO — только ключевые события (запуск, команды, ошибки, смена состояния)
- DEBUG — подробные сообщения (все сообщения пользователя и ассистента, детали запросов/ответов)
- WARNING/ERROR — ошибки, сбои, подозрительные действия
- Пример для .env:
  ```
  LOG_LEVEL=INFO
  ```
- Рекомендуется использовать ротацию логов или хранение в БД/облаке для предотвращения переполнения диска
- Источник логирования можно сменить, создав нужный экземпляр Logger (см. src/logger.py) 

## Автоматическая проверка кода
Для поддержания качества и стиля кода используется:
- ruff — основной линтер (стиль, ошибки, best practices)
- black — автоформаттер (по желанию, для единообразия форматирования)
- mypy — для строгой проверки типов (опционально)
- openai, httpx — для работы с OpenAI-протоколом и LLM

Все инструменты уже добавлены в environment.yml. После изменения зависимостей обновите окружение:

```
conda env update -f environment.yml
```

Все команды выполняются в активированном conda-окружении:

- Запуск линтера: `ruff src/`
- Запуск автоформаттера: `black src/`
- Запуск проверки типов: `mypy src/`

Инструменты должны быть описаны в этом разделе и добавлены в зависимости окружения. 

## Безопасное хранение ключей LLM-моделей
- Ключи для доступа к LLM-сервисам (OpenAI, Anthropic и др.) хранятся только в зашифрованном виде в конфиге моделей (например, llm_models.json).
- Для расшифровки используется мастер-ключ, который задаётся только через переменную окружения `LLM_MODEL_DECRYPT_KEY`.
- В исходном коде и репозитории не должно быть открытых ключей для внешних сервисов.
- Пример для .env:
  ```
  LLM_MODEL_DECRYPT_KEY=your-master-decrypt-key-here
  ```
- Пример для таблицы переменных окружения:
| Переменная              | Обязательность | Назначение                                 | Пример значения                |
|-------------------------|:--------------:|--------------------------------------------|---------------------------------|
| LLM_MODEL_DECRYPT_KEY   |     Да         | Мастер-ключ для расшифровки ключей моделей | your-master-decrypt-key-here    |
- Ключи шифруются отдельно (например, AES-256 + base64), мастер-ключ только в .env. 

## Шифрование ключей для LLM-моделей
Для macOS можно использовать bash-скрипт:

```
./encrypt_llm_key_macos.sh <ваш_секретный_ключ>
```

Скрипт использует переменную LLM_MODEL_DECRYPT_KEY из .env или окружения. Если переменная не задана, скрипт завершится с ошибкой.

### Пример генерации мастер-ключа (LLM_MODEL_DECRYPT_KEY)

В Python:
```python
import os, base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
```

Скопируйте результат в .env:
```
LLM_MODEL_DECRYPT_KEY=... # вставьте сгенерированное значение
```

### Пример генерации encrypted_api_key

1. Убедитесь, что LLM_MODEL_DECRYPT_KEY задан в .env или передайте его вторым аргументом.
2. Запустите:
```
python encrypt_llm_key.py sk-...your_openai_key...
```
или
```
python encrypt_llm_key.py sk-...your_openai_key... <ваш_мастер_ключ>
```

3. Полученное значение вставьте в llm_models.json:
```json
{
  "name": "gpt-3.5-turbo",
  "service": "openai",
  "provider_model_name": "gpt-3.5-turbo",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "encrypted_api_key": "<сюда вставьте результат>"
}
``` 

## Структура llm_models.json
Каждая модель описывается следующими полями:
- `name` — уникальное имя модели внутри системы (для пользователя/чата)
- `service` — провайдер (например, openai, anthropic, lmstudio, fireworks)
- `provider_model_name` — имя/ID модели у провайдера (используется в параметре model при запросе к API)
- `endpoint` — URL для обращения к API
- `encrypted_api_key` — зашифрованный ключ (если требуется; для локальных open-weights моделей может быть пустым)

**Пример для облачного провайдера (ключ обязателен):**
```json
{
  "name": "gpt-3.5-turbo-openai",
  "service": "openai",
  "provider_model_name": "gpt-3.5-turbo",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "encrypted_api_key": "..."
}
```

**Пример для локального LMStudio (ключ не требуется):**
```json
{
  "name": "qwen3-8b-lmstudio",
  "service": "lmstudio",
  "provider_model_name": "qwen/qwen3-8b",
  "endpoint": "http://localhost:1234/v1/chat/completions"
  // encrypted_api_key отсутствует или пустой
}
```

> Для OpenAI, Fireworks, Anthropic и других облачных сервисов encrypted_api_key обязателен. Для LMStudio с open-weights и других локальных сервисов поле может быть пустым или отсутствовать. 