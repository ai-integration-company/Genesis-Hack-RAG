import os
import asyncio
from telebot.async_telebot import AsyncTeleBot

from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.environ.get("API_TOKEN")

bot = AsyncTeleBot(API_TOKEN)

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


async def save_file(document, file_info):
    downloaded_file = await bot.download_file(file_info.file_path)
    file_path = os.path.join(DOWNLOAD_DIR, document.file_name)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)


async def infer(prompt):
    return f"Text: {prompt}"


@bot.message_handler(content_types=['text'])
async def handle_text(message):
    await bot.send_message(message.chat.id, await infer(message.text))


@bot.message_handler(content_types=['document'])
async def handle_docs(message):
    try:
        document = message.document
        if document.mime_type == 'application/pdf':
            file_info = await bot.get_file(document.file_id)
            await save_file(document, file_info)
            await bot.send_message(message.chat.id, "PDF received and saved successfully.")

            if message.caption:
                await bot.send_message(message.chat.id, await infer(message.caption))
        else:
            await bot.send_message(message.chat.id, "Please send a PDF file.")
    except Exception as e:
        await bot.send_message(message.chat.id, "An error occurred while processing the file.")
        print(f"Error: {e}")


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, "Hi! Send me a PDF file and I will save it.")


asyncio.run(bot.polling())
