import asyncio
import os
import shutil


async def cut_video_into_parts(video_path: str, parts_info: list):
    try:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(video_name)[0]

        output_files = []

        for i, part in enumerate(parts_info, 1):
            start_sec = float(part.get('start_sec', 0))
            end_sec = float(part.get('end_sec', 0))
            duration = end_sec - start_sec

            if duration <= 0:
                return [f"ошибка, некорректная длительность части {i} (начало: {start_sec}, конец: {end_sec})"]
            if start_sec < 0:
                return [f"ошибка, отрицательное время начала части {i}"]
            
            output_part = os.path.join(video_dir, f"{name_without_ext}_part_{i}.mp4")

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_sec),
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                output_part
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                for f in output_files:
                    if os.path.exists(f):
                        os.remove(f)
                return [f'ошибка при создании части {i}']
            
            if os.path.exists(output_part) and os.path.getsize(output_part) > 0:
                output_files.append(output_part)
            else:
                return [f"ошибка: файл части {i} не был создан"]
            
        return output_files
    
    except Exception as e:
        return [f'ошибка при разрезании видео: {str(e)}']
    

async def replace_with_effect(original_part_path: str, effect_name: str):
    try:
        video_dir = os.path.dirname(original_part_path)
        part_name = os.path.basename(original_part_path)
        name_without_ext = os.path.splitext(part_name)[0]
        
        effect_output = os.path.join(video_dir, f"{name_without_ext}_{effect_name}.mp4")
        
        vf_filter = None
        
        if effect_name == "darken":
            vf_filter = 'eq=brightness=-0.5:contrast=1.0'
        
        elif effect_name == "brighten":
            vf_filter = 'eq=brightness=0.5:contrast=1.0'
        
        elif effect_name == "black_white":
            vf_filter = 'hue=s=0'
        
        elif effect_name == "saturate":
            vf_filter = 'eq=saturation=1.5'
        
        elif effect_name == "desaturate":
            vf_filter = 'eq=saturation=0.5'
        
        elif effect_name == "blur":
            vf_filter = 'boxblur=5:1'
        
        elif effect_name == "sharpen":
            vf_filter = 'unsharp=5:5:1.0:5:5:0.0'
        
        elif effect_name == "contrast":
            vf_filter = 'eq=contrast=1.5'
        
        elif effect_name == "zoom_in":
            vf_filter = 'crop=iw*0.8:ih*0.8:iw*0.1:ih*0.1,scale=iw*1.25:ih*1.25'
        
        elif effect_name == "zoom_out":
            vf_filter = 'scale=iw*0.8:ih*0.8,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black'
        
        elif effect_name == "slow_motion":
            vf_filter = 'setpts=2.0*PTS'
            cmd = [
                'ffmpeg',
                '-i', original_part_path,
                '-filter_complex', '[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]',
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                effect_output
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0 and os.path.exists(effect_output) and os.path.getsize(effect_output) > 0:
                return effect_output
            return original_part_path
        
        elif effect_name == "fast_motion":
            vf_filter = 'setpts=0.5*PTS'
            cmd = [
                'ffmpeg',
                '-i', original_part_path,
                '-filter_complex', '[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]',
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                effect_output
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0 and os.path.exists(effect_output) and os.path.getsize(effect_output) > 0:
                return effect_output
            return original_part_path
        
        elif effect_name == "rotate":
            vf_filter = 'transpose=1'
        
        elif effect_name == "flip_horizontal":
            vf_filter = 'hflip'
        
        elif effect_name == "flip_vertical":
            vf_filter = 'vflip'
        
        elif effect_name == "vignette":
            vf_filter = 'vignette=PI/4'
        
        elif effect_name == "sepia":
            vf_filter = 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131'
        
        elif effect_name == "invert":
            vf_filter = 'negate'
        
        if vf_filter:
            cmd = [
                'ffmpeg',
                '-i', original_part_path,
                '-vf', vf_filter,
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-y',
                effect_output
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"ошибка FFmpeg для эффекта {effect_name}: {stderr.decode()}")
                return original_part_path
            
            if os.path.exists(effect_output) and os.path.getsize(effect_output) > 0:
                return effect_output
            else:
                return original_part_path
        
        effect_path = f"effects/{effect_name}.mp4"
        
        if not os.path.exists(effect_path):
            effects_dir = "effects"
            if os.path.exists(effects_dir):
                for file in os.listdir(effects_dir):
                    if file.endswith('.mp4'):
                        effect_path = os.path.join(effects_dir, file)
                        break
                else:
                    return original_part_path
            else:
                return original_part_path
        
        shutil.copy2(effect_path, effect_output)
        
        return effect_output
        
    except Exception as e:
        return original_part_path


async def merge_video_parts(parts_paths: list, original_name: str):
    try:
        if not parts_paths:
            return "ошибка: нету частей для склейки"
            
        video_dir = os.path.dirname(parts_paths[0])
        
        list_file = os.path.join(video_dir, f"{original_name}_list.txt")
        
        for part in parts_paths:
            if not os.path.exists(part):
                return f"ошибка: файл {part} не найден"
            if os.path.getsize(part) == 0:
                return f"ошибка: файл {part} пустой"

        with open(list_file, 'w', encoding='utf-8') as f:
            for part in parts_paths:
                abs_path = os.path.abspath(part).replace("'", "'\\''")
                f.write(f"file '{abs_path}'\n")
        
        output_video = os.path.join(video_dir, f"{original_name}_final.mp4")
        
        cmd = [
            'ffmpeg', 
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c:v', 'libx264', 
            '-c:a', 'aac', 
            '-y', 
            output_video
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if os.path.exists(list_file):
            os.remove(list_file)

        if process.returncode != 0:
            if os.path.exists(output_video):
                os.remove(output_video)
            return f"ошибка при склейке видео"
        
        return output_video
        
    except Exception as e:
        return f"ошибка при склейке: {str(e)}"
                

