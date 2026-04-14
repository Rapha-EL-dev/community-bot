"""
Freelancing Community Manager Bot - Path 3
============================================
- Bot sits silently in the group (never posts anything)
- Reads every message automatically
- Drafts a reply and sends it to you privately
- You copy the draft and paste it in the group yourself
- Auto-generates welcome message for new member intros
- Looks 100% like you because YOU are sending everything
"""

import os
import logging
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN        = os.getenv("BOT_TOKEN")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID"))
GROUP_CHAT_ID    = int(os.getenv("GROUP_CHAT_ID"))
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# ─── WELCOME MESSAGE ──────────────────────────────────────────────────────────
WELCOME_MESSAGE = """Hello, you're welcome! 🎉

Access link to your course has been sent to you on WhatsApp alongside the link you used in joining this group. You're expected to start going through your course, identify the skill you want to do, set up your profiles, start sending out proposals.

If you're here to sell the skill, then go through your course lessons to identify the skill you can do great during interviews, set up your profiles on it by going through LinkedIn, Facebook and Upwork modules, send out proposals to get you jobs and hand it over to the academy.

Your CV will be created for you should you not be able to handle it.

So, you're expected to include your name on the CV list only when you've identified your skill by going through your course. The list gets dropped every weekday after 6pm so no cause for panic!!!

When you access your course, start with the MINDSET MODULE, skip the UPWORK, LINKEDIN AND FACEBOOK MODULE, go through the skillset modules to identify the skill you want to do before going through the UPWORK, LINKEDIN AND FACEBOOK modules to set up your profiles and major on it.

Live classes are held every Sunday by 8pm here on Telegram to monitor your progress."""

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a community manager assistant for a freelancing academy community on Telegram.

Your role is to draft formal, helpful, and concise replies to member questions.

Community context:
- This is a freelancing training community/academy
- Members are learning freelancing skills to earn income online
- Common topics: Upwork, buying connects, account verification, profile setup, proposals, LinkedIn, Facebook, CV creation, skill selection
- Members go through a structured course: Mindset Module, Upwork Module, LinkedIn Module, Facebook Module, Skillset Modules
- Live classes are held every Sunday at 8pm on Telegram
- CV creation service is available for members
- The CV list is updated every weekday after 6pm

Tone: Formal, supportive, encouraging, professional.
- Keep replies concise but complete
- Direct members to their course first for learning questions
- For Upwork connects: advise buying from Upwork platform directly
- If unsure, say "Please reach out to the admin directly for more details on this."
- Never use slang
- Draft only the reply text. No preamble, no labels, no explanation."""

# ─── NEW MEMBER DETECTION ─────────────────────────────────────────────────────
NEW_MEMBER_KEYWORDS = [
    "new here", "newbie", "just joined", "newly joined", "i am new",
    "i'm new", "new member", "introduce myself", "my name is",
    "hello everyone", "hi everyone", "good morning everyone",
    "good evening everyone", "glad to be here", "happy to be here",
    "just registered", "just signed up", "new to this group", "newly added"
]

def is_new_member_intro(text: str) -> bool:
    return any(kw in text.lower() for kw in NEW_MEMBER_KEYWORDS)

# ─── AI DRAFT ─────────────────────────────────────────────────────────────────
def generate_ai_draft(message_text: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message_text}
            ],
            max_tokens=400,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "Thank you for your message. I will get back to you shortly."

# ─── /START COMMAND ───────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != YOUR_TELEGRAM_ID:
        return
    await update.message.reply_text(
        "✅ Bot is active!\n\n"
        "I am silently watching your group.\n"
        "Every message will be drafted and sent here for you to copy and paste."
    )

# ─── GROUP MESSAGE HANDLER ────────────────────────────────────────────────────
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    # Only watch the configured group
    if message.chat_id != GROUP_CHAT_ID:
        return

    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        return

    text = message.text
    sender = message.from_user
    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "A member"

    # ── New member intro → send welcome draft ──
    if is_new_member_intro(text):
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=(
                f"👋 New member intro from {sender_name}\n\n"
                f"Their message:\n{text}\n\n"
                f"─────────────────────\n"
                f"Copy and paste this welcome message:\n\n"
                f"{WELCOME_MESSAGE}"
            )
        )
        return

    # ── All other messages → draft reply ──
    draft = generate_ai_draft(text)

    keyboard = [[
        InlineKeyboardButton("🔄 Regenerate", callback_data=f"regen|{text[:200]}"),
    ]]

    await context.bot.send_message(
        chat_id=YOUR_TELEGRAM_ID,
        text=(
            f"📩 Message from {sender_name}:\n"
            f"{text}\n\n"
            f"─────────────────────\n"
            f"📋 Copy and paste this reply:\n\n"
            f"{draft}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── REGENERATE CALLBACK ──────────────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Regenerating...")

    if query.data.startswith("regen|"):
        original_text = query.data[6:]
        draft = generate_ai_draft(original_text)

        keyboard = [[
            InlineKeyboardButton("🔄 Regenerate", callback_data=f"regen|{original_text[:200]}"),
        ]]

        await query.edit_message_text(
            f"📋 New draft — copy and paste this reply:\n\n"
            f"{draft}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(
        filters.Chat(GROUP_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
        handle_group_message
    ))
    logger.info("Bot is running...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
