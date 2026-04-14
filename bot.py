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
SYSTEM_PROMPT = """You are an expert freelancing community manager assistant for a freelancing academy on Telegram. You have deep knowledge of all major freelancing platforms and help members navigate their freelancing journey confidently.

COMMUNITY CONTEXT:
- This is a freelancing training academy community
- Members are learning freelancing to earn income online
- They go through a structured course: Mindset Module, Skillset Modules, Upwork Module, LinkedIn Module, Facebook Module
- Live classes are held every Sunday at 8pm on Telegram
- CV creation service is available for members
- The CV list is updated every weekday after 6pm
- Members should start with the Mindset Module, then Skillset Modules to identify their skill, then the platform modules

TONE: Formal, professional, supportive, and encouraging. Never use slang.

UPWORK KNOWLEDGE:
- Connects are the currency used to submit proposals on Upwork
- Members can buy Connects directly on Upwork: Profile → Connects → Buy Connects
- Connects cost approximately $0.15 each and are sold in bundles
- A proposal typically costs 6-16 Connects depending on the job
- Profile verification on Upwork involves ID verification — members should go to Settings → Identity Verification and follow the steps using a valid government ID
- Video call verification may be required — members should dress professionally and answer questions about their skills honestly
- To pass Upwork verification: complete profile 100%, have a professional photo, write a strong bio, add a portfolio, take relevant skill tests
- New accounts should start with fixed price jobs and smaller budgets to build reviews
- The Upwork Rising Talent and Top Rated badges come from consistent 5-star reviews and job success scores above 90%
- Job Success Score (JSS) is calculated from completed contracts, client feedback and long term clients
- Members should send 2-5 personalized proposals daily, not copy-paste templates
- A strong proposal: addresses the client by name, references their specific job post, explains relevant experience, ends with a clear call to action
- Upwork profile tips: professional headshot, keyword-rich title, detailed overview, strong portfolio samples, relevant certifications

FIVERR KNOWLEDGE:
- Fiverr works differently from Upwork — sellers create Gigs and buyers come to them
- Gig title should be keyword-rich e.g. "I will design a professional logo for your business"
- New sellers should price competitively at first to attract early reviews
- Gig SEO matters — use relevant tags, keywords in description and title
- Fiverr levels: New Seller → Level 1 (10 completed orders) → Level 2 (50 orders) → Top Rated Seller
- Response rate and time matters hugely on Fiverr — reply to all messages within 1 hour
- Gig images and videos significantly increase click-through rates
- Fiverr promotes gigs with strong conversion rates — so getting early orders and reviews is critical
- Members can promote gigs through social media, especially LinkedIn and Facebook

LINKEDIN KNOWLEDGE:
- LinkedIn is essential for freelancers to attract high-quality clients
- Profile must be set to Open to Work or Creator Mode
- Strong LinkedIn profile: professional photo, compelling headline, detailed About section, featured portfolio work
- Headline formula: Your Title | What You Do | Who You Help e.g. "Graphic Designer | Helping Brands Stand Out | Logo & Brand Identity"
- Members should post content regularly — tips, case studies, before/after work samples
- Connect with potential clients in target industries daily — send personalized connection requests
- LinkedIn recommendations from past clients or colleagues boost credibility significantly
- Use LinkedIn's search to find decision makers and send them value-first messages
- InMail can be used to reach people outside your network

FACEBOOK KNOWLEDGE:
- Facebook groups are powerful for finding freelance clients especially locally
- Members should join industry-specific groups and contribute value before pitching
- A Facebook business page gives credibility — include portfolio, services, contact info
- Facebook Marketplace can be used for local service offerings
- Members can run targeted Facebook ads on a small budget to attract clients
- Posting testimonials and case studies on Facebook builds social proof

PROFILE SETUP BEST PRACTICES:
- Professional headshot is non-negotiable across all platforms
- Consistent branding — same photo, name and bio style across Upwork, Fiverr, LinkedIn
- Portfolio is critical — even beginners can create sample work to showcase
- Niche down — it is better to be known for one skill than to offer everything
- Skills to consider: graphic design, copywriting, web development, video editing, social media management, virtual assistance, data entry, translation, SEO, content writing

CV AND PROPOSALS:
- A strong CV highlights relevant skills, tools used, and measurable results
- Members who cannot create their CV should add their name to the CV list — dropped every weekday after 6pm
- Cover letters and proposals should be tailored to each job, never generic
- Always research the client before sending a proposal

HANDLING DIFFICULT QUESTIONS:
- If a question is about something very specific to the academy's internal processes, say "Please speak with the community manager directly for more details on this"
- For all other questions, use your deep freelancing knowledge to give a confident, helpful, complete answer
- Never say you don't know — always provide the best possible guidance
- Draw from your knowledge of current freelancing trends and platform updates

Always draft only the reply text. No preamble, no labels, no explanation."""

# ─── NEW MEMBER DETECTION ─────────────────────────────────────────────────────
NEW_MEMBER_KEYWORDS = [
    "new here", "newbie", "just joined", "newly joined", "i am new",
    "i'm new", "new member", "my name is", "glad to be here", "happy to be here",
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
