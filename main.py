import os
import json
import logging
import datetime
import asyncio
import aiohttp

from fastapi import FastAPI, Request
import uvicorn
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Update

import gspread
from config import BOT_TOKEN, ADMIN_CHAT_ID, SPREADSHEET_ID, WEBHOOK_URL, PAYZE_API_KEY, PAYZE_MERCHANT_ID
from payze import PayzeClient

# === Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === Initialize FastAPI ===
app = FastAPI()

# === Initialize bot and dispatcher ===
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN არ არის განსაზღვრული!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Google Sheets setup ===
if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID არ არის განსაზღვრული!")

gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.sheet1

# === Sample products ===
products = {
    "1": "შეკვეთების მიმღები AI-ბოტი - 300₾",
    "2": "ჯავშნის მიმღები AI-ბოტი - 300₾",
    "3": "პირადი AI-აგენტი - 300₾",
    "4": "ინვოისების და გადახდის გადაგზავნის AI-ბოტი - 300₾",
    "5": "თქვენზე მორგებული AI-ბოტების შექმნა - შეთანხმებით",
    "6": "ავტომატიზირებული სისტემების შექმნა AI გამოყენებით - შეთანხმებით",
    "7": "ვებგვერდების და აპლიკაციების შემოწმება უსაფრთხოებაზე - შეთანხმებით",
    "8": "ვებ გვერდებისა და აპლიკაციების შექმნა - შეთანხმებით"
}

user_data = {}

# === ინვოისების დროებითი ბაზა (user_id <-> invoice_id) ===
user_invoice_map = {}

# === Payze Client ===
payze_client = PayzeClient(PAYZE_API_KEY, PAYZE_MERCHANT_ID) if PAYZE_API_KEY and PAYZE_MERCHANT_ID else None

# === Self-ping system for Render free tier ===
async def self_ping_worker():
    """Keep the bot awake by pinging itself every 5 minutes"""
    ping_interval = 300  # 5 minutes (more aggressive)
    ping_url = None
    
    # Get ping URL from environment or construct from webhook URL
    if os.getenv("SELF_PING_URL"):
        ping_url = os.getenv("SELF_PING_URL")
        if ping_url:
            ping_url = ping_url.rstrip("/") + "/"
    elif WEBHOOK_URL:
        # Use the root of the webhook URL
        from urllib.parse import urlparse
        parsed = urlparse(WEBHOOK_URL)
        ping_url = f"{parsed.scheme}://{parsed.netloc}/"
    
    if not ping_url:
        logger.warning("Self-ping disabled: no SELF_PING_URL or WEBHOOK_URL configured")
        return
    
    logger.info(f"Self-ping worker started. Target: {ping_url}, Interval: {ping_interval}s")
    
    # Also ping the /ping endpoint for better reliability
    ping_endpoints = [
        ping_url,
        f"{ping_url.rstrip('/')}/ping"
    ]
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            success = False
            
            for endpoint in ping_endpoints:
                try:
                    async with session.get(endpoint) as response:
                        if response.status == 200:
                            logger.info(f"Self-ping OK: {endpoint}")
                            success = True
                            break
                        else:
                            logger.warning(f"Self-ping non-200: {response.status} {endpoint}")
                except Exception as e:
                    logger.error(f"Self-ping error for {endpoint}: {e}")
            
            if not success:
                logger.error("All ping endpoints failed")
            
            await asyncio.sleep(ping_interval)

# === Routes ===
@app.get("/")
async def root():
    return {"status": "🤖 Bot is running with webhook on Render", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/ping")
async def ping():
    """Health check endpoint for self-ping and external monitoring"""
    return {"status": "pong", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/health")
async def health():
    """Comprehensive health check endpoint for external monitoring services"""
    try:
        # Check if bot is responsive
        bot_info = await bot.get_me()
        
        # Check if Google Sheets is accessible
        try:
            worksheet.get_all_values()
            sheets_status = "ok"
        except Exception as e:
            sheets_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "bot": {
                "id": bot_info.id if bot_info else None,
                "username": bot_info.username if bot_info else None,
                "first_name": bot_info.first_name if bot_info else None
            },
            "sheets": sheets_status,
            "payze": "configured" if payze_client else "not_configured",
            "uptime": "24/7"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/uptime")
async def uptime():
    """Simple uptime endpoint for monitoring services"""
    return {"status": "up", "timestamp": datetime.datetime.now().isoformat()}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming webhook updates from Telegram"""
    try:
        update_data = await request.json()
        logger.info(f"Received webhook update: {update_data}")
        
        # Process the update
        update = Update(**update_data)
        await dp.feed_update(bot, update)
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"ok": False, "error": str(e)}

# === Bot Handlers ===
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = """🤖 გამარჯობა! მოგესალმებით შეკვეთების ბოტი!

📋 **შეკვეთებისთვის:**
აირჩიეთ პროდუქტი ნომრის მიხედვით:

""" + "\n".join([f"{k}. {v}" for k, v in products.items()]) + """

🛒 შეკვეთებისთვის აირჩიეთ პროდუქტი ზემოთ მოყვანილი სიიდან.

❓ **დახმარებისთვის:** `/help`"""
    
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = """🤖 **ბოტის ბრძანებები:**\n\n📋 **შეკვეთებისთვის:**\n• `/start` - დაიწყეთ შეკვეთის პროცესი\n• აირჩიეთ პროდუქტი ნომრით (1, 2, 3, და ა.შ.)\n\n❓ **დახმარებისთვის:**\n• `/help` - ეს შეტყობინება\n\n🛒 **შეკვეთის პროცესი:**\n1. აირჩიეთ პროდუქტი\n2. შეიყვანეთ სახელი\n3. შეიყვანეთ მისამართი\n4. შეიყვანეთ ტელეფონი\n5. აირჩიეთ გადახდის მეთოდი\n\n💳 **გადახდის ვარიანტები:**\n• 💵 **ნაღდი ფული** - გადაიხადეთ მიწოდებისას\n• 💳 **ონლაინ გადახდა** - გადაიხადეთ ახლა Payze-ით\n\n👨‍💼 **კითხვები ან დახმარება?**\nდაუკავშირდით ადმინს: [ჩატი ადმინთან](https://t.me/mebura)\n\n💡 **შეკვეთებისთვის:** აირჩიეთ პროდუქტი /start ბრძანებით."""
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(lambda message: message.text in products.keys())
async def product_selected(message: types.Message):
    if message.from_user and message.from_user.id:
        user_data[message.from_user.id] = {"product": products[message.text]}
        await message.answer("შენ აირჩიე: " + products[message.text])
        await message.answer("შეიყვანეთ თქვენი სახელი:")

@dp.message(lambda message: message.from_user and message.from_user.id and message.from_user.id in user_data and "name" not in user_data[message.from_user.id])
async def get_name(message: types.Message):
    if message.from_user and message.from_user.id:
        user_data[message.from_user.id]["name"] = message.text
        await message.answer("შეიყვანეთ მისამართი:")

@dp.message(lambda message: message.from_user and message.from_user.id and message.from_user.id in user_data and "address" not in user_data[message.from_user.id])
async def get_address(message: types.Message):
    if message.from_user and message.from_user.id:
        user_data[message.from_user.id]["address"] = message.text
        await message.answer("შეიყვანეთ ტელეფონი:")

@dp.message(lambda message: message.from_user and message.from_user.id and message.from_user.id in user_data and "phone" not in user_data[message.from_user.id])
async def get_phone(message: types.Message):
    if not message.from_user or not message.from_user.id:
        return
        
    user_data[message.from_user.id]["phone"] = message.text

    data = user_data[message.from_user.id]
    order_date = datetime.date.today().isoformat()
    order_time = datetime.datetime.now().strftime("%H:%M:%S")
    # Save date and time in user_data for later status update
    user_data[message.from_user.id]["order_date"] = order_date
    user_data[message.from_user.id]["order_time"] = order_time
    
    # Always append to the last row, ignore empty rows
    worksheet.append_row([
        str(message.from_user.id),  # მხოლოდ user_id A სვეტში
        data["product"],
        data["name"],
        data["address"],
        data["phone"],
        "",  # სტატუსი ცარიელია (F)
        order_date,
        order_time
    ], table_range="A1:H1")

    # შეკვეთის დასრულების შეტყობინება
    await message.answer("✅ მადლობა, თქვენი შეკვეთა წარმატებით მიღებულია!")
    
    # გადახდის ვარიანტების შეტყობინება
    payment_text = f"""💳 **გადახდის ვარიანტები:**\n\n📦 პროდუქტი: {data['product']}\n\n🔸 **ვარიანტი 1: ნაღდი ფული მიწოდებისას**\n   - გადაიხადეთ მიწოდებისას ნაღდი ფულით\n   - უფასო მიწოდება\n\n🔸 **ვარიანტი 2: ონლაინ გადახდა**\n   - გადაიხადეთ ახლა ონლაინ Payze-ით\n   - უფასო მიწოდება\n\nაირჩიეთ გადახდის მეთოდი:"""
    
    # შევქმნათ ღილაკები
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="💵 ნაღდი ფული", callback_data=f"cash_{message.from_user.id}"),
            types.InlineKeyboardButton(text="💳 ონლაინ გადახდა", callback_data=f"online_{message.from_user.id}")
        ]
    ])
    
    await message.answer(payment_text, reply_markup=keyboard)
    
    # შევინახოთ მომხმარებლის მონაცემები გადახდისთვის
    user_data[message.from_user.id]["payment_pending"] = True

# === Callback Handlers for Payment Buttons ===
# Helper to find the correct row for status update

def find_order_row(user_id, product, phone, order_date, order_time):
    all_orders = worksheet.get_all_values()
    for i, row in enumerate(all_orders):
        if (
            len(row) >= 8 and
            row[0] == str(user_id) and
            row[1] == product and
            row[4] == phone and
            row[6] == order_date and
            row[7] == order_time
        ):
            return i + 1  # 1-based index for gspread
    return None

@dp.callback_query(lambda c: c.data and c.data.startswith('cash_'))
async def cash_payment(callback_query: types.CallbackQuery):
    if not callback_query.data:
        return
    user_id = int(callback_query.data.split('_')[1])
    
    if user_id != callback_query.from_user.id:
        await callback_query.answer("ეს ღილაკი არ არის თქვენი შეკვეთისთვის!")
        return
    
    data = user_data.get(user_id)
    if not data:
        logger.error(f"user_data not found for user_id: {user_id}")
        await callback_query.answer("შეკვეთა ვერ მოიძებნა! გთხოვთ, დაიწყეთ ახალი შეკვეთა /start ბრძანებით.")
        return
    
    # შევამოწმოთ, რომ ყველა საჭირო მონაცემი არსებობს
    required_fields = ["product", "name", "address", "phone", "order_date", "order_time"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.error(f"Missing fields for user_id {user_id}: {missing_fields}. Available fields: {list(data.keys())}")
        await callback_query.answer(f"შეკვეთის მონაცემები არასრულია. გთხოვთ, დაიწყეთ ახალი შეკვეთა /start ბრძანებით.")
        return
    
    logger.info(f"find_order_row params: user_id={user_id}, product={data['product']}, phone={data['phone']}, date={data['order_date']}, time={data['order_time']}")
    row_idx = find_order_row(
        user_id,
        data["product"],
        data["phone"],
        data["order_date"],
        data["order_time"]
    )
    logger.info(f"find_order_row result: row_idx={row_idx}")
    if row_idx:
        try:
            worksheet.update_cell(row_idx, 6, "ნაღდი ფული")
        except Exception as e:
            logger.error(f"Google Sheets განახლების შეცდომა: {e}")
    else:
        logger.error(f"ვერ მოიძებნა შესაბამისი რიგი გადახდის სტატუსის ჩასაწერად (cash). user_id={user_id}")

    # შეკვეთის დასრულების შეტყობინება (ნაღდი ფული)
    complete_text = (
        f"💵 **ნაღდი ფულით გადახდა არჩეულია!**\n\n"
        f"📦 პროდუქტი: {data['product']}\n"
        f"📛 სახელი: {data['name']}\n"
        f"📍 მისამართი: {data['address']}\n"
        f"📞 ტელეფონი: {data['phone']}\n\n"
        f"💵 გადაიხადეთ მიწოდებისას ნაღდი ფულით.\n"
        f"🚚 მიწოდება მოხდება მალე.\n\n"
    )
    complete_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="/start", callback_data="start_again"),
            types.InlineKeyboardButton(text="/help", callback_data="help_info")
        ]
    ])
    await callback_query.message.edit_text(complete_text, reply_markup=complete_keyboard)

    # შევატყობინოთ ადმინს შეკვეთის დეტალებით, გადახდის მეთოდით და ბმულით
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"📥 ახალი შეკვეთა\n"
            f"👤 მომხმარებელი: {callback_query.from_user.username or callback_query.from_user.id}\n"
            f"📦 პროდუქტი: {data['product']}\n"
            f"📛 სახელი: {data['name']}\n"
            f"📍 მისამართი: {data['address']}\n"
            f"📞 ტელეფონი: {data['phone']}\n"
            f"🗓 თარიღი: {data['order_date']}\n"
            f"⏰ დრო: {data['order_time']}\n"
            f"💳 გადახდის მეთოდი: ნაღდი ფული"
        )
        # წავშალოთ მომხმარებლის მონაცემები მხოლოდ მას შემდეგ, რაც ადმინს წარმატებით გაეგზავნება შეტყობინება
        del user_data[user_id]
    except Exception as e:
        logger.error(f"ადმინისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
        # თუ ადმინისთვის შეტყობინების გაგზავნა ვერ მოხერხდა, მაინც წავშალოთ მონაცემები
        del user_data[user_id]

@dp.callback_query(lambda c: c.data and c.data.startswith('online_'))
async def online_payment(callback_query: types.CallbackQuery):
    if not callback_query.data:
        return
    user_id = int(callback_query.data.split('_')[1])
    
    if user_id != callback_query.from_user.id:
        await callback_query.answer("ეს ღილაკი არ არის თქვენი შეკვეთისთვის!")
        return
    
    data = user_data.get(user_id)
    if not data:
        logger.error(f"user_data not found for user_id: {user_id}")
        await callback_query.answer("შეკვეთა ვერ მოიძებნა! გთხოვთ, დაიწყეთ ახალი შეკვეთა /start ბრძანებით.")
        return
    
    # შევამოწმოთ, რომ ყველა საჭირო მონაცემი არსებობს
    required_fields = ["product", "name", "address", "phone", "order_date", "order_time"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.error(f"Missing fields for user_id {user_id}: {missing_fields}. Available fields: {list(data.keys())}")
        await callback_query.answer(f"შეკვეთის მონაცემები არასრულია. გთხოვთ, დაიწყეთ ახალი შეკვეთა /start ბრძანებით.")
        return
    
    logger.info(f"find_order_row params: user_id={user_id}, product={data['product']}, phone={data['phone']}, date={data['order_date']}, time={data['order_time']}")
    row_idx = find_order_row(
        user_id,
        data["product"],
        data["phone"],
        data["order_date"],
        data["order_time"]
    )
    logger.info(f"find_order_row result: row_idx={row_idx}")
    if row_idx:
        try:
            worksheet.update_cell(row_idx, 6, "ონლაინ გადახდა")
        except Exception as e:
            logger.error(f"Google Sheets განახლების შეცდომა: {e}")
    else:
        logger.error(f"ვერ მოიძებნა შესაბამისი რიგი გადახდის სტატუსის ჩასაწერად (online). user_id={user_id}")

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
                
                # შეკვეთის დასრულების შეტყობინება (ონლაინ გადახდა)
                complete_text = (
                    f"💳 **ონლაინ გადახდა არჩეულია!**\n\n"
                    f"📦 პროდუქტი: {data['product']}\n"
                    f"💰 თანხა: {amount}₾\n\n"
                    f"🔗 გადახდის ბმული:\n{pay_url}\n\n"
                    f"💡 გადახდის შემდეგ მიიღებთ დადასტურებას."
                )
                # ბოლოს
                complete_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="/start", callback_data="start_again"),
                        types.InlineKeyboardButton(text="/help", callback_data="help_info")
                    ]
                ])
                await callback_query.message.edit_text(complete_text, reply_markup=complete_keyboard)

                # შევატყობინოთ ადმინს შეკვეთის დეტალებით, გადახდის მეთოდით და ბმულით
                try:
                    await bot.send_message(
                        ADMIN_CHAT_ID,
                        f"📥 ახალი შეკვეთა\n"
                        f"👤 მომხმარებელი: {callback_query.from_user.username or callback_query.from_user.id}\n"
                        f"📦 პროდუქტი: {data['product']}\n"
                        f"📛 სახელი: {data['name']}\n"
                        f"📍 მისამართი: {data['address']}\n"
                        f"📞 ტელეფონი: {data['phone']}\n"
                        f"🗓 თარიღი: {data['order_date']}\n"
                        f"⏰ დრო: {data['order_time']}\n"
                        f"💳 გადახდის მეთოდი: ონლაინ გადახდა\n"
                        f"🔗 გადახდის ბმული: {pay_url}"
                    )
                except Exception as e:
                    logger.error(f"ადმინისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
                
            else:
                cash_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="ნაღდი ფულით გადახდა", callback_data=f"cash_{user_id}")]
                ])
                await callback_query.message.edit_text(
                    "❌ გადახდის ბმულის გენერაცია ვერ მოხერხდა.\n"
                    "გთხოვთ, სცადეთ მოგვიანებით ან აირჩიეთ ნაღდი ფულით გადახდა.",
                    reply_markup=cash_keyboard
                )
                
        except Exception as e:
            logger.error(f"PAYZE ERROR: {e}")
            cash_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="ნაღდი ფულით გადახდა", callback_data=f"cash_{user_id}")]
            ])
            await callback_query.message.edit_text(
                "❌ გადახდის სისტემა დროებით მიუწვდომელია.\n"
                "აირჩიეთ ნაღდი ფულით გადახდა 👇",
                reply_markup=cash_keyboard
            )
    else:
        cash_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="ნაღდი ფულით გადახდა", callback_data=f"cash_{user_id}")]
        ])
        await callback_query.message.edit_text(
            "❌ ონლაინ გადახდა დროებით მიუწვდომელია.\n"
            "აირჩიეთ ნაღდი ფულით გადახდა 👇",
            reply_markup=cash_keyboard
        )

# === Payze გადახდის სტატუსის Webhook ===
@app.post("/payze_webhook")
async def payze_webhook(request: Request):
    body = await request.json()
    logger.info(f"[PAYZE] მიღებულია გადახდის სტატუსი: {body}")
    invoice_id = body.get("invoice_id")
    status = body.get("status")
    
    # Payze-ს დოკუმენტაციით, წარმატებული გადახდა: status == 'paid'
    if invoice_id and status == "paid":
        user_id = user_invoice_map.get(invoice_id)
        data = user_data.get(user_id)
        if user_id and data:
            try:
                row_idx = find_order_row(
                    user_id,
                    data["product"],
                    data["phone"],
                    data["order_date"],
                    data["order_time"]
                )
                if row_idx:
                    try:
                        worksheet.update_cell(row_idx, 6, "გადახდილი")
                    except Exception as e:
                        logger.error(f"Google Sheets განახლების შეცდომა: {e}")
                
                # შევატყობინოთ მომხმარებელს
                await bot.send_message(
                    user_id, 
                    "✅ **გადახდა წარმატებით დადასტურდა!**\n\n"
                    "💳 თქვენი გადახდა მიღებულია.\n"
                    "🚚 შეკვეთა დამუშავდება და მოგეწოდება მალე.\n\n" 
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
                    logger.error(f"ადმინისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
                
                del user_invoice_map[invoice_id]
                
            except Exception as e:
                logger.error(f"[PAYZE] მომხმარებლისთვის შეტყობინების გაგზავნის შეცდომა: {e}")
    
    return JSONResponse(content={"ok": True})

# === Start server & webhook setup ===
@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    try:
        # Set webhook
        if WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"✅ Webhook დაყენებულია: {WEBHOOK_URL}")
        else:
            logger.warning("⚠️ WEBHOOK_URL არ არის განსაზღვრული!")
        
        # Start self-ping worker
        asyncio.create_task(self_ping_worker())
        logger.info("✅ Self-ping worker started")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("🔄 ბოტი ითიშება...")
        await bot.delete_webhook()
        logger.info("✅ Webhook წაშლილია")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render-ის პორტი
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

# დაამატე ჰენდლერი start_again და help_info callback-ებისთვის
@dp.callback_query(lambda c: c.data == 'start_again')
async def callback_start_again(callback_query: types.CallbackQuery):
    await send_welcome(callback_query.message)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == 'help_info')
async def callback_help_info(callback_query: types.CallbackQuery):
    await send_help(callback_query.message)
    await callback_query.answer()

