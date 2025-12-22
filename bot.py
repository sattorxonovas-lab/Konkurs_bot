import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- SOZLAMALAR ---
API_TOKEN = "8508417027:AAG0Qt2NV5yFRd-io6mq123ZluTXbgS8l6U"
ADMIN_ID = 6224785199
CHANNEL_ID = "@Abu_pubg_07"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- DATABASE ---
conn = sqlite3.connect('contest.db', check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

class ContestStates(StatesGroup):
    setup = State()
    broadcast = State()

@dp.message_handler(commands=['konkurs'], user_id=ADMIN_ID, state="*")
async def start_konkurs(message: types.Message):
    await message.answer("📝 Format: `Matn | Soni | Stars`", parse_mode="Markdown")
    await ContestStates.setup.set()

@dp.message_handler(state=ContestStates.setup, user_id=ADMIN_ID)
async def finish_setup(message: types.Message, state: FSMContext):
    try:
        text, slots, price = message.text.split("|")
        cur.execute("INSERT OR REPLACE INTO config VALUES ('text', ?), ('slots', ?), ('price', ?), ('active', '1')", (text.strip(), slots.strip(), price.strip()))
        cur.execute("DELETE FROM participants")
        conn.commit()
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Tasdiqlash va Kanalga ✅", callback_data="push_channel"))
        await message.answer(f"✅ Tayyor!\nSoni: {slots}\nNarxi: {price} Stars", reply_markup=kb)
    except:
        await message.answer("❌ Xato! Qaytadan urinib ko'ring.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'push_channel', user_id=ADMIN_ID, state="*")
async def push_channel(call: types.CallbackQuery):
    cur.execute("SELECT value FROM config WHERE key='text'")
    txt = cur.fetchone()[0]
    bot_me = await bot.get_me()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Qatnashish 0", url=f"https://t.me/{bot_me.username}?start=join"))
    msg = await bot.send_message(CHANNEL_ID, txt, reply_markup=kb)
    cur.execute("INSERT OR REPLACE INTO config VALUES ('msg_id', ?)", (msg.message_id,))
    conn.commit()
    await call.message.edit_text("🚀 Kanalga yuborildi!")

@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    conn.commit()
    args = message.get_args()
    cur.execute("SELECT value FROM config WHERE key='active'")
    active = cur.fetchone()
    if "join" in args:
        if not active or active[0] == '0': return await message.answer("❌ Konkurs aktiv emas.")
        cur.execute("SELECT value FROM config WHERE key='price'")
        price = int(cur.fetchone()[0])
        await bot.send_invoice(message.chat.id, title="Konkurs", description="To'lov qiling", payload="pay", provider_token="", currency="XTR", prices=[types.LabeledPrice("Stars", price)])
    else:
        await message.answer("Bot ishlamoqda! ✅")

@dp.pre_checkout_query_handler(lambda q: True, state="*")
async def pre_checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message_handler(content_types=['successful_payment'], state="*")
async def payment_done(message: types.Message):
    user = message.from_user
    cur.execute("INSERT OR IGNORE INTO participants VALUES (?, ?)", (user.id, f"@{user.username}" if user.username else f"ID:{user.id}"))
    cur.execute("SELECT COUNT(*) FROM participants")
    count = cur.fetchone()[0]
    cur.execute("SELECT value FROM config WHERE key='slots'")
    slots = int(cur.fetchone()[0])
    cur.execute("SELECT value FROM config WHERE key='msg_id'")
    msg_id = cur.fetchone()[0]
    bot_me = await bot.get_me()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(f"Qatnashish {count}", url=f"https://t.me/{bot_me.username}?start=join"))
    await bot.edit_message_reply_markup(CHANNEL_ID, msg_id, reply_markup=kb)
    await bot.send_message(ADMIN_ID, f"💰 Yangi to'lov!\n👤 @{user.username}\n🔢 {count}-ishtirokchi")
    if count >= slots:
        cur.execute("UPDATE config SET value='0' WHERE key='active'")
        conn.commit()
        kb_admin = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 Random", callback_data="win_random"), types.InlineKeyboardButton("👤 Tanlash", callback_data="win_list"))
        await bot.send_message(ADMIN_ID, "🏁 Konkurs to'ldi!", reply_markup=kb_admin)

@dp.callback_query_handler(lambda c: c.data.startswith('win_'), user_id=ADMIN_ID, state="*")
async def winner_logic(call: types.CallbackQuery):
    cur.execute("SELECT username FROM participants")
    ppl = cur.fetchall()
    if call.data == "win_random":
        winner = random.choice(ppl)[0]
        await bot.send_message(CHANNEL_ID, f"🎊 G'olib: {winner}")
    elif call.data == "win_list":
        res = "📋 Ro'yxat:\n" + "\n".join([f"{i+1}. {p[0]}" for i, p in enumerate(ppl)])
        await call.message.answer(res)

@dp.message_handler(commands=['Statistika'], user_id=ADMIN_ID, state="*")
async def stats(m: types.Message):
    cur.execute("SELECT COUNT(*) FROM users"); u = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM participants"); p = cur.fetchone()[0]
    await m.answer(f"📊 Statistika:\n- Azolar: {u}\n- Ishtirokchilar: {p}")

@dp.message_handler(commands=['Eror'], user_id=ADMIN_ID, state="*")
async def eror(m: types.Message, state: FSMContext):
    cur.execute("UPDATE config SET value='0' WHERE key='active'")
    cur.execute("DELETE FROM participants")
    conn.commit(); await state.finish()
    await m.answer("🛑 Tozalandi!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
