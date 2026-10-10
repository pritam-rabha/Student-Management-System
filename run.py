"""Local development entry point.

    python run.py

For production use Gunicorn with the wsgi module instead (see README.md).
The entry point is not named app.py because that would clash with the
app/ package.
"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402  (must follow load_dotenv)

application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("APP_ENV", "development").lower() == "development"
    application.run(host="0.0.0.0", port=port, debug=debug)
