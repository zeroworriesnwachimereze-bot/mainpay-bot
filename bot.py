import os
import sqlite3
import threading
import random
from datetime import date
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 0

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "MainPay Bot Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

def init_db():
    conn = sqlite3.connect('mainpay.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0, referrals INTEGER DEFAULT 0, referred_by INTEGER, last_daily TEXT)")
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('mainpay.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(user_id, username, referred_by=None):
    conn = sqlite3.connect('mainpay.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?,?,?)", (user_id, username, referred_by))
    conn.commit()
    if referred_by and referred_by != user_id:
        ref_user = get_user(referred_by)
        if ref_user:
            c.execute("UPDATE users SET balance = balance + 0.05, referrals = referrals + 1 WHERE user_id=?", (referred_by,))
            conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('mainpay.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
       
