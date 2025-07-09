import os
import json
import logging

from fastapi import FastAPI, Request
import uvicorn
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, TelegramAPIError

import gspread
from config import BOT_TOKEN, ADMIN_CHAT_ID, SPREADSHEET_ID, WEBHOOK_URL, HUGGINGFACE_API_KEY, PAYZE_API_KEY, PAYZE_MERCHANT_ID
from huggingface_hub import InferenceClient
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

# === Hugging Face AI Client ===
logging.info(f"HUGGINGFACE_API_KEY exists: {HUGGINGFACE_API_KEY is not None}")
if HUGGINGFACE_API_KEY:
    logging.info(f"HUGGINGFACE_API_KEY length: {len(HUGGINGFACE_API_KEY)}")
    logging.info(f"HUGGINGFACE_API_KEY starts with: {HUGGINGFACE_API_KEY[:10]}...")
hf_client = InferenceClient(token=HUGGINGFACE_API_KEY) if HUGGINGFACE_API_KEY else None
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# === Payze Client ===
payze_client = PayzeClient(PAYZE_API_KEY, PAYZE_MERCHANT_ID) if PAYZE_API_KEY and PAYZE_MERCHANT_ID else None

# === AI Chat Handler ===
@dp.message_handler(commands=["ai"])
async def ai_chat(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("გთხოვთ, მიუთითეთ კითხვა: /ai თქვენი კითხვა")
        return
    
    await message.chat.do("typing")
    
    if hf_client:
        # Use Hugging Face if available
        try:
            response = await hf_client.text_generation(
                HF_MODEL,
                prompt,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.1,
                do_sample=True,
                return_full_text=False,
            )
            if hasattr(response, "generated_text"):
                answer = response.generated_text.strip()
            else:
                answer = str(response)
            await message.reply(answer)
        except Exception as e:
            await message.reply("დაფიქსირდა შეცდომა AI-სთან დაკავშირებისას. სცადეთ მოგვიანებით.")
            logging.error(f"AI ERROR: {e}")
    else:
        # Fallback to simple responses
        prompt_lower = prompt.lower()
        if "გამარჯობა" in prompt_lower or "hello" in prompt_lower or "hi" in prompt_lower:
            await message.reply("გამარჯობა! როგორ შემიძლია დაგეხმაროთ?")
        elif "როგორ ხარ" in prompt_lower or "how are you" in prompt_lower:
            await message.reply("მადლობა, კარგად! მზად ვარ დაგეხმაროთ ნებისმიერი კითხვით.")
        elif "მადლობა" in prompt_lower or "thank" in prompt_lower:
            await message.reply("გთხოვთ! სიამოვნებით დაგეხმარებით.")
        elif "?" in prompt:
            await message.reply("კარგი კითხვაა! უფასო AI ფუნქციონალის გასააქტიურებლად გთხოვთ, დაუკავშირდეთ ადმინისტრატორს HUGGINGFACE_API_KEY-ის დამატებისთვის.")
        else:
            await message.reply("მესმის თქვენი შეტყობინება. უფასო AI ფუნქციონალის გასააქტიურებლად გთხოვთ, დაუკავშირდეთ ადმინისტრატორს HUGGINGFACE_API_KEY-ის დამატებისთვის.")

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
    welcome_text = """🤖 გამარჯობა! მოგესალმებთ AI-ბოტი!

📋 **შეკვეთებისთვის:**
აირჩიე პროდუქტი ნომრის მიხედვით:

""" + "\n".join([f"{k}. {v}" for k, v in products.items()]) + """

💬 **AI ჩატისთვის:**
გამოიყენეთ ბრძანება: `/ai თქვენი კითხვა`

მაგალითად:
• `/ai როგორ ხარ?`
• `/ai გამარჯობა`
• `/ai რა არის AI?`

🛒 შეკვეთებისთვის აირჩიეთ პროდუქტი ზემოთ მოყვანილი სიიდან.
💬 AI ჩატისთვის გამოიყენეთ /ai ბრძანება."""
    
    await bot.send_message(chat_id=message.chat.id, text=welcome_text)

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = """🤖 **ბოტის ბრძანებები:**

📋 **შეკვეთებისთვის:**
• `/start` - დაიწყეთ შეკვეთის პროცესი
• აირჩიეთ პროდუქტი ნომრით (1, 2, 3, და ა.შ.)

💬 **AI ჩატისთვის:**
• `/ai კითხვა` - დაუსვით კითხვა AI-ს
• მაგალითად: `/ai როგორ ხარ?`

❓ **დახმარებისთვის:**
• `/help` - ეს შეტყობინება

🛒 **შეკვეთის პროცესი:**
1. აირჩიეთ პროდუქტი
2. შეიყვანეთ სახელი
3. შეიყვანეთ მისამართი
4. შეიყვანეთ ტელეფონი
5. გადაიხადეთ Payze-ით

💡 **AI ჩატი მუშაობს ორ რეჟიმში:**
• უფასო რეჟიმი - მარტივი პასუხები
• სრული AI რეჟიმი - Hugging Face მოდელით (საჭიროა API გასაღები)"""
    
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
    worksheet.append_row([
        message.from_user.username or str(message.from_user.id),
        data["product"],
        data["name"],
        data["address"],
        data["phone"]
    ])

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

    # === Payze გადახდის ბმული ===
    if payze_client:
        try:
            import re
            price_match = re.search(r"(\d+)[₾]", data["product"])
            amount = int(price_match.group(1)) if price_match else 400
            # description-ში ჩავწეროთ user_id, რომ ვიპოვოთ გადახდისას
            description = f"{data['product']} - {data['name']} (user_id:{message.from_user.id})"
            payze_response = payze_client.create_invoice(
                amount=amount,
                currency="GEL",
                callback_url=f"{WEBHOOK_URL}/payze_webhook",
                description=description
            )
            pay_url = payze_response["pay_url"] if "pay_url" in payze_response else None
            invoice_id = payze_response["invoice_id"] if "invoice_id" in payze_response else None
            if pay_url and invoice_id:
                user_invoice_map[invoice_id] = message.from_user.id
                await bot.send_message(message.chat.id, f"გადახდისთვის დააჭირე ბმულს:\n{pay_url}")
            else:
                await bot.send_message(message.chat.id, "გადახდის ბმულის გენერაცია ვერ მოხერხდა. სცადეთ მოგვიანებით.")
        except Exception as e:
            await bot.send_message(message.chat.id, "გადახდის ბმულის გენერაცია ვერ მოხერხდა. სცადეთ მოგვიანებით.")
            logging.error(f"PAYZE ERROR: {e}")
    else:
        await bot.send_message(message.chat.id, "გადახდის ფუნქციონალი დროებით მიუწვდომელია.")

    await bot.send_message(message.chat.id, "გმადლობთ! თქვენი შეკვეთა მიღებულია ✅")
    
    # დავამატოთ შეტყობინება AI ფუნქციის შესახებ
    await bot.send_message(
        message.chat.id, 
        "💡 **დამატებითი ფუნქციები:**\n"
        "• `/ai კითხვა` - დაუსვით კითხვა AI-ს\n"
        "• `/help` - ნახეთ ყველა ბრძანება\n"
        "• `/start` - დაიწყეთ ახალი შეკვეთა"
    )
    
    del user_data[message.from_user.id]

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
                await bot.send_message(user_id, "გადახდა წარმატებით დადასტურდა! ✅\nგმადლობთ, თქვენი შეკვეთა დამუშავდება მალე.")
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

