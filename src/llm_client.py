import os
import asyncio
import aiohttp
from typing import List, Dict, Optional
from src.llm_models import llm_models
from aiohttp import ClientTimeout, ClientConnectorCertificateError

class LLMClient:
    def __init__(self):
        self.models = llm_models

    async def generate(self, messages: List[Dict], model_name: Optional[str] = None, user_id: Optional[int] = None, **params) -> str:
        model = self.models.get_model_by_name(model_name) if model_name else self.models.get_default_model()
        if not model:
            raise ValueError("LLM model not found")
        model_display = model.get("name", model.get("provider_model_name", "unknown_model"))
        from src.logger import logger
        logger.log('INFO', f'Calling LLM model: {model_display}', user_id, event_type='llm_call')

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
        # bool env var to skip SSL verification (useful for dev when cert issues). 1/true/yes enable skip.
        insecure_ssl = os.environ.get("LLM_INSECURE_SSL", "false").lower() in ("1", "true", "yes")

        max_attempts = int(os.environ.get("LLM_RETRY_ATTEMPTS", "3"))
        backoff = 1  # seconds

        data = None  # type: ignore

        async with aiohttp.ClientSession() as session:
            attempt = 1
            while attempt <= max_attempts:
                try:
                    async with session.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=ClientTimeout(total=60),
                        ssl=False if insecure_ssl else True,
                    ) as resp:
                        if resp.status >= 500 or resp.status in (502, 503, 504):
                            # Серверная ошибка ‒ можно попробовать ещё раз
                            err_text = await resp.text()
                            logger.log('WARNING', f'[{model_display}] LLM API {resp.status}, attempt {attempt}/{max_attempts}: {err_text}', user_id, event_type='llm_retry')
                            if attempt < max_attempts:
                                await asyncio.sleep(backoff)
                                backoff *= 2
                                attempt += 1
                                continue
                            if resp.status == 503:
                                return 'Сервис перегружен, повторите через минуту.'
                            return f'Ошибка LLM API ({resp.status}): {err_text}'
                        if resp.status >= 400:
                            # Прочие клиентские ошибки не повторяем
                            err_text = await resp.text()
                            logger.log('ERROR', f'[{model_display}] LLM API error {resp.status}: {err_text}', user_id, event_type='llm_error')
                            if resp.status == 401:
                                logger.log('ERROR', f'Ошибка авторизации LLM API: {err_text}', user_id, event_type='llm_error')
                                return 'Ошибка авторизации LLM API: проверьте ключ.'
                            elif resp.status == 403:
                                logger.log('ERROR', f'Доступ к LLM API запрещён (403): {err_text}', user_id, event_type='llm_error')
                                return 'Доступ к LLM API запрещён. Проверьте права доступа.'
                            elif resp.status == 404:
                                logger.log('ERROR', f'LLM API не найден (404): {err_text}', user_id, event_type='llm_error')
                                return 'LLM API не найден. Проверьте endpoint и имя модели.'
                            else:
                                logger.log('ERROR', f'LLM API error {resp.status}: {err_text}', user_id, event_type='llm_error')
                                if resp.status == 503:
                                    return 'Сервис перегружен, повторите через минуту.'
                                return f'Ошибка LLM API ({resp.status}): {err_text}'

                        # успех
                        data = await resp.json()
                        break
                except ClientConnectorCertificateError as cert_err:
                    # Автоматический повтор без проверки SSL, если проблема в сертификате
                    logger.log('WARNING', f'[{model_display}] SSL verify failed, retrying without verification: {cert_err}', user_id, event_type='llm_ssl_retry')
                    try:
                        async with session.post(
                            endpoint,
                            json=payload,
                            headers=headers,
                            timeout=ClientTimeout(total=60),
                            ssl=False,
                        ) as resp:
                            if resp.status >= 400:
                                err_text = await resp.text()
                                logger.log('ERROR', f'[{model_display}] LLM API error {resp.status}: {err_text}', user_id, event_type='llm_error')
                                if resp.status == 503:
                                    return 'Сервис перегружен, повторите через минуту.'
                                return f'Ошибка LLM API ({resp.status}): {err_text}'
                            data = await resp.json()
                    except Exception as e2:
                        logger.log('ERROR', f'LLM retry error: {e2}', user_id, event_type='llm_ssl_error')
                        return f'Ошибка SSL при соединении с LLM API: {e2}'
                except Exception as e:
                    logger.log('ERROR', f'LLM API connection error: {e}', user_id, event_type='llm_error')
                    return f'Ошибка соединения с LLM API: {e}'

        # --- Обработка полученных данных после выхода из сессии ---
        if data is None:
            return "Не удалось получить ответ от LLM (попытки исчерпаны)."

        # Anthropic: content in data["content"] or data["completion"]
        if service == "anthropic":
            if "content" in data and isinstance(data["content"], list):
                return "".join([c.get("text", "") for c in data["content"] if c.get("type") == "text"])
            if "completion" in data:
                return data["completion"]
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        return f"Unexpected LLM response: {data}"

llm_client = LLMClient() 