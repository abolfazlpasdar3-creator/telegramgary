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

# استخر کانفیگ‌ها
configs_pool = data.get("configs_pool", {
    "unlimited": [],
    "volume30": [],
    "volume50": []
})

config_history = data.get("config_history", {})
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "users": users,
            "purchases": purchases,
            "pending_purchases": pending_purchases,
            "charge_requests": charge_requests,
            "support_requests": support_requests,
            "configs_pool": configs_pool,
            "config_history": config_history
        }, f, ensure_ascii=False, indent=2)
        # ================== استخر کانفیگ‌ها ==================
configs_pool = data.get("configs_pool", {
    "unlimited": [],
    "volume30": [],
    "volume50": []
})

config_history = data.get("config_history", {})  # جلوگیری از ارسال تکراری
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


# ================== پنل ادمین ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ دسترسی ندارید!")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast"),
        telebot.types.InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("➕ اضافه کردن کانفیگ", callback_data="admin_addconfig"),
        telebot.types.InlineKeyboardButton("📋 لیست کانفیگ‌ها", callback_data="admin_listconfigs")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🗑️ حذف کانفیگ", callback_data="admin_delconfig")
    )
    
    bot.send_message(message.chat.id, "🛠️ **پنل مدیریت**", reply_markup=markup, parse_mode='Markdown')@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "admin_broadcast":
        bot.send_message(call.message.chat.id, "📢 پیام همگانی را بنویسید:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_broadcast)
    
    elif call.data == "admin_stats":
        show_stats(call.message)  # تابع آمار
    
    elif call.data == "admin_addconfig":
        add_config(call.message)
    
    elif call.data == "admin_listconfigs":
        list_configs(call.message)
    
    elif call.data == "admin_delconfig":
        del_config(call.message)

# ================== آمار (روزانه + هفتگی) ==================
@bot.message_handler(func=lambda m: m.text == '📊 آمار')
def show_stats(message):
    if message.from_user.id != ADMIN_ID:
        return

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
                if "نامحدود" in p.get('name', ''):
                    price = 299000
                elif "۳۰ گیگ" in p.get('name', ''):
                    price = 240000
                elif "۵۰ گیگ" in p.get('name', ''):
                    price = 400000
                else:
                    price = 0
                
                if sale_date == today:
                    daily_revenue += price
                    if "نامحدود" in p.get('name', ''):
                        daily_sales["unlimited"] += 1
                    elif "۳۰ گیگ" in p.get('name', ''):
                        daily_sales["volume30"] += 1
                    elif "۵۰ گیگ" in p.get('name', ''):
                        daily_sales["volume50"] += 1
                
                if sale_date >= week_ago:
                    weekly_revenue += price
                    if "نامحدود" in p.get('name', ''):
                        weekly_sales["unlimited"] += 1
                    elif "۳۰ گیگ" in p.get('name', ''):
                        weekly_sales["volume30"] += 1
                    elif "۵۰ گیگ" in p.get('name', ''):
                        weekly_sales["volume50"] += 1
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
configs = {
    "unlimited": {"name": "کانفیگ نامحدود", "price": 299000, "data": "v2ray://نامحدود-اینجا-بگذار"},
    "volume30": {"name": "کانفیگ حجمی ۳۰ گیگ", "price": 240000, "data": "v2ray://۳۰-گیگ-اینجا-بگذار"},
    "volume50": {"name": "کانفیگ حجمی ۵۰ گیگ", "price": 400000, "data": "v2ray://۵۰-گیگ-اینجا-بگذار"}
}

CARD_NUMBER = "5022291344612641"
# ================== مدیریت استخر کانفیگ توسط ادمین ==================
@bot.message_handler(commands=['addconfig'])
def add_config(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "نوع کانفیگ را انتخاب کنید:\n\n1. unlimited\n2. volume30\n3. volume50\n\nمثال: `1`")
    bot.register_next_step_handler(message, process_config_type)

def process_config_type(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        choice = int(message.text.strip())
        types = {1: "unlimited", 2: "volume30", 3: "volume50"}
        if choice not in types:
            bot.send_message(message.chat.id, "❌ انتخاب اشتباه!")
            return
        global current_config_type
        current_config_type = types[choice]
        bot.send_message(message.chat.id, f"حالا کانفیگ(ها) را ارسال کنید (هر خط یکی):\n\nبرای پایان /done")
        bot.register_next_step_handler(message, collect_configs)
    except:
        bot.send_message(message.chat.id, "❌ لطفاً عدد وارد کنید!")

current_config_type = None

def collect_configs(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == '/done':
        bot.send_message(message.chat.id, f"✅ {len(configs_pool[current_config_type])} کانفیگ برای {current_config_type} ذخیره شد.")
        save_data()
        return
    
    configs_pool[current_config_type].append(message.text.strip())
    bot.send_message(message.chat.id, f"✅ اضافه شد. تعداد فعلی: {len(configs_pool[current_config_type])}")
    bot.register_next_step_handler(message, collect_configs)
    # ================== لیست و حذف کانفیگ ==================
@bot.message_handler(commands=['listconfigs'])
def list_configs(message):
    if message.from_user.id != ADMIN_ID:
        return
    
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
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "نوع کانفیگ را انتخاب کنید:\n1. unlimited\n2. volume30\n3. volume50")
    bot.register_next_step_handler(message, process_del_type)

def process_del_type(message):
    if message.from_user.id != ADMIN_ID:
        return
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
    if message.from_user.id != ADMIN_ID:
        return
    if message.text.lower() == 'all':
        count = len(configs_pool[key])
        configs_pool[key].clear()
        bot.send_message(message.chat.id, f"✅ همه {count} کانفیگ حذف شد.")
    else:
        try:
            idx = int(message.text) - 1
            if 0 <= idx < len(configs_pool[key]):
                removed = configs_pool[key].pop(idx)
                bot.send_message(message.chat.id, f"✅ کانفیگ حذف شد:\n{removed[:100]}...")
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
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_callback(call):
    key = call.data.split('_')[1]
    cfg = configs[key]
    user_id = str(call.from_user.id)
    
    if users.get(user_id, 0) < cfg['price']:
        bot.send_message(call.message.chat.id, "❌ موجودی کافی نیست!")
        return
    
    # چک کردن موجودی کانفیگ
    if not configs_pool[key]:
        bot.send_message(call.message.chat.id, "❌ فعلاً کانفیگ این نوع موجود نیست. لطفاً بعداً امتحان کنید.")
        bot.send_message(ADMIN_ID, f"⚠️ هشدار: استخر کانفیگ {key} خالی شد!")
        return
    
    # برداشتن یک کانفیگ از استخر
    config_text = configs_pool[key].pop(0)
    
    # ثبت خرید
    purchases.setdefault(user_id, []).append({
        "name": cfg['name'],
        "config": config_text,
        "date": datetime.now().isoformat(),
        "price": cfg['price']
    })
    
    users[user_id] = users.get(user_id, 0) - cfg['price']
    
    save_data()
    
    bot.send_message(
        call.message.chat.id,
        f"✅ خرید موفق!\n\n📦 {cfg['name']}\n\n🔑 کانفیگ:\n`{config_text}`",
        parse_mode='Markdown'
    )
    
    bot.send_message(
        ADMIN_ID,
        f"🛒 خرید جدید\nکاربر: {user_id}\nنوع: {cfg['name']}\nکانفیگ ارسال شد."
    )

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
