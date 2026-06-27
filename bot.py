import telebot
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5897751861
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "bot_data.json"
CARD_NUMBER = "5022291344612641"

# ================== بارگذاری اطلاعات ==================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            data = {}
else:
    data = {}

users = data.get("users", {})
purchases = data.get("purchases", {})
charge_requests = data.get("charge_requests", {})
support_requests = data.get("support_requests", {})

configs_pool = data.get("configs_pool", {
    "unlimited": [],
    "volume30": [],
    "volume50": []
})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "users": users,
            "purchases": purchases,
            "charge_requests": charge_requests,
            "support_requests": support_requests,
            "configs_pool": configs_pool
        }, f, ensure_ascii=False, indent=2)

# ================== پنل ادمین ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = """🛠️ **پنل مدیریت**
دستورات:
• /addconfig → اضافه کردن کانفیگ
• /listconfigs → لیست کانفیگ‌ها
• /delconfig → حذف کانفیگ
• /broadcast → پیام همگانی
• /stats → آمار"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ================== مدیریت استخر ==================
@bot.message_handler(commands=['addconfig'])
def add_config(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "نوع کانفیگ را انتخاب کنید:\n1. unlimited\n2. volume30\n3. volume50")
    bot.register_next_step_handler(message, process_config_type)

def process_config_type(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        choice = int(message.text.strip())
        types = {1: "unlimited", 2: "volume30", 3: "volume50"}
        if choice not in types:
            bot.send_message(message.chat.id, "❌ انتخاب اشتباه!")
            return
        global current_config_type
        current_config_type = types[choice]
        bot.send_message(message.chat.id, f"کانفیگ‌های {current_config_type} را ارسال کنید (هر خط یکی):\nبرای پایان /done")
        bot.register_next_step_handler(message, collect_configs)
    except:
        bot.send_message(message.chat.id, "❌ عدد وارد کنید!")

current_config_type = None

def collect_configs(message):
    global current_config_type
    if message.from_user.id != ADMIN_ID: return
    if message.text == '/done':
        bot.send_message(message.chat.id, f"✅ {len(configs_pool[current_config_type])} کانفیگ برای {current_config_type} ذخیره شد.")
        save_data()
        return
    configs_pool[current_config_type].append(message.text.strip())
    bot.send_message(message.chat.id, f"✅ اضافه شد. تعداد فعلی: {len(configs_pool[current_config_type])}")
    bot.register_next_step_handler(message, collect_configs)

# ================== خرید کانفیگ (اصلی) ==================
@bot.message_handler(func=lambda m: m.text == '🛒 خرید کانفیگ')
def buy_config(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    options = {
        "unlimited": "نامحدود - 299,000 تومان",
        "volume30": "۳۰ گیگ - 240,000 تومان",
        "volume50": "۵۰ گیگ - 400,000 تومان"
    }
    for key, text in options.items():
        markup.add(telebot.types.InlineKeyboardButton(text, callback_data=f"buy_{key}"))
    bot.send_message(message.chat.id, "نوع کانفیگ مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_callback(call):
    key = call.data.split('_')[1]
    prices = {"unlimited": 299000, "volume30": 240000, "volume50": 400000}
    names = {"unlimited": "کانفیگ نامحدود", "volume30": "کانفیگ ۳۰ گیگ", "volume50": "کانفیگ ۵۰ گیگ"}
    
    price = prices[key]
    name = names[key]
    user_id = str(call.from_user.id)

    if users.get(user_id, 0) < price:
        bot.answer_callback_query(call.id, "❌ موجودی کیف پول شما کافی نیست!", show_alert=True)
        return

    if not configs_pool[key]:
        bot.answer_callback_query(call.id, "❌ فعلاً این نوع کانفیگ موجود نیست", show_alert=True)
        bot.send_message(ADMIN_ID, f"⚠️ استخر {key} خالی شد!")
        return

    # برداشتن از استخر
    config_text = configs_pool[key].pop(0)

    # ثبت خرید
    purchases.setdefault(user_id, []).append({
        "name": name,
        "config": config_text,
        "date": datetime.now().isoformat(),
        "price": price
    })

    users[user_id] -= price
    save_data()

    bot.send_message(
        call.message.chat.id,
        f"✅ خرید موفق!\n\n"
        f"📦 {name}\n\n"
        f"🔑 کانفیگ:\n`{config_text}`",
        parse_mode='Markdown'
    )

    bot.send_message(
        ADMIN_ID,
        f"🛒 خرید جدید\nکاربر: {user_id}\nنوع: {name}\nقیمت: {price:,} تومان"
    )
    bot.answer_callback_query(call.id, "خرید با موفقیت انجام شد ✓")

# ================== شارژ کیف پول ==================
@bot.message_handler(func=lambda m: m.text == '💰 شارژ کیف پول')
def charge_wallet(message):
    bot.send_message(message.chat.id, f"برای شارژ حساب، رسید پرداخت را ارسال کنید.\n\n💳 شماره کارت:\n`{CARD_NUMBER}`", parse_mode='Markdown')

@bot.message_handler(content_types=['photo', 'document'])
def handle_receipt(message):
    sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    charge_requests[str(sent.message_id)] = str(message.from_user.id)
    save_data()
    bot.send_message(ADMIN_ID, "روی عکس/فایل رسید ریپلای کنید و مبلغ را بنویسید.")
    bot.send_message(message.chat.id, "✅ رسید به ادمین ارسال شد. منتظر تأیید باشید.")

# ================== ریپلای ادمین (شارژ + پشتیبانی) ==================
@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == ADMIN_ID)
def admin_reply(message):
    text = message.text.strip()
    reply_id = str(message.reply_to_message.message_id)

    # شارژ کیف پول
    if text.isdigit():
        amount = int(text)
        user_id = charge_requests.get(reply_id)
        if user_id:
            users[user_id] = users.get(user_id, 0) + amount
            save_data()
            bot.send_message(int(user_id), f"✅ کیف پول شارژ شد!\n💰 {amount:,} تومان\nموجودی فعلی: {users[user_id]:,} تومان")
            bot.send_message(ADMIN_ID, f"✅ شارژ {amount:,} تومان برای کاربر {user_id} انجام شد.")
            charge_requests.pop(reply_id, None)
            save_data()
        return

    # پاسخ پشتیبانی
    if reply_id in support_requests:
        user_id = support_requests[reply_id]
        bot.send_message(int(user_id), f"📩 پاسخ پشتیبانی:\n\n{message.text}")
        support_requests.pop(reply_id, None)
        save_data()
        bot.send_message(ADMIN_ID, "✅ پاسخ ارسال شد.")
        return

# ================== بقیه توابع (موجودی، سرویس‌ها، آموزش و ...) ==================
@bot.message_handler(func=lambda m: m.text == '👤 موجودی من')
def show_balance(message):
    user_id = str(message.from_user.id)
    balance = users.get(user_id, 0)
    bot.send_message(message.chat.id, f"💰 موجودی کیف پول شما:\n\n{balance:,} تومان")

@bot.message_handler(func=lambda m: m.text == '🛍️ سرویس‌های من')
def my_services(message):
    user_id = str(message.from_user.id)
    if not purchases.get(user_id):
        bot.send_message(message.chat.id, "شما هنوز هیچ سرویسی خریداری نکرده‌اید.")
        return
    
    text = "🛍️ **سرویس‌های خریداری شده شما:**\n\n"
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for i, service in enumerate(purchases[user_id], 1):
        name = service.get('name', 'کانفیگ') if isinstance(service, dict) else str(service)
        days_left = "نامشخص"
        if isinstance(service, dict) and 'date' in service:
            try:
                d = datetime.fromisoformat(service['date'])
                days_left = max(0, (d + timedelta(days=30) - datetime.now()).days)
            except:
                pass
        text += f"{i}. **{name}**\n⏳ {days_left} روز باقی‌مانده\n\n"
        markup.add(telebot.types.InlineKeyboardButton(f"📋 کپی کانفیگ {i}", callback_data=f"copy_{user_id}_{i-1}"))
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('copy_'))
def copy_config(call):
    _, user_id, idx = call.data.split('_')
    idx = int(idx)
    service = purchases.get(user_id, [])[idx]
    config = service.get('config', str(service)) if isinstance(service, dict) else str(service)
    bot.send_message(call.message.chat.id, f"`{config}`", parse_mode='Markdown')

# آموزش و پشتیبانی (بدون تغییر)
@bot.message_handler(func=lambda m: m.text == '📚 آموزش اتصال')
def education(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("📱 اندروید", callback_data="edu_android"))
    markup.add(telebot.types.InlineKeyboardButton("🍎 آیفون", callback_data="edu_ios"))
    bot.send_message(message.chat.id, "سیستم عامل خود را انتخاب کنید:", reply_markup=markup)

# ... (بقیه توابع آموزش و پشتیبانی را همان قبلی نگه دار)

@bot.message_handler(func=lambda m: m.text == '🆘 پشتیبانی')
def support(message):
    bot.send_message(message.chat.id, "لطفاً مشکل خود را بنویسید:")
    bot.register_next_step_handler(message, send_support_message)

def send_support_message(message):
    forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    support_requests[str(forwarded.message_id)] = str(message.from_user.id)
    save_data()
    bot.send_message(message.chat.id, "✅ پیام شما برای پشتیبانی ارسال شد.")

print("✅ ربات با موفقیت اجرا شد...")
bot.infinity_polling(skip_pending=True)
