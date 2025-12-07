import asyncio
from pathlib import Path
from typing import Dict, List, Any
from deep_translator import GoogleTranslator

import aiohttp

PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"

async def _translate_to_english(text: str) -> str:

    def translate_sync():
        try:
            return GoogleTranslator(source='auto', target='en').translate(text)
        except Exception as e:
            print(f"ошибка перевода '{text}': {e}")
            return text

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, translate_sync)
    return result


class PexelsAPIError(Exception):
    pass


async def _search_best_video_url(
    session: aiohttp.ClientSession,
    query: str,
) -> str | None:

    trns_query = await _translate_to_english(query)

    params = {
        "query": trns_query, 
        "per_page": 1,   
        "orientation": "landscape",
        "size": "medium",    
    }


    async with session.get(PEXELS_VIDEO_SEARCH_URL, params=params) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise PexelsAPIError(
                f"Pexels API вернул статус {resp.status}: {text}"
            )

        data: Dict[str, Any] = await resp.json()

    videos = data.get("videos") or []
    if not videos:
        print(f"по запросу '{query}' видео не найдено")
        return None

    video_data = videos[0]
    video_files = video_data.get("video_files") or []

    if not video_files:
        print(f"у найденного видео по запросу '{query}' нет поля 'video_files'")
        return None

    video_files_sorted = sorted(
        video_files,
        key=lambda f: f.get("width", 0),
        reverse=True,
    )

    best_file = video_files_sorted[0]
    return best_file.get("link")


async def _download_video(
    session: aiohttp.ClientSession,
    url: str,
    output_path: str,
) -> None:

    async with session.get(url) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(
                f"ошибка скачивания '{url}': статус {resp.status}, тело: {text}"
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)


async def _process_single_insert(
    session: aiohttp.ClientSession,
    base_file_path: str,
    description: str,
) -> str:

    path = Path(base_file_path)

    output_path = str(path.with_stem(path.stem + "_vstavka"))

    video_url = await _search_best_video_url(session, description)
    if not video_url:
        raise RuntimeError(
            f"не удалось найти видео по описанию '{description}' для файла '{base_file_path}'"
        )

    await _download_video(session, video_url, output_path)

    print(f"вставка для '{base_file_path}' сохранена в '{output_path}'")
    return output_path


async def process_inserts(
    inserts: Dict[str, str],
    pexels_api_key: str,
) -> List[str]:

    headers = {
        "Authorization": pexels_api_key
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []

        for base_file_path, description in inserts.items():
            task = _process_single_insert(
                session=session,
                base_file_path=base_file_path,
                description=description,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

    output_files: List[str] = []

    for result in results:
        if isinstance(result, Exception):
            print("ошибка при обработке вставки:", result)
        else:
            output_files.append(result)

    return output_files


# Пример использования модуля
# if __name__ == "__main__":
#     async def main():
#         # TODO: сюда вставь свой реальный ключ Pexels
#         API_KEY = "ТВОЙ_PEXELS_API_KEY_СЮДА"

#         # Пример словаря вставок:
#         # ключ — базовое имя файла (мы от него сделаем *_vstavka.mp4),
#         # значение — текстовое описание вставки.
#         inserts = {
#             "clips/segment_01.mp4": "человек считает деньги",
#             "clips/segment_02.mp4": "машины едут по ночному городу",
#         }

#         ready_files = await process_inserts(inserts, API_KEY)
#         print("Готовые вставки:", ready_files)

#     asyncio.run(main())