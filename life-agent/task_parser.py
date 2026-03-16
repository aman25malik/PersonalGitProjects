import json
import anthropic
from datetime import date
from config import ANTHROPIC_API_KEY, USER_CONTEXT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PARSE_SYSTEM_PROMPT = f"""{USER_CONTEXT}

Today's date is: {{today}}

Your job: parse the user's message and extract structured task data.

IMPORTANT: You must respond with ONLY valid JSON, no other text. Use this exact format:
{{{{
  "title": "concise task/reminder title",
  "category": "Fitness|Health|Personal|Work|Creative|Social|Someday",
  "due_date": "YYYY-MM-DD or null if no date mentioned",
  "due_time": "HH:MM or null if no time mentioned",
  "priority": "high|medium|low",
  "item_type": "task|reminder|event|note",
  "reply": "friendly confirmation message, start with Got it ✅ then category emoji and category name, then dash, then the task title and due info"
}}}}

Rules:
- Convert relative dates: "tomorrow" = tomorrow's actual date, "Friday" = next Friday, "next week" = next Monday, etc.
- Priority: "high" if urgent language (ASAP, urgent, important, deadline), "low" if someday/vague/no date, "medium" otherwise
- item_type: "reminder" if they say remind me, "event" if it's a meeting/appointment/shoot, "note" if just logging info, "task" otherwise
- Category emoji mapping: Fitness=🏃, Health=🥗, Personal=🏠, Work=💼, Creative=📸, Social=👥, Someday=🗓️
- Keep the reply concise. Format: "Got it ✅ [emoji] [Category] — [title], [date/time info if any]"
- For someday items add: "I'll resurface this if no action taken."
"""

QUERY_SYSTEM_PROMPT = f"""{USER_CONTEXT}

You are determining what kind of query the user is asking. Respond with ONLY valid JSON:
{{{{
  "query_type": "today|tomorrow|this_week|category|overdue|all",
  "category": "the category name if query_type is category, otherwise null"
}}}}

Category names: Fitness, Health, Personal, Work, Creative, Social, Someday
- "what do I have today" / "today's tasks" → today
- "what's tomorrow" → tomorrow
- "what's this week" / "weekly view" → this_week
- "show my work tasks" / "work items" → category with category="Work"
- "show my creative ideas" → category with category="Creative"
- "what's overdue" / "overdue tasks" → overdue
- "show everything" / "all tasks" → all
"""


def parse_message(text):
    today = date.today().isoformat()
    prompt = PARSE_SYSTEM_PROMPT.replace("{today}", today)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=prompt,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            return raw, "Uncategorized", None

    return (
        data.get("reply", raw),
        data.get("category", "Uncategorized"),
        data,
    )


def parse_query(text):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        system=QUERY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            return None
    return data
