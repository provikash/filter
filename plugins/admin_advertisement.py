
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.config_db import mdb
from info import ADMINS
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("setads") & filters.user(ADMINS))
async def set_advertisement(client, message):
    """
    Set advertisement with impression count and optional expiry
    Usage: /setads <impression_count> <advertisement_text>
    """
    try:
        if len(message.command) < 3:
            await message.reply_text(
                "❌ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> <code>/setads [impression_count] [advertisement_text]</code>\n\n"
                "<b>Example 1:</b> <code>/setads 1000 🎉 Special Offer! Get 50% off on premium subscription! Use code: SAVE50</code>\n\n"
                "<b>Example 2 (with link):</b> <code>/setads 500 🚀 Join our <a href='https://t.me/your_channel'>Premium Channel</a> for exclusive content!</code>"
            )
            return
            
        impression_count = int(message.command[1])
        ad_text = " ".join(message.command[2:])
        
        if impression_count <= 0:
            await message.reply_text("❌ Impression count must be greater than 0!")
            return
          
