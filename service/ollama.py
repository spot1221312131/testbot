import asyncio
import httpx
import os

OLLAMA_BASE = 'http://localhost:11434'


async def ask_ollama(prompt: str, model: str = 'llama3'):

    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 512,
        "stream": False 
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        print(data)

            
        return data


async def assembly_request(user_prompt: str):
    system_instruction = f"""Ты помощник по видеомонтажу.
    Доступные инструменты:
    1. cut_video - обрезать видео по времени.
    Параметры:
    start_sec (float, секунда начала)
    end_sec (float, секунда конца)

    Формат ответа - ТОЛЬКО JSON, без пояснений, в виде одной строки:

    Пример 1: "обрежь до 20 секунды" → {{"tool": "cut_video", "args": {{"start_sec": 0, "end_sec": 20}}}}
    Пример 2: "обрежь с 10 до 30 секунд" → {{"tool": "cut_video", "args": {{"start_sec": 10, "end_sec": 30}}}}

    Теперь обработай запрос пользователя: { user_prompt}"""

    model_name = "llama3"

    answer = await ask_ollama(system_instruction, model=model_name)

    return answer