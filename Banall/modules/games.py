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

import time

# Helper function to send a random word
async def send_random_word(chat_id):
    retries = 5
    for attempt in range(retries):
        try:
            word = random.choice(WORDS)
            await app.send_message(chat_id, f"Type this word: **{word}**")
            return word
        except pyrogram.errors.exceptions.bad_request_400.UsernameNotOccupied:
            print(f"Invalid chat_id: {chat_id}")
            break
        except pyrogram.errors.RPCError as e:
            print(f"Error: {e}. Retrying in 10 seconds...")
            time.sleep(10)
    else:
        print("Max retries reached, could not send message.")

# Function to start the word typing game
async def start_word_game(chat_id):
    while True:
        for minutes in SCHEDULE_TIMES:
            await asyncio.sleep(minutes * 60)
            word = await send_random_word(chat_id)
            await track_word_typing(chat_id, word)

# Function to track who types the word first
async def track_word_typing(chat_id, word):
    def check(msg: Message):
        return msg.text and msg.text.lower() == word.lower() and msg.chat.id == chat_id

    @app.on_message(filters.chat(chat_id) & filters.text)
    async def handler(client, message):
        if check(message):
            user_id = message.from_user.id
            user_points[user_id] = user_points.get(user_id, {"points": 0})
            user_points[user_id]["points"] += 1
            await app.send_message(chat_id, f"🏆 {message.from_user.mention} typed the word first and earned 1 point!")
            app.remove_handler(handler)

    try:
        await asyncio.sleep(60)  # Wait for 60 seconds to see if anyone types the word
    except asyncio.TimeoutError:
        pass
    finally:
        await app.send_message(chat_id, "No one typed the word in time.")
        app.remove_handler(handler)

# Command to display the top 10 users based on points
@app.on_message(filters.command("top_points"))
async def top_points(_, message: Message):
    if not user_points:
        await message.reply_text("No points have been awarded yet.")
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1]["points"], reverse=True)[:10]
    leaderboard = "\n.join(
        [
            f"{i+1}. {await app.get_users(user_id).first_name}: {data['points']} points"
            for i, (user_id, data) in enumerate(sorted_users)
        ]
    )
    await message.reply_text(f"**🏆 TOP 10 USERS BY POINTS 🏆**\n\n{leaderboard}")

# Start the word game automatically when the bot starts
@app.on_message(filters.command("start"))
async def start_game(_, message: Message):
    chat_id = message.chat.id
    await message.reply_text("The word typing game has started!")
    # Send a random word immediately
    word = await send_random_word(chat_id)
    await track_word_typing(chat_id, word)
    asyncio.create_task(start_word_game(chat_id))
