import os
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)



