"""Initialize and runs the UCR Chatbot application.

This script initializes the database and launches the application.
If the environment variable `MOCK_DB` is set, the database will be initialized with mock data.
"""

import subprocess
from pathlib import Path
import os


"""
Initializes the application by creating the 'vector' extension in the database,
installing dependencies, initializing the database, and then starting the Gunicorn web server.
"""

commands = [
    "uv pip install .",
    f"uv run {Path('ucr_chatbot/db')} {'mock' if os.getenv('MOCK_DB') in ['true', 'TRUE', 'True'] else 'initialize'}",
]

for command in commands:
    print(f"Executing: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Successfully executed: {command}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(e)
        exit(1)

gunicorn_command = "uv run gunicorn 'ucr_chatbot:create_app()' --bind 0.0.0.0:5000"
print(f"Starting Gunicorn: {gunicorn_command}")
try:
    os.execvp(
        "uv",
        ["uv", "run", "gunicorn", "ucr_chatbot:create_app()", "--bind", "0.0.0.0:5000"],
    )
except FileNotFoundError:
    print("Error: 'uv' command not found. Ensure 'uv' is in your PATH.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred while starting Gunicorn: {e}")
    exit(1)
