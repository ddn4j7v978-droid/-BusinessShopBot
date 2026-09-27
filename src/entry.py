import json

from workers import WorkerEntrypoint, Response, fetch


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        if request.method == "GET":
            return Response("BusinessShopBot is running!")

        if request.method != "POST":
            return Response("Method not allowed", status=405)

        update = await request.json()

        message = update.get("message", {})
        chat = message.get("chat", {})
        text = message.get("text", "")

        chat_id = chat.get("id")

        if not chat_id:
            return Response("OK")

        token = self.env.BOT_TOKEN

        telegram_url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🏪 Мой бизнес"},
                    {"text": "🛍 Каталог"}
                ],
                [
                    {"text": "📦 Заказы"},
                    {"text": "➕ Добавить товар"}
                ],
                [
                    {"text": "📊 Статистика"},
                    {"text": "⚙️ Настройки"}
                ]
            ],
            "resize_keyboard": True
        }

        if text == "/start":
            answer = (
                "🏪 Business в Telegram\n\n"
                "Добро пожаловать!\n\n"
                "Управляйте своим бизнесом прямо из Telegram.\n\n"
                "Выберите нужный раздел:"
            )

            data = {
                "chat_id": chat_id,
                "text": answer,
                "reply_markup": keyboard
            }

        elif text == "🏪 Мой бизнес":
            data = {
                "chat_id": chat_id,
                "text": (
                    "🏪 Мой бизнес\n\n"
                    "Здесь будет информация о вашем бизнесе."
                ),
                "reply_markup": keyboard
            }

        elif text == "🛍 Каталог":
            data = {
                "chat_id": chat_id,
                "text": (
                    "🛍 Каталог\n\n"
                    "Здесь будут ваши товары и услуги."
                ),
                "reply_markup": keyboard
            }

        elif text == "📦 Заказы":
            data = {
                "chat_id": chat_id,
                "text": (
                    "📦 Заказы\n\n"
                    "Здесь будут отображаться заказы клиентов."
                ),
                "reply_markup": keyboard
            }

        elif text == "➕ Добавить товар":
            data = {
                "chat_id": chat_id,
                "text": (
                    "➕ Добавить товар\n\n"
                    "Скоро здесь появится форма добавления товара."
                ),
                "reply_markup": keyboard
            }

        elif text == "📊 Статистика":
            data = {
                "chat_id": chat_id,
                "text": (
                    "📊 Статистика\n\n"
                    "Статистика продаж появится здесь."
                ),
                "reply_markup": keyboard
            }

        elif text == "⚙️ Настройки":
            data = {
                "chat_id": chat_id,
                "text": (
                    "⚙️ Настройки\n\n"
                    "Настройки бота будут здесь."
                ),
                "reply_markup": keyboard
            }

        else:
            data = {
                "chat_id": chat_id,
                "text": (
                    "Выберите раздел с помощью кнопок ниже 👇"
                ),
                "reply_markup": keyboard
            }

        await fetch(
            telegram_url,
            method="POST",
            headers={
                "Content-Type": "application/json"
            },
            body=json.dumps(data)
        )

        return Response("OK")
