import os
import json
import logging
import datetime

from fastapi import FastAPI, Request
import uvicorn
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, TelegramAPIError

import gspread
from config import BOT_TOKEN, ADMIN_CHAT_ID, SPREADSHEET_ID, WEBHOOK_URL, PAYZE_API_KEY, PAYZE_MERCHANT_ID
from payze import PayzeClient

# === Logging ===
logging.basicConfig(level=logging.INFO)

# === Initialize FastAPI ===
app = FastAPI()

# === Initialize bot and dispatcher ===
bot = Bot(token=BOT_TOKEN)
bot.set_current(bot)

dp = Dispatcher(bot)
dp.set_current(dp)

# === Google Sheets setup ===
gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.sheet1

# === Sample products ===
products = {
    "1": "შეკვეთის მიმღები AI-ბოტი - 400₾",
    "2": "ჯავშნის მიმღები AI-ბოტი - 400₾",
    "3": "პირადი AI-აგენტი - 400₾",
    "4": "ინვოისების და გადახდის გადაგზავნის AI-ბოტი - 400₾",
    "5": "თქვენზე მორგებული AI-ბოტების შექმნა - შეთანხმებით",
    "6": "ავტომატიზირებული სისტემების შექმნა AI გამოყენებით - შეთანხმებით",
    "7": "ვებგვერდების და აპლიკაციების შემოწმება უსაფრთხოებაზე - შეთანხმებით"
}

user_data = {}

# === ინვოისების დროებითი ბაზა (user_id <-> invoice_id) ===
user_invoice_map = {}

# === Payze Client ===
payze_client = PayzeClient(PAYZE_API_KEY, PAYZE_MERCHANT_ID) if PAYZE_API_KEY and PAYZE_MERCHANT_ID else None



@dp.message_handler(commands=["test"])
async def test_bot(message: types.Message):
    """ტესტ ბრძანება ბოტის მუშაობის შესამოწმებლად"""
    logging.info(f"Test command received from user {message.from_user.id}")
    try:
        await bot.send_message(message.chat.id, "🤖 ბოტი მუშაობს! ტესტი წარმატებულია.")
    except Exception as e:
        logging.error(f"Error sending test message: {e}")

# === Routes ===
@app.get("/")
async def root():
    return {"status": "🤖 Bot is running with webhook on Render"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.body()
    logging.info(f"📩 მიღებულია update: {body}")
    
    update = types.Update(**json.loads(body))
    await dp.process_update(update)
    return {"ok": True}

# === Bot Handlers ===
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = """🤖 გამარჯობა! მოგესალმებთ შეკვეთების ბოტი!

📋 **შეკვეთებისთვის:**
აირჩიე პროდუქტი ნომრის მიხედვით:

""" + "\n".join([f"{k}. {v}" for k, v in products.items()]) + """

🛒 შეკვეთებისთვის აირჩიეთ პროდუქტი ზემოთ მოყვანილი სიიდან.

❓ **დახმარებისთვის:** `/help`"""
    
    await bot.send_message(chat_id=message.chat.id, text=welcome_text)
    
    # დავამატოთ ბრძანებების სია
    commands_text = """🔧 **ხელმისაწვდომი ბრძანებები:**

/start - მთავარი მენიუ
/help - დახმარება და ინსტრუქციები
/test - ბოტის ტესტი

💡 **სწრაფი ბრძანებები:**
• `/help` - ნახეთ ყველა ფუნქცია"""
    
    await bot.send_message(chat_id=message.chat.id, text=commands_text)

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = """🤖 **ბოტის ბრძანებები:**

📋 **შეკვეთებისთვის:**
• `/start` - დაიწყეთ შეკვეთის პროცესი
• აირჩიეთ პროდუქტი ნომრით (1, 2, 3, და ა.შ.)

❓ **დახმარებისთვის:**
• `/help` - ეს შეტყობინება

🛒 **შეკვეთის პროცესი:**
1. აირჩიეთ პროდუქტი
2. შეიყვანეთ სახელი
3. შეიყვანეთ მისამართი
4. შეიყვანეთ ტელეფონი
5. აირჩიეთ გადახდის მეთოდი

💳 **გადახდის ვარიანტები:**
• 💵 **ნაღდი ფული** - გადაიხადეთ მიწოდებისას
• 💳 **ონლაინ გადახდა** - გადაიხადეთ ახლა Payze-ით

💡 **შეკვეთებისთვის:** აირჩიეთ პროდუქტი /start ბრძანებით."""
    
    await bot.send_message(chat_id=message.chat.id, text=help_text)

@dp.message_handler(lambda message: message.text in products.keys())
async def product_selected(message: types.Message):
    user_data[message.from_user.id] = {"product": products[message.text]}
    await bot.send_message(message.chat.id, "შენ აირჩიე: " + products[message.text])
    await bot.send_message(message.chat.id, "შეიყვანეთ თქვენი სახელი:")

@dp.message_handler(lambda message: message.from_user.id in user_data and "name" not in user_data[message.from_user.id])
async def get_name(message: types.Message):
    user_data[message.from_user.id]["name"] = message.text
    await bot.send_message(message.chat.id, "შეიყვანეთ მისამართი:")

@dp.message_handler(lambda message: message.from_user.id in user_data and "address" not in user_data[message.from_user.id])
async def get_address(message: types.Message):
    user_data[message.from_user.id]["address"] = message.text
    await bot.send_message(message.chat.id, "შეიყვანეთ ტელეფონი:")

@dp.message_handler(lambda message: message.from_user.id in user_data and "phone" not in user_data[message.from_user.id])
async def get_phone(message: types.Message):
    user_data[message.from_user.id]["phone"] = message.text

    data = user_data[message.from_user.id]
    order_date = datetime.date.today().isoformat()
    order_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # შეკვეთის დამატებისას სტატუსი იყოს ცარიელი, ბოლო ორი სვეტი: თარიღი და დრო
    worksheet.append_row([
        message.from_user.username or str(message.from_user.id),
        data["product"],
        data["name"],
        data["address"],
        data["phone"],
        "",  # სტატუსი ცარიელია
        order_date,
        order_time
    ])

    # შევატყობინოთ ადმინს
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"📥 ახალი შეკვეთა:\n"
            f"👤 მომხმარებელი: {message.from_user.username or message.from_user.id}\n"
            f"📦 პროდუქტი: {data['product']}\n"
            f"📛 სახელი: {data['name']}\n"
            f"📍 მისამართი: {data['address']}\n"
            f"📞 ტელეფონი: {data['phone']}"
        )
    except BotBlocked:
        logging.warning(f"ბოტი დაბლოკილია ADMIN_CHAT_ID: {ADMIN_CHAT_ID}")
    except ChatNotFound:
        logging.warning(f"ჩეთი ვერ მოიძებნა: {ADMIN_CHAT_ID}")
    except TelegramAPIError as e:
        logging.error(f"Telegram API შეცდომა: {e}")

    # შეკვეთის დასრულების შეტყობინება
    await bot.send_message(message.chat.id, "✅ თქვენი შეკვეთა წარმატებით მიღებულია!")
    
    # გადახდის ვარიანტების შეტყობინება
    payment_text = f"""💳 **გადახდის ვარიანტები:**

📦 პროდუქტი: {data['product']}

🔸 **ვარიანტი 1: ნაღდი ფული მიწოდებისას**
   - გადაიხადეთ მიწოდებისას ნაღდი ფულით
   - უფასო მიწოდება

🔸 **ვარიანტი 2: ონლაინ გადახდა**
   - გადაიხადეთ ახლა ონლაინ Payze-ით
   - უფასო მიწოდება

აირჩიეთ გადახდის მეთოდი:"""
    
    # შევქმნათ ღილაკები
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💵 ნაღდი ფული", callback_data=f"cash_{message.from_user.id}"),
        types.InlineKeyboardButton("💳 ონლაინ გადახდა", callback_data=f"online_{message.from_user.id}")
    )
    
    await bot.send_message(message.chat.id, payment_text, reply_markup=keyboard)
    
    # შევინახოთ მომხმარებლის მონაცემები გადახდისთვის
    user_data[message.from_user.id]["payment_pending"] = True

# === Callback Handlers for Payment Buttons ===
@dp.callback_query_handler(lambda c: c.data.startswith('cash_'))
async def cash_payment(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])
    
    if user_id != callback_query.from_user.id:
        await callback_query.answer("ეს ღილაკი არ არის თქვენი შეკვეთისთვის!")
        return
    
    if user_id not in user_data:
        await callback_query.answer("შეკვეთა ვერ მოიძებნა!")
        return
    
    data = user_data[user_id]
    
    # განვახლოთ Google Sheets-ში სტატუსი "ნაღდი ფული"
    try:
        all_orders = worksheet.get_all_values()
        for i, row in enumerate(all_orders):
            if row[0] == str(user_id) and row[1] == data["product"] and row[2] == data["name"]:
                worksheet.update_cell(i + 1, 6, "ნაღდი ფული")
                break
    except Exception as e:
        logging.error(f"Google Sheets განახლების შეცდომა: {e}")
    
    await callback_query.message.edit_text(
        f"✅ **ნაღდი ფულით გადახდა არჩეულია!**\n\n"
        f"📦 პროდუქტი: {data['product']}\n"
        f"📛 სახელი: {data['name']}\n"
        f"📍 მისამართი: {data['address']}\n"
        f"📞 ტელეფონი: {data['phone']}\n\n"
        f"💵 გადაიხადეთ მიწოდებისას ნაღდი ფულით.\n"
        f"🚚 მიწოდება მოხდება მალე.\n\n"
        f"💡 ახალი შეკვეთისთვის: `/start`"
    )
    
    # შევატყობინოთ ადმინს
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"💵 **ნაღდი ფულით გადახდა არჩეულია:**\n"
            f"👤 მომხმარებელი: {callback_query.from_user.username or callback_query.from_user.id}\n"
            f"📦 პროდუქტი: {data['product']}\n"
            f"📛 სახელი: {data['name']}\n"
            f"📍 მისამართი: {data['address']}\n"
            f"📞 ტელეფონი: {data['phone']}"
        )
    except Exception as e:
        logging.error(f"ადმინისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
    
    del user_data[user_id]

@dp.callback_query_handler(lambda c: c.data.startswith('online_'))
async def online_payment(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])
    
    if user_id != callback_query.from_user.id:
        await callback_query.answer("ეს ღილაკი არ არის თქვენი შეკვეთისთვის!")
        return
    
    if user_id not in user_data:
        await callback_query.answer("შეკვეთა ვერ მოიძებნა!")
        return
    
    data = user_data[user_id]
    
    # შევქმნათ Payze გადახდის ბმული
    if payze_client:
        try:
            import re
            price_match = re.search(r"(\d+)[₾]", data["product"])
            amount = int(price_match.group(1)) if price_match else 400
            description = f"{data['product']} - {data['name']} (user_id:{user_id})"
            
            payze_response = payze_client.create_invoice(
                amount=amount,
                currency="GEL",
                callback_url=f"{WEBHOOK_URL}/payze_webhook",
                description=description
            )
            
            pay_url = payze_response.get("pay_url")
            invoice_id = payze_response.get("invoice_id")
            
            if pay_url and invoice_id:
                user_invoice_map[invoice_id] = user_id
                
                await callback_query.message.edit_text(
                    f"💳 **ონლაინ გადახდა არჩეულია!**\n\n"
                    f"📦 პროდუქტი: {data['product']}\n"
                    f"💰 თანხა: {amount}₾\n\n"
                    f"🔗 გადახდის ბმული:\n{pay_url}\n\n"
                    f"💡 გადახდის შემდეგ მიიღებთ დადასტურებას."
                )
                
                # განვახლოთ Google Sheets-ში სტატუსი "ონლაინ გადახდა"
                try:
                    all_orders = worksheet.get_all_values()
                    for i, row in enumerate(all_orders):
                        if row[0] == str(user_id) and row[1] == data["product"] and row[2] == data["name"]:
                            worksheet.update_cell(i + 1, 6, "ონლაინ გადახდა")
                            break
                except Exception as e:
                    logging.error(f"Google Sheets განახლების შეცდომა: {e}")
                
            else:
                await callback_query.message.edit_text(
                    "❌ გადახდის ბმულის გენერაცია ვერ მოხერხდა.\n"
                    "გთხოვთ, სცადეთ მოგვიანებით ან აირჩიეთ ნაღდი ფულით გადახდა."
                )
                
        except Exception as e:
            logging.error(f"PAYZE ERROR: {e}")
            await callback_query.message.edit_text(
                "❌ გადახდის სისტემა დროებით მიუწვდომელია.\n"
                "გთხოვთ, აირჩიეთ ნაღდი ფულით გადახდა."
            )
    else:
        await callback_query.message.edit_text(
            "❌ ონლაინ გადახდა დროებით მიუწვდომელია.\n"
            "გთხოვთ, აირჩიეთ ნაღდი ფულით გადახდა."
        )

# === Payze გადახდის სტატუსის Webhook ===
@app.post("/payze_webhook")
async def payze_webhook(request: Request):
    body = await request.json()
    logging.info(f"[PAYZE] მიღებულია გადახდის სტატუსი: {body}")
    invoice_id = body.get("invoice_id")
    status = body.get("status")
    
    # Payze-ს დოკუმენტაციით, წარმატებული გადახდა: status == 'paid'
    if invoice_id and status == "paid":
        user_id = user_invoice_map.get(invoice_id)
        if user_id:
            try:
                # განვახლოთ Google Sheets-ში სტატუსი მხოლოდ თუ "ონლაინ გადახდა" იყო
                try:
                    all_orders = worksheet.get_all_values()
                    for i, row in enumerate(all_orders):
                        if row[0] == str(user_id) and row[5] == "ონლაინ გადახდა":
                            worksheet.update_cell(i + 1, 6, "გადახდილი")
                            break
                except Exception as e:
                    logging.error(f"Google Sheets განახლების შეცდომა: {e}")
                
                # შევატყობინოთ მომხმარებელს
                await bot.send_message(
                    user_id, 
                    "✅ **გადახდა წარმატებით დადასტურდა!**\n\n"
                    "💳 თქვენი გადახდა მიღებულია.\n"
                    "🚚 შეკვეთა დამუშავდება და მიიტანება მალე.\n\n"
                    "💡 ახალი შეკვეთისთვის: `/start`"
                )
                
                # შევატყობინოთ ადმინს
                try:
                    await bot.send_message(
                        ADMIN_CHAT_ID,
                        f"💳 **გადახდა დადასტურდა!**\n"
                        f"👤 მომხმარებელი: {user_id}\n"
                        f"🆔 Invoice ID: {invoice_id}\n"
                        f"✅ სტატუსი: გადახდილი"
                    )
                except Exception as e:
                    logging.error(f"ადმინისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
                
                del user_invoice_map[invoice_id]
                
            except Exception as e:
                logging.error(f"[PAYZE] მომხმარებლისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
    
    return JSONResponse(content={"ok": True})

# === Start server & webhook setup ===
if __name__ == "__main__":
    import asyncio

    async def on_startup():
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook დაყენებულია: {WEBHOOK_URL}")

    async def on_shutdown():
        logging.info("ბოტი ითიშება...")
        await bot.delete_webhook()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())

    port = int(os.environ.get("PORT", 10000))  # Render-ის პორტი
    uvicorn.run("main:app", host="0.0.0.0", port=port)

