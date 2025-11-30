import os
import json
import requests
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-render-url.onrender.com/webhook
ADMIN_CHANNEL = -1003371815477

BOT_API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

BUYERS_FILE = "buyers.json"


# ---------------- JSON UTILS ----------------

def load_buyers():
    if not os.path.exists(BUYERS_FILE):
        return {}
    try:
        with open(BUYERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_buyers(data):
    with open(BUYERS_FILE, "w") as f:
        json.dump(data, f)


# ---------------- TELEGRAM UTILS ----------------

def tg(method, data=None):
    return requests.post(f"{BOT_API}/{method}", json=data)


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    tg("sendMessage", payload)


def notify_admin(user, item, price):
    text = (
        f"📩 Новый заказ!\n"
        f"Покупатель: @{user.get('username', 'нет юзернейма')}\n"
        f"ID: {user['id']}\n"
        f"Товар: {item}\n"
        f"Оплата: {price}⭐"
    )
    send_message(ADMIN_CHANNEL, text)


# ---------------- BUTTON MENUS ----------------

def main_menu(user_id):
    buyers = load_buyers()
    bought_main = str(user_id) in buyers

    buttons = [
        [{"text": "Купить Все Локации — 300⭐", "callback_data": "buy_300"}]
    ]

    if bought_main:
        buttons.append([{"text": "Купить Доп. товар — 50⭐", "callback_data": "buy_50"}])

    return {"inline_keyboard": buttons}


# ---------------- WEBHOOK HANDLER ----------------

@app.route("/", methods=["GET"])
def root():
    return "Bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json

    # ---------------- MESSAGE ----------------
    if "message" in update:
        msg = update["message"]
        user = msg["from"]
        chat_id = msg["chat"]["id"]

        send_message(chat_id, "Меню:", reply_markup=main_menu(user["id"]))
        return "ok"

    # ---------------- CALLBACK ----------------
    if "callback_query" in update:
        query = update["callback_query"]
        data = query["data"]
        user = query["from"]
        chat_id = query["message"]["chat"]["id"]
        user_id = str(user["id"])

        buyers = load_buyers()

        # Покупка за 300
        if data == "buy_300":
            if user_id not in buyers:
                buyers[user_id] = {"main": True}
                save_buyers(buyers)
                notify_admin(user, "Все Локации", 300)

            send_message(chat_id, "Вы купили Все Локации!", reply_markup=main_menu(user_id))

        # Покупка за 50
        elif data == "buy_50":
            if user_id not in buyers:
                send_message(chat_id, "Сначала купите основной товар за 300⭐")
                return "ok"

            notify_admin(user, "Дополнительный товар", 50)
            send_message(chat_id, "Вы купили Доп. товар!", reply_markup=main_menu(user_id))

        return "ok"

    return "ok"


# ---------------- WEBHOOK SETUP ----------------

def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"
    tg("setWebhook", {"url": url})
    print("Webhook установлен:", url)


if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
