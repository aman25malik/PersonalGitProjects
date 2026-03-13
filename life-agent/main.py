import logging
from database import init_db
from bot import create_bot_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting Life Agent bot...")
    app = create_bot_app()
    app.run_polling()


if __name__ == "__main__":
    main()
