import logging
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from database import init_db
from bot import create_bot_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"life-agent is running")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server listening on port %d", port)
    server.serve_forever()


def main():
    logger.info("Initializing database...")
    init_db()

    # Render requires a web server on $PORT to keep the service alive
    threading.Thread(target=start_health_server, daemon=True).start()

    logger.info("Starting Life Agent bot...")
    app = create_bot_app()
    app.run_polling()


if __name__ == "__main__":
    main()
