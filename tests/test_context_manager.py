"""
Тесты для context_manager.py
Покрытие: формирование контекста, ограничения по количеству и длине сообщений.
"""
import unittest
from unittest.mock import Mock, patch
import os
import sys

# Добавляем src в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.context_manager import ContextManager, context_manager


class TestContextManager(unittest.TestCase):
    """Тесты для ContextManager."""
    
    def setUp(self):
        """Подготовка к тестам."""
        self.context_manager = ContextManager()
        self.mock_storage = Mock()
        
    def test_get_user_context_empty_history(self):
        """Тест получения контекста при пустой истории."""
        with patch('src.context_manager.storage') as mock_storage:
            mock_storage.get_history.return_value = []
            
            result = self.context_manager.get_user_context(123)
            
            self.assertEqual(result, [])
            mock_storage.get_history.assert_called_once_with(123)
    
    def test_get_user_context_with_messages(self):
        """Тест получения контекста с сообщениями."""
        mock_history = [
            {"user_id": 123, "action": "user_message", "details": "Привет!", "created_at": "2024-01-01T10:00:00"},
            {"user_id": 123, "action": "assistant_reply", "details": "Здравствуйте!", "created_at": "2024-01-01T10:00:01"},
            {"user_id": 123, "action": "user_message", "details": "Как дела?", "created_at": "2024-01-01T10:00:02"},
        ]
        
        with patch('src.context_manager.storage') as mock_storage:
            mock_storage.get_history.return_value = mock_history
            
            result = self.context_manager.get_user_context(123)
            
            expected = [
                {"role": "user", "content": "Привет!"},
                {"role": "assistant", "content": "Здравствуйте!"},
                {"role": "user", "content": "Как дела?"},
            ]
            self.assertEqual(result, expected)
    
    def test_get_user_context_filters_other_actions(self):
        """Тест фильтрации действий, не относящихся к диалогу."""
        mock_history = [
            {"user_id": 123, "action": "user_message", "details": "Привет!", "created_at": "2024-01-01T10:00:00"},
            {"user_id": 123, "action": "contact_submitted", "details": "name=John", "created_at": "2024-01-01T10:00:01"},
            {"user_id": 123, "action": "assistant_reply", "details": "Здравствуйте!", "created_at": "2024-01-01T10:00:02"},
        ]
        
        with patch('src.context_manager.storage') as mock_storage:
            mock_storage.get_history.return_value = mock_history
            
            result = self.context_manager.get_user_context(123)
            
            expected = [
                {"role": "user", "content": "Привет!"},
                {"role": "assistant", "content": "Здравствуйте!"},
            ]
            self.assertEqual(result, expected)
    
    def test_get_user_context_max_messages_limit(self):
        """Тест ограничения по количеству сообщений."""
        # Создаем больше сообщений, чем MAX_CONTEXT_MESSAGES
        mock_history = []
        for i in range(15):  # Больше чем MAX_CONTEXT_MESSAGES (10)
            mock_history.append({
                "user_id": 123, 
                "action": "user_message" if i % 2 == 0 else "assistant_reply", 
                "details": f"Message {i}", 
                "created_at": f"2024-01-01T10:00:{i:02d}"
            })
        
        with patch('src.context_manager.storage') as mock_storage:
            mock_storage.get_history.return_value = mock_history
            
            result = self.context_manager.get_user_context(123)
            
            # Должно быть только последние 10 сообщений
            self.assertEqual(len(result), 10)
            self.assertEqual(result[0]["content"], "Message 5")  # Первое из последних 10
    
    def test_get_user_context_max_length_limit(self):
        """Тест ограничения по длине контекста."""
        # Создаем сообщения с большой длиной
        long_message = "A" * 1000  # 1000 символов
        mock_history = []
        for i in range(10):
            mock_history.append({
                "user_id": 123, 
                "action": "user_message" if i % 2 == 0 else "assistant_reply", 
                "details": long_message, 
                "created_at": f"2024-01-01T10:00:{i:02d}"
            })
        
        with patch('src.context_manager.storage') as mock_storage:
            mock_storage.get_history.return_value = mock_history
            
            result = self.context_manager.get_user_context(123)
            
            # Должно быть ограничено по длине (4000 символов)
            total_length = sum(len(msg["content"]) for msg in result)
            self.assertLessEqual(total_length, 4000)
    
    def test_build_messages_with_context(self):
        """Тест построения сообщений с контекстом."""
        mock_context = [
            {"role": "user", "content": "Привет!"},
            {"role": "assistant", "content": "Здравствуйте!"},
        ]
        
        with patch.object(self.context_manager, 'get_user_context', return_value=mock_context):
            result = self.context_manager.build_messages_with_context(123, "Как дела?")
            
            expected = [
                {"role": "user", "content": "Привет!"},
                {"role": "assistant", "content": "Здравствуйте!"},
                {"role": "user", "content": "Как дела?"},
            ]
            self.assertEqual(result, expected)
    
    def test_build_messages_with_context_empty_history(self):
        """Тест построения сообщений с пустой историей."""
        with patch.object(self.context_manager, 'get_user_context', return_value=[]):
            result = self.context_manager.build_messages_with_context(123, "Привет!")
            
            expected = [{"role": "user", "content": "Привет!"}]
            self.assertEqual(result, expected)
    
    def test_context_manager_singleton(self):
        """Тест, что context_manager является синглтоном."""
        self.assertIsInstance(context_manager, ContextManager)
        self.assertIs(context_manager, context_manager)  # Тот же объект


if __name__ == '__main__':
    unittest.main() 