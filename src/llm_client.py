import os
import aiohttp
from typing import List, Dict, Optional
from src.llm_models import llm_models
from aiohttp import ClientTimeout

class LLMClient:
    def __init__(self):
        self.models = llm_models

    async def generate(self, messages: List[Dict], model_name: Optional[str] = None, user_id: Optional[int] = None, **params) -> str:
        model = self.models.get_model_by_name(model_name) if model_name else self.models.get_default_model()
        if not model:
            raise ValueError("LLM model not found")
        endpoint = model["endpoint"]
        api_key = model.get("api_key")
        service = model.get("service", "openai")
        headers = {"Content-Type": "application/json"}
        if api_key:
            if service == "anthropic":
                headers["x-api-key"] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"
        elif service in ("openai", "fireworks", "anthropic"):
            # Для облачных сервисов ключ обязателен
            error_msg = f"Для модели '{model.get('name')}' требуется API-ключ. Проверьте настройки."
            from src.logger import logger
            logger.log('ERROR', error_msg, user_id, event_type='llm_error')
            return error_msg
        payload = {}
        if service == "anthropic":
            # Anthropic Claude (messages endpoint)
            payload = {
                "model": model["provider_model_name"],
                "messages": messages,
                "max_tokens": params.get("max_tokens", 1024),
                "stream": False
            }
        else:
            # OpenAI, LM Studio, Ollama, Fireworks, Together, etc.
            payload = {
                "model": model["provider_model_name"],
                "messages": messages,
                "max_tokens": params.get("max_tokens", 1024),
                "stream": False
            }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=payload, headers=headers, timeout=ClientTimeout(total=60)) as resp:
                    if resp.status >= 400:
                        err_text = await resp.text()
                        from src.logger import logger
                        logger.log('ERROR', f'LLM API error {resp.status}: {err_text}', user_id, event_type='llm_error')
                        if resp.status == 401:
                            return 'Ошибка авторизации LLM API: проверьте ключ.'
                        elif resp.status == 403:
                            return 'Доступ к LLM API запрещён. Проверьте права доступа.'
                        elif resp.status == 404:
                            return 'LLM API не найден. Проверьте endpoint и имя модели.'
                        elif resp.status >= 500:
                            return 'Внутренняя ошибка LLM API. Попробуйте позже.'
                        else:
                            return f'Ошибка LLM API ({resp.status}): {err_text}'
                    data = await resp.json()
            except Exception as e:
                from src.logger import logger
                logger.log('ERROR', f'LLM API connection error: {e}', user_id, event_type='llm_error')
                return f'Ошибка соединения с LLM API: {e}'
            # Anthropic: content in data["content"] or data["choices"][0]["message"]["content"]
            if service == "anthropic":
                if "content" in data and isinstance(data["content"], list):
                    return "".join([c.get("text", "") for c in data["content"] if c.get("type") == "text"])
                if "completion" in data:
                    return data["completion"]
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            return f"Unexpected LLM response: {data}"

llm_client = LLMClient() 