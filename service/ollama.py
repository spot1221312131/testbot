import asyncio
import httpx
import os

OLLAMA_BASE = 'http://localhost:11434'


async def ask_ollama(prompt: str, model: str = 'llama3'):
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 1024,
        "stream": False 
    }

    try:
        # Увеличиваем таймаут до 220 секунд для больших моделей
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
    system_instruction = f"""Ты API, который возвращает ТОЛЬКО JSON. Никаких приветствий, объяснений, текста.
Запрос: {user_prompt}

Ты должен вернуть JSON с планом монтажа видео.

Доступные эффекты: zoom_in, zoom_out, black_white, slow_motion, fast_motion, transition.

Формат JSON:
{{"parts": [{{"start_sec": число, "end_sec": число, "action": "keep" или "edit", "effect_name": "название" или null}}]}}

Правила:
1. Все времена в секундах
2. Если в запросе есть "эффект", "сделай", "добавь" - action = "edit"
3. Если просто время без эффекта - action = "keep"
4. Для action = "edit" укажи effect_name из списка

Примеры:
- "раздели на 3 части по 10 секунд, на вторую часть добавь эффект увеличения" → {{"parts": [{{"start_sec": 0, "end_sec": 10, "action": "keep", "effect_name": null}}, {{"start_sec": 10, "end_sec": 20, "action": "edit", "effect_name": "zoom_in"}}, {{"start_sec": 20, "end_sec": 30, "action": "keep", "effect_name": null}}]}}

- "сделай чёрно-белый эффект с 5 до 15 секунд" → {{"parts": [{{"start_sec": 0, "end_sec": 5, "action": "keep", "effect_name": null}}, {{"start_sec": 5, "end_sec": 15, "action": "edit", "effect_name": "black_white"}}, {{"start_sec": 15, "end_sec": 30, "action": "keep", "effect_name": null}}]}}

ТВОЙ ОТВЕТ (ТОЛЬКО JSON, БЕЗ ЛИШНЕГО ТЕКСТА):"""

    model_name = "llama3"

    try:
        answer = await ask_ollama(system_instruction, model=model_name)
        # Извлекаем текст ответа из структуры Ollama
        response_text = answer.get('response', '')
        if not response_text:
            raise ValueError("Ollama вернул пустой ответ")
        return {"response": response_text}
    except (ConnectionError, TimeoutError) as e:
        raise e
    except Exception as e:
        raise Exception(f"Ошибка при обработке запроса через Ollama: {str(e)}")