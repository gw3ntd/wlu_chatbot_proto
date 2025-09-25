"""A database management CLI tool for the UCR Chatbot.

This tool should be used to initialize a database, i.e. to create the necessary tables.
This tool may be used to create new users as needed.
"""

import argparse
import typing as t
from sqlalchemy import inspect, text
import sys

from ucr_chatbot.db.models import (
    get_engine,
    base,
    Course,
    User,
    add_new_course,
    add_new_user,
    add_user_to_course,
    Session,
    ParticipatesIn,
    Limit,
)


def main(arg_list: list[str] | None = None):
    """Executes the database management script."""
    parser = argparse.ArgumentParser(
        "db-manager",
        description=__doc__,
    )

    # Command options
    sub_parsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="specifies the action to be taken on the database.",
    )

    init_parser = sub_parsers.add_parser(
        "initialize",
        help="initialize the database tables if they are not already initialized.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="if set, forcefully clears all tables and recreates them, deleting all data.",
    )

    mock_parser = sub_parsers.add_parser(
        "mock",
        help="initialize all tables and adds mock data if the database is uninitialized.",
    )
    mock_parser.add_argument(
        "--force",
        action="store_true",
        help="if set, forcefully clears all tables and recreates them, deleting all data.",
    )

    create_parser = sub_parsers.add_parser(
        "create", help="create a new entity in the database."
    )
    for _ in range(1):
        ## Create options
        create_sub = create_parser.add_subparsers(
            dest="entity_type",
            help="the entity to be created.",
            required=True,
        )

        course_parser = create_sub.add_parser("course")
        course_parser.add_argument("course_name")

        user_parser = create_sub.add_parser("user")
        user_parser.add_argument("email")
        user_parser.add_argument("password")

        participates_in_parser = create_sub.add_parser("participates_in")
        participates_in_parser.add_argument("email")
        participates_in_parser.add_argument("course_id", type=int)
        participates_in_parser.add_argument(
            "role", choices=["instructor", "assistant", "student"]
        )

        limit_parser = create_sub.add_parser("limit")
        limit_parser.add_argument("course_id", type=int)
        limit_parser.add_argument("number_of_uses", type=int)
        limit_parser.add_argument(
            "--per",
            required=True,
            choices=[
                "week",
                "day",
                "hour",
                "minute",
                "ten-seconds",
                "five-seconds",
                "second",
            ],
        )

    search_parser = sub_parsers.add_parser(
        "search", help="Search entities in the database."
    )

    for _ in range(1):
        search_sub = search_parser.add_subparsers(
            dest="entity_type",
            help="the entity type for which to search.",
            required=True,
        )

        course_parser = search_sub.add_parser("course")

        limit_parser = search_sub.add_parser("limit")
        limit_parser.add_argument("course_id", type=int)

    destroy_parser = sub_parsers.add_parser(
        "destroy", help="Destroy entities in the database."
    )
    for _ in range(1):
        destroy_sub = destroy_parser.add_subparsers(
            dest="entity_type",
            help="the entity type to be destroyed.",
            required=True,
        )

        course_parser = destroy_sub.add_parser("course")
        course_parser.add_argument("course_id", type=int)
        course_parser.add_argument("course_name", type=str)

        user_parser = destroy_sub.add_parser("participates_in")
        user_parser.add_argument("email", type=str)
        user_parser.add_argument("course_id", type=int)

        user_parser = destroy_sub.add_parser("user")
        user_parser.add_argument("email", type=str)

    args = parser.parse_args(arg_list)

    if args.command == "initialize":
        initialize(args.force)
    elif args.command == "mock":
        mock(args.force)
    elif args.command == "create":
        match args.entity_type:
            case "course":
                with Session(get_engine()) as sess:
                    course = Course(name=args.course_name)
                    sess.add(course)
                    sess.commit()
                    print(
                        f"Course '{course.name}' added successfully with ID '{course.id}'."
                    )
            case "user":
                with Session(get_engine()) as sess:
                    user = User(email=args.email)
                    user.set_password(args.password)
                    sess.add(user)
                    sess.commit()
                    print(f"User '{user.email}' added successfully.")
            case "participates_in":
                with Session(get_engine()) as sess:
                    part_in = ParticipatesIn(
                        email=args.email, course_id=args.course_id, role=args.role
                    )
                    sess.add(part_in)
                    sess.commit()
                    print(
                        f"User '{part_in.email}' now participates in the course with id '{part_in.course_id}' as a(n) '{part_in.role}'."
                    )
            case "limit":
                word_to_seconds = {
                    "second": 1,
                    "five-seconds": 5,
                    "ten-seconds": 10,
                    "minute": 60,
                    "hour": 60 * 60,
                    "day": 24 * 60 * 60,
                    "week": 7 * 24 * 60 * 60,
                }
                args.per
                with Session(get_engine()) as sess:
                    limit = Limit(
                        course_id=args.course_id,
                        maximum_number_of_uses=args.number_of_uses,
                        time_span_seconds=word_to_seconds[args.per],
                    )
                    sess.add(limit)
                    sess.commit()
                    print(
                        f"Limit with id '{limit.id}' has been added for the course with id '{args.course_id}'"
                    )
            case type_:
                raise error(f"Invalid entity type '{type_}'.")
    elif args.command == "search":
        match args.entity_type:
            case "course":
                with Session(get_engine()) as sess:
                    result = t.cast(
                        list[tuple[str, int, str | None]],
                        sess.query(Course.name, Course.id, User.email)
                        .outerjoin(
                            ParticipatesIn,
                            (Course.id == ParticipatesIn.course_id)
                            & (ParticipatesIn.role == "instructor"),
                        )
                        .outerjoin(User, User.email == ParticipatesIn.email)
                        .order_by(Course.name, Course.id)
                        .all(),
                    )
                    table = Table("Course Name", "Course ID", "Instructor Email")
                    for course_name, course_id, instructor_email in result:
                        table.add_row(
                            course_name, str(course_id), instructor_email or "None"
                        )
                    table.print()
            case "limit":
                with Session(get_engine()) as sess:
                    course = sess.get(Course, args.course_id)
                    if not course:
                        error(f"Invalid course ID '{args.course_id}'")
                    limits = (
                        sess.query(Limit).where(Limit.course_id == args.course_id).all()
                    )

                    print(f"For course with name '{course.name}' and ID '{course.id}'")
                    table = Table("Maximum Uses", "Time Frame (s)")
                    for limit in limits:
                        table.add_row(
                            str(limit.maximum_number_of_uses),
                            str(limit.time_span_seconds),
                        )
                    table.print()
            case type_:
                raise error(f"Invalid entity type '{type_}'.")
    elif args.command == "destroy":
        match args.entity_type:
            case "participates_in":
                with Session(get_engine()) as sess:
                    participates_in = sess.get(
                        ParticipatesIn, (args.email, args.course_id)
                    )
                    if not participates_in:
                        raise error(
                            f"No participation exists with for {args.email, args.course_id}"
                        )
                    sess.delete(participates_in)
                    sess.commit()
                    print(
                        f"Deleted participation of user '{participates_in.email}' in course '{participates_in.course_id}'"
                    )
            case "course":
                with Session(get_engine()) as sess:
                    course = sess.get(Course, args.course_id)
                    if not course:
                        raise error(f"No course exists with id {args.course_id}")

                    if course.name != args.course_name:
                        raise error(
                            f"The input course_id '{args.course_id}' belongs to a course with name '{course.name}', but you wanted to delete a course with the name '{args.course_name}'. Deletion aborted."
                        )
                    sess.delete(course)
                    sess.commit()
                    print(
                        f"Deleted course '{args.course_id}' with name '{args.course_name}'"
                    )
            case "user":
                with Session(get_engine()) as sess:
                    user = sess.get(User, args.email)
                    if not user:
                        raise error(f"No user exists with email '{args.email}'")
                    sess.delete(user)
                    sess.commit()
                    print(f"Deleted user with email '{args.email}'")

            case type_:
                raise error(f"Invalid entity type '{type_}'.")


def error(message: str) -> t.NoReturn:
    """Halt the program with an error message."""
    print(message, file=sys.stderr)
    exit(1)


class Table:
    """A displayable table."""

    def __init__(self, *column_names: str):
        self._column_names = [*column_names]
        self._num_columns = len(column_names)
        self._rows: list[tuple[str, ...]] = []
        self._max_column_lengths = [len(c) for c in column_names]

    def add_row(self, *columns: str):
        """Append a row to this table"""
        if len(columns) != self._num_columns:
            return ValueError(
                f"Cannot add a row with {len(columns)} entries to a table with {self._num_columns} columns."
            )

        self._max_column_lengths = [
            max(len(c), l) for c, l in zip(columns, self._max_column_lengths)
        ]

        self._rows.append(columns)

    def print(self, exptra_space: int = 4):
        """Print the table to standard output."""
        column_widths = list(map(lambda l: l + exptra_space, self._max_column_lengths))

        def format_row(row: tuple[str, ...]) -> str:
            return "".join(f"{val:<{w}}" for val, w in zip(row, column_widths))

        print(format_row(tuple(self._column_names)))

        print("-" * (sum(column_widths) - exptra_space))

        for row in self._rows:
            print(format_row(row))


def create_vector_extension():
    """Connects to the database and runs CREATE EXTENSION IF NOT EXISTS vector."""
    try:
        with get_engine().begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        print("'vector' extension created successfully.")
    except Exception as e:
        print(f"Error creating 'vector' extension: {e}")
        raise


def initialize(force: bool):
    """Creates all tables in the database if they do not already exist.
    If --force is also passed, all tables and the uploads folder will
    be deleted first and then the tables will be re-created.
    :param force: If True, clears existing tables and creates empty tables.
    """
    create_vector_extension()
    if not inspect(get_engine()).has_table("users"):
        base.metadata.create_all(get_engine())
        print("Database initialized.")
    elif force:
        base.metadata.drop_all(get_engine())
        base.metadata.create_all(get_engine())
        print("Database cleared and initialized.")
    else:
        print("Database already initialized.")


def mock(force: bool):
    """Adds mock courses and users with varying roles to the database.
    Only adds mock data if the users and Course tables are empty.
    """
    create_vector_extension()

    if not inspect(get_engine()).has_table("users"):
        base.metadata.create_all(get_engine())
    elif force:
        initialize(True)

    with Session(get_engine()) as session:
        courses_empty = not session.query(session.query(Course).exists()).scalar()
        users_empty = not session.query(session.query(User).exists()).scalar()

        if courses_empty and users_empty:
            add_new_course("CS010C")  # course ID 1
            add_new_course("CS061")  # course ID 2
            add_new_course("CS0111")  # course ID 3
            add_new_user("test001@ucr.edu")
            add_new_user("test002@ucr.edu")
            add_new_user("test003@ucr.edu")
            add_user_to_course("test001@ucr.edu", 1, "instructor")
            add_user_to_course("test001@ucr.edu", 2, "instructor")
            add_user_to_course("test001@ucr.edu", 3, "instructor")
            add_user_to_course("test002@ucr.edu", 1, "student")
            add_user_to_course("test002@ucr.edu", 2, "student")
            add_user_to_course("test002@ucr.edu", 3, "student")
            add_user_to_course("test003@ucr.edu", 1, "assistant")
            add_user_to_course("test003@ucr.edu", 2, "assistant")
            add_user_to_course("test003@ucr.edu", 3, "assistant")
            print("Mock data added to database.")
        else:
            print("Mock data not added, database already has data.")


if __name__ == "__main__":
    main()
