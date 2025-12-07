import json
import os
from service.ffmpeg import cut_video_into_parts, merge_video_parts, replace_with_effect


async def process_video_with_ffmpeg(video_path: str, command_json: dict):
    try:
        if not video_path or not os.path.exists(video_path):
            return ["ошибка: исходное видео не найдено"]
        
        response_str = command_json.get('response', '')
        
        if not response_str:
            return ["ошибка: пустой ответ от AI"]
        
        import re

        json_in_markdown = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if json_in_markdown:
            response_str = json_in_markdown.group(1)
        else:
            json_match_simple = re.search(r'\{[\s\S]*\}', response_str)
            if json_match_simple:
                response_str = json_match_simple.group(0)
        
        response_str = response_str.replace('\n', ' ').replace('\r', ' ').strip()
        
        try:
            plan = json.loads(response_str)
        except json.JSONDecodeError as e:
            first_brace = response_str.find('{')
            last_brace = response_str.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                try:
                    json_str = response_str[first_brace:last_brace + 1]
                    plan = json.loads(json_str)
                except Exception as parse_error:
                    json_match = re.search(r'\{[\s\S]*\}', response_str)
                    if json_match:
                        try:
                            plan = json.loads(json_match.group(0))
                        except:
                            return [f"ошибка: неверный формат JSON от AI, ответ: {response_str[:200]}..."]
                    else:
                        return [f"ошибка: неверный формат JSON от AI, ответ: {response_str[:200]}..."]
            else:
                return [f"ошибка: не найден JSON в ответе AI, ответ: {response_str[:200]}..."]
        
        parts = plan.get('parts', [])
        
        if not parts:
            return ["ошибка: AI не предоставил план монтажа"]
        
        print(f"DEBUG: Получен план монтажа с {len(parts)} частями")
        for i, part in enumerate(parts):
            print(f"DEBUG: часть {i+1}: {part.get('start_sec')} - {part.get('end_sec')}, action={part.get('action')}, effect={part.get('effect_name')}")
        
        try:
            import subprocess
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                   '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            video_duration = float(result.stdout.strip())
            
            print(f"DEBUG: длительность видео: {video_duration} секунд")
            
            parts.sort(key=lambda x: float(x.get('start_sec', 0)))
            
            for i, part in enumerate(parts):
                start_sec = float(part.get('start_sec', 0))
                end_sec = float(part.get('end_sec', video_duration))
                
                start_sec = max(0, min(start_sec, video_duration))
                end_sec = max(0, min(end_sec, video_duration))
                
                if start_sec >= end_sec:
                    if start_sec >= video_duration:
                        start_sec = max(0, video_duration - 1)
                    end_sec = min(start_sec + 1, video_duration)
                
                if i == len(parts) - 1:
                    end_sec = video_duration
                
                part['start_sec'] = start_sec
                part['end_sec'] = end_sec
                print(f"DEBUG: Скорректирована часть {i+1}: {start_sec} - {end_sec}")
        except:
            pass
        
        cut_parts = await cut_video_into_parts(video_path, parts)
        
        if isinstance(cut_parts, list) and len(cut_parts) > 0 and cut_parts[0].startswith("Ошибка"):
            return cut_parts
        
        if len(parts) != len(cut_parts):
            for part in cut_parts:
                if os.path.exists(part):
                    try:
                        os.remove(part)
                    except:
                        pass
            return [f"ошибка: несоответствие количества частей (план: {len(parts)}, создано: {len(cut_parts)})"]
        
        processed_parts = []
        
        for i, (part_info, part_path) in enumerate(zip(parts, cut_parts)):
            if part_info.get('action') == 'edit':
                effect_name = part_info.get('effect_name')

                if effect_name:
                    effect_path = await replace_with_effect(part_path, effect_name)
                    processed_parts.append(effect_path)
                else:
                    processed_parts.append(part_path)
            else:
                processed_parts.append(part_path)
        
        video_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(video_name)[0]
        
        final_video = await merge_video_parts(processed_parts, name_without_ext)
        
        if isinstance(final_video, str) and final_video.startswith("ошибка"):
            return [final_video]
        
        files_to_keep = set(processed_parts)
        files_to_keep.add(final_video)
        
        for part in cut_parts:
            if part not in files_to_keep and os.path.exists(part):
                try:
                    os.remove(part)
                except:
                    pass
        
        for part in processed_parts:
            if part != final_video and os.path.exists(part):
                if part not in cut_parts:
                    try:
                        os.remove(part)
                    except:
                        pass
        
        return [final_video]
        
    except Exception as e:
        return [f"критическая ошибка: {str(e)}"]