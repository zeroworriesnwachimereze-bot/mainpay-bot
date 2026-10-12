import os, sqlite3, threading, random
from datetime import date
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
BOT_TOKEN=os.getenv("BOT_TOKEN")
flask_app=Flask(__name__)
@flask_app.route('/')
def home():
    return "OK"
def run_flask():
    flask_app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
def init_db():
    c=sqlite3.connect('mainpay.db').cursor()
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0, referrals INTEGER DEFAULT 0, referred_by INTEGER, last_daily TEXT)");conn.commit();conn.close()
def get_user(uid):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("SELECT * FROM users WHERE user_id=?",(uid,));u=cur.fetchone();conn.close();return u
def add_user(uid,uname,ref=None):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("INSERT OR IGNORE INTO users (user_id,username,referred_by) VALUES (?,?,?)",(uid,uname,ref));conn.commit()
    if ref and ref!=uid:
        if get_user(ref):
            cur.execute("UPDATE users SET balance=balance+0.05,referrals=referrals+1 WHERE user_id=?",(ref,));conn.commit()
    conn.close()
def add_bal(uid,amt):
    conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?",(amt,uid));conn.commit();conn.close()
def menu():
    b1=InlineKeyboardButton("Balance",callback_data="balance");b2=InlineKeyboardButton("Daily $0.02",callback_data="daily");b3=InlineKeyboardButton("Game $0.01",callback_data="game");b4=InlineKeyboardButton("Invite $0.05",callback_data="invite");b5=InlineKeyboardButton("Withdraw",callback_data="withdraw")
    return InlineKeyboardMarkup([[b1],[b2],[b3],[b4],[b5]])
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id;uname=update.effective_user.username or "User";ref=None
    if context.args:
        try:ref=int(context.args[0])
        except:pass
    if not get_user(uid):
        add_user(uid,uname,ref)
    await update.message.reply_text(f"Welcome MainPay @{uname}! Daily $0.02 Game $0.01 Invite $0.05 Min $0.50",reply_markup=menu())
async def btn(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query;await q.answer();u=get_user(q.from_user.id);bal=u[2];d=q.data
    if d=="balance":await q.edit_message_text(f"Balance ${bal:.3f} Ref {u[3]}",reply_markup=menu())
    elif d=="daily":
        today=str(date.today())
        if u[5]==today:await q.edit_message_text(f"Already claimed! ${bal:.3f}",reply_markup=menu())
        else:
            conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=balance+0.02,last_daily=? WHERE user_id=?",(today,q.from_user.id));conn.commit();conn.close();await q.edit_message_text(f"+$0.02 New ${bal+0.02:.3f}",reply_markup=menu())
    elif d=="game":
        if random.choice([True,False]):add_bal(q.from_user.id,0.01);await q.edit_message_text(f"WIN +$0.01 New ${bal+0.01:.3f}",reply_markup=menu())
        else:await q.edit_message_text(f"Lose try again ${bal:.3f}",reply_markup=menu())
    elif d=="invite":
        bn=(await context.bot.get_me()).username;link=f"https://t.me/{bn}?start={q.from_user.id}";await q.edit_message_text(f"Invite {link} Refs {u[3]}",reply_markup=menu())
    elif d=="withdraw":
        if bal<0.50:await q.edit_message_text(f"Need $0.50 have ${bal:.3f}",reply_markup=menu())
        else:await q.edit_message_text(f"Send wallet for ${bal:.3f}",reply_markup=menu());context.user_data['w']=True
async def msg(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('w'):
        u=get_user(update.effective_user.id);b=u[2];conn=sqlite3.connect('mainpay.db');cur=conn.cursor();cur.execute("UPDATE users SET balance=0 WHERE user_id=?",(update.effective_user.id,));conn.commit();conn.close();await update.message.reply_text(f"Req ${b:.3f} wallet {update.message.text} 24h",reply_markup=menu());context.user_data['w']=False
def main():
    init_db();threading.Thread(target=run_flask,daemon=True).start();app=Application.builder().token(BOT_TOKEN).build();app.add_handler(CommandHandler("start",start));app.add_handler(CallbackQueryHandler(btn));app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg));app.run_polling()
if __name__=='__main__':main()
