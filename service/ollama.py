import asyncio
import httpx
import os
from service.prompts import get_system_prompt

OLLAMA_BASE = 'http://localhost:11434'


async def ask_ollama(prompt: str, model: str = 'llama3'):
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 1024,
        "stream": False 
    }

    try:
        async with httpx.AsyncClient(timeout=220.0) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            print(data)
            return data
    except httpx.ConnectError:
        raise ConnectionError(f"Не удалось подключиться к Ollama по адресу {OLLAMA_BASE}. Убедитесь, что Ollama запущен.")
    except httpx.ReadTimeout:
        raise TimeoutError("Превышено время ожидания ответа от Ollama (220 секунд). Попробуйте упростить запрос или использовать более быструю модель.")
    except httpx.TimeoutException:
        raise TimeoutError("Превышено время ожидания ответа от Ollama.")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Ошибка HTTP от Ollama: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"Неожиданная ошибка при обращении к Ollama: {str(e)}")


async def assembly_request(user_prompt: str):
    system_instruction = get_system_prompt(user_prompt)

    model_name = "llama3"

    try:
        answer = await ask_ollama(system_instruction, model=model_name)
        response_text = answer.get('response', '')
        if not response_text:
            raise ValueError("Ollama вернул пустой ответ")
        return {"response": response_text}
    except (ConnectionError, TimeoutError) as e:
        raise e
    except Exception as e:
        raise Exception(f"Ошибка при обработке запроса через Ollama: {str(e)}")