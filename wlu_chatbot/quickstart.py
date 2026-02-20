import os
from wlu_chatbot import create_app
from wlu_chatbot.db.cli import main as db_cli


def main():
    app = create_app()
    
    with app.app_context():
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