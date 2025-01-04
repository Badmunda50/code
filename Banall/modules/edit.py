from Banall import app as shizuchat
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio


@shizuchat.on_edited_message(filters.group & ~filters.me)
async def delete_edited_message(client, message: Message):
    # Ensure the message edit is a text edit (not a reaction, media, or similar)
    if not message.text:
        return

    # Check if the same user who sent the message edited it
    if message.from_user and message.from_user.id == message.edit_date:
        try:
            # Wait for a specified time (e.g., 2 seconds)
            await asyncio.sleep(2)

            # Delete the edited message
            await message.delete()

            # Send a reply mentioning the user
            await message.reply(
                f"ʜᴇʏ, {message.from_user.mention}\nʏᴏᴜʀ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ."
            )
        except Exception as e:
            LOGGER.error(f"Error deleting edited message: {e}")
