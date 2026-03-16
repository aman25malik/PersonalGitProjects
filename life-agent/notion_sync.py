import logging
import requests
from config import NOTION_API_KEY, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

CATEGORY_COLORS = {
    "Fitness": "blue",
    "Health": "green",
    "Personal": "purple",
    "Work": "orange",
    "Creative": "pink",
    "Social": "yellow",
    "Someday": "gray",
}


def is_configured():
    return bool(NOTION_API_KEY and NOTION_DATABASE_ID)


def sync_task_to_notion(title, category, due_date, status, priority):
    if not is_configured():
        return None

    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Category": {"select": {"name": category, "color": CATEGORY_COLORS.get(category, "default")}},
        "Status": {"select": {"name": status.capitalize()}},
        "Priority": {"select": {"name": priority.capitalize()}},
    }

    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}

    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
    }

    try:
        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
        resp.raise_for_status()
        page_id = resp.json()["id"]
        logger.info("Synced to Notion: %s (page %s)", title, page_id)
        return page_id
    except Exception as e:
        logger.error("Notion sync failed: %s", e)
        return None


def update_notion_status(page_id, new_status):
    if not is_configured() or not page_id:
        return False

    data = {
        "properties": {
            "Status": {"select": {"name": new_status.capitalize()}},
        }
    }

    try:
        resp = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS, json=data)
        resp.raise_for_status()
        logger.info("Updated Notion status: %s → %s", page_id, new_status)
        return True
    except Exception as e:
        logger.error("Notion update failed: %s", e)
        return False


def find_notion_page_by_title(title):
    """Search for a page by title in the database."""
    if not is_configured():
        return None

    data = {
        "filter": {
            "property": "Title",
            "title": {"contains": title},
        }
    }

    try:
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
            headers=HEADERS,
            json=data,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
    except Exception as e:
        logger.error("Notion search failed: %s", e)
    return None
