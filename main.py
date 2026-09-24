import os
import json
import time
import urllib.request
import urllib.parse

# Токен будет добавлен на сервере Render.
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ Ошибка: переменная BOT_TOKEN не задана")
    raise SystemExit

API = f"https://api.telegram.org/bot{TOKEN}"


def telegram(method, data=None):
    url = f"{API}/{method}"

    if data:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(url, data=encoded)
    else:
        request = urllib.request.Request(url)

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = json.dumps(keyboard, ensure_ascii=False)

    return telegram("sendMessage", data)


def main_menu():
    return {
        "keyboard": [
            ["🏪 Мой бизнес"],
            ["🛍 Каталог", "📦 Заказы"],
            ["➕ Добавить товар"],
            ["📊 Статистика", "⚙️ Настройки"]
        ],
        "resize_keyboard": True
    }


def business_menu():
    return {
        "keyboard": [
            ["🏢 Создать бизнес"],
            ["📋 Данные бизнеса"],
            ["📞 Контакты"],
            ["🚚 Доставка"],
            ["⬅️ Назад"]
        ],
        "resize_keyboard": True
    }


def settings_menu():
    return {
        "keyboard": [
            ["🔔 Уведомления"],
            ["🌐 Язык"],
            ["⬅️ Назад"]
        ],
        "resize_keyboard": True
    }


def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return

    if text == "/start":
        send_message(
            chat_id,
            "🏪 Бизнес в Telegram\n\n"
            "Добро пожаловать!\n\n"
            "Создайте свой бизнес и управляйте "
            "магазином прямо в Telegram.\n\n"
            "Выберите нужный раздел:",
            main_menu()
        )

    elif text == "🏪 Мой бизнес":
        send_message(
            chat_id,
            "🏪 Мой бизнес\n\n"
            "Здесь вы сможете создать и настроить "
            "свой бизнес.",
            business_menu()
        )

    elif text == "🏢 Создать бизнес":
        send_message(
            chat_id,
            "🏢 Создание бизнеса\n\n"
            "На следующем этапе здесь появится "
            "пошаговая регистрация бизнеса."
        )

    elif text == "📋 Данные бизнеса":
        send_message(
            chat_id,
            "📋 Данные бизнеса\n\n"
            "Название: пока не указано\n"
            "Описание: пока не указано\n"
            "Телефон: пока не указан"
        )

    elif text == "📞 Контакты":
        send_message(
            chat_id,
            "📞 Контакты\n\n"
            "Контактные данные бизнеса пока не заполнены."
        )

    elif text == "🚚 Доставка":
        send_message(
            chat_id,
            "🚚 Доставка\n\n"
            "Настройки доставки появятся здесь."
        )

    elif text == "🛍 Каталог":
        send_message(
            chat_id,
            "🛍 Каталог\n\n"
            "Ваш каталог пока пуст.\n\n"
            "Используйте «➕ Добавить товар», "
            "чтобы добавить первый товар."
        )

    elif text == "📦 Заказы":
        send_message(
            chat_id,
            "📦 Заказы\n\n"
            "Пока заказов нет."
        )

    elif text == "➕ Добавить товар":
        send_message(
            chat_id,
            "➕ Добавление товара\n\n"
            "На следующем этапе сделаем форму:\n"
            "1️⃣ Название товара\n"
            "2️⃣ Цена\n"
            "3️⃣ Описание\n"
            "4️⃣ Фото\n"
            "5️⃣ Сохранение товара"
        )

    elif text == "📊 Статистика":
        send_message(
            chat_id,
            "📊 Статистика\n\n"
            "Заказов: 0\n"
            "Товаров: 0\n"
            "Продаж: 0"
        )

    elif text == "⚙️ Настройки":
        send_message(
            chat_id,
            "⚙️ Настройки",
            settings_menu()
        )

    elif text == "🔔 Уведомления":
        send_message(
            chat_id,
            "🔔 Уведомления\n\n"
            "Настройки уведомлений пока находятся "
            "в разработке."
        )

    elif text == "🌐 Язык":
        send_message(
            chat_id,
            "🌐 Язык\n\n"
            "🇷🇺 Русский\n"
            "🇺🇿 O'zbekcha\n"
            "🇬🇧 English"
        )

    elif text == "⬅️ Назад":
        send_message(
            chat_id,
            "🏪 Главное меню",
            main_menu()
        )

    else:
        send_message(
            chat_id,
            "Я пока не знаю эту команду.\n\n"
            "Выберите действие из меню 👇",
            main_menu()
        )


def main():
    print("================================")
    print("🚀 BusinessShopBot запускается")
    print("================================")

    bot = telegram("getMe")["result"]

    print("✅ Telegram подключён!")
    print(f"🤖 Бот: {bot.get('first_name')}")
    print(f"👤 Username: @{bot.get('username')}")
    print("⏳ Бот работает постоянно...")
    print("================================")

    offset = 0

    while True:
        try:
            result = telegram(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 30
                }
            )

            updates = result.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message")

                if message:
                    handle_message(message)

        except Exception as error:
            print("⚠️ Ошибка:", error)
            time.sleep(5)


if __name__ == "__main__":
    main()
