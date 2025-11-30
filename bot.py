import json
import time
import requests
from flask import Flask, request

TOKEN = "YOUR_TOKEN"
ADMIN_CHANNEL = -1003371815477

URL = f"https://api.telegram.org/bot{TOKEN}"
BOT_ID = TOKEN.split(":")[0]

PRICE_MAIN = 300
PRICE_EXTRA = 50

TITLE_MAIN = "Все Локации"
TITLE_EXTRA = "Дополнительный актив"

BUYERS_FILE = "buyers.json"

app = Flask(__name__)


# ---------------- JSON UTILS ----------------
def load_buyers():
    try:
        with open(BUYERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_buyers(data):
    with open(BUYERS_FILE, "w") as f:
        json.dump(data, f)


def user_has_main(uid: int):
    return uid in load_buyers()


def add_buyer(uid: int):
    buyers = load_buyers()
    if uid not in buyers:
        buyers.append(uid)
        save_buyers(buyers)


# ---------------- TELEGRAM UTILS ----------------
def send_msg(chat_id, text, kb=None):
    data = {"chat_id": chat_id, "text": text}

    if kb:
        data["reply_markup"] = kb

    requests.post(f"{URL}/sendMessage", json=data)


def send_invoice(chat_id, title, price, payload):
    invoice = {
        "chat_id": chat_id,
        "title": title,
        "description": title,
        "payload": payload,
        "provider_token": "",  # Stars → пусто
        "currency": "XTR",
        "prices": [{"label": title, "amount": price}],
    }

    requests.post(f"{URL}/sendInvoice", json=invoice)


# ---------------- KEYBOARD ----------------
def menu_kb(uid):
    kb = {"inline_keyboard": []}

    kb["inline_keyboard"].append([
        {"text": f"Купить «{TITLE_MAIN}» за {PRICE_MAIN}⭐", "callback_data": "buy_main"}
    ])

    if user_has_main(uid):
        kb["inline_keyboard"].append([
            {"text": f"Купить «{TITLE_EXTRA}» за {PRICE_EXTRA}⭐", "callback_data": "buy_extra"}
        ])

    return kb


# ---------------- LOGIC ----------------
def handle_callback(uid, callback_id, data):
    if data == "buy_main":
        send_invoice(uid, TITLE_MAIN, PRICE_MAIN, "main")
    elif data == "buy_extra":
        if not user_has_main(uid):
            answer_cb(callback_id, "Сначала купите товар за 300⭐", alert=True)
            return
        send_invoice(uid, TITLE_EXTRA, PRICE_EXTRA, "extra")

    answer_cb(callback_id)


def answer_cb(callback_id, text="", alert=False):
    requests.post(
        f"{URL}/answerCallbackQuery",
        json={"callback_query_id": callback_id, "text": text, "show_alert": alert},
    )


def handle_payment(msg):
    uid = msg["from"]["id"]
    payload = msg["successful_payment"]["invoice_payload"]

    if payload == "main":
        add_buyer(uid)
        user_msg = f"Активировано: {TITLE_MAIN}"
        admin_msg = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{msg['from'].get('username','нет')}\n"
            f"ID: {uid}\n"
            f"Товар: {TITLE_MAIN}\n"
            f"Оплата: {PRICE_MAIN}⭐"
        )
    else:
        user_msg = f"Активировано: {TITLE_EXTRA}"
        admin_msg = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{msg['from'].get('username','нет')}\n"
            f"ID: {uid}\n"
            f"Товар: {TITLE_EXTRA}\n"
            f"Оплата: {PRICE_EXTRA}⭐"
        )

    send_msg(uid, user_msg)
    send_msg(ADMIN_CHANNEL, admin_msg)
    send_msg(uid, "Меню обновлено:", kb=menu_kb(uid))


# ---------------- POLLING ----------------
offset = 0


def poll():
    global offset

    while True:
        r = requests.get(f"{URL}/getUpdates", params={"timeout": 50, "offset": offset})
        res = r.json()

        if not res.get("ok"):
            time.sleep(1)
            continue

        for upd in res["result"]:
            offset = upd["update_id"] + 1

            # START
            if "message" in upd and upd["message"].get("text") == "/start":
                uid = upd["message"]["from"]["id"]
                send_msg(uid, "Меню покупок:", kb=menu_kb(uid))

            # CALLBACK
            if "callback_query" in upd:
                cb = upd["callback_query"]
                handle_callback(cb["from"]["id"], cb["id"], cb["data"])

            # PAYMENT
            if "message" in upd and "successful_payment" in upd["message"]:
                handle_payment(upd["message"])

        time.sleep(1)


# ---------------- FLASK ENTRY ----------------
@app.route("/")
def hello():
    return "Bot is running"


if __name__ == "__main__":
    poll()
