"""Initialize and runs the WLU Chatbot application.

This script initializes the database and launches the application with mock data.
"""

import os
from wlu_chatbot.db.cli import main as db_cli


def main():
    """Initialize and run the WLU Chatbot application with mock data."""
    db_args = ["mock"]
    db_cli(db_args)

    gunicorn_command = "uv run gunicorn 'wlu_chatbot:create_app()' --bind 0.0.0.0:5000"
    print(f"Starting Gunicorn: {gunicorn_command}")
    try:
        os.execvp(
            "uv",
            [
                "uv",
                "run",
                "gunicorn",
                "wlu_chatbot:create_app()",
                "--bind",
                "0.0.0.0:5000",
            ],
        )
    except FileNotFoundError:
        print("Error: 'uv' command not found. Ensure 'uv' is in your PATH.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while starting Gunicorn: {e}")
        exit(1)


if __name__ == "__main__":
    main()
