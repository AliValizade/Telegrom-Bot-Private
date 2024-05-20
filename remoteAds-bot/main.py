import mysql.connector
from mysql.connector import errorcode
import re
from telebot import TeleBot
from telebot import formatting
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery

from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

from config import *

# Create accounts table in Database 
def create_accounts_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS accounts (
        id BIGINT PRIMARY KEY,
        balance INT DEFAULT 0,
        lang VARCHAR(255) DEFAULT 'fa'
    );
    """
    try:
        # Establish the connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        # Execute the query
        cursor.execute(create_table_query)
        # Commit the changes
        connection.commit()
        print("Table 'accounts' created successfully.")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("Table already exists.")
        else:
            print(f"Error: {err.msg}")
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

def delete_row_from_accounts(ids):
    format_strings = ','.join(['%s'] * len(ids))
    delete_row_query = f"DELETE FROM accounts WHERE id IN ({format_strings});"
    try:
        # Establish the connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        # Execute the query
        cursor.execute(delete_row_query, ids)
        # Commit the changes
        connection.commit()
        print("The row deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err.msg}")
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

# Call the function to delete rows, fill the list by ids you want to delete.
delete_row_from_accounts([])
# Call the function to create the table
create_accounts_table()

state_storage = StateMemoryStorage()

bot = TeleBot(token=TOKEN, state_storage=state_storage, parse_mode='HTML')

# Classes 
class Support(StatesGroup):
    text = State()
    respond = State()
    ads = State()
    ad_type = State()

# Functions 
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
    sql = f"SELECT balance FROM accounts WHERE id = {user}"
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
    return result

# Start 
@bot.message_handler(commands=['start'])
def start(m):
    markup2 = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='کانال درج آگهی رایگان', callback_data='proceed', url='https://t.me/remote_ads')
    markup2.add(button)
    try:
        with mysql.connector.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                sql = f'INSERT INTO accounts (id) VALUES ({m.from_user.id})'
                cursor.execute(sql)
                connection.commit()
        bot.send_message(chat_id=m.chat.id, text='سلام کاربر جدید\nبرای استفاده از امکانات ربات و درج آگهی لطفا در کانال آگهی رایگان ما عضو شوید.', reply_markup=markup2)
    except mysql.connector.Error as err:
        print("خطای دیتابیس:", err)
        # bot.send_message(chat_id=m.chat.id, text='سلام کاربر قدیمی', reply_markup=markup2)
        with mysql.connector.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                sql = f"SELECT lang FROM accounts WHERE id = {m.from_user.id}"
                cursor.execute(sql)
                result = cursor.fetchone()

                if result is None:
                    token = m.text.split()
                    if len(token) > 1:
                        sql = f"UPDATE accounts SET balance = balance + 10000 WHERE id = {token[1]}"
                        cursor.execute(sql)
                        connection.commit()

                    sql = f"INSERT INTO accounts(id) VALUES ({m.from_user.id})"
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
                        markup.add("👤 حساب کاربری", "💲 حمایت از کانال", "👨‍👦‍👦 زیرمجموعه گیری", "☎ پشتیبانی")

                        bot.send_message(chat_id=m.chat.id, text=formatting.format_text(
                            formatting.hbold(f'سلام {m.from_user.first_name}'),
                            formatting.hbold(f'⚡ به ربات درج آگهی رایگان خوش آمدید'),
                            formatting.hitalic(f'با این ربات میتوانید آگهی های خود را بصورت خودکار در کانال درج آگهی رایگان'),
                            formatting.hunderline('@remote_ads'),
                            formatting.hitalic('ثبت کنید.'),
                            separator="\n"
                            ),
                            reply_markup=markup)
                    else:
                        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                        markup.add("➕ Submit Ads")
                        markup.add("👤 My Account", "💲 Add Funds", "👨‍👦‍👦 Referral", "☎ Support")

                        bot.send_message(chat_id=m.chat.id, text=f"""ٌHi <b>{m.from_user.first_name}</b>,
                                        Welcome to my bot, ⚡
                                        With this robot, you can automatically register your ads in agahi724 channel.
                                        تغییر زبان:👉 /lang""", reply_markup=markup)


# change language 
@bot.message_handler(commands=['lang'])
def change_lang(m):
    markup = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton(text='English', callback_data='en')
    button2 = InlineKeyboardButton(text='فارسی', callback_data='fa')
    markup.add(button1, button2)

    bot.send_message(chat_id=m.chat.id, text="""کاربر گرامی لطفا زبان خود را انتخاب کنید:
                     Please select your language:""", reply_markup=markup)
    
# Reply Keyboard 
@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def account(m):
    balance = user_balance(user=m.from_user.id)
    bot.send_message(chat_id=m.chat.id, text=f"""ℹ اطلاعات حساب کاربری شما:
                     👤 نام کاربری: <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>
                     🆔 شناسه کاربری: <code>{m.from_user.id}</code>
                     💲 موجودی: {balance[0]} تومان""")

# Submit Ads
@bot.message_handler(func=lambda m: m.text == "➕ ثبت آگهی")
def select_ad_type(m: Message):
    markup = InlineKeyboardMarkup(row_width=3)
    btn1 = InlineKeyboardButton(text='کارجو ', callback_data='worker')
    btn2 = InlineKeyboardButton(text='کارفرما', callback_data='employer')
    btn3 = InlineKeyboardButton(text='فروشنده', callback_data='seller')
    markup.add(btn1, btn2, btn3)
    bot.send_message(chat_id=m.chat.id, text="""لطفا نوع آگهی خود را انتخاب کنید:""", reply_markup=markup)
    bot.set_state(user_id=m.from_user.id, state=Support.ads, chat_id=m.chat.id)

@bot.callback_query_handler(func=lambda call: call.data in ['worker', 'employer', 'seller'])
def ad_title(call: CallbackQuery):
    global title
    if call.data == 'worker':
        title = 'انجام دهنده هستم'
    elif call.data == 'employer':
        title = 'درخواست کننده هستم'
    elif call.data == 'seller':
        title = 'فروشنده هستم'
    bot.send_message(chat_id=call.message.chat.id, text='لطفا متن آگهی خود را ارسال کنید:')

@bot.message_handler(state=Support.ads)
def check_ad_request(m: Message):
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton(text='رد کردن', callback_data='deny')
    btn2 = InlineKeyboardButton(text='تایید کردن', callback_data='confirm')
    markup.add(btn1, btn2)
    forwarded_m = bot.forward_message(chat_id=admins[0], from_chat_id=m.chat.id, message_id=m.message_id)
    bot.send_message(chat_id=admins[0], text=f"درخواست ثبت آگهی از سمت کاربر:‌ @{m.from_user.username}\nid: {m.from_user.id}", reply_markup=markup, reply_to_message_id=forwarded_m.message_id)
    bot.send_message(chat_id=m.chat.id, text='آگهی شما در صورت تایید ادمین تا ساعاتی دیگر منتشر میشود.')
    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'deny')
def deny(call: CallbackQuery):
    pattern = r'id: \d+'
    user = re.findall(pattern=pattern, string=call.message.text)[0].split()[1]
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(text='درخواست رد شد😢', callback_data='aaa')
    markup.add(btn)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.send_message(chat_id=int(user), text='متاسفانه درخواست شما توسط ادمین رد شد.⛔')

@bot.callback_query_handler(func=lambda call: call.data == 'confirm')
def confirm(call: CallbackQuery):
    pattern = r'id: \d+'
    user = re.findall(pattern=pattern, string=call.message.text)[0].split()[1]
    username = call.message.text.split("@")[1].split("\n")[0]
    # Fetch the message text from the forwarded message
    forwarded_message = bot.forward_message(
        chat_id=call.message.chat.id, 
        from_chat_id=call.message.chat.id, 
        message_id=call.message.reply_to_message.message_id
    )
    # Get the text of the forwarded message
    message_text = '📌 ' + title + '\n\n' + forwarded_message.text + '\n' + '============' + '\n' + '@' + username

    # Create the inline keyboard for the published ad
    markup1 = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton(text='➕ ثبت آگهی جدید', callback_data='aaaa', url='https://t.me/Remote_project_bot')
    btn2 = InlineKeyboardButton(text='☎ پشتیبانی', callback_data='aaaa', url='https://t.me/TitechCo')
    markup1.add(btn1, btn2)

    # Send the message to the channel with the inline keyboard
    bot.send_message(
        chat_id=-1002111355264, 
        text=message_text, 
        reply_markup=markup1
    )
    # Update the admin's message to reflect the confirmation
    markup2 = InlineKeyboardMarkup()
    btn2 = InlineKeyboardButton(text='درخواست تایید شد😉', callback_data='aaa')
    markup2.add(btn2)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup2)

    # Notify the user that their ad was approved
    bot.send_message(chat_id=int(user), text='آگهی شما با موفقیت ثبت شد.✅')

# Support State handlers 
@bot.message_handler(func=lambda m: m.text == "☎ پشتیبانی")
def sup(m):
    bot.send_message(chat_id=m.chat.id, text="""لطفا پیام خود را ارسال کنید:""")
    bot.set_state(user_id=m.from_user.id, state=Support.text, chat_id=m.chat.id)
    
@bot.message_handler(state=Support.text)
def sup_text(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='پاسخ', callback_data=m.from_user.id))
    bot.send_message(chat_id=95045499, text=f"""یک پیام از <code>{m.from_user.id}</code> با نام کاربری @{m.from_user.username} دریافت شد:
                     متن پیام:
                     <b>{escape_special_characters(m.text)}</b>""", reply_markup=markup)
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
                         <b>{escape_special_characters(m.text)}</b>""")
        bot.send_message(chat_id=m.chat.id, text='پاسخ شما ارسال شد.')

        del texts[chat_id]
        chat_ids.remove(chat_id)
    else:
        bot.send_message(chat_id=m.chat.id, text='اشتباهی رخ داده، لطفا دوباره تلاش کنید.')

    bot.delete_state(user_id=m.from_user.id, chat_id=m.chat.id)

# callback lang 
@bot.callback_query_handler(func=lambda call: call.data == 'en')
def english(call):
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"UPDATE accounts SET lang = 'en' WHERE id = {call.from_user.id}"
            cursor.execute(sql)
            connection.commit()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("➕ Submit Ads")
    markup.add("👤 My Account", "💲 Add Funds", "👨‍👦‍👦 Referral", "☎ Support")

    bot.send_message(chat_id=call.message.chat.id, text=f"""ٌHi <b>{call.from_user.first_name}</b>,
                     Welcome to my bot, ⚡
                     With this robot, you can automatically register your ads in agahi724 channel.
                     تغییر زبان:👉 /lang""", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'fa')
def farsi(call):
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"UPDATE accounts SET lang = 'fa' WHERE id = {call.from_user.id}"
            cursor.execute(sql)
            connection.commit()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("➕ ثبت آگهی")
    markup.add("👤 حساب کاربری", "💲 شارژ حساب", "👨‍👦‍👦 زیرمجموعه گیری", "☎ پشتیبانی")

    bot.send_message(chat_id=call.message.chat.id, text=f"""سلام <b>{call.from_user.first_name}</b>,
                     به ربات ما خوش آمدید، ⚡
                     با این ربات میتوانید آگهی های خود را بصورت خودکار در کانال آگهی724 ثبت کنید.
                     Change Language:👉 /lang""", reply_markup=markup)
    
# Forced join 
@bot.callback_query_handler(func=lambda call: call.data == 'proceed')
def proceed(call):
    is_member = check_join(user=call.from_user.id, channels=channels)

    if is_member is False:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='تایید', callback_data='proceed')
        markup.add(button)
        bot.send_message(chat_id=call.message.chat.id, text='جهت درج آگهی رایگان در کانال ما عضو شوید @Remote_ads', reply_markup=markup)
    else:
        bot.send_message(chat_id=call.message.chat.id, text='شما میتوانید از ربات استفاده کنید')

# charge account handler
@bot.message_handler(func=lambda m: m.text == "💲 حمایت از کانال")
def charge_account(m):
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(text='50.000 تومان', callback_data='50')
    btn2 = InlineKeyboardButton(text='25.000 تومان', callback_data='25')
    markup.add(btn1, btn2)
    bot.send_message(chat_id=m.chat.id, text='مبلغ موردنظر خود را جهت حمایت از کانال انتخاب کنید:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == '50')
def ten(call):
    markup = InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton(text='پرداخت', url=f"https://youraddress/zarinpal/request/?user={call.from_user.id}")
    markup.add(btn)
    bot.send_message(chat_id=call.message.chat.id, text='لینک پرداخت:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == '25')
def twenty(call):
    markup = InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton(text='پرداخت', url=f"https://youraddress/zarinpal/request/?user={call.from_user.id}")
    markup.add(btn)
    bot.send_message(chat_id=call.message.chat.id, text='لینک پرداخت:', reply_markup=markup)

# Referral link handler
@bot.message_handler(func=lambda m: m.text == "👨‍👦‍👦 زیرمجموعه گیری")
def referral(m):
    with open('ref.jpg', 'rb') as photo:
        bot.send_photo(chat_id=m.chat.id, photo=photo, caption=f"""این لینک رفرال شماست:
                       
https://t.me/Remote_project_bot?start={m.from_user.id}""")

# Support callback handler 
@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    bot.send_message(chat_id=call.message.chat.id, text=f"ارسال پیام به <code>{call.data}</code>:")

    chat_ids.append(int(call.data))

    bot.set_state(user_id=call.from_user.id, state=Support.respond, chat_id=call.message.chat.id)

# polling() 
if __name__ == "__main__":
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.remove_webhook()
    bot.infinity_polling()
