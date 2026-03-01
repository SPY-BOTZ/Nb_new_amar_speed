import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
from database.users_chats_db import db
from database.refer import referdb
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import *
from fuzzywuzzy import process
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files
from logging_helper import LOGGER
from urllib.parse import quote_plus
from Lucia.util.file_properties import get_name, get_hash, get_media_file_size
from database.topdb import silentdb
import requests
import string
import tracemalloc
import atexit

tracemalloc.start()
atexit.register(tracemalloc.stop)

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}
lock = asyncio.Lock()

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    bot_id = client.me.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text("ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜")
        return
    await silentdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        if settings['auto_ffilter']:
            if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                if await is_check_admin(client, message.chat.id, message.from_user.id):
                    return
                return await message.delete()   
            await auto_filter(client, message)
    else:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ✅\n\n📂 ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ : {str(total_results)}\n🔍 ꜱᴇᴀʀᴄʜ :</b> <code>{search}</code>\n\n<b>‼️ ᴛʜɪs ɪs ᴀ <u>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</u> sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]]))


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text("ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜")
        return
    if content.startswith(("/", "#")):
        return  
    try:
        await silentdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b><i>ɪ ᴀᴍ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ 🚫.\nᴊᴏɪɴ ᴍʏ ɢʀᴏᴜᴘ ꜰʀᴏᴍ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ᴛʜᴇʀᴇ !</i></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ ", url=GRP_LNK)]])
            )
    except Exception as e:
        LOGGER.error(f"An error occurred: {str(e)}")


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('ɪɴᴠɪᴛᴇ ɪɪɴᴋ', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='premium')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await bot.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto("https://graph.org/file/1a2e64aee3d4d10edd930.jpg")
        )
    await query.message.edit_text(
        text=f'Hay Your refer link:\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nShare this link with your friends, Each time they join,  you will get 10 refferal points and after 100 points you will get 1 month premium subscription.',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
        )
    await query.answer()
	
async def build_pagination_buttons(btn, total_results, current_offset, next_offset, req, key, settings):
    limit = 10 if settings.get('max_btn') else int(MAX_B_TN)
    total_pages = math.ceil(total_results / limit)
    current_page = math.ceil(current_offset / limit) + 1
    pagination_row = []
    if current_offset > 0:
        prev_offset = max(0, current_offset - limit)
        pagination_row.append(InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{prev_offset}"))
    pagination_row.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))
    if next_offset is not None and next_offset != 0 and next_offset < total_results:
         pagination_row.append(InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{next_offset}"))
    elif next_offset == 0 and current_offset + limit < total_results:
         pass
    if len(pagination_row) == 1 and pagination_row[0].text.startswith(str(current_page)):
         if total_pages > 1:
             btn.append(pagination_row)
         else:
             btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages")])
    else:
         btn.append(pagination_row)

async def generic_filter_handler(client, query, key, offset, search_query):
    files, n_offset, total_results = await get_search_results(query.message.chat.id, search_query, offset=offset, filter=True)
    if not files:
        await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
        return
    temp.GETALL[key] = files
    chat_id = query.message.chat.id
    settings = await get_settings(chat_id)
    req = query.from_user.id
    btn = []
    if settings.get('button'):
        for file in files:
            btn.append([InlineKeyboardButton(
                text=f"{silent_size(file.file_size)} | {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                callback_data=f'file#{file.file_id}'
            )])
    btn.insert(0, [
        InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
        InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
        InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
    ])
    btn.insert(1, [InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")])
    await build_pagination_buttons(btn, total_results, offset, n_offset, req, key, settings)
    cap = ""
    if not settings.get('button'):
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_query, offset)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass

async def open_category_handler(client, query, items, prefix, title_text):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
             return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass
    _, key, offset = query.data.split("#")
    btn = []
    for i in range(0, len(items)-1, 2):
        btn.append([
            InlineKeyboardButton(
                text=items[i].title(),
                callback_data=f"{prefix}#{items[i].lower()}#{key}#0"
            ),
            InlineKeyboardButton(
                text=items[i+1].title(),
                callback_data=f"{prefix}#{items[i+1].lower()}#{key}#0"
            ),
        ])
    btn.insert(0, [InlineKeyboardButton(text=f"⇊ {title_text} ⇊", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"{prefix}#homepage#{key}#0")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))

async def filter_selection_handler(client, query, prefix):
    _, value, key, offset = query.data.split("#")
    if not value:
        await query.answer()
        return
    offset = int(offset)
    if value == "homepage":
        search = FRESH.get(key)
    else:
        search = BUTTONS.get(key) if BUTTONS.get(key) else FRESH.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    search = re.sub(r'\s+', ' ', search).strip()
    if value != "homepage":
        category_list = []
        if prefix == "fq":
            category_list = [x for x in QUALITIES if x]
        elif prefix == "fl":
            category_list = [x for x in LANGUAGES if x]
        elif prefix == "fs":
            category_list = [x for x in SEASONS if x]
        is_present = False
        match_pattern = ""
        if prefix == "fs":
            season_search = re.search(r"(?i)season\s*(\d+)", value)
            if season_search:
                season_num = int(season_search.group(1))
                added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                pattern_combined = re.escape(added_regex)
                if re.search(pattern_combined, search):
                    is_present = True
                    match_pattern = pattern_combined
            else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
             if value.lower().startswith("s0") and len(value) == 3:
                 short_val = "s" + str(int(value[1:]))
                 added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                 pattern_combined = re.escape(added_regex)
                 if re.search(pattern_combined, search):
                     is_present = True
                     match_pattern = pattern_combined
             else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        else:
            pattern = r'(?i)\b' + re.escape(value) + r'\b'
            if re.search(pattern, search):
                is_present = True
                match_pattern = pattern
        if is_present:
            search = re.sub(match_pattern, '', search, count=1)
        else:
            for item in category_list:
                if item.lower() == value.lower():
                    continue
                item_val = item
                if prefix == "fs":
                     season_search = re.search(r"(?i)season\s*(\d+)", item_val)
                     if season_search:
                         season_num = int(season_search.group(1))
                         added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     elif item_val.lower().startswith("s0") and len(item_val) == 3:
                         short_val = "s" + str(int(item_val[1:]))
                         added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     else:
                        pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                        search = re.sub(pattern, '', search)
                else:
                    pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                    search = re.sub(pattern, '', search)
            if prefix == "fs":
                 season_search = re.search(r"(?i)season\s*(\d+)", value)
                 if season_search:
                     season_num = int(season_search.group(1))
                     search = f"{search} (s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
                 if value.lower().startswith("s0") and len(value) == 3:
                     short_val = "s" + str(int(value[1:]))
                     search = f"{search} s0?{short_val[1:]}(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            else:
                search = f"{search} {value}"
    search = re.sub(r'\s+', ' ', search).strip()
    BUTTONS[key] = search
    await generic_filter_handler(client, query, key, offset, search)

async def handle_alert_status(client, query, status_text, alert_message, log_hashtag, is_hindi=False):
    ident, from_user = query.data.split("#")
    btn = [[InlineKeyboardButton(status_text, callback_data=f"{ident}alert#{from_user}")]]
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
        invite_url = link.invite_link
    except Exception:
        invite_url = GRP_LNK
    btn2 = [[
        InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=invite_url),
        InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
    ]]
    if is_hindi or "Available" in status_text or "Uploaded" in status_text:
         btn2.append([InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)])
    if query.from_user.id in ADMINS:
        user = await client.get_users(from_user)
        reply_markup = InlineKeyboardMarkup(btn)
        content = query.message.text
        await query.message.edit_text(f"<b><strike>{content}</strike></b>")
        await query.message.edit_reply_markup(reply_markup)
        simple_status = status_text.replace("•", "").strip()
        await query.answer(f"Sᴇᴛ ᴛᴏ {simple_status} !")
        content = extract_request_content(query.message.text)
        alert_text = alert_message.format(user_mention=user.mention, content=content)
        try:
            await client.send_message(
                chat_id=int(from_user),
                text=f"{alert_text}\n\n{log_hashtag}",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
        except UserIsBlocked:
             await client.send_message(
                chat_id=int(SUPPORT_CHAT_ID),
                text=f"{alert_text}\n\n{log_hashtag}\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
    else:
        await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        try:
            offset = int(offset)
        except (ValueError, TypeError):
            offset = 0

        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)

        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return

        await generic_filter_handler(bot, query, key, offset, search)
        await query.answer()
    except Exception as e:
        LOGGER.error(f"Error In Next Function - {e}")


@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, QUALITIES, "fq", "ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ")

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fq")

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, LANGUAGES, "fl", "ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ")

@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fl")
        
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def season_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, SEASONS, "fs", "ꜱᴇʟᴇᴄᴛ Sᴇᴀsᴏɴ")

@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_season_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fs")

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movies = await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            await bot.send_message(chat_id=BIN_CHANNEL,text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔰 Cʟɪᴄᴋ ʜᴇʀᴇ & ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴀᴅᴍɪɴ🔰", url=OWNER_LNK)]])
        k = await query.message.edit(script.MVE_NT_FND,reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await k.delete()
                
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = 
