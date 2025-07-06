import pytest
from unittest.mock import MagicMock, patch

# Предполагается, что в src/bot.py функции вынесены для тестирования (например, handle_start, handle_contact, handle_faq, handle_services)
# Если нет — эти тесты служат шаблоном для рефакторинга и покрытия логики

@pytest.fixture
def mock_update():
    m = MagicMock()
    m.message.reply_text = MagicMock()
    m.message.from_user.id = 123
    m.message.text = 'test'
    return m

@pytest.fixture
def mock_context():
    return MagicMock()

@patch('src.bot.logger')
@patch('src.bot.storage')
def test_handle_start(mock_storage, mock_logger, mock_update, mock_context):
    from src.bot import handle_start
    handle_start(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()
    mock_logger.log.assert_called()

@patch('src.bot.logger')
@patch('src.bot.storage')
def test_handle_contact(mock_storage, mock_logger, mock_update, mock_context):
    from src.bot import handle_contact
    mock_update.message.contact = MagicMock(phone_number='+123', first_name='Alice')
    handle_contact(mock_update, mock_context)
    mock_storage.save_contact.assert_called()
    mock_logger.log.assert_called()

@patch('src.bot.logger')
@patch('src.bot.storage')
def test_handle_faq(mock_storage, mock_logger, mock_update, mock_context):
    from src.bot import handle_faq
    mock_storage.get_faq.return_value = [{'question': 'Q', 'answer': 'A'}]
    handle_faq(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()
    mock_logger.log.assert_called()

@patch('src.bot.logger')
@patch('src.bot.service_catalog')
def test_handle_services(mock_service_catalog, mock_logger, mock_update, mock_context):
    from src.bot import handle_services
    mock_service_catalog.get_services.return_value = [{'name': 'S', 'description': 'D'}]
    handle_services(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()
    mock_logger.log.assert_called()

# Edge case: неизвестная команда
@patch('src.bot.logger')
def test_unknown_command(mock_logger, mock_update, mock_context):
    from src.bot import handle_unknown
    handle_unknown(mock_update, mock_context)
    mock_update.message.reply_text.assert_called()
    mock_logger.log.assert_called() 