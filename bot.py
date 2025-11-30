import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
import os

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
ADMIN_CHANNEL = -1003371815477

PRICE_MAIN = 300
PRICE_EXTRA = 50

TITLE_MAIN = "Все Локации"
TITLE_EXTRA = "Дополнительный актив"

BUYERS_FILE = "buyers.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


# ---------------- JSON STORAGE ----------------
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


# ---------------- KEYBOARD ----------------
def kb_menu(uid: int):
    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            f"Купить «{TITLE_MAIN}» за {PRICE_MAIN}⭐",
            callback_data="buy_main"
        )
    )

    if user_has_main(uid):
        kb.add(
            InlineKeyboardButton(
                f"Купить «{TITLE_EXTRA}» за {PRICE_EXTRA}⭐",
                callback_data="buy_extra"
            )
        )

    return kb


# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("Меню покупок:", reply_markup=kb_menu(msg.from_user.id))


# ---------------- BUY MAIN ----------------
@dp.callback_query_handler(lambda c: c.data == "buy_main")
async def buy_main(call: types.CallbackQuery):
    prices = [LabeledPrice(label=TITLE_MAIN, amount=PRICE_MAIN)]
    await bot.send_invoice(
        call.from_user.id,
        title=TITLE_MAIN,
        description="Покупка основного товара",
        payload="main",
        provider_token="",  # пусто для Stars
        currency="XTR",
        prices=prices
    )
    await call.answer()


# ---------------- BUY EXTRA ----------------
@dp.callback_query_handler(lambda c: c.data == "buy_extra")
async def buy_extra(call: types.CallbackQuery):
    if not user_has_main(call.from_user.id):
        await call.answer("Сначала купите товар за 300⭐", show_alert=True)
        return

    prices = [LabeledPrice(label=TITLE_EXTRA, amount=PRICE_EXTRA)]
    await bot.send_invoice(
        call.from_user.id,
        title=TITLE_EXTRA,
        description="Покупка дополнительного товара",
        payload="extra",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await call.answer()


# ---------------- PAYMENT CHECKOUT ----------------
@dp.pre_checkout_query_handler(lambda q: True)
async def checkout(pre: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre.id, ok=True)


# ---------------- SUCCESSFUL PAYMENT ----------------
@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def paid(msg: types.Message):
    uid = msg.from_user.id
    payload = msg.successful_payment.invoice_payload

    # MAIN ITEM
    if payload == "main":
        add_buyer(uid)

        txt_user = f"Активировано: {TITLE_MAIN}"
        txt_admin = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{msg.from_user.username or 'нет'}\n"
            f"ID: {uid}\n"
            f"Товар: {TITLE_MAIN}\n"
            f"Оплата: {PRICE_MAIN}⭐"
        )

    # EXTRA ITEM
    elif payload == "extra":
        txt_user = f"Активировано: {TITLE_EXTRA}"
        txt_admin = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{msg.from_user.username or 'нет'}\n"
            f"ID: {uid}\n"
            f"Товар: {TITLE_EXTRA}\n"
            f"Оплата: {PRICE_EXTRA}⭐"
        )

    else:
        return

    await msg.answer(txt_user)
    await bot.send_message(ADMIN_CHANNEL, txt_admin)
    await msg.answer("Меню обновлено:", reply_markup=kb_menu(uid))


# ---------------- RUN ----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
