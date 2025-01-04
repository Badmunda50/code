from Banall import app
from pyrogram import filters
from pyrogram.types import Message
import asyncio

@app.on_edited_message(filters.group & ~filters.me)
async def delete_edited_message(client, message: Message):
    """
    Deletes text-edited messages in a group, excluding reactions and bot edits.
    """
    # Ensure the edit is a text edit (not a reaction, media, or other)
    if not message.text:
        return

    try:
        # Wait for a specified time (e.g., 2 seconds) to ensure proper handling
        await asyncio.sleep(2)

        # Delete the edited message
        await message.delete()

        # Inform the user in the same chat (not as a reply)
        await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"ʜᴇʏ, {message.from_user.mention}\n"
                f"ʏᴏᴜʀ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ."
            ),
        )
    except Exception as e:
        print(f"Error deleting edited message: {e}")
