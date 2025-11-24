import streamlit as st
import requests
import json
import random
from datetime import datetime
import pytz
import time
import threading
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging

# Set page config
st.set_page_config(
    page_title="Prayer Bot Controller",
    page_icon="🙏",
    layout="wide"
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8419113682:AAHeiz6hAUarFw-r1yYXHzjKdjtiYkvrCKs"

# Timezone for Ethiopia
ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')

# Store bot state in session state
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'bot_application' not in st.session_state:
    st.session_state.bot_application = None

# AMHARIC BIBLE VERSES
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
    {"verse": "እግዚአብሔር ከእኛ ጋር ነው፤ ለምን እንፈራለን?", "category": "የመጽናናት ጥቅስ"}
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
    """Save prayers, testimonies, and feedback"""
    try:
        timestamp = datetime.now(ethiopia_tz).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"SAVED - Type: {data_type}, Content: {content}, User: {user_info}, Time: {timestamp}")
        return True
    except Exception as e:
        logger.error(f"Error saving: {e}")
        return False

# Telegram Bot Handlers
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
        st.session_state.user_data[user_id] = {'action': 'adding_prayer'}
        text = "🙏 <b>ጸሎትዎን አሳልፉ</b>\n\nእባክዎ ጸሎትዎን ይፃፉ፡"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=cancel_keyboard())
    
    elif data == "add_testimony":
        st.session_state.user_data[user_id] = {'action': 'adding_testimony'}
        text = "✨ <b>ምስክርነትዎን አጋሩ</b>\n\nእግዚአብሔር በሕይወትዎ ያደረገውን ነገር ይፃፉ፡"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=cancel_keyboard())
    
    elif data == "add_feedback":
        st.session_state.user_data[user_id] = {'action': 'adding_feedback'}
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
    
    elif data == "cancel":
        if user_id in st.session_state.user_data:
            del st.session_state.user_data[user_id]
        await query.edit_message_text(
            text="ክንውን ተሰርዟል። ዋና መግለጫ፡",
            reply_markup=main_menu_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text
    
    if user_id in st.session_state.user_data:
        action = st.session_state.user_data[user_id]['action']
        
        if action == 'adding_prayer':
            save_to_sheet("PRAYER", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "🙏 ጸሎትዎ ተቀብሎል! አምላክ ይመስርዎት።\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del st.session_state.user_data[user_id]
        
        elif action == 'adding_testimony':
            save_to_sheet("TESTIMONY", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "✨ ምስክርነትዎ ተቀብሎል! አምላክ ይባረክዎት።\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del st.session_state.user_data[user_id]
        
        elif action == 'adding_feedback':
            save_to_sheet("FEEDBACK", text, f"User: {user_name} (ID: {user_id})")
            await update.message.reply_text(
                "📝 ግብረመልስዎ ተቀብሎል! አመሰግናለሁ! 🙏\n\n"
                "እንደገና ለመጠቀም ከታች ያሉትን ቁልፎች ይጠቀሙ።",
                reply_markup=main_menu_keyboard()
            )
            del st.session_state.user_data[user_id]
    
    else:
        await update.message.reply_text(
            "ዋና መግለጫ፡ የሚፈልጉትን አገልግሎት ይምረጡ፡",
            reply_markup=main_menu_keyboard()
        )

def main_menu_keyboard():
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
    keyboard = [[InlineKeyboardButton("❌ ሰርዝ", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception occurred:", exc_info=context.error)

def keep_alive():
    """Function to keep the bot alive by making requests"""
    def wake_thread():
        while st.session_state.bot_running:
            try:
                # This keeps the thread active and prevents timeouts
                time.sleep(60)  # Sleep for 1 minute
                logger.info("🤖 Bot is still running...")
            except Exception as e:
                logger.error(f"Keep-alive error: {e}")
    
    thread = threading.Thread(target=wake_thread)
    thread.daemon = True
    thread.start()

def start_bot():
    """Start the Telegram bot in a separate thread"""
    async def run_bot():
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)

        st.session_state.bot_application = application
        logger.info("🤖 Telegram Bot is starting...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    # Run the bot in a separate thread
    def run_async():
        asyncio.run(run_bot())
    
    bot_thread = threading.Thread(target=run_async)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start keep-alive
    keep_alive()
    
    st.session_state.bot_running = True
    return True

def stop_bot():
    """Stop the Telegram bot"""
    if st.session_state.bot_application:
        st.session_state.bot_application.stop()
    st.session_state.bot_running = False
    return True

# Streamlit UI
st.title("🤖 Amharic Prayer Bot Controller")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Bot Status")
    if st.session_state.bot_running:
        st.success("🟢 Bot is RUNNING")
        st.info("The bot is active 24/7 and listening for Telegram messages")
    else:
        st.error("🔴 Bot is STOPPED")
        st.info("Click the button below to start the bot")

with col2:
    st.subheader("Controls")
    
    if not st.session_state.bot_running:
        if st.button("🚀 Start Bot", type="primary", use_container_width=True):
            if start_bot():
                st.success("Bot started successfully!")
                st.rerun()
    else:
        if st.button("🛑 Stop Bot", type="secondary", use_container_width=True):
            if stop_bot():
                st.success("Bot stopped successfully!")
                st.rerun()

st.markdown("---")
st.subheader("📊 Bot Information")

st.info("""
**Features:**
- 📖 Daily Amharic Bible verses
- 🎲 Random verses on demand  
- 🙏 Prayer submission
- ✨ Testimony sharing
- 📝 Youth committee feedback
- 24/7 operation

**How to use:**
1. Start the bot using the button above
2. Search for your bot on Telegram
3. Send `/start` to begin
""")

st.subheader("🔧 Technical Details")
st.code(f"""
Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...
Status: {'Running' if st.session_state.bot_running else 'Stopped'}
Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

# Auto-restart logic (for 24/7 operation)
if st.session_state.bot_running:
    st.balloons()
    
    # This ensures the app stays active
    st.markdown("---")
    st.caption("🔄 Auto-refresh enabled for 24/7 operation")

# Initialize bot on startup if not running
if not st.session_state.bot_running and 'initialized' not in st.session_state:
    st.session_state.initialized = True
    # Uncomment the line below to auto-start the bot when the app loads
    # start_bot()