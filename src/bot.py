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

session = db.get_session()
db_dml = db.DB_DML(session)

# now it's always true, probably some handlers can block adding new notes
add_new_command_state = True
current_note = db.Thought()
default_prompt = "Please use /new command to add new thought to your pull " \
                 "or /random to get a random thought from your pull."


@st.cache
def load_classifier():
    return BertClassifier("models/fine_tuned_bert/230126_test_model/checkpoint-187")


bert_clf = load_classifier()


def get_markup(status):
    if status == 'in_progress':
        itembtn2 = telebot.types.InlineKeyboardButton('Done', callback_data='#done')
    else:
        itembtn2 = telebot.types.InlineKeyboardButton('Working on it', callback_data='#in_progress')

    markup = telebot.types.InlineKeyboardMarkup()
    itembtn1 = telebot.types.InlineKeyboardButton('Send me later', callback_data='#later')
    itembtn3 = telebot.types.InlineKeyboardButton('Not relevant', callback_data='#not_relevant')
    itembtn4 = telebot.types.InlineKeyboardButton('Edit category', callback_data='#edit_category')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    return markup


def remove_keyboard():
    # TODO set as default keyboard for all messages
    return telebot.types.ReplyKeyboardRemove(selective=False)


@bot.message_handler(commands=['random'])
def send_random_note(message):
    user = message.from_user
    if user.username == ADMIN_USERNAME:
        global current_note
        current_note = db_dml.get_random_note()
        # global add_new_command_state
        # it is considered that user will interact with the note somehow, so adding new notes is blocked
        # add_new_command_state = False
        bot.send_message(
            user.id,
            f"Random thought from your pull: \n{current_note}",
            reply_markup=get_markup(current_note.status),
        )
        # bot.register_next_step_handler(message, interact_with_note)
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
            reply_markup=remove_keyboard(),
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
            global current_note
            current_note = db.Thought(
                thought=message.text,
                label=label,
                urgency=default_urgency,
                status=default_status,
                eta=default_eta,
                date_created=None,
                date_completed=None
            )
            db_dml.add_thought(current_note)
            # db_dml.add_thought(
            #     message.text,
            #     label,
            #     default_urgency,
            #     default_status,
            #     default_eta,
            # )
            bot.send_message(
                user.id,
                f"Added\nThought: \"{message.text}\"\nCategory: \"{label}\"\n"
            )
        else:
            bot.send_message(
                user.id,
                default_prompt,
                reply_markup=remove_keyboard(),
            )
    else:
        bot.send_message(
            user.id,
            f"You are not authorized to use this bot. Please contact @{ADMIN_USERNAME} to get access.",
        )


# change the status of the note after pressing a button
@bot.callback_query_handler(func=lambda call: call.data in [
    '#done', '#in_progress', '#not_relevant', '#later', '#edit_category'
])
def callback_worker(call):
    if call.data == '#done':
        new_status = "done"
        # current_note.date_completed = db_dml.get_current_date()
    elif call.data == '#in_progress':
        new_status = 'in_progress'
    elif call.data == '#not_relevant':
        new_status = 'not_relevant'
    # elif call.data == '#later':

    else:
        new_status = current_note.status

    if new_status != current_note.status:
        db_dml.update_note_status(current_note, new_status)
    bot.send_message(
        call.message.chat.id,
        f"Status updated to {new_status}.",
        reply_markup=remove_keyboard(),
    )
    # elif call.data == '#edit_category':
    #     bot.send_message(
    #         call.message.chat.id,
    #         f"Please send me a new category for the thought.",
    #     )  # TODO: add logic to handle new category


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
