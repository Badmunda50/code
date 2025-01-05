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

# Helper function to send a random word
async def send_random_word(chat_id):
    word = random.choice(WORDS)
    await app.send_message(chat_id, f"Type this word: **{word}**")
    return word

# Function to track who types the word first
async def track_word_typing(chat_id, word):
    def check(_, message: Message):
        return message.text and message.text.strip().lower() == word.lower() and message.chat.id == chat_id

    user_scored = False
    handler_added = False

    @app.on_message(filters.chat(chat_id) & filters.text)
    async def handler(_, message: Message):
        nonlocal user_scored
        if check(_, message) and not user_scored:
            user_id = message.from_user.id
            user_points[user_id] = user_points.get(user_id, 0) + 1
            await app.send_message(chat_id, f"🏆 {message.from_user.mention} typed the word first and earned 1 point!")
            user_scored = True

    try:
        app.add_handler(handler)
        handler_added = True
        await asyncio.sleep(60)  # Wait for 60 seconds for someone to type the word
        if not user_scored:
            await app.send_message(chat_id, "No one typed the word in time.")
    finally:
        if handler_added:
            app.remove_handler(handler)

# Function to start the word typing game
async def start_word_game(chat_id):
    while True:
        for minutes in SCHEDULE_TIMES:
            await asyncio.sleep(minutes * 60)
            word = await send_random_word(chat_id)
            await track_word_typing(chat_id, word)

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

# Command to start the game
@app.on_message(filters.command("start"))
async def start_game(_, message: Message):
    chat_id = message.chat.id
    await message.reply_text("The word typing game has started! Get ready!")
    # Send the first word and start the game loop
    word = await send_random_word(chat_id)
    await track_word_typing(chat_id, word)
    asyncio.create_task(start_word_game(chat_id))
