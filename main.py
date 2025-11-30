import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    PreCheckoutQuery,
    LabeledPrice,
)
from aiogram.filters import Command
import os

TOKEN = os.getenv("TOKEN")
ADMIN_CHANNEL = -1003371815477

PRICE_MAIN = 300
PRICE_EXTRA = 50

TITLE_MAIN = "Все Локации"
TITLE_EXTRA = "Дополнительный актив"

BUYERS_FILE = "buyers.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------- JSON STORAGE ----------
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


def add_main_buyer(uid: int):
    buyers = load_buyers()
    if uid not in buyers:
        buyers.append(uid)
        save_buyers(buyers)


# ---------- KEYBOARD ----------
def kb_menu(user_id: int):
    btns = [
        [InlineKeyboardButton(
            text=f"Купить «{TITLE_MAIN}» за {PRICE_MAIN}⭐",
            callback_data="buy_main"
        )]
    ]

    if user_has_main(user_id):
        btns.append([
            InlineKeyboardButton(
                text=f"Купить «{TITLE_EXTRA}» за {PRICE_EXTRA}⭐",
                callback_data="buy_extra"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=btns)


# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Меню покупок:", reply_markup=kb_menu(msg.from_user.id))


# ---------- BUY MAIN ----------
@dp.callback_query(F.data == "buy_main")
async def cb_main(call):
    prices = [LabeledPrice(label=TITLE_MAIN, amount=PRICE_MAIN)]
    await bot.send_invoice(
        call.from_user.id,
        title=TITLE_MAIN,
        description="Основной товар",
        currency="XTR",
        prices=prices,
        payload="main_buy",
    )
    await call.answer()


# ---------- BUY EXTRA ----------
@dp.callback_query(F.data == "buy_extra")
async def cb_extra(call):
    if not user_has_main(call.from_user.id):
        await call.answer("Сначала купите товар за 300⭐", show_alert=True)
        return

    prices = [LabeledPrice(label=TITLE_EXTRA, amount=PRICE_EXTRA)]
    await bot.send_invoice(
        call.from_user.id,
        title=TITLE_EXTRA,
        description="Дополнительный товар",
        currency="XTR",
        prices=prices,
        payload="extra_buy",
    )
    await call.answer()


# ---------- PAYMENT ----------
@dp.pre_checkout_query()
async def pre(pre: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre.id, ok=True)


@dp.message(F.successful_payment)
async def paid(msg: Message):
    uid = msg.from_user.id
    payload = msg.successful_payment.invoice_payload

    # MAIN
    if payload == "main_buy":
        add_main_buyer(uid)
        txt_user = f"Активировано: {TITLE_MAIN}"
        txt_admin = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{msg.from_user.username or 'нет'}\n"
            f"ID: {uid}\n"
            f"Товар: {TITLE_MAIN}\n"
            f"Оплата: {PRICE_MAIN}⭐"
        )

    # EXTRA
    elif payload == "extra_buy":
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


# ---------- RUN ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
