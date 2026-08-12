import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Security ke liye Token environment variable se aayega
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Mujhe koi bhi TeraBox link bhejo, main use streaming link me convert kar dunga."
    )

async def handle_terabox_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "terabox" in user_message or "neardown" in user_message or "freeterabox" in user_message or "teraboxapp" in user_message:
        await update.message.reply_text("Link mil gaya! Process ho raha hai... ⏳")
        
        # Temporary link (aage website banane par update karenge)
        stream_link = f"https://my-free-stream-site.vercel.app/watch?url={user_message}"
        
        await update.message.reply_text(
            f"✅ Aapka Streaming Link Taiyar Hai:\n\n{stream_link}"
        )
    else:
        await update.message.reply_text("Kripya sahi TeraBox URL bhejein!")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN nahi mil raha!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_terabox_link))

    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
