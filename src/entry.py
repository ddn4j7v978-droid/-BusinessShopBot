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
        telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
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
        # Получаем состояние пользователя
        state_key = f"state:{chat_id}"
        state_data = await self.env.BUSINESS_DATA.get(state_key)
        state = None
        if state_data:
            state = json.loads(state_data)
        answer = ""
        reply_markup = keyboard
        # =========================
        # ДОБАВЛЕНИЕ ТОВАРА
        # =========================
        if state and state.get("step") == "name":
            state["name"] = text
            state["step"] = "price"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            answer = (
                "💰 Отлично!\n\n"
                "Теперь отправьте цену товара.\n\n"
                "Например:\n"
                "150000"
            )
        elif state and state.get("step") == "price":
            try:
                price = float(text.replace(" ", "").replace(",", "."))
            except ValueError:
                answer = (
                    "❌ Не удалось распознать цену.\n\n"
                    "Введите только число.\n"
                    "Например: 150000"
                )
            else:
                state["price"] = price
                state["step"] = "description"
                await self.env.BUSINESS_DATA.put(
                    state_key,
                    json.dumps(state, ensure_ascii=False)
                )
                answer = (
                    "📝 Теперь отправьте описание товара.\n\n"
                    "Например:\n"
                    "Хлопковая футболка, размеры S–XL."
                )
        elif state and state.get("step") == "description":
            state["description"] = text
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(products_key)
            if products_data:
                products = json.loads(products_data)
            else:
                products = []
            product = {
                "name": state["name"],
                "price": state["price"],
                "description": state["description"]
            }
            products.append(product)
            await self.env.BUSINESS_DATA.put(
                products_key,
                json.dumps(products, ensure_ascii=False)
            )
            await self.env.BUSINESS_DATA.delete(state_key)
            answer = (
                "✅ Товар добавлен!\n\n"
                f"🛍 {product['name']}\n"
                f"💰 Цена: {product['price']:g}\n"
                f"📝 {product['description']}\n\n"
                "Товар сохранён в каталоге."
            )
        # =========================
        # ГЛАВНОЕ МЕНЮ
        # =========================
        elif text == "/start":
            answer = (
                "🏪 Business в Telegram\n\n"
                "Добро пожаловать!\n\n"
                "Управляйте своим бизнесом прямо из Telegram.\n\n"
                "Выберите нужный раздел:"
            )
        # =========================
        # КАТАЛОГ
        # =========================
        elif text == "🛍 Каталог":
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(products_key)
            if not products_data:
                answer = (
                    "🛍 Каталог\n\n"
                    "Каталог пока пуст.\n\n"
                    "Нажмите «➕ Добавить товар», "
                    "чтобы добавить первый товар."
                )
            else:
                products = json.loads(products_data)
                lines = ["🛍 Ваш каталог\n"]
                for i, product in enumerate(products, 1):
                    lines.append(
                        f"{i}. {product['name']}\n"
                        f"💰 {product['price']:g}\n"
                        f"📝 {product['description']}\n"
                    )
                answer = "\n".join(lines)
        # =========================
        # ДОБАВИТЬ ТОВАР
        # =========================
        elif text == "➕ Добавить товар":
            state = {
                "step": "name"
            }
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            answer = (
                "➕ Добавление товара\n\n"
                "Шаг 1 из 3\n\n"
                "Введите название товара."
            )
        # =========================
        # ОСТАЛЬНЫЕ РАЗДЕЛЫ
        # =========================
        elif text == "🏪 Мой бизнес":
            answer = (
                "🏪 Мой бизнес\n\n"
                "Здесь будет информация о вашем бизнесе."
            )
        elif text == "📦 Заказы":
            answer = (
                "📦 Заказы\n\n"
                "Здесь будут отображаться заказы клиентов."
            )
        elif text == "📊 Статистика":
            answer = (
                "📊 Статистика\n\n"
                "Статистика продаж появится здесь."
            )
        elif text == "⚙️ Настройки":
            answer = (
                "⚙️ Настройки\n\n"
                "Настройки бота будут здесь."
            )
        else:
            answer = (
                "Выберите раздел с помощью кнопок ниже 👇"
            )
        data = {
            "chat_id": chat_id,
            "text": answer,
            "reply_markup": reply_markup
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
