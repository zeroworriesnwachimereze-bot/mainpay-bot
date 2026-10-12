import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TIMEWALL_ID = "59c1192f5492e841"
balances = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in balances:
        balances[user_id] = 0
    text = f"💰 *MainPay Rewards* 💰\n\nWelcome {update.effective_user.first_name}!\n\nBalance: *{balances[user_id]} Coins*\n\n1000 Coins = $1\n\n👇 Choose:"
    keyboard = [
        [InlineKeyboardButton("💰 Earn Coins", callback_data="earn")],
        [InlineKeyboardButton("💳 Check Balance", callback_data="balance")],
        [InlineKeyboardButton("🏧 Withdraw", callback_data="withdraw")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_id not in balances:
        balances[user_id] = 0
    if query.data == "earn":
        url = f"https://wall.timewall.io/index.html?o={TIMEWALL_ID}&uid={user_id}"
        keyboard = [
            [InlineKeyboardButton("🔥 Open TimeWall & Earn", url=url)],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
        await query.edit_message_text(f"💰 *EARN COINS*\n\nClick below, complete tasks!\n\nYour ID: `{user_id}`\nBalance: {balances[user_id]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif query.data == "balance":
        await query.edit_message_text(f"💳 Balance: *{balances[user_id]} Coins*\nMin: 5000 = $5", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Earn More", callback_data="earn")]]))
    elif query.data == "withdraw":
        await query.edit_message_text(f"🏧 Earn 5000 Coins to withdraw.\nBalance: {balances[user_id]}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Earn Now", callback_data="earn")]]))
    elif query.data == "back":
        text = f"💰 *MainPay Rewards* 💰\n\nBalance: *{balances[user_id]} Coins*\n\n👇 Choose:"
        keyboard = [
            [InlineKeyboardButton("💰 Earn Coins", callback_data="earn")],
            [InlineKeyboardButton("💳 Check Balance", callback_data="balance")],
            [InlineKeyboardButton("🏧 Withdraw", callback_data="withdraw")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot Started!")
    app.run_polling()

if __name__ == "__main__":
    main()
