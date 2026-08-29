pkill -f python
cat << 'EOF' > main.py
import telebot, json, os, uuid, time, threading, urllib.parse, datetime
from telebot import types

BOT_TOKEN = "8930055066:AAGBiKXyZolKqB3Kv98LLEpLsFgvvKx-OOo"
BOT_USERNAME = "Mystreamterabot"
ADMIN_ID = 7712648594
UPI_ID = "9458050517@kotakbank"

# CHANNELS CONFIG
MAIN_CHANNEL_INVITE = "https://t.me/+3H677HppeqQzMjdl"
PACK_10K_PRIVATE_LINK = "https://t.me/kvjuufgv"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
DATA_FILE = "bot_data.json"

try:
    bot_desc = (
        "🚀 Fast Terabox & Stream Hub - Direct Fast Delivery\n\n"
        "✨ Features & Benefits:\n"
        "🎁 2 Free Trial video/photo downloads weekly for every user.\n"
        "💰 Refer & Earn: Earn ₹5.00 per referral!\n"
        "💳 1st Withdrawal ₹50 only | Next withdrawals ₹100 direct to UPI.\n\n"
        "👑 VIP Memberships:\n"
        "• ⚡ 3 Days VIP Trial — ₹49\n"
        "• 👑 1 Month VIP — ₹99\n"
        "• ♾️ Lifetime VIP — ₹249\n"
        "• 🔥 10,000+ Direct Videos Pack — ₹99\n\n"
        "📞 Official Support: @GETSUPPORT99\n"
        "🌐 Network: @Mystreamterabot"
    )
    bot.set_my_description(bot_desc)
    bot.set_my_short_description("Fast Stream Hub | 2 Free Trials Weekly | VIP Instant Delivery")
except Exception as e:
    print("Description update notice:", e)

default_data = {
    "files": {},
    "users": [],
    "premium": {},
    "force_sub": ["@news18backup", "@GETSUPPORT99"],
    "auto_delete_mins": 0,
    "stats_enabled": True,
    "weekly_usage": {},
    "pending_requests": {},
    "withdraw_requests": {},
    "used_utrs": [],
    "user_wallets": {},
    "user_sessions": {},
    "total_revenue": 0.0,
    "total_withdrawn": 0.0
}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "user_sessions" not in data: data["user_sessions"] = {}
            if "weekly_usage" not in data: data["weekly_usage"] = {}
            if "pending_requests" not in data: data["pending_requests"] = {}
            if "withdraw_requests" not in data: data["withdraw_requests"] = {}
            if "used_utrs" not in data: data["used_utrs"] = []
            if "user_wallets" not in data: data["user_wallets"] = {}
            if "force_sub" not in data: data["force_sub"] = ["@news18backup", "@GETSUPPORT99"]
            if "total_revenue" not in data: data["total_revenue"] = 0.0
            if "total_withdrawn" not in data: data["total_withdrawn"] = 0.0
    except Exception:
        data = default_data
else:
    data = default_data

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_batches = {}

PLANS = {
    "plan_49": {"name": "VIP 3 Days Trial", "amount": 49, "days": 3, "tokens": 98},
    "plan_99": {"name": "VIP 1 Month Access", "amount": 99, "days": 30, "tokens": 198},
    "plan_249": {"name": "VIP Lifetime Access", "amount": 249, "days": 365, "tokens": 498},
    "pack_10k": {"name": "10,000+ Direct Videos Pack", "amount": 99, "days": 365, "tokens": 198}
}

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_premium(user_id):
    if user_id == ADMIN_ID: return True
    exp = data["premium"].get(str(user_id))
    if exp and time.time() < exp: return True
    elif exp:
        del data["premium"][str(user_id)]
        save_data()
    return False

def get_wallet(user_id):
    uid_str = str(user_id)
    if uid_str not in data["user_wallets"]:
        data["user_wallets"][uid_str] = {
            "balance": 0.0,
            "referred_by": None,
            "total_ref": 0,
            "reward_given": False,
            "withdraw_count": 0
        }
        save_data()
    wallet = data["user_wallets"][uid_str]
    if "withdraw_count" not in wallet:
        wallet["withdraw_count"] = 0
    wallet["tokens"] = int(wallet.get("balance", 0.0) * 2)
    return wallet

def add_to_wallet(user_id, rupees_amount):
    wallet = get_wallet(user_id)
    wallet["balance"] = max(0.0, wallet.get("balance", 0.0) + rupees_amount)
    wallet["tokens"] = int(wallet["balance"] * 2)
    save_data()
    return wallet

def deduct_from_wallet(user_id, rupees_amount):
    wallet = get_wallet(user_id)
    if wallet.get("balance", 0.0) >= rupees_amount:
        wallet["balance"] -= rupees_amount
        wallet["tokens"] = int(wallet["balance"] * 2)
        save_data()
        return True
    return False

def get_min_withdraw_amount(user_id):
    wallet = get_wallet(user_id)
    if wallet.get("withdraw_count", 0) == 0:
        return 50.0
    return 100.0

def get_current_week_str():
    now = datetime.datetime.now()
    return f"{now.year}-W{now.isocalendar()[1]}"

def check_and_increment_weekly_limit(user_id):
    if is_premium(user_id):
        return True, 0
    current_week = get_current_week_str()
    if current_week not in data["weekly_usage"]:
        data["weekly_usage"] = {current_week: {}}
    user_counts = data["weekly_usage"][current_week]
    count = user_counts.get(str(user_id), 0)
    if count >= 2:
        return False, count
    user_counts[str(user_id)] = count + 1
    save_data()
    return True, count + 1

def check_force_sub(user_id):
    if not data.get("force_sub") or is_admin(user_id): return True, []
    unsub = []
    for ch in data["force_sub"]:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']: unsub.append(ch)
        except Exception: 
            continue
    return len(unsub) == 0, unsub

def auto_delete_task(chat_id, message_ids, delay_mins):
    if delay_mins <= 0: return
    def delete_job():
        time.sleep(delay_mins * 60)
        for mid in message_ids:
            try: bot.delete_message(chat_id, mid)
            except Exception: pass
    threading.Thread(target=delete_job, daemon=True).start()

def deliver_files(chat_id, code):
    file_item = data["files"].get(code)
    if not file_item: return
    files = file_item.get('files', [])
    sent_msg_ids = []
    try:
        info_msg = bot.send_message(chat_id, f"📦 Delivering {len(files)} file(s)...")
        sent_msg_ids.append(info_msg.message_id)
    except Exception: pass

    for f_data in files:
        ftype, fid, cap = f_data.get('type'), f_data.get('file_id'), f_data.get('caption', '')
        try:
            if ftype == 'video': s = bot.send_video(chat_id, fid, caption=cap)
            elif ftype == 'photo': s = bot.send_photo(chat_id, fid, caption=cap)
            elif ftype == 'document': s = bot.send_document(chat_id, fid, caption=cap)
            elif ftype == 'audio': s = bot.send_audio(chat_id, fid, caption=cap)
            sent_msg_ids.append(s.message_id)
        except Exception as ex:
            print("Deliver media item error:", ex)

    ad_mins = data.get("auto_delete_mins", 0)
    if ad_mins > 0:
        try:
            warn = bot.send_message(chat_id, f"⏳ File {ad_mins} min baad auto-delete ho jayegi.")
            sent_msg_ids.append(warn.message_id)
            auto_delete_task(chat_id, sent_msg_ids, ad_mins)
        except Exception: pass

def get_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎁 Refer & Earn", callback_data="menu_refer"),
        types.InlineKeyboardButton("👑 VIP Plans", callback_data="menu_vip")
    )
    markup.add(
        types.InlineKeyboardButton("🔥 10,000+ Direct Videos Pack (₹99)", callback_data="buy_pack_10k_none")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Withdraw Cash", callback_data="menu_withdraw"),
        types.InlineKeyboardButton("🪙 Redeem Tokens", callback_data="menu_redeem")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Official Channel", url=MAIN_CHANNEL_INVITE),
        types.InlineKeyboardButton("📞 Support / Help", url="https://t.me/GETSUPPORT99")
    )
    return markup

def show_two_choices_limit_screen(chat_id, message_id=None, code=""):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 1. Invite Friends & Earn (FREE)", callback_data="menu_refer"),
        types.InlineKeyboardButton("👑 2. Instant VIP Recharge (FAST)", callback_data=f"menu_vip_code_{code}"),
        types.InlineKeyboardButton("🪙 3. Redeem My Earned Tokens", callback_data="menu_redeem")
    )
    choice_text = (
        "🚫 <b>Weekly Free Limit Over! (2/2 Files Used)</b>\n\n"
        "Aapki is hafte ki 2 free trial files khatam ho chuki hain. Agle video/file ko access karne ke liye <b>aapke paas 2 raste hain:</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 <b>Rasta 1: Invite & Earn (FREE)</b>\n"
        "Apne dosto ko bot share karein aur har invite par <b>₹5 (10 Tokens)</b> paayein. Free tokens se VIP unlock karein!\n\n"
        "👉 <b>Rasta 2: VIP Recharge (INSTANT)</b>\n"
        "Sirf ₹49 me VIP upgrade karein aur direct bina kisi limit ke unlimited access paayein.\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Niche se apna pasandeeda tarika chunein 👇"
    )
    if message_id:
        try: bot.edit_message_text(choice_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except Exception: bot.send_message(chat_id, choice_text, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, choice_text, reply_markup=markup, parse_mode="HTML")

def show_vip_plans(chat_id, message_id=None, code="", is_strict_premium=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ ₹49 — 3 Days Trial", callback_data=f"buy_plan_49_{code}"),
        types.InlineKeyboardButton("👑 ₹99 — 1 Month Access", callback_data=f"buy_plan_99_{code}"),
        types.InlineKeyboardButton("♾️ ₹249 — Lifetime Access", callback_data=f"buy_plan_249_{code}"),
        types.InlineKeyboardButton("🔥 ₹99 — 10,000+ Direct Videos Pack", callback_data=f"buy_pack_10k_{code}"),
        types.InlineKeyboardButton("🔙 Back to Options", callback_data=f"back_limit_{code}")
    )
    vip_text = (
        "👑 <b>Select Your VIP Membership Plan</b>\n\n"
        "✨ <b>VIP Benefits:</b>\n"
        "• Unlimited high-speed file downloads\n"
        "• Direct access without weekly limit\n"
        "• High priority instant delivery\n\n"
        "Apna plan choose karein 👇"
    )
    if message_id:
        try: bot.edit_message_text(vip_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except Exception: bot.send_message(chat_id, vip_text, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, vip_text, reply_markup=markup, parse_mode="HTML")

# ADMIN ANALYTICS & STATS COMMANDS
@bot.message_handler(commands=['stats'])
def handle_stats(m):
    if not is_admin(m.from_user.id): return
    total_users = len(data.get("users", []))
    total_files = len(data.get("files", {}))
    vip_count = len(data.get("premium", {}))
    pending_orders = len(data.get("pending_requests", {}))
    pending_withdraw = len(data.get("withdraw_requests", {}))
    
    stats_msg = (
        "📊 <b>Bot Live Statistics</b>\n\n"
        f"👥 Total Registered Users: <b>{total_users}</b>\n"
        f"📁 Total Stored Files/Batches: <b>{total_files}</b>\n"
        f"👑 Active VIP Members: <b>{vip_count}</b>\n"
        f"⏳ Pending Payment Approvals: <b>{pending_orders}</b>\n"
        f"💸 Pending Withdrawals: <b>{pending_withdraw}</b>\n"
        f"🛡️ Used Anti-Fraud UTRs: <b>{len(data.get('used_utrs', []))}</b>"
    )
    bot.reply_to(m, stats_msg, parse_mode="HTML")

@bot.message_handler(commands=['premiumstats'])
def handle_premium_stats(m):
    if not is_admin(m.from_user.id): return
    pre_dict = data.get("premium", {})
    if not pre_dict:
        bot.reply_to(m, "ℹ️ No active VIP members currently.")
        return
    
    lines = ["👑 <b>Active VIP Members List:</b>\n"]
    now = time.time()
    for uid, exp in list(pre_dict.items())[:25]:
        rem_hours = max(0, int((exp - now) // 3600))
        lines.append(f"• User: <code>{uid}</code> (Expires in {rem_hours}h / {rem_hours//24}d)")
    
    bot.reply_to(m, "\n".join(lines), parse_mode="HTML")

@bot.message_handler(commands=['profit'])
def handle_profit(m):
    if not is_admin(m.from_user.id): return
    rev = data.get("total_revenue", 0.0)
    wdr = data.get("total_withdrawn", 0.0)
    net_profit = rev - wdr
    
    profit_text = (
        "💰 <b>Financial Overview & Profit</b>\n\n"
        f"💵 Total Revenue Received: <b>₹{rev:.2f}</b>\n"
        f"💸 Total Paid Withdrawals: <b>₹{wdr:.2f}</b>\n"
        f"📈 <b>Net Real Profit: ₹{net_profit:.2f}</b>\n"
        f"⏳ Pending Orders: <b>{len(data.get('pending_requests', {}))}</b>"
    )
    bot.reply_to(m, profit_text, parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(m):
    if not is_admin(m.from_user.id): return
    msg_text = m.text.replace('/broadcast', '').strip()
    if not msg_text:
        bot.reply_to(m, "Usage: <code>/broadcast Your text message here</code>", parse_mode="HTML")
        return
    
    users = data.get("users", [])
    sent, failed = 0, 0
    bot.reply_to(m, f"📢 Broadcasting message to {len(users)} users...")
    
    for u in users:
        try:
            bot.send_message(u, msg_text, parse_mode="HTML")
            sent += 1
            time.sleep(0.04)
        except Exception:
            failed += 1
            
    bot.reply_to(m, f"✅ <b>Broadcast Completed!</b>\nSent: {sent}\nFailed/Blocked: {failed}", parse_mode="HTML")

@bot.message_handler(commands=['myid'])
def handle_myid(m):
    bot.reply_to(m, f"🆔 Aapki Telegram User ID: <code>{m.from_user.id}</code>", parse_mode="HTML")

@bot.message_handler(commands=['make_pre'])
def handle_make_pre(m):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2:
        bot.reply_to(m, "Usage: <code>/make_pre FILE_CODE</code>\nExample: <code>/make_pre a1b2c3d4</code>", parse_mode="HTML")
        return
    code = args[1].strip()
    if code in data["files"]:
        data["files"][code]["is_premium"] = True
        save_data()
        bot.reply_to(m, f"🔒 <b>File <code>{code}</code> set to STRICT PREMIUM ONLY!</b>\n(Ab sirf VIP users hi ise access kar sakenge)", parse_mode="HTML")
    else:
        bot.reply_to(m, "❌ Code not found in database.")

@bot.message_handler(commands=['make_free'])
def handle_make_free(m):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2:
        bot.reply_to(m, "Usage: <code>/make_free FILE_CODE</code>", parse_mode="HTML")
        return
    code = args[1].strip()
    if code in data["files"]:
        data["files"][code]["is_premium"] = False
        save_data()
        bot.reply_to(m, f"🔓 <b>File <code>{code}</code> set to FREE/TRIAL mode!</b>", parse_mode="HTML")
    else:
        bot.reply_to(m, "❌ Code not found.")

@bot.message_handler(commands=['batch'])
def handle_batch(m):
    if not is_admin(m.from_user.id): return
    cid = m.chat.id
    user_batches[cid] = []
    bot.reply_to(m, "📦 <b>Batch Mode Started!</b>\nAb ek ek karke media (Photos/Videos) upload karein. Jab complete ho jaye toh <code>/done</code> send karein.", parse_mode="HTML")

@bot.message_handler(commands=['done'])
def handle_done(m):
    if not is_admin(m.from_user.id): return
    cid = m.chat.id
    if cid in user_batches and user_batches[cid]:
        files_list = user_batches[cid]
        del user_batches[cid]
        code = str(uuid.uuid4())[:8]
        data["files"][code] = {'files': files_list, 'is_premium': False}
        save_data()

        link = f"https://t.me/{BOT_USERNAME}?start={code}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚡ Open Batch Link", url=link))

        msg = (
            f"✅ <b>Batch Created Successfully! ({len(files_list)} items)</b>\n\n"
            f"📁 <b>Code:</b> <code>{code}</code>\n"
            f"🔒 Make Premium: <code>/make_pre {code}</code>\n\n"
            f"⚡ <b>Link:</b>\n<code>{link}</code>"
        )
        bot.reply_to(m, msg, reply_markup=markup, parse_mode="HTML")
    else:
        bot.reply_to(m, "❌ No batch in progress. Use /batch first.")

@bot.message_handler(commands=['add_bal'])
def handle_add_bal(m):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3:
        bot.reply_to(m, "Usage: <code>/add_bal USER_ID AMOUNT</code>", parse_mode="HTML")
        return
    try:
        amount = float(args[2].strip())
        target_id_str = args[1].strip()
        wallet = add_to_wallet(target_id_str, amount)
        bot.reply_to(m, f"✅ <b>Added ₹{amount:.2f} to {target_id_str}!</b>\nNew Balance: ₹{wallet['balance']:.2f}", parse_mode="HTML")
        try:
            bot.send_message(int(target_id_str), f"🎉 <b>Bonus Added:</b> ₹{amount:.2f}\nTotal Balance: ₹{wallet['balance']:.2f}", parse_mode="HTML")
        except Exception: pass
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")

@bot.message_handler(commands=['add_token'])
def handle_add_token(m):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 3:
        bot.reply_to(m, "Usage: <code>/add_token USER_ID TOKENS</code>", parse_mode="HTML")
        return
    try:
        tokens_to_add = int(args[2].strip())
        target_id_str = args[1].strip()
        wallet = add_to_wallet(target_id_str, tokens_to_add / 2.0)
        bot.reply_to(m, f"✅ <b>Added {tokens_to_add} Tokens to {target_id_str}!</b>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")

@bot.message_handler(commands=['reset_user'])
def handle_reset_user(m):
    if not is_admin(m.from_user.id): return
    args = m.text.split()
    if len(args) < 2: return
    target_id_str = args[1].strip()
    try:
        target_id = int(target_id_str)
        if target_id in data["users"]: data["users"].remove(target_id)
        if target_id_str in data["user_wallets"]: del data["user_wallets"][target_id_str]
        if target_id_str in data["user_sessions"]: del data["user_sessions"][target_id_str]
        if target_id_str in data["premium"]: del data["premium"][target_id_str]
        save_data()
        bot.reply_to(m, f"✅ User {target_id} Reset!")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")

@bot.message_handler(commands=['start'])
def handle_start(m):
    uid = m.from_user.id
    is_new = uid not in data["users"]
    wallet = get_wallet(uid)
    
    if data.get("stats_enabled", True) and is_new:
        data["users"].append(uid)
        save_data()

    text = m.text.split()
    referral_id = None
    file_code = None

    if len(text) > 1:
        param = text[1]
        if param.startswith("ref_"):
            try: referral_id = int(param.replace("ref_", ""))
            except Exception: pass
        else:
            file_code = param

    if is_new and referral_id and referral_id != uid and not wallet.get("referred_by"):
        wallet["referred_by"] = referral_id
        save_data()

    passed, unsub_list = check_force_sub(uid)
    if not passed:
        join_markup = types.InlineKeyboardMarkup(row_width=1)
        join_markup.add(
            types.InlineKeyboardButton("📢 Join Main Channel 1", url="https://t.me/news18backup"),
            types.InlineKeyboardButton("📢 Join Backup Channel 2", url=MAIN_CHANNEL_INVITE),
            types.InlineKeyboardButton("🔄 Verify Membership", callback_data=f"verify_sub_{file_code or 'none'}")
        )
        bot.reply_to(
            m,
            "⚠️ <b>Must Join Both Channels to Continue:</b>\n\n"
            "1. @news18backup\n"
            f"2. {MAIN_CHANNEL_INVITE}\n\n"
            "Dono join karke Verify par click karein 👇",
            reply_markup=join_markup,
            parse_mode="HTML"
        )
        return

    # Reward Referrer (Rs 5)
    if wallet.get("referred_by") and not wallet.get("reward_given"):
        ref_uid = str(wallet["referred_by"])
        if ref_uid in data["user_wallets"]:
            add_to_wallet(ref_uid, 5.0)
            data["user_wallets"][ref_uid]["total_ref"] = data["user_wallets"][ref_uid].get("total_ref", 0) + 1
            wallet["reward_given"] = True
            save_data()
            try:
                bot.send_message(
                    int(ref_uid),
                    f"🎉 <b>New Referral Joined!</b>\n\n💰 Added: <b>+₹5.00 Cash</b>",
                    parse_mode="HTML"
                )
            except Exception: pass

    if file_code:
        if file_code not in data["files"]:
            bot.reply_to(m, "❌ Link expire ya delete ho chuka hai.")
            return

        file_item = data["files"][file_code]
        
        if file_item.get("is_premium") and not is_premium(uid):
            show_vip_plans(m.chat.id, code=file_code, is_strict_premium=True)
            return

        allowed, current_count = check_and_increment_weekly_limit(uid)
        if not allowed:
            show_two_choices_limit_screen(m.chat.id, code=file_code)
            return

        deliver_files(m.chat.id, file_code)
        return

    welcome_text = (
        f"👋 <b>Welcome {m.from_user.first_name}!</b>\n\n"
        f"🎁 <b>You have 2 free trial access to any video/photo weekly.</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <b>Join Our VIP Updates Channel:</b>\n"
        f"🔗 <b><a href='{MAIN_CHANNEL_INVITE}'>{MAIN_CHANNEL_INVITE}</a></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚀 <i>Earn real cash by inviting friends (1st Withdraw @ ₹50 only)!</i>"
    )
    bot.send_message(m.chat.id, welcome_text, reply_markup=get_main_menu_markup(), parse_mode="HTML", disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    data_str = call.data

    try:
        if data_str.startswith("verify_sub_"):
            code = data_str.replace("verify_sub_", "")
            passed, unsub_list = check_force_sub(uid)
            if not passed:
                bot.answer_callback_query(call.id, "❌ Pehle dono channel join karein!", show_alert=True)
                return
            
            bot.answer_callback_query(call.id, "✅ Verified!")
            try: bot.delete_message(cid, mid)
            except Exception: pass

            wallet = get_wallet(uid)
            if wallet.get("referred_by") and not wallet.get("reward_given"):
                ref_uid = str(wallet["referred_by"])
                if ref_uid in data["user_wallets"]:
                    add_to_wallet(ref_uid, 5.0)
                    data["user_wallets"][ref_uid]["total_ref"] = data["user_wallets"][ref_uid].get("total_ref", 0) + 1
                    wallet["reward_given"] = True
                    save_data()
                    try:
                        bot.send_message(int(ref_uid), f"🎉 <b>Referral Verified!</b>\n\n💰 Added: <b>+₹5.00 Cash</b>", parse_mode="HTML")
                    except Exception: pass

            if code != "none" and code in data["files"]:
                file_item = data["files"][code]
                if file_item.get("is_premium") and not is_premium(uid):
                    show_vip_plans(cid, code=code, is_strict_premium=True)
                    return
                allowed, _ = check_and_increment_weekly_limit(uid)
                if not allowed:
                    show_two_choices_limit_screen(cid, code=code)
                    return
                deliver_files(cid, code)
            else:
                welcome_text = (
                    f"🎁 <b>You have 2 free trial access to any video/photo weekly.</b>\n\n"
                    f"👉 <b>Official Channel:</b> {MAIN_CHANNEL_INVITE}"
                )
                bot.send_message(cid, welcome_text, reply_markup=get_main_menu_markup(), parse_mode="HTML", disable_web_page_preview=True)

        elif data_str.startswith("menu_vip_code_"):
            code = data_str.replace("menu_vip_code_", "")
            show_vip_plans(cid, message_id=mid, code=code)

        elif data_str.startswith("back_limit_"):
            code = data_str.replace("back_limit_", "")
            show_two_choices_limit_screen(cid, message_id=mid, code=code)

        elif data_str == "menu_refer":
            wallet = get_wallet(uid)
            ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
            min_w = get_min_withdraw_amount(uid)
            
            withdraw_info = f"• 💳 <b>1st Withdrawal:</b> ₹50 direct to UPI\n• ⚡ <b>Next Withdrawals:</b> ₹100 direct to UPI"
            
            refer_text = (
                f"🎁 <b>Refer & Earn Program (FREE VIP)</b>\n\n"
                f"• 💰 <b>Reward:</b> ₹5.00 (10 Tokens) per Refer\n"
                f"{withdraw_info}\n\n"
                f"📊 <b>Your Wallet:</b>\n"
                f"👥 Total Invites: <b>{wallet.get('total_ref', 0)} users</b>\n"
                f"💵 Total Balance: <b>₹{wallet.get('balance', 0.0):.2f}</b> (<code>{wallet.get('tokens', 0)} Tokens</code>)\n"
                f"🎯 Next Minimum Cashout: <b>₹{min_w:.0f}</b>\n\n"
                f"🔗 <b>Your Referral Link:</b>\n<code>{ref_link}</code>"
            )
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("💳 Withdraw Cash", callback_data="menu_withdraw"),
                types.InlineKeyboardButton("🪙 Redeem Tokens for VIP", callback_data="menu_redeem")
            )
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_home"))
            bot.edit_message_text(refer_text, cid, mid, reply_markup=markup, parse_mode="HTML")

        elif data_str == "menu_home":
            welcome_text = (
                f"👋 <b>Main Dashboard</b>\n\n"
                f"🎁 <b>You have 2 free trial access to any video/photo weekly.</b>\n"
                f"👉 <b>Official Channel:</b> {MAIN_CHANNEL_INVITE}"
            )
            bot.edit_message_text(welcome_text, cid, mid, reply_markup=get_main_menu_markup(), parse_mode="HTML", disable_web_page_preview=True)

        elif data_str == "menu_vip":
            show_vip_plans(cid, message_id=mid)

        elif data_str == "menu_withdraw":
            wallet = get_wallet(uid)
            bal = wallet.get("balance", 0.0)
            min_required = get_min_withdraw_amount(uid)
            
            if bal < min_required:
                is_first = (wallet.get("withdraw_count", 0) == 0)
                notice = f"1st withdrawal limit is ₹50" if is_first else f"Minimum withdrawal limit is ₹100"
                bot.answer_callback_query(call.id, f"❌ {notice}. Your balance: ₹{bal:.2f}", show_alert=True)
                return
            
            data["user_sessions"][str(uid)] = {"mode": "withdraw", "amount": bal}
            save_data()
            bot.answer_callback_query(call.id)
            cancel_markup = types.InlineKeyboardMarkup()
            cancel_markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_req"))
            bot.send_message(cid, f"💳 <b>Enter your UPI ID to withdraw ₹{bal:.2f}:</b>", reply_markup=cancel_markup, parse_mode="HTML")

        elif data_str == "menu_redeem":
            wallet = get_wallet(uid)
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("⚡ VIP 3 Days — 98 Tokens", callback_data="redeem_plan_49"),
                types.InlineKeyboardButton("👑 VIP 1 Month — 198 Tokens", callback_data="redeem_plan_99"),
                types.InlineKeyboardButton("♾️ VIP Lifetime — 498 Tokens", callback_data="redeem_plan_249"),
                types.InlineKeyboardButton("🔥 10k Videos Pack — 198 Tokens", callback_data="redeem_pack_10k"),
                types.InlineKeyboardButton("🔙 Back", callback_data="menu_home")
            )
            bot.edit_message_text(f"🪙 <b>Redeem Tokens for VIP</b>\nAvailable: <b>{wallet.get('tokens', 0)} Tokens (₹{wallet.get('balance', 0.0):.2f})</b>", cid, mid, reply_markup=markup, parse_mode="HTML")

        elif data_str.startswith("redeem_"):
            plan_key = data_str.replace("redeem_", "")
            plan = PLANS.get(plan_key)
            if not plan: return
            wallet = get_wallet(uid)
            req_rs = plan["amount"]
            if wallet.get("tokens", 0) < plan["tokens"]:
                bot.answer_callback_query(call.id, f"❌ Need {plan['tokens']} Tokens.", show_alert=True)
                return

            if deduct_from_wallet(uid, req_rs):
                if plan_key == "pack_10k":
                    bot.answer_callback_query(call.id, "🎉 10K Pack Unlocked!")
                    bot.send_message(
                        cid, 
                        f"🎉 <b>10,000+ Direct Videos Pack Unlocked!</b>\n\n"
                        f"👉 <b><a href='{PACK_10K_PRIVATE_LINK}'>Click Here to Access 10k Videos Channel</a></b>",
                        reply_markup=get_main_menu_markup(),
                        parse_mode="HTML"
                    )
                else:
                    days = plan["days"]
                    data["premium"][str(uid)] = time.time() + (days * 86400)
                    save_data()
                    bot.answer_callback_query(call.id, "🎉 VIP Activated!")
                    bot.send_message(cid, f"🎉 <b>VIP Activated ({days} Days)!</b>", reply_markup=get_main_menu_markup(), parse_mode="HTML")

        elif data_str.startswith("buy_"):
            parts = data_str.split("_")
            plan_key = f"{parts[1]}_{parts[2]}"
            code = parts[3] if len(parts) > 3 and parts[3] != "none" else ""
            plan = PLANS.get(plan_key)
            if not plan: return

            data["user_sessions"][str(uid)] = {"mode": "payment", "plan_key": plan_key, "code": code}
            save_data()

            amt = plan["amount"]
            upi_url = f"upi://pay?pa={UPI_ID}&pn=BotVIP&am={amt}&cu=INR"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"

            bot.answer_callback_query(call.id)
            try: bot.delete_message(cid, mid)
            except Exception: pass

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_req"))
            bot.send_photo(
                cid,
                qr_url,
                caption=f"👑 <b>Unlock: {plan['name']}</b>\n\n💰 Pay: <b>₹{amt}</b> to UPI:\n<code>{UPI_ID}</code>\n\n👇 Payment karke <b>Screenshot ya 12-digit UTR</b> send karein:",
                reply_markup=markup,
                parse_mode="HTML"
            )

        elif data_str == "cancel_req":
            if str(uid) in data["user_sessions"]:
                del data["user_sessions"][str(uid)]
                save_data()
            bot.answer_callback_query(call.id, "Cancelled.")
            try: bot.delete_message(cid, mid)
            except Exception: pass
            bot.send_message(cid, "❌ Cancelled.", reply_markup=get_main_menu_markup())

        elif data_str.startswith("adm_app_"):
            if not is_admin(uid): return
            req_id = data_str.replace("adm_app_", "")
            req = data["pending_requests"].get(req_id)
            if not req:
                bot.answer_callback_query(call.id, "Already processed.")
                return

            target_uid = req["user_id"]
            plan_key = req.get("plan_key", "")
            target_code = req.get("code")
            plan_amt = req.get("amount", 0.0)
            
            data["total_revenue"] = data.get("total_revenue", 0.0) + plan_amt
            del data["pending_requests"][req_id]
            save_data()

            bot.answer_callback_query(call.id, "✅ Request Approved!")
            try: bot.edit_message_caption(caption=f"✅ <b>APPROVED & DELIVERED</b> (<code>{target_uid}</code>)", chat_id=cid, message_id=mid, parse_mode="HTML")
            except Exception: pass

            if plan_key == "pack_10k":
                try:
                    bot.send_message(
                        target_uid,
                        f"🎉 <b>Badhaai Ho! 10,000+ Direct Videos Pack Unlock Ho Gaya Hai!</b>\n\n"
                        f"👉 <b><a href='{PACK_10K_PRIVATE_LINK}'>Click Here to Access 10k Direct Videos</a></b>",
                        reply_markup=get_main_menu_markup(),
                        parse_mode="HTML"
                    )
                except Exception as ex:
                    print("User notify error:", ex)
            else:
                days = req["plan_days"]
                data["premium"][str(target_uid)] = time.time() + (days * 86400)
                save_data()
                try:
                    bot.send_message(target_uid, f"🎉 <b>VIP Activated ({days} Days)!</b>\nUnlimited downloads active.", reply_markup=get_main_menu_markup(), parse_mode="HTML")
                    if target_code: deliver_files(target_uid, target_code)
                except Exception as ex:
                    print("User notify error:", ex)

        elif data_str.startswith("adm_rej_"):
            if not is_admin(uid): return
            req_id = data_str.replace("adm_rej_", "")
            if req_id in data["pending_requests"]:
                target_uid = data["pending_requests"][req_id]["user_id"]
                del data["pending_requests"][req_id]
                save_data()
                bot.answer_callback_query(call.id, "Rejected.")
                try: bot.edit_message_caption(caption="❌ <b>PAYMENT REJECTED</b>", chat_id=cid, message_id=mid, parse_mode="HTML")
                except Exception: pass
                try: bot.send_message(target_uid, "❌ Payment reject ho gaya. Contact: @GETSUPPORT99", parse_mode="HTML")
                except Exception: pass

        elif data_str.startswith("wdr_app_"):
            if not is_admin(uid): return
            w_id = data_str.replace("wdr_app_", "")
            w_req = data["withdraw_requests"].get(w_id)
            if not w_req: return
            
            data["total_withdrawn"] = data.get("total_withdrawn", 0.0) + w_req['amount']
            del data["withdraw_requests"][w_id]
            save_data()
            
            bot.answer_callback_query(call.id, "Paid!")
            try: bot.edit_message_text(f"✅ <b>WITHDRAWAL PAID</b> (₹{w_req['amount']:.2f})", cid, mid, parse_mode="HTML")
            except Exception: pass
            try: bot.send_message(w_req["user_id"], f"🎉 ₹{w_req['amount']:.2f} transferred to <code>{w_req['upi']}</code>!", parse_mode="HTML")
            except Exception: pass

        elif data_str.startswith("wdr_rej_"):
            if not is_admin(uid): return
            w_id = data_str.replace("wdr_rej_", "")
            w_req = data["withdraw_requests"].get(w_id)
            if not w_req: return
            add_to_wallet(str(w_req["user_id"]), w_req["amount"])
            user_w = get_wallet(w_req["user_id"])
            if user_w.get("withdraw_count", 0) > 0:
                user_w["withdraw_count"] -= 1
            del data["withdraw_requests"][w_id]
            save_data()
            bot.answer_callback_query(call.id, "Refunded.")
            try: bot.edit_message_text("❌ <b>WITHDRAWAL REJECTED (Refunded)</b>", cid, mid, parse_mode="HTML")
            except Exception: pass

    except Exception as e:
        print("Callback error:", e)

# PROOF / WITHDRAWAL HANDLER
@bot.message_handler(func=lambda m: str(m.from_user.id) in data["user_sessions"], content_types=['text', 'photo'])
def handle_text_and_proofs(m):
    uid = str(m.from_user.id)
    session = data["user_sessions"][uid]
    mode = session.get("mode")

    if mode == "withdraw" and m.content_type == 'text':
        upi_text = m.text.strip()
        amt = session.get("amount", 0.0)
        wallet = get_wallet(uid)
        
        if not deduct_from_wallet(uid, amt):
            bot.reply_to(m, "❌ Insufficient balance.")
            del data["user_sessions"][uid]
            return

        wallet["withdraw_count"] = wallet.get("withdraw_count", 0) + 1
        is_first_time = (wallet["withdraw_count"] == 1)

        del data["user_sessions"][uid]
        w_id = str(uuid.uuid4())[:6]
        data["withdraw_requests"][w_id] = {"user_id": int(uid), "amount": amt, "upi": upi_text}
        save_data()

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Mark Paid", callback_data=f"wdr_app_{w_id}"),
            types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"wdr_rej_{w_id}")
        )
        badge = "🌟 1st Withdrawal" if is_first_time else "🔁 Regular Withdrawal"
        bot.send_message(ADMIN_ID, f"💸 <b>Withdraw Request ({badge}):</b>\nUser: <code>{uid}</code>\nAmount: ₹{amt:.2f}\nUPI: <code>{upi_text}</code>", reply_markup=markup, parse_mode="HTML")
        bot.reply_to(m, f"✅ Withdrawal of ₹{amt:.2f} submitted to admin.", reply_markup=get_main_menu_markup(), parse_mode="HTML")
        return

    elif mode == "payment":
        utr_clean = m.text.strip() if m.content_type == 'text' else None
        
        if utr_clean and len(utr_clean) >= 8:
            if utr_clean in data.get("used_utrs", []):
                bot.reply_to(m, "❌ <b>Duplicate UTR Detected!</b>\nYeh transaction number pehle se submit kiya ja chuka hai.", parse_mode="HTML")
                return
            data["used_utrs"].append(utr_clean)

        plan_key = session.get("plan_key", "plan_49")
        plan = PLANS.get(plan_key, {"name": "VIP Plan", "amount": 49, "days": 3})
        del data["user_sessions"][uid]
        req_id = str(uuid.uuid4())[:6]

        data["pending_requests"][req_id] = {
            "user_id": int(uid),
            "plan_key": plan_key,
            "plan_name": plan["name"],
            "plan_days": plan["days"],
            "amount": plan["amount"],
            "code": session.get("code", "")
        }
        save_data()

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ APPROVE ACCESS", callback_data=f"adm_app_{req_id}"),
            types.InlineKeyboardButton("❌ REJECT", callback_data=f"adm_rej_{req_id}")
        )
        admin_caption = f"👑 <b>New Order Received!</b>\nUser: {m.from_user.first_name} (<code>{uid}</code>)\nOrder: {plan['name']} (₹{plan['amount']})\n"

        if m.content_type == 'photo':
            bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=admin_caption + "📸 <i>Screenshot Attached</i>", reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_caption + f"✍️ <b>UTR:</b> <code>{utr_clean}</code>", reply_markup=markup, parse_mode="HTML")

        bot.reply_to(m, "✅ <b>Payment Proof Submitted!</b>\nAdmin verify kar rahe hain. Jaldi unlock ho jayega.", reply_markup=get_main_menu_markup(), parse_mode="HTML")
        return

# ADMIN MEDIA LINK GENERATION
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_admin_media(m):
    if not is_admin(m.from_user.id): return
    cid = m.chat.id
    cap = m.caption or ""
    fid, ftype = None, None

    if m.content_type == 'photo':
        fid = m.photo[-1].file_id
        ftype = 'photo'
    elif m.content_type == 'video':
        fid = m.video.file_id
        ftype = 'video'
    elif m.content_type == 'document':
        fid = m.document.file_id
        ftype = 'document'
    elif m.content_type == 'audio':
        fid = m.audio.file_id
        ftype = 'audio'

    if fid:
        file_info = {'file_id': fid, 'type': ftype, 'caption': cap}
        if cid in user_batches:
            user_batches[cid].append(file_info)
            bot.reply_to(m, f"➕ {ftype.capitalize()} #{len(user_batches[cid])} added to batch! Send more or <code>/done</code>", parse_mode="HTML")
        else:
            code = str(uuid.uuid4())[:8]
            data["files"][code] = {'files': [file_info], 'is_premium': False}
            save_data()
            
            direct_clean_link = f"https://t.me/{BOT_USERNAME}?start={code}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚡ Open Direct Link", url=direct_clean_link))

            msg_text = (
                f"✅ <b>{ftype.capitalize()} Link Ready!</b>\n\n"
         f"📁 <b>Code:</b> <code>{code}</code>\n"
                f"🔒 Set Premium Only: <code>/make_pre {code}</code>\n"
                f"🔓 Set Free: <code>/make_free {code}</code>\n\n"
                f"⚡ <b>Shareable Clean Link:</b>\n<code>{direct_clean_link}</code>"
            )
            bot.reply_to(m, msg_text, reply_markup=markup, parse_mode="HTML")

bot.infinity_polling(skip_pending=True)
bot.infinity_polling(skip_pending=True)


