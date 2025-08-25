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
