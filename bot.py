from os import environ

from dotenv import load_dotenv
import telebot

from push_random_note import get_random_note

load_dotenv()
TOKEN = environ.get('TOKEN')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def command_help(message):
    thought = get_random_note()
    bot.send_message(
        message.from_user.id,
        f"Revisit this thought: \n{thought}",
    )


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
