# Импортируем необходимые модули
import asyncio  # Для асинхронного программирования
import os  # Для работы с файловой системой
import shutil  # Для копирования файлов


# Функция 1: Делит видео на N частей
async def cut_video_into_parts(video_path: str, parts_info: list):
    """
    Режет видео на несколько частей по указанным временным отрезкам
    
    Args:
        video_path (str): Путь к исходному видеофайлу
        parts_info (list): Список словарей с информацией о частях
            Пример: [{"start_sec": 0, "end_sec": 10, "action": "keep", "effect_name": null}, ...]
    
    Returns:
        list: Список путей к созданным файлам частей или список с ошибкой
    """
    try:
        # Получаем директорию, в которой лежит исходное видео
        video_dir = os.path.dirname(video_path)
        # Получаем имя файла с расширением (например, "video_123.mp4")
        video_name = os.path.basename(video_path)
        # Убираем расширение .mp4, оставляем только имя (например, "video_123")
        name_without_ext = os.path.splitext(video_name)[0]
        
        # Создаём пустой список для хранения путей к созданным частям
        output_files = []
        
        # Проходим по всем частям из плана AI (enumerate начиная с 1 для удобства)
        for i, part in enumerate(parts_info, 1):
            # Извлекаем время начала части из словаря
            start_sec = float(part['start_sec'])
            # Извлекаем время конца части из словаря
            end_sec = float(part['end_sec'])
            # Вычисляем длительность части (конец - начало)
            duration = end_sec - start_sec
            
            # Формируем имя для выходного файла части
            # Например: "video_123_part_1.mp4"
            output_part = os.path.join(video_dir, f"{name_without_ext}_part_{i}.mp4")
            
            # Формируем команду для FFmpeg:
            # ffmpeg -i исходное_видео.mp4 -ss начало -t длительность -кодеки выходной_файл.mp4
            cmd = [
                'ffmpeg',  # Основная команда FFmpeg
                '-i', video_path,  # Указываем входной файл (input)
                '-ss', str(start_sec),  # Начинаем с этой секунды (seek start)
                '-t', str(duration),  # Вырезаем такую длительность (time)
                '-c:v', 'libx264',  # Используем кодек h.264 для видео
                '-c:a', 'aac',  # Используем кодек AAC для аудио
                '-y',  # Автоматически подтверждаем перезапись файлов (yes)
                output_part  # Выходной файл
            ]
            
            # Запускаем FFmpeg асинхронно как подпроцесс
            process = await asyncio.create_subprocess_exec(
                *cmd,  # Разворачиваем список аргументов команды
                stdout=asyncio.subprocess.PIPE,  # Перехватываем стандартный вывод
                stderr=asyncio.subprocess.PIPE  # Перехватываем вывод ошибок
            )
            
            # Ждём завершения процесса и получаем вывод
            stdout, stderr = await process.communicate()
            
            # Проверяем код возврата: 0 = успех, не 0 = ошибка
            if process.returncode != 0:
                # Если ошибка, удаляем уже созданные файлы
                for f in output_files:
                    if os.path.exists(f):
                        os.remove(f)
                # Возвращаем сообщение об ошибке
                return [f"Ошибка при создании части {i}"]
            
            # Проверяем, что файл создан и не пустой
            if os.path.exists(output_part) and os.path.getsize(output_part) > 0:
                # Добавляем путь к файлу в список успешных
                output_files.append(output_part)
            else:
                # Если файл не создан или пустой
                return [f"Ошибка: Файл части {i} не был создан"]
        
        # Возвращаем список путей к созданным файлам
        return output_files
        
    except Exception as e:
        # Если произошла непредвиденная ошибка
        return [f"Ошибка при разрезании видео: {str(e)}"]


# Функция 2: Заменяет часть видео на готовую отмонтажированную часть
async def replace_with_effect(original_part_path: str, effect_name: str):
    """
    Заменяет часть видео на готовую отмонтажированную часть из папки effects
    
    Args:
        original_part_path (str): Путь к оригинальной части, которую нужно заменить
        effect_name (str): Название эффекта (имя файла без .mp4 в папке effects)
    
    Returns:
        str: Путь к файлу с эффектом (или оригинальной части, если эффект не найден)
    """
    try:
        # Формируем путь к файлу с эффектом в папке effects
        # Например: "effects/zoom_in.mp4"
        effect_path = f"effects/video_2025-12-03_22-31-14.mp4"
        
        # Проверяем, существует ли файл с эффектом
        if not os.path.exists(effect_path):
            # Если файла с эффектом нет, возвращаем оригинальную часть
            return original_part_path
        
        # Получаем директорию, где лежит оригинальная часть
        video_dir = os.path.dirname(original_part_path)
        # Получаем имя оригинального файла (например, "video_123_part_2.mp4")
        part_name = os.path.basename(original_part_path)
        # Убираем расширение, оставляем только имя
        name_without_ext = os.path.splitext(part_name)[0]
        
        # Формируем имя для файла с эффектом в той же директории
        # Например: "video_123_part_2_zoom_in.mp4"
        effect_output = os.path.join(video_dir, f"{name_without_ext}_{effect_name}.mp4")
        
        # ПРОСТО КОПИРУЕМ готовую отмонтажированную часть
        # Это имитация AI-монтажа: вместо реального монтажа мы подменяем часть
        # заранее подготовленным видео
        shutil.copy2(effect_path, effect_output)
        
        # Возвращаем путь к скопированному файлу с эффектом
        return effect_output
        
    except Exception as e:
        # Если произошла ошибка при копировании, возвращаем оригинальную часть
        return original_part_path


# Функция 3: Склеивает все части в одно видео
async def merge_video_parts(parts_paths: list, original_name: str):
    """
    Склеивает несколько видеофайлов в один
    
    Args:
        parts_paths (list): Список путей к файлам, которые нужно склеить
        original_name (str): Исходное имя видео (без расширения) для именования результата
    
    Returns:
        str: Путь к склеенному видео или строка с ошибкой
    """
    try:
        # Проверяем, что есть что склеивать
        if not parts_paths:
            return "Ошибка: Нет частей для склейки"
            
        # Получаем директорию первой части (все части в одной директории)
        video_dir = os.path.dirname(parts_paths[0])
        
        # Создаём текстовый файл со списком видео для склейки
        # FFmpeg требует такой файл для формата concat
        list_file = os.path.join(video_dir, f"{original_name}_list.txt")
        
        # Открываем файл для записи (w = write, encoding='utf-8' для корректной работы с путями)
        with open(list_file, 'w', encoding='utf-8') as f:
            # Записываем каждый файл в формате: file 'полный_путь_к_файлу'
            for part in parts_paths:
                # os.path.abspath() получает абсолютный путь к файлу
                f.write(f"file '{os.path.abspath(part)}'\n")
        
        # Формируем имя для итогового склеенного видео
        # Например: "video_123_final.mp4"
        output_video = os.path.join(video_dir, f"{original_name}_final.mp4")
        
        # Формируем команду для склейки:
        # ffmpeg -f concat -safe 0 -i список_файлов.txt -кодеки выходной_файл.mp4
        cmd = [
            'ffmpeg',  # Основная команда
            '-f', 'concat',  # Указываем формат конкатенации (склейки)
            '-safe', '0',  # Разрешаем абсолютные пути в файле списка
            '-i', list_file,  # Файл со списком видео для склейки
            '-c:v', 'libx264',  # Кодек видео (перекодируем для надёжности)
            '-c:a', 'aac',  # Кодек аудио
            '-y',  # Автоматически подтверждаем перезапись
            output_video  # Выходной файл
        ]
        
        # Запускаем FFmpeg асинхронно
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Ждём завершения процесса
        stdout, stderr = await process.communicate()
        
        # Удаляем временный файл списка (он больше не нужен)
        if os.path.exists(list_file):
            os.remove(list_file)
        
        # Проверяем успешность выполнения
        if process.returncode != 0:
            # Если ошибка, удаляем частично созданный файл
            if os.path.exists(output_video):
                os.remove(output_video)
            return f"Ошибка при склейке видео"
        
        # Возвращаем путь к готовому склеенному видео
        return output_video
        
    except Exception as e:
        # Если произошла непредвиденная ошибка
        return f"Ошибка при склейке: {str(e)}"