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

        if text == "/start":
            answer = (
                "🏪 Business в Telegram\n\n"
                "Добро пожаловать!\n\n"
                "Здесь мы создадим управление вашим бизнесом.\n\n"
                "Выберите нужный раздел:"
            )
        else:
            answer = f"Вы написали: {text}"

        token = self.env.BOT_TOKEN

        telegram_url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        data = {
            "chat_id": chat_id,
            "text": answer
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
