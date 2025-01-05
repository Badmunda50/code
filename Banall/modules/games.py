import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from Banall import app

# Define a list of random words
WORDS = ["cat", "dog", "blue", "green", "apple", "banana", "tiger", "lion", "red", "yellow"]

# Schedule times (in minutes) for sending words
SCHEDULE_TIMES = [1, 18, 25, 35, 46, 60]

# Dictionary to track user points
user_points = {}

# Track the current word for each chat
current_word = {}

# Helper function to send a random word
async def send_random_word(chat_id):
    word = random.choice(WORDS)
    current_word[chat_id] = word  # Store the word for the chat
    await app.send_message(chat_id, f"Type this word: **{word}**")
    return word

# Function to track who types the word first
@app.on_message(filters.text)
async def track_word_typing(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    # Check if the chat has an active word
    if chat_id in current_word and text == current_word[chat_id].lower():
        # Award points and notify the user
        user_points[user_id] = user_points.get(user_id, 0) + 1
        await app.send_message(chat_id, f"🏆 {message.from_user.mention} typed the word first and earned 1 point!")
        # Remove the word to prevent duplicate points
        del current_word[chat_id]

# Function to start the word typing game
async def start_word_game(chat_id):
    while True:
        for minutes in SCHEDULE_TIMES:
            await asyncio.sleep(minutes * 60)
            await send_random_word(chat_id)

# Command to display the top 10 users based on points
@app.on_message(filters.command("top_points"))
async def top_points(_, message: Message):
    if not user_points:
        await message.reply_text("No points have been awarded yet.")
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    leaderboard = "\n".join(
        [
            f"{i+1}. {await app.get_users(user_id).first_name}: {points} points"
            for i, (user_id, points) in enumerate(sorted_users)
        ]
    )
    await message.reply_text(f"**🏆 TOP 10 USERS BY POINTS 🏆**\n\n{leaderboard}")

# Start the word game automatically when the bot starts
@app.on_message(filters.command("start"))
async def start_game(_, message: Message):
    chat_id = message.chat.id
    await message.reply_text("The word typing game has started!")
    # Send a random word immediately
    await send_random_word(chat_id)
    asyncio.create_task(start_word_game(chat_id))
