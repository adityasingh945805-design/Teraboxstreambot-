import os
import json
import time
import requests
import telebot
from telebot import types
from threading import Thread
from flask import Flask

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8930055066:AAGBiKXyZolKqB3Kv98LLEpLsFgvvKx-OOo"
BOT_USERNAME = "Mystreamterabot"
ADMIN_ID = 7712648594
UPI_ID = "9458050517@kotakbank"

JOIN_CHANNEL_INVITE = "https://t.me/+3H677HppeqQzMjd1"
PACK_10K_PRIVATE_LINK = "https://t.me/kvjuufgv"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
DATA_FILE = "bot_data.json"

default_data = {
    "files": {},
    "users": [],
    "premium": {},
    "force_sub": ["news18backup", "GETSUPPORT99"],
    "balances": {},
    "referrals": {},
    "stats": {"total_views": 0, "total_payout": 0}
}

# --- DATABASE MANAGEMENT ---
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data.copy()
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return default_data.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- VERIFICATION HELPERS ---
def is_subscribed(user_id):
    for ch in db.get("force_sub", []):
        try:
            ch_clean = ch.replace("@", "")
            member = bot.get_chat_member(f"@{ch_clean}", user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            continue
    return True

def is_vip(user_id):
    u_str = str(user_id)
    if u_str in db.get("premium", {}):
        exp = db["premium"][u_str]
        if exp == "lifetime" or (isinstance(exp, (int, float)) and exp > time.time()):
            return True
    return False

# --- TELEGRAM BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    u_str = str(uid)
    args = message.text.split()

    # User registration & Referral handler
    if uid not in db["users"]:
        db["users"].append(uid)
        db["balances"][u_str] = db["balances"].get(u_str, 0.0)
        
        if len(args) > 1 and args[1].startswith("ref_"):
            ref_by = args[1].replace("ref_", "")
            if ref_by != u_str and ref_by not in db.get("referrals", {}).get(u_str, []):
                db.setdefault("referrals", {}).setdefault(ref_by, []).append(u_str)
                db["balances"][ref_by] = db["balances"].get(ref_by, 0.0) + 5.0
                try:
                    bot.send_message(int(ref_by), "🎉 Naya Referral Jud Gaya! Aapke wallet me ₹5.00 add kar diye gaye hain.")
                except Exception:
                    pass
        save_data(db)

    # Force Subscription Check
    if not is_subscribed(uid):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ch in db.get("force_sub", []):
            ch_clean = ch.replace("@", "")
            markup.add(types.InlineKeyboardButton(f"📢 Join Channel", url=f"https://t.me/{ch_clean}"))
        markup.add(types.InlineKeyboardButton("✅ Joined / Check Sub", callback_data="check_sub"))
        bot.send_message(
            uid,
            "⚠️ **Bot access karne ke liye kripya pehle official channels join karein:**",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # Deep Link Handler (File Direct Access)
    if len(args) > 1 and not args[1].startswith("ref_"):
        file_code = args[1]
        if file_code in db.get("files", {}):
            f_info = db["files"][file_code]
            if f_info.get("premium_only", False) and not is_vip(uid):
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⭐ Buy VIP", callback_data="buy_vip"))
                bot.send_message(uid, "🔒 Ye video/link sirf **VIP Members** ke liye locked hai!\nVIP unlock karne ke liye niche button dabayein.", reply_markup=markup, parse_mode="Markdown")
                return
            
            db["stats"]["total_views"] = db["stats"].get("total_views", 0) + 1
            save_data(db)
            bot.send_message(uid, f"🎬 **Aapka Video/File Link Ready Hai:**\n\n🔗 {f_info['link']}", parse_mode="Markdown")
            return

    # Main Start Menu
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💎 VIP Membership", callback_data="buy_vip"),
        types.InlineKeyboardButton("💰 Refer & Earn", callback_data="refer_earn"),
        types.InlineKeyboardButton("💳 My Wallet", callback_data="my_wallet"),
        types.InlineKeyboardButton("📦 10,000+ Videos Pack", callback_data="pack_10k"),
        types.InlineKeyboardButton("💬 Support Team", url="https://t.me/GETSUPPORT99")
    )

    user_first_name = message.from_user.first_name if message.from_user.first_name else "User"
    bot.send_message(
        uid,
        f"👋 **Namaste {user_first_name}!**\n\n"
        "🚀 **Fast TeraBox Direct Stream & Download Bot** me aapka swagat hai.\n\n"
        "✨ **Features:**\n"
        "• Koi bhi TeraBox URL bhejein aur streaming link payein.\n"
        "• Har referral par ₹5.00 kamayein.\n"
        "• High speed downloading & instant fast stream.\n\n"
        "Niche diye gaye options me se select karein 👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    u_str = str(uid)

    if call.data == "check_sub":
        if is_subscribed(uid):
            bot.answer_callback_query(call.id, "✅ Verified! Access Granted.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Aapne abhi tak channels join nahi kiye!", show_alert=True)

    elif call.data == "buy_vip":
        text = (
            "👑 **VIP MEMBERSHIP PLANS**\n\n"
            "⚡ 3 Days VIP — ₹49\n"
            "👑 1 Month VIP — ₹99\n"
            "♾️ Lifetime VIP — ₹249\n\n"
            f"💵 **UPI ID:** `{UPI_ID}`\n\n"
            "Payment complete hone ke baad payment screenshot aur UTR/Ref number **@GETSUPPORT99** par bhejein."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Send Proof to Support", url="https://t.me/GETSUPPORT99"))
        bot.send_message(uid, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "refer_earn":
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        count = len(db.get("referrals", {}).get(u_str, []))
        text = (
            "💰 **REFER & EARN SYSTEM**\n\n"
            "Apne dosto ko invite karein aur per refer **₹5.00** earn karein!\n\n"
            f"👥 Total Friends Joined: **{count}**\n"
            f"🔗 Aapka Referral Link:\n`{ref_link}`"
        )
        bot.send_message(uid, text, parse_mode="Markdown")

    elif call.data == "my_wallet":
        bal = db["balances"].get(u_str, 0.0)
        text = (
            "💳 **MY WALLET DASHBOARD**\n\n"
            f"💰 Available Balance: **₹{bal:.2f}**\n"
            "📌 Min 1st Withdrawal: ₹50\n\n"
            "Payout lene ke liye balance reach hone par Support ko message karein."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏧 Request Withdrawal", url="https://t.me/GETSUPPORT99"))
        bot.send_message(uid, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "pack_10k":
        text = (
            "🔥 **10,000+ DIRECT VIDEOS PACK ACCESS**\n\n"
            "Price: **₹99 Only**\n"
            f"Pay to UPI: `{UPI_ID}`\n\n"
            "Payment ke turant baad screenshot @GETSUPPORT99 par send karein VIP access link ke liye."
        )
        bot.send_message(uid, text, parse_mode="Markdown")

# --- TERABOX LINK EXTRACTOR ---
@bot.message_handler(func=lambda m: any(domain in m.text.lower() for domain in ["terabox", "1024tera", "terafileshare", "terashare"]))
def handle_terabox_links(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        bot.reply_to(message, "⚠️ Link download karne ke liye pehle `/start` dabakar channels join karein.")
        return
    
    url = message.text.strip()
    wait_msg = bot.reply_to(message, "⏳ Link generate ho raha hai, kripya 2 second wait karein...")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("▶️ Fast Stream Online", url=url),
        types.InlineKeyboardButton("⚡ High Speed Download Link", url=url)
    )
    
    bot.edit_message_text(
        "✅ **Link Successfully Processed!**\n\nNiche button par click karke play ya download karein:",
        chat_id=message.chat.id,
        message_id=wait_msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# --- ADMIN PANEL ---
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    u_count = len(db.get("users", []))
    views = db["stats"].get("total_views", 0)
    bot.reply_to(message, f"📊 **Bot Real-Time Stats:**\n\n👤 Total Active Users: `{u_count}`\n👁️ Processed Views: `{views}`", parse_mode="Markdown")

# --- EXECUTION ENTRY POINT ---
if __name__ == "__main__":
    print("Starting Flask Webhook Server...")
    keep_alive()
    print("Bot Polling Initialized Successfully...")
    bot.infinity_polling(skip_pending=True)
