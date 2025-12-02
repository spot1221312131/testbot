import os
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from service.ollama import assembly_request
from service.parser import process_video_with_ffmpeg


user_private_router = Router()


class WaitData(StatesGroup):
    video = State()
    promt = State()


@user_private_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer('Бот тестов, начнем с вашего видео, жду его!')
    await state.set_state(WaitData.video)


@user_private_router.message(WaitData.video, F.video)
async def video_user(message: types.Message, state: FSMContext):
    video = message.video

    # Получаем путь к файлу на серверах Telegram
    video_file_info = await message.bot.get_file(video.file_id)

    # Формируем путь для сохранения
    video_file_path = video_file_info.file_path
    video_filename = f'downloads_video/video_{video.file_unique_id}.mp4'

    await message.bot.download_file(video_file_path, video_filename)

    await message.answer('Видео получено и скачено\nОтправьте описание монтажа и что нужно сделать')
    await state.update_data(video_path=video_filename)
    await state.set_state(WaitData.promt)


@user_private_router.message(WaitData.promt, F.text)
async def promt_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    promt = message.text
    video_path = data.get("video_path")
    
    command = await assembly_request(promt)
    await message.answer('супер, мы получили и проанализировали ваше описание, сейчас работаем над монтажем видео..')
    try:
        result_files = await process_video_with_ffmpeg(video_path, command)
        
        if result_files and not isinstance(result_files[0], str):
            for file_path in result_files:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as video_file:
                        await message.answer_video(
                            types.BufferedInputFile(
                                video_file.read(),
                                filename=os.path.basename(file_path)
                            ),
                            caption=f"Часть видео"
                        )
                        os.remove(file_path)
        else:
            await message.answer(f"Ошибка: {result_files[0] if result_files else 'Неизвестная ошибка'}")
            
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    
    await state.clear()
    await message.answer('Обработка завершена!')
    os.remove(video_path)
