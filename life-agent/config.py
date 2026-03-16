import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# On Render free tier, /tmp is used for SQLite — data resets on redeploy.
# Will upgrade to persistent storage (Render Disk or external DB) later.
DATA_DIR = os.getenv("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "life_agent.db")

USER_CONTEXT = """
You are a personal life assistant for Aman. Here is context about him:

Task categories (always classify into exactly one):
- Personal
- Work/Business
- Photography
- Finance
- Someday

Fitness context:
- Currently in marathon training — logs runs, mileage, and weekly training load
- Daily protein goal: 180g

Behavior:
- When Aman gives you new context about himself naturally in conversation, acknowledge it and adapt.
- Morning digest goes out at 8am daily via Telegram (to be built later).
- All tasks and data are stored locally in SQLite for now; Notion sync coming later.
"""
