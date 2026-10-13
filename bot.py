import os, sqlite3, threading, random
from datetime import date
from flask import Flask, request, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=os.getenv("ADMIN_ID")
APP_URL=os.getenv("APP_URL") # put your Render URL here e.g https://mainpay-bot.onrender.com

flask_app=Flask(__name__, static_folder='.')

@flask_app.route('/')
def home():
    return "MainPay Running"

@flask_app.route('/app')
def miniapp():
    return send_from_directory('.', 'index.html')

@flask_app.route('/reward')
def reward():
    uid=request.args.get('uid')
    if uid:
        try:
            conn=sqlite3.connect('mainpay.db');cur=conn.cursor()
            cur.execute("UPDATE users SET balance=balance+0.01 WHERE user_id=?",(int(uid),))
            conn.commit();conn.close()
        except: pass
    return "ok"

def run_flask():
    flask_app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))

def init_db():
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0, referrals INTEGER DEFAULT 0, referred_by INTEGER, last_daily TEXT, invested REAL DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS invests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, status TEXT DEFAULT 'pending')")
    conn.commit();conn.close()
def get_user(uid):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("SELECT * FROM users WHERE user_id=?",(uid,));u=cur.fetchone();conn.close();return u
def add_user(uid,uname,ref=None):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("INSERT OR IGNORE INTO users (user_id,username,referred_by) VALUES (?,?,?)",(uid,uname,ref));conn.commit();conn.close()
def add_bal(uid,amt):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?",(amt,uid));conn.commit();conn.close()
def menu():
    web_url = (APP_URL + "/app") if APP_URL else "https://mainpay-bot.onrender.com/app"
    b1=InlineKeyboardButton("💰 Balance",callback_data="balance")
    b2=InlineKeyboardButton("📈 Invest $3/$5/$10",callback_data="invest")
    b3=InlineKeyboardButton("🎬 Watch Ads $0.01", web_app=WebAppInfo(url=web_url))
    b4=InlineKeyboardButton("🎮 Game $0.01",callback_data="game")
    b5=InlineKeyboardButton("🎁 Daily $0.02",callback_data="daily")
    b6=InlineKeyboardButton("👥 Invite 5% Bonus",callback_data="invite")
    b7=InlineKeyboardButton("💸 Withdraw $0.50",callback_data="withdraw")
    return InlineKeyboardMarkup([[b1],[b2],[b3],[b4],[b5],[b6],[b7]])

#... rest of your code same (invest_menu, start, btn, etc) KEEP SAME

def invest_menu():
    i1=InlineKeyboardButton("Invest $3 - Earn $0.30/day",callback_data="inv3")
    i2=InlineKeyboardButton("Invest $5 - Earn $0.60/day",callback_data="inv5")
    i3=InlineKeyboardButton("Invest $10 - Earn $1.30/day",callback_data="inv10")
    i4=InlineKeyboardButton("⬅️ Back",callback_data="back")
    return InlineKeyboardMarkup([[i1],[i2],[i3],[i4]])

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id;uname=update.effective_user.username or "User";ref=None
    if context.args:
        try:ref=int(context.args[0])
        except:pass
    if not get_user(uid):
        add_user(uid,uname,ref)
        if ref and ref!=uid and get_user(ref):
            add_bal(ref,0.05)
            conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?",(ref,));conn.commit();conn.close()
            try:await context.bot.send_message(chat_id=ref,text=f"New user @{uname} joined via your link! +$0.05")
            except:pass
    await update.message.reply_text(f"Welcome MainPay @{uname}!\n\n💵 Plans:\n$3 = $0.30/day\n$5 = $0.60/day\n$10 = $1.30/day\n\n🎬 Watch Ads = $0.01\n👥 Referral = 5%\n\nMin Withdraw $0.50",reply_markup=menu())

async def btn(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query;await q.answer();uid=q.from_user.id;u=get_user(uid);bal=u[2];d=q.data
    if d=="balance":
        await q.edit_message_text(f"Balance: ${bal:.3f}\nInvested: ${u[6]:.2f}\nReferrals: {u[3]}",reply_markup=menu())
    elif d=="invest":
        await q.edit_message_text(f"Choose Plan:",reply_markup=invest_menu())
    elif d in ["inv3","inv5","inv10"]:
        amt={"inv3":3,"inv5":5,"inv10":10}[d]
        conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("INSERT INTO invests (user_id,amount) VALUES (?,?)",(uid,amt));conn.commit();conn.close()
        await q.edit_message_text(f"You choose ${amt} Plan\nSend ${amt} to USDT TRC20: YOUR_WALLET_HERE\nThen send proof",reply_markup=menu())
    elif d=="daily":
        today=str(date.today())
        if u[5]==today:await q.edit_message_text(f"Already claimed today! ${bal:.3f}",reply_markup=menu())
        else:
            conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=balance+0.02,last_daily=? WHERE user_id=?",(today,uid));conn.commit();conn.close()
            await q.edit_message_text(f"+$0.02 Daily! New ${bal+0.02:.3f}",reply_markup=menu())
    elif d=="game":
        if random.choice([True, False]):add_bal(uid,0.01);await q.edit_message_text(f"YOU WIN +$0.01 New ${bal+0.01:.3f}",reply_markup=menu())
        else:await q.edit_message_text(f"You lose! Try again ${bal:.3f}",reply_markup=menu())
    elif d=="invite":
        bn=(await context.bot.get_me()).username;link=f"https://t.me/{bn}?start={uid}"
        await q.edit_message_text(f"Invite link:\n{link}\nEarn 5% of invest!",reply_markup=menu())
    elif d=="withdraw":
        if bal<0.50:await q.edit_message_text(f"Need $0.50 you have ${bal:.3f}",reply_markup=menu())
        else:await q.edit_message_text(f"Send wallet address to withdraw ${bal:.3f}:",reply_markup=menu());context.user_data['w']=True
    elif d=="back":
        await q.edit_message_text(f"Main Menu Balance ${bal:.3f}",reply_markup=menu())

async def handle_msg(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('w'):
        wallet=update.message.text;u=get_user(update.effective_user.id);b=u[2]
        conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=0 WHERE user_id=?",(update.effective_user.id,));conn.commit();conn.close()
        await update.message.reply_text(f"Withdraw ${b:.3f} to {wallet} received! 24hrs",reply_markup=menu())
        context.user_data['w']=False
    else:
        await update.message.reply_text("Proof received!",reply_markup=menu())

def main():
    init_db();threading.Thread(target=run_flask,daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO,handle_msg))
    print("Bot Started!");app.run_polling()
if __name__=='__main__':main()
