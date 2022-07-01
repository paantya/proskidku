import time
import pytz
import telebot

from typing import Optional, Union

from datetime import datetime

from config_prod import TOKEN
from config_prod import NO_PHOTO

from config_prod import CHAT_ID, CHAT_ID_LOG, CHAT_TD_LOG

bot = telebot.TeleBot(TOKEN, parse_mode='MARKDOWN')  # You can set parse_mode by default. HTML or MARKDOWN


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)
    print(message)


def send_message(data, time_end, chat_id, time_limit=3.1):
    img = data['img']
    url = data['url']
    name = f"[{data['name']}]({url})"
    price = f"Цена: *{data['price_new'].replace(' ₽', '₽')}* (Скидка {data['pp']})"
    price_link = f"{data['price_new'].replace(' ₽', '₽')} (Скидка {data['pp']})"
    сharacteristics = '\n'.join([k + ': #' + v.replace(' ', '\_').replace('-', '\_').replace('`', '').replace("'",
                                                                                                              '').replace(
        "!", '').replace(",", '').replace(".", '') for k, v in data['сharacteristics'].items()])

    if img != NO_PHOTO:
        url_pic = f"[ ]({img})"
        disable_web_page_preview = False
    else:
        url_pic = ''
        disable_web_page_preview = True
    text = f'{url_pic}{name}\n{price}\n{сharacteristics}'

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(price_link, url=url))

    time_diff = time.time() - time_end
    print(f"\rtime_diff: {time_diff} {time_limit}", end='')
    time.sleep(time_limit)

    try:
        send_message_ = bot_send_message(chat_id,
                                         text,
                                         reply_markup=markup,
                                         #                                     entities=entities,
                                         disable_web_page_preview=disable_web_page_preview,
                                         disable_notification=True,
                                         )
        time_end = time.time()
    except Exception as e:
        text = f"Exception send_message: {e}"
        print(text)
        time.sleep(5)
        bot_send_message(chat_id=CHAT_ID_LOG, text=text, disable_notification=True)
        time_end = time.time()
        return None, time_end

    message_json_tmp = send_message_.json
    message_json = {
        'message_id': message_json_tmp['message_id'],
        'chat': {
            'id': message_json_tmp['chat']['id'],
        },
        "date": message_json_tmp['date'],
        "text": message_json_tmp['text'],
    }

    return message_json, time_end


# bot.infinity_polling()
def bot_send_message(chat_id: Union[int, str],
                     text: str,
                     parse_mode: Optional[str] = None,
                     reply_markup=None,
                     entities=None,
                     disable_web_page_preview: Optional[bool] = None,
                     disable_notification: Optional[bool] = True,
                     time_sleep: Union[bool, int] = False,
                     ):
    try:
        if time_sleep:
            if type(time_sleep) == int:
                time.sleep(time_sleep)
            else:
                time.sleep(5)
        message = bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
        )
    except Exception as e:
        text = f"Exception get_soup: {e}"
        print(text)
        message = None
    return message


# # bot.infinity_polling()
# def edit_message_text(data, message_json, chat_id = -1001686304047,time_limit=3.1 ):

# #     bot.get_me().de_json()
#     img = data['img']
#     url = data['url']
#     name = f"[{data['name']}]({url})"
#     price = f"*{data['price_new'].replace(' ₽','₽')}* (Старая цена: {data['price_old'].replace(' ₽','₽')}, {data['price_economy'].replace(' ₽','₽')}, {data['pp']})"
#     price_link = f"{data['price_new'].replace(' ₽','₽')} (Старая цена: {data['price_old'].replace(' ₽','₽')}, {data['price_economy'].replace(' ₽','₽')}, {data['pp']})"
#     сharacteristics = '\n'.join([k+': #'+v.replace(' ','\_') for k,v in data['сharacteristics'].items()])

#     if img != 'https://www.proskidku.ru/local/templates/.default/components/bitrix/catalog.element/proskidku/images/no_photo.png':
#         url_pic = f"[ ]({img})"
#         disable_web_page_preview = False
#     else:
#         url_pic = ''
#         disable_web_page_preview = True
#     text = f'{url_pic}{name}\n{price}\n{сharacteristics}'

#     markup = telebot.types.InlineKeyboardMarkup()
#     markup.add(telebot.types.InlineKeyboardButton(price_link, url=url))

#     time_diff = time.time() - time_end
#     time.sleep(0 if time_diff > time_limit else time_diff)

#     send_message_ = bot.edit_message_text(text,
#                                          chat_id=message_json['chat']['id'],
#                                          message_id=message_json['message_id'],
#                                          reply_markup=markup,
# #                                          entities=entities,
#                                          disable_web_page_preview=disable_web_page_preview,
#                                          disable_notification=True,
#                                         )
#     return send_message_.json


# bot.infinity_polling()

def upd_info(msg_json, n):
    datetime_now = datetime.now().astimezone().astimezone(tz=pytz.timezone('Europe/Moscow'))
    text = f'''Скидок доступно в канале и на сайте (last upd: `{datetime_now.strftime('%H:%m:%S %Y-%M-%d')}`):'''

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(n, url=f'https://t.me/ProSkidkuru'))

    try:
        time.sleep(1)
        bot.edit_message_text(
            text=text,
            chat_id=msg_json['chat']['id'],
            message_id=msg_json['message_id'],
            reply_markup=markup,
        )

    except Exception as e:
        text = f"Exception edit_message_text: {e}, message_json:{msg_json}"
        print(text)
        time.sleep(5)
        bot_send_message(chat_id=CHAT_ID_LOG, text=text, disable_notification=True)


def upd_info_log(msg_json, text, d, o, n):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(f"{d}, {o}, {n}", url=f'https://t.me/ProSkidkuru'))

    try:
        time.sleep(1)
        bot.edit_message_text(
            text=text,
            chat_id=msg_json['chat']['id'],
            message_id=msg_json['message_id'],
            reply_markup=markup,
        )
    except Exception as e:
        text = f"Exception edit_message_text: {e}, message_json:{msg_json}"
        print(text)
        time.sleep(5)
        bot_send_message(chat_id=CHAT_ID_LOG, text=text, disable_notification=True)


def delete_message(msg_json):
    try:
        time.sleep(4)
        now = datetime.now()
        dmsg = datetime.fromtimestamp(msg_json['date'])
        if (now - dmsg).days < 2:
            flag_delete_message = bot.delete_message(
                chat_id=msg_json['chat']['id'],
                message_id=msg_json['message_id'],
            )
            return flag_delete_message
        else:
            remsg = bot.edit_message_text(
                text='#продано',
                chat_id=msg_json['chat']['id'],
                message_id=msg_json['message_id'],
            )
            return remsg.json
    except Exception as e:
        text = f"Exception delete_message: {e}, message_json:{msg_json}"
        print(text)
        time.sleep(5)
        bot_send_message(chat_id=CHAT_ID_LOG, text=text, disable_notification=True)

        return False
