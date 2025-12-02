import asyncio
import os


async def cut_video_simple(video_path: str, args: dict):
    """
    Простая асинхронная обрезка видео
    """
    try:
        start_sec = args.get('start_sec', 0)
        end_sec = args.get('end_sec', 0)
        
        if end_sec <= start_sec:
            return ["Ошибка: end_sec должен быть больше start_sec"]
        
        # Создаем выходные файлы
        video_dir = os.path.dirname(video_path)
        video_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(video_name)[0]
        
        output_files = []
        
        # Часть 1: от start_sec до end_sec
        output_part1 = os.path.join(video_dir, f"{name_without_ext}_part1.mp4")
        
        cmd1 = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_sec),
            '-t', str(end_sec - start_sec),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-y',
            output_part1
        ]
        
        # Запускаем асинхронно
        process1 = await asyncio.create_subprocess_exec(
            *cmd1,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout1, stderr1 = await process1.communicate()
        
        if process1.returncode == 0:
            output_files.append(output_part1)
        else:
            error_msg = stderr1.decode('utf-8', errors='ignore')[:500]
            return [f"Ошибка при создании первой части: {error_msg}"]
        
        # Часть 2: от end_sec до конца
        try:
            # Проверяем длительность видео
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            process_probe = await asyncio.create_subprocess_exec(
                *probe_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_probe, stderr_probe = await process_probe.communicate()
            
            if process_probe.returncode == 0:
                total_duration = float(stdout_probe.decode().strip())
                
                if total_duration > end_sec:
                    output_part2 = os.path.join(video_dir, f"{name_without_ext}_part2.mp4")
                    
                    cmd2 = [
                        'ffmpeg',
                        '-i', video_path,
                        '-ss', str(end_sec),
                        '-c', 'copy',
                        '-y',
                        output_part2
                    ]
                    
                    process2 = await asyncio.create_subprocess_exec(
                        *cmd2,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout2, stderr2 = await process2.communicate()
                    
                    if process2.returncode == 0:
                        output_files.append(output_part2)
                        
        except Exception as e:
            # Продолжаем только с первой частью
            pass
        
        return output_files
        
    except Exception as e:
        return [f"Ошибка при обрезке видео: {str(e)}"]