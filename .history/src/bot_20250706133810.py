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
from storage import save_contact, save_history

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

ASK_NAME, ASK_CONTACT = range(2)
FAQ_FILE = os.path.join(os.path.dirname(__file__), 'faq_prompts.json')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  """Приветствие и запрос имени пользователя."""
  await update.message.reply_text(
    'Здравствуйте! Я LLM-ассистент. Как вас зовут?'
  )
  return ASK_NAME

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  """Запрос контактных данных после имени."""
  context.user_data['name'] = update.message.text.strip()
  await update.message.reply_text(
    'Спасибо, {0}! Пожалуйста, отправьте ваш телефон или ник в Telegram.'.format(context.user_data['name'])
  )
  return ASK_CONTACT

async def save_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  """Сохраняет контактные данные и завершает диалог."""
  contact = update.message.text.strip()
  name = context.user_data.get('name', 'Неизвестно')
  user_id = update.effective_user.id
  save_contact(user_id, name, contact)
  save_history(user_id, 'contact_submitted', f'name={name}, contact={contact}')
  await update.message.reply_text(
    f'Спасибо, {name}! Мы свяжемся с вами при необходимости.'
  )
  return ConversationHandler.END

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Показывает список FAQ и инструкции по выбору."""
  with open(FAQ_FILE, encoding='utf-8') as f:
    faqs = json.load(f)
  questions = [f"{i+1}. {item['question']}" for i, item in enumerate(faqs)]
  text = 'Часто задаваемые вопросы:\n' + '\n'.join(questions)
  text += '\n\nОтправьте номер или текст вопроса для получения ответа.'
  context.user_data['faqs'] = faqs
  user_id = update.effective_user.id
  save_history(user_id, 'faq_list_shown')
  await update.message.reply_text(text)

async def answer_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Отвечает на выбранный вопрос из FAQ."""
  faqs = context.user_data.get('faqs')
  if not faqs:
    return
  text = update.message.text.strip()
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
  user_id = update.effective_user.id
  if answer:
    save_history(user_id, 'faq_answered', f'question={text}')
    await update.message.reply_text(answer)
  else:
    save_history(user_id, 'faq_not_found', f'question={text}')
    await update.message.reply_text('Вопрос не найден. Пожалуйста, выберите из списка.')

def main() -> None:
  """Запуск Telegram-бота."""
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
  application.run_polling()

if __name__ == '__main__':
  main() 