from os import environ

from dotenv import load_dotenv
import streamlit as st
import telebot

from classifier.bert_classifier import BertClassifier
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

session = db.get_session()
db_dml = db.DB_DML(session)

# now it's always true, probably some handlers can block adding new notes
add_new_command_state = True
default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /note to get a random thought from your pull."


@st.cache
def load_classifier():
    return BertClassifier("models/fine_tuned_bert/230126_test_model/checkpoint-187")


bert_clf = load_classifier()


@bot.message_handler(commands=['random'])
def send_random_note(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        thought = db_dml.get_random_note()
        global add_new_command_state
        # it is considered that user will interact with the note somehow, so adding new notes is blocked
        add_new_command_state = False
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
    # doesn't do anything but just invites to send a new note and sets the state to True
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
    labels, score = bert_clf.predict([message.text])
    label = labels[0]
    # TODO: add logic to handle different labels
    if label == 'relationships':
        label = 'personal'
    default_urgency = 'week'
    default_status = 'open'
    default_eta = 0.5

    if user.username == ADMIN_USERNAME:
        if add_new_command_state:
            db_dml.add_thought(
                message.text,
                label,
                default_urgency,
                default_status,
                default_eta,
            )
            bot.send_message(
                user.id,
                f"Added\nThought: \"{message.text}\"\nCategory: \"{label}\"\n"
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
