import random
import asyncio
from Banall import app
from pyrogram import Client, filters
from pyrogram.types import Message

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

# Function to start the word typing game
async def start_word_game():
    while True:
        for minutes in SCHEDULE_TIMES:
            await asyncio.sleep(minutes * 60)
            chat_id = "your_chat_id"  # Replace with your chat ID
            word = await send_random_word(chat_id)
            await track_word_typing(chat_id, word)

# Function to track who types the word first
async def track_word_typing(chat_id, word):
    def check(msg):
        return msg.text.lower() == word.lower() and msg.chat.id == chat_id

    try:
        msg = await app.listen(chat_id, filters=filters.text, check=check, timeout=60)
        user_id = msg.from_user.id
        user_points[user_id] = user_points.get(user_id, {"points": 0})
        user_points[user_id]["points"] += 1
        await app.send_message(chat_id, f"🏆 {msg.from_user.mention} typed the word first and earned 1 point!")
    except asyncio.TimeoutError:
        await app.send_message(chat_id, "No one typed the word in time.")

# Command to display the top 10 users based on points
@app.on_message(filters.command("top_points"))
async def top_points(_, message):
    if not user_points:
        await message.reply_text("No points have been awarded yet.")
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1]["points"], reverse=True)[:10]
    leaderboard = "\n".join([f"{i+1}. {await app.get_users(user_id).first_name}: {data['points']} points" for i, (user_id, data) in enumerate(sorted_users)])
    await message.reply_text(f"**🏆 TOP 10 USERS BY POINTS 🏆**\n\n{leaderboard}")

# Start the word game automatically when the bot starts
app.add_task(start_word_game())
