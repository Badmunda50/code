import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from Banall import app

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://BADMUNDA:BADMYDAD@badhacker.i5nw9na.mongodb.net/")
db = mongo_client["word_game"]
user_points_collection = db["user_points"]

# Define a list of random words
WORDS = ["cat", "dog", "blue", "green", "apple", "banana", "tiger", "lion", "red", "yellow"]

# Schedule times (in minutes) for sending words
SCHEDULE_TIMES = [1, 18, 25, 35, 46, 60]

# Dictionary to track active words for chats
active_words = {}

# Helper function to get user points from MongoDB
def get_user_points(user_id):
    user = user_points_collection.find_one({"user_id": user_id})
    return user["points"] if user else 0

# Helper function to update user points in MongoDB
def update_user_points(user_id, points):
    user_points_collection.update_one(
        {"user_id": user_id}, {"$set": {"points": points}}, upsert=True
    )

# Helper function to send a random word
async def send_random_word(chat_id):
    word = random.choice(WORDS)
    active_words[chat_id] = word
    await app.send_message(chat_id, f"Type this word: **{word}**")

# Function to start the word typing game
async def start_word_game(chat_id):
    while True:
        for minutes in SCHEDULE_TIMES:
            await asyncio.sleep(minutes * 60)
            await send_random_word(chat_id)

# Command to display the top 10 users based on points
@app.on_message(filters.command("top"))
async def top_points(_, message: Message):
    leaderboard_data = list(user_points_collection.find().sort("points", -1).limit(10))
    if not leaderboard_data:
        await message.reply_text("No points have been awarded yet.")
        return

    leaderboard = "\n".join(
        [
            f"{i+1}. [{user['name']}](tg://user?id={user['user_id']}): {user['points']} points"
            for i, user in enumerate(leaderboard_data)
        ]
    )
    await message.reply_text(f"**🏆 TOP 10 USERS BY POINTS 🏆**\n\n{leaderboard}", disable_web_page_preview=True)

# Start the game automatically when the bot is added as an admin
@app.on_chat_member_updated()
async def on_chat_member_updated(_, event):
    if event.new_chat_member.is_admin and not event.old_chat_member.is_admin:
        chat_id = event.chat.id
        if chat_id in active_words:
            return
        asyncio.create_task(start_word_game(chat_id))
        await app.send_message(chat_id, "I'm now an admin! The word typing game has started!")

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def check_word(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    word = active_words.get(chat_id)

    if word and message.text.strip().lower() == word.lower():
        active_words.pop(chat_id, None)  # Remove the active word
        user_points = get_user_points(user_id) + 1
        update_user_points(user_id, user_points)

        await app.send_message(
            chat_id,
            f"🏆 [{message.from_user.first_name}](tg://user?id={user_id}) typed the word first and earned 1 point!",
            disable_web_page_preview=True,
        )
