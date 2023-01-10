from os import environ

from dotenv import load_dotenv
import telebot

import db_operations as db


load_dotenv()
TOKEN = environ.get('TOKEN')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_random_note(message):
    thought = db.get_random_note()
    bot.send_message(
        message.from_user.id,
        f"Revisit this thought: \n{thought}",
    )


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
