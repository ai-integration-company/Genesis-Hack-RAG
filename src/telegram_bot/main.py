import os
import asyncio

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

import db

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

bot = AsyncTeleBot(API_TOKEN)


async def save_file(document, file_info):
    downloaded_file = await bot.download_file(file_info.file_path)
    file_path = os.path.join(DOWNLOAD_DIR, document.file_name)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)


def gen_markup():
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(KeyboardButton("Clear Chat History"))
    return markup


async def infer(prompt):
    response = f"Text: {prompt}"
    return response


async def process_text(message):
    if message.text.lower() == 'clear chat history':
        db.clear_history(message.from_user.id)
        await bot.send_message(message.chat.id, "Chat history cleared.")
        return
    else:
        response = await infer(message.text)
        db.save_message(message.from_user.id, message.text, response)
        await bot.send_message(message.chat.id,
                               response,
                               reply_markup=gen_markup())


@bot.message_handler(content_types=['text'])
async def handle_text(message):
    await process_text(message)


@bot.message_handler(content_types=['document'])
async def handle_docs(message):
    try:
        document = message.document
        if document.mime_type == 'application/pdf':
            file_info = await bot.get_file(document.file_id)
            await save_file(document, file_info)
            await bot.send_message(message.chat.id, "PDF received and saved successfully.")
            if message.caption:
                await process_text(message)
        else:
            await bot.send_message(message.chat.id, "Please send a PDF file.")
    except Exception as e:
        await bot.send_message(message.chat.id, "An error occurred while processing the file.")
        print(f"Error: {e}")


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, "Hi! Please send a query and I'll try to help you.")


if __name__ == '__main__':
    db.init()
    asyncio.run(bot.polling())
