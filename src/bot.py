from os import environ

from dotenv import load_dotenv
import streamlit as st
import telebot

from classifier.rag import RAG
from db_action_handler import DBActionHandler
from db_entities import Thought


load_dotenv()
TOKEN = environ.get('TOKEN')
ADMIN_USERNAME = environ.get('ADMIN_USERNAME')

bot = telebot.TeleBot(TOKEN)
action_handler = DBActionHandler()

current_note = Thought()  # TODO: make it a class attribute of the bot
category_editing = False

default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /random to get a random thought from your pull."
default_keyboard = telebot.types.ReplyKeyboardRemove(selective=False)


@st.cache_resource
def load_category_classifier():
    return RAG()


clf_category = load_category_classifier()


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


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user = message.from_user
    label = clf_category.predict(message.text)["category"]
    # TODO default values should be set in the Thought class
    default_status = 'open'
    urgency = 'week'
    eta = 0.5
    global current_note
    global category_editing

    if not category_editing and user.username == ADMIN_USERNAME:
        global current_note
        current_note = Thought(
            thought=message.text,
            label=label,
            urgency=urgency,
            status=default_status,
            eta=eta,
            date_created=None,
            date_completed=None
        )
        action_handler.add_thought(current_note)
        label_text = telebot.formatting.hbold(label)
        urgency_text = telebot.formatting.hbold(urgency)
        response_message = f"Note: \"{message.text}\"\nCategory: {label_text}\nUrgency: {urgency_text}\n"
        if eta is not None:
            # convert to hours with minutes: 1.5h -> 1h 30min
            float_eta = float(eta)
            hours = int(float_eta)
            minutes = int((float_eta - hours) * 60)
            eta_text = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
            eta_text = telebot.formatting.hbold(eta_text)
            response_message = f"{response_message}ETA: {eta_text}\n"
        bot.send_message(
            user.id,
            # TODO: highlight values with a different color instead of quotes
            response_message,
            reply_markup=get_buttons(current_note.status),
            parse_mode='HTML',
        )
    elif category_editing and user.username == ADMIN_USERNAME:
        # TODO make sure the category is valid
        action_handler.update_note_category(current_note, message.text)
        bot.send_message(
            user.id,
            f"Category updated to '{message.text}'.",
            reply_markup=default_keyboard,
        )
        category_editing = False
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
    global current_note  # TODO change not current note, but the note linked to the message id
    action_handler.update_note_status(current_note, new_status)
    bot.send_message(
        call.message.chat.id,
        f"Status updated to {current_note.status}.",
        reply_markup=default_keyboard,
        # TODO: can I edit the previous message buttons? instead of sending buttons again as below
        # reply_markup=get_buttons(current_note.status),
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
