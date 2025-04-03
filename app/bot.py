import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv
import random
import re
import logging

from generation.generation_route import generate_route
from generation.generate_artwork_info import generate_artwork_info
from generation.generate_answer import generate_answer, generate_answer_max
from process_data.load_data import send_text_in_chunks, send_text_with_image
from generation.generate_goodbye_word import generate_goodbye_word
from validation.validation_QA import evaluate_hallucinations
from validation.validation_artworkinfo import evaluate_hallucinations_artworkinfo

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

def create_keyboard(buttons):
    keyboard = InlineKeyboardBuilder()
    for text, data in buttons:
        keyboard.button(text=text, callback_data=data)
    return keyboard.as_markup()

@dp.message(Command("start"))
async def start(message: Message):
    user_data[message.from_user.id] = {'state': 'route_mode', 'current_artwork_index': 0, 'last_shown_artwork_index': 0}
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Старт")]],
        resize_keyboard=True, one_time_keyboard=True
    )

    await message.answer(
        "Привет! 👋 Я твой гид по виртуальному выставочному фонду ОЦ «Сириус». Моя цель — рассказать об экспонатах и истории, которые делают каждую выставку уникальной.\n"
        "\n"
        "Но сначала давай познакомимся! Расскажи немного о себе: сколько тебе лет, чем ты увлекаешься? "
        "Что тебя привело в наше пространство — ты здесь ради вдохновения, учебы или просто решил(а) интересно провести время? "
        "Чем больше я о тебе узнаю, тем более персонализированной будет твоя экскурсия! 😊", 
        reply_markup=keyboard
    )
    user_data[message.from_user.id]['state'] = 'awaiting_description'


@dp.message()
async def handle_user_input(message: Message):
    user_id = message.from_user.id
    state = user_data.get(user_id, {}).get('state')

    if state == 'awaiting_description':
        user_data[user_id]['user_description'] = message.text  
        user_data[user_id]['send_images'] = True  

        keyboard = create_keyboard([
            ("🕒 Экспресс", "short"),
            ("⏳ Стандарт", "medium"),
            ("🕰 Полное погружение", "long")
        ])

        await message.answer(
            "Я очень рад с вами познакомиться! Теперь выберите продолжительность экскурсии:",
            reply_markup=keyboard
        )

        user_data[user_id]['state'] = 'awaiting_tour_length'

    elif state == 'route_mode':
        await message.answer("Подождите немного, я готовлю ваш маршрут... ⏳")
        user_query = message.text
        user_description = user_data[user_id].get('user_description', '')
        top_k = user_data[user_id].get('top_k', 5)
        logging.debug(f'top_k: {top_k}')
        route, artworks = generate_route(top_k, user_description, user_query)
        user_data[user_id]['artworks'] = artworks

        clean_route = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,:"«»]', '', route)
        await send_text_in_chunks(clean_route, lambda text: message.answer(text))

        keyboard = create_keyboard([("Да, я готов(а)", "next_artwork")])
        await message.answer("Вы готовы начать экскурсию?", reply_markup=keyboard)

    elif state == 'question_mode':
        await process_question(message)


@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data in ["short", "medium", "long"]:
        await handle_tour_length(callback)
    elif callback.data == "next_artwork":
        await next_artwork(callback)
    elif callback.data == "end_tour":
        await end_tour(callback)

async def handle_tour_length(callback: CallbackQuery):
    user_id = callback.from_user.id
    tour_lengths = {
        "short": random.randint(2, 5),
        "medium": random.randint(8, 12),
        "long": random.randint(13, 20)
    }

    if callback.data in tour_lengths:
        user_data[user_id]['top_k'] = tour_lengths[callback.data]

    
    user_data[user_id]['state'] = 'route_mode'

    await callback.message.answer("Что бы вы хотели посмотреть в музее сегодня?")


async def process_question(message: Message):
    user_id = message.from_user.id
    user_question = message.text
    index = user_data[user_id]['last_shown_artwork_index']
    artwork = user_data[user_id]['artworks'][index]
    user_description = user_data[user_id].get('user_description', '')

    await message.answer("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    answer = generate_answer(user_question, artwork, user_description)
    validation_res = evaluate_hallucinations(artwork.get("text"), answer, user_question)
    logging.debug(f'validation result:{ validation_res}')
    

    if validation_res.lower() == "false":
        await message.answer(answer)
    else: 
        answer_max = generate_answer_max(user_question, artwork, user_description)
        secondary_validation_res = evaluate_hallucinations(artwork.get("text"), answer_max, user_question)

        if secondary_validation_res.lower() == "false":
            await message.answer(answer_max)  
        else: 
            await message.answer("К сожалению, я затрудняюсь ответить. Пожалуйста перефразируйте ваш вопрос.")


async def next_artwork(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_artwork_index = user_data[user_id].get('current_artwork_index', 0) 
    user_data[user_id]['state'] = 'question_mode'
    user_data[user_id]['last_shown_artwork_index'] = current_artwork_index
    artwork = user_data[user_id]['artworks'][current_artwork_index]

    await callback.message.answer("Обрабатываю ваш запрос... Подождите немного! ⏳")
    artwork_info = generate_artwork_info(artwork.get("text"), user_data[user_id].get('user_description', ''))
    validation_res = evaluate_hallucinations_artworkinfo(artwork.get("text"), artwork_info)
    logging.debug(f'validation result:{ validation_res}')

    image_url = artwork.get("image")

    if image_url:
        await send_text_with_image(
            artwork_info, 
            image_url, 
            lambda text: callback.message.answer(text), 
            lambda url, caption: callback.message.answer_photo(url, caption=caption)
        )
    else:
        await send_text_in_chunks(artwork_info, lambda text: callback.message.answer(text))

    user_data[user_id]['current_artwork_index'] += 1

    if user_data[user_id]['current_artwork_index'] < len(user_data[user_id]['artworks']):
        keyboard = create_keyboard([("Следующий экспонат", "next_artwork")])
        await callback.message.answer("Задайте вопрос о текущем экспонате или нажмите ниже, чтобы перейти к следующему.", reply_markup=keyboard)
    else:
        keyboard = create_keyboard([("Завершить маршрут", "end_tour")])
        await callback.message.answer("Задайте вопрос о текущем экспонате. Это последний экспонат нашего маршрута!", reply_markup=keyboard)


async def end_tour(callback: CallbackQuery):
    user_id = callback.from_user.id
    museum_info = "\n\nПродолжить знакомство с миром искусства вы можете на сайте: https://photo.sirius.ru/links/YwWpZAppgnsZYQhAKJvfFM"
    await callback.message.answer(generate_goodbye_word(user_data[user_id].get('user_description', '')) + museum_info)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
