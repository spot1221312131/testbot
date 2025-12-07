import asyncio
import os
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class VideoStyleAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_name = "gemini-3-pro-latest"

    async def analyze_video_style(self, video_path: str) -> str:
        print(f"загрузка видео примера для анализа: {video_path}")
        
        video_file = genai.upload_file(path=video_path)
        print(f"ждём обработки (URI: {video_file.uri})...")
        
        while video_file.state.name == "PROCESSING":
            await asyncio.sleep(5)
            video_file = genai.get_file(video_file.name)
            print(".", end="", flush=True)
        
        if video_file.state.name == "FAILED":
            raise RuntimeError("ошибка обработки видео.")
        
        prompt = """
        Ты эксперт по монтажу видео: режиссёр, колорист и дизайнер. Сделай полный реверс-инжиниринг стиля монтажа этого видео. 
        Опиши каждую мелочь, чтобы монтажёр мог воспроизвести стиль 1:1. Избегай обобщений – только конкретные параметры, измерения, цвета (в HEX или именах), шрифты, тайминги.
        
        Структурируй отчёт по разделам на русском языке:

        1. **Общая структура видео:**
           - Длина видео, количество сцен/кадров.
           - Общий стиль (например, динамичный TikTok-style, кинематографический, минималистичный).
           - Темп: средняя длительность кадра (в секундах, с примерами: 0.5с для быстрых, 5с для длинных).
           - Синхронизация: как кадры/эффекты синхронизированы с аудио (битами музыки, речью).

        2. **Цветокоррекция и тона:**
           - Цветовая палитра: доминирующие цвета (HEX: #RRGGBB), насыщенность (высокая/низкая), контраст.
           - Грейдинг: теплые/холодные тона, LUT (например, cinematic teal-orange), фильтры (VHS-grain, bloom).
           - Изменения по видео: градиенты, фейды в чёрный/белый, коррекция в конкретных сценах.

        3. **Субтитры и типографика:**
           - Шрифты: точные названия (Arial, Impact, handwritten), размер (в pt или relative), стиль (bold, italic).
           - Цвета: текст (#FFFFFF), обводка (#000000), тени (offset в px).
           - Позиция: центр, низ, верх; отступы от краёв.
           - Анимация: тип (fade-in 0.2с, typewriter по буквам, bounce), длительность, easing (linear/ease-in-out).
           - Выделения: ключевые слова жирным/цветом, эмодзи/иконки.

        4. **Эффекты и переходы:**
           - Визуальные эффекты: glitch (интенсивность), zoom (in/out, speed), particle effects, overlays (textures, light leaks).
           - Переходы: тип (cut, dissolve 0.5с, swipe left), частота, синхрон с аудио.
           - Фоны: цвета (# hex), градиенты, изображения; как меняются.

        5. **Аудио и звуковой дизайн:**
           - Музыка: жанр (lo-fi, epic orchestral), BPM, объём (громкость пиков).
           - SFX: эффекты на переходах (whoosh, click), синхронизация с визуалом.
           - Голос: тон (энергичный/спокойный), эффекты (echo, reverb).

        6. **Мелочи и паттерны:**
           - Любые повторяющиеся элементы: логотипы, водяные знаки, aspect ratio (16:9, 9:16).
           - Качество: разрешение, FPS видео, артефакты.
           - Рекомендации по recreation: инструменты (Premiere, After Effects), плагины.

        Будь исчерпывающе детальным – опиши по таймкодам (например, 00:15-00:30: эффект X).
        """
        
        model = genai.GenerativeModel(model_name=self.model_name)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(
                [video_file, prompt],
                request_options={"timeout": 600}
            )
        )
        
        try:
            genai.delete_file(video_file.name)
        except:
            pass
        
        return response.text

# Пример использования
# if __name__ == "__main__":
#     async def main():
#         GEMINI_KEY = "ТВОЙ_API_KEY"
#         analyzer = VideoStyleAnalyzer(GEMINI_KEY)
#         video_path = "example_video.mp4"
#         if not os.path.exists(video_path):
#             print("Файл не найден.")
#             return
#         try:
#             report = await analyzer.analyze_video_style(video_path)
#             print("\n" + "="*40)
#             print("ДЕТАЛЬНЫЙ ОТЧЁТ ПО МОНТАЖУ:")
#             print("="*40)
#             print(report)
#         except Exception as e:
#             print(f"Ошибка: {e}")
    
#     asyncio.run(main())