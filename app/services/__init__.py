from flask import current_app


def get_services():
    """Return the service container created by create_app."""
    return current_app.extensions["sms"]
