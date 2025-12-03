import json
import os
from service.ffmpeg import cut_video_into_parts, merge_video_parts, replace_with_effect


async def process_video_with_ffmpeg(video_path: str, command_json: dict):
    try:
        response_str = command_json.get('response', '')
        
        if not response_str:
            return ["Ошибка: Пустой ответ от AI"]
        
        # Убираем переносы строк из JSON строки
        response_str = response_str.replace('\n', ' ').replace('\r', ' ')
        
        try:
            # Преобразуем JSON строку в объект
            plan = json.loads(response_str)
        except json.JSONDecodeError as e:
            # Пробуем очистить строку от лишних символов
            import re
            json_match = re.search(r'\{.*\}', response_str)
            if json_match:
                try:
                    plan = json.loads(json_match.group(0))
                except:
                    return [f"Ошибка: Неверный формат JSON от AI. Ответ: {response_str[:100]}..."]
            else:
                return [f"Ошибка: Не найден JSON в ответе AI. Ответ: {response_str[:100]}..."]
        
        # Получаем план монтажа от AI
        parts = plan.get('parts', [])
        
        if not parts:
            return ["Ошибка: AI не предоставил план монтажа"]
        
        # Проверяем, что времена не выходят за пределы видео
        # Сначала узнаем длительность видео
        try:
            import subprocess
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                   '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            video_duration = float(result.stdout.strip())
            
            # Корректируем времена, если они выходят за пределы видео
            for part in parts:
                if part['end_sec'] > video_duration:
                    part['end_sec'] = video_duration
                if part['start_sec'] > video_duration:
                    part['start_sec'] = 0
        except:
            # Если не удалось определить длительность, продолжаем как есть
            pass
        
        # ШАГ 1: Режем видео на части
        cut_parts = await cut_video_into_parts(video_path, parts)
        
        # Проверяем на ошибки
        if isinstance(cut_parts, list) and len(cut_parts) > 0 and cut_parts[0].startswith("Ошибка"):
            return cut_parts
        
        # ШАГ 2: Обрабатываем каждую часть
        processed_parts = []
        
        for i, (part_info, part_path) in enumerate(zip(parts, cut_parts)):
            # Если часть нужно отредактировать
            if part_info.get('action') == 'edit':
                # Получаем название эффекта
                effect_name = part_info.get('effect_name')
                if effect_name:
                    # Заменяем часть на эффект
                    effect_path = await replace_with_effect(part_path, effect_name)
                    processed_parts.append(effect_path)
                else:
                    # Если эффекта нет - оставляем оригинал
                    processed_parts.append(part_path)
            else:
                # Для частей без редактирования оставляем как есть
                processed_parts.append(part_path)
        
        # ШАГ 3: Склеиваем все части обратно
        video_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(video_name)[0]
        
        final_video = await merge_video_parts(processed_parts, name_without_ext)
        
        # Проверяем на ошибки
        if isinstance(final_video, str) and final_video.startswith("Ошибка"):
            return [final_video]
        
        # ШАГ 4: Удаляем временные части
        for part in cut_parts:
            if os.path.exists(part):
                try:
                    os.remove(part)
                except:
                    pass
        
        # Удаляем обработанные части с эффектами
        for part in processed_parts:
            # Если это не оригинальная часть (она уже удалена)
            if part in cut_parts:
                continue
            if os.path.exists(part):
                try:
                    os.remove(part)
                except:
                    pass
        
        # Возвращаем путь к финальному видео
        return [final_video]
        
    except Exception as e:
        return [f"Критическая ошибка: {str(e)}"]