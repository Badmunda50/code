from Banall import app as shizuchat
from pyrogram import filters
from pyrogram.types import Message
import asyncio

@shizuchat.on_edited_message(filters.group & ~filters.me)
async def delete_edited_message(client, message: Message):
    """
    Deletes a message in a group if the user edits the text.
    Ignores edits like reactions, media changes, etc.
    """
    # Check if the edit is a text edit
    if not message.text or (message.media and not message.text):
        return

    try:
        # Wait for a short duration (e.g., 2 seconds)
        await asyncio.sleep(2)

        # Delete the edited message
        await message.delete()

        # Inform the user in the chat (not as a reply to the deleted message)
        await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"ʜᴇʏ, {message.from_user.mention}\n"
                f"ʏᴏᴜʀ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ."
            ),
        )
    except Exception as e:
        print(f"Error deleting edited message: {e}")
