import os
import json
import time
import threading
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ Ошибка: BOT_TOKEN не задан")
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
        data["reply_markup"] = json.dumps(
            keyboard,
            ensure_ascii=False
        )

    telegram("sendMessage", data)


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
            "Здесь будет пошаговая регистрация бизнеса."
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
            "Контактные данные пока не заполнены."
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
            "Используйте «➕ Добавить товар»."
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
            "Здесь сделаем форму добавления товара."
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
            "Настройки уведомлений пока в разработке."
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


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BusinessShopBot is running")

    def log_message(self, format, *args):
        return


def start_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"🌐 HTTP сервер запущен на порту {port}")
    server.serve_forever()


def bot_loop():
    print("🤖 Telegram бот запускается...")

    bot = telegram("getMe")["result"]

    print("✅ Telegram подключён!")
    print(f"🤖 Бот: {bot.get('first_name')}")
    print(f"👤 Username: @{bot.get('username')}")
    print("⏳ Бот работает...")

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

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if message:
                    handle_message(message)

        except Exception as error:
            print("⚠️ Ошибка:", error)
            time.sleep(5)


if __name__ == "__main__":

    print("================================")
    print("🚀 BusinessShopBot запускается")
    print("================================")

    threading.Thread(
        target=start_server,
        daemon=True
    ).start()

    bot_loop()
