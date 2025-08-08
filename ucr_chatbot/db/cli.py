"""
Database Initialization Script

This script allows the user to initialize the database tables, optionally clearing all existing data.
It also allows the user to add mock data to the database for demonstration purposes.

Usage (assuming running from project root):
  uv run ucr_chatbot/db/cli.py initialize [--force]
  uv run ucr_chatbot/db/cli.py mock


This file contains the following functions:

    * initialize(force: bool) - Creates all database tables if they have not already been created.
      If --force is passed, deletes all tables and then creates them.

    * mock() - Adds mock courses and users with different roles to the database.
      Copy email and password info output when users are created for later use.
      Mock users:
      - test001@ucr.edu (instructor access)
      - test002@ucr.edu (student access)
      - test003@ucr.edu (assistant access)

    * main() - Initializes the argument parser, parses the CLI arguments,
      and calls the corresponding functions.

"""

import argparse
from sqlalchemy import inspect
from ucr_chatbot.db.models import *
# try:
#     from ucr_chatbot.db.models import *
# except ModuleNotFoundError:
#     from models import *

inspector = inspect(engine)


def initialize(force: bool):
    """Creates all tables in the database if they do not already exist.
    If --force is also passed, all tables and the uploads folder will
    be deleted first and then the tables will be re-created.
    :param force: If True, clears existing tables and creates empty tables.
    """
    if not inspector.has_table("Users"):
        base.metadata.create_all(engine)
        print("Database initialized.")
    elif force:
        base.metadata.drop_all(engine)
        delete_uploads_folder()
        base.metadata.create_all(engine)
        print("Database cleared and initialized.")
    else:
        print("Database already initialized.")


def mock():
    """Adds mock courses and users with varying roles to the database.
    Only adds mock data if the Users and Courses tables are empty.
    """
    if not inspector.has_table("Users"):
        base.metadata.create_all(engine)

    with Session(engine) as session:
        courses_empty = not session.query(session.query(Courses).exists()).scalar()
        users_empty = not session.query(session.query(Users).exists()).scalar()

        if courses_empty and users_empty:
            add_new_course("CS010C")  # course ID 1
            add_new_course("CS061")  # course ID 2
            add_new_course("CS0111")  # course ID 3
            add_new_user("test001@ucr.edu", "fname1", "lname1")
            add_new_user("test002@ucr.edu", "fname2", "lname2")
            add_new_user("test003@ucr.edu", "fname3", "lname3")
            add_user_to_course("test001@ucr.edu", "fname1", "lname1", 1, "instructor")
            add_user_to_course("test001@ucr.edu", "fname1", "lname1", 2, "instructor")
            add_user_to_course("test001@ucr.edu", "fname1", "lname1", 3, "instructor")
            add_user_to_course("test002@ucr.edu", "fname2", "lname2", 1, "student")
            add_user_to_course("test002@ucr.edu", "fname2", "lname2", 2, "student")
            add_user_to_course("test002@ucr.edu", "fname2", "lname2", 3, "student")
            add_user_to_course("test003@ucr.edu", "fname3", "lname3", 1, "assistant")
            add_user_to_course("test003@ucr.edu", "fname3", "lname3", 2, "assistant")
            add_user_to_course("test003@ucr.edu", "fname3", "lname3", 3, "assistant")
            print("Mock data added to database.")
        else:
            print("Mock data not added, database already has data.")


def main(arg_list: list[str] | None = None):
    """Initializes the argument parser and gets the arguments passed in through the CLI

    Usage:
      uv run ucr_chatbot/db/cli.py initialize [--force]
      uv run ucr_chatbot/db/cli.py mock
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        prog="uv run ucr_chatbot/db/cli.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "action",
        type=str,
        choices=["initialize", "mock"],
        help="use 'initialize' to set up database tables or 'mock' to add mock data",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="use with 'initialize' to forcefully clear and recreate all tables",
    )

    args = parser.parse_args(arg_list)

    if args.action == "initialize":
        initialize(args.force)
    elif args.action == "mock":
        mock()


if __name__ == "__main__":
    main()
