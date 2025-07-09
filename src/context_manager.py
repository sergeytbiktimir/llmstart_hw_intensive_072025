"""
Менеджер контекста для краткосрочной и долгосрочной памяти LLM Telegram-ассистента.
Формирует контекст из истории сообщений пользователя/ассистента.
Оформление по code_conventions.md.
"""
import os
from typing import List, Dict, Optional
from src.storage import storage
from src.logger import logger
import re

# Настройки контекста через переменные окружения
MAX_CONTEXT_MESSAGES = int(os.environ.get("MAX_CONTEXT_MESSAGES", "10"))
MAX_CONTEXT_LENGTH = int(os.environ.get("MAX_CONTEXT_LENGTH", "4000"))
# Настройки долгосрочной памяти
LONG_TERM_MEMORY_ENABLED = os.environ.get("LONG_TERM_MEMORY_ENABLED", "true").lower() == "true"
MAX_LONG_TERM_RESULTS = int(os.environ.get("MAX_LONG_TERM_RESULTS", "3"))
LONG_TERM_MEMORY_LENGTH = int(os.environ.get("LONG_TERM_MEMORY_LENGTH", "2000"))

class ContextManager:
    """Менеджер контекста для формирования краткосрочной и долгосрочной памяти."""
    
    def __init__(self):
        self.max_messages = MAX_CONTEXT_MESSAGES
        self.max_length = MAX_CONTEXT_LENGTH
        self.long_term_enabled = LONG_TERM_MEMORY_ENABLED
        self.max_long_term_results = MAX_LONG_TERM_RESULTS
        self.long_term_memory_length = LONG_TERM_MEMORY_LENGTH
    
    def get_user_context(self, user_id: int) -> List[Dict[str, str]]:
        """
        Получает контекст пользователя из истории сообщений.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список сообщений в формате [{"role": "user|assistant", "content": "текст"}]
        """
        try:
            # Получаем только последние self.max_messages сообщений пользователя
            history = storage.get_recent_history(user_id, self.max_messages)
            
            # Фильтруем только сообщения пользователя и ассистента
            conversation_messages = []
            for entry in history:
                if entry["action"] in ["user_message", "assistant_reply"]:
                    role = "user" if entry["action"] == "user_message" else "assistant"
                    content = entry["details"]
                    if content and content.strip():
                        conversation_messages.append({
                            "role": role,
                            "content": content.strip()
                        })
            
            # Берем последние MAX_CONTEXT_MESSAGES сообщений (уже ограничено выборкой)
            recent_messages = conversation_messages
            
            # Проверяем общую длину контекста
            total_length = sum(len(msg["content"]) for msg in recent_messages)
            if total_length > self.max_length:
                # Если контекст слишком длинный, берем только последние сообщения
                # до достижения лимита
                trimmed_messages = []
                current_length = 0
                for msg in reversed(recent_messages):
                    if current_length + len(msg["content"]) <= self.max_length:
                        trimmed_messages.insert(0, msg)
                        current_length += len(msg["content"])
                    else:
                        break
                recent_messages = trimmed_messages
            
            logger.log('DEBUG', f'Context for user {user_id}: {len(recent_messages)} messages, {sum(len(msg["content"]) for msg in recent_messages)} chars', 
                      user_id, event_type='context_formed')
            
            return recent_messages
            
        except Exception as e:
            logger.log('ERROR', f'Error getting user context: {e}', user_id, event_type='context_error')
            return []
    
    def search_long_term_memory(self, user_id: int, query: str) -> List[Dict[str, str]]:
        """
        Поиск релевантных сообщений в долгосрочной памяти.
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            
        Returns:
            Список релевантных сообщений
        """
        if not self.long_term_enabled or not query:
            return []
        
        try:
            # Получаем полную историю сообщений пользователя
            history = storage.get_history(user_id)
            
            # Фильтруем только сообщения пользователя и ассистента
            conversation_pairs = []
            current_pair = {"user": "", "assistant": "", "timestamp": None}
            
            for entry in history:
                if entry["action"] == "user_message":
                    # Если начинается новое сообщение пользователя, сохраняем предыдущую пару
                    if current_pair["user"] and current_pair["assistant"]:
                        conversation_pairs.append(current_pair.copy())
                    
                    # Начинаем новую пару
                    current_pair = {
                        "user": entry["details"],
                        "assistant": "",
                        "timestamp": entry.get("created_at")  # фиксация времени сообщения
                    }
                elif entry["action"] == "assistant_reply" and current_pair["user"]:
                    # Добавляем ответ ассистента к текущей паре
                    current_pair["assistant"] = entry["details"]
            
            # Добавляем последнюю пару, если она есть
            if current_pair["user"] and current_pair["assistant"]:
                conversation_pairs.append(current_pair)
            
            # Поиск по ключевым словам
            # Разбиваем запрос на ключевые слова
            keywords = re.findall(r'\w+', query.lower())
            
            # Оцениваем релевантность каждой пары сообщений
            scored_pairs = []
            for pair in conversation_pairs:
                score = 0
                for keyword in keywords:
                    if keyword in pair["user"].lower():
                        score += 2  # Больший вес для совпадений в запросе пользователя
                    if keyword in pair["assistant"].lower():
                        score += 1
                
                if score > 0:
                    scored_pairs.append((score, pair))
            
            # Сортируем по релевантности (по убыванию)
            scored_pairs.sort(reverse=True, key=lambda x: x[0])
            
            # Берем только top-N результатов
            top_pairs = scored_pairs[:self.max_long_term_results]
            
            # Форматируем результаты для LLM
            memory_messages = []
            total_length = 0
            
            for _, pair in top_pairs:
                memory_text = f"User: {pair['user']}\nAssistant: {pair['assistant']}"
                
                # Проверяем, не превысим ли лимит длины
                if total_length + len(memory_text) <= self.long_term_memory_length:
                    memory_messages.append({
                        "role": "system",
                        "content": f"Relevant past conversation from {pair['timestamp']}:\n{memory_text}"
                    })
                    total_length += len(memory_text)
                else:
                    break
            
            logger.log('DEBUG', f'Long-term memory search for user {user_id}: found {len(memory_messages)} relevant conversations', 
                      user_id, event_type='long_term_memory_search')
            
            return memory_messages
            
        except Exception as e:
            logger.log('ERROR', f'Error searching long-term memory: {e}', user_id, event_type='long_term_memory_error')
            return []
    
    def build_messages_with_context(self, user_id: int, current_message: str) -> List[Dict[str, str]]:
        """
        Строит полный список сообщений для LLM с контекстом.
        
        Args:
            user_id: ID пользователя
            current_message: Текущее сообщение пользователя
            
        Returns:
            Список сообщений для отправки в LLM
        """
        # Получаем контекст из истории
        context_messages = self.get_user_context(user_id)
        
        # Получаем релевантные сообщения из долгосрочной памяти
        long_term_messages = []
        if self.long_term_enabled:
            long_term_messages = self.search_long_term_memory(user_id, current_message)
            if long_term_messages:
                logger.log('INFO', f'Added {len(long_term_messages)} relevant conversations from long-term memory', 
                          user_id, event_type='long_term_memory_used')
        
        # Добавляем system-промт в начало истории
        system_prompt = {
            "role": "system",
            "content": (
                "Ты — умный и внимательный собеседник, ведущий живой диалог с пользователем в формате чата. "
                "Ниже приведена история вашей переписки: это последовательность сообщений, где роль 'user' — это пользователь, а 'assistant' — ты, ассистент. "
                "Ты обладаешь памятью: можешь ссылаться на предыдущие сообщения, вспоминать детали прошлых обсуждений, поддерживать контекст и нить разговора. "
                "Если пользователь спрашивает о своих или твоих прошлых репликах, ищи их в истории ниже и используй для ответа. "
                "Старайся быть последовательным, не повторяйся, не теряй тему, реагируй на намёки и уточнения пользователя. "
                "Веди себя естественно, дружелюбно и профессионально, как человек, который действительно помнит, о чём шла речь ранее. "
                "Если в истории есть незавершённые вопросы или темы — можешь предложить к ним вернуться. "
                "Всегда отвечай на русском языке, если не указано иное."
            )
        }
        # Формируем итоговый список сообщений
        messages = [system_prompt] + long_term_messages + context_messages + [{"role": "user", "content": current_message}]
        
        logger.log('DEBUG', f'Built messages for LLM: {len(messages)} total messages', 
                  user_id, event_type='llm_messages_built')
        return messages

# Глобальный экземпляр менеджера контекста
context_manager = ContextManager() 