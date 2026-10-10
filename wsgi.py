"""WSGI entry point used by Gunicorn: gunicorn wsgi:app"""
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402  (must follow load_dotenv)

app = create_app()
