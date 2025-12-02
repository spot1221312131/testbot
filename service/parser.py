import json

from service.ffmpeg import cut_video_simple


async def process_video_with_ffmpeg(video_path: str, command_json: dict):
    try:
        response_str = command_json.get('response', '')
        
        if not response_str:
            return ["Ошибка: Пустой response в ответе LLM"]
        
        try:
            response_str_clean = response_str.strip()
            command_info = json.loads(response_str_clean)
        except json.JSONDecodeError as e:
            return [f"Ошибка: Неверный формат JSON в ответе LLM. Детали: {str(e)}"]
        
        tool = command_info.get('tool', '')
        args = command_info.get('args', {})
        
        if not tool:
            return ["Ошибка: Не указан tool в команде"]
        
        if tool == 'cut_video':
            result = await cut_video_simple(video_path, args)
            return result
        else:
            return [f"Ошибка: Неизвестная команда '{tool}'"]
            
    except Exception as e:
        return [f"Критическая ошибка: {str(e)}"]