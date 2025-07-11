# Telegram Order Bot V2

---

## 🇬🇪 ქართული ინსტრუქცია

### ფუნქციები
- 🛒 შეკვეთების მიღება Telegram-ში
- 💳 გადახდა Payze (Sandbox და Production)
- 📄 შეკვეთების ჩაწერა Google Sheets-ში
- 🔔 გადახდის დადასტურების ავტომატური შეტყობინება
- 🌐 მარტივი გაშვება Render-ზე
- ⚡ 24/7 მუშაობა Render-ის უფასო ვერსიაზე

### Render-ზე 24/7 მუშაობის უზრუნველყოფა

Render-ის უფასო ვერსიაზე აპლიკაცია 15 წუთი ინაქტიურობის შემდეგ იძინება. ამის გადასაჭრელად გამოყენებულია რამდენიმე მიდგომა:

#### 1. ინტეგრირებული Self-Ping სისტემა
- ბოტი ავტომატურად აგზავნის ping-ებს თავის თავზე ყოველ 5 წუთში
- მუშაობს ორი endpoint-ით: `/` და `/ping`

#### 2. ცალკე Pinger სერვისი (რეკომენდებული)
- `render.yml`-ში კონფიგურირებულია ორი სერვისი
- `bot-pinger` სერვისი მხოლოდ ბოტს აგზავნის ping-ებს
- უფრო ეფექტურია ვიდრე self-ping

#### 3. გარე მონიტორინგი (საუკეთესო)
გამოიყენეთ უფასო მონიტორინგ სერვისები:
- **UptimeRobot**: https://uptimerobot.com/
- **Cron-job.org**: https://cron-job.org/
- **Pingdom**: https://tools.pingdom.com/

**კონფიგურაცია:**
- URL: `https://your-bot.onrender.com/uptime`
- ინტერვალი: 5-10 წუთი
- მეთოდი: GET

#### 4. Health Check Endpoints
ბოტი გთავაზობთ რამდენიმე endpoint-ს მონიტორინგისთვის:
- `/` - ძირითადი სტატუსი
- `/ping` - მარტივი ping
- `/health` - სრული სისტემის სტატუსი
- `/uptime` - მონიტორინგისთვის

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
3. Google Sheets-ისთვის შექმენი service account და ატვირთე `credentials.json`.
4. გაუშვი ბოტი:
   ```bash
   python main.py
   ```

### Render-ზე გაშვება
- ატვირთე პროექტი GitHub-ზე და დააკონექტე Render-ზე.
- დაამატე ყველა საჭირო გარემოს ცვლადი Render-ის Settings-ში.
- **რეკომენდებული**: დაამატე გარე მონიტორინგი UptimeRobot-ით.
- სერვისი ავტომატურად გაეშვება და ექნება საჯარო მისამართი.

### ტესტირება Payze-ს Sandbox-ით
- გამოიყენე ტესტ გასაღებები და Merchant ID.
- ტესტ ბარათის მონაცემები:
  - ბარათის ნომერი: 4977 0000 0000 3436
  - ვადა: ნებისმიერი მომავალი თვე/წელი
  - CVC: ნებისმიერი 3-ნიშნა
- გადახდის შემდეგ ბოტი გამოგიგზავნის შეტყობინებას.

---

## 🇬🇧 English Instructions

### Features
- 🛒 Receive orders in Telegram
- 💳 Payze payments (Sandbox & Production)
- 📄 Save orders to Google Sheets
- 🔔 Automatic notification after payment confirmation
- 🌐 Easy deployment on Render
- ⚡ 24/7 operation on Render's free tier

### Keeping the Bot Awake on Render Free Tier

Render's free tier puts applications to sleep after 15 minutes of inactivity. Multiple approaches are implemented to solve this:

#### 1. Integrated Self-Ping System
- Bot automatically pings itself every 5 minutes
- Works with two endpoints: `/` and `/ping`

#### 2. Separate Pinger Service (Recommended)
- Two services configured in `render.yml`
- `bot-pinger` service only sends pings to the bot
- More effective than self-ping

#### 3. External Monitoring (Best)
Use free monitoring services:
- **UptimeRobot**: https://uptimerobot.com/
- **Cron-job.org**: https://cron-job.org/
- **Pingdom**: https://tools.pingdom.com/

**Configuration:**
- URL: `https://your-bot.onrender.com/uptime`
- Interval: 5-10 minutes
- Method: GET

#### 4. Health Check Endpoints
Bot provides several endpoints for monitoring:
- `/` - Main status
- `/ping` - Simple ping
- `/health` - Full system status
- `/uptime` - For monitoring

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
3. For Google Sheets, create a service account and upload `credentials.json`.
4. Run the bot:
   ```bash
   python main.py
   ```

### Deploying on Render
- Push your project to GitHub and connect it to Render.
- Add all required environment variables in Render Settings.
- **Recommended**: Add external monitoring with UptimeRobot.
- The service will start automatically and have a public URL.

### Testing with Payze Sandbox
- Use test API key and Merchant ID.
- Test card details:
  - Card number: 4977 0000 0000 3436
  - Expiry: any future month/year
  - CVC: any 3 digits
- After payment, the bot will send you a confirmation message.
