"""
Минимальный Telegram-бот для консультаций.
Приветствует пользователя и собирает контактные данные.
Секреты — только через .env (python-dotenv).
"""
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import json
from storage import storage
from service_catalog import service_catalog
from logger import logger
import logging

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

ASK_NAME, ASK_CONTACT = range(2)
FAQ_FILE = os.path.join(os.path.dirname(__file__), 'faq_prompts.json')

async def save_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
  """Отправляет сообщение пользователю и сохраняет его в истории как assistant_reply."""
  user_id = update.effective_user.id
  await update.message.reply_text(text)
  storage.save_history(user_id, 'assistant_reply', text)
  logger.log('INFO', text, user_id, event_type='assistant_reply')

async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Сохраняет любое пользовательское сообщение в истории как user_message."""
  user_id = update.effective_user.id
  text = update.message.text.strip()
  storage.save_history(user_id, 'user_message', text)
  logger.log('INFO', text, user_id, event_type='user_message')
  # Не отвечаем, если это не команда/FAQ (чтобы не было эха)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  user_id = update.effective_user.id
  storage.save_history(user_id, 'user_message', '/start')
  logger.log('INFO', '/start', user_id, event_type='user_message')
  text = 'Здравствуйте! Я LLM-ассистент. Как вас зовут?'
  await save_and_reply(update, context, text)
  logger.log('INFO', text, user_id, event_type='assistant_reply')
  return ASK_NAME

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  user_id = update.effective_user.id
  text = update.message.text.strip()
  storage.save_history(user_id, 'user_message', text)
  logger.log('INFO', text, user_id, event_type='user_message')
  context.user_data['name'] = text
  reply = f'Спасибо, {text}! Пожалуйста, отправьте ваш телефон или ник в Telegram.'
  await save_and_reply(update, context, reply)
  logger.log('INFO', reply, user_id, event_type='assistant_reply')
  return ASK_CONTACT

async def save_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  contact = update.message.text.strip()
  name = context.user_data.get('name', 'Неизвестно')
  user_id = update.effective_user.id
  storage.save_history(user_id, 'user_message', contact)
  logger.log('INFO', contact, user_id, event_type='user_message')
  storage.save_contact(user_id, name, contact)
  storage.save_history(user_id, 'contact_submitted', f'name={name}, contact={contact}')
  logger.log('INFO', f'name={name}, contact={contact}', user_id, event_type='contact_submitted')
  reply = f'Спасибо, {name}! Мы свяжемся с вами при необходимости.'
  await save_and_reply(update, context, reply)
  logger.log('INFO', reply, user_id, event_type='assistant_reply')
  return ConversationHandler.END

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  storage.save_history(user_id, 'user_message', '/faq')
  logger.log('INFO', '/faq', user_id, event_type='user_message')
  with open(FAQ_FILE, encoding='utf-8') as f:
    faqs = json.load(f)
  questions = [f"{i+1}. {item['question']}" for i, item in enumerate(faqs)]
  text = 'Часто задаваемые вопросы:\n' + '\n'.join(questions)
  text += '\n\nОтправьте номер или текст вопроса для получения ответа.'
  context.user_data['faqs'] = faqs
  storage.save_history(user_id, 'faq_list_shown')
  logger.log('INFO', 'faq_list_shown', user_id, event_type='faq')
  await save_and_reply(update, context, text)
  logger.log('INFO', text, user_id, event_type='assistant_reply')

async def answer_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  faqs = context.user_data.get('faqs')
  if not faqs:
    return
  user_id = update.effective_user.id
  text = update.message.text.strip()
  storage.save_history(user_id, 'user_message', text)
  logger.log('INFO', text, user_id, event_type='user_message')
  answer = None
  if text.isdigit():
    idx = int(text) - 1
    if 0 <= idx < len(faqs):
      answer = faqs[idx]['answer']
  else:
    for item in faqs:
      if text.lower() in item['question'].lower():
        answer = item['answer']
        break
  if answer:
    storage.save_history(user_id, 'faq_answered', f'question={text}')
    logger.log('INFO', f'faq_answered: {text}', user_id, event_type='faq')
    await save_and_reply(update, context, answer)
    logger.log('INFO', answer, user_id, event_type='assistant_reply')
  else:
    storage.save_history(user_id, 'faq_not_found', f'question={text}')
    logger.log('WARNING', f'faq_not_found: {text}', user_id, event_type='faq')
    await save_and_reply(update, context, 'Вопрос не найден. Пожалуйста, выберите из списка.')
    logger.log('INFO', 'Вопрос не найден. Пожалуйста, выберите из списка.', user_id, event_type='assistant_reply')

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Показывает список услуг из каталога."""
  services = service_catalog.get_services()
  user_id = update.effective_user.id
  if not services:
    text = 'Каталог услуг временно недоступен.'
    logger.log('WARNING', text, user_id, event_type='services')
  else:
    text = 'Наши услуги:\n'
    for s in services:
      text += f"\n{s['id']}. {s['name']}\n{s['description']}\n"
    logger.log('INFO', 'services_list_shown', user_id, event_type='services')
  await save_and_reply(update, context, text)
  logger.log('INFO', text, user_id, event_type='assistant_reply')

def main() -> None:
  """Запуск Telegram-бота."""
  logger.log('INFO', 'Bot started')
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
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_faq))
  application.add_handler(CommandHandler('services', services))
  # Универсальный handler для всех пользовательских сообщений (user_message)
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler))
  application.run_polling()

if __name__ == '__main__':
  main() 