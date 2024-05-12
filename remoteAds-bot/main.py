import mysql.connector
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import *


bot = TeleBot(token=TOKEN)


def check_join(user, channels):
    for i in channels:
        is_member = bot.get_chat_member(chat_id=i, user_id=user)

        if is_member.status in ['kicked', 'left']:
            return False
    return True


@bot.message_handler(commands=['start'])
def start(m):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='ادامه', callback_data='proceed')
    markup.add(button)
    try:
        with mysql.connector.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                sql = f'INSERT INTO users (id) VALUES ({m.from_user.id})'
                cursor.execute(sql)
                connection.commit()
        bot.send_message(chat_id=m.chat.id, text='سلام کاربر جدید', reply_markup=markup)
    except:
        bot.send_message(chat_id=m.chat.id, text='سلام کاربر قدیمی', reply_markup=markup)



if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling()
