from os import environ

from dotenv import load_dotenv
import streamlit as st
import telebot

from classifier.bert_classifier import BertClassifier
from db_action_handler import DBActionHandler
from db_entities import Thought


load_dotenv()
TOKEN = environ.get('TOKEN')
ADMIN_USERNAME = environ.get('ADMIN_USERNAME')

bot = telebot.TeleBot(TOKEN)
action_handler = DBActionHandler()

# some handlers can block adding new notes in the current state
# TODO check if we really need this: check that inline buttons are not recognized as text
add_new_command_state = True
current_note = Thought()
default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /random to get a random thought from your pull."
default_keyboard = telebot.types.ReplyKeyboardRemove(selective=False)


@st.cache
def load_classifier():
    return BertClassifier("models/fine_tuned_bert/230126_test_model/checkpoint-187")


bert_clf = load_classifier()


def get_buttons(note_status):
    # TODO add mapping of statuses to button names
    if note_status == 'in_progress':
        itembtn2 = telebot.types.InlineKeyboardButton('Done', callback_data='#done')
    else:
        itembtn2 = telebot.types.InlineKeyboardButton('Working on it', callback_data='#in_progress')

    markup = telebot.types.InlineKeyboardMarkup()
    itembtn1 = telebot.types.InlineKeyboardButton('Send me later', callback_data='#later')
    itembtn3 = telebot.types.InlineKeyboardButton('Not relevant', callback_data='#not_relevant')
    itembtn4 = telebot.types.InlineKeyboardButton('Edit category', callback_data='#edit_category')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    return markup


@bot.message_handler(commands=['random'])
def send_random_note(message):
    user = message.from_user
    # TODO move checking to decorator
    if user.username == ADMIN_USERNAME:
        global current_note
        current_note = action_handler.get_random_note()
        bot.send_message(
            user.id,
            f"Random thought from your pull: \n{current_note}",
            reply_markup=get_buttons(current_note.status),
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
            reply_markup=default_keyboard,
        )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user = message.from_user
    label = bert_clf.predict([message.text])[0][0]
    # TODO: add logic to handle different labels
    if label == 'relationships':
        label = 'personal'
    # TODO default values should be set in the Thought class
    default_urgency = 'week'
    default_status = 'open'
    default_eta = 0.5

    if user.username == ADMIN_USERNAME:
        if add_new_command_state:
            global current_note
            current_note = Thought(
                thought=message.text,
                label=label,
                urgency=default_urgency,
                status=default_status,
                eta=default_eta,
                date_created=None,
                date_completed=None
            )
            action_handler.add_thought(current_note)
            bot.send_message(
                user.id,
                f"Added\nThought: \"{message.text}\"\nCategory: \"{label}\"\n"
            )
        else:
            bot.send_message(
                user.id,
                default_prompt,
                reply_markup=default_keyboard,
            )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


# change the status of the note after pressing a button
@bot.callback_query_handler(func=lambda call: call.data in [
    '#done', '#in_progress', '#not_relevant'
])
def button_update_status(call):
    new_status = get_new_note_status(call.data)
    action_handler.update_note_status(current_note, new_status)
    bot.send_message(
        call.message.chat.id,
        f"Status updated to {new_status}.",
        reply_markup=default_keyboard,
    )

def get_new_note_status(callback_data: str):
    if callback_data == '#done':
        new_status = "done"
    elif callback_data == '#in_progress':
        new_status = 'in_progress'
    elif callback_data == '#not_relevant':
        new_status = 'not_relevant'
    else:
        new_status = current_note.status
    return new_status


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
