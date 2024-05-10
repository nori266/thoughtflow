import platform
# Workaround for the issue with sqlite3 in streamlit share
if platform.system() != 'Darwin':
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from os import environ
from typing import Optional

from dotenv import load_dotenv
import streamlit as st
import telebot

from categories_to_html import CategoryTree
from db_action_handler import DBActionHandler
from db_entities import Thought
from rag import RAG


load_dotenv()
TOKEN = environ.get('TOKEN')
ADMIN_USERNAME = environ.get('ADMIN_USERNAME')

bot = telebot.TeleBot(TOKEN)
action_handler = DBActionHandler()

"""Global variables"""
category_editing = False
editing_message_id: Optional[int] = None
candidate_categories = ["AI Progress", "Chores", "Beauty > Hair and skin care", "Note", "Plan"]

default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /random to get a random thought from your pull."
default_keyboard = telebot.types.ReplyKeyboardRemove(selective=False)


@st.cache_resource
def load_category_classifier():
    return RAG()


@st.cache_resource
def load_category_tree():
    category_tree = CategoryTree()
    categories = action_handler.get_all_categories()
    category_tree.parse_categories(categories)
    return category_tree


clf_category = load_category_classifier()
tree = load_category_tree()


def get_response_buttons(note_status):
    # TODO add mapping of statuses to button names
    # FIXME: show all the buttons except the one with the current status
    if note_status == 'in_progress':
        itembtn2 = telebot.types.InlineKeyboardButton('✅Done', callback_data='#done')
    else:
        itembtn2 = telebot.types.InlineKeyboardButton('👩🏻‍💻Working on it', callback_data='#in_progress')

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('⏳Send me later', callback_data='#later')
    itembtn3 = telebot.types.InlineKeyboardButton('🚫Not relevant', callback_data='#not_relevant')
    itembtn4 = telebot.types.InlineKeyboardButton('🌿Edit category', callback_data='#edit_category')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    return markup


@bot.message_handler(commands=['random'])
def send_random_note(message):
    user = message.from_user
    # TODO move checking to decorator
    if user.username == ADMIN_USERNAME:
        random_note = action_handler.get_random_note()
        bot.send_message(
            user.id,
            f"Random thought from your pull: \n{random_note}",  # TODO format the message
            reply_markup=get_response_buttons(random_note.status),
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
                thought.note_text,
                reply_markup=get_response_buttons(thought.status),
            )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


@bot.message_handler(commands=['new'])
def add_new_note(message):
    # Invites to send a new note and sets category_editing to False
    global category_editing
    category_editing = False
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        bot.send_message(
            user.id,
            f"Please send me a new note to save.",
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


@bot.message_handler(commands=['tree'])
def show_tree(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        html_output = tree.generate_html_with_todos()
        with open('output_collapsible.html', mode='w', encoding='utf-8') as file:
            file.write(html_output)
        bot.send_document(
            user.id,
            open('output_collapsible.html', 'rb'),
            reply_markup=default_keyboard,
        )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


def get_note_category(message):
    return clf_category.predict(message.text)


def format_response_message(note_text, label, urgency, eta=None) -> str:
    label_text = telebot.formatting.hbold(label)
    urgency_text = telebot.formatting.hbold(urgency)
    # TODO take text instead of message as an argument, or better take a Thought object
    response_message = f"Note: \"{note_text}\"\nCategory: {label_text}\nUrgency: {urgency_text}\n"
    if eta is not None:
        float_eta = float(eta)
        hours = int(float_eta)
        minutes = int((float_eta - hours) * 60)
        eta_text = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
        eta_text = telebot.formatting.hbold(eta_text)
        response_message = f"{response_message}ETA: {eta_text}\n"
    return response_message


def handle_note_creation(note_text, label, urgency, eta, message_id, status):
    note = Thought(
        note_text=note_text,
        label=label,
        urgency=urgency,
        status=status,
        eta=eta,
        date_created=None,
        date_completed=None,
        message_id=message_id,
    )
    action_handler.add_thought(note)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global category_editing
    global candidate_categories
    user = message.from_user

    if not category_editing and user.username == ADMIN_USERNAME:
        model_prediction = get_note_category(message)
        label = model_prediction['category']
        candidate_categories = model_prediction['categories_for_user_selection']
        status = "open"
        urgency = 'week'
        eta = 0.5
        response_message_text: str = format_response_message(message.text, label, urgency, eta)
        response_message = bot.send_message(user.id, response_message_text, reply_markup=get_response_buttons(status), parse_mode='HTML')
        handle_note_creation(message.text, label, urgency, eta, response_message.message_id, status)
        tree.add_todo_to_category(label, message.text)
    elif category_editing and user.username == ADMIN_USERNAME:
        global editing_message_id
        updated_note = action_handler.update_note_category(editing_message_id, message.text)
        bot.send_message(
            user.id,
            f'Category of the note "{updated_note.note_text}" updated to "{updated_note.label}".',
            reply_markup=default_keyboard,
        )
        edited_response_message_text: str = format_response_message(
            updated_note.note_text, updated_note.label, updated_note.urgency, updated_note.eta
        )
        bot.edit_message_text(
            edited_response_message_text,
            user.id,
            editing_message_id,
            reply_markup=get_response_buttons(updated_note.status),
            parse_mode='HTML'
        )
        category_editing = False
        editing_message_id = None
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
    message_id = call.message.message_id
    note = action_handler.update_note_status(message_id, new_status)
    bot.send_message(
        call.message.chat.id,
        f'Status of the note "{note.note_text}" updated to "{note.status}".',
        reply_markup=default_keyboard,
    )
    response_message_text: str = format_response_message(note.note_text, note.label, note.urgency, note.eta)
    bot.edit_message_text(
        response_message_text,
        call.message.chat.id,
        message_id,
        reply_markup=get_response_buttons(note.status),
        parse_mode='HTML'
    )


@bot.callback_query_handler(func=lambda call: call.data == '#edit_category')
def button_edit_category(call):
    global category_editing
    global editing_message_id
    global candidate_categories
    category_editing = True
    editing_message_id = call.message.message_id
    buttons = [
        telebot.types.KeyboardButton(category) for category in candidate_categories
    ]
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    bot.send_message(
        call.message.chat.id,
        "Choose a new category from the list or type a new one:",
        reply_markup=keyboard,
    )


# @bot.callback_query_handler(func=lambda call: call.data.startswith('#category_'))
# def button_edit_category(call):
#     global category_editing
#     global editing_message_id
#     new_category = call.data.split('_')[1]
#     updated_note = action_handler.update_note_category(editing_message_id, new_category)
#     bot.send_message(
#         call.message.chat.id,
#         f'Category of the note "{updated_note.note_text}" updated to "{updated_note.label}".',
#         reply_markup=default_keyboard,
#     )
#     edited_response_message_text: str = format_response_message(
#         updated_note.note_text, updated_note.label, updated_note.urgency, updated_note.eta
#     )
#     bot.edit_message_text(
#         edited_response_message_text,
#         call.message.chat.id,
#         editing_message_id,
#         reply_markup=get_response_buttons(updated_note.status),
#         parse_mode='HTML'
#     )
#     category_editing = False
#     editing_message_id = None


def get_new_note_status(callback_data: str):
    if callback_data == '#done':
        new_status = "done"
    elif callback_data == '#in_progress':
        new_status = 'in_progress'
    elif callback_data == '#not_relevant':
        new_status = 'irrelevant'
    else:
        new_status = None
    return new_status


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
