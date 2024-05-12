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


@bot.callback_query_handler(func=lambda call: call.data == 'proceed')
def proceed(call):
    is_member = check_join(user=call.from_user.id, channels=channels)

    if is_member is False:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='تایید', callback_data='proceed')
        markup.add(button)
        bot.send_message(chat_id=call.message.chat.id, text='باید در کانال ما عضو شوید @Remote_project_bot')
    else:
        bot.send_message(chat_id=call.message.chat.id, text='شما میتوانید از ربات استفاده کنید')



if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling()
