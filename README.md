# Telegram Order Bot V2

---

## 🇬🇪 ქართული ინსტრუქცია

### ფუნქციები
- 🛒 შეკვეთების მიღება Telegram-ში
- 💳 გადახდა Payze (Sandbox და Production)
- 🤖 AI ჩატი (უფასო მოდელი, Hugging Face)
- 📄 შეკვეთების ჩაწერა Google Sheets-ში
- 🔔 გადახდის დადასტურების ავტომატური შეტყობინება
- 🌐 მარტივი გაშვება Render-ზე

### დაყენება
1. დააკლონირე პროექტი და დააყენე დამოკიდებულებები:
   ```bash
   pip install -r requirements.txt
   ```
2. შექმენი `.env` ფაილი ან დაამატე გარემოს ცვლადები:
   - TELEGRAM_BOT_TOKEN
   - ADMIN_CHAT_ID
   - SPREADSHEET_ID
   - WEBHOOK_URL (მაგ: https://your-app.onrender.com/webhook)
   - PAYZE_API_KEY (Sandbox ან Production)
   - PAYZE_MERCHANT_ID (Sandbox ან Production)
   - HUGGINGFACE_API_KEY (Hugging Face-ის უფასო ტოკენი)
3. Google Sheets-ისთვის შექმენი service account და ატვირთე `credentials.json`.
4. გაუშვი ბოტი:
   ```bash
   python main.py
   ```

### ტესტირება Payze-ს Sandbox-ით
- გამოიყენე ტესტ გასაღებები და Merchant ID.
- ტესტ ბარათის მონაცემები:
  - ბარათის ნომერი: 4977 0000 0000 3436
  - ვადა: ნებისმიერი მომავალი თვე/წელი
  - CVC: ნებისმიერი 3-ნიშნა
- გადახდის შემდეგ ბოტი გამოგიგზავნის შეტყობინებას.

### Render-ზე გაშვება
- ატვირთე პროექტი GitHub-ზე და დააკონექტე Render-ზე.
- დაამატე ყველა საჭირო გარემოს ცვლადი Render-ის Settings-ში.
- სერვისი ავტომატურად გაეშვება და ექნება საჯარო მისამართი.

---

## 🇬🇧 English Instructions

### Features
- 🛒 Receive orders in Telegram
- 💳 Payze payments (Sandbox & Production)
- 🤖 AI chat (free model, Hugging Face)
- 📄 Save orders to Google Sheets
- 🔔 Automatic notification after payment confirmation
- 🌐 Easy deployment on Render

### Setup
1. Clone the project and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file or set environment variables:
   - TELEGRAM_BOT_TOKEN
   - ADMIN_CHAT_ID
   - SPREADSHEET_ID
   - WEBHOOK_URL (e.g. https://your-app.onrender.com/webhook)
   - PAYZE_API_KEY (Sandbox or Production)
   - PAYZE_MERCHANT_ID (Sandbox or Production)
   - HUGGINGFACE_API_KEY (Hugging Face free token)
3. For Google Sheets, create a service account and upload `credentials.json`.
4. Run the bot:
   ```bash
   python main.py
   ```

### Testing with Payze Sandbox
- Use test API key and Merchant ID.
- Test card details:
  - Card number: 4977 0000 0000 3436
  - Expiry: any future month/year
  - CVC: any 3 digits
- After payment, the bot will send you a confirmation message.

### Deploying on Render
- Push your project to GitHub and connect it to Render.
- Add all required environment variables in Render Settings.
- The service will start automatically and have a public URL.
