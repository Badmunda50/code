from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from Banall import app


# Track edited messages
edited_messages = {}

@app.on_message(filters.text)
async def track_messages(client: Client, message: Message):
    """
    Track new messages sent by users.
    """
    # Log the original message to track edits later
    if message.text:
        edited_messages[message.id] = {"message": message, "edited": False}

@app.on_edited_message(filters.text)
async def delete_edited_message(client: Client, message: Message):
    """
    Automatically delete a user's text message 10 seconds after it is edited.
    """
    msg_id = message.id

    # Check if the message exists in the tracked messages and mark as edited
    if msg_id in edited_messages:
        edited_messages[msg_id]["edited"] = True

        # Wait for 10 seconds
        await asyncio.sleep(10)

        # Check again if the message still exists and has no reactions
        chat_id = message.chat.id
        try:
            updated_message = await client.get_messages(chat_id, msg_id)

            # If the message has no reactions, delete it
            if not updated_message.reactions:
                await client.delete_messages(chat_id, msg_id)
                edited_messages.pop(msg_id, None)  # Clean up the tracking
            else:
                # If the message has reactions, do nothing
                edited_messages.pop(msg_id, None)
        except Exception as e:
            print(f"Error handling message {msg_id}: {e}")
            edited_messages.pop(msg_id, None)

