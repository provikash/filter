
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
            
        if len(ad_text) > 500:
            await message.reply_text("❌ Advertisement text is too long! Maximum 500 characters allowed.")
            return
            
        # Set advertisement with 7 days expiry by default
        expiry_date = datetime.now() + timedelta(days=7)
        
        await mdb.update_advirtisment(
            ads_string=ad_text,
            ads_name="Admin Advertisement",
            expiry=expiry_date,
            impression=impression_count
        )
        
        await message.reply_text(
            f"✅ <b>Advertisement Set Successfully!</b>\n\n"
            f"📝 <b>Text:</b> {ad_text}\n"
            f"👁️ <b>Impressions:</b> {impression_count}\n"
            f"⏰ <b>Expires:</b> {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📢 The advertisement will now appear above search results!"
        )
        
    except ValueError:
        await message.reply_text("❌ Invalid impression count! Please enter a valid number.")
    except Exception as e:
        logger.error(f"Set advertisement error: {e}")
        await message.reply_text("❌ An error occurred while setting the advertisement!")

@Client.on_message(filters.command("viewads") & filters.user(ADMINS))
async def view_advertisement(client, message):
    """View current advertisement status"""
    try:
        ads_string, ads_name, impression_count = await mdb.get_advirtisment()
        
        if ads_string and ads_name:
            status = f"✅ <b>Active Advertisement</b>\n\n"
            status += f"📝 <b>Text:</b> {ads_string}\n"
            status += f"👁️ <b>Remaining Impressions:</b> {impression_count if impression_count else 0}\n"
            status += f"📊 <b>Status:</b> {'Active' if impression_count and impression_count > 0 else 'Expired'}"
        else:
            status = "❌ <b>No Active Advertisement</b>\n\nUse /setads to create a new advertisement."
            
        buttons = [
            [InlineKeyboardButton("🗑️ Remove Ads", callback_data="remove_ads")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ads")]
        ]
        
        await message.reply_text(status, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logger.error(f"View advertisement error: {e}")
        await message.reply_text("❌ An error occurred while fetching advertisement data!")

@Client.on_message(filters.command("removeads") & filters.user(ADMINS))
async def remove_advertisement(client, message):
    """Remove current advertisement"""
    try:
        await mdb.update_advirtisment(
            ads_string=None,
            ads_name=None,
            expiry=None,
            impression=0
        )
        
        await message.reply_text("✅ <b>Advertisement Removed Successfully!</b>")
        
    except Exception as e:
        logger.error(f"Remove advertisement error: {e}")
        await message.reply_text("❌ An error occurred while removing the advertisement!")

@Client.on_callback_query(filters.regex("^remove_ads$"))
async def remove_ads_callback(client, query):
    """Handle remove ads callback"""
    try:
        if query.from_user.id not in ADMINS:
            await query.answer("❌ You are not authorized!", show_alert=True)
            return
            
        # Remove advertisement from database
        await mdb.update_advirtisment(
            ads_string=None,
            ads_name=None,
            expiry=None,
            impression=0
        )
        
        # Answer callback and update message
        await query.answer("Advertisement removed successfully!")
        
        try:
            await query.message.edit_text("✅ <b>Advertisement Removed Successfully!</b>")
        except Exception as edit_error:
            logger.error(f"Failed to edit message: {edit_error}")
            try:
                await query.message.reply_text("✅ <b>Advertisement Removed Successfully!</b>")
            except Exception as reply_error:
                logger.error(f"Failed to reply: {reply_error}")
        
    except Exception as e:
        logger.error(f"Remove ads callback error: {e}")
        try:
            await query.answer("❌ Failed to remove advertisement!", show_alert=True)
        except Exception as answer_error:
            logger.error(f"Failed to send error answer: {answer_error}")

@Client.on_callback_query(filters.regex("^refresh_ads$"))
async def refresh_ads_callback(client, query):
    """Handle refresh ads callback"""
    try:
        if query.from_user.id not in ADMINS:
            await query.answer("❌ You are not authorized!", show_alert=True)
            return
            
        # Get fresh advertisement data
        ads_string, ads_name, impression_count = await mdb.get_advirtisment()
        
        if ads_string and ads_name and impression_count and impression_count > 0:
            status = f"✅ <b>Active Advertisement</b>\n\n"
            status += f"📝 <b>Text:</b> {ads_string}\n"
            status += f"👁️ <b>Remaining Impressions:</b> {impression_count}\n"
            status += f"📊 <b>Status:</b> Active"
        else:
            status = "❌ <b>No Active Advertisement</b>\n\nUse /setads to create a new advertisement."
            
        buttons = [
            [InlineKeyboardButton("🗑️ Remove Ads", callback_data="remove_ads")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ads")]
        ]
        
        # Answer callback first
        await query.answer("Refreshed!")
        
        try:
            await query.message.edit_text(status, reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as edit_error:
            logger.error(f"Failed to edit message: {edit_error}")
            try:
                await query.message.reply_text(status, reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as reply_error:
                logger.error(f"Failed to reply: {reply_error}")
        
    except Exception as e:
        logger.error(f"Refresh ads callback error: {e}")
        try:
            await query.answer("❌ Refresh failed! Please try again.", show_alert=True)
        except Exception as answer_error:
            logger.error(f"Failed to send error answer: {answer_error}")
@Client.on_message(filters.command("testads") & filters.user(ADMINS))
async def test_advertisement(client, message):
    """Test advertisement display"""
    try:
        ads_string, ads_name, impression_count = await mdb.get_advirtisment()
        
        if ads_string and ads_name and impression_count and impression_count > 0:
            test_ad_block = f"""📢 <b>Advertisement</b> 📢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ads_string}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>This is how your advertisement will appear above search results.</b>"""
            
            await message.reply_text(test_ad_block, disable_web_page_preview=False)
        else:
            await message.reply_text("❌ <b>No Active Advertisement</b>\n\nUse /setads to create a new advertisement.")
            
    except Exception as e:
        logger.error(f"Test advertisement error: {e}")
        await message.reply_text("❌ An error occurred while testing the advertisement!")

@Client.on_message(filters.command("debugads") & filters.user(ADMINS))
async def debug_advertisement(client, message):
    """Debug advertisement system"""
    try:
        # Get raw data from database
        configuration = await mdb.config_col.find_one({})
        
        debug_info = f"🔍 <b>Advertisement Debug Information</b>\n\n"
        
        if configuration:
            advertisement = configuration.get('advertisement')
            debug_info += f"📊 <b>Raw Advertisement Data:</b>\n"
            debug_info += f"   Advertisement Field: {advertisement}\n\n"
            
            if advertisement:
                debug_info += f"   ads_string: {advertisement.get('ads_string')}\n"
                debug_info += f"   ads_name: {advertisement.get('ads_name')}\n"
                debug_info += f"   impression_count: {advertisement.get('impression_count')}\n"
                debug_info += f"   expiry: {advertisement.get('expiry')}\n\n"
            
            # Test get_advirtisment function
            ads_string, ads_name, impression_count = await mdb.get_advirtisment()
            debug_info += f"🔧 <b>Function Output:</b>\n"
            debug_info += f"   ads_string: {ads_string}\n"
            debug_info += f"   ads_name: {ads_name}\n"
            debug_info += f"   impression_count: {impression_count}\n"
        else:
            debug_info += "❌ No configuration found in database"
            
        await message.reply_text(debug_info)
        
    except Exception as e:
        logger.error(f"Debug advertisement error: {e}")
        await message.reply_text(f"❌ Debug failed: {e}")
        
