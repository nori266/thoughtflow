from os import environ

from dotenv import load_dotenv
import telebot

from bert_clf import model
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

print(model.config)


@bot.message_handler(commands=['note'])
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


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
