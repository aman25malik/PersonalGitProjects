import anthropic
from config import ANTHROPIC_API_KEY, USER_CONTEXT


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""{USER_CONTEXT}

Your job: parse the user's message and respond with a smart, concise confirmation.
Always include the category in your response like: "Category: <category>"

Examples:
- "remind me to call John tomorrow" → "Got it — I'll remind you to call John tomorrow. Category: Personal"
- "log 8 mile run today, felt good" → "Logged: 8-mile run today, feeling good. Category: Personal"
- "need to invoice client X for $2000" → "Noted — invoice client X for $2,000. Category: Finance"
- "someday I want to visit Iceland for landscape photography" → "Added to your someday list — Iceland landscape photography trip. Category: Someday"

Keep responses brief, friendly, and actionable. Don't use emojis.
"""


def parse_message(text):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    reply = response.content[0].text

    category = "Uncategorized"
    for line in reply.split("\n"):
        if "Category:" in line:
            category = line.split("Category:")[-1].strip()
            break

    return reply, category
