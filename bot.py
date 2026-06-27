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

# بارگذاری اطلاعات
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
pending_purchases = data.get("pending_purchases", {})
charge_requests = data.get("charge_requests", {})
support_requests = data.get("support_requests", {})
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "users": users,
            "purchases": purchases,
            "pending_purchases": pending_purchases,
            "charge_requests": charge_requests,
            "support_requests": support_requests
        }, f, ensure_ascii=False, indent=2)
# ================== پیام همگانی (Broadcast) ==================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    bot.send_message(message.chat.id, "📢 پیام همگانی را ارسال کنید:")
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    success = 0
    failed = 0
    
    for user_id in list(users.keys()):
        try:
            bot.send_message(int(user_id), message.text, parse_mode='Markdown')
            success += 1
        except:
            failed += 1
    
    bot.send_message(
        ADMIN_ID, 
        f"✅ پیام همگانی ارسال شد!\n\n"
        f"✅ موفق: {success}\n"
        f"❌ ناموفق: {failed}\n"
        f"👥 کل کاربران: {len(users)}"
    )
    @bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ دسترسی ندارید!")
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('📢 پیام همگانی', '📊 آمار')
    markup.add('🔙 بازگشت به منو اصلی')
    
    bot.send_message(message.chat.id, "🛠️ پنل ادمین:", reply_markup=markup)
    
configs = {
    "unlimited": {"name": "کانفیگ نامحدود", "price": 299000, "data": "v2ray://نامحدود-اینجا-بگذار"},
    "volume30": {"name": "کانفیگ حجمی ۳۰ گیگ", "price": 240000, "data": "v2ray://۳۰-گیگ-اینجا-بگذار"},
    "volume50": {"name": "کانفیگ حجمی ۵۰ گیگ", "price": 400000, "data": "v2ray://۵۰-گیگ-اینجا-بگذار"}
}

CARD_NUMBER = "5022291344612641"

# ================== منوی اصلی ==================
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🛒 خرید کانفیگ', '👤 موجودی من')
    markup.add('💰 شارژ کیف پول', '🛍️ سرویس‌های من')
    markup.add('📚 آموزش اتصال', '🆘 پشتیبانی')
    bot.send_message(message.chat.id, f"سلام {message.from_user.first_name} 👋\nبه فروشگاه کانفیگ خوش اومدی!", reply_markup=markup)

# ================== موجودی من ==================
@bot.message_handler(func=lambda m: m.text == '👤 موجودی من')
def show_balance(message):
    user_id = str(message.from_user.id)
    balance = users.get(user_id, 0)
    bot.send_message(message.chat.id, f"💰 موجودی کیف پول شما:\n\n{balance:,} تومان")

# ================== شارژ کیف پول ==================
@bot.message_handler(func=lambda m: m.text == '💰 شارژ کیف پول')
def charge_wallet(message):
    bot.send_message(message.chat.id, f"برای شارژ حساب، رسید پرداخت را ارسال کنید.\n\n💳 شماره کارت:\n`{CARD_NUMBER}`", parse_mode='Markdown')

@bot.message_handler(content_types=['photo', 'document'])
def handle_receipt(message):
    sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    charge_requests[str(sent.message_id)] = str(message.from_user.id)
    save_data()
    bot.send_message(
    ADMIN_ID,
    "روی خودِ عکس یا فایل رسید فوروارد شده ریپلای کن."
)
    bot.send_message(message.chat.id, "✅ رسید به ادمین ارسال شد.")

# ================== Reply ادمین ==================
@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == ADMIN_ID)
def admin_reply(message):
    global pending_purchases, charge_requests
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
            bot.send_message(ADMIN_ID, f"✅ شارژ {amount:,} تومان انجام شد.")
            if reply_id in charge_requests:
                del charge_requests[reply_id]
            save_data()
        return

    # ارسال کانفیگ
    # پاسخ پشتیبانی
    if reply_id in support_requests:

        user_id = support_requests[reply_id]

        bot.send_message(
            int(user_id),
            f"📩 پاسخ پشتیبانی:\n\n{message.text}"
        )

        del support_requests[reply_id]

        save_data()

        bot.send_message(
            ADMIN_ID,
            "✅ پاسخ برای کاربر ارسال شد."
        )

        return

    # ارسال کانفیگ
    if reply_id in pending_purchases:

        d = pending_purchases[reply_id]
        user_id = d["user_id"]

        users[user_id] = users.get(user_id, 0) - d["price"]

        purchases.setdefault(user_id, []).append({
            "name": d["config_name"],
            "config": message.text,
            "date": datetime.now().isoformat()
        })

        save_data()

        bot.send_message(
            int(user_id),
            f"✅ خرید موفق!\n\n📦 {d['config_name']}\n\n🔑 کانفیگ:\n`{message.text}`",
            parse_mode='Markdown'
        )

        bot.send_message(
            ADMIN_ID,
            "✅ کانفیگ ارسال شد."
        )

        del pending_purchases[reply_id]

        save_data()

# ================== خرید کانفیگ ==================
@bot.message_handler(func=lambda m: m.text == '🛒 خرید کانفیگ')
def buy_config(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for key, cfg in configs.items():
        markup.add(telebot.types.InlineKeyboardButton(f"{cfg['name']} - {cfg['price']:,} تومان", callback_data=f"buy_{key}"))
    bot.send_message(message.chat.id, "کانفیگ مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_callback(call):
    key = call.data.split('_')[1]
    cfg = configs[key]
    user_id = str(call.from_user.id)
    if users.get(user_id, 0) < cfg['price']:
        bot.send_message(call.message.chat.id, "❌ موجودی کافی نیست!")
        return
    msg = bot.send_message(ADMIN_ID, f"🛒 درخواست خرید\nکاربر: {user_id}\nکانفیگ: {cfg['name']}\nقیمت: {cfg['price']:,}\n\nReply + کانفیگ")
    pending_purchases[str(msg.message_id)] = {"user_id": user_id, "config_name": cfg['name'], "price": cfg['price']}
    save_data()
    bot.send_message(call.message.chat.id, "✅ درخواست خرید ثبت شد.")

# ================== سرویس‌های من ==================
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
        text += f"{i}. **{name}**\n   ⏳ {days_left} روز باقی‌مانده\n\n"
        markup.add(telebot.types.InlineKeyboardButton(f"📋 کپی کانفیگ {i}", callback_data=f"copy_{user_id}_{i-1}"))

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('copy_'))
def copy_config(call):
    _, user_id, idx = call.data.split('_')
    idx = int(idx)
    service = purchases.get(user_id, [])[idx]
    config = service.get('config', str(service)) if isinstance(service, dict) else str(service)
    bot.send_message(call.message.chat.id, f"`{config}`", parse_mode='Markdown')

# ================== آموزش اتصال ==================
@bot.message_handler(func=lambda m: m.text == '📚 آموزش اتصال')
def education(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("📱 اندروید", callback_data="edu_android"))
    markup.add(telebot.types.InlineKeyboardButton("🍎 آیفون", callback_data="edu_ios"))
    bot.send_message(message.chat.id, "سیستم عامل خود را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edu_'))
def edu_callback(call):
    if call.data == "edu_android":
        m = telebot.types.InlineKeyboardMarkup(row_width=1)
        m.add(telebot.types.InlineKeyboardButton("V2RayNG", callback_data="app_v2rayng"))
        m.add(telebot.types.InlineKeyboardButton("NPV Tunnel", callback_data="app_npvtunnel"))
        bot.send_message(call.message.chat.id, "برنامه اندروید:", reply_markup=m)
    else:
        m = telebot.types.InlineKeyboardMarkup(row_width=1)
        m.add(telebot.types.InlineKeyboardButton("V2Box", callback_data="app_v2box"))
        m.add(telebot.types.InlineKeyboardButton("Napster", callback_data="app_napster"))
        bot.send_message(call.message.chat.id, "برنامه آیفون:", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith('app_'))
def app_callback(call):
    bot.send_message(call.message.chat.id, f"آموزش {call.data.split('_')[1].upper()} به زودی اضافه خواهد شد.")

# پشتیبانی
@bot.message_handler(func=lambda m: m.text == '🆘 پشتیبانی')
def support(message):
    bot.send_message(
        message.chat.id,
        "لطفاً مشکل خود را بنویسید:"
    )

    bot.register_next_step_handler(
        message,
        send_support_message
    )
def send_support_message(message):

    forwarded = bot.forward_message(
        ADMIN_ID,
        message.chat.id,
        message.message_id
    )

    support_requests[str(forwarded.message_id)] = str(message.from_user.id)

    save_data()

    bot.send_message(
        message.chat.id,
        "✅ پیام شما برای پشتیبانی ارسال شد."
    )
print("✅ ربات اجرا شد...")
@bot.message_handler(func=lambda m: m.text == '📢 پیام همگانی')
def handle_broadcast_button(message):
    if message.from_user.id == ADMIN_ID:
        broadcast(message)
bot.infinity_polling(skip_pending=True)
