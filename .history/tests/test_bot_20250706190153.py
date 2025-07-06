import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import types

pytestmark = pytest.mark.asyncio

# Предполагается, что в src/bot.py функции вынесены для тестирования (например, handle_start, handle_contact, handle_faq, handle_services)
# Если нет — эти тесты служат шаблоном для рефакторинга и покрытия логики

@pytest.fixture
def mock_update():
    m = MagicMock()
    m.effective_user.id = 123
    m.message.text = 'test'
    m.message.reply_text = AsyncMock()
    return m

@pytest.fixture
def mock_context():
    c = MagicMock()
    c.user_data = {}
    return c

import src.bot as bot

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_start(mock_storage, mock_logger, mock_update, mock_context):
    result = await bot.start(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()
    assert result == bot.ASK_NAME

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_ask_contact(mock_storage, mock_logger, mock_update, mock_context):
    result = await bot.ask_contact(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()
    assert result == bot.ASK_CONTACT
    assert mock_context.user_data['name'] == 'test'

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_save_contact_handler(mock_storage, mock_logger, mock_update, mock_context):
    mock_context.user_data['name'] = 'Alice'
    mock_update.message.text = '+123'
    result = await bot.save_contact_handler(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()
    mock_storage.save_contact.assert_called_with(123, 'Alice', '+123')

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_faq(mock_storage, mock_logger, mock_update, mock_context, tmp_path):
    # Подменяем FAQ_FILE на временный файл
    faqs = [{"question": "Q1", "answer": "A1"}]
    faq_file = tmp_path / 'faq.json'
    faq_file.write_text('[{"question": "Q1", "answer": "A1"}]', encoding='utf-8')
    with patch('src.bot.FAQ_FILE', str(faq_file)):
        await bot.faq(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited()
        mock_logger.log.assert_called()
        assert 'faqs' in mock_context.user_data

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_answer_faq_found(mock_storage, mock_logger, mock_update, mock_context):
    mock_context.user_data['faqs'] = [{"question": "Q1", "answer": "A1"}]
    mock_update.message.text = 'Q1'
    await bot.answer_faq(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()

@patch('src.bot.logger')
@patch('src.bot.storage')
async def test_answer_faq_not_found(mock_storage, mock_logger, mock_update, mock_context):
    mock_context.user_data['faqs'] = [{"question": "Q1", "answer": "A1"}]
    mock_update.message.text = 'unknown'
    await bot.answer_faq(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()

@patch('src.bot.logger')
@patch('src.bot.service_catalog')
async def test_services(mock_service_catalog, mock_logger, mock_update, mock_context):
    mock_service_catalog.get_services.return_value = [{"id": 1, "name": "S", "description": "D"}]
    await bot.services(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited()
    mock_logger.log.assert_called()

# Edge case: неизвестная команда
@patch('src.bot.logger')
def test_unknown_command(mock_logger, mock_update, mock_context):
    from src.bot import handle_unknown
    handle_unknown(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()
    mock_logger.log.assert_called() 