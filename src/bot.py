"""
Минимальный Telegram-бот для консультаций.
Приветствует пользователя и собирает контактные данные.
Секреты — только через .env (python-dotenv).
"""
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, CallbackContext
import json
from src.storage import storage
from src.service_catalog import service_catalog
from src.logger import logger
from telegram.constants import ChatAction

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN is not set in the environment. Please set it in your .env file.')

ASK_NAME, ASK_CONTACT = range(2)
FAQ_FILE = os.path.join(os.path.dirname(__file__), 'faq_prompts.json')

async def save_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
  """Отправляет сообщение пользователю и сохраняет его в истории как assistant_reply."""
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  msg = getattr(update, 'message', None)
  if msg and hasattr(msg, 'reply_text'):
    await msg.reply_text(text)
  if user_id is not None:
    storage.save_history(user_id, 'assistant_reply', text)
  logger.log('DEBUG', text, user_id, event_type='assistant_reply')

def is_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_data = getattr(context, 'user_data', None)
    return isinstance(user_data, dict) and 'faqs' in user_data

async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  print("user_message_handler called")
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  msg = getattr(update, 'message', None)
  text = (getattr(msg, 'text', '') or '').strip()
  if user_id is not None:
    storage.save_history(user_id, 'user_message', text)
  logger.log('INFO', text, user_id, event_type='user_message')
  user_data = getattr(context, 'user_data', None)
  if user_data is not None and isinstance(user_data, dict) and 'faqs' in user_data:
    await answer_faq(update, context)
    return
  if text.startswith('/'):
    return
  # Индикация "бот печатает"
  if msg and hasattr(msg, 'chat'):
    try:
      await context.bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)
    except Exception as e:
      logger.log('DEBUG', f'Chat action error: {e}', user_id, event_type='chat_action')
  try:
    from src.llm_client import llm_client
    response = await llm_client.generate([{"role": "user", "content": text}], user_id=user_id)
    logger.log('INFO', f'LLM response: {response}', user_id, event_type='assistant_reply')
    logger.log('DEBUG', f'LLM response: {response}', user_id, event_type='assistant_reply')
  except Exception as e:
    logger.log('ERROR', f'LLM error: {e}', user_id, event_type='llm_error')
    response = 'Извините, произошла ошибка при обращении к ИИ.'
  if msg and hasattr(msg, 'reply_text'):
    await msg.reply_text(response)
  if user_id is not None:
    storage.save_history(user_id, 'assistant_reply', response)
  logger.log('DEBUG', response, user_id, event_type='assistant_reply')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  if user_id is not None:
    storage.save_history(user_id, 'user_message', '/start')
    logger.log('INFO', '/start', user_id, event_type='user_message')
  text = 'Здравствуйте! Я LLM-ассистент. Как вас зовут?'
  await save_and_reply(update, context, text)
  return ASK_NAME

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  text = (getattr(getattr(update, 'message', None), 'text', '') or '').strip()
  if user_id is not None:
    storage.save_history(user_id, 'user_message', text)
  logger.log('DEBUG', text, user_id, event_type='user_message')
  context.user_data['name'] = text
  reply = f'Спасибо, {text}! Пожалуйста, отправьте ваш телефон или ник в Telegram.'
  await save_and_reply(update, context, reply)
  return ASK_CONTACT

async def save_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  contact = (getattr(getattr(update, 'message', None), 'text', '') or '').strip()
  name = 'Неизвестно'
  user_data = getattr(context, 'user_data', None)
  if user_data is not None and isinstance(user_data, dict):
    name = user_data.get('name', 'Неизвестно')
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  if user_id is not None:
    storage.save_history(user_id, 'user_message', contact)
    logger.log('DEBUG', contact, user_id, event_type='user_message')
    storage.save_contact(user_id, name, contact)
    storage.save_history(user_id, 'contact_submitted', f'name={name}, contact={contact}')
    logger.log('INFO', f'name={name}, contact={contact}', user_id, event_type='contact_submitted')
  reply = f'Спасибо, {name}! Мы свяжемся с вами при необходимости.'
  await save_and_reply(update, context, reply)
  return ConversationHandler.END

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  if user_id is not None:
    storage.save_history(user_id, 'user_message', '/faq')
    logger.log('INFO', '/faq', user_id, event_type='user_message')
  with open(FAQ_FILE, encoding='utf-8') as f:
    faqs = json.load(f)
  questions = [f"{i+1}. {item['question']}" for i, item in enumerate(faqs)]
  text = 'Часто задаваемые вопросы:\n' + '\n'.join(questions)
  text += '\n\nОтправьте номер или текст вопроса для получения ответа.'
  context.user_data['faqs'] = faqs
  if user_id is not None:
    storage.save_history(user_id, 'faq_list_shown')
    logger.log('INFO', 'faq_list_shown', user_id, event_type='faq')
  await save_and_reply(update, context, text)

async def answer_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  faqs = None
  user_data = getattr(context, 'user_data', None)
  if user_data is not None and isinstance(user_data, dict):
    faqs = user_data.get('faqs')
  if not faqs:
    return
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  text = (getattr(getattr(update, 'message', None), 'text', '') or '').strip()
  if user_id is not None:
    storage.save_history(user_id, 'user_message', text)
  logger.log('DEBUG', text, user_id, event_type='user_message')
  answer = None
  if text.isdigit():
    idx = int(text) - 1
    if isinstance(faqs, list) and 0 <= idx < len(faqs):
      item = faqs[idx]
      if isinstance(item, dict):
        answer = item.get('answer')
  else:
    for item in faqs:
      if text.lower() in item['question'].lower():
        answer = item['answer']
        break
  if answer:
    if user_id is not None:
      storage.save_history(user_id, 'faq_answered', f'question={text}')
      logger.log('INFO', f'faq_answered: {text}', user_id, event_type='faq')
    await save_and_reply(update, context, answer)
  else:
    if user_id is not None:
      storage.save_history(user_id, 'faq_not_found', f'question={text}')
      logger.log('WARNING', f'faq_not_found: {text}', user_id, event_type='faq')
    await save_and_reply(update, context, 'Вопрос не найден. Пожалуйста, выберите из списка.')

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Показывает список услуг из каталога."""
  services = service_catalog.get_services()
  user = getattr(update, 'effective_user', None)
  user_id = getattr(user, 'id', None)
  if not services:
    text = 'Каталог услуг временно недоступен.'
    logger.log('WARNING', text, user_id, event_type='services')
  else:
    text = 'Наши услуги:\n'
    for s in services:
      text += f"\n{s['id']}. {s['name']}\n{s['description']}\n"
    logger.log('INFO', 'services_list_shown', user_id, event_type='services')
  await save_and_reply(update, context, text)

def handle_unknown(update, context):
    """Обработка неизвестной команды (для тестов и fallback)."""
    user_id = getattr(getattr(update, 'effective_user', None), 'id', None)
    msg = getattr(update, 'message', None)
    text = getattr(msg, 'text', '')
    logger.log('WARNING', f'Неизвестная команда: {text}', user_id, event_type='unknown_command')
    if msg and hasattr(msg, 'reply_text'):
        msg.reply_text('Извините, команда не распознана. Пожалуйста, используйте /start, /faq или /services.')

def main() -> None:
  """Запуск Telegram-бота."""
  logger.log('INFO', 'Bot started')
  if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN is not set in the environment. Please set it in your .env file.')
  application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
      ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_contact)],
      ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_contact_handler)],
    },
    fallbacks=[]
  )
  application.add_handler(conv_handler)
  application.add_handler(CommandHandler('faq', faq))
  application.add_handler(CommandHandler('services', services))
  # Универсальный handler для всех пользовательских сообщений (user_message)
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler))
  application.run_polling()

if __name__ == '__main__':
  main() 