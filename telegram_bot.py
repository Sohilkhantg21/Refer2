from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import sqlite3
import os

# Define states
BALANCE, BONUS, REFER, WITHDRAW, ADD_UPI = range(5)

# Create and connect to SQLite DB (in-memory database, as Render uses ephemeral storage)
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        referrer INTEGER,
        upi TEXT DEFAULT '',
        referred_by INTEGER DEFAULT NULL
    )
''')
conn.commit()

# Set your Telegram Bot Token
TOKEN = os.getenv("7398067602:AAHkJ183lUT-3s4Y40TIP7hosvYKyFR2CQY")
CHANNEL = "@sohilscripter"  # Set your channel link here

# Function to start the bot and check channel membership
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    
    # Check if the user has joined the channel
    member = context.bot.get_chat_member(CHANNEL, user_id)
    if member.status in ['member', 'administrator']:
        # Add user to the database if not already
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
            conn.commit()

        # Show the main menu
        keyboard = [
            [KeyboardButton("Balance"), KeyboardButton("Bonus")],
            [KeyboardButton("Refer"), KeyboardButton("Withdraw")],
            [KeyboardButton("Add UPI")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text("Welcome to the Referral Bot! Choose an option:", reply_markup=reply_markup)
        return BALANCE
    else:
        update.message.reply_text(f"Please join the channel {CHANNEL} to proceed.")
        return ConversationHandler.END

# Function to show balance
def balance(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    update.message.reply_text(f"Your balance is ₹{balance}")
    return BALANCE

# Function for bonus (you can adjust logic as needed)
def bonus(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("You earned 10 bonus coins!")
    return BONUS

# Function for referring users
def refer(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    cursor.execute('SELECT referrer FROM users WHERE user_id = ?', (user_id,))
    referrer = cursor.fetchone()[0]
    
    if referrer:
        update.message.reply_text(f"Your referral link is: https://t.me/YOUR_BOT_NAME?start={user_id}")
    else:
        update.message.reply_text("You don't have a referrer yet. Please refer someone to get your link.")
    
    return REFER

# Function to withdraw funds
def withdraw(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    
    if balance >= 50:
        update.message.reply_text("Please enter your UPI ID to withdraw.")
        return ADD_UPI
    else:
        update.message.reply_text("Minimum withdrawal is ₹50. Your balance is insufficient.")
        return WITHDRAW

# Function to add UPI for withdrawal
def add_upi(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    upi_id = update.message.text
    cursor.execute('UPDATE users SET upi = ? WHERE user_id = ?', (upi_id, user_id))
    conn.commit()
    update.message.reply_text(f"UPI ID {upi_id} added successfully. Your withdrawal request will be processed.")
    return ADD_UPI

# Main function to set up handlers and start the bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BALANCE: [MessageHandler(Filters.text & ~Filters.command, balance)],
            BONUS: [MessageHandler(Filters.text & ~Filters.command, bonus)],
            REFER: [MessageHandler(Filters.text & ~Filters.command, refer)],
            WITHDRAW: [MessageHandler(Filters.text & ~Filters.command, withdraw)],
            ADD_UPI: [MessageHandler(Filters.text & ~Filters.command, add_upi)],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
