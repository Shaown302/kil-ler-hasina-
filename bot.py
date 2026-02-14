# -*- coding: utf-8 -*-
"""
Hinata Bot - Final Premium v2.1
- Optimized for Render deployment
- Multi-Platform Media Downloader (yt-dlp)
- Advanced AI Engines (Gemini 3, DeepSeek, ChatGPT Addy)
- Premium UI with sanitized buttons and full command guide
"""
import os
import sys
import time
import json
import logging
import asyncio
import httpx
import shutil
import html
import re
import qrcode
import io
from datetime import datetime, timedelta
from typing import List, Dict, Union
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ChatMemberHandler
)
import yt_dlp

async def cmd_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        await update.message.reply_text("💡 Usage: /shorten <url>")
        return
    await do_url_shorten(update, context, context.args[0])

# ================= Configuration =================
OWNER_ID = 7333244376
BOT_TOKEN_FILE = "token.txt"
BOT_NAME = "Hinata"
BOT_USERNAME = "@Hinata_00_bot"

INBOX_FORWARD_GROUP_ID = -1003113491147

# tracked users -> forward groups
TRACKED_USER1_ID = 7039869055
FORWARD_USER1_GROUP_ID = -1002768142169
TRACKED_USER2_ID = 7209584974
FORWARD_USER2_GROUP_ID = -1002536019847

# source/destination
SOURCE_GROUP_ID = -4767799138
DESTINATION_GROUP_ID = -1002510490386

KEYWORDS = [
    "shawon", "shawn", "sn", "@shawonxnone", "shwon", "shaun", "sahun", "sawon",
    "sawn", "nusu", "nusrat", "saun", "ilma", "izumi", "🎀꧁𖨆❦︎ 𝑰𝒁𝑼𝑴𝑰 𝑼𝒄𝒉𝒊𝒉𝒂 ❦︎𖨆꧂🎀"
]

LOG_FILE = "hinata.log"
MAX_LOG_SIZE = 200 * 1024  # 200 KB

# Folders
os.makedirs("downloads", exist_ok=True)

# Latest API URLs
CHATGPT_API_URL = "https://addy-chatgpt-api.vercel.app/?text={prompt}"
GEMINI3_API = "https://shawon-gemini-3-api.onrender.com/api/ask?prompt={}"
DEEPSEEK_API = "https://void-deep.drsudo.workers.dev/api/?q={}"
INSTA_API = "https://instagram-api-ashy.vercel.app/api/ig-profile.php?username={}"
FF_API = "http://danger-info-alpha.vercel.app/accinfo?uid={}&key=DANGERxINFO"

# ================= Logging =================
def setup_logger():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        open(LOG_FILE, "w").close()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
    )
    return logging.getLogger("hinata")

logger = setup_logger()

# ================= Utilities =================
def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def read_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default if default is not None else []
                data = json.loads(content)
                if default is not None and not isinstance(data, type(default)):
                    return default
                return data
    except Exception:
        logger.exception("Failed to read JSON: %s", path)
    return default if default is not None else []

def write_json(path, data):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        logger.exception("Failed to write JSON: %s", path)

BOT_TOKEN = read_file(BOT_TOKEN_FILE)

# Global Settings (Can be saved to a config.json if needed)
CONFIG_FILE = "config.json"
def load_config():
    return read_json(CONFIG_FILE, {"global_access": True, "banned_users": []})

def save_config(config):
    write_json(CONFIG_FILE, config)

CONFIG = load_config()

start_time = time.time()
STATS = {
    "broadcasts": 0,
    "status": "online"
}

def get_uptime() -> str:
    elapsed = time.time() - start_time
    return str(timedelta(seconds=int(elapsed)))


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def check_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_owner(user_id):
        return True
    
    # Check if user is banned
    if user_id in CONFIG.get("banned_users", []):
        await update.effective_message.reply_text("🚫 <b>Access Denied:</b> You have been globally banned from using this bot.", parse_mode="HTML")
        return False
        
    # Check global access toggle
    if not CONFIG.get("global_access", True):
        await update.effective_message.reply_text("🔒 <b>Bot Maintenance:</b> The bot is currently set to private mode by the owner.", parse_mode="HTML")
        return False
        
    return True

# ================= Forward Helper =================
async def forward_or_copy(update: Update, context: ContextTypes.DEFAULT_TYPE, command_text: str = None):
    user = update.effective_user
    msg_type = "Command" if command_text else "Message"
    try:
        caption = f"📨 From: {user.full_name} (@{user.username})\nID: <code>{user.id}</code>\nType: {msg_type}"
        if command_text:
            caption += f"\nCommand: {command_text}"
        elif update.message and update.message.text:
            caption += f"\nMessage: {update.message.text}"

        await context.bot.send_message(chat_id=INBOX_FORWARD_GROUP_ID, text=caption, parse_mode="HTML")
        if update.message:
            await update.message.forward(chat_id=INBOX_FORWARD_GROUP_ID)
    except Exception as e:
        logger.warning(f"Failed to forward: {e}")
        try:
            if update.message:
                text = update.message.text or "<Media/Sticker/Other>"
                safe_text = f"📨 From: {user.full_name} (@{user.username})\nID: <code>{user.id}</code>\nType: {msg_type}\nContent: {text}"
                await context.bot.send_message(chat_id=INBOX_FORWARD_GROUP_ID, text=safe_text, parse_mode="HTML")
        except Exception as e2:
            logger.warning(f"Failed fallback forward: {e2}")

# ================= HTTP Helpers =================
async def fetch_json(client: httpx.AsyncClient, url: str):
    try:
        resp = await client.get(url, timeout=30.0)
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}
    except Exception as e:
        logger.exception("HTTP fetch failed for %s", url)
        return {"error": str(e)}

async def fetch_chatgpt(client: httpx.AsyncClient, prompt: str):
    url = CHATGPT_API_URL.format(prompt=quote(prompt))
    data = await fetch_json(client, url)
    if isinstance(data, dict):
        return data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    return str(data)

async def fetch_flirt(client: httpx.AsyncClient, prompt: str):
    system_prompt = "Act as a charming, romantic, and playful flirt. Respond to: "
    url = CHATGPT_API_URL.format(prompt=quote(system_prompt + prompt))
    data = await fetch_json(client, url)
    if isinstance(data, dict):
        return data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    return str(data)

async def fetch_code(client: httpx.AsyncClient, prompt: str):
    system_prompt = "Act as an expert software engineer. Provide clean code and explanations. Text: "
    url = CHATGPT_API_URL.format(prompt=quote(system_prompt + prompt))
    data = await fetch_json(client, url)
    if isinstance(data, dict):
        return data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    return str(data)

async def fetch_gemini3(client: httpx.AsyncClient, prompt: str):
    try:
        url = GEMINI3_API.format(quote(prompt))
        data = await fetch_json(client, url)
        if isinstance(data, dict):
            return data.get("response") or data.get("reply") or data.get("answer") or data.get("message") or json.dumps(data)
        res = str(data)
        if len(res) < 2 or "error" in res.lower():
             return "❌ Gemini API error or empty response."
        return res
    except Exception as e:
        logger.exception("Gemini3 fetch failed")
        return f"Error: {e}"

async def fetch_deepseek(client: httpx.AsyncClient, prompt: str):
    try:
        url = DEEPSEEK_API.format(quote(prompt))
        data = await fetch_json(client, url)
        if isinstance(data, dict):
            return data.get("Response") or data.get("reply") or data.get("answer") or data.get("raw") or json.dumps(data)
        return str(data)
    except Exception as e:
        logger.exception("DeepSeek fetch failed")
        return f"Error: {e}"

# ================= Broadcast Helpers =================
def update_stats(sent_users=0, failed_users=0, sent_groups=0, failed_groups=0):
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    if not isinstance(stats, dict): stats = default_stats
    stats["sent_users"] = stats.get("sent_users", 0) + sent_users
    stats["failed_users"] = stats.get("failed_users", 0) + failed_users
    stats["sent_groups"] = stats.get("sent_groups", 0) + sent_groups
    stats["failed_groups"] = stats.get("failed_groups", 0) + failed_groups
    write_json("stats.json", stats)

# ================= Commands =================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context):
        return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/start")
    user = update.effective_user
    users = read_json("users.json", [])
    
    # Registration & First-time Notification
    users = read_json("users.json", [])
    user_entry = next((u for u in users if u['id'] == user.id), None) if users and isinstance(users[0], dict) else None
    
    # Fallback for old format (list of IDs)
    if users and not isinstance(users[0], dict):
        users = [{"id": uid, "name": "Unknown", "username": "unknown"} for uid in users]

    if not any(u['id'] == user.id for u in users):
        new_user = {
            "id": user.id,
            "name": user.full_name,
            "username": user.username,
            "joined_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        users.append(new_user)
        write_json("users.json", users)
        
        if not is_owner(user.id):
            admin_msg = (f"👤 <b>New User Notification</b>\n\n"
                         f"🆔 <b>Name:</b> {user.full_name}\n"
                         f"🔗 <b>Username:</b> @{user.username}\n"
                         f"🔑 <b>ID:</b> <code>{user.id}</code>")
            try:
                await context.bot.send_message(chat_id=OWNER_ID, text=admin_msg, parse_mode="HTML")
            except Exception:
                pass
    elif user_deprecated := next((u for u in users if u['id'] == user.id), None):
        # Update name/username if changed
        if user_deprecated.get('name') != user.full_name or user_deprecated.get('username') != user.username:
            user_deprecated['name'] = user.full_name
            user_deprecated['username'] = user.username
            write_json("users.json", users)


    # UI Buttons
    buttons = [
        [InlineKeyboardButton("🧠 Gemini 3", callback_data="btn_gemini"),
         InlineKeyboardButton("🔥 DeepSeek", callback_data="btn_deepseek")],
        [InlineKeyboardButton("💖 Flirt AI", callback_data="btn_flirt"),
         InlineKeyboardButton("🎲 Truth/Dare", callback_data="btn_tod")],
        [InlineKeyboardButton("📸 Insta Info", callback_data="btn_insta"),
         InlineKeyboardButton("👤 User Info", callback_data="btn_userinfo")],
        [InlineKeyboardButton("🎮 FF Player", callback_data="btn_ff"),
         InlineKeyboardButton("🏰 FF Guild", callback_data="btn_ffguild")],
        [InlineKeyboardButton("📥 Downloader", callback_data="btn_dl"),
         InlineKeyboardButton("🖼 QR Gen", callback_data="btn_qrgen")],
        [InlineKeyboardButton("🔗 Shortener", callback_data="btn_shorten"),
         InlineKeyboardButton("👑 Owner", callback_data="btn_owner")],
        [InlineKeyboardButton("📜 Commands", callback_data="btn_commands"),
         InlineKeyboardButton("❓ Help", callback_data="btn_help")]
    ]
    if is_owner(user.id):
        buttons.append([InlineKeyboardButton("⚙️ Admin Menu", callback_data="btn_admin")])

    keyboard = InlineKeyboardMarkup(buttons)
    welcome_text = (
        f"✨ <b>Welcome to {BOT_NAME} v2.5</b> ✨\n\n"
        "I am your premium AI companion, powered by elite models "
        "and specialized tools to enhance your experience! 🚀\n\n"
        "🌟 <b>Core AI Engines:</b>\n"
        "╭── 🧠 <b>Gemini 3 Pro</b>\n"
        "├── 🚀 <b>DeepSeek v3.2</b>\n"
        "╰── 💬 <b>ChatGPT Addy</b>\n\n"
        "🛠 <b>Expert Utilities:</b>\n"
        "╭── 📸 <b>Instagram Lookup</b>\n"
        "├── 🎮 <b>FF UID Scraper</b>\n"
        "├── 💖 <b>Flirt Assistant</b>\n"
        "╰── 💻 <b>Master Code AI</b>\n\n"
        "<i>Select a service from the menu below!</i> 👇"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="HTML")

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 <b>This bot is private.</b> Only the owner can use it.", parse_mode="HTML")
        return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/ping")
    start_ping = time.time()
    ping_ms = int((time.time() - start_ping) * 1000)
    uptime = get_uptime()
    ping_text = (
        f"🚀 <b>System Status: Online</b>\n\n"
        f"⚡ <b>Latency:</b> <code>{ping_ms} ms</code>\n"
        f"⏱️ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"🤖 <b>Username:</b> {BOT_USERNAME}\n"
        f"📡 <b>Server:</b> Active ✅"
    )
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(ping_text, parse_mode="HTML", reply_markup=back_btn)
    else:
        await update.message.reply_text(ping_text, parse_mode="HTML", reply_markup=back_btn)

async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("🔒 <b>Access Denied:</b> This command guide is for the owner only.", parse_mode="HTML")
        return
    clear_states(context.user_data)
    text = (
        "📜 <b>Hinata Bot: Full Command Guide</b>\n\n"
        "🤖 <b>AI Interaction:</b>\n"
        "├ <code>/gemini &lt;prompt&gt;</code> - High-IQ Intelligence\n"
        "├ <code>/deepseek &lt;prompt&gt;</code> - Fast Analysis Engine\n"
        "├ <code>/code &lt;request&gt;</code> - Software Engineering\n"
        "├ <code>/flirt &lt;text&gt;</code> - Romantic Companion\n"
        "└ <code>/ai &lt;prompt&gt;</code> - Parallel Brain Power\n\n"
        "🎥 <b>Premium Downloader:</b>\n"
        "├ <code>/dl &lt;url&gt;</code> - One-click Media Fetch\n"
        "└ <i>(Insta Reels, YT, TikTok, X, FB)</i>\n\n"
        "📡 <b>System & Utilities:</b>\n"
        "├ <code>/insta &lt;user&gt;</code> - Search Profiles\n"
        "├ <code>/userinfo &lt;id/user&gt;</code> - Telegram ID\n"
        "├ <code>/ff &lt;uid&gt;</code> - Player Statistics\n"
        "├ <code>/ping</code> - Check Connection\n"
        "├ <code>/help</code> - Quick Guide\n"
        "├ <code>/shorten &lt;url&gt;</code> - URL Shortener\n"
        "└ <code>/start</code> - Interactive Menu\n"
    )
    if is_owner(user_id):
        text += (
            "\n👑 <b>Admin Powers:</b>\n"
            "├ <code>/stats</code> - Global Dashboard\n"
            "├ <code>/ban [chat] [user]</code> - Remote Ban\n"
            "├ <code>/mute [chat] [user]</code> - Remote Mute\n"
            "├ <code>/kick [chat] [user]</code> - Remote Kick\n"
            "├ <code>/broadcastall &lt;msg&gt;</code> - Global Blast\n"
            "├ <code>/broadcastuser &lt;id&gt; &lt;msg&gt;</code> - User DM\n"
            "└ <code>/broadcast_media</code> - Media Blast"
        )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 <b>Private Bot:</b> Contact @ShaunXnone for access.", parse_mode="HTML")
        return
    clear_states(context.user_data)
    help_text = (
        "❓ <b>How to Use Hinata Bot</b>\n\n"
        "1. <b>Menu Mode:</b> Use the buttons on /start for guided flows.\n"
        "2. <b>Command Mode:</b> Type /gemini or /dl followed by your input.\n\n"
        "💡 <b>Tip:</b> Click 📜 <b>Commands</b> for the full list of syntax!"
    )
    if update.callback_query:
         await update.callback_query.edit_message_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
    else:
        await update.message.reply_text(help_text, parse_mode="HTML")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    users = len(read_json("users.json", []))
    groups = len(read_json("groups.json", []))
    text = (f"📊 <b>Bot Metrics Viewer</b>\n\n"
            f"👤 <b>Users:</b> <code>{users}</code>\n"
            f"👥 <b>Groups:</b> <code>{groups}</code>\n\n"
            f"📤 <b>Broadcast Record:</b>\n"
            f"✅ Users: {stats.get('sent_users')}\n"
            f"❌ Fail Users: {stats.get('failed_users')}\n"
            f"✅ Groups: {stats.get('sent_groups')}\n"
            f"❌ Fail Groups: {stats.get('failed_groups')}")
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("💡 Usage: /gban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        if target_id == OWNER_ID:
            await update.message.reply_text("❌ You cannot ban the owner.")
            return
        if target_id not in CONFIG["banned_users"]:
            CONFIG["banned_users"].append(target_id)
            save_config(CONFIG)
            await update.message.reply_text(f"✅ User <code>{target_id}</code> has been globally banned.", parse_mode="HTML")
        else:
            await update.message.reply_text("ℹ️ User is already banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID.")

async def cmd_ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("💡 Usage: /ungban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        if target_id in CONFIG["banned_users"]:
            CONFIG["banned_users"].remove(target_id)
            save_config(CONFIG)
            await update.message.reply_text(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
        else:
            await update.message.reply_text("ℹ️ User is not banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID.")

async def cmd_toggle_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    CONFIG["global_access"] = not CONFIG["global_access"]
    save_config(CONFIG)
    status = "ON (Public)" if CONFIG["global_access"] else "OFF (Private)"
    await update.message.reply_text(f"🔐 <b>Global Access:</b> <code>{status}</code>", parse_mode="HTML")

# ================= AI Command Functions =================
async def cmd_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💡 Usage: /gemini <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🧠 Gemini 3 is thinking... ⏳")
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"💎 <b>Gemini Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💡 Usage: /deepseek <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🚀 DeepSeek is searching... ⏳")
    async with httpx.AsyncClient() as client:
        reply = await fetch_deepseek(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"🔥 <b>DeepSeek Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💖 Usage: /flirt <text>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("😚 Thinking... 💘")
    async with httpx.AsyncClient() as client:
        reply = await fetch_flirt(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"✨ <b>Flirt AI:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_ai_combined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    clear_states(context.user_data)
    if not context.args: return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🤖 Consultation in progress... ⏳")
    async with httpx.AsyncClient() as client:
        t1 = fetch_chatgpt(client, prompt)
        t2 = fetch_gemini3(client, prompt)
        r1, r2 = await asyncio.gather(t1, t2)
    safe_r1, safe_r2 = html.escape(r1), html.escape(r2)
    await msg.edit_text(f"💡 <b>Combined AI Results:</b>\n\n<b>ChatGPT:</b>\n{safe_r1}\n\n<b>Gemini:</b>\n{safe_r2}", parse_mode="HTML")

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💻 Usage: /code <request>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("👨‍💻 Working on code... ⌨️")
    async with httpx.AsyncClient() as client:
        reply = await fetch_code(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"💻 <b>Code AI Output:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_qrgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        help_text = (
            "🖼️ <b>Advanced QR Generator</b>\n\n"
            "<b>Usage:</b> <code>/qrgen [text] [options]</code>\n\n"
            "<b>Options:</b>\n"
            "├ <code>-c \"caption\"</code> (text below)\n"
            "├ <code>-d hex</code> (dark color, e.g. #ff0000)\n"
            "├ <code>-l hex</code> (light color)\n"
            "├ <code>-img url</code> (center image)\n"
            "└ <code>-s size</code> (e.g. 300)\n\n"
            "<b>Example:</b>\n"
            "<code>/qrgen https://google.com -c \"Google\" -d #4285F4</code>"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")
        return

    raw_args = " ".join(context.args)
    # Improved parsing for flags
    text = raw_args
    params = {}
    
    if " -" in raw_args:
        # Split text from flags
        text_match = re.split(r'\s+-\w+', raw_args, maxsplit=1)
        text = text_match[0].strip()
        flags_part = raw_args[len(text):].strip()
        
        # Parse flags like -c "text" or -d hex
        matches = re.findall(r'-(\w+)\s+(?:\"([^\"]+)\"|(\S+))', flags_part)
        for key, val1, val2 in matches:
            val = val1 or val2
            if key == "c": params["caption"] = val
            elif key == "d": params["dark"] = val.replace("#", "")
            elif key == "l": params["light"] = val.replace("#", "")
            elif key == "img": params["centerImageUrl"] = val
            elif key == "s": params["size"] = val

    msg = await update.message.reply_text("✨ <b>Crafting Advanced QR...</b>", parse_mode="HTML")
    
    try:
        api_url = f"https://quickchart.io/qr?text={quote(text)}"
        for k, v in params.items():
            api_url += f"&{k}={quote(str(v))}"
        
        # Add high error correction if image is present
        if "centerImageUrl" in params:
            api_url += "&ecLevel=H"
            
        file_name = f"qr_{int(time.time())}.png"
        file_path = os.path.join("downloads", file_name)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=20.0)
            if resp.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(resp.content)
            else:
                await msg.edit_text(f"❌ <b>API Error:</b> <code>HTTP {resp.status_code}</code>", parse_mode="HTML")
                return

        await msg.delete()
        with open(file_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo, 
                caption=f"🖼️ <b>QR Code Generated</b>\n\n📝 <b>Content:</b> <code>{html.escape(text[:200])}</code>", 
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"QR Gen Error: {e}")
        await msg.edit_text(f"❌ <b>Generation Failed:</b> <code>System Error</code>", parse_mode="HTML")

async def cmd_qrread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = update.message
    photo = None
    
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1]
    elif msg.photo:
        photo = msg.photo[-1]
    else:
        await msg.reply_text("💡 Usage: Reply to a photo with /qrread to read the QR code.")
        return

    status = await msg.reply_text("🔍 <b>Reading QR Code...</b>", parse_mode="HTML")
    try:
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path # This is the direct download URL
        
        # Use a free API to read QR
        api_url = f"https://api.qrserver.com/v1/read-qr-code/?fileurl={quote(file_url)}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url)
            data = resp.json()
            
        if data and isinstance(data, list) and data[0]['symbol'][0]['data']:
            result = data[0]['symbol'][0]['data']
            await status.edit_text(f"✅ <b>QR Code Decoded:</b>\n\n<code>{html.escape(result)}</code>", parse_mode="HTML")
        else:
            await status.edit_text("❌ <b>Decode Failed:</b> No QR code detected in this image.")
    except Exception as e:
        logger.error(f"QR Read Error: {e}")
        await status.edit_text(f"❌ <b>System Error:</b> <code>Something went wrong while scanning.</code>", parse_mode="HTML")

async def do_url_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    if not await check_permission(update, context): return
    # Use the provided example API key from Shareaholic docs
    apikey = "8943b7fd64cd8b1770ff5affa9a9437b"
    api_url = f"https://www.shareaholic.com/v2/share/shorten_link?apikey={apikey}&url={quote(url)}&service[name]=shrlc"
    
    msg = await update.message.reply_text("🔗 <b>Shortening your URL...</b>", parse_mode="HTML")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=15.0)
            data = resp.json()
            
        if data.get("status_code") == "200" and data.get("data"):
            short_url = data["data"]
            text = (
                f"✅ <b>URL Shortened Successfully!</b>\n\n"
                f"🔗 <b>Original:</b> <code>{html.escape(url)}</code>\n"
                f"🚀 <b>Short URL:</b> <code>{short_url}</code>"
            )
            await msg.edit_text(text, parse_mode="HTML")
        elif "errors" in data:
            err = data["errors"][0].get("detail", "Unknown API Error")
            await msg.edit_text(f"❌ <b>API Error:</b> <code>{html.escape(err)}</code>", parse_mode="HTML")
        else:
            await msg.edit_text("❌ <b>Error:</b> Could not shorten this URL. Please ensure it is valid.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Shortener Error: {e}")
        await msg.edit_text("❌ <b>System Error:</b> Service currently unavailable.", parse_mode="HTML")

async def cmd_truthordare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    kb = [
        [InlineKeyboardButton("🔵 Truth", callback_data="tod_truth"),
         InlineKeyboardButton("🔴 Dare", callback_data="tod_dare")],
        [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    text = "🎲 <b>Truth or Dare: Selection</b>\n\nChoose your destiny below:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# ================= Flows & State Management =================
AWAIT_GEMINI = "await_gemini"
AWAIT_DEEPSEEK = "await_deepseek"
AWAIT_FLIRT = "await_flirt"
AWAIT_INSTA = "await_insta"
AWAIT_USERINFO = "await_userinfo"
AWAIT_FF = "await_ff"
AWAIT_FFGUILD = "await_ffguild"
AWAIT_CODE = "await_code"
AWAIT_DL = "await_dl"
AWAIT_QRGEN = "await_qrgen"
AWAIT_SHORTEN = "await_shorten"

def clear_states(ud):
    """Clears all pending prompt states to prevent tool conflicts."""
    for key in [AWAIT_GEMINI, AWAIT_DEEPSEEK, AWAIT_FLIRT, AWAIT_INSTA, AWAIT_USERINFO, AWAIT_FF, AWAIT_FFGUILD, AWAIT_CODE, AWAIT_DL, AWAIT_QRGEN, AWAIT_SHORTEN]:
        ud.pop(key, None)

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    msg = update.message
    status = await msg.reply_text("⏳ <b>Analyzing URL...</b> 🔍\n<i>Fetching available qualities...</i>", parse_mode="HTML")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            formats = info.get('formats', [])
            title = info.get('title', 'Media')
            duration = info.get('duration', 0)
            views = info.get('view_count', 0)
            uploader = info.get('uploader', 'Unknown')
            
            # Filter qualities
            available_formats = []
            seen_heights = set()
            
            # Add MP3 option
            available_formats.append({"id": "bestaudio/best", "label": "🎵 MP3 (Audio)", "ext": "mp3"})

            for f in formats:
                h = f.get('height')
                if h and h in [360, 480, 720, 1080] and h not in seen_heights:
                    ext = f.get('ext', 'mp4')
                    available_formats.append({"id": f['format_id'], "label": f"🎬 {h}p ({ext.upper()})", "ext": ext})
                    seen_heights.add(h)

            if not seen_heights:
                available_formats.append({"id": "best[ext=mp4]/best", "label": "🎬 Best Quality", "ext": "mp4"})

            # Save info for later
            context.user_data['dl_info'] = {
                'url': url,
                'title': title,
                'duration': str(timedelta(seconds=duration)),
                'views': f"{views:,}" if views else "N/A",
                'uploader': uploader
            }

            buttons = []
            row = []
            for fmt in available_formats:
                row.append(InlineKeyboardButton(fmt['label'], callback_data=f"dl_fmt|{fmt['id']}|{fmt['ext']}"))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row: buttons.append(row)
            buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="btn_back")])

            cap = (
                f"🎬 <b>Title:</b> {html.escape(title[:100])}\n"
                f"👤 <b>Uploader:</b> {html.escape(uploader)}\n"
                f"⏱ <b>Duration:</b> {context.user_data['dl_info']['duration']}\n"
                f"👁 <b>Views:</b> {context.user_data['dl_info']['views']}\n\n"
                f"<i>Choose your preferred quality below:</i>"
            )
            
            await status.edit_text(cap, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    except Exception as e:
        logger.exception("Format fetch failed")
        await status.edit_text(f"❌ <b>Error:</b> <code>{html.escape(str(e))[:200]}</code>", parse_mode="HTML")

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE, format_id: str, extension: str):
    query = update.callback_query
    dl_info = context.user_data.get('dl_info')
    if not dl_info:
        await query.answer("❌ Error: Download session expired.")
        return

    url = dl_info['url']
    await query.edit_message_text(f"📥 <b>Downloading {dl_info['title']}...</b>\n\nQuality: <code>{format_id}</code>\n<i>This might take a moment.</i>", parse_mode="HTML")

    filename = f"downloads/{int(time.time())}.{extension}"
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': filename,
        'restrictfilenames': True,
        'quiet': True,
    }

    if extension == "mp3":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
            
        # Check if actual filename changed (e.g. mp3 conversion)
        actual_file = filename
        if extension == "mp3" and not os.path.exists(filename):
            actual_file = filename.replace(".mp3", "") + ".mp3"
            if not os.path.exists(actual_file):
                for f in os.listdir("downloads"):
                    if f.endswith(".mp3"):
                        actual_file = os.path.join("downloads", f)
                        break

        if not os.path.exists(actual_file):
            raise Exception("File not found after download.")

        filesize = os.path.getsize(actual_file)
        if filesize > 50 * 1024 * 1024:
            os.remove(actual_file)
            await query.edit_message_text("⚠️ <b>Size Limit exceeded (50MB).</b>")
            return

        await query.edit_message_text("📤 <b>Uploading...</b>", parse_mode="HTML")
        
        cap = (
            f"🎬 <b>{html.escape(dl_info['title'][:100])}</b>\n\n"
            f"👤 <b>Uploader:</b> {html.escape(dl_info['uploader'])}\n"
            f"⏱ <b>Duration:</b> {dl_info['duration']}\n"
            f"👁 <b>Views:</b> {dl_info['views']}\n\n"
            f"🚀 <i>Fetched via {BOT_NAME}</i>"
        )

        with open(actual_file, 'rb') as f:
            if extension == "mp3":
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=cap, parse_mode="HTML")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=f, caption=cap, parse_mode="HTML")

        await query.delete_message()
        if os.path.exists(actual_file): os.remove(actual_file)

    except Exception as e:
        logger.exception("Download failed")
        await query.edit_message_text(f"❌ <b>Download Failed:</b>\n<code>{html.escape(str(e))[:100]}</code>", parse_mode="HTML")

async def do_insta_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    msg = await update.message.reply_text("🔎 Searching Instagram... ⏳")
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, INSTA_API.format(username))
    if not isinstance(data, dict) or data.get("status") != "ok":
        await msg.edit_text("❌ Profile not found.")
        return
    p = data.get("profile", {})
    
    # Extract more info as requested
    full_name = html.escape(p.get('full_name') or "Unknown")
    uname = html.escape(p.get('username') or username)
    bio = html.escape(p.get('biography') or "No bio")
    followers = p.get('followers', 0)
    following = p.get('following', 0)
    posts = p.get('posts', 0)
    user_id = p.get('id', 'N/A')
    is_private = "Yes 🔒" if p.get('is_private') else "No 🔓"
    is_verified = "Yes ✅" if p.get('is_verified') else "No ❌"
    is_business = "Yes 💼" if p.get('is_business_account') else "No"
    created_year = p.get('account_creation_year', 'Unknown')
    ext_url = p.get('external_url') or "None"

    cap = (
        f"📸 <b>Instagram Profile: {full_name}</b>\n\n"
        f"👤 <b>Username:</b> @{uname}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"👥 <b>Followers:</b> {followers:,}\n"
        f"👣 <b>Following:</b> {following:,}\n"
        f"📮 <b>Posts:</b> {posts:,}\n\n"
        f"📅 <b>Created Around:</b> {created_year}\n"
        f"🔒 <b>Private:</b> {is_private}\n"
        f"🔵 <b>Verified:</b> {is_verified}\n"
        f"💼 <b>Business:</b> {is_business}\n"
        f"🔗 <b>Link:</b> {ext_url}\n\n"
        f"📝 <b>Bio:</b>\n{bio}"
    )
    
    pic = p.get("profile_pic_url_hd")
    if pic:
        try:
            await msg.delete()
            await update.message.reply_photo(photo=pic, caption=cap[:1024], parse_mode="HTML")
        except Exception:
            await update.message.reply_text(cap, parse_mode="HTML")
    else:
        await msg.edit_text(cap, parse_mode="HTML")

async def do_ff_guild_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, guild_id: str):
    msg = await update.message.reply_text("🔍 <b>Searching Guild...</b>", parse_mode="HTML")
    
    # Progress Bar Animation
    for i in range(1, 6):
        bar = "🟩" * i + "⬜" * (5 - i)
        await msg.edit_text(f"🎮 <b>Fetching Guild Data...</b>\n\n<code>{bar} {i*20}%</code>", parse_mode="HTML")
        await asyncio.sleep(0.5)

    url = f"http://guild-info-danger.vercel.app/guild?guild_id={guild_id}&region=bd"
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, url)
    
    if not isinstance(data, dict) or data.get("status") != "success":
        await msg.edit_text("❌ <b>Guild not found or API error.</b>", parse_mode="HTML")
        return

    # Extract Data
    name = html.escape(data.get("guild_name", "Unknown"))
    g_id = data.get("guild_id", "N/A")
    level = data.get("guild_level", "0")
    members = data.get("current_members", "0")
    max_members = data.get("max_members", "0")
    region = data.get("guild_region", "Unknown")
    slogan = html.escape(data.get("guild_slogan", "No Slogan"))
    act_points = data.get("total_activity_points", 0)
    weekly_points = data.get("weekly_activity_points", 0)
    min_level = data.get("min_level_required", 0)
    leader = data.get("guild_leader", {})
    l_name = html.escape(leader.get("name", "Unknown"))
    l_uid = leader.get("uid", "N/A")
    l_level = leader.get("level", 0)
    
    report = (
        f"🏰 <b>FREE FIRE GUILD REPORT</b> 🏰\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>Name:</b> <code>{name}</code>\n"
        f"🆔 <b>Guild ID:</b> <code>{g_id}</code>\n"
        f"⭐ <b>Level:</b> <code>{level}</code>\n"
        f"👥 <b>Members:</b> <code>{members}/{max_members}</code>\n"
        f"🌍 <b>Region:</b> <code>{region}</code>\n"
        f"🎭 <b>Slogan:</b> <i>{slogan}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Activity Details:</b>\n"
        f"🔥 <b>Total Glories:</b> <code>{act_points:,}</code>\n"
        f"📅 <b>Weekly Glories:</b> <code>{weekly_points:,}</code>\n"
        f"🎖 <b>Min Level Req:</b> <code>{min_level}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Guild Leader Info:</b>\n"
        f"👤 <b>Name:</b> {l_name}\n"
        f"🔑 <b>UID:</b> <code>{l_uid}</code>\n"
        f"📈 <b>Level:</b> <code>{l_level}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Fetched via {BOT_NAME}</i>"
    )
    
    await msg.edit_text(report, parse_mode="HTML")

async def do_ff_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.message.reply_text("🎮 Fetching FF Player... ⏳")
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, FF_API.format(uid))
    safe_data = html.escape(json.dumps(data, indent=2))
    await msg.edit_text(f"🎮 <b>FF Player Statistics:</b>\n\n<code>{safe_data}</code>", parse_mode="HTML")

async def do_user_info_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    target_user = None
    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif query:
        try:
            # Try as ID first
            if query.isdigit() or query.startswith("-"):
                 chat = await context.bot.get_chat(int(query))
                 target_user = chat
            else:
                 # Try as username
                 username = query.replace("@", "")
                 chat = await context.bot.get_chat(f"@{username}")
                 target_user = chat
        except Exception:
            await update.message.reply_text("❌ User not found. The bot must share a group with the user or the person must have started the bot.")
            return
    else:
        target_user = update.effective_user

    if not target_user: return

    status_msg = await update.message.reply_text("👤 Fetching user details...")
    
    # Detailed info
    user_id = target_user.id
    first_name = html.escape(target_user.first_name or "N/A")
    last_name = html.escape(target_user.last_name or "")
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{target_user.username}" if target_user.username else "None"
    is_bot = "Yes 🤖" if getattr(target_user, 'is_bot', False) else "No"
    is_premium = "Yes ⭐" if getattr(target_user, 'is_premium', False) else "No"
    dc_id = getattr(target_user, 'dc_id', "Unknown")
    
    bio = "N/A"
    try:
        chat_full = await context.bot.get_chat(user_id)
        bio = html.escape(chat_full.bio or "No bio set")
    except: pass

    info_text = (
        f"👤 <b>Telegram User Information</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📛 <b>Full Name:</b> {full_name}\n"
        f"🔗 <b>Username:</b> {username}\n\n"
        f"🤖 <b>Is Bot:</b> {is_bot}\n"
        f"💎 <b>Premium:</b> {is_premium}\n"
        f"🌐 <b>DC ID:</b> {dc_id}\n\n"
        f"📝 <b>Bio:</b>\n{bio}\n\n"
        f"🔗 <b>Permanent Link:</b> <a href='tg://user?id={user_id}'>Click Here</a>"
    )

    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            photo_file = photos.photos[0][-1].file_id
            await status_msg.delete()
            await update.message.reply_photo(photo=photo_file, caption=info_text, parse_mode="HTML")
        else:
            await status_msg.edit_text(info_text, parse_mode="HTML")
    except Exception:
        await status_msg.edit_text(info_text, parse_mode="HTML")

# ================= Handlers =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    clear_states(context.user_data)
    await query.answer()
    
    if data in ["btn_gemini", "btn_deepseek", "btn_flirt", "btn_code", "btn_insta", "btn_ff", "btn_dl", "btn_admin", "btn_ping", "btn_commands", "btn_help", "btn_shorten"]:
        if not is_owner(user_id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="🔒 <b>Owner Only:</b> Command restricted to Shawon (@ShaunXnone).", parse_mode="HTML")
            return

    back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])
    if data == "btn_gemini":
        context.user_data[AWAIT_GEMINI] = True
        await query.edit_message_text("🧠 <b>Gemini Intelligence:</b>\n\nSend your prompt below:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_deepseek":
        context.user_data[AWAIT_DEEPSEEK] = True
        await query.edit_message_text("🚀 <b>DeepSeek Engine:</b>\n\nSend your question below:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_flirt":
        context.user_data[AWAIT_FLIRT] = True
        await query.edit_message_text("💘 <b>Sweet Companion:</b>\n\nSay something sweet:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_code":
        context.user_data[AWAIT_CODE] = True
        await query.edit_message_text("💻 <b>Master Logic Assistant:</b>\n\nDescribe your code request:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_insta":
        context.user_data[AWAIT_INSTA] = True
        await query.edit_message_text("📸 <b>Instagram Lookup:</b>\n\nEnter username:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_userinfo":
        context.user_data[AWAIT_USERINFO] = True
        await query.edit_message_text("👤 <b>User Information:</b>\n\nEnter User ID or Username:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_ff":
        context.user_data[AWAIT_FF] = True
        await query.edit_message_text("🎮 <b>FF Player Scraper:</b>\n\nEnter Player UID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_ffguild":
        context.user_data[AWAIT_FFGUILD] = True
        await query.edit_message_text("🏰 <b>FF Guild Scraper:</b>\n\nEnter Guild ID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_dl":
        context.user_data[AWAIT_DL] = True
        await query.edit_message_text("📥 <b>Premium Downloader:</b>\n\nPaste URL (TikTok, Reels, YT):", reply_markup=back, parse_mode="HTML")
    elif data == "btn_qrgen":
        context.user_data[AWAIT_QRGEN] = True
        await query.edit_message_text("🖼 <b>QR Generator:</b>\n\nEnter text or URL:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_shorten":
        context.user_data[AWAIT_SHORTEN] = True
        await query.edit_message_text("🔗 <b>URL Shortener:</b>\n\nEnter the long URL below:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_tod":
        await cmd_truthordare(update, context)
    elif data == "btn_ping":
        await cmd_ping(update, context)
    elif data == "btn_commands":
        await cmd_commands(update, context)
    elif data == "btn_help":
        await cmd_help(update, context)
    elif data == "btn_admin":
        kb = [
            [InlineKeyboardButton("📢 All Groups", callback_data="adm_ball"),
             InlineKeyboardButton("🖼️ Media Blast", callback_data="adm_media")],
            [InlineKeyboardButton("👤 User DM", callback_data="adm_user"),
             InlineKeyboardButton("👥 Group DM", callback_data="adm_group")],
            [InlineKeyboardButton("🛡️ Group Manage", callback_data="adm_gmanage"),
             InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
        ]
        await query.edit_message_text("⚙️ <b>Admin Control Center</b>\n\nChoose a broadcast tool or view metrics:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    elif data == "adm_gmanage":
        text = (
            "🛡️ <b>Remote Group Management</b>\n\n"
            "Use these commands to manage users in specific groups:\n\n"
            "🚫 <b>Ban:</b> <code>/ban [chat_id] [user_id]</code>\n"
            "✅ <b>Unban:</b> <code>/unban [chat_id] [user_id]</code>\n"
            "🔇 <b>Mute:</b> <code>/mute [chat_id] [user_id]</code>\n"
            "🔊 <b>Unmute:</b> <code>/unmute [chat_id] [user_id]</code>\n"
            "👞 <b>Kick:</b> <code>/kick [chat_id] [user_id]</code>\n\n"
            "<i>Note: Bot must be admin in the target group!</i>"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_admin")]]))
    elif data == "adm_ball":
        await query.edit_message_text("📢 <b>Broadcast to All Groups:</b>\n\nUsage: <code>/broadcastall [message]</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_admin")]]))
    elif data == "adm_media":
        await query.edit_message_text("🖼️ <b>Media Broadcast:</b>\n\nUsage: Send/Reply to a photo with <code>/broadcast_media [caption]</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_admin")]]))
    elif data == "adm_user":
        await query.edit_message_text("👤 <b>Direct User DM:</b>\n\nUsage: <code>/broadcastuser [id] [message]</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_admin")]]))
    elif data == "adm_group":
        await query.edit_message_text("👥 <b>Target Group:</b>\n\nUsage: <code>/broadcast [id] [message]</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_admin")]]))
    elif data == "adm_stats":
        await cmd_stats(update, context)
    elif data == "btn_owner":
        owner_text = (
            "👑 <b>Owner Information</b>\n\n"
            "👤 <b>Name:</b> Shawon\n"
            "🔗 <b>Username:</b> @ShaunXnone\n"
            "🌍 <b>Location:</b> Bangladesh\n"
            "💻 <b>Role:</b> Full-Stack Developer & Bot Creator\n\n"
            "<i>Feel free to message for custom bot developments!</i>"
        )
        await query.edit_message_text(owner_text, parse_mode="HTML", reply_markup=back)
    elif data == "btn_back":
        await cmd_start(update, context)
    elif data.startswith("dl_fmt|"):
        _, fmt_id, ext = data.split("|")
        await process_download(update, context, fmt_id, ext)
    elif data.startswith("tod_"):
        mode = data.split("_")[1] # truth or dare
        await do_tod_fetch(update, context, mode)

async def do_tod_fetch(update: Update, _context: ContextTypes.DEFAULT_TYPE, mode: str):
    query = update.callback_query
    await query.edit_message_text(f"🎲 <b>Generating {mode.capitalize()}...</b>", parse_mode="HTML")
    
    prompt = f"Generate a creative and engaging {mode} question/task for a Truth or Dare game. Make it fun and suitable for a group. Return only the {mode} text."
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    
    kb = [
        [InlineKeyboardButton("🔄 Roll Again", callback_data=f"tod_{mode}"),
         InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    await query.edit_message_text(f"🎲 <b>{mode.capitalize()}:</b>\n\n{html.escape(reply)}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user: return
    ud = context.user_data
    txt = msg.text or ""

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back")]])

    if await check_permission(update, context):
        if ud.pop(AWAIT_GEMINI, False):
            m = await msg.reply_text("🧠 <b>Analyzing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_gemini3(c, txt)
            await m.edit_text(f"💎 <b>Gemini:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_DEEPSEEK, False):
            m = await msg.reply_text("🚀 <b>Searching...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_deepseek(c, txt)
            await m.edit_text(f"🔥 <b>DeepSeek:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_FLIRT, False):
            m = await msg.reply_text("💖 <b>Thinking...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_flirt(c, txt)
            await m.edit_text(f"✨ <b>Flirt AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_CODE, False):
            m = await msg.reply_text("👨‍💻 <b>Coding...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_code(c, txt)
            await m.edit_text(f"💻 <b>Code AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_INSTA, False): await do_insta_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_USERINFO, False): await do_user_info_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FF, False): await do_ff_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FFGUILD, False): await do_ff_guild_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_DL, False): await download_media(update, context, txt.strip()); return
        elif ud.pop(AWAIT_QRGEN, False): await cmd_qrgen(update, context); return
        elif ud.pop(AWAIT_SHORTEN, False): await do_url_shorten(update, context, txt.strip()); return
    
    if msg.chat.type == "private": 
        await forward_or_copy(update, context)

    # Keywords & Forwards
    txt_to_check = (msg.text or msg.caption or "").strip()
    if txt_to_check:
        low = txt_to_check.lower()
        for k in KEYWORDS:
            if k.lower() in low:
                user = msg.from_user
                chat_title = msg.chat.title or "Private Chat"
                from_info = f"{html.escape(user.full_name)} (@{user.username})" if user.username else html.escape(user.full_name)
                alert_text = (
                    f"🚨 <b>Keyword Mention Detected!</b>\n\n"
                    f"<b>Keyword:</b> <code>{k}</code>\n"
                    f"<b>From:</b> {from_info}\n"
                    f"<b>Group:</b> {html.escape(chat_title)}\n"
                    f"<b>Message:</b> {html.escape(txt_to_check[:1024])}"
                )
                try:
                    await context.bot.send_message(OWNER_ID, alert_text, parse_mode="HTML")
                except: pass
                break
    
    # Perfect Tracking Logic
    async def safe_track(target_id):
        try:
            await msg.forward(target_id)
        except Exception:
            try:
                await msg.copy(target_id)
            except: pass

    if msg.from_user.id == TRACKED_USER1_ID: await safe_track(FORWARD_USER1_GROUP_ID)
    if msg.from_user.id == TRACKED_USER2_ID: await safe_track(FORWARD_USER2_GROUP_ID)
    if msg.chat.id == SOURCE_GROUP_ID: await safe_track(DESTINATION_GROUP_ID)

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat
    if chat.type in ["group", "supergroup"]:
        gs = read_json("groups.json", [])
        if gs and not isinstance(gs[0], dict):
            gs = [{"id": gid, "title": "Unknown"} for gid in gs]
            
        if not any(g['id'] == chat.id for g in gs):
            new_group = {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            gs.append(new_group)
            write_json("groups.json", gs)


async def broadcast_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]), text=" ".join(context.args[1:]))
        await update.message.reply_text("✅ Sent")
        update_stats(sent_users=1)
    except:
        await update.message.reply_text("❌ Failed")
        update_stats(failed_users=1)

async def group_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /ban [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> banned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /unban [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> unbanned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /mute [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 User <code>{user_id}</code> muted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /unmute [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True))
        await update.message.reply_text(f"🔊 User <code>{user_id}</code> unmuted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /kick [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.message.reply_text(f"👞 User <code>{user_id}</code> kicked from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def broadcastall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or not context.args: return
    gs = read_json("groups.json", []); s = f = 0
    t = " ".join(context.args)
    for g in gs:
        gid = g.get('id') if isinstance(g, dict) else g
        try:
            await context.bot.send_message(chat_id=gid, text=t)
            s += 1
        except:
            f += 1
    await update.message.reply_text(f"✅ {s} | ❌ {f}")
    update_stats(sent_groups=s, failed_groups=f)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]), text=" ".join(context.args[1:]))
        STATS["broadcasts"] += 1
        await update.message.reply_text("✅ Sent to group")
        update_stats(sent_groups=1)
    except:
        await update.message.reply_text("❌ Failed")
        update_stats(failed_groups=1)


async def broadcast_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    msg = update.message
    photo = None
    if msg.reply_to_message and (msg.reply_to_message.photo or msg.reply_to_message.document):
        photo = msg.reply_to_message.photo[-1].file_id if msg.reply_to_message.photo else msg.reply_to_message.document.file_id
        cap = " ".join(context.args) if context.args else (msg.reply_to_message.caption or "")
    elif msg.photo:
        photo = msg.photo[-1].file_id
        cap = msg.caption or ""
    else:
        await msg.reply_text("💡 Usage: Send/Reply to photo with /broadcast_media")
        return
    gs = read_json("groups.json", []); s = f = 0
    for g in gs:
        gid = g.get('id') if isinstance(g, dict) else g
        try:
            await context.bot.send_photo(chat_id=gid, photo=photo, caption=cap, parse_mode="HTML")
            s += 1
        except:
            f += 1
    await msg.reply_text(f"🖼️ Media Blast: ✅ {s} | ❌ {f}")
    update_stats(sent_groups=s, failed_groups=f)

# ================= Background Cleanup =================
async def auto_cleanup_task():
    """Wipes the downloads folder every 10 minutes to save space."""
    while True:
        try:
            if os.path.exists("downloads"):
                for f in os.listdir("downloads"):
                    path = os.path.join("downloads", f)
                    try:
                        if os.path.isfile(path): os.remove(path)
                        elif os.path.isdir(path): shutil.rmtree(path)
                    except: pass
            logger.info("Auto-cleanup: Downloads folder cleared.")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(600) # 10 minutes

# ================= Run =================
# Global application object for access from main.py
app = None

async def start_bot():
    global app
    if not BOT_TOKEN: return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("commands", cmd_commands))
    app.add_handler(CommandHandler("help", cmd_help))
    
    async def handle_dl_cmd(u, c):
        if not is_owner(u.effective_user.id):
            await u.message.reply_text("🔒 <b>Private Tool:</b> Only Shawon can use the downloader.")
            return
        clear_states(c.user_data)
        if c.args: await download_media(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /dl <url>")
    
    async def handle_insta_cmd(u, c):
        if not is_owner(u.effective_user.id): return
        clear_states(c.user_data)
        if c.args: await do_insta_fetch_by_text(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /insta <username>")

    async def handle_ff_cmd(u, c):
        if not is_owner(u.effective_user.id): return
        clear_states(c.user_data)
        if c.args: await do_ff_fetch_by_text(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /ff <uid>")

    async def handle_userinfo_cmd(u, c):
        if not is_owner(u.effective_user.id): return
        clear_states(c.user_data)
        query = c.args[0] if c.args else None
        await do_user_info_fetch(u, c, query)

    app.add_handler(CommandHandler("insta", handle_insta_cmd))
    app.add_handler(CommandHandler("userinfo", handle_userinfo_cmd))
    app.add_handler(CommandHandler("id", handle_userinfo_cmd))
    app.add_handler(CommandHandler("ff", handle_ff_cmd))
    app.add_handler(CommandHandler("dl", handle_dl_cmd))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("commands", cmd_commands))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("gemini", cmd_gemini))
    app.add_handler(CommandHandler("deepseek", cmd_deepseek))
    app.add_handler(CommandHandler("flirt", cmd_flirt))
    app.add_handler(CommandHandler("code", cmd_code))
    app.add_handler(CommandHandler("ai", cmd_ai_combined))
    app.add_handler(CommandHandler("qrgen", cmd_qrgen))
    app.add_handler(CommandHandler("qrread", cmd_qrread))
    app.add_handler(CommandHandler("shorten", cmd_shorten))
    app.add_handler(CommandHandler("tod", cmd_truthordare))
    app.add_handler(CommandHandler("ffguild", lambda u, c: do_ff_guild_fetch(u, c, c.args[0]) if c.args else u.message.reply_text("💡 Usage: /ffguild <id>")))
    app.add_handler(CommandHandler("gban", cmd_gban))
    app.add_handler(CommandHandler("ungban", cmd_ungban))
    app.add_handler(CommandHandler("toggle_access", cmd_toggle_access))
    app.add_handler(CommandHandler("broadcastall", broadcastall))
    app.add_handler(CommandHandler("broadcastuser", broadcast_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("broadcast_media", broadcast_media))
    app.add_handler(CommandHandler("ban", group_ban))
    app.add_handler(CommandHandler("unban", group_unban))
    app.add_handler(CommandHandler("mute", group_mute))
    app.add_handler(CommandHandler("unmute", group_unmute))
    app.add_handler(CommandHandler("kick", group_kick))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(track_group, ChatMemberHandler.MY_CHAT_MEMBER))
    
    logger.info("Hinata Initialized")
    
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        logger.info("Hinata Live and Polling")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        STATS["status"] = "offline"
        if "rejected by the server" in str(e).lower() or "unauthorized" in str(e).lower():
            logger.error("CRITICAL: Your Telegram Bot Token is INVALID. Please check @BotFather.")

    # Start cleanup task (runs regardless of bot connection)
    asyncio.create_task(auto_cleanup_task())



async def stop_bot():
    global app
    if app:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
    loop.run_forever()

