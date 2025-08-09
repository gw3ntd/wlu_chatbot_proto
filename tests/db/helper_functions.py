import shutil
from tabulate import tabulate
import typing
import sys
<<<<<<< HEAD
from pathlib import Path
=======
>>>>>>> 77da22c (base.html extended & message PFPs added)
from ucr_chatbot.db.models import *
from ucr_chatbot.config import Config

def initialize_db():
    """Creates database using specified engine."""
    base.metadata.create_all(engine)

def clear_db():
    """Deletes all tables in database."""
    base.metadata.drop_all(engine)

def delete_uploads_folder():
    """Deletes uploads folder and all files within it."""
    uploads_folder_path = Path(Config.FILE_STORAGE_PATH)
    if uploads_folder_path.exists():
        shutil.rmtree(uploads_folder_path)
    else:
        print("Uploads folder not found.")

def add_courses():
    """Adds all courses needed for testing to Courses table"""
    course_names: list[str] = [
        "CS009A",
        "CS009B",
        "CS009C",
        "CS010A",
        "CS010B",
        "CS010C",
        "CS011",
        "CS061",
        "CS100",
        "CS111",
        "CS141",
    ]
    for name in course_names:
        add_new_course(name)


def print_users():
    """Prints all users and their information"""
    with Session(engine) as session:
        all_entries = session.query(Users).all()
        rows: list[typing.Tuple[Column[str], Column[str], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.first_name, row.last_name))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_courses():
    """Prints all users and their information"""
    with Session(engine) as session:
        all_entries = session.query(Courses).all()
        rows: list[typing.Tuple[Column[int], Column[str]]] = []

        for row in all_entries:
            rows.append((row.id, row.name))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_participation():
    """Prints all relationships between users and courses"""
    with Session(engine) as session:
        all_entries = session.query(ParticipatesIn).all()
        rows: list[typing.Tuple[Column[str], Column[int], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.course_id, row.role))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_documents():
    """Prints all documents instances"""
    with Session(engine) as session:
        all_entries = session.query(Documents).all()
        rows: list[typing.Tuple[Column[str], Column[int], Column[bool]]] = []

        for row in all_entries:
            rows.append((row.file_path, row.course_id, row.is_active))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_segments():
    """Prints all segments instances"""
    with Session(engine) as session:
        all_entries = session.query(Segments).all()
        rows: list[typing.Tuple[Column[int], Column[str], Column[str]]] = []

        for row in all_entries:
            rows.append((row.id, row.text, row.document_id))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_embeddings():
    """Prints all embeddings instances"""
    with Session(engine) as session:
        all_entries = session.query(Embeddings).all()
        rows: list[typing.Tuple[Column[int], Column[Sequence[float]], Column[int]]] = []

        for row in all_entries:
            rows.append((row.id, row.vector, row.segment_id))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


if __name__ == "__main__":
    if "reset" in sys.argv:
        delete_uploads_folder()
        clear_db()
        initialize_db()
        add_courses()
<<<<<<< HEAD
        add_new_user("gnico007@ucr.edu", "test", "user")
        add_user_to_course("gnico007@ucr.edu", "test", "user", 1, "instructor")
        add_user_to_course("gnico007@ucr.edu", "test", "user", 9, "student")\
=======
        add_new_user("snall008@ucr.edu", "test", "user")
        add_user_to_course("snall008@ucr.edu", "test", "user", 1, "instructor")
        add_user_to_course("snall008@ucr.edu", "test", "user", 9, "student")
>>>>>>> 592d8ec (Added assistants form and fixed CSS paths)
        print("Database reset.")
    # elif "print" in sys.argv:
    #     print_users()
    #     print_courses()
    #     print_participation()
    #     print_documents()
    #     print_segments()
    #     print_embeddings()