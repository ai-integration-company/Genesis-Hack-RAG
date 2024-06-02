import asyncio
import os
import logging

import requests
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

import db

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

bot = AsyncTeleBot(API_TOKEN)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(levelname)s:     [%(asctime)s] %(message)s')


async def save_file(document, file_info):
    downloaded_file = await bot.download_file(file_info.file_path)
    files = {'file': (document.file_name, downloaded_file, 'application/pdf')}
    response = requests.post("http://ml:3000/load_pdf", files=files)
    return response.status_code == 200


def gen_markup():
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(KeyboardButton("Очистить историю чата"))
    return markup


async def handle_keyboard_callbacks(message) -> bool:
    if message.text.lower() == 'очистить историю чата':
        logger.info(f"User {message.from_user.id}. Clearing chat history.")
        db.clear_history(message.from_user.id)
        await bot.send_message(message.chat.id, "История чата очищена.")
        requests.get("http://ml:3000/clear_history")
        return True
    return False


async def process_question(message):
    response = requests.post("http://ml:3000/question", json={"text": message.text})

    if response.status_code != 200:
        await bot.send_message(message.chat.id, "Произошла ошибка при обработке вопроса.")
        db.save_message(message.from_user.id, message.text, "ERR")
        return

    response = response.json()['answer']
    db.save_message(message.from_user.id, message.text, response)
    await bot.send_message(message.chat.id,
                           response,
                           reply_markup=gen_markup())


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    logger.info(f"User {message.from_user.id}. Starting the bot.")
    await bot.send_message(message.chat.id,
                           "Здравствуйте! Задайте вопрос или пришлите PDF файл, который нужно обработать."
                           "Для очистки истории чата нажмите кнопку в меню бота.",
                           reply_markup=gen_markup())


@bot.message_handler(content_types=['text'])
async def handle_text_question(message):
    logger.info(f"User {message.from_user.id} sent a text.")
    if await handle_keyboard_callbacks(message):
        logger.info(f"User {message.from_user.id}. Process callback")
        return
    logger.info(f"User {message.from_user.id}. Sending question to ML service.")
    await process_question(message)


@bot.message_handler(content_types=['document'])
async def handle_docs(message):
    try:
        document = message.document
        if document.mime_type == 'application/pdf':

            file_info = await bot.get_file(document.file_id)
            if await save_file(document, file_info):
                logger.info(f"User {message.from_user.id}. PDF file saved.")
                await bot.send_message(message.chat.id, "PDF файл сохранен.")
            else:
                logger.error(f"User {message.from_user.id}. Error while saving the file.")
                await bot.send_message(message.chat.id, "Произошла ошибка при обработке файла.")
            if message.caption:
                await process_question(message)
        else:
            logger.info(f"User {message.from_user.id}. Invalid file format.")
            await bot.send_message(message.chat.id, "Пожалуйста, пришлите PDF файл.")
    except Exception as e:
        logger.error(f"User {message.from_user.id}. Error while saving the file.")
        await bot.send_message(message.chat.id, "Произошла ошибка при обработке файла.")
        print(f"Error: {e}")


if __name__ == '__main__':
    db.init()
    asyncio.run(bot.polling())
