"""
Bilingual (RU / UZ) Telegram Bot for Tashkent Pharmacy Search & Smart Multi-Branch Delivery.
Run with: BOT_TOKEN=<your_token> python bot.py
"""
import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import database

USER_LANG = {}
USER_CART = {}

TEXTS = {
    "ru": {
        "welcome": (
            "💊 <b>Добро пожаловать в поиск и доставку лекарств по Ташкенту!</b>\n\n"
            "• Напишите название лекарства (например: <code>Нурофен</code>, <code>Магне</code>, <code>ТераФлю</code>)\n"
            "• Бот проверит наличие по филиалам (Тузель-2, Кадышева, Буюк Ипак Йули, Чиланзар) и соберёт оптимальную корзину."
        ),
        "not_found": "❌ Препарат не найден. Попробуйте ввести часть названия (например: Нурофен).",
        "added": "✅ Добавлено в корзину! Отправьте ещё название или нажмите /cart для расчёта доставки.",
    },
    "uz": {
        "welcome": (
            "💊 <b>Toshkent bo'ylab dori qidirish va yetkazib berish botiga xush kelibsiz!</b>\n\n"
            "• Dori nomini yozing (masalan: <code>Nurofen</code>, <code>Magne</code>, <code>TeraFlyu</code>)\n"
            "• Bot filiallar (Tuzel-2, Kadisheva, Buyuk Ipak Yo'li, Chilonzor) bo'yicha qoldiqni tekshiradi."
        ),
        "not_found": "❌ Dori topilmadi. Nomini qisqaroq yozib ko'ring (masalan: Nurofen).",
        "added": "✅ Savatchaga qo'shildi! Yana dori yozing yoki yetkazib berishni hisoblash uchun /cart bosing.",
    },
}

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    database.init_db()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="lang:uz"),
            ]
        ]
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=kb)


@dp.callback_query(F.data.startswith("lang:"))
async def cb_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    USER_LANG[call.from_user.id] = lang
    await call.message.edit_text(TEXTS[lang]["welcome"], parse_mode="HTML")


@dp.message(Command("cart"))
async def cmd_cart(message: Message):
    skus = USER_CART.get(message.from_user.id, [])
    if not skus:
        await message.answer("🛒 Корзина пуста / Savatcha bo'sh.")
        return
    plan = database.optimize_cart(skus)["FulfillmentPlan"]
    if plan["mode"] == "single_branch":
        items_str = "\n".join(f"• {i['title_ru']} — {i['price_uzs']:,} UZS" for i in plan["items"])
        text = (
            f"✅ <b>Все препараты есть в ОДНОМ ближайшем филиале:</b>\n"
            f"📍 <b>{plan['branch']}</b> ({plan['distance_km']} км)\n\n"
            f"{items_str}\n\n"
            f"💊 Сумма лекарств: {plan['subtotal_uzs']:,} UZS\n"
            f"🛵 Доставка (1 филиал): {plan['delivery_fee_uzs']:,} UZS\n"
            f"💰 <b>Итого: {plan['total_uzs']:,} UZS</b>"
        )
    else:
        parts = []
        for alloc in plan["allocations"]:
            its = ", ".join(i["title_ru"] for i in alloc["items"])
            parts.append(f"📍 <b>{alloc['branch']}</b> ({alloc['distance_km']} км): {its}")
        text = (
            f"⚠️ <b>Препараты находятся в разных филиалах (Сплит-заказ):</b>\n\n"
            + "\n".join(parts)
            + f"\n\n💊 Сумма лекарств: {plan['subtotal_uzs']:,} UZS\n"
            f"🛵 Доставка с заездом в 2 филиала: {plan['delivery_fee_uzs']:,} UZS\n"
            f"💰 <b>Итого: {plan['total_uzs']:,} UZS</b>"
        )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text)
async def handle_search(message: Message):
    lang = USER_LANG.get(message.from_user.id, "ru")
    rows = database.search_medicines(message.text)
    if not rows:
        await message.answer(TEXTS[lang]["not_found"])
        return
    kb_rows = []
    seen = set()
    lines = []
    for r in rows[:6]:
        title = r["title_ru"] if lang == "ru" else r["title_uz"]
        lines.append(f"• <b>{title}</b>\n  📍 {r['branch_name']} — <b>{r['price_uzs']:,} UZS</b> ({r['stock_qty']} шт.)")
        if r["sku"] not in seen:
            seen.add(r["sku"])
            kb_rows.append([InlineKeyboardButton(text=f"➕ В корзину: {title[:28]}", callback_data=f"add:{r['sku']}")])
    await message.answer("\n\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@dp.callback_query(F.data.startswith("add:"))
async def cb_add(call: CallbackQuery):
    sku = call.data.split(":")[1]
    USER_CART.setdefault(call.from_user.id, []).append(sku)
    lang = USER_LANG.get(call.from_user.id, "ru")
    await call.answer(TEXTS[lang]["added"], show_alert=True)


async def main():
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Set BOT_TOKEN environment variable to run the Telegram bot.")
    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
