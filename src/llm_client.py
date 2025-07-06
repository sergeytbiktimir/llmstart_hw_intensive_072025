import os
import aiohttp
from typing import List, Dict, Optional
from src.llm_models import llm_models

class LLMClient:
    def __init__(self):
        self.models = llm_models

    async def generate(self, messages: List[Dict], model_name: Optional[str] = None, user_id: Optional[int] = None, **params) -> str:
        model = self.models.get_model_by_name(model_name) if model_name else self.models.get_default_model()
        if not model:
            raise ValueError("LLM model not found")
        endpoint = model["endpoint"]
        api_key_env = model.get("api_key_env")
        api_key = os.environ.get(api_key_env) if api_key_env else None
        service = model.get("service", "openai")
        headers = {"Content-Type": "application/json"}
        if api_key:
            if service == "anthropic":
                headers["x-api-key"] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"
        payload = {}
        if service == "anthropic":
            # Anthropic Claude (messages endpoint)
            payload = {
                "model": model["name"],
                "messages": messages,
                "max_tokens": params.get("max_tokens", 1024),
                "stream": False
            }
        else:
            # OpenAI, LM Studio, Ollama, Fireworks, Together, etc.
            payload = {
                "model": model["name"],
                "messages": messages,
                "max_tokens": params.get("max_tokens", 1024),
                "stream": False
            }
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # Anthropic: content in data["content"] or data["choices"][0]["message"]["content"]
                if service == "anthropic":
                    # Claude 3 returns content in data["content"] (list of dicts with type/text)
                    if "content" in data and isinstance(data["content"], list):
                        return "".join([c.get("text", "") for c in data["content"] if c.get("type") == "text"])
                    # Claude 2/old: data["completion"]
                    if "completion" in data:
                        return data["completion"]
                # OpenAI/compatible: data["choices"][0]["message"]["content"]
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                raise RuntimeError(f"Unexpected LLM response: {data}")

llm_client = LLMClient() 