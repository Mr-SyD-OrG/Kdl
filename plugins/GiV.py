from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message 
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert, download_image
from helper.database import db
from config import Config
from .syd_rename import autosydd
import os
import time, asyncio
import logging
import re
#import shutil

@Client.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome to the Giveaway Bot!")

@Client.on_message(filters.command("giveaway"))
async def giveaway(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Giveaway", callback_data="join_giveaway")]
    ])
    await client.send_message(
        chat_id=CHANNEL_ID,
        text=f"Click to join the giveaway!\n\nJoin @{GIVEAWAY_CHANNEL_USERNAME}\nJoin @{REQUIRED_CHANNEL_USERNAME}",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("join_giveaway"))
async def join_giveaway_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_in_both_channels = await is_user_in_channels(client, user_id)

    if not is_in_both_channels:
        await callback_query.answer(
            text=f"Please join both channels to participate ☺️",
            show_alert=True
        )
    else:
        added = await add_user(user_id)
        if not added:
            await callback_query.answer("You already joined!", show_alert=True)
        else:
            await callback_query.answer("You're in the giveaway!", show_alert=True)

@Client.on_message(filters.command("end"))
async def end_giveaway(client, message):
    try:
        number_to_pick = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply_text("Usage: /end <number>. Example: /end 5")
        return

    users = participants.find()
    participant_ids = [str(user['_id']) for user in users]
    total_users = len(participant_ids)

    valid_ids = []
    for user_id in participant_ids:
        try:
            in_giveaway = await is_user_in_channels(client, int(user_id), GIVEAWAY_CHANNEL_ID, GIVEAWAY_CHANNEL_USERNAME)
           # in_required = await is_user_in_channels(client, int(user_id), REQUIRED_CHANNEL_ID, REQUIRED_CHANNEL_USERNAME)

            if in_giveaway: #and in_required:
                valid_ids.append(user_id)
            else:
                await delete_user(int(user_id))  # Remove from DB
        except Exception as e:
            print(f"Error checking user {user_id}: {e}")
            continue

    valid_count = len(valid_ids)

    if number_to_pick > valid_count:
        await message.reply_text(f"Not enough valid participants (have: {valid_count}).")
        return

    random.shuffle(valid_ids)
    selected_ids = random.sample(valid_ids, number_to_pick)

    winner_text = []
    for user_id in selected_ids:
        try:
            user = await client.get_users(int(user_id))
            username = f"@{user.username}" if user.username else "No Username"
            winner_text.append(f"User ID: {user_id}, Username: {username}")
        except Exception:
            winner_text.append(f"User ID: {user_id}, Username: Unknown")

    await client.send_message(
        CHANNEL_ID,
        f"Total Participants: {total_users}\n"
        f"Valid Participants: {valid_count}\n\n"
        f"Selected Winners:\n" + "\n".join(winner_text)
    )
    await db.delete_user_data()                       
        
