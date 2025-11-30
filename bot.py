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

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_CHANNEL = -1003371815477

PRICE_MAIN = 300
PRICE_EXTRA = 50

TITLE_MAIN = "Все локации"
TITLE_EXTRA = "Доп. актив"

DESC_MAIN = "Основной товар за 300⭐"
DESC_EXTRA = "Дополнительный товар за 50⭐"

BUYERS_FILE = "buyers.json"


# ---------------- UTILS ----------------
def load_buyers() -> dict:
    try:
        with open(BUYERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_buyers(data: dict):
    with open(BUYERS_FILE, "w") as f:
        json.dump(data, f)


def user_has_main(user_id: int) -> bool:
    buyers = load_buyers()
    return str(user_id) in buyers


def add_main_buyer(user_id: int):
    buyers = load_buyers()
    buyers[str(user_id)] = True
    save_buyers(buyers)


# ---------------- KEYBOARD ----------------
def main_keyboard(user_id: int):
    buttons = [
        [InlineKeyboardButton(
            text=f"Купить «{TITLE_MAIN}» — {PRICE_MAIN}⭐",
            callback_data="buy_main"
        )]
    ]

    if user_has_main(user_id):
        buttons.append([
            InlineKeyboardButton(
                text=f"Купить «{TITLE_EXTRA}» — {PRICE_EXTRA}⭐",
                callback_data="buy_extra"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------------- AIOGRAM SETUP ----------------
bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------------- HANDLERS ----------------
@dp.message(Command("start"))
async def start_handler(msg: Message):
    kb = main_keyboard(msg.from_user.id)
    await msg.answer("Меню:", reply_markup=kb)


@dp.callback_query(F.data == "buy_main")
async def buy_main(callback):
    user_id = callback.from_user.id

    prices = [LabeledPrice(label=TITLE_MAIN, amount=PRICE_MAIN)]

    await bot.send_invoice(
        chat_id=user_id,
        title=TITLE_MAIN,
        description=DESC_MAIN,
        currency="XTR",
        prices=prices,
        payload="main"
    )

    await callback.answer()


@dp.callback_query(F.data == "buy_extra")
async def buy_extra(callback):
    user_id = callback.from_user.id

    if not user_has_main(user_id):
        await callback.answer("Сначала купите Все Локации за 300⭐", show_alert=True)
        return

    prices = [LabeledPrice(label=TITLE_EXTRA, amount=PRICE_EXTRA)]

    await bot.send_invoice(
        chat_id=user_id,
        title=TITLE_EXTRA,
        description=DESC_EXTRA,
        currency="XTR",
        prices=prices,
        payload="extra"
    )

    await callback.answer()


# ---------------- PAYMENT ----------------
@dp.pre_checkout_query()
async def checkout(pre: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(msg: Message):
    user = msg.from_user
    payload = msg.successful_payment.invoice_payload

    if payload == "main":
        add_main_buyer(user.id)
        text_user = "Вы купили Все Локации!"
        text_admin = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{user.username or 'нет username'}\n"
            f"ID: {user.id}\n"
            f"Товар: Все Локации\n"
            f"Оплата: {PRICE_MAIN}⭐"
        )

    elif payload == "extra":
        text_user = "Вы купили Доп. товар!"
        text_admin = (
            f"📩 Новый заказ!\n"
            f"Покупатель: @{user.username or 'нет username'}\n"
            f"ID: {user.id}\n"
            f"Товар: Доп. актив\n"
            f"Оплата: {PRICE_EXTRA}⭐"
        )

    else:
        return

    await msg.answer(text_user)
    await bot.send_message(ADMIN_CHANNEL, text_admin)

    # обновить меню
    await msg.answer("Меню:", reply_markup=main_keyboard(user.id))


# ---------------- START ----------------
async def main():
    print("Bot started.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
