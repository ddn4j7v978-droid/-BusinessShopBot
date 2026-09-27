import json
from workers import WorkerEntrypoint, Response, fetch
class Default(WorkerEntrypoint):
    async def telegram(self, method, data):
        token = self.env.BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/{method}"
        return await fetch(
            url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(data)
        )
    async def send_message(self, chat_id, text, reply_markup=None):
        data = {
            "chat_id": chat_id,
            "text": text
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        await self.telegram("sendMessage", data)
    async def send_photo(self, chat_id, photo, caption, reply_markup=None):
        data = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        await self.telegram("sendPhoto", data)
    async def fetch(self, request):
        if request.method == "GET":
            return Response("BusinessShopBot is running!")
        if request.method != "POST":
            return Response("Method not allowed", status=405)
        update = await request.json()
        token = self.env.BOT_TOKEN
        # ==========================================
        # ОСНОВНАЯ КЛАВИАТУРА
        # ==========================================
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
        # ==========================================
        # CALLBACK QUERY
        # ==========================================
        if "callback_query" in update:
            callback = update["callback_query"]
            callback_id = callback["id"]
            callback_data = callback.get("data", "")
            callback_message = callback.get("message", {})
            chat = callback_message.get("chat", {})
            chat_id = chat.get("id")
            # Убираем "часики" на кнопке
            await self.telegram(
                "answerCallbackQuery",
                {
                    "callback_query_id": callback_id
                }
            )
            if not chat_id:
                return Response("OK")
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(products_key)
            if products_data:
                products = json.loads(products_data)
            else:
                products = []
            # ======================================
            # УДАЛЕНИЕ
            # ======================================
            if callback_data.startswith("delete:"):
                try:
                    index = int(callback_data.split(":")[1])
                except:
                    return Response("OK")
                if 0 <= index < len(products):
                    deleted = products.pop(index)
                    await self.env.BUSINESS_DATA.put(
                        products_key,
                        json.dumps(products, ensure_ascii=False)
                    )
                    await self.send_message(
                        chat_id,
                        (
                            "🗑 Товар удалён.\n\n"
                            f"Удалён товар: {deleted['name']}"
                        ),
                        keyboard
                    )
            # ======================================
            # РЕДАКТИРОВАНИЕ
            # ======================================
            elif callback_data.startswith("edit:"):
                try:
                    index = int(callback_data.split(":")[1])
                except:
                    return Response("OK")
                if 0 <= index < len(products):
                    state_key = f"state:{chat_id}"
                    state = {
                        "step": "edit_name",
                        "index": index
                    }
                    await self.env.BUSINESS_DATA.put(
                        state_key,
                        json.dumps(state, ensure_ascii=False)
                    )
                    await self.send_message(
                        chat_id,
                        (
                            "✏️ Редактирование товара\n\n"
                            f"Текущие данные:\n"
                            f"🛍 {products[index]['name']}\n"
                            f"💰 {products[index]['price']:g}\n\n"
                            "Введите новое название товара."
                        ),
                        keyboard
                    )
            return Response("OK")
        # ==========================================
        # ОБЫЧНОЕ СООБЩЕНИЕ
        # ==========================================
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if not chat_id:
            return Response("OK")
        text = message.get("text", "")
        # ==========================================
        # СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ
        # ==========================================
        state_key = f"state:{chat_id}"
        state_data = await self.env.BUSINESS_DATA.get(state_key)
        state = None
        if state_data:
            state = json.loads(state_data)
        # ==========================================
        # ДОБАВЛЕНИЕ — НАЗВАНИЕ
        # ==========================================
        if state and state.get("step") == "name":
            state["name"] = text
            state["step"] = "price"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            await self.send_message(
                chat_id,
                (
                    "💰 Шаг 2 из 4\n\n"
                    "Введите цену товара.\n\n"
                    "Например:\n"
                    "150000"
                )
            )
            return Response("OK")
        # ==========================================
        # ДОБАВЛЕНИЕ — ЦЕНА
        # ==========================================
        if state and state.get("step") == "price":
            try:
                price = float(
                    text.replace(" ", "").replace(",", ".")
                )
            except:
                await self.send_message(
                    chat_id,
                    (
                        "❌ Неверная цена.\n\n"
                        "Введите только число.\n"
                        "Например: 150000"
                    )
                )
                return Response("OK")
            state["price"] = price
            state["step"] = "description"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            await self.send_message(
                chat_id,
                (
                    "📝 Шаг 3 из 4\n\n"
                    "Введите описание товара."
                )
            )
            return Response("OK")
        # ==========================================
        # ДОБАВЛЕНИЕ — ОПИСАНИЕ
        # ==========================================
        if state and state.get("step") == "description":
            state["description"] = text
            state["step"] = "photo"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            skip_keyboard = {
                "keyboard": [
                    [
                        {"text": "⏭ Пропустить фото"}
                    ]
                ],
                "resize_keyboard": True
            }
            await self.send_message(
                chat_id,
                (
                    "📷 Шаг 4 из 4\n\n"
                    "Теперь отправьте фотографию товара.\n\n"
                    "Или нажмите «⏭ Пропустить фото»."
                ),
                skip_keyboard
            )
            return Response("OK")
        # ==========================================
        # ДОБАВЛЕНИЕ — ФОТО
        # ==========================================
        if state and state.get("step") == "photo":
            photo = message.get("photo", [])
            if photo:
                state["photo"] = photo[-1]["file_id"]
            elif text == "⏭ Пропустить фото":
                state["photo"] = ""
            else:
                await self.send_message(
                    chat_id,
                    (
                        "📷 Пожалуйста, отправьте фотографию "
                        "или нажмите «⏭ Пропустить фото»."
                    )
                )
                return Response("OK")
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(
                products_key
            )
            if products_data:
                products = json.loads(products_data)
            else:
                products = []
            product = {
                "name": state["name"],
                "price": state["price"],
                "description": state["description"],
                "photo": state.get("photo", "")
            }
            products.append(product)
            await self.env.BUSINESS_DATA.put(
                products_key,
                json.dumps(products, ensure_ascii=False)
            )
            await self.env.BUSINESS_DATA.delete(state_key)
            await self.send_message(
                chat_id,
                (
                    "✅ Товар успешно добавлен!\n\n"
                    f"🛍 {product['name']}\n"
                    f"💰 {product['price']:g}\n"
                    f"📝 {product['description']}"
                ),
                keyboard
            )
            return Response("OK")
        # ==========================================
        # РЕДАКТИРОВАНИЕ — НАЗВАНИЕ
        # ==========================================
        if state and state.get("step") == "edit_name":
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(
                products_key
            )
            products = json.loads(products_data)
            index = state["index"]
            if index >= len(products):
                await self.send_message(
                    chat_id,
                    "❌ Товар не найден.",
                    keyboard
                )
                await self.env.BUSINESS_DATA.delete(state_key)
                return Response("OK")
            state["name"] = text
            state["step"] = "edit_price"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            await self.send_message(
                chat_id,
                "💰 Введите новую цену товара."
            )
            return Response("OK")
        # ==========================================
        # РЕДАКТИРОВАНИЕ — ЦЕНА
        # ==========================================
        if state and state.get("step") == "edit_price":
            try:
                price = float(
                    text.replace(" ", "").replace(",", ".")
                )
            except:
                await self.send_message(
                    chat_id,
                    "❌ Введите цену числом. Например: 150000"
                )
                return Response("OK")
            state["price"] = price
            state["step"] = "edit_description"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            await self.send_message(
                chat_id,
                "📝 Введите новое описание товара."
            )
            return Response("OK")
        # ==========================================
        # РЕДАКТИРОВАНИЕ — ОПИСАНИЕ
        # ==========================================
        if state and state.get("step") == "edit_description":
            state["description"] = text
            state["step"] = "edit_photo"
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            skip_keyboard = {
                "keyboard": [
                    [
                        {"text": "⏭ Оставить старое фото"}
                    ]
                ],
                "resize_keyboard": True
            }
            await self.send_message(
                chat_id,
                (
                    "📷 Отправьте новое фото товара.\n\n"
                    "Или нажмите «⏭ Оставить старое фото»."
                ),
                skip_keyboard
            )
            return Response("OK")
        # ==========================================
        # РЕДАКТИРОВАНИЕ — ФОТО
        # ==========================================
        if state and state.get("step") == "edit_photo":
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(
                products_key
            )
            products = json.loads(products_data)
            index = state["index"]
            if index >= len(products):
                await self.send_message(
                    chat_id,
                    "❌ Товар не найден.",
                    keyboard
                )
                await self.env.BUSINESS_DATA.delete(state_key)
                return Response("OK")
            photo = message.get("photo", [])
            if photo:
                products[index]["photo"] = photo[-1]["file_id"]
            elif text == "⏭ Оставить старое фото":
                pass
            else:
                await self.send_message(
                    chat_id,
                    (
                        "📷 Отправьте новое фото "
                        "или нажмите «⏭ Оставить старое фото»."
                    )
                )
                return Response("OK")
            products[index]["name"] = state["name"]
            products[index]["price"] = state["price"]
            products[index]["description"] = state["description"]
            await self.env.BUSINESS_DATA.put(
                products_key,
                json.dumps(products, ensure_ascii=False)
            )
            await self.env.BUSINESS_DATA.delete(state_key)
            await self.send_message(
                chat_id,
                "✅ Товар успешно изменён!",
                keyboard
            )
            return Response("OK")
        # ==========================================
        # /START
        # ==========================================
        if text == "/myid":

            await self.send_message(
                chat_id,
                f"🆔 Ваш Telegram ID:\n\n{chat_id}",
                keyboard
            )

            return Response("OK")
        if text == "/start":
            await self.send_message(
                chat_id,
                (
                    "🏪 Business в Telegram\n\n"
                    "Добро пожаловать!\n\n"
                    "Управляйте своим бизнесом прямо "
                    "из Telegram.\n\n"
                    "Выберите нужный раздел:"
                ),
                keyboard
            )
            return Response("OK")
        # ==========================================
        # ДОБАВИТЬ ТОВАР
        # ==========================================
        if text == "➕ Добавить товар":
            state = {
                "step": "name"
            }
            await self.env.BUSINESS_DATA.put(
                state_key,
                json.dumps(state, ensure_ascii=False)
            )
            await self.send_message(
                chat_id,
                (
                    "➕ Добавление товара\n\n"
                    "Шаг 1 из 4\n\n"
                    "Введите название товара."
                ),
                keyboard
            )
            return Response("OK")
        # ==========================================
        # КАТАЛОГ
        # ==========================================
        if text == "🛍 Каталог":
            products_key = f"products:{chat_id}"
            products_data = await self.env.BUSINESS_DATA.get(
                products_key
            )
            if not products_data:
                await self.send_message(
                    chat_id,
                    (
                        "🛍 Каталог пока пуст.\n\n"
                        "Нажмите «➕ Добавить товар»."
                    ),
                    keyboard
                )
                return Response("OK")
            products = json.loads(products_data)
            for index, product in enumerate(products):
                caption = (
                    f"🛍 {product['name']}\n\n"
                    f"💰 Цена: {product['price']:g}\n"
                    f"📝 {product['description']}"
                )
                buttons = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "✏️ Изменить",
                                "callback_data": f"edit:{index}"
                            },
                            {
                                "text": "🗑 Удалить",
                                "callback_data": f"delete:{index}"
                            }
                        ]
                    ]
                }
                if product.get("photo"):
                    await self.send_photo(
                        chat_id,
                        product["photo"],
                        caption,
                        buttons
                    )
                else:
                    await self.send_message(
                        chat_id,
                        caption,
                        buttons
                    )
            await self.send_message(
                chat_id,
                "🏠 Главное меню",
                keyboard
            )
            return Response("OK")
        # ==========================================
        # ОСТАЛЬНЫЕ РАЗДЕЛЫ
        # ==========================================
        if text == "🏪 Мой бизнес":
            await self.send_message(
                chat_id,
                (
                    "🏪 Мой бизнес\n\n"
                    "Здесь будет информация о вашем бизнесе."
                ),
                keyboard
            )
            return Response("OK")
        if text == "📦 Заказы":
            await self.send_message(
                chat_id,
                (
                    "📦 Заказы\n\n"
                    "Здесь будут отображаться заказы клиентов."
                ),
                keyboard
            )
            return Response("OK")
        if text == "📊 Статистика":
            await self.send_message(
                chat_id,
                (
                    "📊 Статистика\n\n"
                    "Статистика продаж появится здесь."
                ),
                keyboard
            )
            return Response("OK")
        if text == "⚙️ Настройки":
            await self.send_message(
                chat_id,
                (
                    "⚙️ Настройки\n\n"
                    "Настройки бота будут здесь."
                ),
                keyboard
            )
            return Response("OK")
        await self.send_message(
            chat_id,
            "Выберите раздел с помощью кнопок ниже 👇",
            keyboard
        )
        return Response("OK")
