from os import environ

from dotenv import load_dotenv
import telebot

import db_operations as db


load_dotenv()
TOKEN = environ.get('TOKEN')
ADMIN_USERNAME = environ.get('ADMIN_USERNAME')

bot = telebot.TeleBot(TOKEN)

markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
itembtn1 = telebot.types.KeyboardButton('Send me later')
# TODO if status Open, then 'working on it', if in_progress, then 'done'
itembtn2 = telebot.types.KeyboardButton('Working on it')
# itembtn2 = telebot.types.KeyboardButton('Done')
itembtn3 = telebot.types.KeyboardButton('Not relevant')
markup.add(itembtn1, itembtn2, itembtn3)

db_connection = db.get_connection()

add_new_command_state = False
default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /note to get a random thought from your pull."


@bot.message_handler(commands=['random'])
def send_random_note(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        thought = db.get_random_note(db_connection)
        bot.send_message(
            user.id,
            f"Random thought from your pull: \n{thought}",
            reply_markup=markup
        )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


@bot.message_handler(commands=['new'])
def add_new_note(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        global add_new_command_state
        add_new_command_state = True
        bot.send_message(
            user.id,
            f"Please send me a new thought to add to your pull.",
        )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user = message.from_user
    default_class = 'todo'
    default_priority = 'week'
    default_eta = 1
    if user.username == ADMIN_USERNAME:
        if add_new_command_state:
            db.add_thought(db_connection, message.text, default_class, default_priority, 1)
            bot.send_message(
                user.id,
                f"New thought added to your pull with a label \"{default_class}\" and priority \"{default_priority}\"."
                f" ETA is {default_eta} hour.",
            )
        else:
            bot.send_message(
                user.id,
                default_prompt,
            )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
