import logging
import os
import platform
import psutil
import time
from Banall import app
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

# Define the maximum allowed length for a message
MAX_MESSAGE_LENGTH = 25

async def delete_long_edited_messages(client: Client, edited_message: Message):
    if edited_message.text:
        # Check if the edited message exceeds the word limit
        if len(edited_message.text.split()) > MAX_MESSAGE_LENGTH:
            await edited_message.delete()

@app.on_edited_message(filters.group & ~filters.me)
async def handle_edited_messages(client: Client, edited_message: Message):
    await delete_long_edited_messages(client, edited_message)

async def delete_long_messages(client: Client, message: Message):
    if message.text:
        # Check if the message exceeds the word limit
        if len(message.text.split()) > MAX_MESSAGE_LENGTH:
            await message.delete()

@app.on_message(filters.group & ~filters.me)
async def handle_messages(client: Client, message: Message):
    await delete_long_messages(client, message)
