from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from Banall import app

@app.on_edited_message(filters.text)
async def delete_edited_message(client: Client, message: Message):
    """
    Automatically delete a user's text message 10 seconds after it is edited,
    but only if it has no reactions.
    """
    msg_id = message.id
    chat_id = message.chat.id

    # Wait for 10 seconds
    await asyncio.sleep(10)

    try:
        # Fetch the latest version of the message
        updated_message = await client.get_messages(chat_id, msg_id)

        # Check if the message has reactions
        if updated_message.reactions:
            print(f"Message {msg_id} in chat {chat_id} has reactions, not deleting.")
            return

        # If no reactions, delete the message
        await client.delete_messages(chat_id, msg_id)
        print(f"Deleted message {msg_id} in chat {chat_id}")
    except Exception as e:
        print(f"Error handling message {msg_id}: {e}")

