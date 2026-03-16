import os
import tempfile
import logging
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
from parser import parse_message
from database import save_message

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Life Agent is running. Send me a text or voice message and I'll parse it for you."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    logger.info("Received text message: %s", text[:80])

    reply, category = parse_message(text)
    save_message("text", text, category, reply, chat_id)
    await update.message.reply_text(reply)


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
    reply, category = parse_message(transcript)
    save_message("voice", transcript, category, reply, chat_id)
    await update.message.reply_text(f"[Transcribed]: {transcript}\n\n{reply}")


def create_bot_app():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    return app
