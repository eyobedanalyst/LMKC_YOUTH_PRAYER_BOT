import os
import logging
import requests
import json
import random
from datetime import datetime
import pytz
import time
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8419113682:AAHeiz6hAUarFw-r1yYXHzjKdjtiYkvrCKs"

# Your Google Sheet configuration (for storing prayers/testimonies/feedback only)
SHEET_ID = "1S-WDOuIK_h1e-vA7U9n-1DTGwIB_UoTa1U1A61Mhye0"

# Timezone for Ethiopia
ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')

# Store user data temporarily
user_data = {}

# Create Flask app for keeping the bot awake
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running! 🚀"

def run_flask():
    """Run Flask app to keep the bot awake"""
    app.run(host='0.0.0.0', port=5000)

def keep_awake():
    """Function to keep the bot awake by pinging itself"""
    def wake_thread():
        while True:
            try:
                requests.get("https://your-bot-name.onrender.com", timeout=10)
                print("Keep-alive ping sent at", datetime.now())
            except Exception as e:
                print("Ping failed:", e)
            time.sleep(300)  # Sleep for 5 minutes
    
    thread = Thread(target=wake_thread)
    thread.daemon = True
    thread.start()

# AMHARIC BIBLE VERSES BUILT INTO THE CODE
AMHARIC_VERSES = [
    {"verse": "እግዚአብሔር ፈቃዱን ይፈጽማል፤ በእርሱ ተማምኜ አደርጋለሁ።", "category": "የእምነት ጥቅስ"},
    {"verse": "ሁሉን በክርስቶስ የማጠነከር ኃይል አለኝ።", "category": "የኃይል ጥቅስ"},
    {"verse": "ከቶ አልተረፈሁም፤ ከቶ አልተወሁም።", "category": "የመጽናናት ጥቅስ"},
    {"verse": "በሁሉ ነገር ስለ እምነት አመስግኑ።", "category": "የምስጋና ጥቅስ"},
    {"verse": "እግዚአብሔር ፊት ለፊት እያለሁ ሁልጊዜ ደስ ይለኛል።", "category": "የደስታ ጥቅስ"},
    {"verse": "እግዚአብሔር መንገዴን ያውቃል፤ በእርሱ ተመክቼ እጓዋለሁ።", "category": "የመመርመር ጥቅስ"},
    {"verse": "የእግዚአብሔር ቃል ለእግሬ መብራት ለመንገዴ ብርሃን ነው።", "category": "የመምራት ጥቅስ"},
    {"verse": "እግዚአብሔር ወዳጄ ነው፤ ከሁሉ በላይ በእርሱ ረጋለሁ።", "category": "የመታገስ ጥቅስ"},
    {"verse": "በእግዚአብሔር ሰላም ልባችንን ይጠብቃል።", "category": "የሰላም ጥቅስ"},
    {"verse": "እግዚአብሔር ከእኛ ጋር ነው፤ ለምን እንፈራለን?", "category": "የመጽናናት ጥቅስ"},
    {"verse": "በልጆችህ ይባርክ፤ በውስጥህ ያሉት ሁሉ ይባረክ።", "category": "የበረከት ጥቅስ"},
    {"verse": "እግዚአብሔር አምላክ አንድ ነው፤ ከእርሱ በቀር ሌላ የለም።", "category": "የአምልኮ ጥቅስ"},
    {"verse": "የእግዚአብሔር ፍቅር ዘለዓለም ነው፤ ሁልጊዜ ይጠብቀናል።", "category": "የፍቅር ጥቅስ"},
    {"verse": "በእግዚአብሔር ቃል ሁሉ ይቻላል፤ ለማይናገር ነገር የለም።", "category": "የእምነት ጥቅስ"},
    {"verse": "እግዚአብሔር ቸር ነው፤ ምህረቱ ዘለዓለም ነው።", "category": "የምህረት ጥቅስ"}
]

def get_daily_verse():
    """Get daily verse (consistent for everyone each day)"""
    day_of_year = datetime.now(ethiopia_tz).timetuple().tm_yday
    daily_verse = AMHARIC_VERSES[day_of_year % len(AMHARIC_VERSES)]
    return daily_verse

def get_random_verse():
    """Get random verse"""
    return random.choice(AMHARIC_VERSES)

def save_to_sheet(data_type, content, user_info=""):
    """Save prayers, testimonies, and feedback to Google Sheet"""
    try:
        # This function would normally save to Google Sheets
        # For now, we'll just log it since we don't have write access
        timestamp = datetime.now(ethiopia_tz).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"SAVED TO SHEET - Type: {data_type}, Content: {content}, User: {user_info}, Time: {timestamp}")
        
        # In a real implementation, you would use Google Sheets API here
        # to append this data to your sheet
        return True
    except Exception as e:
        logger.error(f"Error saving to sheet: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    welcome_text = f"""
ሰላም {user.first_name}! 👋

የጸሎት ቦት ወደ አገልግሎት በሰላም መጡ! 🙏

የሚፈልጉትን አገልግሎት ይምረጡ፡
"""
    
    keyboard = [
        [InlineKeyboardButton("📖 የዛሬ ጥቅስ", callback_data="daily_verse")],
        [InlineKeyboardButton("🎲 የተለያየ ጥቅስ", callback_data="random_verse")],
        [InlineKeyboardButton("🙏 ጸሎት ለመጨመር", callback_data="add_prayer")],
        [InlineKeyboardButton("✨ ምስክርነት ለመጨመር", callback_data="add_testimony")],
        [InlineKeyboardButton("📝 ለወጣቶች ኮሚቴ ግብረመልስ", callback_data="add_feedback")],
        [InlineKeyboardButton("ℹ️ እርዳታ", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "daily_verse":
        verse = get_daily_verse()
        text = f"📖 <b>የዛሬ ጥቅስ</b>\n\n{verse['verse']}\n\n<em>ምድብ: {verse['category']}</em>\n<em>ቀን: {datetime.now(ethiopia_tz).strftime('%Y-%m-%d')}</em>"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=main_menu_keyboard())
    
    elif data == "random_verse":
        verse = get_random_verse()
        text = f"🎲 <b>የተለያየ ጥቅስ</b>\n\n{verse['verse']}\n\n<em>ምድብ: {verse['category']}</em>"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=main_menu_keyboard())
    
    elif data == "add_prayer":
        user_data[user_id] = {'action': 'adding_prayer'}
        text = "🙏 <b>ጸሎትዎን አሳልፉ</b>\n\nእባክዎ ጸሎትዎን ይፃፉ፡"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=cancel_keyboard())
    
    elif data == "add_testimony":
        user_data[user_id] = {'action': 'adding_testimony'}
        text = "✨ <b>ምስክርነትዎን አጋሩ</b>\n\nእግዚአብሔር በሕይወትዎ ያደረገውን ነገር ይፃፉ፡"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=cancel_keyboard())
    
    elif data == "add_feedback":
        user_data[user_id] = {'action': 'adding_feedback'}
        text = "📝 <b>ለወጣቶች ኮሚቴ ግብረመልስ</b>\n\nሀሳብዎን ወይም ግብረመልስዎን ይፃፉ፡"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=cancel_keyboard())
    
    elif data == "help":
        text = """
<b>እርዳታ 🆘</b>

📖 <b>የዛሬ ጥቅስ</b> - ለዛሬ የተወሰነ ጥቅስ ያግኙ
🎲 <b>የተለያየ ጥቅስ</b> - የተለያዩ ጥቅሶችን ያግኙ
🙏 <b>ጸሎት ለመጨመር</b> - የግል ጸሎትዎን ያካፍሉ
✨ <b>ምስክርነት ለመጨመር</b> - ምስክርነትዎን ያካፍሉ
📝 <b>ግብረመልስ</b> - ለወጣቶች ኮሚቴ ግብረመልስ ይስጡ

ለማንኛውም አገልግሎት በትር ላይ ጠቅ ያድርጉ።
"""
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=main_menu_keyboard())
    
    elif data == "main_menu":
        await query.edit_message_text(
            text="ዋና መግለጫ፡ የሚፈልጉትን አገልግሎት ይምረጡ፡",
            reply_markup=main_menu_keyboard()
        )
    
    elif data == "cancel":
        if user_id in user_data:
            del user_data[user_id]
        await query.edit_message_text(
            text="ክንውን ተሰርዟል። ዋና መግለጫ፡",
            reply_markup=main_menu_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text
    
    if user_id in user_data:
        action = user_data[user_id]['action']
        
        if action == 'adding_prayer':
            # Save prayer to Google Sheet
            save_to_sheet("PRAYER", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "🙏 ጸሎትዎ ተቀብሎል! አምላክ ይመስርዎት።\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del user_data[user_id]
        
        elif action == 'adding_testimony':
            # Save testimony to Google Sheet
            save_to_sheet("TESTIMONY", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "✨ ምስክርነትዎ ተቀብሎል! አምላክ ይባረክዎት።\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del user_data[user_id]
        
        elif action == 'adding_feedback':
            # Save feedback to Google Sheet
            save_to_sheet("FEEDBACK", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "📝 ግብረመልስዎ ተቀብሎል! አመሰግናለሁ! 🙏\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del user_data[user_id]
    
    else:
        # If no specific action, show main menu
        await update.message.reply_text(
            "ዋና መግለጫ፡ የሚፈልጉትን አገልግሎት ይምረጡ፡",
            reply_markup=main_menu_keyboard()
        )

def main_menu_keyboard():
    """Create the main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📖 የዛሬ ጥቅስ", callback_data="daily_verse")],
        [InlineKeyboardButton("🎲 የተለያየ ጥቅስ", callback_data="random_verse")],
        [InlineKeyboardButton("🙏 ጸሎት ለመጨመር", callback_data="add_prayer")],
        [InlineKeyboardButton("✨ ምስክርነት ለመጨመር", callback_data="add_testimony")],
        [InlineKeyboardButton("📝 ለወጣቶች ኮሚቴ ግብረመልስ", callback_data="add_feedback")],
        [InlineKeyboardButton("ℹ️ እርዳታ", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard():
    """Create cancel keyboard"""
    keyboard = [
        [InlineKeyboardButton("❌ ሰርዝ", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(msg="Exception occurred:", exc_info=context.error)

def start_bot():
    """Start the Telegram bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Start the Bot
    print("🤖 Telegram Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Start Flask in a separate thread for keeping awake
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start keep-awake function
    keep_awake()
    
    # Start the Telegram bot
    start_bot()