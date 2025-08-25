from tabulate import tabulate
import typing
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from ucr_chatbot.db.models import *

def initialize_db():
    """Creates database using specified engine."""
    base.metadata.create_all(get_engine())


def clear_db():
    """Deletes all tables in database."""
    base.metadata.drop_all(get_engine())

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
    with Session(get_engine()) as session:
        all_entries = session.query(Users).all()
        rows: list[typing.Tuple[Column[str], Column[str], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.first_name, row.last_name))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_courses():
    """Prints all users and their information"""
    with Session(get_engine()) as session:
        all_entries = session.query(Courses).all()
        rows: list[typing.Tuple[Column[int], Column[str]]] = []

        for row in all_entries:
            rows.append((row.id, row.name))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_participation():
    """Prints all relationships between users and courses"""
    with Session(get_engine()) as session:
        all_entries = session.query(ParticipatesIn).all()
        rows: list[typing.Tuple[Column[str], Column[int], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.course_id, row.role))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_documents():
    """Prints all documents instances"""
    with Session(get_engine()) as session:
        all_entries = session.query(Documents).all()
        rows: list[typing.Tuple[Column[str], Column[int], Column[bool]]] = []

        for row in all_entries:
            rows.append((row.file_path, row.course_id, row.is_active))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_segments():
    """Prints all segments instances"""
    with Session(get_engine()) as session:
        all_entries = session.query(Segments).all()
        rows: list[typing.Tuple[Column[int], Column[str], Column[str]]] = []

        for row in all_entries:
            rows.append((row.id, row.text, row.document_id))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


def print_embeddings():
    """Prints all embeddings instances"""
    with Session(get_engine()) as session:
        all_entries = session.query(Embeddings).all()
        rows: list[typing.Tuple[Column[int], Column[Sequence[float]], Column[int]]] = []

        for row in all_entries:
            rows.append((row.id, row.vector, row.segment_id))
        print(tabulate(rows, headers="keys", tablefmt="psql"))