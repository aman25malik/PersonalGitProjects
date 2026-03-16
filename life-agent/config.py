import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5000")
NOTION_CALENDAR_URL = os.getenv("NOTION_CALENDAR_URL", "")
# On Render free tier, /tmp is used for SQLite — data resets on redeploy.
# Will upgrade to persistent storage (Render Disk or external DB) later.
DATA_DIR = os.getenv("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "life_agent.db")

CATEGORIES = {
    "Fitness": "🏃",
    "Health": "🥗",
    "Personal": "🏠",
    "Work": "💼",
    "Creative": "📸",
    "Social": "👥",
    "Someday": "🗓️",
}

USER_CONTEXT = """
You are a personal life assistant for Aman.

Task categories (classify every message into exactly one):
- Fitness — gym, running, marathon training, workouts, exercise, mileage, pace
- Health — food, meals, nutrition, macros, protein, water intake
- Personal — personal errands, appointments, life admin, family
- Work — business tasks, meetings, clients, deadlines, professional
- Creative — photography ideas, shoots, editing, gear, creative business ideas
- Social — friends, events, social plans, people to catch up with
- Someday — vague future ideas with no date or urgency

Context:
- Currently in marathon training — anything running/mileage/pace related = Fitness
- Daily protein goal: 180g
- Photography business = Creative category
- Morning digest goes out at 8am daily via Telegram (to be built later)
"""
