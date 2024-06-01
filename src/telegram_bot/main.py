import os
import logging

import requests
from dotenv import load_dotenv
# from telebot.async_telebot import AsyncTeleBot
from telebot import TeleBot, custom_filters
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.handler_backends import State, StatesGroup  # States
from telebot.storage import StateMemoryStorage

import db

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

state_storage = StateMemoryStorage()
bot = TeleBot(API_TOKEN, state_storage=state_storage)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(levelname)s:     [%(asctime)s] %(message)s')


class MyStates(StatesGroup):
    getting_info = State()
    answering_questions = State()


def save_file(document, file_info):
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = os.path.join(DOWNLOAD_DIR, document.file_name)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)


def gen_markup():
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(KeyboardButton("Clear Chat History"))
    markup.add(KeyboardButton("I want to ask a question"))
    markup.add(KeyboardButton("I want to add info"))
    return markup


def handle_keyboard_callbacks(message) -> bool:
    if message.text.lower() == 'clear chat history':
        db.clear_history(message.from_user.id)
        bot.send_message(message.chat.id, "Chat history cleared.")
        return True
    if message.text.lower() == 'i want to ask a question':
        bot.set_state(message.from_user.id, MyStates.answering_questions, message.chat.id)
        bot.send_message(message.chat.id, "Please ask a question.")
        return True
    if message.text.lower() == 'i want to add info':
        bot.set_state(message.from_user.id, MyStates.getting_info, message.chat.id)
        bot.send_message(message.chat.id, "Please send the text you want to add.")
        return True
    return False


def process_question(message):
    response = requests.post("http://ml:3000/question", json={"text": message.text}).json()['answer']
    db.save_message(message.from_user.id, message.text, response)
    bot.send_message(message.chat.id,
                     response,
                     reply_markup=gen_markup())


@bot.message_handler(state=MyStates.answering_questions, content_types=['text'])
def handle_text_question(message):
    logger.info(f"User {message.from_user.id} sent a text.")
    if handle_keyboard_callbacks(message):
        logger.info(f"User {message.from_user.id}. Process callback")
        return
    logger.info(f"User {message.from_user.id}. Sending question to ML service.")
    process_question(message)


@bot.message_handler(state=MyStates.getting_info, content_types=['text'])
def handle_text_info(message):
    logger.info(f"User {message.from_user.id}. Processing a text message.")
    if handle_keyboard_callbacks(message):
        logger.info(f"User {message.from_user.id}. Process callback")
        return

    logger.info(f"User {message.from_user.id}. Sending text to ML service.")
    response = requests.post("http://ml:3000/load_text", json={"text": message.text})
    if response.status_code == 200:
        bot.send_message(message.chat.id,
                         "Text received successfully.",
                         reply_markup=gen_markup())
    else:
        bot.send_message(message.chat.id,
                         "An error occurred while processing the text.",
                         reply_markup=gen_markup())


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        document = message.document
        if document.mime_type == 'application/pdf':
            file_info = bot.get_file(document.file_id)
            save_file(document, file_info)
            bot.send_message(message.chat.id, "PDF received and saved successfully.")
            if message.caption:
                process_question(message)
        else:
            bot.send_message(message.chat.id, "Please send a PDF file.")
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while processing the file.")
        print(f"Error: {e}")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logger.info(f"User {message.from_user.id}. Starting the bot.")
    bot.set_state(message.from_user.id, MyStates.getting_info, message.chat.id)
    bot.send_message(message.chat.id,
                     "Hi! Please send a query and I'll try to help you.",
                     reply_markup=gen_markup())


if __name__ == '__main__':
    db.init()
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling(skip_pending=True)
