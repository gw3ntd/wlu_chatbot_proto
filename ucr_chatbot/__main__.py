"""Contains a Flask application for a tutoring chatbot,
including a public web interface and an API for interacting with the chatbot.

There are some utility functions for managing the ucr_chatbot application.

Available commands:
- db: Manage the database
- quickstart: Initialize and run the application with mock data
"""

import sys
from ucr_chatbot import create_app
from ucr_chatbot.quickstart import main as quickstart_main

if len(sys.argv) == 1:
    print(__doc__)
    exit(0)

match sys.argv[1]:
    case "help":
        print(__doc__)
    case "db":
        import ucr_chatbot.db.cli

        with create_app().app_context():
            ucr_chatbot.db.cli.main(sys.argv[2:])
    case "quickstart":
        with create_app().app_context():
            quickstart_main()
    case _:
        print("Unknown command", file=sys.stderr)
        exit(1)
