from pyrogram import filters
from pymongo import MongoClient
from Banall import app
from pyrogram.types import *
import datetime
import matplotlib.pyplot as plt
from pyrogram import enums
import io
import logging
import time

# Set up logging for error tracking
logging.basicConfig(level=logging.INFO)

# MongoDB setup
MONGO_URI = "mongodb+srv://BADMUNDA:BADMYDAD@badhacker.i5nw9na.mongodb.net/"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["rankings_database"]
overall_collection = db["overall_ranking"]
today_collection = db["today_ranking"]
weekly_collection = db["weekly_ranking"]
group_collection = db["group_ranking"]


# Helper Functions
def get_current_week():
    """Returns the current week number."""
    return datetime.date.today().isocalendar()[1]

def update_group_total(chat_id):
    """Updates the total message count for a group in the group collection."""
    group_data = group_collection.find_one({"chat_id": chat_id}) or {"chat_id": chat_id, "total_messages": 0}
    group_data["total_messages"] += 1
    group_collection.update_one({"chat_id": chat_id}, {"$set": group_data}, upsert=True)


def generate_graph(data, title):
    """Generates a graph based on the given data."""
    usernames = [d[0] for d in data]
    messages = [d[2] for d in data]
    plt.figure(figsize=(10, 6))
    plt.barh(usernames, messages, color="#FF1493")
    plt.xlabel("Messages", color="white")
    plt.ylabel("Users", color="white")
    plt.title(title, color="white")
    plt.gca().invert_yaxis()
    plt.gca().set_facecolor("black")
    plt.gcf().set_facecolor("black")
    plt.xticks(color="white")
    plt.yticks(color="white")
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()
    return buffer

async def fetch_usernames(app, users_data):
    result = []
    for user_id, count in users_data:
        try:
            user = await app.get_users(int(user_id))
            user_name = user.username if user.username else "Unknown"
            first_name = user.first_name if user.first_name else "Unknown"
            result.append((user_name, first_name, count, user_id))
        except Exception as e:
            logging.error(f"Error fetching username for {user_id}: {e}")
            result.append(("Unknown", "Unknown", count, user_id))
    return result
    
# ------------------- Watcher -----------------------
user_message_counts = {}
user_block_times = {}

@app.on_message(filters.group & ~filters.bot, group=6)
async def group_watcher(_, message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    current_time = time.time()

    # Initialize message count and block time for the user
    if user_id not in user_message_counts:
        user_message_counts[user_id] = []
    if user_id not in user_block_times:
        user_block_times[user_id] = 0

    # Remove messages older than 3 seconds
    user_message_counts[user_id] = [t for t in user_message_counts[user_id] if current_time - t <= 3]

    # Check if user is blocked
    if current_time < user_block_times[user_id]:
        return

    # Update message count
    user_message_counts[user_id].append(current_time)

    # Block user if they sent more than 8 messages in 3 seconds
    if len(user_message_counts[user_id]) > 8:
        await message.reply_text(f"⛔️ {message.from_user.mention}ɪꜱ ꜰʟᴏᴏᴅɪɴɢ: ʙʟᴏᴄᴋᴇᴅ ꜰᴏʀ 20 ᴍɪɴᴜᴛᴇꜱ ꜰᴏʀ ᴜꜱɪɴɢ ᴛʜᴇ ʙᴏᴛ.")
        user_block_times[user_id] = current_time + 20 * 60  # Block for 20 minutes
        return

    # Block user if they sent more than 3 messages in 8 seconds
    if len([t for t in user_message_counts[user_id] if current_time - t <= 8]) > 3:
        await message.reply_text(f"⛔️ {message.from_user.mention}ɪꜱ ꜰʟᴏᴏᴅɪɴɢ: ʙʟᴏᴄᴋᴇᴅ ꜰᴏʀ 20 ᴍɪɴᴜᴛᴇꜱ ꜰᴏʀ ᴜꜱɪɴɢ ᴛʜᴇ ʙᴏᴛ.")
        user_block_times[user_id] = current_time + 20 * 60  # Block for 20 minutes
        return

    # Update today's data
    today_data = today_collection.find_one({"chat_id": chat_id}) or {"chat_id": chat_id, "users": {}}
    today_users = today_data["users"]
    today_users[user_id] = today_users.get(user_id, {"total_messages": 0})
    today_users[user_id]["total_messages"] += 1
    today_collection.update_one({"chat_id": chat_id}, {"$set": {"users": today_users}}, upsert=True)

    # Update weekly data
    current_week = get_current_week()
    weekly_data = weekly_collection.find_one({"chat_id": chat_id, "week": current_week}) or {"chat_id": chat_id, "week": current_week, "users": {}}
    weekly_users = weekly_data["users"]
    weekly_users[user_id] = weekly_users.get(user_id, {"total_messages": 0})
    weekly_users[user_id]["total_messages"] += 1
    weekly_collection.update_one({"chat_id": chat_id, "week": current_week}, {"$set": {"users": weekly_users}}, upsert=True)

    # Update overall user data
    overall_data = overall_collection.find_one({"chat_id": chat_id}) or {"chat_id": chat_id, "users": {}}
    overall_users = overall_data["users"]
    overall_users[user_id] = overall_users.get(user_id, {"total_messages": 0})
    overall_users[user_id]["total_messages"] += 1
    overall_collection.update_one({"chat_id": chat_id}, {"$set": {"users": overall_users}}, upsert=True)

    # Update group total
    update_group_total(chat_id)

# ------------------- Rankings ----------------------

@app.on_message(
    filters.command(["rankings", "today"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"])
)
async def today_rankings(_, message):
    chat_id = str(message.chat.id)
    today_data = today_collection.find_one({"chat_id": chat_id})

    if today_data and "users" in today_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in today_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph(usernames_data, "📊 Today's Leaderboard")
            text_leaderboard = "\n".join(
                [f"[{first_name}](tg://user?id={user_id}): {count}" for username, first_name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
            )
            await message.reply_photo(
                photo=graph_buffer, 
                caption=f"**📈 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴛᴏᴅᴀʏ**\n\n{text_leaderboard}",
                reply_markup=buttons
            )
        else:
            await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛᴏᴅᴀʏ.")
    else:
        await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛᴏᴅᴀʏ.")

    # Delete the command message
    await message.delete()

@app.on_callback_query(filters.regex(r"^today$"))
async def on_today_callback(_, callback_query):
    chat_id = str(callback_query.message.chat.id)
    today_data = today_collection.find_one({"chat_id": chat_id})

    if today_data and "users" in today_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in today_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph([(u[0], u[1]) for u in usernames_data], "📊 Today's Leaderboard")
            text_leaderboard = "\n".join(
                [f"[{name}](tg://user?id={user_id}): {count}" for name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
            )
        await callback_query.message.edit_media(
            media=InputMediaPhoto(media=graph_buffer, caption=f"**📈 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴛᴏᴅᴀʏ**\n\n{text_leaderboard}"),
            reply_markup=buttons
        )
    else:
        await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴀʟʟ ɢʀᴏᴜᴘꜱ.")
           
           
@app.on_callback_query(filters.regex(r"^weekly$"))
async def on_weekly_callback(_, callback_query):
    chat_id = str(callback_query.message.chat.id)
    current_week = get_current_week()
    weekly_data = weekly_collection.find_one({"chat_id": chat_id, "week": current_week})

    if weekly_data and "users" in weekly_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in weekly_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph([(u[0], u[1]) for u in usernames_data], "📊 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
            text_leaderboard = "\n".join(
                [f"[{name}](tg://user?id={user_id}): {count}" for name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
            )
            await callback_query.message.edit_media(
                media=InputMediaPhoto(graph_buffer, caption=f"**📈 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ**\n\n{text_leaderboard}"),
                reply_markup=buttons
            )
        else:
            await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ᴡᴇᴇᴋ.")
    else:
        await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ᴡᴇᴇᴋ.")
        
@app.on_callback_query(filters.regex(r"^overall$"))
async def on_overall_callback(_, callback_query):
    chat_id = str(callback_query.message.chat.id)
    overall_data = overall_collection.find_one({"chat_id": chat_id})

    if overall_data and "users" in overall_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in overall_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph([(u[0], u[1]) for u in usernames_data], "📊 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
            text_leaderboard = "\n".join(
                [f"[{name}](tg://user?id={user_id}): {count}" for name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
        )
        await callback_query.message.edit_media(
            media=InputMediaPhoto(media=graph_buffer, caption=f"**📈 ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ᴏᴠᴇʀᴀʟʟ**\n\n{text_leaderboard}"),
            reply_markup=buttons
        )
    else:
        await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴀʟʟ ɢʀᴏᴜᴘꜱ.")
        
@app.on_callback_query(filters.regex(r"^group_overall$"))
async def on_group_overall_callback(_, callback_query):
    groups_data = group_collection.find().sort("total_messages", -1).limit(5)
    sorted_groups = []

    for group in groups_data:
        try:
            group_chat = await app.get_chat(group["chat_id"])
            group_name = group_chat.title if group_chat else f"Group {group['chat_id']}"
        except Exception as e:
            logging.error(f"Error fetching group name for {group['chat_id']}: {e}")
            group_name = f"Group {group['chat_id']}"

        sorted_groups.append((group_name, group["total_messages"]))

    if sorted_groups:
        graph_buffer = generate_graph(sorted_groups, "📊 ᴀʟʟ ɢʀᴏᴜᴘꜱ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
        text_leaderboard = "\n".join(
            [f"{group}: {count}" for group, count in sorted_groups]
        )
        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
            ],
            [
                InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
            ],
            [
                InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
            ]]
        )
        await callback_query.message.edit_media(
            media=InputMediaPhoto(media=graph_buffer, caption=f"**📈 ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ᴏᴠᴇʀᴀʟʟ**\n\n{text_leaderboard}"),
            reply_markup=buttons
        )
    else:
        await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴀʟʟ ɢʀᴏᴜᴘꜱ.")

@app.on_callback_query(filters.regex(r"^back$"))
async def on_back_callback(_, callback_query):
    await callback_query.answer()
    await today_rankings(callback_query.message)

async def weekly_rankings(message):
    chat_id = str(message.chat.id)
    current_week = get_current_week()
    weekly_data = weekly_collection.find_one({"chat_id": chat_id, "week": current_week})

    if weekly_data and "users" in weekly_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in weekly_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph([(u[0], u[1]) for u in usernames_data], "📊 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
            text_leaderboard = "\n".join(
                [f"[{name}](tg://user?id={user_id}): {count}" for name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
            )
            await message.reply_photo(
                photo=graph_buffer, 
                caption=f"**📈 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ**\n\n{text_leaderboard}",
                reply_markup=buttons
            )
        else:
            await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ᴡᴇᴇᴋ.")
    else:
        await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ᴡᴇᴇᴋ.")

async def overall_rankings(message):
    chat_id = str(message.chat.id)
    overall_data = overall_collection.find_one({"chat_id": chat_id})

    if overall_data and "users" in overall_data:
        users_data = [(user_id, data["total_messages"]) for user_id, data in overall_data["users"].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            usernames_data = await fetch_usernames(app, sorted_users_data)
            graph_buffer = generate_graph([(u[0], u[1]) for u in usernames_data], "📊 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
            text_leaderboard = "\n".join(
                [f"[{name}](tg://user?id={user_id}): {count}" for name, count, user_id in usernames_data]
            )
            buttons = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ],
                [
                    InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                ],
                [
                    InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
                ]]
            )
            await message.reply_photo(
                photo=graph_buffer, 
                caption=f"**📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ**\n\n{text_leaderboard}",
                reply_markup=buttons
            )
        else:
            await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ.")
    else:
        await message.reply_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ.")

async def all_groups_rankings(message):
    groups_data = group_collection.find().sort("total_messages", -1).limit(5)
    sorted_groups = []

    for group in groups_data:
        try:
            group_chat = await app.get_chat(group["chat_id"])
            group_name = group_chat.title if group_chat else f"Group {group['chat_id']}"
        except Exception as e:
            logging.error(f"Error fetching group name for {group['chat_id']}: {e}")
            group_name = f"Group {group['chat_id']}"

        sorted_groups.append((group_name, group["total_messages"]))

    if sorted_groups:
        graph_buffer = generate_graph(sorted_groups, "📊 ᴀʟʟ ɢʀᴏᴜᴘꜱ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
        text_leaderboard = "\n".join(
            [f"{group}: {count}" for group, count in sorted_groups]
        )
        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
            ],
            [
                InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
            ],
            [
                InlineKeyboardButton("ɢʀᴏᴜᴘ ᴏᴠᴇʀᴀʟʟ", callback_data="group_overall")
            ]]
        )
        await message.reply_photo(
            photo=graph_buffer, 
            caption=f"**📈 ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ᴏᴠᴇʀᴀʟʟ**\n\n{text_leaderboard}"
        )
    else:
        await callback_query.message.edit_text("ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ꜰᴏʀ ᴀʟʟ ɢʀᴏᴜᴘꜱ.")
