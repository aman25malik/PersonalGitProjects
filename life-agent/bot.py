import os
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from faster_whisper import WhisperModel
from config import TELEGRAM_BOT_TOKEN, WHISPER_MODEL_SIZE
from parser import parse_message
from database import save_message

logger = logging.getLogger(__name__)

whisper_model = None


def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        logger.info("Loading Whisper model (%s)...", WHISPER_MODEL_SIZE)
        whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return whisper_model


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
    await update.message.reply_text("Transcribing your voice message...")

    voice_file = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
        await voice_file.download_to_drive(tmp_path)

    try:
        model = get_whisper_model()
        segments, _ = model.transcribe(tmp_path)
        transcript = " ".join(segment.text for segment in segments).strip()
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
