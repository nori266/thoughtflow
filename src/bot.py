from os import environ

from dotenv import load_dotenv
import streamlit as st
import telebot

from classifier.bert_classifier import BertClassifier
from classifier.gpt_classifier import GPTClassifier, GPTAllFieldsGenerator
from db_action_handler import DBActionHandler
from db_entities import Thought


load_dotenv()
TOKEN = environ.get('TOKEN')
ADMIN_USERNAME = environ.get('ADMIN_USERNAME')

bot = telebot.TeleBot(TOKEN)
action_handler = DBActionHandler()

"""Global variables"""
current_note = Thought()  # TODO: make it a class attribute of the bot
category_editing = False
last_note_message_id = None  # id of the bot message related to the last note (for editing)

default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /random to get a random thought from your pull."
default_keyboard = telebot.types.ReplyKeyboardRemove(selective=False)



@st.cache_resource
def load_category_classifier():
    # TODO make Bert a test version of category classifier
    #return BertClassifier("models/fine_tuned_bert/230126_test_model/checkpoint-187")
    return GPTClassifier()


@st.cache_resource
def load_all_fields_classifier():
    return GPTAllFieldsGenerator()


clf_category = load_category_classifier()
clf_all_fields = load_all_fields_classifier()


def get_buttons(note_status):
    # TODO add mapping of statuses to button names
    # FIXME: show all the buttons except the one with the current status
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


@bot.message_handler(commands=['last'])  # TODO add to bot commands
def send_last_n_notes(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        n = 5
        thoughts = action_handler.show_last_n(n)
        for thought in thoughts:
            bot.send_message(
                user.id,
                thought,
                reply_markup=get_buttons(thought.status),
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


@bot.message_handler(commands=['plot'])
def send_plots(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        plot_filename = action_handler.send_plots()
        bot.send_photo(
            user.id,
            open(plot_filename, 'rb'),
            reply_markup=default_keyboard,
        )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


def get_note_category(message):
    label = clf_category.predict(message.text)["category"]
    if label == 'relationships':
        label = 'personal'
    return label


def get_all_fields_prediction(message):
    return clf_all_fields.predict(message.text)


def format_response_message(message, label, urgency, eta=None):
    label_text = telebot.formatting.hbold(label)
    urgency_text = telebot.formatting.hbold(urgency)
    # TODO take text instead of message as an argument, or better take a Thought object (current_note)
    response_message = f"Note: \"{message.text}\"\nCategory: {label_text}\nUrgency: {urgency_text}\n"
    if eta is not None:
        float_eta = float(eta)
        hours = int(float_eta)
        minutes = int((float_eta - hours) * 60)
        eta_text = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
        eta_text = telebot.formatting.hbold(eta_text)
        response_message = f"{response_message}ETA: {eta_text}\n"
    return response_message


def handle_note_creation(message, label, prediction):
    global current_note
    current_note = Thought(
        thought=message.text,
        label=label,
        urgency=prediction["urgency"],
        status='open',
        eta=prediction["eta"],
        date_created=None,
        date_completed=None
    )
    action_handler.add_thought(current_note)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global current_note
    global category_editing
    global last_note_message_id
    user = message.from_user
    label = get_note_category(message)
    prediction = get_all_fields_prediction(message)
    handle_note_creation(message, label, prediction)

    if not category_editing and user.username == ADMIN_USERNAME:
        response_message = format_response_message(message, label, prediction["urgency"], prediction["eta"])
        sent_message = bot.send_message(user.id, response_message, reply_markup=get_buttons(current_note.status), parse_mode='HTML')
        last_note_message_id = sent_message.message_id
    elif category_editing and user.username == ADMIN_USERNAME:
        action_handler.update_note_category(current_note, message.text)
        bot.send_message(user.id, f"Category updated to '{message.text}'.", reply_markup=default_keyboard)
        category_editing = False
    else:
        bot.send_message(user.id, f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.")


# change the status of the note after pressing a button
@bot.callback_query_handler(func=lambda call: call.data in [
    '#done', '#in_progress', '#not_relevant'
])
def button_update_status(call):
    new_status = get_new_note_status(call.data)
    global current_note  # TODO change not current note, but the note linked to the message id
    action_handler.update_note_status(current_note, new_status)
    bot.send_message(
        call.message.chat.id,
        f"Status updated to {current_note.status}.",
        reply_markup=default_keyboard,
    )
    # TODO: same formatting as in the message handler
    # TODO: do not store last message id, but the message id linked to the note
    bot.edit_message_text(
        f"Note: {current_note.thought},\nCategory: {current_note.label},\nUrgency: {current_note.urgency},\n"
        f"ETA: {current_note.eta},\nStatus: {current_note.status}",
        call.message.chat.id,
        last_note_message_id,
        reply_markup=get_buttons(current_note.status)
    )


@bot.callback_query_handler(func=lambda call: call.data == '#edit_category')
def button_edit_category(call):
    global category_editing
    category_editing = True
    bot.send_message(
        call.message.chat.id,
        f"New category:",
        reply_markup=default_keyboard,
    )


def get_new_note_status(callback_data: str):
    if callback_data == '#done':
        new_status = "done"
    elif callback_data == '#in_progress':
        new_status = 'in_progress'
    elif callback_data == '#not_relevant':
        new_status = 'irrelevant'
    else:
        new_status = current_note.status
    return new_status


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
