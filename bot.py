import asyncio
import random
import requests
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import TOKEN, THE_CAT_API_KEY, NASA_API_KEY, OPENWEATHER_API_KEY

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ====================== The Cat API Functions ======================
def get_cat_breeds():
    url = "https://api.thecatapi.com/v1/breeds"
    headers = {"x-api-key": THE_CAT_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()


def get_cat_image_by_breed(breed_id):
    url = f"https://api.thecatapi.com/v1/images/search?breed_ids={breed_id}"
    headers = {"x-api-key": THE_CAT_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data[0]['url'] if data else None


def get_breed_info(breed_name):
    breeds = get_cat_breeds()
    for breed in breeds:
        if breed['name'].lower() == breed_name.lower():
            return breed
    return None


# ====================== NASA APOD API Functions ======================
def get_random_apod():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)  # 5 лет истории
    random_date = start_date + (end_date - start_date) * random.random()
    date_str = random_date.strftime("%Y-%m-%d")

    url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={date_str}'
    response = requests.get(url)
    return response.json()


# ====================== Random User API Functions ======================
def get_random_user():
    url = "https://randomuser.me/api/"
    response = requests.get(url)
    data = response.json()['results'][0]
    return {
        'name': f"{data['name']['first']} {data['name']['last']}",
        'gender': data['gender'],
        'email': data['email'],
        'phone': data['phone'],
        'location': f"{data['location']['city']}, {data['location']['country']}",
        'picture': data['picture']['large']
    }


# ====================== OpenWeather API Functions ======================
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    return {
        'city': data['name'],
        'temp': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'description': data['weather'][0]['description'],
        'humidity': data['main']['humidity'],
        'wind': data['wind']['speed'],
        'icon': f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
    }


# ====================== Handlers ======================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    welcome_text = (
        "?? Привет! Я бот с интеграцией различных API.\n"
        "Вот что я умею:\n\n"
        "?? /cat <порода> - Информация о породе кошки\n"
        "?? /apod - Случайная космическая фотография дня от NASA\n"
        "?? /user - Случайный пользователь\n"
        "?? /weather <город> - Погода в указанном городе\n"
        "?? /help - Список команд"
    )
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "?? Доступные команды:\n\n"
        "?? /cat <порода> - Информация о породе кошки (например: /cat siamese)\n"
        "?? /apod - Случайная космическая фотография дня от NASA\n"
        "?? /user - Случайный пользователь с аватаром\n"
        "?? /weather <город> - Погода в указанном городе (например: /weather Москва)\n"
        "?? /help - Показать это сообщение"
    )
    await message.answer(help_text)


@dp.message(Command("cat"))
async def cat_command(message: types.Message):
    breed_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not breed_name:
        await message.answer("Пожалуйста, укажите породу кошки. Например: /cat siamese")
        return

    breed_info = get_breed_info(breed_name)
    if not breed_info:
        await message.answer("?? Порода не найдена. Попробуйте еще раз.")
        return

    cat_image_url = get_cat_image_by_breed(breed_info['id'])
    if not cat_image_url:
        await message.answer("?? Не удалось загрузить изображение кошки.")
        return

    info = (
        f"?? <b>{breed_info['name']}</b>\n\n"
        f"?? <i>{breed_info['description']}</i>\n\n"
        f"? Продолжительность жизни: {breed_info['life_span']} лет\n"
        f"?? Происхождение: {breed_info.get('origin', 'неизвестно')}\n"
        f"?? Темперамент: {breed_info.get('temperament', 'неизвестно')}"
    )

    await message.answer_photo(photo=cat_image_url, caption=info, parse_mode="HTML")


@dp.message(Command("apod"))
async def apod_command(message: types.Message):
    try:
        apod = get_random_apod()
        if 'url' not in apod:
            await message.answer("?? Не удалось получить изображение. Попробуйте позже.")
            return

        title = apod.get('title', 'Космическое изображение')
        explanation = apod.get('explanation', 'Описание недоступно')

        caption = f"?? <b>{title}</b>\n\n{explanation[:1000]}..."
        await message.answer_photo(photo=apod['url'], caption=caption, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"?? Ошибка: {str(e)}")


@dp.message(Command("user"))
async def user_command(message: types.Message):
    try:
        user = get_random_user()
        user_info = (
            f"?? <b>{user['name']}</b>\n"
            f"?? Пол: {user['gender']}\n"
            f"?? Email: {user['email']}\n"
            f"?? Телефон: {user['phone']}\n"
            f"?? Местоположение: {user['location']}"
        )
        await message.answer_photo(photo=user['picture'], caption=user_info, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"?? Ошибка при получении пользователя: {str(e)}")


@dp.message(Command("weather"))
async def weather_command(message: types.Message):
    city = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not city:
        await message.answer("Пожалуйста, укажите город. Например: /weather Москва")
        return

    weather = get_weather(city)
    if not weather:
        await message.answer(f"?? Не удалось найти погоду для города: {city}")
        return

    weather_info = (
        f"?? <b>{weather['city']}</b>\n\n"
        f"??? Температура: {weather['temp']}°C\n"
        f"?? Ощущается как: {weather['feels_like']}°C\n"
        f"?? Описание: {weather['description'].capitalize()}\n"
        f"?? Влажность: {weather['humidity']}%\n"
        f"?? Ветер: {weather['wind']} м/с"
    )

    await message.answer_photo(
        photo=weather['icon'],
        caption=weather_info,
        parse_mode="HTML"
    )


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
