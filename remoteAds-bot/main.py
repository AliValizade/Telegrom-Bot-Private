import mysql.connector
import re
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

from config import *

state_storage = StateMemoryStorage()

bot = TeleBot(token=TOKEN, state_storage=state_storage)

############################################## Classes ##############################################
class Support(StatesGroup):
    text = State()
    respond = State()

############################################## Functions ##############################################

def escape_special_characters(text):
    special_characters = r"[\*\_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!]"
    return re.sub(special_characters, r'\\\g<0>', text)

def check_join(user, channels):
    for i in channels:
        is_member = bot.get_chat_member(chat_id=i, user_id=user)

        if is_member.status in ['kicked', 'left']:
            return False
    return True

def user_balance(user):
    sql = f"SELECT balance FROM users WHERE id = {user}"
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
    return result

############################################## Start ##############################################

@bot.message_handler(commands=['start'])
def start(m):
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"SELECT lang FROM users WHERE id = {m.from_user.id}"
            cursor.execute(sql)
            result = cursor.fetchone()

            if result is None:
                sql = f"INSERT INTO users(id) VALUES ({m.from_user.id})"
                cursor.execute(sql)
                connection.commit()

                markup = InlineKeyboardMarkup(row_width=1)
                button1 = InlineKeyboardButton(text='English', callback_data='en')
                button2 = InlineKeyboardButton(text='فارسی', callback_data='fa')
                markup.add(button1, button2)

                bot.send_message(chat_id=m.chat.id, text='کاربر گرامی لطفا زبان خود را انتخاب کنید:\nPlease select your language:', reply_markup=markup)

            else:
                if result[0] == 'fa':
                    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    markup.add("➕ ثبت آگهی")
                    markup.add("👤 حساب کاربری", "💲 شارژ حساب", "👨‍👦‍👦 زیرمجموعه گیری", "☎ پشتیبانی")

                    bot.send_message(chat_id=m.chat.id, text=f"""سلام <b>{m.from_user.first_name}</b>,
                                     به ربات ما خوش آمدید، ⚡
                                     با این ربات میتوانید آگهی های خود را بصورت خودکار در کانال آگهی724 ثبت کنید.
                                     Change Language:👉 /lang""", parse_mode='HTML', reply_markup=markup)
                else:
                    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    markup.add("➕ Submit Ads")
                    markup.add("👤 My Account", "💲 Add Funds", "👨‍👦‍👦 Referral", "☎ Support")

                    bot.send_message(chat_id=m.chat.id, text=f"""ٌHi <b>{m.from_user.first_name}</b>,
                                     Welcome to my bot, ⚡
                                     With this robot, you can automatically register your ads in agahi724 channel.
                                     تغییر زبان:👉 /lang""", parse_mode='HTML', reply_markup=markup)

    # markup = InlineKeyboardMarkup()
    # button = InlineKeyboardButton(text='ادامه', callback_data='proceed')
    # markup.add(button)
    # try:
    #     with mysql.connector.connect(**db_config) as connection:
    #         with connection.cursor() as cursor:
    #             sql = f'INSERT INTO users (id) VALUES ({m.from_user.id})'
    #             cursor.execute(sql)
    #             connection.commit()
    #     bot.send_message(chat_id=m.chat.id, text='سلام کاربر جدید', reply_markup=markup)
    # except mysql.connector.Error as err:
    #     print("خطای دیتابیس:", err)
    #     bot.send_message(chat_id=m.chat.id, text='سلام کاربر قدیمی', reply_markup=markup)

############################################## change language ##############################################

@bot.message_handler(commands=['lang'])
def change_lang(m):
    markup = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton(text='English', callback_data='en')
    button2 = InlineKeyboardButton(text='فارسی', callback_data='fa')
    markup.add(button1, button2)

    bot.send_message(chat_id=m.chat.id, text="""کاربر گرامی لطفا زبان خود را انتخاب کنید:
                     Please select your language:""", reply_markup=markup)
    
############################################## Reply Keyboard ##############################################

@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def account(m):
    balance = user_balance(user=m.from_user.id)
    bot.send_message(chat_id=m.chat.id, text=f"""ℹ اطلاعات حساب کاربری شما:
                     👤 نام کاربری: <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>
                     🆔 شناسه کاربری: <code>{m.from_user.id}</code>
                     💲 موجودی: {balance[0]} تومان""", parse_mode='HTML')
    
############################################## Support State handlers ##############################################

@bot.message_handler(func=lambda m: m.text == "☎ پشتیبانی")
def sup(m):
    bot.send_message(chat_id=m.chat.id, text="""لطفا پیام خود را ارسال کنید:""")
    bot.set_state(user_id=m.from_user.id, state=Support.text, chat_id=m.chat.id)
    
@bot.message_handler(state=Support.text)
def sup_text(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='پاسخ', callback_data='m.from_user.id'))
    bot.send_message(chat_id=95045499, text=f"""یک پیام از <code>{m.from_user.id}</code> با نام کاربری @{m.from_user.username} دریافت شد:
                     متن پیام:
                     <b>{escape_special_characters(m.text)}</b>""", reply_markup=markup, parse_mode='HTML')
    bot.send_message(chat_id=m.chat.id, text='پیام شما برای ادمین ارسال شد.')

    texts[m.from_user.id] = m.text

    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)

@bot.message_handler(state=Support.respond)
def answer_text(m):
    chat_id = chat_ids[-1]

    if chat_id in texts:
        bot.send_message(chat_id=chat_id, text=f"""پیام شما:
                         <i>{escape_special_characters(texts[chat_id])}</i>
                         پاسخ پشتیبانی:
                         <b>{escape_special_characters(m.text)}</b>""", parse_mode="HTML")
        bot.send_message(chat_id=m.chat.id, text='پاسخ شما ارسال شد.')

        del texts[chat_id]
        chat_ids.remove(chat_id)
    else:
        bot.send_message(chat_id=m.chat.id, text='اشتباهی رخ داده، لطفا دوباره تلاش کنید.')

    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)

############################################## callback lang ##############################################

@bot.callback_query_handler(func=lambda call: call.data == 'en')
def english(call):
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"UPDATE users SET lang = 'en' WHERE id = {call.from_user.id}"
            cursor.execute(sql)
            connection.commit()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("➕ Submit Ads")
    markup.add("👤 My Account", "💲 Add Funds", "👨‍👦‍👦 Referral", "☎ Support")

    bot.send_message(chat_id=call.message.chat.id, text=f"""ٌHi <b>{call.from_user.first_name}</b>,
                     Welcome to my bot, ⚡
                     With this robot, you can automatically register your ads in agahi724 channel.
                     تغییر زبان:👉 /lang""", parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'fa')
def farsi(call):
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"UPDATE users SET lang = 'fa' WHERE id = {call.from_user.id}"
            cursor.execute(sql)
            connection.commit()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("➕ ثبت آگهی")
    markup.add("👤 حساب کاربری", "💲 شارژ حساب", "👨‍👦‍👦 زیرمجموعه گیری", "☎ پشتیبانی")

    bot.send_message(chat_id=call.message.chat.id, text=f"""سلام <b>{call.from_user.first_name}</b>,
                     به ربات ما خوش آمدید، ⚡
                     با این ربات میتوانید آگهی های خود را بصورت خودکار در کانال آگهی724 ثبت کنید.
                     Change Language:👉 /lang""", parse_mode='HTML', reply_markup=markup)
    
############################################## Forced join ##############################################

@bot.callback_query_handler(func=lambda call: call.data == 'proceed')
def proceed(call):
    is_member = check_join(user=call.from_user.id, channels=channels)

    if is_member is False:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='تایید', callback_data='proceed')
        markup.add(button)
        bot.send_message(chat_id=call.message.chat.id, text='باید در کانال ما عضو شوید @Remote_ad , @Remote_ads')
    else:
        bot.send_message(chat_id=call.message.chat.id, text='شما میتوانید از ربات استفاده کنید')

############################################## Support callback handler ##############################################

@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    bot.send_message(chat_id=call.message.chat.id, text=f"ارسال پیام به <code>{call.from_user.id}</code>:", parse_mode='HTML')

    chat_ids.append(call.from_user.id)

    bot.set_state(user_id=call.from_user.id, state=Support.respond, chat_id=call.message.chat.id)
        

############################################## polling() ##############################################

if __name__ == "__main__":
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.remove_webhook()
    bot.infinity_polling()
