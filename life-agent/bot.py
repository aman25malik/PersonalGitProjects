import os
import re
import tempfile
import logging
from datetime import date, timedelta
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, CATEGORIES
from parser import parse_message, parse_query
from database import (
    save_message, save_task, complete_task, drop_task,
    get_tasks_by_date, get_tasks_by_date_range, get_tasks_by_category,
    get_overdue_tasks, get_all_pending_tasks, recategorize_last_task,
)
from gym import parse_workout, parse_gym_query, save_workout, format_workout_response, handle_gym_query
from nutrition import parse_food, parse_nutrition_query, save_food_entry, get_daily_total, format_food_response, handle_nutrition_query
from notion_sync import sync_task_to_notion, update_notion_status, find_notion_page_by_title, is_configured as notion_configured
from config import DASHBOARD_URL, NOTION_CALENDAR_URL

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

QUERY_PATTERNS = re.compile(
    r"^(what do i have|what's|whats|show|list|my tasks|my items|everything|overdue|this week|today|tomorrow)",
    re.IGNORECASE,
)
GYM_LOG_PATTERNS = re.compile(
    r"(chest.*(back|press|fly)|leg\s*(day|workout|press)|shoulder|arms?\s*(day|workout)|squat|deadlift|bench\s*\d|workout.*(?:sets?|reps?|x\d)|\d+\s*(?:lbs?|pounds?)\b.*sets?|(?:sets?\s*of\s*\d)|(?:lat\s*pull)|(?:incline.*press)|(?:rows?\s*(?:for|at)))",
    re.IGNORECASE,
)
GYM_QUERY_PATTERNS = re.compile(
    r"(what should i (do|train|lift)|bench pr|squat pr|deadlift pr|pr$|prs$|how many.*(lift|gym|train)|am i hitting|last.*(chest|leg|shoulder|arm|back)\s*day|show.*progress|my prs|all prs|what did i do last)",
    re.IGNORECASE,
)
NUTRITION_LOG_PATTERNS = re.compile(
    r"(had |ate |eaten |breakfast|lunch|dinner|snack|meal|protein shake|eggs?|chicken|steak|salmon|yogurt|oatmeal|rice and|for breakfast|for lunch|for dinner)",
    re.IGNORECASE,
)
NUTRITION_QUERY_PATTERNS = re.compile(
    r"(how much protein|protein today|what did i eat|food log|meals today|protein this week|weekly protein|protein average|how.*(protein|nutrition).*week|average protein)",
    re.IGNORECASE,
)
DONE_PATTERN = re.compile(r"^(done|completed|finish|finished)\s+(.+)", re.IGNORECASE)
DROP_PATTERN = re.compile(r"^(drop|dismiss|cancel|skip)\s+(.+)", re.IGNORECASE)
FIX_PATTERN = re.compile(r"^(fix|recategorize|recategori[sz]e)\s+(.+)", re.IGNORECASE)

CATEGORY_NAMES = {k.lower(): k for k in CATEGORIES}


def parse_category_prefix(text):
    """Check if text starts with 'category: ...' and return (category, remaining_text) or (None, text)."""
    match = re.match(r"^(\w+)\s*:\s*(.+)", text, re.DOTALL)
    if match:
        prefix = match.group(1).lower()
        if prefix in CATEGORY_NAMES:
            return CATEGORY_NAMES[prefix], match.group(2).strip()
    return None, text


def format_task_list(tasks, title):
    if not tasks:
        return f"{title}\n\nNo tasks found."

    today = date.today().isoformat()
    grouped = {}
    for t in tasks:
        cat = t["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(t)

    lines = [title, ""]
    for cat, items in grouped.items():
        emoji = CATEGORIES.get(cat, "📌")
        lines.append(f"{emoji} {cat}")
        for t in items:
            priority_flag = "🔴 " if t["priority"] == "high" else ""
            overdue_flag = "⚠️ " if t["due_date"] and t["due_date"] < today else ""
            time_str = f" at {t['due_time']}" if t["due_time"] else ""
            date_str = f" ({t['due_date']}{time_str})" if t["due_date"] else ""
            lines.append(f"  {overdue_flag}{priority_flag}• {t['title']}{date_str}")
        lines.append("")

    return "\n".join(lines).strip()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Life Agent is running. Send me a text or voice message and I'll parse it for you.\n\n"
        "You can also ask:\n"
        "• \"what do I have today\"\n"
        "• \"what's this week\"\n"
        "• \"show my work tasks\"\n"
        "• \"what's overdue\"\n"
        "• \"show everything\"\n"
        "• \"done [task name]\" to complete\n"
        "• \"drop [task name]\" to dismiss"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    logger.info("Received text message: %s", text[:80])

    # Check for done/drop commands first
    done_match = DONE_PATTERN.match(text)
    if done_match:
        task_query = done_match.group(2).strip()
        title = complete_task(task_query, chat_id)
        if title:
            if notion_configured():
                page_id = find_notion_page_by_title(title)
                if page_id:
                    update_notion_status(page_id, "Done")
            await update.message.reply_text(f"✅ Marked complete — {title}")
        else:
            await update.message.reply_text(f"Couldn't find a pending task matching \"{task_query}\".")
        return

    drop_match = DROP_PATTERN.match(text)
    if drop_match:
        task_query = drop_match.group(2).strip()
        title = drop_task(task_query, chat_id)
        if title:
            await update.message.reply_text(f"🗑️ Dropped — {title}")
        else:
            await update.message.reply_text(f"Couldn't find a pending task matching \"{task_query}\".")
        return

    # Check for fix/recategorize command
    fix_match = FIX_PATTERN.match(text)
    if fix_match:
        new_cat_input = fix_match.group(2).strip().lower()
        if new_cat_input in CATEGORY_NAMES:
            new_cat = CATEGORY_NAMES[new_cat_input]
            emoji = CATEGORIES[new_cat]
            title, old_cat = recategorize_last_task(new_cat, chat_id)
            if title:
                old_emoji = CATEGORIES.get(old_cat, "📌")
                await update.message.reply_text(f"Fixed — {title}\n{old_emoji} {old_cat} → {emoji} {new_cat}")
            else:
                await update.message.reply_text("No recent task found to recategorize.")
        else:
            valid = ", ".join(CATEGORY_NAMES.values())
            await update.message.reply_text(f"Unknown category. Valid options: {valid}")
        return

    # Quick commands: dashboard, notion
    text_lower = text.lower().strip()
    if text_lower == "dashboard":
        await update.message.reply_text(f"📊 Your dashboard:\n{DASHBOARD_URL}")
        return
    if text_lower == "notion":
        if NOTION_CALENDAR_URL:
            await update.message.reply_text(f"🗓️ Your Notion calendar:\n{NOTION_CALENDAR_URL}")
        else:
            await update.message.reply_text("Notion calendar URL not configured yet.")
        return

    # Check if this is a nutrition query
    if NUTRITION_QUERY_PATTERNS.search(text):
        query_data = parse_nutrition_query(text)
        if query_data:
            result = handle_nutrition_query(query_data, chat_id)
            if result:
                await update.message.reply_text(result)
                return

    # Check if this is a food log
    if NUTRITION_LOG_PATTERNS.search(text) and not GYM_LOG_PATTERNS.search(text):
        data = parse_food(text)
        if data and data.get("foods"):
            total_protein = data.get("total_protein", 0)
            description = ", ".join(f["item"] for f in data["foods"])
            save_food_entry(description, total_protein, chat_id)
            daily_total = get_daily_total(date.today().isoformat(), chat_id)
            reply = format_food_response(data, daily_total)
            save_message("text", text, "Health", reply, chat_id)
            await update.message.reply_text(reply)
            return

    # Check if this is a gym query
    if GYM_QUERY_PATTERNS.search(text):
        query_data = parse_gym_query(text)
        if query_data:
            result = handle_gym_query(query_data, chat_id)
            if result:
                await update.message.reply_text(result)
                return

    # Check if this is a gym workout log
    if GYM_LOG_PATTERNS.search(text):
        data = parse_workout(text)
        if data and data.get("exercises"):
            workout_id, prs, is_baseline = save_workout(data, text, chat_id)
            reply = format_workout_response(data, prs, is_baseline)
            save_message("text", text, "Fitness", reply, chat_id)
            await update.message.reply_text(reply)
            return

    # Check if this is a query
    if QUERY_PATTERNS.match(text):
        await handle_query(update, text, chat_id)
        return

    # Check for category prefix override (e.g. "personal: send proposal to Sarah")
    forced_category, message_text = parse_category_prefix(text)

    # Regular task/message input
    reply, category, parsed_data = parse_message(message_text)
    save_message("text", text, category, reply, chat_id)

    if forced_category and parsed_data:
        parsed_data["category"] = forced_category
        category = forced_category
        emoji = CATEGORIES.get(forced_category, "📌")
        reply = re.sub(
            r"(🏃|🥗|🏠|💼|📸|👥|🗓️)\s*\w+",
            f"{emoji} {forced_category}",
            reply,
            count=1,
        )

    if parsed_data:
        save_task(
            title=parsed_data.get("title", message_text),
            category=parsed_data.get("category", category),
            due_date=parsed_data.get("due_date"),
            due_time=parsed_data.get("due_time"),
            priority=parsed_data.get("priority", "medium"),
            item_type=parsed_data.get("item_type", "task"),
            raw_input=text,
            chat_id=chat_id,
        )
        if notion_configured():
            sync_task_to_notion(
                parsed_data.get("title", message_text),
                parsed_data.get("category", category),
                parsed_data.get("due_date"),
                "pending",
                parsed_data.get("priority", "medium"),
            )

    await update.message.reply_text(reply)


async def handle_query(update: Update, text: str, chat_id: int):
    query_data = parse_query(text)
    if not query_data:
        await update.message.reply_text("Sorry, I didn't understand that query.")
        return

    query_type = query_data.get("query_type")
    today = date.today()

    if query_type == "today":
        tasks = get_tasks_by_date(today.isoformat(), chat_id)
        result = format_task_list(tasks, f"📅 Today — {today.strftime('%A, %B %d')}")

    elif query_type == "tomorrow":
        tomorrow = today + timedelta(days=1)
        tasks = get_tasks_by_date(tomorrow.isoformat(), chat_id)
        result = format_task_list(tasks, f"📅 Tomorrow — {tomorrow.strftime('%A, %B %d')}")

    elif query_type == "this_week":
        start = today
        end = today + timedelta(days=(6 - today.weekday()))
        tasks = get_tasks_by_date_range(start.isoformat(), end.isoformat(), chat_id)
        result = format_task_list(tasks, f"📅 This Week ({start.strftime('%b %d')} – {end.strftime('%b %d')})")

    elif query_type == "category":
        cat = query_data.get("category", "")
        tasks = get_tasks_by_category(cat, chat_id)
        emoji = CATEGORIES.get(cat, "📌")
        result = format_task_list(tasks, f"{emoji} {cat} Tasks")

    elif query_type == "overdue":
        tasks = get_overdue_tasks(chat_id)
        result = format_task_list(tasks, "⚠️ Overdue Tasks")

    elif query_type == "all":
        tasks = get_all_pending_tasks(chat_id)
        result = format_task_list(tasks, "📋 All Pending Tasks")

    else:
        result = "Sorry, I didn't understand that query."

    await update.message.reply_text(result)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    voice_file = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
        await voice_file.download_to_drive(tmp_path)

    try:
        with open(tmp_path, "rb") as audio:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
            )
        transcript = transcription.text.strip()
    finally:
        os.unlink(tmp_path)

    if not transcript:
        await update.message.reply_text("Sorry, I couldn't understand the audio.")
        return

    logger.info("Transcribed voice: %s", transcript[:80])

    # Check if voice is a nutrition query
    if NUTRITION_QUERY_PATTERNS.search(transcript):
        query_data = parse_nutrition_query(transcript)
        if query_data:
            result = handle_nutrition_query(query_data, chat_id)
            if result:
                await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{result}")
                return

    # Check if voice is a food log
    if NUTRITION_LOG_PATTERNS.search(transcript) and not GYM_LOG_PATTERNS.search(transcript):
        data = parse_food(transcript)
        if data and data.get("foods"):
            total_protein = data.get("total_protein", 0)
            description = ", ".join(f["item"] for f in data["foods"])
            save_food_entry(description, total_protein, chat_id)
            daily_total = get_daily_total(date.today().isoformat(), chat_id)
            reply = format_food_response(data, daily_total)
            save_message("voice", transcript, "Health", reply, chat_id)
            await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{reply}")
            return

    # Check if voice is a gym query
    if GYM_QUERY_PATTERNS.search(transcript):
        query_data = parse_gym_query(transcript)
        if query_data:
            result = handle_gym_query(query_data, chat_id)
            if result:
                await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{result}")
                return

    # Check if voice is a gym log
    if GYM_LOG_PATTERNS.search(transcript):
        data = parse_workout(transcript)
        if data and data.get("exercises"):
            workout_id, prs, is_baseline = save_workout(data, transcript, chat_id)
            reply = format_workout_response(data, prs, is_baseline)
            save_message("voice", transcript, "Fitness", reply, chat_id)
            await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{reply}")
            return

    # Check if voice is a query
    if QUERY_PATTERNS.match(transcript):
        await handle_query(update, transcript, chat_id)
        return

    reply, category, parsed_data = parse_message(transcript)
    save_message("voice", transcript, category, reply, chat_id)

    if parsed_data:
        save_task(
            title=parsed_data.get("title", transcript),
            category=parsed_data.get("category", category),
            due_date=parsed_data.get("due_date"),
            due_time=parsed_data.get("due_time"),
            priority=parsed_data.get("priority", "medium"),
            item_type=parsed_data.get("item_type", "task"),
            raw_input=transcript,
            chat_id=chat_id,
        )

    await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{reply}")


def create_bot_app():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    return app
