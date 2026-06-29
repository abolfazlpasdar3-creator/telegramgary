import telebot
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq
from collections import defaultdict

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
        bot.send_message(message.chat.id, "❌ دسترسی ندارید!")
        return
    text = """🛠️ **پنل مدیریت**
دستورات موجود:
/addconfig → اضافه کردن کانفیگ جدید
/listconfigs → نمایش لیست کانفیگ‌ها
/delconfig → حذف کانفیگ
/broadcast → پیام همگانی
/stats → آمار روزانه و هفتگی"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ================== آمار ==================
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = len(users)
    total_balance = sum(users.values())

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    daily_sales = {"unlimited": 0, "volume30": 0, "volume50": 0}
    weekly_sales = {"unlimited": 0, "volume30": 0, "volume50": 0}
    daily_revenue = 0
    weekly_revenue = 0

    for user_purchases in purchases.values():
        for p in user_purchases:
            if not isinstance(p, dict) or 'date' not in p:
                continue
            try:
                sale_date = datetime.fromisoformat(p['date']).date()
                price = p.get('price', 0)

                if sale_date == today:
                    daily_revenue += price
                    if "نامحدود" in p.get('name', ''): daily_sales["unlimited"] += 1
                    elif "۳۰ گیگ" in p.get('name', ''): daily_sales["volume30"] += 1
                    elif "۵۰ گیگ" in p.get('name', ''): daily_sales["volume50"] += 1

                if sale_date >= week_ago:
                    weekly_revenue += price
                    if "نامحدود" in p.get('name', ''): weekly_sales["unlimited"] += 1
                    elif "۳۰ گیگ" in p.get('name', ''): weekly_sales["volume30"] += 1
                    elif "۵۰ گیگ" in p.get('name', ''): weekly_sales["volume50"] += 1
            except:
                continue

    text = f"""📊 **آمار ربات**
👥 تعداد کل کاربران: {total_users:,}
💰 مجموع شارژ کیف پول‌ها: {total_balance:,} تومان

📅 **امروز**
• نامحدود: {daily_sales['unlimited']} عدد
• ۳۰ گیگ: {daily_sales['volume30']} عدد
• ۵۰ گیگ: {daily_sales['volume50']} عدد
💵 درآمد امروز: {daily_revenue:,} تومان

📆 **۷ روز اخیر**
• نامحدود: {weekly_sales['unlimited']} عدد
• ۳۰ گیگ: {weekly_sales['volume30']} عدد
• ۵۰ گیگ: {weekly_sales['volume50']} عدد
💵 درآمد هفتگی: {weekly_revenue:,} تومان"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ================== پیام همگانی ==================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "📢 پیام همگانی را ارسال کنید:")
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    success = 0
    failed = 0
    for user_id in list(users.keys()):
        try:
            bot.send_message(int(user_id), message.text, parse_mode='Markdown')
            success += 1
        except:
            failed += 1
    bot.send_message(ADMIN_ID, f"✅ پیام همگانی ارسال شد!\n\nموفق: {success}\nناموفق: {failed}\nکل کاربران: {len(users)}")

# ================== مدیریت کانفیگ‌ها ==================
current_config_type = None   # ← این خط خیلی مهم است

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
        bot.send_message(message.chat.id, f"حالا کانفیگ(ها) را ارسال کنید (هر خط یکی):\nبرای پایان /done")
        bot.register_next_step_handler(message, collect_configs)
    except:
        bot.send_message(message.chat.id, "❌ عدد وارد کنید!")

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

@bot.message_handler(commands=['listconfigs'])
def list_configs(message):
    if message.from_user.id != ADMIN_ID: return
    text = "📋 **کانفیگ‌های موجود:**\n\n"
    for key, pool in configs_pool.items():
        name = {"unlimited": "نامحدود", "volume30": "۳۰ گیگ", "volume50": "۵۰ گیگ"}[key]
        text += f"**{name}**: {len(pool)} عدد\n"
        if pool:
            text += "نمونه: " + pool[0][:50] + "...\n\n"
        else:
            text += "خالی\n\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['delconfig'])
def del_config(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "نوع کانفیگ را انتخاب کنید:\n1. unlimited\n2. volume30\n3. volume50")
    bot.register_next_step_handler(message, process_del_type)

def process_del_type(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        choice = int(message.text.strip())
        types = {1: "unlimited", 2: "volume30", 3: "volume50"}
        if choice not in types:
            bot.send_message(message.chat.id, "❌ انتخاب اشتباه!")
            return
        key = types[choice]
        if not configs_pool[key]:
            bot.send_message(message.chat.id, "این دسته خالی است!")
            return
        bot.send_message(message.chat.id, f"تعداد {len(configs_pool[key])} کانفیگ موجود است.\n\nبرای حذف همه بنویس `all`\nیا شماره کانفیگ را بنویس (از ۱ شروع می‌شود)")
        bot.register_next_step_handler(message, lambda m: do_delete(m, key))
    except:
        bot.send_message(message.chat.id, "❌ عدد وارد کنید!")

def do_delete(message, key):
    if message.from_user.id != ADMIN_ID: return
    if message.text.lower() == 'all':
        count = len(configs_pool[key])
        configs_pool[key].clear()
        bot.send_message(message.chat.id, f"✅ همه {count} کانفیگ حذف شد.")
    else:
        try:
            idx = int(message.text) - 1
            if 0 <= idx < len(configs_pool[key]):
                configs_pool[key].pop(idx)
                bot.send_message(message.chat.id, "✅ کانفیگ حذف شد.")
            else:
                bot.send_message(message.chat.id, "❌ شماره اشتباه!")
        except:
            bot.send_message(message.chat.id, "❌ ورودی اشتباه!")
    save_data()
    # ================== ریپلای ادمین (برای پشتیبانی و شارژ) ==================
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
            bot.send_message(ADMIN_ID, f"✅ شارژ {amount:,} تومان انجام شد.")
            charge_requests.pop(reply_id, None)
            save_data()
        return

    # پاسخ به پیام پشتیبانی
    if reply_id in support_requests:
        user_id = support_requests[reply_id]
        bot.send_message(int(user_id), f"📩 پاسخ پشتیبانی:\n\n{message.text}")
        support_requests.pop(reply_id, None)
        save_data()
        bot.send_message(ADMIN_ID, "✅ پاسخ به کاربر ارسال شد.")
        return

def do_delete(message, key):
    if message.from_user.id != ADMIN_ID: return
    if message.text.lower() == 'all':
        count = len(configs_pool[key])
        configs_pool[key].clear()
        bot.send_message(message.chat.id, f"✅ همه {count} کانفیگ حذف شد.")
    else:
        try:
            idx = int(message.text) - 1
            if 0 <= idx < len(configs_pool[key]):
                removed = configs_pool[key].pop(idx)
                bot.send_message(message.chat.id, f"✅ کانفیگ حذف شد.")
            else:
                bot.send_message(message.chat.id, "❌ شماره اشتباه!")
        except:
            bot.send_message(message.chat.id, "❌ ورودی اشتباه!")
    save_data()

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
    bot.send_message(ADMIN_ID, "روی رسید فوروارد شده ریپلای کنید و مبلغ را بنویسید.")
    bot.send_message(message.chat.id, "✅ رسید به ادمین ارسال شد.")

# ================== خرید از استخر ==================
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
    bot.send_message(message.chat.id, "کانفیگ مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_callback(call):
    key = call.data.split('_')[1]
    prices = {"unlimited": 299000, "volume30": 240000, "volume50": 400000}
    names = {"unlimited": "کانفیگ نامحدود", "volume30": "کانفیگ ۳۰ گیگ", "volume50": "کانفیگ ۵۰ گیگ"}
    
    price = prices[key]
    name = names[key]
    user_id = str(call.from_user.id)

    if users.get(user_id, 0) < price:
        bot.answer_callback_query(call.id, "❌ موجودی کافی نیست!", show_alert=True)
        return

    if not configs_pool[key]:
        bot.answer_callback_query(call.id, "❌ فعلاً این نوع کانفیگ موجود نیست!", show_alert=True)
        bot.send_message(ADMIN_ID, f"⚠️ استخر {key} خالی شد!")
        return

    config_text = configs_pool[key].pop(0)

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
        f"✅ خرید موفق!\n\n📦 {name}\n\n🔑 کانفیگ:\n`{config_text}`",
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id, "خرید با موفقیت انجام شد")

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
        text += f"{i}. **{name}**\n ⏳ {days_left} روز باقی‌مانده\n\n"
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

# ================== Groq (تست مستقیم) ==================
from groq import Groq
from collections import defaultdict

client = Groq(api_key="8871062070:AAGJ6XCI4Wh0Y8TMYm3D7Mch86gEInAotW8")  #

user_memory = defaultdict(list)

def get_ai_response(user_id, user_message):
    user_memory[user_id].append({"role": "user", "content": user_message})
    if len(user_memory[user_id]) > 10:
        user_memory[user_id] = user_memory[user_id][-10:]

    system_prompt = """تو یک پشتیبانی حرفه‌ای فروش کانفیگ V2Ray هستی.
تمرکز روی راهنمای اتصال اندروید و آیفون."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id])

    try:
        chat = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=700,
        )
        response = chat.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": response})
        return response
    except Exception as e:
        print("Groq Error:", str(e))
        return "❌ خطا در اتصال به هوش مصنوعی."
# پشتیبانی
@bot.message_handler(func=lambda m: m.text == '🆘 پشتیبانی')
def support(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("💬 چت با هوش مصنوعی", callback_data="ai_chat"))
    markup.add(telebot.types.InlineKeyboardButton("👨‍💼 ارسال به ادمین", callback_data="to_admin"))
    bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ai_chat")
def start_ai_chat(call):
    bot.send_message(call.message.chat.id, "✅ سوالت رو بنویس:")
    bot.register_next_step_handler(call.message, ai_chat_handler)

def ai_chat_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_ai_response(str(message.from_user.id), message.text)
    bot.send_message(message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data == "to_admin")
def start_to_admin(call):
    bot.send_message(call.message.chat.id, "✅ پیام خود را بنویسید:")
    bot.register_next_step_handler(call.message, to_admin_handler)

def to_admin_handler(message):
    forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    support_requests[str(forwarded.message_id)] = str(message.from_user.id)
    save_data()
    bot.send_message(message.chat.id, "✅ پیام شما به ادمین ارسال شد.")

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
            bot.send_message(ADMIN_ID, f"✅ شارژ {amount:,} تومان انجام شد.")
            charge_requests.pop(reply_id, None)
            save_data()
        return

    # پاسخ به پشتیبانی
    if reply_id in support_requests:
        user_id = support_requests[reply_id]
        bot.send_message(int(user_id), f"📩 پاسخ پشتیبانی:\n\n{message.text}")
        support_requests.pop(reply_id, None)
        save_data()
        bot.send_message(ADMIN_ID, "✅ پاسخ به کاربر ارسال شد.")
        return

print("✅ ربات با موفقیت اجرا شد...")
bot.infinity_polling(skip_pending=True)
